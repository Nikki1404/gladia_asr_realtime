from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.config import (
    LID_CONFIDENCE_THRESHOLD,
    LID_DEVICE,
    LID_LANGUAGE_ALIASES,
    LID_MIN_AUDIO_MS,
    LID_MODEL_ID,
    SAMPLE_RATE,
)


@dataclass
class LIDResult:
    language: str
    confidence: float
    label: str


class SpeechBrainLanguageIdentifier:
    """
    SpeechBrain VoxLingua107 language identifier.

    This runs at utterance boundaries, not on every audio chunk.
    That keeps routing CPU/GPU-friendly and closer to the Gladia-style design.
    """

    def __init__(self):
        try:
            import torch
            from speechbrain.inference.classifiers import EncoderClassifier
        except ImportError as exc:
            raise ImportError(
                "speechbrain and torch are required. "
                "Install using: pip install speechbrain torch"
            ) from exc

        self.torch = torch

        self.classifier = EncoderClassifier.from_hparams(
            source=LID_MODEL_ID,
            savedir="pretrained_models/lang-id-voxlingua107",
            run_opts={"device": LID_DEVICE},
        )

        self.min_samples = int(SAMPLE_RATE * LID_MIN_AUDIO_MS / 1000)

    def detect(self, audio: np.ndarray) -> Optional[LIDResult]:
        """
        Detect language from one utterance worth of audio.
        """
        if audio.size < self.min_samples:
            return None

        wav = self.torch.from_numpy(
            audio.astype(np.float32, copy=False)
        ).unsqueeze(0)

        with self.torch.no_grad():
            _out_prob, score, _index, text_lab = self.classifier.classify_batch(wav)

        label = self._label_to_string(text_lab)
        confidence = self._score_to_float(score)
        language = self._normalize_label(label)

        if language is None:
            return None

        if confidence < LID_CONFIDENCE_THRESHOLD:
            return None

        return LIDResult(
            language=language,
            confidence=confidence,
            label=label,
        )

    @staticmethod
    def _label_to_string(label) -> str:
        if isinstance(label, str):
            return label

        if isinstance(label, (list, tuple)) and label:
            return str(label[0])

        return str(label)

    @staticmethod
    def _score_to_float(score) -> float:
        try:
            if hasattr(score, "detach"):
                score = score.detach().cpu().numpy()

            arr = np.asarray(score).reshape(-1)
            return float(arr[0])

        except Exception:
            return 0.0

    @staticmethod
    def _normalize_label(label: str) -> Optional[str]:
        normalized = label.lower().strip()

        for key, value in LID_LANGUAGE_ALIASES.items():
            key = key.lower()

            if (
                normalized == key
                or normalized.startswith(key + ":")
                or key in normalized
            ):
                return value

        return None
