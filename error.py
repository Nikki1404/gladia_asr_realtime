#!/usr/bin/env python3
"""
benchmark_maria_nemotron.py

Benchmarks Nemotron 3.5 ASR WebSocket server on maria*.mp3 files from GCS.

Inputs:
  gs://cx-asr-test-data/audios/maria*.mp3
  gs://cx-asr-test-data/references/maria*_reference.txt

Outputs per original audio:
  maria*_latencies.json
  maria*_transcript.txt

If an audio fails:
  maria*_error.json

Uploads to:
  gs://cx-asr-test-data/results/nemotron_3.5/

Recommended run:
  nohup python benchmark_maria_nemotron.py --limit 15 --language auto --realtime --segment-seconds 300 --receive-timeout 1200 > nemotron_benchmark_full.log 2>&1 &

Resume without re-downloading:
  nohup python benchmark_maria_nemotron.py --limit 15 --language auto --realtime --segment-seconds 300 --receive-timeout 1200 --no-download > nemotron_benchmark_resume.log 2>&1 &
"""

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import sys
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import websockets


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
DEFAULT_WS_URL = "ws://35.254.200.29:8003/asr/realtime-custom-vad"

AUDIO_GCS = "gs://cx-asr-test-data/audios"
REFERENCE_GCS = "gs://cx-asr-test-data/references"
RESULT_GCS = "gs://cx-asr-test-data/results/nemotron_3.5"

MODEL_NAME = "nemotron-3.5-asr-streaming-0.6b"

SAMPLE_RATE = 16000
CHUNK_MS = 100
CHUNK_BYTES = int(SAMPLE_RATE * CHUNK_MS / 1000) * 2

WORK_DIR = Path("benchmark_workspace")
AUDIO_DIR = WORK_DIR / "audios"
REF_DIR = WORK_DIR / "references"
WAV_DIR = WORK_DIR / "wav_16k"
SEGMENT_DIR = WORK_DIR / "segments_16k"
OUT_DIR = WORK_DIR / "results" / "nemotron_3.5"

_LANG_TAG_RE = re.compile(r"<[a-z]{2}-[A-Z]{2}>\s*")


# ---------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    return _LANG_TAG_RE.sub("", text).strip()


