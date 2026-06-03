# Simple Multilingual ASR Router

Simple FastAPI WebSocket server using sherpa-onnx streaming transducer models.

Supported languages:

- English: `en`
- Spanish: `es`

## Important design

- Dockerfile host/port are directly inside CMD.
- Model variant `64` is inside Python code.
- Client realtime streaming chunk size is controlled by `--chunk-ms`.
- File mode streams the WAV like realtime mic audio.

## Build

```bash
docker build -t simple-multilingual-asr .
```

During build, Docker downloads EN + ES models.

## Run server

```bash
docker run --rm -p 8001:8001 simple-multilingual-asr
```

Server:

```text
http://localhost:8001/health
ws://localhost:8001/asr/ml/ws
```

## Test file streaming

```bash
pip install websockets numpy scipy
python client.py --mode file --file audio/english.wav --language en --chunk-ms 30
```

Spanish:

```bash
python client.py --mode file --file audio/spanish.wav --language es --chunk-ms 30
```

## Test mic streaming

```bash
pip install websockets numpy scipy pyaudio
python client.py --mode mic --language en --chunk-ms 30
```
