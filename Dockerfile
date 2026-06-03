FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04

ENV http_proxy="http://163.116.128.80:8080"
ENV https_proxy="http://163.116.128.80:8080"
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# ------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    ffmpeg \
    libsndfile1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Python base setup
# ------------------------------------------------------------
RUN python3 -m pip install --upgrade pip setuptools wheel

COPY requirements.txt /app/requirements.txt

# ------------------------------------------------------------
# Install GPU PyTorch for CUDA 12.1
# ------------------------------------------------------------
RUN python3 -m pip install \
    torch==2.4.0+cu121 \
    torchaudio==2.4.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# ------------------------------------------------------------
# Install GPU sherpa-onnx CUDA wheel
# IMPORTANT:
# sherpa-onnx GPU builds are not installed from normal PyPI.
# ------------------------------------------------------------
RUN python3 -m pip install \
    sherpa-onnx==1.13.2+cuda12.cudnn9 \
    -f https://k2-fsa.github.io/sherpa/onnx/cuda.html

# ------------------------------------------------------------
# Install remaining Python dependencies
# silero-vad and speechbrain will use GPU torch.
# ------------------------------------------------------------
RUN python3 -m pip install -r /app/requirements.txt

# ------------------------------------------------------------
# Copy project
# ------------------------------------------------------------
COPY . /app

# ------------------------------------------------------------
# Download sherpa Zipformer ASR models
# Expected output:
# /app/models/streaming_transducers/64/en
# /app/models/streaming_transducers/64/es
# ------------------------------------------------------------
RUN python3 scripts/download_models.py \
    --languages en es \
    --models-root /app/models

# ------------------------------------------------------------
# Preload Silero VAD and SpeechBrain LID models
# Build-time preload uses CPU because Docker build may not have GPU.
# Runtime can use CUDA based on app/config.py.
# ------------------------------------------------------------
RUN python3 - <<'PY'
print("Preloading Silero VAD...", flush=True)
from silero_vad import load_silero_vad
load_silero_vad(onnx=False)
print("Silero VAD ready.", flush=True)

print("Preloading SpeechBrain language-id model...", flush=True)
from speechbrain.inference.classifiers import EncoderClassifier
EncoderClassifier.from_hparams(
    source="speechbrain/lang-id-voxlingua107-ecapa",
    savedir="/app/pretrained_models/lang-id-voxlingua107",
    run_opts={"device": "cpu"},
)
print("SpeechBrain LID ready.", flush=True)
PY

EXPOSE 8002

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--ws-ping-interval", "20", "--ws-ping-timeout", "120"]
