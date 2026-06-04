import argparse
import asyncio
import json
import re
import time
import wave
from pathlib import Path
from typing import Optional

import numpy as np
import websockets
from scipy.signal import resample_poly

try:
    from jiwer import cer, process_words, wer

    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False


TARGET_SAMPLE_RATE = 16000


def read_wav_as_pcm16(path: str) -> bytes:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"WAV file not found: {path}")

    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if sample_width != 2:
        raise ValueError("Only PCM16 WAV files are supported.")

    audio = np.frombuffer(frames, dtype=np.int16)

    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)

    if sample_rate != TARGET_SAMPLE_RATE:
        audio_f32 = audio.astype(np.float32) / 32768.0

        gcd = np.gcd(sample_rate, TARGET_SAMPLE_RATE)
        up = TARGET_SAMPLE_RATE // gcd
        down = sample_rate // gcd

        audio_f32 = resample_poly(audio_f32, up, down)

        audio = np.clip(
            audio_f32 * 32767,
            -32768,
            32767,
        ).astype(np.int16)

    return audio.tobytes()


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\sáéíóúñü]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def none_wer_metrics(final_text: str, error_message: str) -> dict:
    final_norm = normalize_text(final_text)

    return {
        "reference": None,
        "hypothesis": final_text,
        "reference_normalized": None,
        "hypothesis_normalized": final_norm,
        "wer": None,
        "wer_percent": None,
        "cer": None,
        "cer_percent": None,
        "hits": None,
        "substitutions": None,
        "deletions": None,
        "insertions": None,
        "reference_word_count": None,
        "hypothesis_word_count": len(final_norm.split()),
        "wer_error": error_message,
    }


def calculate_asr_metrics(reference_text: str, hypothesis_text: str) -> dict:
    if not JIWER_AVAILABLE:
        return none_wer_metrics(
            final_text=hypothesis_text,
            error_message="jiwer is not installed. Run: pip install jiwer==3.0.5",
        )

    reference_norm = normalize_text(reference_text)
    hypothesis_norm = normalize_text(hypothesis_text)

    word_output = process_words(reference_norm, hypothesis_norm)

    wer_score = wer(reference_norm, hypothesis_norm)
    cer_score = cer(reference_norm, hypothesis_norm)

    return {
        "reference": reference_text,
        "hypothesis": hypothesis_text,
        "reference_normalized": reference_norm,
        "hypothesis_normalized": hypothesis_norm,
        "wer": round(wer_score, 4),
        "wer_percent": round(wer_score * 100, 2),
        "cer": round(cer_score, 4),
        "cer_percent": round(cer_score * 100, 2),
        "hits": word_output.hits,
        "substitutions": word_output.substitutions,
        "deletions": word_output.deletions,
        "insertions": word_output.insertions,
        "reference_word_count": len(reference_norm.split()),
        "hypothesis_word_count": len(hypothesis_norm.split()),
        "wer_error": None,
    }


def calculate_latency_fields(
    data: dict,
    client_receive_ts_ms: float,
    timing_holder: dict,
) -> dict:
    msg_type = data.get("type")
    text = data.get("text", "") or ""

    server_send_ts_ms = data.get("server_send_ts_ms")
    server_audio_received_ts_ms = data.get("server_audio_received_ts_ms")
    utterance_start_ts_ms = data.get("utterance_start_ts_ms")

    latency_ms = None
    if server_send_ts_ms is not None:
        latency_ms = round(
            client_receive_ts_ms - float(server_send_ts_ms),
            2,
        )

    # Per-event TTFB:
    # How long server took to send this response after it received latest audio chunk.
    ttfb_ms = None
    if (
        server_send_ts_ms is not None
        and server_audio_received_ts_ms is not None
        and msg_type not in {"ready", "loading", "config_ack"}
    ):
        ttfb_ms = round(
            float(server_send_ts_ms) - float(server_audio_received_ts_ms),
            2,
        )

    # Per-event TTFT:
    # For text messages, how long from current utterance start to this text output.
    # This is intentionally different from TTFB.
    ttft_ms = None
    if (
        server_send_ts_ms is not None
        and utterance_start_ts_ms is not None
        and text.strip()
    ):
        ttft_ms = round(
            float(server_send_ts_ms) - float(utterance_start_ts_ms),
            2,
        )

    first_audio_send_ts_ms = timing_holder.get("first_audio_send_ts_ms")

    if (
        timing_holder.get("session_ttfb_ms") is None
        and first_audio_send_ts_ms is not None
        and msg_type not in {"ready", "loading", "config_ack"}
    ):
        timing_holder["session_ttfb_ms"] = round(
            client_receive_ts_ms - first_audio_send_ts_ms,
            2,
        )
        timing_holder["first_response_type"] = msg_type

    if (
        timing_holder.get("session_ttft_ms") is None
        and first_audio_send_ts_ms is not None
        and text.strip()
    ):
        timing_holder["session_ttft_ms"] = round(
            client_receive_ts_ms - first_audio_send_ts_ms,
            2,
        )
        timing_holder["first_text_type"] = msg_type

    return {
        "latency_ms": latency_ms,
        "ttfb_ms": ttfb_ms,
        "ttft_ms": ttft_ms,
        "session_ttfb_ms": timing_holder.get("session_ttfb_ms"),
        "session_ttft_ms": timing_holder.get("session_ttft_ms"),
        "first_response_type": timing_holder.get("first_response_type"),
        "first_text_type": timing_holder.get("first_text_type"),
    }


