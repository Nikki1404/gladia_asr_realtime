from typing import Optional

import numpy as np
import sherpa_onnx

from app.config import (
    FINAL_PAD_MS,
    MODEL_ROOT,
    MODEL_VARIANT,
    SAMPLE_RATE,
    SHERPA_PROVIDER,
)


def extract_text(result) -> str:
    """
    Safely extract text from sherpa-onnx recognition result.
    """
    if result is None:
        return ""

    if isinstance(result, str):
        return result.strip()

    if hasattr(result, "text"):
        return str(result.text).strip()

    return str(result).strip()


class StreamingASR:
    """
    One streaming ASR session for one language.

    This uses sherpa-onnx online Zipformer transducer models.
    """

    def __init__(self, language: str):
        self.language = language

        model_dir = MODEL_ROOT / MODEL_VARIANT / language

        encoder = model_dir / "encoder.onnx"
        decoder = model_dir / "decoder.onnx"
        joiner = model_dir / "joiner.onnx"
        tokens = model_dir / "tokens.txt"

        missing = [
            str(p)
            for p in [encoder, decoder, joiner, tokens]
            if not p.exists()
        ]

        if missing:
            raise FileNotFoundError(
                f"Missing model files for language='{language}'. Missing: {missing}"
            )

        print(
            f"Loading ASR model language={language}, provider={SHERPA_PROVIDER}",
            flush=True,
        )

        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(tokens),
            encoder=str(encoder),
            decoder=str(decoder),
            joiner=str(joiner),
            num_threads=2,
            sample_rate=SAMPLE_RATE,
            feature_dim=80,
            decoding_method="greedy_search",
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=2.4,
            rule2_min_trailing_silence=1.2,
            rule3_min_utterance_length=20,
            provider=SHERPA_PROVIDER,
        )

        self.reset()

    def reset(self) -> None:
        self.stream = self.recognizer.create_stream()
        self.last_partial = ""

    def accept_audio(self, audio: np.ndarray) -> Optional[str]:
        """
        Feed audio to ASR and return latest partial text if changed.
        """
        if audio.size == 0:
            return None

        self.stream.accept_waveform(
            SAMPLE_RATE,
            audio.astype(np.float32, copy=False),
        )

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        result = self.recognizer.get_result(self.stream)
        text = extract_text(result)

        if text and text != self.last_partial:
            self.last_partial = text
            return text

        return None

    def finalize(self, reset_after: bool = False) -> str:
        """
        Flush current streaming session.

        Silence padding is intentionally added before input_finished()
        to reduce the last-word-missing issue.
        """
        silence = np.zeros(
            int(SAMPLE_RATE * FINAL_PAD_MS / 1000),
            dtype=np.float32,
        )

        self.stream.accept_waveform(SAMPLE_RATE, silence)

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        self.stream.input_finished()

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        result = self.recognizer.get_result(self.stream)
        text = extract_text(result)

        if reset_after:
            self.reset()

        return text


class ASRManager:
    """
    Factory/helper for ASR sessions.

    A WebSocket session should get its own StreamingASR stream.
    """

    def create_session(self, language: str) -> StreamingASR:
        return StreamingASR(language=language)

    def transcribe_array(self, language: str, audio: np.ndarray) -> str:
        """
        One-shot re-transcription used for rollback/revision
        after language ID detects a switch.
        """
        session = self.create_session(language)
        session.accept_audio(audio)
        return session.finalize(reset_after=False)
