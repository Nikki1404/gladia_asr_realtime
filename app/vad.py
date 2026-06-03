from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.config import (
    SAMPLE_RATE,
    VAD_MAX_UTTERANCE_SEC,
    VAD_MIN_SILENCE_MS,
    VAD_MIN_UTTERANCE_MS,
    VAD_SPEECH_PAD_MS,
    VAD_THRESHOLD,
)


@dataclass
class VADEvent:
    type: str
    sample_index: int


class SileroStreamingVAD:
    """
    Server-side Silero VAD wrapper.

    Silero streaming VAD expects fixed-size frames:
    - 512 samples at 16 kHz
    - 256 samples at 8 kHz

    The client can still send 20/30/50/100 ms chunks.
    This wrapper buffers chunks and feeds Silero valid frame sizes.
    """

    def __init__(self):
        try:
            import torch
            from silero_vad import VADIterator, load_silero_vad
        except ImportError as exc:
            raise ImportError(
                "silero-vad and torch are required. "
                "Install using: pip install silero-vad torch"
            ) from exc

        self.torch = torch
        self.torch.set_num_threads(1)

        self.model = load_silero_vad(onnx=False)

        self.iterator = VADIterator(
            self.model,
            threshold=VAD_THRESHOLD,
            sampling_rate=SAMPLE_RATE,
            min_silence_duration_ms=VAD_MIN_SILENCE_MS,
            speech_pad_ms=VAD_SPEECH_PAD_MS,
        )

        self.frame_samples = 512 if SAMPLE_RATE == 16000 else 256

        self.pending = np.array([], dtype=np.float32)
        self.processed_samples = 0

        self.in_speech = False
        self.last_start_sample: Optional[int] = None

        self.min_utt_samples = int(SAMPLE_RATE * VAD_MIN_UTTERANCE_MS / 1000)
        self.max_utt_samples = int(SAMPLE_RATE * VAD_MAX_UTTERANCE_SEC)

    def reset(self) -> None:
        self.iterator.reset_states()

        self.pending = np.array([], dtype=np.float32)
        self.processed_samples = 0

        self.in_speech = False
        self.last_start_sample = None

    def accept_audio(self, audio: np.ndarray) -> Optional[VADEvent]:
        """
        Accept float32 audio and return first VAD event from this chunk,
        if any.
        """
        if audio.size == 0:
            return None

        self.pending = np.concatenate(
            [
                self.pending,
                audio.astype(np.float32, copy=False),
            ]
        )

        first_event: Optional[VADEvent] = None

        while self.pending.size >= self.frame_samples:
            frame = self.pending[: self.frame_samples]
            self.pending = self.pending[self.frame_samples :]

            tensor = self.torch.from_numpy(
                frame.astype(np.float32, copy=False)
            )

            result = self.iterator(tensor, return_seconds=False)

            self.processed_samples += self.frame_samples

            event: Optional[VADEvent] = None

            if result:
                if "start" in result:
                    self.in_speech = True
                    self.last_start_sample = int(result["start"])

                    event = VADEvent(
                        type="speech_start",
                        sample_index=self.last_start_sample,
                    )

                elif "end" in result:
                    end_sample = int(result["end"])

                    if self.last_start_sample is None:
                        duration = self.min_utt_samples
                    else:
                        duration = end_sample - self.last_start_sample

                    if duration >= self.min_utt_samples:
                        self.in_speech = False
                        self.last_start_sample = None

                        event = VADEvent(
                            type="speech_end",
                            sample_index=end_sample,
                        )

            # Safety cutoff for very long utterances.
            if (
                event is None
                and self.in_speech
                and self.last_start_sample is not None
                and self.processed_samples - self.last_start_sample
                >= self.max_utt_samples
            ):
                self.in_speech = False
                end_sample = self.processed_samples
                self.last_start_sample = None

                event = VADEvent(
                    type="speech_end",
                    sample_index=end_sample,
                )

            if event and first_event is None:
                first_event = event

        return first_event
