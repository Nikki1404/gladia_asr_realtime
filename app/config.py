from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent

# Model folder variant only.
# This is NOT client streaming chunk size.
MODEL_VARIANT = "64"

MODEL_ROOT = APP_ROOT / "models" / "streaming_transducers"

SAMPLE_RATE = 16000

SUPPORTED_LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = "en"

# Use "cuda" for GPU build.
# Use "cpu" if running CPU image.
SHERPA_PROVIDER = "cuda"
