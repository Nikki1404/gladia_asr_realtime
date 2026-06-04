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


async def receiver(ws) -> dict:
    result = {
        "partials": [],
        "utterance_finals": [],
        "language_switches": [],
        "final_text": "",
        "server_ttfb_ms": None,
        "server_ttft_ms": None,
        "server_final_elapsed_ms": None,
        "asr_confidence": None,
        "lid_confidences": [],
        "last_lid_confidence": None,
        "last_lid_label": None,
    }

    async for message in ws:
        data = json.loads(message)
        msg_type = data.get("type")

        if msg_type in {"ready", "loading", "config_ack"}:
            print(data)

        elif msg_type == "partial":
            text = data.get("text", "")

            if text:
                result["partials"].append(text)

                if result["server_ttfb_ms"] is None:
                    result["server_ttfb_ms"] = data.get("ttfb_ms")

                if result["server_ttft_ms"] is None:
                    result["server_ttft_ms"] = data.get("ttft_ms")

                if result["asr_confidence"] is None:
                    result["asr_confidence"] = data.get("asr_confidence")

            print(
                f"PARTIAL [{data.get('language')}] "
                f"ttfb={data.get('ttfb_ms')}ms "
                f"ttft={data.get('ttft_ms')}ms "
                f"conf={data.get('asr_confidence')} : "
                f"{text}"
            )

        elif msg_type == "utterance_final":
            text = data.get("text", "")
            result["utterance_finals"].append(text)

            lid_conf = data.get("lid_confidence")
            lid_label = data.get("lid_label")

            if lid_conf is not None:
                result["lid_confidences"].append(lid_conf)
                result["last_lid_confidence"] = lid_conf

            if lid_label is not None:
                result["last_lid_label"] = lid_label

            if result["server_ttfb_ms"] is None:
                result["server_ttfb_ms"] = data.get("ttfb_ms")

            if result["server_ttft_ms"] is None:
                result["server_ttft_ms"] = data.get("ttft_ms")

            print(
                f"\nUTTERANCE_FINAL [{data.get('language')}] "
                f"ttfb={data.get('ttfb_ms')}ms "
                f"ttft={data.get('ttft_ms')}ms "
                f"lid_conf={lid_conf} "
                f"lid_label={lid_label} : "
                f"{text}"
            )

        elif msg_type == "language_switch":
            result["language_switches"].append(data)

            print(
                f"\nLANGUAGE_SWITCH "
                f"{data.get('language')} -> {data.get('detected_language')} "
                f"ttfb={data.get('ttfb_ms')}ms "
                f"ttft={data.get('ttft_ms')}ms "
                f"conf={data.get('lid_confidence')} "
                f"label={data.get('lid_label')}"
            )

            if data.get("text"):
                print(
                    f"REVISION [{data.get('detected_language')}]: "
                    f"{data.get('text')}"
                )

        elif msg_type == "final":
            final_text = data.get("text", "")
            result["final_text"] = final_text
            result["server_final_elapsed_ms"] = data.get("elapsed_ms")

            if result["server_ttfb_ms"] is None:
                result["server_ttfb_ms"] = data.get("ttfb_ms")

            if result["server_ttft_ms"] is None:
                result["server_ttft_ms"] = data.get("ttft_ms")

            print(
                f"\nFINAL [{data.get('language')}] "
                f"ttfb={data.get('ttfb_ms')}ms "
                f"ttft={data.get('ttft_ms')}ms "
                f"elapsed={data.get('elapsed_ms')}ms "
                f"conf={data.get('asr_confidence')} : "
                f"{final_text}"
            )

            if data.get("stream_end", True):
                break

        elif msg_type == "error":
            print(f"ERROR: {data.get('message')}")

        else:
            print(data)

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

    async with websockets.connect(
        url,
        max_size=None,
        ping_interval=20,
        ping_timeout=120,
        open_timeout=300,
    ) as ws:
        await send_config(ws, language)

        recv_task = asyncio.create_task(receiver(ws))

        for i in range(0, len(audio_bytes), bytes_per_chunk):
            if first_audio_send_time is None:
                first_audio_send_time = time.time()

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
        "server_ttfb_ms": receive_result.get("server_ttfb_ms"),
        "server_ttft_ms": receive_result.get("server_ttft_ms"),
        "server_final_elapsed_ms": receive_result.get("server_final_elapsed_ms"),
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

    print("Mic streaming started. Press Ctrl+C to stop.")

    async with websockets.connect(
        url,
        max_size=None,
        ping_interval=20,
        ping_timeout=120,
        open_timeout=300,
    ) as ws:
        await send_config(ws, language)

        recv_task = asyncio.create_task(receiver(ws))

        try:
            while True:
                data = stream.read(
                    frames_per_buffer,
                    exception_on_overflow=False,
                )

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
