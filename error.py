INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     ('172.17.0.1', 57442) - "WebSocket /asr/ws" [accepted]
Loading ASR model language=en, provider=cuda
INFO:speechbrain.utils.quirks:Applied quirks (see `speechbrain.utils.quirks`): [disable_jit_profiling, allow_tf32]
INFO:speechbrain.utils.quirks:Excluded quirks specified by the `SB_DISABLE_QUIRKS` environment (comma-separated list): []
INFO:speechbrain.utils.fetching:Fetch hyperparams.yaml: Fetching from HuggingFace Hub 'speechbrain/lang-id-voxlingua107-ecapa' if not cached
INFO:speechbrain.utils.fetching:Fetch custom.py: Fetching from HuggingFace Hub 'speechbrain/lang-id-voxlingua107-ecapa' if not cached
/usr/local/lib/python3.10/dist-packages/speechbrain/utils/autocast.py:68: FutureWarning: `torch.cuda.amp.custom_fwd(args...)` is deprecated. Please use `torch.amp.custom_fwd(args..., device_type='cuda')` instead.
  wrapped_fwd = torch.cuda.amp.custom_fwd(fwd, cast_inputs=cast_inputs)
INFO:speechbrain.utils.fetching:Fetch embedding_model.ckpt: Fetching from HuggingFace Hub 'speechbrain/lang-id-voxlingua107-ecapa' if not cached
INFO:speechbrain.utils.fetching:Fetch classifier.ckpt: Fetching from HuggingFace Hub 'speechbrain/lang-id-voxlingua107-ecapa' if not cached
INFO:speechbrain.utils.fetching:Fetch label_encoder.txt: Fetching from HuggingFace Hub 'speechbrain/lang-id-voxlingua107-ecapa' if not cached
INFO:speechbrain.utils.parameter_transfer:Loading pretrained files for: embedding_model, classifier, label_encoder
/usr/local/lib/python3.10/dist-packages/speechbrain/utils/checkpoints.py:200: FutureWarning: You are using `torch.load` with `weights_only=False` (the current default value), which uses the default pickle module implicitly. It is possible to construct malicious pickle data which will execute arbitrary code during unpickling (See https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models for more details). In a future release, the default value for `weights_only` will be flipped to `True`. This limits the functions that could be executed during unpickling. Arbitrary objects will no longer be allowed to be loaded via this mode unless they are explicitly allowlisted by the user via `torch.serialization.add_safe_globals`. We recommend you start setting `weights_only=True` for any use case where you don't have full control of the loaded file. Please open an issue on GitHub for any issues related to this experimental feature.
  state_dict = torch.load(path, map_location=device)
[b6adeba5-f78b-4022-80f7-76ac167148e4] connected language=en
INFO:     connection open
[b6adeba5-f78b-4022-80f7-76ac167148e4] ERROR: Cannot call "receive" once a disconnect message has been received.
INFO:     connection closed

getting this at server side 

and got this at client side 
(client_env) PS C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script> python .\gladia_client.py --mode file --file C:/Users/re_nikitav/Documents/azure_benchmarking/audio/a.wav --language en --chunk-ms 30
Traceback (most recent call last):
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\client_env\Lib\site-packages\websockets\asyncio\client.py", line 546, in __await_impl__
    await self.connection.handshake(
    ...<2 lines>...
    )
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\client_env\Lib\site-packages\websockets\asyncio\client.py", line 105, in handshake
    await asyncio.wait(
    ...<2 lines>...
    )
  File "C:\Program Files\Python313\Lib\asyncio\tasks.py", line 451, in wait
    return await _wait(fs, timeout, return_when, loop)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\tasks.py", line 537, in _wait
    await waiter
asyncio.exceptions.CancelledError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\client_env\Lib\site-packages\websockets\asyncio\client.py", line 542, in __await_impl__
    async with asyncio_timeout(self.open_timeout):
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "C:\Program Files\Python313\Lib\asyncio\timeouts.py", line 116, in __aexit__
    raise TimeoutError from exc_val
TimeoutError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\gladia_client.py", line 273, in <module>
    main()
    ~~~~^^
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\gladia_client.py", line 252, in main
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
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\gladia_client.py", line 127, in run_file
    async with websockets.connect(
               ~~~~~~~~~~~~~~~~~~^
        url,
        ^^^^
    ...<2 lines>...
        ping_timeout=120,
        ^^^^^^^^^^^^^^^^^
    ) as ws:
    ^
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\client_env\Lib\site-packages\websockets\asyncio\client.py", line 590, in __aenter__
    return await self
           ^^^^^^^^^^
  File "C:\Users\re_nikitav\Documents\parakeet_asr_custom_vad\script\client_env\Lib\site-packages\websockets\asyncio\client.py", line 581, in __await_impl__
    raise TimeoutError("timed out during opening handshake") from exc
TimeoutError: timed out during opening handshake
