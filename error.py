getting this 

==========
== CUDA ==
==========

CUDA Version 12.1.1

Container image Copyright (c) 2016-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.

This container image and its contents are governed by the NVIDIA Deep Learning Container License.
By pulling and using the container, you accept the terms and conditions of this license:
https://developer.nvidia.com/ngc/nvidia-deep-learning-container-license

A copy of this license is made available in this container at /NGC-DL-CONTAINER-LICENSE for your convenience.

INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/gladia_asr_realtime# docker logs d62a924c8f03

==========
== CUDA ==
==========

CUDA Version 12.1.1

Container image Copyright (c) 2016-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.

This container image and its contents are governed by the NVIDIA Deep Learning Container License.
By pulling and using the container, you accept the terms and conditions of this license:
https://developer.nvidia.com/ngc/nvidia-deep-learning-container-license

A copy of this license is made available in this container at /NGC-DL-CONTAINER-LICENSE for your convenience.

INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     ('172.17.0.1', 39410) - "WebSocket /asr/ws" [accepted]
Loading ASR model language=en, provider=cuda
2026-06-03 20:49:14.667533461 [E:onnxruntime:, provider_bridge_ort.cc:2101 Create] /onnxruntime_src/onnxruntime/core/session/provider_bridge_ort.cc:1952 onnxruntime::Provider& onnxruntime::ProviderLibrary::Get() [ONNXRuntimeError] : 1 : FAIL : Failed to load library /opt/venv/lib/python3.10/site-packages/sherpa_onnx/lib/libonnxruntime_providers_cuda.so with error: libcudnn.so.9: cannot open shared object file: No such file or directory

ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/opt/venv/lib/python3.10/site-packages/uvicorn/protocols/websockets/websockets_impl.py", line 243, in run_asgi
    result = await self.app(self.scope, self.asgi_receive, self.asgi_send)  # type: ignore[func-returns-value]
  File "/opt/venv/lib/python3.10/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/applications.py", line 113, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/middleware/errors.py", line 152, in __call__
    await self.app(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/opt/venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/opt/venv/lib/python3.10/site-packages/starlette/routing.py", line 715, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/routing.py", line 735, in app
    await route.handle(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/routing.py", line 362, in handle
    await self.app(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/routing.py", line 95, in app
    await wrap_app_handling_exceptions(app, session)(scope, receive, send)
  File "/opt/venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/opt/venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/opt/venv/lib/python3.10/site-packages/starlette/routing.py", line 93, in app
    await func(session)
  File "/opt/venv/lib/python3.10/site-packages/fastapi/routing.py", line 383, in app
    await dependant.call(**solved_result.values)
  File "/app/app/main.py", line 76, in websocket_asr
    router = MultilingualASRRouterSession(
  File "/app/app/router.py", line 68, in __init__
    self.asr_session: StreamingASR = self.asr_manager.create_session(
  File "/app/app/asr.py", line 149, in create_session
    return StreamingASR(language=language)
  File "/app/app/asr.py", line 64, in __init__
    self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
  File "/opt/venv/lib/python3.10/site-packages/sherpa_onnx/online_recognizer.py", line 332, in from_transducer
    self.recognizer = _Recognizer(recognizer_config)
RuntimeError: OrtSessionOptionsAppendExecutionProvider_Cuda: Failed to load shared library
INFO:     connection open
INFO:     connection closed
