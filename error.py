from livekit.plugins import openai
stt=openai.STT(
        model="nemotron-3.5-asr-streaming-0.6b",
        base_url="http://localhost:8000/v1",
        api_key="unused",
        language="es-US",   # or omit for auto-detect
    )

following this 
and this is my current working client 

        #!/usr/bin/env python3
"""
client.py — Test client for the Nemotron 3.5 ASR WebSocket server.

Modes:
  1. Microphone (real-time)  →  python client.py --mic
  2. WAV file                →  python client.py --file audio.wav
  3. WAV file (simulated RT) →  python client.py --file audio.wav --realtime

Language:
  --language en-US   (default)
  --language es-US   (Spanish US)
  --language auto    (model auto-detects)

Usage examples:
  python client.py --mic
  python client.py --mic --language es-US
  python client.py --file speech.wav
  python client.py --file speech_es.wav --language es-US
  python client.py --file speech.wav --realtime --language auto
"""

import argparse
import asyncio
import json
import re
import sys
import time
import wave
from pathlib import Path

import websockets

# ── Config ────────────────────────────────────────────────────────────────────
SERVER_URL = "ws://35.254.200.29:8003/asr/realtime-custom-vad"
SAMPLE_RATE = 16000
CHUNK_MS = 100
CHUNK_BYTES = int(SAMPLE_RATE * CHUNK_MS / 1000) * 2   # int16 = 2 bytes/sample

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

# ── Strip language tags like <en-US>, <es-US> that leak from model prompt ─────
_LANG_TAG_RE = re.compile(r"<[a-z]{2}-[A-Z]{2}>\s*")

def clean_text(text: str) -> str:
    return _LANG_TAG_RE.sub("", text).strip()


def print_partial(text: str):
    sys.stdout.write(f"\r{YELLOW}[partial]{RESET} {text}    ")
    sys.stdout.flush()


def print_final(text: str, ttfb_ms):
    ttfb_str = f"  {DIM}(TTFB {ttfb_ms}ms){RESET}" if ttfb_ms else ""
    sys.stdout.write(f"\r{GREEN}{BOLD}[final]  {RESET}{GREEN}{text}{RESET}{ttfb_str}\n")
    sys.stdout.flush()


def print_info(msg: str):
    print(f"{CYAN}[info]{RESET} {msg}")


# ── WebSocket receiver (runs concurrently) ────────────────────────────────────
async def receive_loop(ws, stop_event: asyncio.Event):
    """Print incoming transcript events until stop_event is set."""
    try:
        async for raw in ws:
            if isinstance(raw, bytes):
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            ev_type = msg.get("type", "")
            text    = clean_text(msg.get("text", ""))
            ttfb    = msg.get("t_start")

            if ev_type == "done":
                # Server confirmed EOF flush is complete
                stop_event.set()
                break
            elif ev_type == "partial":
                print_partial(text)
            elif ev_type == "final":
                print_final(text, ttfb)
            elif ev_type == "error":
                print(f"\n[server error] {text}")

    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as e:
        print(f"\n[receive error] {e}")
    finally:
        stop_event.set()


# ── Microphone mode ───────────────────────────────────────────────────────────
async def run_mic(language: str, url: str):
    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice not installed. Run:  pip install sounddevice")
        sys.exit(1)

    print_info(f"Connecting to {url}")
    print_info(f"Language: {language}")
    print_info("Speak into your microphone. Press Ctrl+C to stop.\n")

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "backend":     "nemotron",
            "sample_rate": SAMPLE_RATE,
            "language":    language,
        }))

        stop_event = asyncio.Event()
        recv_task = asyncio.create_task(receive_loop(ws, stop_event))

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def audio_callback(indata, frames, time_info, status):
            import numpy as np
            pcm = (indata[:, 0] * 32767).astype("int16").tobytes()
            loop.call_soon_threadsafe(queue.put_nowait, pcm)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=int(SAMPLE_RATE * CHUNK_MS / 1000),
            callback=audio_callback,
        ):
            try:
                while not stop_event.is_set():
                    try:
                        pcm = await asyncio.wait_for(queue.get(), timeout=0.5)
                        await ws.send(pcm)
                    except asyncio.TimeoutError:
                        continue
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\n")
                print_info("Stopping...")

        recv_task.cancel()
        try:
            await recv_task
        except asyncio.CancelledError:
            pass


