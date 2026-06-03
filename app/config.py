from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent

# Kroko model variant folder.
# This is NOT the realtime mic/file streaming chunk size.
MODEL_VARIANT = "64"

MODEL_ROOT = APP_ROOT / "models" / "streaming_transducers"

SAMPLE_RATE = 16000
SUPPORTED_LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = "en"
