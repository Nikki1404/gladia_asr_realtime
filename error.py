(client_env) PS C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script> python .\gladia_client.py --mode file --file C:/Users/re_nikitav/Documents/azure_benchmarking/audio/a.wav --language en --chunk-ms 30
{'type': 'ready', 'session_id': '49515763-5eec-4e3f-acb3-0a7bc5048e6c', 'language': 'en', 'sample_rate': 16000}
{'type': 'config_ack', 'language': 'en'}
ERROR: 'str' object has no attribute 'text'

getting this at client side 
and this at server side 

INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     ('172.17.0.1', 42056) - "WebSocket /asr/ws" [accepted]
Loading ASR model language=en, provider=cuda
[49515763-5eec-4e3f-acb3-0a7bc5048e6c] connected language=en
INFO:     connection open
Loading ASR model language=en, provider=cuda
[49515763-5eec-4e3f-acb3-0a7bc5048e6c] config language=en
[49515763-5eec-4e3f-acb3-0a7bc5048e6c] ERROR: 'str' object has no attribute 'text'
^CINFO:     Shutting down
