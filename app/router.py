from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.asr import ASRManager, StreamingASR
from app.config import (
    DEFAULT_LANGUAGE,
    ENABLE_LANGUAGE_ID,
    ENABLE_LANGUAGE_ROUTING,
    ENABLE_SILERO_VAD,
    SUPPORTED_LANGUAGES,
)
from app.lid import LIDResult, SpeechBrainLanguageIdentifier
from app.vad import SileroStreamingVAD


def now_ms() -> float:
    return time.time() * 1000.0


@dataclass
class RouterOutput:
    type: str
    text: str = ""
    language: str = ""

    detected_language: Optional[str] = None
    lid_confidence: Optional[float] = None
    lid_label: Optional[str] = None

    # Server-side timing values.
    server_elapsed_ms: Optional[float] = None
    server_audio_received_ts_ms: Optional[float] = None
    utterance_start_ts_ms: Optional[float] = None

    # sherpa-onnx greedy transducer does not expose ASR word confidence.
    asr_confidence: Optional[float] = None


class MultilingualASRRouterSession:
    """
    Router session.

    Timing design:
    - server_audio_received_ts_ms:
        Timestamp when latest audio chunk was received by server.
    - utterance_start_ts_ms:
        Timestamp when current utterance started.
    - server_send_ts_ms:
        Added in main.py immediately before WebSocket send.

    Client calculates:
    - latency_ms = client_receive_ts_ms - server_send_ts_ms
    - ttfb_ms    = server_send_ts_ms - server_audio_received_ts_ms
    - ttft_ms    = server_send_ts_ms - utterance_start_ts_ms
                   only for text-bearing events.
    """

    def __init__(
        self,
        asr_manager: ASRManager,
        initial_language: str = DEFAULT_LANGUAGE,
        enable_vad: bool = ENABLE_SILERO_VAD,
        enable_lid: bool = ENABLE_LANGUAGE_ID,
        enable_routing: bool = ENABLE_LANGUAGE_ROUTING,
    ):
        if initial_language not in SUPPORTED_LANGUAGES:
            initial_language = DEFAULT_LANGUAGE

        self.asr_manager = asr_manager
        self.current_language = initial_language

        self.enable_vad = enable_vad
        self.enable_lid = enable_lid
        self.enable_routing = enable_routing

        self.asr_session: StreamingASR = self.asr_manager.create_session(
            self.current_language
        )

        self.vad = SileroStreamingVAD() if self.enable_vad else None
        self.lid = SpeechBrainLanguageIdentifier() if self.enable_lid else None

        self.started_at_perf = time.perf_counter()

        self.audio_received_emitted = False

        self.latest_audio_received_ts_ms: Optional[float] = None
        self.current_utterance_start_ts_ms: Optional[float] = None

        self.full_transcript_parts: list[str] = []

        self.current_utterance_audio = np.array([], dtype=np.float32)
        self.total_audio_samples = 0

        self.in_utterance = False

    def _server_elapsed_ms(self) -> float:
        return (time.perf_counter() - self.started_at_perf) * 1000.0

    def _mark_utterance_start(self) -> None:
        self.in_utterance = True
        self.current_utterance_audio = np.array([], dtype=np.float32)

        # Utterance start must be different from latest audio chunk time.
        # This lets TTFT grow from the start of the utterance.
        self.current_utterance_start_ts_ms = now_ms()

    def _ensure_utterance_started(self) -> None:
        if self.current_utterance_start_ts_ms is None:
            self.current_utterance_start_ts_ms = (
                self.latest_audio_received_ts_ms or now_ms()
            )

        if not self.in_utterance:
            self.in_utterance = True

    def _build_output(
        self,
        output_type: str,
        text: str = "",
        language: Optional[str] = None,
        detected_language: Optional[str] = None,
        lid_confidence: Optional[float] = None,
        lid_label: Optional[str] = None,
    ) -> RouterOutput:
        return RouterOutput(
            type=output_type,
            text=text,
            language=language or self.current_language,
            detected_language=detected_language,
            lid_confidence=lid_confidence,
            lid_label=lid_label,
            server_elapsed_ms=self._server_elapsed_ms(),
            server_audio_received_ts_ms=self.latest_audio_received_ts_ms,
            utterance_start_ts_ms=self.current_utterance_start_ts_ms,
            asr_confidence=None,
        )

    def accept_audio(self, audio: np.ndarray) -> list[RouterOutput]:
        outputs: list[RouterOutput] = []

        if audio.size == 0:
            return outputs

        audio = audio.astype(np.float32, copy=False)

        # This is updated for every chunk received by the server.
        self.latest_audio_received_ts_ms = now_ms()
        self.total_audio_samples += audio.size

        if not self.audio_received_emitted:
            self.audio_received_emitted = True

            # Start an utterance clock from first audio if VAD has not fired yet.
            if self.current_utterance_start_ts_ms is None:
                self.current_utterance_start_ts_ms = self.latest_audio_received_ts_ms

            outputs.append(
                self._build_output(
                    output_type="audio_received",
                    text="",
                    language=self.current_language,
                )
            )

        vad_event = self.vad.accept_audio(audio) if self.vad else None

        if vad_event and vad_event.type == "speech_start":
            self._mark_utterance_start()

        if not self.vad and not self.in_utterance:
            self._mark_utterance_start()

        if self.in_utterance:
            self.current_utterance_audio = np.concatenate(
                [
                    self.current_utterance_audio,
                    audio,
                ]
            )

        partial = self.asr_session.accept_audio(audio)

        if partial:
            self._ensure_utterance_started()

            outputs.append(
                self._build_output(
                    output_type="partial",
                    text=partial,
                    language=self.current_language,
                )
            )

        if vad_event and vad_event.type == "speech_end":
            outputs.extend(self._finalize_utterance())

        return outputs

    def _finalize_utterance(self) -> list[RouterOutput]:
        outputs: list[RouterOutput] = []

        self._ensure_utterance_started()

        raw_final = self.asr_session.finalize(reset_after=True).strip()

        final_text = raw_final
        final_language = self.current_language

        lid_result: Optional[LIDResult] = None

        if self.lid and self.current_utterance_audio.size > 0:
            lid_result = self.lid.detect(self.current_utterance_audio)

        if (
            lid_result
            and self.enable_routing
            and lid_result.language in SUPPORTED_LANGUAGES
            and lid_result.language != self.current_language
        ):
            previous_language = self.current_language
            final_language = lid_result.language

            try:
                corrected_text = self.asr_manager.transcribe_array(
                    language=final_language,
                    audio=self.current_utterance_audio,
                ).strip()

                if corrected_text:
                    final_text = corrected_text

                outputs.append(
                    self._build_output(
                        output_type="language_switch",
                        text=final_text,
                        language=previous_language,
                        detected_language=final_language,
                        lid_confidence=lid_result.confidence,
                        lid_label=lid_result.label,
                    )
                )

                self.current_language = final_language
                self.asr_session = self.asr_manager.create_session(
                    self.current_language
                )

            except Exception as exc:
                print(
                    "LID route correction failed. "
                    f"Keeping language={self.current_language}. Error={exc}",
                    flush=True,
                )

        if final_text:
            self.full_transcript_parts.append(final_text)

        outputs.append(
            self._build_output(
                output_type="utterance_final",
                text=final_text,
                language=final_language,
                detected_language=lid_result.language if lid_result else None,
                lid_confidence=lid_result.confidence if lid_result else None,
                lid_label=lid_result.label if lid_result else None,
            )
        )

        self.current_utterance_audio = np.array([], dtype=np.float32)
        self.in_utterance = False
        self.current_utterance_start_ts_ms = None

        return outputs

    def finalize_stream(self) -> list[RouterOutput]:
        outputs: list[RouterOutput] = []

        if self.current_utterance_audio.size > 0:
            outputs.extend(self._finalize_utterance())
        else:
            final_text = self.asr_session.finalize(reset_after=False).strip()

            if final_text:
                if self.current_utterance_start_ts_ms is None:
                    self.current_utterance_start_ts_ms = (
                        self.latest_audio_received_ts_ms or now_ms()
                    )

                self.full_transcript_parts.append(final_text)

        full_text = " ".join(
            part for part in self.full_transcript_parts if part
        ).strip()

        outputs.append(
            self._build_output(
                output_type="final",
                text=full_text,
                language=self.current_language,
            )
        )

        return outputs