# ── WAV file mode ─────────────────────────────────────────────────────────────
async def run_file(path: str, language: str, realtime: bool, url: str):
    wav_path = Path(path)
    if not wav_path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    with wave.open(str(wav_path), "rb") as wf:
        n_channels   = wf.getnchannels()
        sample_width = wf.getsampwidth()
        file_sr      = wf.getframerate()
        n_frames     = wf.getnframes()
        raw_audio    = wf.readframes(n_frames)

    print_info(f"File: {wav_path.name}")
    print_info(f"Audio: {file_sr}Hz  {n_channels}ch  {sample_width*8}bit  "
               f"{n_frames/file_sr:.1f}s")
    print_info(f"Language: {language}")
    print_info(f"Realtime simulation: {realtime}")
    print_info(f"Connecting to {url}\n")

    import numpy as np
    audio_i16 = np.frombuffer(raw_audio, dtype=np.int16)
    if n_channels == 2:
        audio_i16 = audio_i16.reshape(-1, 2).mean(axis=1).astype(np.int16)

    if file_sr != SAMPLE_RATE:
        print_info(f"Resampling {file_sr}Hz → {SAMPLE_RATE}Hz")
        try:
            import resampy
        except ImportError:
            print("resampy not installed. Run:  pip install resampy")
            sys.exit(1)
        audio_f32 = audio_i16.astype(np.float32) / 32768.0
        audio_f32 = resampy.resample(audio_f32, file_sr, SAMPLE_RATE)
        audio_i16 = (np.clip(audio_f32, -1.0, 1.0) * 32767).astype(np.int16)

    raw_bytes = audio_i16.tobytes()
    chunk_samples = int(SAMPLE_RATE * CHUNK_MS / 1000)
    chunk_bytes   = chunk_samples * 2
    chunks = [raw_bytes[i:i + chunk_bytes] for i in range(0, len(raw_bytes), chunk_bytes)]

    t_start = time.time()

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({
            "backend":     "nemotron",
            "sample_rate": SAMPLE_RATE,
            "language":    language,
        }))

        stop_event = asyncio.Event()
        recv_task  = asyncio.create_task(receive_loop(ws, stop_event))

        try:
            for i, chunk in enumerate(chunks):
                await ws.send(chunk)

                if realtime:
                    expected_elapsed = (i + 1) * CHUNK_MS / 1000.0
                    actual_elapsed   = time.time() - t_start
                    sleep_for = expected_elapsed - actual_elapsed
                    if sleep_for > 0:
                        await asyncio.sleep(sleep_for)
                else:
                    await asyncio.sleep(0.001)

        except (KeyboardInterrupt, asyncio.CancelledError):
            pass

        # Send EOF so server flushes the last in-progress utterance
        print_info("\nAll audio sent — sending EOF signal...")
        await ws.send(json.dumps({"type": "eof"}))

        # Wait for server to reply with {"type": "done"}
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=15.0)
        except asyncio.TimeoutError:
            print_info("Timeout waiting for server — last utterance may be incomplete")

        recv_task.cancel()
        try:
            await recv_task
        except asyncio.CancelledError:
            pass

    elapsed = time.time() - t_start
    audio_sec = len(audio_i16) / SAMPLE_RATE
    rtf = elapsed / audio_sec if audio_sec > 0 else 0
    print_info(f"\nDone. Audio={audio_sec:.1f}s  Wall={elapsed:.2f}s  RTF={rtf:.2f}x")


# ── Health check ──────────────────────────────────────────────────────────────
async def check_health(host: str = "http://localhost:8002"):
    try:
        import urllib.request
        with urllib.request.urlopen(f"{host}/health", timeout=3) as r:
            data = json.loads(r.read())
        print_info(f"Server health: {data}")
        return True
    except Exception as e:
        print(f"[warn] Health check failed: {e}  (server may still be starting)")
        return False


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Nemotron 3.5 ASR WebSocket test client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--mic",  action="store_true", help="Use microphone input")
    mode.add_argument("--file", metavar="PATH",      help="Transcribe a WAV file")

    parser.add_argument(
        "--language",
        default="en-US",
        help=(
            "Language locale. Examples: en-US, en-GB, es-US, es-ES, "
            "fr-FR, de-DE, hi-IN, ja-JP, auto. Default: en-US"
        ),
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="(file mode) Simulate real-time pacing",
    )
    parser.add_argument(
        "--url",
        default=SERVER_URL,
        help=f"WebSocket URL. Default: {SERVER_URL}",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Just check server health and exit",
    )

    args = parser.parse_args()

    http_host = args.url.replace("ws://", "http://").replace("wss://", "https://")
    http_host = http_host.rsplit("/", 1)[0]

    if args.health:
        asyncio.run(check_health(http_host))
        return

    asyncio.run(check_health(http_host))

    if args.mic:
        asyncio.run(run_mic(language=args.language, url=args.url))
    else:
        asyncio.run(
            run_file(
                path=args.file,
                language=args.language,
                realtime=args.realtime,
                url=args.url,
            )
        )


if __name__ == "__main__":
    main()