async def receiver(ws, timing_holder: dict) -> dict:
    result = {
        "partials": [],
        "utterance_finals": [],
        "language_switches": [],
        "event_metrics": [],

        "final_text": "",

        "session_ttfb_ms": None,
        "session_ttft_ms": None,
        "first_response_type": None,
        "first_text_type": None,

        "final_latency_ms": None,
        "server_final_elapsed_ms": None,

        "asr_confidence": None,

        "lid_confidences": [],
        "last_lid_confidence": None,
        "last_lid_label": None,
    }

    async for message in ws:
        client_receive_ts_ms = time.time() * 1000.0
        data = json.loads(message)

        msg_type = data.get("type")
        text = data.get("text", "") or ""

        latency_fields = calculate_latency_fields(
            data=data,
            client_receive_ts_ms=client_receive_ts_ms,
            timing_holder=timing_holder,
        )

        latency_ms = latency_fields["latency_ms"]
        ttfb_ms = latency_fields["ttfb_ms"]
        ttft_ms = latency_fields["ttft_ms"]
        session_ttfb_ms = latency_fields["session_ttfb_ms"]
        session_ttft_ms = latency_fields["session_ttft_ms"]

        if msg_type in {
            "audio_received",
            "partial",
            "utterance_final",
            "language_switch",
            "final",
        }:
            result["event_metrics"].append(
                {
                    "type": msg_type,
                    "language": data.get("language"),
                    "latency_ms": latency_ms,
                    "ttfb_ms": ttfb_ms,
                    "ttft_ms": ttft_ms,
                    "session_ttfb_ms": session_ttfb_ms,
                    "session_ttft_ms": session_ttft_ms,
                    "server_elapsed_ms": data.get("server_elapsed_ms"),
                    "client_receive_ts_ms": round(client_receive_ts_ms, 3),
                    "server_send_ts_ms": data.get("server_send_ts_ms"),
                    "server_audio_received_ts_ms": data.get(
                        "server_audio_received_ts_ms"
                    ),
                    "utterance_start_ts_ms": data.get("utterance_start_ts_ms"),
                    "lid_confidence": data.get("lid_confidence"),
                    "lid_label": data.get("lid_label"),
                    "text": text,
                }
            )

        if msg_type in {"ready", "loading", "config_ack"}:
            print(data)

        elif msg_type == "audio_received":
            print(
                f"AUDIO_RECEIVED "
                f"latency_ms={latency_ms} "
                f"ttfb_ms={ttfb_ms} "
                f"ttft_ms={ttft_ms} "
                f"session_ttfb_ms={session_ttfb_ms} "
                f"session_ttft_ms={session_ttft_ms} "
                f"server_elapsed_ms={data.get('server_elapsed_ms')}"
            )

        elif msg_type == "partial":
            if text:
                result["partials"].append(text)

                if result["asr_confidence"] is None:
                    result["asr_confidence"] = data.get("asr_confidence")

            print(
                f"PARTIAL [{data.get('language')}] "
                f"latency_ms={latency_ms} "
                f"ttfb_ms={ttfb_ms} "
                f"ttft_ms={ttft_ms} "
                f"session_ttfb_ms={session_ttfb_ms} "
                f"session_ttft_ms={session_ttft_ms} "
                f"server_elapsed_ms={data.get('server_elapsed_ms')} "
                f"conf={data.get('asr_confidence')} : "
                f"{text}"
            )

        elif msg_type == "utterance_final":
            result["utterance_finals"].append(text)

            lid_conf = data.get("lid_confidence")
            lid_label = data.get("lid_label")

            if lid_conf is not None:
                result["lid_confidences"].append(lid_conf)
                result["last_lid_confidence"] = lid_conf

            if lid_label is not None:
                result["last_lid_label"] = lid_label

            print(
                f"\nUTTERANCE_FINAL [{data.get('language')}] "
                f"latency_ms={latency_ms} "
                f"ttfb_ms={ttfb_ms} "
                f"ttft_ms={ttft_ms} "
                f"session_ttfb_ms={session_ttfb_ms} "
                f"session_ttft_ms={session_ttft_ms} "
                f"server_elapsed_ms={data.get('server_elapsed_ms')} "
                f"lid_conf={lid_conf} "
                f"lid_label={lid_label} : "
                f"{text}"
            )

        elif msg_type == "language_switch":
            result["language_switches"].append(data)

            print(
                f"\nLANGUAGE_SWITCH "
                f"{data.get('language')} -> {data.get('detected_language')} "
                f"latency_ms={latency_ms} "
                f"ttfb_ms={ttfb_ms} "
                f"ttft_ms={ttft_ms} "
                f"session_ttfb_ms={session_ttfb_ms} "
                f"session_ttft_ms={session_ttft_ms} "
                f"lid_conf={data.get('lid_confidence')} "
                f"lid_label={data.get('lid_label')}"
            )

        elif msg_type == "final":
            result["final_text"] = text
            result["final_latency_ms"] = latency_ms
            result["server_final_elapsed_ms"] = data.get("server_elapsed_ms")

            print(
                f"\nFINAL [{data.get('language')}] "
                f"latency_ms={latency_ms} "
                f"ttfb_ms={ttfb_ms} "
                f"ttft_ms={ttft_ms} "
                f"session_ttfb_ms={session_ttfb_ms} "
                f"session_ttft_ms={session_ttft_ms} "
                f"server_elapsed_ms={data.get('server_elapsed_ms')} "
                f"conf={data.get('asr_confidence')} : "
                f"{text}"
            )

            if data.get("stream_end", True):
                break

        elif msg_type == "error":
            print(f"ERROR: {data.get('message')}")

        else:
            print(data)

    result["session_ttfb_ms"] = timing_holder.get("session_ttfb_ms")
    result["session_ttft_ms"] = timing_holder.get("session_ttft_ms")
    result["first_response_type"] = timing_holder.get("first_response_type")
    result["first_text_type"] = timing_holder.get("first_text_type")

    return result


