import numpy as np
from scipy.signal import resample_poly


def pcm16_bytes_to_float32(audio_bytes: bytes) -> np.ndarray:
    """
    Convert raw PCM16 little-endian bytes to float32 audio in [-1, 1].
    """
    if not audio_bytes:
        return np.array([], dtype=np.float32)

    audio = np.frombuffer(audio_bytes, dtype=np.int16)
    return audio.astype(np.float32) / 32768.0


def float32_to_pcm16_bytes(audio: np.ndarray) -> bytes:
    """
    Convert float32 audio in [-1, 1] to raw PCM16 little-endian bytes.
    """
    audio = np.clip(audio, -1.0, 1.0)
    pcm16 = (audio * 32767).astype(np.int16)
    return pcm16.tobytes()


def resample_audio(
    audio: np.ndarray,
    source_sr: int,
    target_sr: int = 16000,
) -> np.ndarray:
    """
    Resample mono float32 audio to target sample rate.
    """
    if source_sr == target_sr:
        return audio.astype(np.float32)

    gcd = np.gcd(source_sr, target_sr)
    up = target_sr // gcd
    down = source_sr // gcd

    return resample_poly(audio, up, down).astype(np.float32)
