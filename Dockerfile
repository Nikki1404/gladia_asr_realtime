FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

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
# Install GPU PyTorch
# CUDA 12.x minor versions are compatible, so cu121 wheels are okay
# inside a CUDA 12.3 runtime as long as the NVIDIA driver supports it.
# ------------------------------------------------------------
RUN python3 -m pip install \
    torch==2.4.0+cu121 \
    torchaudio==2.4.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# ------------------------------------------------------------
# Install GPU sherpa-onnx CUDA/cuDNN9 wheel
# This needs libcudnn.so.9 from the base image.
# ------------------------------------------------------------
RUN python3 -m pip install \
    sherpa-onnx==1.13.2+cuda12.cudnn9 \
    -f https://k2-fsa.github.io/sherpa/onnx/cuda.html

# ------------------------------------------------------------
# Install remaining Python dependencies
# ------------------------------------------------------------
RUN python3 -m pip install -r /app/requirements.txt

COPY . /app

# ------------------------------------------------------------
# Download sherpa Zipformer ASR models
# ------------------------------------------------------------
RUN python3 scripts/download_models.py \
    --languages en es \
    --models-root /app/models

# ------------------------------------------------------------
# Preload Silero VAD and SpeechBrain LID models
# ------------------------------------------------------------
RUN python3 - <<'PY'
print("Checking CUDA/PyTorch...", flush=True)
import torch
print("torch:", torch.__version__, flush=True)
print("torch cuda available:", torch.cuda.is_available(), flush=True)

print("Checking sherpa-onnx import...", flush=True)
import sherpa_onnx
print("sherpa-onnx import ok", flush=True)

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
