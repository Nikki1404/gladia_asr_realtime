from typing import Optional

import numpy as np
import sherpa_onnx

from app.config import MODEL_ROOT, MODEL_VARIANT, SAMPLE_RATE


class StreamingASR:
    """One streaming ASR session for one selected language."""

    def __init__(self, language: str):
        self.language = language
        self.model_dir = MODEL_ROOT / MODEL_VARIANT / language

        encoder = self.model_dir / "encoder.onnx"
        decoder = self.model_dir / "decoder.onnx"
        joiner = self.model_dir / "joiner.onnx"
        tokens = self.model_dir / "tokens.txt"

        missing = [str(p) for p in [encoder, decoder, joiner, tokens] if not p.exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing model files for language='{language}'. Missing: {missing}"
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
        )

        self.stream = self.recognizer.create_stream()
        self.last_partial = ""

    def accept_audio(self, audio: np.ndarray) -> Optional[str]:
        """Accept mono float32 16 kHz audio and return updated partial text."""
        if audio.size == 0:
            return None

        self.stream.accept_waveform(SAMPLE_RATE, audio)

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        result = self.recognizer.get_result(self.stream)
        text = result.text.strip()

        if text and text != self.last_partial:
            self.last_partial = text
            return text

        return None

    def finalize(self) -> str:
        """Finish stream and return final text."""
        self.stream.input_finished()

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        result = self.recognizer.get_result(self.stream)
        return result.text.strip()


class ASRManager:
    def create_session(self, language: str) -> StreamingASR:
        return StreamingASR(language=language)