async def send_config(ws, language: str):
    await ws.send(
        json.dumps(
            {
                "type": "config",
                "language": language,
                "sample_rate": TARGET_SAMPLE_RATE,
            }
        )
    )


async def run_file(
    url: str,
    file_path: str,
    language: str,
    chunk_ms: int,
    reference_path: Optional[str] = None,
):
    audio_bytes = read_wav_as_pcm16(file_path)

    bytes_per_chunk = int(TARGET_SAMPLE_RATE * 2 * chunk_ms / 1000)
    audio_duration_sec = len(audio_bytes) / (TARGET_SAMPLE_RATE * 2)

    client_start = time.time()
    first_audio_send_time = None
    last_audio_send_time = None

    timing_holder = {
        "first_audio_send_ts_ms": None,
        "session_ttfb_ms": None,
        "session_ttft_ms": None,
        "first_response_type": None,
        "first_text_type": None,
    }

    async with websockets.connect(
        url,
        max_size=None,
        ping_interval=20,
        ping_timeout=120,
        open_timeout=300,
    ) as ws:
        await send_config(ws, language)

        recv_task = asyncio.create_task(
            receiver(
                ws,
                timing_holder,
            )
        )

        for i in range(0, len(audio_bytes), bytes_per_chunk):
            now = time.time()

            if first_audio_send_time is None:
                first_audio_send_time = now
                timing_holder["first_audio_send_ts_ms"] = now * 1000.0

            chunk = audio_bytes[i : i + bytes_per_chunk]
            await ws.send(chunk)

            last_audio_send_time = time.time()

            await asyncio.sleep(chunk_ms / 1000)

        await ws.send(json.dumps({"type": "end"}))

        receive_result = await recv_task

    client_end = time.time()

    total_client_elapsed_sec = client_end - client_start

    streaming_elapsed_sec = (
        last_audio_send_time - first_audio_send_time
        if first_audio_send_time and last_audio_send_time
        else None
    )

    real_time_factor = (
        total_client_elapsed_sec / audio_duration_sec
        if audio_duration_sec > 0
        else None
    )

    lid_confidences = receive_result.get("lid_confidences", [])

    avg_lid_confidence = (
        round(sum(lid_confidences) / len(lid_confidences), 4)
        if lid_confidences
        else None
    )

    final_text = receive_result.get("final_text", "")

    metrics = {
        "file": file_path,
        "language": language,
        "chunk_ms": chunk_ms,

        "audio_duration_sec": round(audio_duration_sec, 3),
        "client_total_elapsed_sec": round(total_client_elapsed_sec, 3),
        "streaming_elapsed_sec": round(streaming_elapsed_sec, 3)
        if streaming_elapsed_sec is not None
        else None,
        "real_time_factor": round(real_time_factor, 3)
        if real_time_factor is not None
        else None,

        "session_ttfb_ms": receive_result.get("session_ttfb_ms"),
        "session_ttft_ms": receive_result.get("session_ttft_ms"),
        "first_response_type": receive_result.get("first_response_type"),
        "first_text_type": receive_result.get("first_text_type"),

        "final_latency_ms": receive_result.get("final_latency_ms"),
        "server_final_elapsed_ms": receive_result.get("server_final_elapsed_ms"),

        "event_metrics": receive_result.get("event_metrics", []),

        "asr_confidence": receive_result.get("asr_confidence"),

        "last_lid_confidence": receive_result.get("last_lid_confidence"),
        "avg_lid_confidence": avg_lid_confidence,
        "last_lid_label": receive_result.get("last_lid_label"),

        "partial_count": len(receive_result.get("partials", [])),
        "utterance_count": len(receive_result.get("utterance_finals", [])),
        "language_switch_count": len(receive_result.get("language_switches", [])),

        "final_text": final_text,
    }

    if reference_path:
        reference_file = Path(reference_path)

        if reference_file.exists():
            reference_text = reference_file.read_text(encoding="utf-8")
            metrics.update(calculate_asr_metrics(reference_text, final_text))
        else:
            metrics.update(
                none_wer_metrics(
                    final_text=final_text,
                    error_message=f"Reference file not found: {reference_path}",
                )
            )
    else:
        metrics.update(
            none_wer_metrics(
                final_text=final_text,
                error_message="No reference transcript provided",
            )
        )

    print("\n" + "=" * 80)
    print("ASR BENCHMARK RESULT")
    print("=" * 80)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print("=" * 80)

    output_path = Path(file_path).with_suffix(".metrics.json")
    output_path.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nSaved metrics to: {output_path}")

    return metrics


