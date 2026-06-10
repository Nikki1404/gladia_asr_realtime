(nemo_env) root@cx-asr-test:/home/nikita_verma2/nemotron_asr# tail nemotron_benchmark.log 
           ^^^^^^^^^^^^^^^
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 642, in run_benchmark
    download_inputs()
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 145, in download_inputs
    gcs_cp_many(f"{REFERENCE_GCS}/maria*_reference.text", REF_DIR)
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 124, in gcs_cp_many
    run_cmd(["gcloud", "storage", "cp", src_pattern, str(dst_dir)])
  File "/home/nikita_verma2/nemotron_asr/benchmark_maria_nemotron.py", line 99, in run_cmd
    raise RuntimeError(f"Command failed: {' '.join(cmd)}")
RuntimeError: Command failed: gcloud storage cp gs://cx-asr-test-data/references/maria*_reference.text benchmark_workspace/references


gs://cx-asr-test-data/references/herring7_reference.txt
gs://cx-asr-test-data/references/herring8_reference.txt
gs://cx-asr-test-data/references/herring9_reference.txt
gs://cx-asr-test-data/references/maria10_reference.txt
gs://cx-asr-test-data/references/maria16_reference.txt
gs://cx-asr-test-data/references/maria18_reference.txt
gs://cx-asr-test-data/references/maria19_reference.txt
gs://cx-asr-test-data/references/maria1_reference.txt
gs://cx-asr-test-data/references/maria20_reference.txt
gs://cx-asr-test-data/references/maria21_reference.txt
gs://cx-asr-test-data/references/maria24_reference.txt
gs://cx-asr-test-data/references/maria27_reference.txt
gs://cx-asr-test-data/references/maria2_reference.txt
gs://cx-asr-test-data/references/maria30_reference.txt
gs://cx-asr-test-data/references/maria31_reference.txt
gs://cx-asr-test-data/references/maria40_reference.txt
gs://cx-asr-test-data/references/maria4_reference.txt
gs://cx-asr-test-data/references/maria7_reference.txt
gs://cx-asr-test-data/references/sastre10_reference.txt
