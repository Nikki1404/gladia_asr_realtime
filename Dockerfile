FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04

ENV http_proxy="http://163.116.128.80:8080"
ENV https_proxy="http://163.116.128.80:8080"
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update -o Acquire::Retries=5 && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip --break-system-packages && \
    python3 -m pip install -r requirements.txt --break-system-packages

# CUDA-enabled sherpa-onnx
RUN python3 -m pip install \
    sherpa-onnx==1.13.2+cuda12.cudnn9 \
    -f https://k2-fsa.github.io/sherpa/onnx/cuda.html \
    --break-system-packages

COPY app ./app
COPY scripts ./scripts
COPY client.py ./client.py

# Download EN + ES models during docker build
RUN python3 scripts/download_models.py --languages en es --models-root models

EXPOSE 8002

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--ws-ping-interval", "20", "--ws-ping-timeout", "120"]
