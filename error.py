#!/usr/bin/env python3
"""
benchmark_maria_nemotron.py

Benchmarks Nemotron 3.5 ASR WebSocket server on maria*.mp3 files from GCS.

Input:
  gs://cx-asr-test-data/audios/maria*.mp3
  gs://cx-asr-test-data/references/maria*_reference.txt

Output per audio:
  maria*_latencies.json
  maria*_transcript.txt

Upload output to:
  gs://cx-asr-test-data/results/nemotron_3.5/

Usage:
  python benchmark_maria_nemotron.py

Optional:
  python benchmark_maria_nemotron.py --limit 15
  python benchmark_maria_nemotron.py --language auto
  python benchmark_maria_nemotron.py --language es-US
  python benchmark_maria_nemotron.py --language en-US
  python benchmark_maria_nemotron.py --realtime
  python benchmark_maria_nemotron.py --no-download
  python benchmark_maria_nemotron.py --no-upload
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
OUT_DIR = WORK_DIR / "results" / "nemotron_3.5"

_LANG_TAG_RE = re.compile(r"<[a-z]{2}-[A-Z]{2}>\s*")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    return _LANG_TAG_RE.sub("", text).strip()


def ensure_dirs():
    for d in [AUDIO_DIR, REF_DIR, WAV_DIR, OUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    print("[cmd]", " ".join(cmd))

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if check and result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

    return result


def find_storage_cli() -> str:
    """
    Prefer gcloud storage. Fallback to gsutil.
    """

    if shutil.which("gcloud"):
        return "gcloud"

    if shutil.which("gsutil"):
        return "gsutil"

    raise RuntimeError(
        "Neither gcloud nor gsutil found. Install Google Cloud SDK first."
    )


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


def download_inputs():
    ensure_dirs()

    print("\nDownloading maria*.mp3 audios...")
    gcs_cp_many(f"{AUDIO_GCS}/maria*.mp3", AUDIO_DIR)

    print("\nDownloading maria*_reference.txt references...")
    gcs_cp_many(f"{REFERENCE_GCS}/maria*_reference.txt", REF_DIR)


def convert_mp3_to_wav_16k_mono(mp3_path: Path) -> Path:
    wav_path = WAV_DIR / f"{mp3_path.stem}.wav"

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
        str(wav_path),
    ]

    run_cmd(cmd)
    return wav_path


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
        raise ValueError(
            f"{wav_path} sample rate is {file_sr}, expected {SAMPLE_RATE}"
        )

    audio_duration_sec = len(audio_i16) / SAMPLE_RATE
    return audio_i16.tobytes(), audio_duration_sec


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------
def normalize_for_metrics(text: str) -> str:
    """
    Normalize multilingual transcript text for WER/CER/SER.

    - lowercases
    - converts underscores to spaces
    - removes punctuation
    - keeps accented characters
    """

    if not text:
        return ""

    text = text.lower()
    text = text.replace("_", " ")
    text = re.sub(r"<[a-z]{2}-[a-z]{2}>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\sáéíóúüñàèìòùç]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def levenshtein_distance(a: List[str], b: List[str]) -> int:
    """
    Memory-efficient Levenshtein distance.
    Works for words or characters.
    """

    if len(a) < len(b):
        a, b = b, a

    previous = list(range(len(b) + 1))

    for i, ca in enumerate(a, start=1):
        current = [i]

        for j, cb in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (ca != cb)

            current.append(
                min(
                    insert_cost,
                    delete_cost,
                    replace_cost,
                )
            )

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

    # SER:
    # If reference has multiple lines, compare line-by-line.
    # If reference has one long line, SER is 1.0 if any word error exists.
    ref_lines = [x.strip() for x in reference_text.splitlines() if x.strip()]
    hyp_lines = [x.strip() for x in hypothesis_text.splitlines() if x.strip()]

    if len(ref_lines) <= 1:
        sentence_errors = 1 if word_edits > 0 else 0
        sentence_count = 1
        ser = 1.0 if word_edits > 0 else 0.0
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
        "ser_percent": ser * 100,
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
# WebSocket benchmarking
# ---------------------------------------------------------------------
async def benchmark_one_audio(
    wav_path: Path,
    original_audio_path: Path,
    reference_path: Optional[Path],
    language: str,
    url: str,
    realtime: bool,
    receive_timeout_sec: float,
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

    async with websockets.connect(
        url,
        ping_interval=20,
        ping_timeout=120,
        max_size=None,
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
                                "type": "error",
                                "text": text,
                                "timestamp": datetime.now().isoformat(),
                                "server_session_id": server_session_id,
                                "server_timestamp_utc": server_timestamp_utc,
                                "latency_from_start_ms": (
                                    now - connection_start
                                )
                                * 1000,
                                "latency_from_send_start_ms": (
                                    now - send_start
                                )
                                * 1000,
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
                            "type": ev_type,
                            "latency_from_start_ms": (
                                now - connection_start
                            )
                            * 1000,
                            "latency_from_send_start_ms": (
                                now - send_start
                            )
                            * 1000,
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
                await asyncio.sleep(0.001)

        send_end = time.time()
        send_duration_sec = send_end - send_start

        await ws.send(json.dumps({"type": "eof"}))

        try:
            await asyncio.wait_for(
                done_event.wait(),
                timeout=receive_timeout_sec,
            )
        except asyncio.TimeoutError:
            print(
                f"[warn] Timeout waiting for done event after EOF: {wav_path.name}"
            )

        recv_task.cancel()

        try:
            await recv_task
        except asyncio.CancelledError:
            pass

    total_processing_time_sec = time.time() - connection_start

    # Important:
    # transcript.txt is generated line-by-line.
    # Each final ASR segment becomes one line.
    transcript = "\n".join(t.strip() for t in final_texts if t.strip())

    first_response = response_events[0] if response_events else None
    first_final = next((x for x in response_events if x.get("is_final")), None)

    first_response_latency_sec = (
        first_response["latency_from_start_ms"] / 1000
        if first_response
        else None
    )

    first_final_latency_sec = (
        first_final["latency_from_start_ms"] / 1000
        if first_final
        else None
    )

    first_byte_latency_sec = first_response_latency_sec

    timing_metrics = {
        "connection_time_sec": connection_time_sec,
        "send_duration_sec": send_duration_sec,
        "first_byte_latency_sec": first_byte_latency_sec,
        "first_response_latency_sec": first_response_latency_sec,
        "first_final_latency_sec": first_final_latency_sec,
        "time_to_first_chunk_sec": (
            first_chunk_sent_at - connection_start
            if first_chunk_sent_at
            else None
        ),
    }

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

    result = {
        "audio_file": str(original_audio_path),
        "converted_wav_file": str(wav_path),
        "reference_file": str(reference_path) if reference_path else None,
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
            "transcript_lines": len(
                [x for x in transcript.splitlines() if x.strip()]
            ),
            "transcript_words": len(transcript.split()),
            "transcript_chars": len(transcript),
        },
        "accuracy_metrics": accuracy_metrics,
        "latencies": response_events,
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
    """
    maria1.mp3 -> maria1_reference.txt
    """

    ref_name = f"{audio_path.stem}_reference.txt"
    ref_path = REF_DIR / ref_name

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

    audio_files = sorted(AUDIO_DIR.glob("maria*.mp3"))

    if args.limit:
        audio_files = audio_files[: args.limit]

    if not audio_files:
        raise RuntimeError(f"No maria*.mp3 files found in {AUDIO_DIR}")

    print(f"\nFound {len(audio_files)} maria audio files.")

    for idx, audio_path in enumerate(audio_files, start=1):
        print("\n" + "=" * 80)
        print(f"[{idx}/{len(audio_files)}] Benchmarking: {audio_path.name}")
        print("=" * 80)

        reference_path = find_reference_for_audio(audio_path)

        if reference_path:
            print(f"Reference: {reference_path.name}")
        else:
            print(f"[warn] No reference found for {audio_path.name}")

        wav_path = convert_mp3_to_wav_16k_mono(audio_path)

        output_prefix = audio_path.stem

        latency_out = OUT_DIR / f"{output_prefix}_latencies.json"
        transcript_out = OUT_DIR / f"{output_prefix}_transcript.txt"

        benchmark = await benchmark_one_audio(
            wav_path=wav_path,
            original_audio_path=audio_path,
            reference_path=reference_path,
            language=args.language,
            url=args.url,
            realtime=args.realtime,
            receive_timeout_sec=args.receive_timeout,
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
            print(
                f"WER={acc['wer_percent']:.2f}% "
                f"CER={acc['cer_percent']:.2f}% "
                f"SER={acc['ser_percent']:.2f}%"
            )

        print(f"Saved: {latency_out}")
        print(f"Saved: {transcript_out}")

    if args.upload:
        print("\nUploading result files to GCS...")
        gcs_upload_dir(OUT_DIR, RESULT_GCS)
        print(f"Uploaded to: {RESULT_GCS}/")


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
        "--realtime",
        action="store_true",
        help="Send chunks in real-time pacing. Default is fast mode.",
    )

    parser.add_argument(
        "--receive-timeout",
        type=float,
        default=120.0,
        help="Seconds to wait for done after EOF. Default: 120",
    )

    parser.add_argument(
        "--download",
        action="store_true",
        default=True,
        help="Download audios/references from GCS. Default: true",
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
        help="Upload result files to GCS. Default: true",
    )

    parser.add_argument(
        "--no-upload",
        dest="upload",
        action="store_false",
        help="Skip GCS upload.",
    )

    args = parser.parse_args()

    asyncio.run(run_benchmark(args))


if __name__ == "__main__":
    main()


(nemo_env) root@cx-asr-test:/home/nikita_verma2/nemotron_asr# tail --200 nemotron_benchmark.log 
tail: unrecognized option '--200'
Try 'tail --help' for more information.
(nemo_env) root@cx-asr-test:/home/nikita_verma2/nemotron_asr# tail -200 nemotron_benchmark.log 
nohup: ignoring input

Downloading maria*.mp3 audios...
[cmd] gcloud storage cp gs://cx-asr-test-data/audios/maria*.mp3 benchmark_workspace/audios

Downloading maria*_reference.txt references...
[cmd] gcloud storage cp gs://cx-asr-test-data/references/maria*_reference.txt benchmark_workspace/references

Found 15 maria audio files.

================================================================================
[1/15] Benchmarking: maria1.mp3
================================================================================
Reference: maria1_reference.txt
[cmd] ffmpeg -y -i benchmark_workspace/audios/maria1.mp3 -ac 1 -ar 16000 -sample_fmt s16 benchmark_workspace/wav_16k/maria1.wav
WER=33.58% CER=24.96% SER=100.00%
Saved: benchmark_workspace/results/nemotron_3.5/maria1_latencies.json
Saved: benchmark_workspace/results/nemotron_3.5/maria1_transcript.txt

================================================================================
[2/15] Benchmarking: maria10.mp3
================================================================================
Reference: maria10_reference.txt
[cmd] ffmpeg -y -i benchmark_workspace/audios/maria10.mp3 -ac 1 -ar 16000 -sample_fmt s16 benchmark_workspace/wav_16k/maria10.wav
WER=78.83% CER=74.48% SER=100.00%
Saved: benchmark_workspace/results/nemotron_3.5/maria10_latencies.json
Saved: benchmark_workspace/results/nemotron_3.5/maria10_transcript.txt

================================================================================
[3/15] Benchmarking: maria16.mp3
================================================================================
Reference: maria16_reference.txt
[cmd] ffmpeg -y -i benchmark_workspace/audios/maria16.mp3 -ac 1 -ar 16000 -sample_fmt s16 benchmark_workspace/wav_16k/maria16.wav
Traceback (most recent call last):
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 786, in <module>
    main()
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 782, in main
    asyncio.run(run_benchmark(args))
  File "/usr/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 673, in run_benchmark
    benchmark = await benchmark_one_audio(
                ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 495, in benchmark_one_audio
    await ws.send(chunk)
  File "/home/nikita_verma2/nemotron_asr/nemo_env/lib/python3.11/site-packages/websockets/asyncio/connection.py", line 485, in send
    async with self.send_context():
  File "/usr/lib/python3.11/contextlib.py", line 204, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/nikita_verma2/nemotron_asr/nemo_env/lib/python3.11/site-packages/websockets/asyncio/connection.py", line 965, in send_context
    raise self.protocol.close_exc from original_exc
websockets.exceptions.ConnectionClosedError: sent 1011 (internal error) keepalive ping timeout; no close frame received
