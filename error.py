 => [11/12] COPY client.py ./client.py                                                                             0.1s
 => ERROR [12/12] RUN python scripts/download_models.py --languages en es --models-root models                    74.7s
------
 > [12/12] RUN python scripts/download_models.py --languages en es --models-root models:
0.621 Downloading TAR model language=en
0.621 Repo: xumo/onnx_models
0.621 File: sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2
5.667 Extracting models/downloads/sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2 -> models/extracted/en
50.29 Available model files:
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/decoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/decoder-epoch-99-avg-1-chunk-16-left-128.onnx
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/encoder-epoch-99-avg-1-chunk-16-left-128.onnx
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/joiner-epoch-99-avg-1-chunk-16-left-128.onnx
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/test_wavs/trans.txt
50.29   models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/tokens.txt
50.29 Copying models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/encoder-epoch-99-avg-1-chunk-16-left-128.onnx -> models/streaming_transducers/64/en/encoder.onnx
70.03 Copying models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/decoder-epoch-99-avg-1-chunk-16-left-128.onnx -> models/streaming_transducers/64/en/decoder.onnx
70.03 Copying models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/joiner-epoch-99-avg-1-chunk-16-left-128.onnx -> models/streaming_transducers/64/en/joiner.onnx
70.04 Copying models/extracted/en/sherpa-onnx-streaming-zipformer-en-2023-06-26/tokens.txt -> models/streaming_transducers/64/en/tokens.txt
70.04 Validated final model folder: models/streaming_transducers/64/en
70.04 Done language=en
70.04 Downloading SNAPSHOT model language=es
70.04 Repo: csukuangfj/sherpa-onnx-streaming-zipformer-es-kroko-2025-08-06
Fetching 4 files:   0%|          | 0/4 [00:00<?, ?it/s]/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py:651: UserWarning: Not enough free disk space to download the file. The expected file size is: 154.88 MB. The target location models/snapshots/es/.cache/huggingface/download only has 26.64 MB free disk space.
70.24   warnings.warn(
70.24 /opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py:651: UserWarning: Not enough free disk space to download the file. The expected file size is: 154.88 MB. The target location models/snapshots/es only has 26.64 MB free disk space.
70.24   warnings.warn(
Fetching 4 files:  25%|██▌       | 1/4 [00:04<00:13,  4.54s/it]
74.61 Traceback (most recent call last):
74.61   File "/app/scripts/download_models.py", line 182, in <module>
74.61     main()
74.61   File "/app/scripts/download_models.py", line 176, in main
74.61     download_language(language=language, models_root=models_root)
74.61   File "/app/scripts/download_models.py", line 162, in download_language
74.62     download_snapshot_model(language, model_info, models_root)
74.62   File "/app/scripts/download_models.py", line 129, in download_snapshot_model
74.62     snapshot_root = snapshot_download(
74.62                     ^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
74.62     return fn(*args, **kwargs)
74.62            ^^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/_snapshot_download.py", line 296, in snapshot_download
74.62     thread_map(
74.62   File "/opt/venv/lib/python3.12/site-packages/tqdm/contrib/concurrent.py", line 69, in thread_map
74.62     return _executor_map(ThreadPoolExecutor, fn, *iterables, **tqdm_kwargs)
74.62            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/tqdm/contrib/concurrent.py", line 51, in _executor_map
74.62     return list(tqdm_class(ex.map(fn, *iterables, chunksize=chunksize), **kwargs))
74.62            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/tqdm/std.py", line 1181, in __iter__
74.62     for obj in iterable:
74.62   File "/usr/lib/python3.12/concurrent/futures/_base.py", line 619, in result_iterator
74.62     yield _result_or_cancel(fs.pop())
74.62           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
74.62   File "/usr/lib/python3.12/concurrent/futures/_base.py", line 317, in _result_or_cancel
74.62     return fut.result(timeout)
74.62            ^^^^^^^^^^^^^^^^^^^
74.62   File "/usr/lib/python3.12/concurrent/futures/_base.py", line 456, in result
74.62     return self.__get_result()
74.62            ^^^^^^^^^^^^^^^^^^^
74.62   File "/usr/lib/python3.12/concurrent/futures/_base.py", line 401, in __get_result
74.62     raise self._exception
74.62   File "/usr/lib/python3.12/concurrent/futures/thread.py", line 58, in run
74.62     result = self.fn(*self.args, **self.kwargs)
74.62              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/_snapshot_download.py", line 270, in _inner_hf_hub_download
74.62     return hf_hub_download(
74.62            ^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
74.62     return fn(*args, **kwargs)
74.62            ^^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 840, in hf_hub_download
74.62     return _hf_hub_download_to_local_dir(
74.62            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1136, in _hf_hub_download_to_local_dir
74.62     _download_to_tmp_and_move(
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1543, in _download_to_tmp_and_move
74.62     http_get(
74.62   File "/opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 455, in http_get
74.62     temp_file.write(chunk)
74.62 OSError: [Errno 28] No space left on device
------
Dockerfile:41
--------------------
  39 |
  40 |     # Download EN + ES models during docker build
  41 | >>> RUN python scripts/download_models.py --languages en es --models-root models
  42 |
  43 |     EXPOSE 8002
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python scripts/download_models.py --languages en es --models-root models" did not complete successfully: exit code: 1
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/gladia_asr_realtime#
