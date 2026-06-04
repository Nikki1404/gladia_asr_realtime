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


def router_output_to_payload(output: RouterOutput, session_id: str) -> dict:
    payload = {
        "type": output.type,
        "session_id": session_id,
        "language": output.language,
        "text": output.text,

        # Refreshed again immediately before send.
        "server_send_ts_ms": time.time() * 1000.0,

        # Used by client to calculate per-event TTFB.
        "server_audio_received_ts_ms": output.server_audio_received_ts_ms,

        # Used by client to calculate per-event TTFT.
        "utterance_start_ts_ms": output.utterance_start_ts_ms,

        "server_elapsed_ms": (
            round(output.server_elapsed_ms, 2)
            if output.server_elapsed_ms is not None
            else None
        ),
    }

    if output.detected_language is not None:
        payload["detected_language"] = output.detected_language

    if output.lid_confidence is not None:
        payload["lid_confidence"] = round(output.lid_confidence, 4)
        payload["conf"] = round(output.lid_confidence, 4)

    if output.lid_label is not None:
        payload["lid_label"] = output.lid_label

    payload["asr_confidence"] = (
        round(output.asr_confidence, 4)
        if output.asr_confidence is not None
        else None
    )

    return payload


async def send_payload(websocket: WebSocket, payload: dict) -> None:
    # Critical: update timestamp immediately before sending to client.
    payload["server_send_ts_ms"] = time.time() * 1000.0
    await websocket.send_text(json.dumps(payload))


def create_router(session_id: str, language: str) -> MultilingualASRRouterSession:
    print(f"[{session_id}] loading router language={language}", flush=True)

    router = MultilingualASRRouterSession(
        asr_manager=asr_manager,
        initial_language=language,
    )

    print(f"[{session_id}] router loaded language={language}", flush=True)
    return router


