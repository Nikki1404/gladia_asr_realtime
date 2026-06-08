 => [6/9] COPY requirements.txt .                                                                                                          0.1s
 => [7/9] RUN python3.11 -m pip install --no-cache-dir -r requirements.txt                                                               250.4s
 => ERROR [8/9] RUN python3.11 - <<EOF                                                                                                   132.3s
------
 > [8/9] RUN python3.11 - <<EOF:
15.89 [NeMo W 2026-06-08 13:13:45 nemo_logging:405] Megatron num_microbatches_calculator not found, using Apex version.
16.63 OneLogger: Setting error_handling_strategy to DISABLE_QUIETLY_AND_REPORT_METRIC_ERROR for rank (rank=0) with OneLogger disabled. To override: explicitly set error_handling_strategy parameter.
16.65 No exporters were provided. This means that no telemetry data will be collected.
20.54 Downloading Nemotron 3.5 from HuggingFace...
129.5 [NeMo E 2026-06-08 13:15:39 nemo_logging:417] Model instantiation failed!
129.5     Target class: nemo.collections.asr.models.rnnt_bpe_models_prompt.EncDecRNNTBPEModelWithPrompt
129.5     Error(s):     No module named 'nemo.collections.asr.models.rnnt_bpe_models_prompt'
129.5     Traceback (most recent call last):
129.5       File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 619, in from_config_dict
129.5         imported_cls = import_class_by_path(target_cls_path)
129.5                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
129.5       File "/usr/local/lib/python3.11/site-packages/nemo/utils/model_utils.py", line 585, in import_class_by_path
129.5         mod = __import__(path, fromlist=[class_name])
129.5               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
129.5     ModuleNotFoundError: No module named 'nemo.collections.asr.models.rnnt_bpe_models_prompt'
129.5
130.1 Traceback (most recent call last):
130.1   File "<stdin>", line 3, in <module>
130.1   File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 885, in from_pretrained
130.1     instance = class_.restore_from(
130.1                ^^^^^^^^^^^^^^^^^^^^
130.1   File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/modelPT.py", line 501, in restore_from
130.1     instance = cls._save_restore_connector.restore_from(
130.1                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130.1   File "/usr/local/lib/python3.11/site-packages/nemo/core/connectors/save_restore_connector.py", line 269, in restore_from
130.1     loaded_params = self.load_config_and_state_dict(
130.1                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130.1   File "/usr/local/lib/python3.11/site-packages/nemo/core/connectors/save_restore_connector.py", line 190, in load_config_and_state_dict
130.1     instance = calling_cls.from_config_dict(config=conf, trainer=trainer)
130.1                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130.1   File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 650, in from_config_dict
130.1     raise e
130.1   File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 642, in from_config_dict
130.1     instance = cls(cfg=config, trainer=trainer)
130.1                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130.1 TypeError: Can't instantiate abstract class ASRModel with abstract methods setup_training_data, setup_validation_data
------
Dockerfile:43
--------------------
  42 |     # 4. Download Nemotron model during build
  43 | >>> RUN python3.11 - <<EOF
  44 | >>> import nemo.collections.asr as nemo_asr
  45 | >>> print("Downloading Nemotron 3.5 from HuggingFace...")
  46 | >>> model = nemo_asr.models.ASRModel.from_pretrained(
  47 | >>>     "nvidia/nemotron-3.5-asr-streaming-0.6b"
  48 | >>> )
  49 | >>> model.save_to("/srv/nemotron-3.5-asr-streaming-0.6b.nemo")
  50 | >>> print("Nemotron saved successfully.")
  51 | >>> EOF
  52 |     # 5. Copy app
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python3.11 - <<EOF\nimport nemo.collections.asr as nemo_asr\nprint(\"Downloading Nemotron 3.5 from HuggingFace...\")\nmodel = nemo_asr.models.ASRModel.from_pretrained(\n    \"nvidia/nemotron-3.5-asr-streaming-0.6b\"\n)\nmodel.save_to(\"/srv/nemotron-3.5-asr-streaming-0.6b.nemo\")\nprint(\"Nemotron saved successfully.\")\nEOF" did not complete successfully: exit code: 1
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/nemotron_asr#