def ensure_dirs():
    for d in [AUDIO_DIR, REF_DIR, WAV_DIR, SEGMENT_DIR, OUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    print("[cmd]", " ".join(cmd), flush=True)

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if check and result.returncode != 0:
        if result.stdout:
            print(result.stdout, flush=True)
        if result.stderr:
            print(result.stderr, file=sys.stderr, flush=True)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

    return result


def find_storage_cli() -> str:
    if shutil.which("gcloud"):
        return "gcloud"

    if shutil.which("gsutil"):
        return "gsutil"

    raise RuntimeError("Neither gcloud nor gsutil found. Install Google Cloud SDK first.")


def gcs_cp_many(src_pattern: str, dst_dir: Path):
    cli = find_storage_cli()

    if cli == "gcloud":
        run_cmd(["gcloud", "storage", "cp", src_pattern, str(dst_dir)])
    else:
        run_cmd(["gsutil", "-m", "cp", src_pattern, str(dst_dir)])


def gcs_upload_dir(src_dir: Path, dst_gcs: str):
    cli = find_storage_cli()

    if cli == "gcloud":
        run_cmd(["gcloud", "storage", "cp", f"{src_dir}/*", f"{dst_gcs}/"])
    else:
        run_cmd(["gsutil", "-m", "cp", f"{src_dir}/*", f"{dst_gcs}/"])


def gcs_upload_files(files: List[Path], dst_gcs: str):
    cli = find_storage_cli()

    for file_path in files:
        if not file_path.exists():
            print(f"[warn] File not found, skipping upload: {file_path}", flush=True)
            continue

        if cli == "gcloud":
            run_cmd(["gcloud", "storage", "cp", str(file_path), f"{dst_gcs}/"])
        else:
            run_cmd(["gsutil", "cp", str(file_path), f"{dst_gcs}/"])


def download_inputs():
    ensure_dirs()

    print("\nDownloading maria*.mp3 audios...", flush=True)
    gcs_cp_many(f"{AUDIO_GCS}/maria*.mp3", AUDIO_DIR)

    print("\nDownloading maria*_reference.txt references...", flush=True)
    gcs_cp_many(f"{REFERENCE_GCS}/maria*_reference.txt", REF_DIR)


def natural_key(path: Path):
    return [
        int(x) if x.isdigit() else x.lower()
        for x in re.split(r"(\d+)", path.name)
    ]


# ---------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------
def read_wav_pcm16(wav_path: Path) -> Tuple[bytes, float]:
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        file_sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw_audio = wf.readframes(n_frames)

    if sample_width != 2:
        raise ValueError(f"{wav_path} is not 16-bit PCM WAV")

    audio_i16 = np.frombuffer(raw_audio, dtype=np.int16)

    if n_channels == 2:
        audio_i16 = audio_i16.reshape(-1, 2).mean(axis=1).astype(np.int16)

    if file_sr != SAMPLE_RATE:
        raise ValueError(f"{wav_path} sample rate is {file_sr}, expected {SAMPLE_RATE}")

    audio_duration_sec = len(audio_i16) / SAMPLE_RATE
    return audio_i16.tobytes(), audio_duration_sec


def split_mp3_to_wav_segments(
    mp3_path: Path,
    segment_seconds: int,
    force_split: bool = False,
) -> List[Path]:
    """
    Split one MP3 into 16kHz mono PCM16 WAV segments.

    For any audio duration:
      5 min audio       -> 1 segment if segment_seconds=300 or 600
      45 min audio      -> multiple segments
      2 hr 41 min audio -> many segments

    All segments are later transcribed and combined into one final transcript.
    """

    per_audio_segment_dir = SEGMENT_DIR / mp3_path.stem
    per_audio_segment_dir.mkdir(parents=True, exist_ok=True)

    pattern = per_audio_segment_dir / f"{mp3_path.stem}_part_%04d.wav"

    existing_segments = sorted(
        per_audio_segment_dir.glob(f"{mp3_path.stem}_part_*.wav"),
        key=natural_key,
    )

    if existing_segments and not force_split:
        print(
            f"[info] Using existing {len(existing_segments)} segments for {mp3_path.name}",
            flush=True,
        )
        return existing_segments

    for old_file in existing_segments:
        try:
            old_file.unlink()
        except FileNotFoundError:
            pass

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(mp3_path),
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-sample_fmt",
        "s16",
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        str(pattern),
    ]

    run_cmd(cmd)

    segment_paths = sorted(
        per_audio_segment_dir.glob(f"{mp3_path.stem}_part_*.wav"),
        key=natural_key,
    )

    if not segment_paths:
        raise RuntimeError(f"No segments created for {mp3_path}")

    return segment_paths


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------
def normalize_for_metrics(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = text.replace("_", " ")
    text = re.sub(r"<[a-z]{2}-[a-z]{2}>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\sáéíóúüñàèìòùç]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def levenshtein_distance(a: List[str], b: List[str]) -> int:
    if len(a) < len(b):
        a, b = b, a

    previous = list(range(len(b) + 1))

    for i, ca in enumerate(a, start=1):
        current = [i]

        for j, cb in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (ca != cb)

            current.append(min(insert_cost, delete_cost, replace_cost))

        previous = current

    return previous[-1]


def calculate_wer_cer_ser(reference_text: str, hypothesis_text: str) -> Dict:
    ref_norm = normalize_for_metrics(reference_text)
    hyp_norm = normalize_for_metrics(hypothesis_text)

    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()

    word_edits = levenshtein_distance(ref_words, hyp_words)
    wer = word_edits / max(1, len(ref_words))

    ref_chars = list(ref_norm.replace(" ", ""))
    hyp_chars = list(hyp_norm.replace(" ", ""))

    char_edits = levenshtein_distance(ref_chars, hyp_chars)
    cer = char_edits / max(1, len(ref_chars))

    ref_lines = [x.strip() for x in reference_text.splitlines() if x.strip()]
    hyp_lines = [x.strip() for x in hypothesis_text.splitlines() if x.strip()]

    # If reference is one paragraph, SER is not meaningful.
    if len(ref_lines) <= 1:
        sentence_errors = None
        sentence_count = len(ref_lines)
        ser = None
    else:
        sentence_count = len(ref_lines)
        sentence_errors = 0

        for i, ref_line in enumerate(ref_lines):
            hyp_line = hyp_lines[i] if i < len(hyp_lines) else ""

            r = normalize_for_metrics(ref_line).split()
            h = normalize_for_metrics(hyp_line).split()

            if levenshtein_distance(r, h) > 0:
                sentence_errors += 1

        ser = sentence_errors / max(1, sentence_count)

    return {
        "wer": wer,
        "wer_percent": wer * 100,
        "cer": cer,
        "cer_percent": cer * 100,
        "ser": ser,
        "ser_percent": ser * 100 if ser is not None else None,
        "word_edits": word_edits,
        "reference_words": len(ref_words),
        "hypothesis_words": len(hyp_words),
        "char_edits": char_edits,
        "reference_chars": len(ref_chars),
        "hypothesis_chars": len(hyp_chars),
        "sentence_errors": sentence_errors,
        "sentence_count": sentence_count,
    }


# ---------------------------------------------------------------------
# Single-segment WebSocket transcription
# ---------------------------------------------------------------------
async def benchmark_one_segment(
    wav_path: Path,
    original_audio_path: Path,
    language: str,
    url: str,
    realtime: bool,
    receive_timeout_sec: float,
    fast_sleep_sec: float,
    segment_idx: int,
    segment_count: int,
) -> Dict:
    raw_bytes, audio_duration_sec = read_wav_pcm16(wav_path)

    chunks = [
        raw_bytes[i : i + CHUNK_BYTES]
        for i in range(0, len(raw_bytes), CHUNK_BYTES)
    ]

    response_events = []
    final_texts = []

    partial_count = 0
    final_count = 0

    connection_start = time.time()

    # Disable client ping timeout so long ASR processing does not kill connection.
    async with websockets.connect(
        url,
        ping_interval=None,
        ping_timeout=None,
        max_size=None,
        close_timeout=30,
    ) as ws:
        connected_at = time.time()
        connection_time_sec = connected_at - connection_start

        await ws.send(
            json.dumps(
                {
                    "backend": "nemotron",
                    "sample_rate": SAMPLE_RATE,
                    "language": language,
                }
            )
        )

        first_chunk_sent_at = None
        send_start = time.time()
        send_end = None

        done_event = asyncio.Event()

        async def receiver():
            nonlocal partial_count
            nonlocal final_count
            nonlocal send_end

            response_num = 0

            try:
                async for raw in ws:
                    if isinstance(raw, bytes):
                        continue

                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    now = time.time()
                    ev_type = msg.get("type", "")
                    text = clean_text(msg.get("text", ""))
                    t_start = msg.get("t_start")
                    server_session_id = msg.get("session_id")
                    server_timestamp_utc = msg.get("timestamp_utc")

                    if ev_type == "done":
                        done_event.set()
                        break

                    if ev_type == "error":
                        response_num += 1

                        response_events.append(
                            {
                                "response_num": response_num,
                                "segment_idx": segment_idx,
                                "segment_count": segment_count,
                                "segment_file": str(wav_path),
                                "type": "error",
                                "text": text,
                                "timestamp": datetime.now().isoformat(),
                                "server_session_id": server_session_id,
                                "server_timestamp_utc": server_timestamp_utc,
                                "latency_from_start_ms": (now - connection_start) * 1000,
                                "latency_from_send_start_ms": (now - send_start) * 1000,
                                "latency_from_first_chunk_ms": (
                                    (now - first_chunk_sent_at) * 1000
                                    if first_chunk_sent_at
                                    else None
                                ),
                                "latency_from_send_end_ms": (
                                    (now - send_end) * 1000
                                    if send_end
                                    else None
                                ),
                                "is_final": False,
                                "words": 0,
                                "char_count": 0,
                                "server_t_start": t_start,
                            }
                        )

                        continue

                    if ev_type not in {"partial", "final"}:
                        continue

                    response_num += 1

                    if ev_type == "partial":
                        partial_count += 1

                    if ev_type == "final":
                        final_count += 1
                        if text:
                            final_texts.append(text)

                    response_events.append(
                        {
                            "response_num": response_num,
                            "segment_idx": segment_idx,
                            "segment_count": segment_count,
                            "segment_file": str(wav_path),
                            "type": ev_type,
                            "latency_from_start_ms": (now - connection_start) * 1000,
                            "latency_from_send_start_ms": (now - send_start) * 1000,
                            "latency_from_first_chunk_ms": (
                                (now - first_chunk_sent_at) * 1000
                                if first_chunk_sent_at
                                else None
                            ),
                            "latency_from_send_end_ms": (
                                (now - send_end) * 1000
                                if send_end
                                else None
                            ),
                            "is_final": ev_type == "final",
                            "words": len(text.split()),
                            "char_count": len(text),
                            "server_t_start": t_start,
                            "server_session_id": server_session_id,
                            "server_timestamp_utc": server_timestamp_utc,
                            "text": text,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            except Exception as e:
                response_events.append(
                    {
                        "response_num": len(response_events) + 1,
                        "segment_idx": segment_idx,
                        "segment_count": segment_count,
                        "segment_file": str(wav_path),
                        "type": "client_receive_error",
                        "text": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "is_final": False,
                        "words": 0,
                        "char_count": 0,
                    }
                )

                done_event.set()

        recv_task = asyncio.create_task(receiver())

        print(
            f"Sending segment {segment_idx}/{segment_count} "
            f"duration={audio_duration_sec:.2f}s chunks={len(chunks)} realtime={realtime}",
            flush=True,
        )

        for i, chunk in enumerate(chunks):
            if first_chunk_sent_at is None:
                first_chunk_sent_at = time.time()

            await ws.send(chunk)

            if realtime:
                expected_elapsed = (i + 1) * CHUNK_MS / 1000.0
                actual_elapsed = time.time() - send_start
                sleep_for = expected_elapsed - actual_elapsed

                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
            else:
                await asyncio.sleep(fast_sleep_sec)

        send_end = time.time()
        send_duration_sec = send_end - send_start

        await ws.send(json.dumps({"type": "eof"}))

        # Dynamic timeout:
        # For 5-10 min segment, wait enough for EOF flush.
        dynamic_timeout = max(receive_timeout_sec, audio_duration_sec + 600)

        try:
            await asyncio.wait_for(done_event.wait(), timeout=dynamic_timeout)
        except asyncio.TimeoutError:
            print(
                f"[warn] Timeout waiting for done after EOF: "
                f"{wav_path.name} timeout={dynamic_timeout}s",
                flush=True,
            )

        recv_task.cancel()

        try:
            await recv_task
        except asyncio.CancelledError:
            pass

    total_processing_time_sec = time.time() - connection_start

    transcript = " ".join(t.strip() for t in final_texts if t.strip())
    transcript = re.sub(r"\s+", " ", transcript).strip()

    first_response = response_events[0] if response_events else None
    first_final = next((x for x in response_events if x.get("is_final")), None)

    timing_metrics = {
        "connection_time_sec": connection_time_sec,
        "send_duration_sec": send_duration_sec,
        "first_byte_latency_sec": (
            first_response["latency_from_start_ms"] / 1000
            if first_response
            else None
        ),
        "first_response_latency_sec": (
            first_response["latency_from_start_ms"] / 1000
            if first_response
            else None
        ),
        "first_final_latency_sec": (
            first_final["latency_from_start_ms"] / 1000
            if first_final
            else None
        ),
        "time_to_first_chunk_sec": (
            first_chunk_sent_at - connection_start if first_chunk_sent_at else None
        ),
    }

    result = {
        "audio_file": str(original_audio_path),
        "segment_file": str(wav_path),
        "segment_idx": segment_idx,
        "segment_count": segment_count,
        "audio_duration_sec": audio_duration_sec,
        "total_processing_time_sec": total_processing_time_sec,
        "rtf": (
            total_processing_time_sec / audio_duration_sec
            if audio_duration_sec > 0
            else None
        ),
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "language": language,
        "server_url": url,
        "realtime": realtime,
        "timing_metrics": timing_metrics,
        "summary": {
            "partial_count": partial_count,
            "final_count": final_count,
            "total_response_count": len(response_events),
            "transcript_words": len(transcript.split()),
            "transcript_chars": len(transcript),
        },
        "latencies": response_events,
    }

    return {
        "result": result,
        "transcript": transcript,
    }


# ---------------------------------------------------------------------
# Full original audio benchmark using segments
# ---------------------------------------------------------------------
async def benchmark_segmented_audio(
    segment_paths: List[Path],
    original_audio_path: Path,
    reference_path: Optional[Path],
    language: str,
    url: str,
    realtime: bool,
    receive_timeout_sec: float,
    fast_sleep_sec: float,
) -> Dict:
    all_latencies = []
    all_transcript_parts = []
    segment_summaries = []

    total_audio_duration_sec = 0.0
    total_processing_time_sec = 0.0

    segment_count = len(segment_paths)

    for segment_idx, wav_path in enumerate(segment_paths, start=1):
        print(
            f"\nTranscribing segment {segment_idx}/{segment_count}: {wav_path.name}",
            flush=True,
        )

        segment_start = time.time()

        segment_benchmark = await benchmark_one_segment(
            wav_path=wav_path,
            original_audio_path=original_audio_path,
            language=language,
            url=url,
            realtime=realtime,
            receive_timeout_sec=receive_timeout_sec,
            fast_sleep_sec=fast_sleep_sec,
            segment_idx=segment_idx,
            segment_count=segment_count,
        )

        segment_processing_time_sec = time.time() - segment_start

        segment_result = segment_benchmark["result"]
        segment_transcript = segment_benchmark["transcript"].strip()

        if segment_transcript:
            all_transcript_parts.append(segment_transcript)

        segment_latencies = segment_result["latencies"]
        all_latencies.extend(segment_latencies)

        total_audio_duration_sec += segment_result["audio_duration_sec"]
        total_processing_time_sec += segment_processing_time_sec

        segment_summaries.append(
            {
                "segment_idx": segment_idx,
                "segment_file": str(wav_path),
                "audio_duration_sec": segment_result["audio_duration_sec"],
                "processing_time_sec": segment_processing_time_sec,
                "rtf": (
                    segment_processing_time_sec / segment_result["audio_duration_sec"]
                    if segment_result["audio_duration_sec"] > 0
                    else None
                ),
                "final_count": segment_result["summary"]["final_count"],
                "partial_count": segment_result["summary"]["partial_count"],
                "total_response_count": segment_result["summary"]["total_response_count"],
                "transcript_words": len(segment_transcript.split()),
                "transcript_chars": len(segment_transcript),
            }
        )

    # Match your reference format: one continuous paragraph.
    transcript = " ".join(x.strip() for x in all_transcript_parts if x.strip())
    transcript = re.sub(r"\s+", " ", transcript).strip()

    reference_text = ""
    accuracy_metrics = None

    if reference_path and reference_path.exists():
        reference_text = reference_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        accuracy_metrics = calculate_wer_cer_ser(
            reference_text=reference_text,
            hypothesis_text=transcript,
        )

    first_response = all_latencies[0] if all_latencies else None
    first_final = next((x for x in all_latencies if x.get("is_final")), None)

    result = {
        "audio_file": str(original_audio_path),
        "reference_file": str(reference_path) if reference_path else None,
        "audio_duration_sec": total_audio_duration_sec,
        "total_processing_time_sec": total_processing_time_sec,
        "rtf": (
            total_processing_time_sec / total_audio_duration_sec
            if total_audio_duration_sec > 0
            else None
        ),
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "language": language,
        "server_url": url,
        "realtime": realtime,
        "segmented": True,
        "segment_count": segment_count,
        "timing_metrics": {
            "first_byte_latency_sec": (
                first_response["latency_from_start_ms"] / 1000
                if first_response
                else None
            ),
            "first_response_latency_sec": (
                first_response["latency_from_start_ms"] / 1000
                if first_response
                else None
            ),
            "first_final_latency_sec": (
                first_final["latency_from_start_ms"] / 1000
                if first_final
                else None
            ),
        },
        "summary": {
            "segment_count": segment_count,
            "total_response_count": len(all_latencies),
            "final_count": sum(1 for x in all_latencies if x.get("is_final")),
            "partial_count": sum(1 for x in all_latencies if x.get("type") == "partial"),
            "transcript_lines": 1 if transcript else 0,
            "transcript_words": len(transcript.split()),
            "transcript_chars": len(transcript),
        },
        "segment_summaries": segment_summaries,
        "accuracy_metrics": accuracy_metrics,
        "latencies": all_latencies,
    }

    return {
        "result": result,
        "transcript": transcript,
        "reference_text": reference_text,
    }


# ---------------------------------------------------------------------
# File matching
# ---------------------------------------------------------------------
def find_reference_for_audio(audio_path: Path) -> Optional[Path]:
    candidates = [
        REF_DIR / f"{audio_path.stem}_reference.txt",
        REF_DIR / f"{audio_path.stem}_reference.text",
    ]

    for ref_path in candidates:
        if ref_path.exists():
            return ref_path

    return None


# ---------------------------------------------------------------------
# Main benchmark runner
# ---------------------------------------------------------------------
async def run_benchmark(args):
    ensure_dirs()

    if args.download:
        download_inputs()

    audio_files = sorted(AUDIO_DIR.glob("maria*.mp3"), key=natural_key)

    if args.limit:
        audio_files = audio_files[: args.limit]

    if not audio_files:
        raise RuntimeError(f"No maria*.mp3 files found in {AUDIO_DIR}")

    print(f"\nFound {len(audio_files)} maria audio files.", flush=True)

    completed = 0
    failed = 0
    skipped = 0

    for idx, audio_path in enumerate(audio_files, start=1):
        print("\n" + "=" * 80, flush=True)
        print(f"[{idx}/{len(audio_files)}] Benchmarking: {audio_path.name}", flush=True)
        print("=" * 80, flush=True)

        reference_path = find_reference_for_audio(audio_path)

        if reference_path:
            print(f"Reference: {reference_path.name}", flush=True)
        else:
            print(f"[warn] No reference found for {audio_path.name}", flush=True)

        output_prefix = audio_path.stem

        latency_out = OUT_DIR / f"{output_prefix}_latencies.json"
        transcript_out = OUT_DIR / f"{output_prefix}_transcript.txt"
        error_out = OUT_DIR / f"{output_prefix}_error.json"

        if latency_out.exists() and transcript_out.exists() and not args.force:
            print(f"[skip] Existing output found for {output_prefix}, skipping.", flush=True)
            skipped += 1

            if args.upload_each:
                try:
                    gcs_upload_files([latency_out, transcript_out], RESULT_GCS)
                except Exception as upload_error:
                    print(
                        f"[warn] Could not upload skipped existing files: {upload_error}",
                        flush=True,
                    )

            continue

        try:
            segment_paths = split_mp3_to_wav_segments(
                mp3_path=audio_path,
                segment_seconds=args.segment_seconds,
                force_split=args.force_split,
            )

            print(
                f"Created/found {len(segment_paths)} segments for {audio_path.name}",
                flush=True,
            )

            benchmark = await benchmark_segmented_audio(
                segment_paths=segment_paths,
                original_audio_path=audio_path,
                reference_path=reference_path,
                language=args.language,
                url=args.url,
                realtime=args.realtime,
                receive_timeout_sec=args.receive_timeout,
                fast_sleep_sec=args.fast_sleep,
            )

            latency_out.write_text(
                json.dumps(
                    benchmark["result"],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            transcript_out.write_text(
                benchmark["transcript"],
                encoding="utf-8",
            )

            acc = benchmark["result"].get("accuracy_metrics")

            if acc:
                ser_str = (
                    f"{acc['ser_percent']:.2f}%"
                    if acc.get("ser_percent") is not None
                    else "N/A"
                )

                print(
                    f"WER={acc['wer_percent']:.2f}% "
                    f"CER={acc['cer_percent']:.2f}% "
                    f"SER={ser_str}",
                    flush=True,
                )

            print(f"Saved: {latency_out}", flush=True)
            print(f"Saved: {transcript_out}", flush=True)

            completed += 1

            if args.upload_each:
                print(f"Uploading result files for {output_prefix} to GCS...", flush=True)
                gcs_upload_files([latency_out, transcript_out], RESULT_GCS)

        except Exception as e:
            failed += 1
            print(f"[error] Failed benchmarking {audio_path.name}: {e}", flush=True)

            error_payload = {
                "audio_file": str(audio_path),
                "reference_file": str(reference_path) if reference_path else None,
                "timestamp": datetime.now().isoformat(),
                "model": MODEL_NAME,
                "language": args.language,
                "server_url": args.url,
                "segment_seconds": args.segment_seconds,
                "error": repr(e),
                "status": "failed",
            }

            error_out.write_text(
                json.dumps(error_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            print(f"Saved error file: {error_out}", flush=True)

            if args.upload_each:
                try:
                    gcs_upload_files([error_out], RESULT_GCS)
                except Exception as upload_error:
                    print(f"[warn] Could not upload error file: {upload_error}", flush=True)

            continue

    if args.upload:
        print("\nUploading all result files to GCS...", flush=True)
        gcs_upload_dir(OUT_DIR, RESULT_GCS)
        print(f"Uploaded to: {RESULT_GCS}/", flush=True)

    print("\nBenchmark complete.", flush=True)
    print(f"Completed: {completed}", flush=True)
    print(f"Skipped:   {skipped}", flush=True)
    print(f"Failed:    {failed}", flush=True)
    print(f"Results:   {OUT_DIR}", flush=True)
    print(f"GCS:       {RESULT_GCS}/", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Nemotron 3.5 ASR on maria*.mp3 files from GCS"
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_WS_URL,
        help=f"Nemotron WebSocket URL. Default: {DEFAULT_WS_URL}",
    )

    parser.add_argument(
        "--language",
        default="auto",
        help="Language: auto, en-US, es-US. Default: auto",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Number of maria*.mp3 files to benchmark. Default: 15",
    )

    parser.add_argument(
        "--segment-seconds",
        type=int,
        default=300,
        help="Split audio into N-second chunks. Default: 300 seconds.",
    )

    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Send chunks in real-time pacing. Recommended for complete long audio transcription.",
    )

    parser.add_argument(
        "--receive-timeout",
        type=float,
        default=1200.0,
        help="Minimum seconds to wait for done after EOF. Default: 1200.",
    )

    parser.add_argument(
        "--fast-sleep",
        type=float,
        default=0.005,
        help="Sleep between chunks in non-realtime mode. Default: 0.005 sec.",
    )

    parser.add_argument(
        "--download",
        action="store_true",
        default=True,
        help="Download audios/references from GCS. Default: true.",
    )

    parser.add_argument(
        "--no-download",
        dest="download",
        action="store_false",
        help="Skip GCS download and use local benchmark_workspace files.",
    )

    parser.add_argument(
        "--upload",
        action="store_true",
        default=True,
        help="Upload all result files to GCS at the end. Default: true.",
    )

    parser.add_argument(
        "--no-upload",
        dest="upload",
        action="store_false",
        help="Skip final bulk GCS upload.",
    )

    parser.add_argument(
        "--upload-each",
        action="store_true",
        default=True,
        help="Upload each audio result immediately after benchmarking. Default: true.",
    )

    parser.add_argument(
        "--no-upload-each",
        dest="upload_each",
        action="store_false",
        help="Do not upload each result immediately.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if output files already exist.",
    )

    parser.add_argument(
        "--force-split",
        action="store_true",
        help="Recreate WAV segments even if segment files already exist.",
    )

    args = parser.parse_args()

    asyncio.run(run_benchmark(args))


if __name__ == "__main__":
    main()
