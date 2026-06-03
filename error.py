 => [11/12] COPY client.py ./client.py                                                                             0.1s
 => ERROR [12/12] RUN python scripts/download_models.py --languages en --models-root models                       52.3s
------
 > [12/12] RUN python scripts/download_models.py --languages en --models-root models:
0.425 Downloading language=en
0.425 Repo: xumo/onnx_models
0.425 File: sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2
7.124 Extracting models/downloads/sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2 -> models/extracted/en
52.19 Traceback (most recent call last):
52.19   File "/app/scripts/download_models.py", line 111, in <module>
52.19     main()
52.19   File "/app/scripts/download_models.py", line 105, in main
52.20     download_language(language=language, models_root=models_root)
52.20   File "/app/scripts/download_models.py", line 91, in download_language
52.20     find_and_copy_required_files(extract_root, final_dir)
52.20   File "/app/scripts/download_models.py", line 41, in find_and_copy_required_files
52.20     raise FileNotFoundError(
52.20 FileNotFoundError: Could not find encoder.onnx under models/extracted/en
------
Dockerfile:38
--------------------
  36 |
  37 |     # Download EN + ES models during docker build
  38 | >>> RUN python scripts/download_models.py --languages en --models-root models
  39 |
  40 |     EXPOSE 8002
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python scripts/download_models.py --languages en --models-root models" did not complete successfully: exit code: 1
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/gladia_asr_realtime#
