 => [11/12] COPY client.py ./client.py                                                                             0.1s
 => ERROR [12/12] RUN python scripts/download_models.py --languages en es --models-root models                     0.6s
------
 > [12/12] RUN python scripts/download_models.py --languages en es --models-root models:
0.405 Downloading language=en
0.405 Repo: csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26
0.405 File: sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2
0.537 Traceback (most recent call last):
0.537   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 406, in hf_raise_for_status
0.537     response.raise_for_status()
0.537   File "/opt/venv/lib/python3.12/site-packages/requests/models.py", line 1167, in raise_for_status
0.537     raise HTTPError(http_error_msg, response=self)
0.537 requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26/resolve/main/sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2
0.537
0.537 The above exception was the direct cause of the following exception:
0.537
0.537 Traceback (most recent call last):
0.537   File "/app/scripts/download_models.py", line 121, in <module>
0.538     main()
0.538   File "/app/scripts/download_models.py", line 115, in main
0.538     download_language(language=language, models_root=models_root)
0.538   File "/app/scripts/download_models.py", line 77, in download_language
0.538     downloaded_path = hf_hub_download(
0.538                       ^^^^^^^^^^^^^^^^
0.538   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
0.538     return fn(*args, **kwargs)
0.538            ^^^^^^^^^^^^^^^^^^^
0.539   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 840, in hf_hub_download
0.539     return _hf_hub_download_to_local_dir(
0.539            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
0.540   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1068, in _hf_hub_download_to_local_dir
0.540     (url_to_download, etag, commit_hash, expected_size, head_call_error) = _get_metadata_or_catch_error(
0.540                                                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
0.541   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1374, in _get_metadata_or_catch_error
0.541     metadata = get_hf_file_metadata(
0.541                ^^^^^^^^^^^^^^^^^^^^^
0.541   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
0.541     return fn(*args, **kwargs)
0.541            ^^^^^^^^^^^^^^^^^^^
0.541   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1294, in get_hf_file_metadata
0.542     r = _request_wrapper(
0.542         ^^^^^^^^^^^^^^^^^
0.542   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 278, in _request_wrapper
0.542     response = _request_wrapper(
0.542                ^^^^^^^^^^^^^^^^^
0.542   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 302, in _request_wrapper
0.543     hf_raise_for_status(response)
0.543   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 417, in hf_raise_for_status
0.543     raise _format(EntryNotFoundError, message, response) from e
0.543 huggingface_hub.errors.EntryNotFoundError: 404 Client Error. (Request ID: Root=1-6a1fe967-440ec22415531baf3802a898;da3d2601-9864-4529-8552-417a7deb7d33)
0.543
0.543 Entry Not Found for url: https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26/resolve/main/sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2.
------
Dockerfile:38
--------------------
  36 |
  37 |     # Download EN + ES models during docker build
  38 | >>> RUN python scripts/download_models.py --languages en es --models-root models
  39 |
  40 |     EXPOSE 8002
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python scripts/download_models.py --languages en es --models-root models" did not complete successfully: exit code: 1
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/gladia_asr_realtime#
