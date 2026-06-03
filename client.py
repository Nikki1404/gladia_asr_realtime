import argparse
import asyncio
import json
import wave
from pathlib import Path
from typing import Optional

import numpy as np
import websockets
from scipy.signal import resample_poly

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
        audio = np.clip(audio_f32 * 32767, -32768, 32767).astype(np.int16)

    return audio.tobytes()


async def receiver(ws):
    async for message in ws:
        data = json.loads(message)
        msg_type = data.get("type")

        if msg_type == "partial":
            print(f"PARTIAL [{data.get('language')}]: {data.get('text')}")

        elif msg_type == "final":
            print(f"\nFINAL [{data.get('language')}]: {data.get('text')}")
            break

        elif msg_type == "error":
            print(f"ERROR: {data.get('message')}")

        else:
            print(data)


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


async def run_file(url: str, file_path: str, language: str, chunk_ms: int):
    audio_bytes = read_wav_as_pcm16(file_path)
    bytes_per_chunk = int(TARGET_SAMPLE_RATE * 2 * chunk_ms / 1000)

    async with websockets.connect(url, max_size=None, ping_interval=20, ping_timeout=120) as ws:
        await send_config(ws, language)
        recv_task = asyncio.create_task(receiver(ws))

        for i in range(0, len(audio_bytes), bytes_per_chunk):
            chunk = audio_bytes[i : i + bytes_per_chunk]
            await ws.send(chunk)

            # Makes file streaming behave like realtime mic streaming.
            await asyncio.sleep(chunk_ms / 1000)

        await ws.send(json.dumps({"type": "end"}))
        await recv_task


async def run_mic(url: str, language: str, chunk_ms: int, device_index: Optional[int]):
    try:
        import pyaudio
    except ImportError as exc:
        raise ImportError("Install PyAudio locally for mic mode: pip install pyaudio") from exc

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

    async with websockets.connect(url, max_size=None, ping_interval=20, ping_timeout=120) as ws:
        await send_config(ws, language)
        recv_task = asyncio.create_task(receiver(ws))

        try:
            while True:
                data = stream.read(frames_per_buffer, exception_on_overflow=False)
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
    parser.add_argument("--url", default="ws://127.0.0.1:8004/asr/ws")
    parser.add_argument("--mode", choices=["file", "mic"], default="file")
    parser.add_argument("--file", help="Path to PCM16 WAV file for file mode")
    parser.add_argument("--language", choices=["en", "es"], default="en")
    parser.add_argument("--chunk-ms", type=int, default=30)
    parser.add_argument("--device-index", type=int, default=None)
    args = parser.parse_args()

    if args.mode == "file":
        if not args.file:
            raise ValueError("--file is required when --mode file")
        asyncio.run(run_file(args.url, args.file, args.language, args.chunk_ms))
    else:
        asyncio.run(run_mic(args.url, args.language, args.chunk_ms, args.device_index))


if __name__ == "__main__":
    main()
