from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.config import (
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
    def __init__(self):
        try:
            import torch
            from speechbrain.inference.classifiers import EncoderClassifier
        except ImportError as exc:
            raise ImportError(
                "speechbrain and torch are required. Install using: pip install speechbrain torch"
            ) from exc

        self.torch = torch

        self.classifier = EncoderClassifier.from_hparams(
            source=LID_MODEL_ID,
            savedir="pretrained_models/lang-id-voxlingua107",
            run_opts={"device": LID_DEVICE},
        )

        self.min_samples = int(SAMPLE_RATE * LID_MIN_AUDIO_MS / 1000)

    def detect(self, audio: np.ndarray) -> Optional[LIDResult]:
        if audio is None or audio.size < self.min_samples:
            print(
                f"LID skipped: audio too short. "
                f"samples={0 if audio is None else audio.size}, "
                f"required={self.min_samples}",
                flush=True,
            )
            return None

        try:
            audio = audio.astype(np.float32, copy=False)
            wav = self.torch.from_numpy(audio).unsqueeze(0)

            with self.torch.no_grad():
                _out_prob, score, _index, text_lab = self.classifier.classify_batch(
                    wav
                )

            raw_label = self._label_to_string(text_lab)
            confidence = self._score_to_confidence(score)
            language = self._normalize_label(raw_label)

            if language is None:
                print(
                    f"LID unsupported label={raw_label}, confidence={confidence}",
                    flush=True,
                )
                return None

            print(
                f"LID detected label={raw_label}, "
                f"language={language}, confidence={confidence}",
                flush=True,
            )

            return LIDResult(
                language=language,
                confidence=confidence,
                label=raw_label,
            )

        except Exception as exc:
            print(f"LID detect failed: {exc}", flush=True)
            return None

    @staticmethod
    def _label_to_string(label) -> str:
        if isinstance(label, str):
            return label.strip()

        if isinstance(label, (list, tuple)) and label:
            return str(label[0]).strip()

        return str(label).strip()

    @staticmethod
    def _score_to_confidence(score) -> float:
        try:
            if hasattr(score, "detach"):
                score = score.detach().cpu().numpy()

            arr = np.asarray(score).reshape(-1)

            if arr.size == 0:
                return 0.0

            value = float(arr[0])

            if 0.0 <= value <= 1.0:
                return round(value, 4)

            if value <= 0.0:
                return round(float(np.exp(value)), 4)

            return round(float(1.0 / (1.0 + np.exp(-value))), 4)

        except Exception:
            return 0.0

    @staticmethod
    def _normalize_label(label: str) -> Optional[str]:
        normalized = label.lower().strip()

        for key, value in LID_LANGUAGE_ALIASES.items():
            key = key.lower().strip()

            if normalized == key:
                return value

            if normalized.startswith(key + ":"):
                return value

            if key in normalized:
                return value

        if "english" in normalized or "eng" in normalized:
            return "en"

        if (
            "spanish" in normalized
            or "espanol" in normalized
            or "español" in normalized
            or "spa" in normalized
        ):
            return "es"

        return None