@app.websocket("/asr/ws")
async def websocket_asr(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    language = DEFAULT_LANGUAGE
    router: Optional[MultilingualASRRouterSession] = None

    print(f"[{session_id}] connected language={language}", flush=True)

    await send_payload(
        websocket,
        {
            "type": "ready",
            "session_id": session_id,
            "language": language,
            "sample_rate": SAMPLE_RATE,
            "text": "",
            "message": "WebSocket connected. Send config first, then PCM16 audio bytes.",
        },
    )

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                print(f"[{session_id}] disconnect message received", flush=True)
                break

            if "text" in message and message["text"] is not None:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    await send_payload(
                        websocket,
                        {
                            "type": "error",
                            "session_id": session_id,
                            "language": language,
                            "text": "",
                            "message": "Invalid JSON message",
                        },
                    )
                    continue

                msg_type = data.get("type")

                if msg_type == "config":
                    requested_language = data.get("language", DEFAULT_LANGUAGE)

                    if requested_language not in SUPPORTED_LANGUAGES:
                        await send_payload(
                            websocket,
                            {
                                "type": "error",
                                "session_id": session_id,
                                "language": language,
                                "text": "",
                                "message": f"Unsupported language: {requested_language}",
                                "supported_languages": SUPPORTED_LANGUAGES,
                            },
                        )
                        continue

                    language = requested_language

                    print(f"[{session_id}] config language={language}", flush=True)

                    await send_payload(
                        websocket,
                        {
                            "type": "loading",
                            "session_id": session_id,
                            "language": language,
                            "text": "",
                            "message": "Loading ASR router, Silero VAD, and SpeechBrain LID",
                        },
                    )

                    router = create_router(session_id=session_id, language=language)

                    await send_payload(
                        websocket,
                        {
                            "type": "config_ack",
                            "session_id": session_id,
                            "language": language,
                            "sample_rate": SAMPLE_RATE,
                            "text": "",
                        },
                    )

                elif msg_type == "end":
                    if router is None:
                        await send_payload(
                            websocket,
                            {
                                "type": "final",
                                "session_id": session_id,
                                "language": language,
                                "text": "",
                                "server_audio_received_ts_ms": None,
                                "utterance_start_ts_ms": None,
                                "server_elapsed_ms": None,
                                "asr_confidence": None,
                                "stream_end": True,
                            },
                        )
                        break

                    outputs = router.finalize_stream()
                    final_text = ""

                    for output in outputs:
                        payload = router_output_to_payload(
                            output=output,
                            session_id=session_id,
                        )

                        if output.type == "final":
                            final_text = output.text
                            payload["stream_end"] = True

                        await send_payload(websocket, payload)

                    print(
                        f"[{session_id}] FINAL [{router.current_language}]: {final_text}",
                        flush=True,
                    )

                    break

                elif msg_type == "ping":
                    await send_payload(
                        websocket,
                        {
                            "type": "pong",
                            "session_id": session_id,
                            "language": language,
                            "text": "",
                        },
                    )

                else:
                    await send_payload(
                        websocket,
                        {
                            "type": "error",
                            "session_id": session_id,
                            "language": language,
                            "text": "",
                            "message": f"Unsupported message type: {msg_type}",
                        },
                    )

            elif "bytes" in message and message["bytes"] is not None:
                if router is None:
                    await send_payload(
                        websocket,
                        {
                            "type": "loading",
                            "session_id": session_id,
                            "language": language,
                            "text": "",
                            "message": "Loading default ASR router",
                        },
                    )

                    router = create_router(session_id=session_id, language=language)

                    await send_payload(
                        websocket,
                        {
                            "type": "config_ack",
                            "session_id": session_id,
                            "language": language,
                            "sample_rate": SAMPLE_RATE,
                            "text": "",
                        },
                    )

                audio = pcm16_bytes_to_float32(message["bytes"])
                outputs = router.accept_audio(audio)

                for output in outputs:
                    payload = router_output_to_payload(
                        output=output,
                        session_id=session_id,
                    )

                    if output.type == "audio_received":
                        print(
                            f"[{session_id}] AUDIO_RECEIVED "
                            f"server_elapsed={payload.get('server_elapsed_ms')}ms",
                            flush=True,
                        )

                    elif output.type == "partial":
                        print(
                            f"[{session_id}] PARTIAL [{output.language}] "
                            f"server_elapsed={payload.get('server_elapsed_ms')}ms "
                            f"asr_conf={payload.get('asr_confidence')} : {output.text}",
                            flush=True,
                        )

                    elif output.type == "language_switch":
                        print(
                            f"[{session_id}] LANGUAGE_SWITCH "
                            f"{output.language} -> {output.detected_language} "
                            f"server_elapsed={payload.get('server_elapsed_ms')}ms "
                            f"lid_conf={payload.get('lid_confidence')} "
                            f"lid_label={payload.get('lid_label')}",
                            flush=True,
                        )

                    elif output.type == "utterance_final":
                        print(
                            f"[{session_id}] UTTERANCE_FINAL [{output.language}] "
                            f"server_elapsed={payload.get('server_elapsed_ms')}ms "
                            f"lid_conf={payload.get('lid_confidence')} "
                            f"lid_label={payload.get('lid_label')} : {output.text}",
                            flush=True,
                        )

                    await send_payload(websocket, payload)

    except WebSocketDisconnect:
        print(f"[{session_id}] disconnected", flush=True)

    except RuntimeError as exc:
        if "disconnect message has been received" in str(exc):
            print(f"[{session_id}] disconnected cleanly", flush=True)
        else:
            print(f"[{session_id}] RUNTIME ERROR: {exc}", flush=True)

            try:
                await send_payload(
                    websocket,
                    {
                        "type": "error",
                        "session_id": session_id,
                        "language": language,
                        "text": "",
                        "message": str(exc),
                    },
                )
            except Exception:
                pass

    except Exception as exc:
        print(f"[{session_id}] ERROR: {exc}", flush=True)

        try:
            await send_payload(
                websocket,
                {
                    "type": "error",
                    "session_id": session_id,
                    "language": language,
                    "text": "",
                    "message": str(exc),
                },
            )
        except Exception:
            pass

    finally:
        print(f"[{session_id}] websocket closed", flush=True)


@app.websocket("/asr/ml/ws")
async def websocket_asr_ml(websocket: WebSocket):
    await websocket_asr(websocket)
