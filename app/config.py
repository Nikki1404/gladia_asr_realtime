from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent

MODEL_VARIANT = "64"
MODEL_ROOT = APP_ROOT / "models" / "streaming_transducers"

SAMPLE_RATE = 16000

SUPPORTED_LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = "en"

# Use "cuda" inside GPU Docker image.
# Use "cpu" only if you build/run a CPU-only setup.
SHERPA_PROVIDER = "cuda"


ENABLE_SILERO_VAD = True
ENABLE_LANGUAGE_ID = True
ENABLE_LANGUAGE_ROUTING = True

# Silero VAD settings
VAD_THRESHOLD = 0.50
VAD_MIN_SILENCE_MS = 450
VAD_SPEECH_PAD_MS = 180
VAD_MIN_UTTERANCE_MS = 300
VAD_MAX_UTTERANCE_SEC = 25.0

# SpeechBrain LID settings
LID_MODEL_ID = "speechbrain/lang-id-voxlingua107-ecapa"
LID_DEVICE = "cuda" if SHERPA_PROVIDER == "cuda" else "cpu"
LID_MIN_AUDIO_MS = 500
LID_CONFIDENCE_THRESHOLD = 0.45

# Map SpeechBrain labels to local ASR model folder names.
LID_LANGUAGE_ALIASES = {
    "en": "en",
    "eng": "en",
    "english": "en",
    "es": "es",
    "spa": "es",
    "spanish": "es",
}

# Final silence padding to avoid missing last words.
FINAL_PAD_MS = 1200
