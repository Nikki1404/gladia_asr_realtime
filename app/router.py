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


@dataclass
class RouterOutput:
    type: str
    text: str = ""
    language: str = ""
    detected_language: Optional[str] = None
    lid_confidence: Optional[float] = None
    lid_label: Optional[str] = None
    ttfb_ms: Optional[float] = None
    elapsed_ms: Optional[float] = None


class MultilingualASRRouterSession:
    """
    Gladia-style ASR coordinator adapted to this simple project.

    Flow:
    1. Client sends PCM16 mono 16 kHz bytes.
    2. Server converts PCM16 to float32.
    3. Silero VAD detects speech boundaries.
    4. Current monolingual ASR emits partials.
    5. At speech end:
       - finalize current ASR stream
       - run SpeechBrain LID on utterance audio
       - if LID says another supported language, re-transcribe that utterance
         with the detected language model
       - switch future route to the detected language
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

        self.started_at = time.perf_counter()
        self.first_partial_at: Optional[float] = None

        self.full_transcript_parts: list[str] = []

        self.current_utterance_audio = np.array([], dtype=np.float32)
        self.total_audio_samples = 0

        self.in_utterance = False

    def accept_audio(self, audio: np.ndarray) -> list[RouterOutput]:
        """
        Accept one chunk of float32 audio.
        """
        outputs: list[RouterOutput] = []

        if audio.size == 0:
            return outputs

        audio = audio.astype(np.float32, copy=False)
        self.total_audio_samples += audio.size

        vad_event = self.vad.accept_audio(audio) if self.vad else None

        if vad_event and vad_event.type == "speech_start":
            self.in_utterance = True
            self.current_utterance_audio = np.array([], dtype=np.float32)

        # If VAD is disabled, treat stream as continuous speech.
        if not self.vad:
            self.in_utterance = True

        if self.in_utterance:
            self.current_utterance_audio = np.concatenate(
                [
                    self.current_utterance_audio,
                    audio,
                ]
            )

        partial = self.asr_session.accept_audio(audio)

        if partial:
            now = time.perf_counter()

            if self.first_partial_at is None:
                self.first_partial_at = now

            outputs.append(
                RouterOutput(
                    type="partial",
                    text=partial,
                    language=self.current_language,
                    ttfb_ms=(self.first_partial_at - self.started_at) * 1000,
                    elapsed_ms=(now - self.started_at) * 1000,
                )
            )

        if vad_event and vad_event.type == "speech_end":
            outputs.extend(self._finalize_utterance())

        return outputs

    def _finalize_utterance(self) -> list[RouterOutput]:
        """
        Finalize current utterance and optionally correct language route.
        """
        outputs: list[RouterOutput] = []

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
                    RouterOutput(
                        type="language_switch",
                        text=final_text,
                        language=previous_language,
                        detected_language=final_language,
                        lid_confidence=lid_result.confidence,
                        lid_label=lid_result.label,
                        elapsed_ms=(time.perf_counter() - self.started_at) * 1000,
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
            RouterOutput(
                type="utterance_final",
                text=final_text,
                language=final_language,
                detected_language=lid_result.language if lid_result else None,
                lid_confidence=lid_result.confidence if lid_result else None,
                lid_label=lid_result.label if lid_result else None,
                elapsed_ms=(time.perf_counter() - self.started_at) * 1000,
            )
        )

        self.current_utterance_audio = np.array([], dtype=np.float32)
        self.in_utterance = False

        return outputs

    def finalize_stream(self) -> list[RouterOutput]:
        """
        Called when client sends {"type": "end"}.
        """
        outputs: list[RouterOutput] = []

        if self.current_utterance_audio.size > 0:
            outputs.extend(self._finalize_utterance())
        else:
            final_text = self.asr_session.finalize(reset_after=False).strip()

            if final_text:
                self.full_transcript_parts.append(final_text)

        full_text = " ".join(
            part for part in self.full_transcript_parts if part
        ).strip()

        outputs.append(
            RouterOutput(
                type="final",
                text=full_text,
                language=self.current_language,
                elapsed_ms=(time.perf_counter() - self.started_at) * 1000,
            )
        )

        return outputs
