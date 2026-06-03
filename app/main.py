import json
import time
import uuid
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.asr import ASRManager
from app.audio_utils import pcm16_bytes_to_float32
from app.config import DEFAULT_LANGUAGE, SAMPLE_RATE, SUPPORTED_LANGUAGES
from app.router import MultilingualASRRouterSession, RouterOutput

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


def router_output_to_payload(
    output: RouterOutput,
    session_id: str,
) -> dict:
    payload = {
        "type": output.type,
        "session_id": session_id,
        "language": output.language,
        "text": output.text,
    }

    if output.detected_language is not None:
        payload["detected_language"] = output.detected_language

    if output.lid_confidence is not None:
        payload["lid_confidence"] = output.lid_confidence

    if output.lid_label is not None:
        payload["lid_label"] = output.lid_label

    if output.ttfb_ms is not None:
        payload["ttfb_ms"] = round(output.ttfb_ms, 2)

    if output.elapsed_ms is not None:
        payload["elapsed_ms"] = round(output.elapsed_ms, 2)

    return payload


@app.websocket("/asr/ws")
async def websocket_asr(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    language = DEFAULT_LANGUAGE

    router = MultilingualASRRouterSession(
        asr_manager=asr_manager,
        initial_language=language,
    )

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

            if "text" in message and message["text"] is not None:
                data = json.loads(message["text"])
                msg_type = data.get("type")

                if msg_type == "config":
                    requested_language = data.get("language", DEFAULT_LANGUAGE)

                    if requested_language not in SUPPORTED_LANGUAGES:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "session_id": session_id,
                                    "message": f"Unsupported language: {requested_language}",
                                    "supported_languages": SUPPORTED_LANGUAGES,
                                }
                            )
                        )
                        continue

                    language = requested_language

                    router = MultilingualASRRouterSession(
                        asr_manager=asr_manager,
                        initial_language=language,
                    )

                    start_time = time.time()
                    first_partial_time = None

                    print(f"[{session_id}] config language={language}", flush=True)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "config_ack",
                                "session_id": session_id,
                                "language": language,
                            }
                        )
                    )

                elif msg_type == "end":
                    outputs = router.finalize_stream()
                    elapsed_ms = round((time.time() - start_time) * 1000, 2)

                    final_text = ""

                    for output in outputs:
                        payload = router_output_to_payload(
                            output=output,
                            session_id=session_id,
                        )

                        if output.type == "final":
                            payload["elapsed_ms"] = elapsed_ms
                            final_text = output.text

                        await websocket.send_text(json.dumps(payload))

                    print(
                        f"[{session_id}] FINAL [{router.current_language}]: {final_text}",
                        flush=True,
                    )

                    break

                elif msg_type == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "pong",
                                "session_id": session_id,
                            }
                        )
                    )

            elif "bytes" in message and message["bytes"] is not None:
                audio = pcm16_bytes_to_float32(message["bytes"])

                outputs = router.accept_audio(audio)

                for output in outputs:
                    if output.type == "partial":
                        now = time.time()

                        if first_partial_time is None:
                            first_partial_time = now

                        ttfb_ms = round((first_partial_time - start_time) * 1000, 2)
                        elapsed_ms = round((now - start_time) * 1000, 2)

                        print(
                            f"[{session_id}] PARTIAL [{output.language}]: {output.text}",
                            flush=True,
                        )

                        payload = router_output_to_payload(
                            output=output,
                            session_id=session_id,
                        )

                        payload["ttfb_ms"] = ttfb_ms
                        payload["elapsed_ms"] = elapsed_ms

                        await websocket.send_text(json.dumps(payload))

                    elif output.type == "language_switch":
                        print(
                            f"[{session_id}] LANGUAGE_SWITCH "
                            f"{output.language} -> {output.detected_language} "
                            f"conf={output.lid_confidence} "
                            f"label={output.lid_label}",
                            flush=True,
                        )

                        await websocket.send_text(
                            json.dumps(
                                router_output_to_payload(
                                    output=output,
                                    session_id=session_id,
                                )
                            )
                        )

                    elif output.type == "utterance_final":
                        print(
                            f"[{session_id}] UTTERANCE_FINAL "
                            f"[{output.language}]: {output.text}",
                            flush=True,
                        )

                        await websocket.send_text(
                            json.dumps(
                                router_output_to_payload(
                                    output=output,
                                    session_id=session_id,
                                )
                            )
                        )

    except WebSocketDisconnect:
        print(f"[{session_id}] disconnected", flush=True)

    except Exception as exc:
        print(f"[{session_id}] ERROR: {exc}", flush=True)

        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "session_id": session_id,
                        "message": str(exc),
                    }
                )
            )
        except Exception:
            pass

