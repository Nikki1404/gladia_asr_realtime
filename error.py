websockets.exceptions.InvalidMessage: did not receive a valid HTTP response
(venv) PS C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts> python .\nemotron_new_client.py --file C:\Users\re_nikitav\Downloads\audio_wav\Monologue.wav
[warn] Health check failed: HTTP Error 404: Not Found  (server may still be starting)
[info] File: Monologue.wav
[info] Audio: 16000Hz  1ch  16bit  124.7s
[info] Language: en-US
[info] Realtime simulation: False
[info] Connecting to ws://localhost:8002/asr/realtime-custom-vad

Traceback (most recent call last):
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\nemotron_new_client.py", line 322, in <module>
    main()
    ~~~~^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\nemotron_new_client.py", line 311, in main
    asyncio.run(
    ~~~~~~~~~~~^
        run_file(
        ^^^^^^^^^
    ...<4 lines>...
        )
        ^
    )
    ^
  File "C:\Program Files\Python313\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\nemotron_new_client.py", line 199, in run_file
    async with websockets.connect(url) as ws:
               ~~~~~~~~~~~~~~~~~~^^^^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\asyncio\client.py", line 590, in __aenter__
    return await self
           ^^^^^^^^^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\asyncio\client.py", line 546, in __await_impl__
    await self.connection.handshake(
    ...<2 lines>...
    )
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\asyncio\client.py", line 115, in handshake
    raise self.protocol.handshake_exc
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\client.py", line 327, in parse
    self.process_response(response)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\client.py", line 144, in process_response
    raise InvalidStatus(response)
websockets.exceptions.InvalidStatus: server rejected WebSocket connection: HTTP 403
(venv) PS C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts>
