from livekit.plugins import openai
stt=openai.STT(
        model="nemotron-3.5-asr-streaming-0.6b",
        base_url="http://localhost:8000/v1",
        api_key="unused",
        language="es-US",   # or omit for auto-detect
    )
