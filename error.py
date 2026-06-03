
==========
== CUDA ==
==========

CUDA Version 12.8.1

Container image Copyright (c) 2016-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.

This container image and its contents are governed by the NVIDIA Deep Learning Container License.
By pulling and using the container, you accept the terms and conditions of this license:
https://developer.nvidia.com/ngc/nvidia-deep-learning-container-license

A copy of this license is made available in this container at /NGC-DL-CONTAINER-LICENSE for your convenience.

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/__main__.py", line 4, in <module>
    uvicorn.main()
  File "/opt/venv/lib/python3.12/site-packages/click/core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/click/core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/click/core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/click/core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/main.py", line 412, in main
    run(
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/main.py", line 579, in run
    server.run()
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/server.py", line 66, in run
    return asyncio.run(self.serve(sockets=sockets))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/server.py", line 70, in serve
    await self._serve(sockets)
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/server.py", line 77, in _serve
    config.load()
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/config.py", line 435, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/importlib/__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/app/app/main.py", line 8, in <module>
    from app.asr import ASRManager
  File "/app/app/asr.py", line 4, in <module>
    import sherpa_onnx
  File "/opt/venv/lib/python3.12/site-packages/sherpa_onnx/__init__.py", line 1, in <module>
    from sherpa_onnx.lib._sherpa_onnx import (
ImportError: libasound.so.2: cannot open shared object file: No such file or directory
