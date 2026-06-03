 => [11/12] COPY client.py ./client.py                                                                             0.1s
 => ERROR [12/12] RUN python scripts/download_models.py --languages en es --models-root models                     4.7s
------
 > [12/12] RUN python scripts/download_models.py --languages en es --models-root models:
0.424 Downloading language=en, file=Kroko-EN-Community-64-L-Streaming-001.data
0.424 /opt/venv/lib/python3.12/site-packages/huggingface_hub/file_download.py:832: UserWarning: `local_dir_use_symlinks` parameter is deprecated and will be ignored. The process to download files to a local folder has been updated and do not rely on symlinks anymore. You only need to pass a destination folder as`local_dir`.
0.424 For more details, check out https://huggingface.co/docs/huggingface_hub/main/en/guides/download#download-files-to-local-folder.
0.424   warnings.warn(
4.627 Extracting models/downloads/Kroko-EN-Community-64-L-Streaming-001.data -> models/streaming_transducers/64/en
4.628 Traceback (most recent call last):
4.628   File "/app/scripts/download_models.py", line 106, in <module>
4.628     main()
4.628   File "/app/scripts/download_models.py", line 100, in main
4.628     download_language(language=language, models_root=models_root)
4.629   File "/app/scripts/download_models.py", line 85, in download_language
4.629     extract_archive(downloaded_path, output_dir)
4.629   File "/app/scripts/download_models.py", line 46, in extract_archive
4.629     raise RuntimeError(
4.629 RuntimeError: Unsupported model archive format: models/downloads/Kroko-EN-Community-64-L-Streaming-001.data. Expected tar or zip-like .data archive.
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
