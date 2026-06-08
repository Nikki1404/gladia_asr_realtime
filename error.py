(venv) PS C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts> python .\nemotron_new_client.py --file C:\Users\re_nikitav\Downloads\audio_wav\Monologue.wav
[warn] Health check failed: Remote end closed connection without response  (server may still be starting)
[info] File: Monologue.wav
[info] Audio: 16000Hz  1ch  16bit  124.7s
[info] Language: en-US
[info] Realtime simulation: False
[info] Connecting to ws://localhost:8003/asr/realtime-custom-vad

Traceback (most recent call last):
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\http11.py", line 244, in parse
    status_line = yield from parse_line(read_line)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\http11.py", line 320, in parse_line
    line = yield from read_line(MAX_LINE_LENGTH)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\streams.py", line 46, in read_line
    raise EOFError(f"stream ends after {p} bytes, before end of line")
EOFError: stream ends after 0 bytes, before end of line

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\client.py", line 303, in parse
    response = yield from Response.parse(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "C:\Users\re_nikitav\Desktop\bu-digital-cx-speech-asr-realtime-custom-vad\scripts\venv\Lib\site-packages\websockets\http11.py", line 246, in parse
    raise EOFError("connection closed while reading HTTP status line") from exc
EOFError: connection closed while reading HTTP status line

The above exception was the direct cause of the following exception:

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
websockets.exceptions.InvalidMessage: did not receive a valid HTTP response
(venv) PS C:\Users\re_nikitav\De
