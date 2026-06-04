import json
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
    }

    if output.detected_language is not None:
        payload["detected_language"] = output.detected_language

    if output.lid_confidence is not None:
        payload["lid_confidence"] = round(output.lid_confidence, 4)
        payload["conf"] = round(output.lid_confidence, 4)

    if output.lid_label is not None:
        payload["lid_label"] = output.lid_label

    if output.asr_confidence is not None:
        payload["asr_confidence"] = round(output.asr_confidence, 4)
    else:
        payload["asr_confidence"] = None

    if output.ttfb_ms is not None:
        payload["ttfb_ms"] = round(output.ttfb_ms, 2)

    if output.ttft_ms is not None:
        payload["ttft_ms"] = round(output.ttft_ms, 2)

    if output.elapsed_ms is not None:
        payload["elapsed_ms"] = round(output.elapsed_ms, 2)

    if output.utterance_ttfb_ms is not None:
        payload["utterance_ttfb_ms"] = round(output.utterance_ttfb_ms, 2)

    if output.utterance_ttft_ms is not None:
        payload["utterance_ttft_ms"] = round(output.utterance_ttft_ms, 2)

    return payload


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

    await websocket.send_text(
        json.dumps(
            {
                "type": "ready",
                "session_id": session_id,
                "language": language,
                "sample_rate": SAMPLE_RATE,
                "message": "WebSocket connected. Send config first, then PCM16 audio bytes.",
            }
        )
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
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "session_id": session_id,
                                "message": "Invalid JSON message",
                            }
                        )
                    )
                    continue

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

                    print(f"[{session_id}] config language={language}", flush=True)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "loading",
                                "session_id": session_id,
                                "language": language,
                                "message": "Loading ASR router, Silero VAD, and SpeechBrain LID",
                            }
                        )
                    )

                    router = create_router(session_id=session_id, language=language)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "config_ack",
                                "session_id": session_id,
                                "language": language,
                                "sample_rate": SAMPLE_RATE,
                            }
                        )
                    )

                elif msg_type == "end":
                    if router is None:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final",
                                    "session_id": session_id,
                                    "language": language,
                                    "text": "",
                                    "ttfb_ms": None,
                                    "ttft_ms": None,
                                    "elapsed_ms": None,
                                    "asr_confidence": None,
                                    "stream_end": True,
                                }
                            )
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

                else:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "session_id": session_id,
                                "message": f"Unsupported message type: {msg_type}",
                            }
                        )
                    )

            elif "bytes" in message and message["bytes"] is not None:
                if router is None:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "loading",
                                "session_id": session_id,
                                "language": language,
                                "message": "Loading default ASR router",
                            }
                        )
                    )

                    router = create_router(session_id=session_id, language=language)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "config_ack",
                                "session_id": session_id,
                                "language": language,
                                "sample_rate": SAMPLE_RATE,
                            }
                        )
                    )

                audio = pcm16_bytes_to_float32(message["bytes"])
                outputs = router.accept_audio(audio)

                for output in outputs:
                    payload = router_output_to_payload(
                        output=output,
                        session_id=session_id,
                    )

                    if output.type == "partial":
                        print(
                            f"[{session_id}] PARTIAL [{output.language}] "
                            f"session_ttfb={payload.get('ttfb_ms')}ms "
                            f"session_ttft={payload.get('ttft_ms')}ms "
                            f"utterance_ttfb={payload.get('utterance_ttfb_ms')}ms "
                            f"utterance_ttft={payload.get('utterance_ttft_ms')}ms "
                            f"elapsed={payload.get('elapsed_ms')}ms "
                            f"asr_conf={payload.get('asr_confidence')} : {output.text}",
                            flush=True,
                        )

                    elif output.type == "language_switch":
                        print(
                            f"[{session_id}] LANGUAGE_SWITCH "
                            f"{output.language} -> {output.detected_language} "
                            f"session_ttfb={payload.get('ttfb_ms')}ms "
                            f"session_ttft={payload.get('ttft_ms')}ms "
                            f"elapsed={payload.get('elapsed_ms')}ms "
                            f"lid_conf={payload.get('lid_confidence')} "
                            f"lid_label={payload.get('lid_label')}",
                            flush=True,
                        )

                    elif output.type == "utterance_final":
                        print(
                            f"[{session_id}] UTTERANCE_FINAL [{output.language}] "
                            f"session_ttfb={payload.get('ttfb_ms')}ms "
                            f"session_ttft={payload.get('ttft_ms')}ms "
                            f"utterance_ttfb={payload.get('utterance_ttfb_ms')}ms "
                            f"utterance_ttft={payload.get('utterance_ttft_ms')}ms "
                            f"elapsed={payload.get('elapsed_ms')}ms "
                            f"lid_conf={payload.get('lid_confidence')} "
                            f"lid_label={payload.get('lid_label')} : {output.text}",
                            flush=True,
                        )

                    await websocket.send_text(json.dumps(payload))

    except WebSocketDisconnect:
        print(f"[{session_id}] disconnected", flush=True)

    except RuntimeError as exc:
        if "disconnect message has been received" in str(exc):
            print(f"[{session_id}] disconnected cleanly", flush=True)
        else:
            print(f"[{session_id}] RUNTIME ERROR: {exc}", flush=True)
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

    finally:
        print(f"[{session_id}] websocket closed", flush=True)