async def run_mic(
    url: str,
    language: str,
    chunk_ms: int,
    device_index: Optional[int],
):
    try:
        import pyaudio
    except ImportError as exc:
        raise ImportError(
            "Install PyAudio locally for mic mode: pip install pyaudio"
        ) from exc

    pa = pyaudio.PyAudio()
    frames_per_buffer = int(TARGET_SAMPLE_RATE * chunk_ms / 1000)

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=TARGET_SAMPLE_RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=frames_per_buffer,
    )

    timing_holder = {
        "first_audio_send_ts_ms": None,
        "session_ttfb_ms": None,
        "session_ttft_ms": None,
        "first_response_type": None,
        "first_text_type": None,
    }

    print("Mic streaming started. Press Ctrl+C to stop.")

    async with websockets.connect(
        url,
        max_size=None,
        ping_interval=20,
        ping_timeout=120,
        open_timeout=300,
    ) as ws:
        await send_config(ws, language)

        recv_task = asyncio.create_task(
            receiver(
                ws,
                timing_holder,
            )
        )

        try:
            while True:
                data = stream.read(
                    frames_per_buffer,
                    exception_on_overflow=False,
                )

                now = time.time()

                if timing_holder["first_audio_send_ts_ms"] is None:
                    timing_holder["first_audio_send_ts_ms"] = now * 1000.0

                await ws.send(data)
                await asyncio.sleep(0)

        except KeyboardInterrupt:
            await ws.send(json.dumps({"type": "end"}))
            await recv_task

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        default="ws://127.0.0.1:8002/asr/ws",
    )

    parser.add_argument(
        "--mode",
        choices=["file", "mic"],
        default="file",
    )

    parser.add_argument(
        "--file",
        help="Path to PCM16 WAV file for file mode",
    )

    parser.add_argument(
        "--reference",
        help="Optional path to human reference transcript .txt file for WER/CER",
    )

    parser.add_argument(
        "--language",
        choices=["en", "es"],
        default="en",
    )

    parser.add_argument(
        "--chunk-ms",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--device-index",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    if args.mode == "file":
        if not args.file:
            raise ValueError("--file is required when --mode file")

        asyncio.run(
            run_file(
                url=args.url,
                file_path=args.file,
                language=args.language,
                chunk_ms=args.chunk_ms,
                reference_path=args.reference,
            )
        )

    else:
        asyncio.run(
            run_mic(
                url=args.url,
                language=args.language,
                chunk_ms=args.chunk_ms,
                device_index=args.device_index,
            )
        )


if __name__ == "__main__":
    main()
