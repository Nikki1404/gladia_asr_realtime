import json
import time
import uuid
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.asr import ASRManager
from app.audio_utils import pcm16_bytes_to_float32
from app.config import DEFAULT_LANGUAGE, SAMPLE_RATE, SUPPORTED_LANGUAGES

app = FastAPI(title="Simple Multilingual ASR Router")
asr_manager = ASRManager()


@app.get("/")
def root():
    return {
        "message": "Simple Multilingual ASR Router",
        "websocket": "/asr/ml/ws",
        "sample_rate": SAMPLE_RATE,
        "supported_languages": SUPPORTED_LANGUAGES,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/languages")
def languages():
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "default_language": DEFAULT_LANGUAGE,
    }


@app.websocket("/asr/ws")
async def websocket_asr(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    language = DEFAULT_LANGUAGE
    asr = asr_manager.create_session(language)

    start_time = time.time()
    first_partial_time: Optional[float] = None

    print(f"[{session_id}] connected language={language}", flush=True)

    await websocket.send_text(
        json.dumps(
            {
                "type": "ready",
                "session_id": session_id,
                "language": language,
                "sample_rate": SAMPLE_RATE,
            }
        )
    )

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type")

                if msg_type == "config":
                    requested_language = data.get("language", DEFAULT_LANGUAGE)

                    if requested_language not in SUPPORTED_LANGUAGES:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": f"Unsupported language: {requested_language}",
                                    "supported_languages": SUPPORTED_LANGUAGES,
                                }
                            )
                        )
                        continue

                    language = requested_language
                    asr = asr_manager.create_session(language)
                    start_time = time.time()
                    first_partial_time = None

                    print(f"[{session_id}] config language={language}", flush=True)

                    await websocket.send_text(
                        json.dumps({"type": "config_ack", "language": language})
                    )

                elif msg_type == "end":
                    final_text = asr.finalize()
                    elapsed_ms = round((time.time() - start_time) * 1000, 2)

                    print(f"[{session_id}] FINAL [{language}]: {final_text}", flush=True)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "final",
                                "language": language,
                                "text": final_text,
                                "elapsed_ms": elapsed_ms,
                            }
                        )
                    )
                    break

            elif "bytes" in message:
                audio = pcm16_bytes_to_float32(message["bytes"])
                partial_text = asr.accept_audio(audio)

                if partial_text:
                    now = time.time()

                    if first_partial_time is None:
                        first_partial_time = now

                    ttfb_ms = round((first_partial_time - start_time) * 1000, 2)
                    elapsed_ms = round((now - start_time) * 1000, 2)

                    print(f"[{session_id}] PARTIAL [{language}]: {partial_text}", flush=True)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "partial",
                                "language": language,
                                "text": partial_text,
                                "ttfb_ms": ttfb_ms,
                                "elapsed_ms": elapsed_ms,
                            }
                        )
                    )

    except WebSocketDisconnect:
        print(f"[{session_id}] disconnected", flush=True)

    except Exception as exc:
        print(f"[{session_id}] ERROR: {exc}", flush=True)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            pass
