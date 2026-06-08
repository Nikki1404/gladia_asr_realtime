 => [10/13] RUN python3.11 - <<'EOF'                                                                                                       4.3s
 => ERROR [11/13] RUN python3.11 - <<'EOF'                                                                                                18.3s
------
 > [11/13] RUN python3.11 - <<'EOF':
15.47 OneLogger: Setting error_handling_strategy to DISABLE_QUIETLY_AND_REPORT_METRIC_ERROR for rank (rank=0) with OneLogger disabled. To override: explicitly set error_handling_strategy parameter.
15.48 No exporters were provided. This means that no telemetry data will be collected.
17.26 Traceback (most recent call last):
17.26   File "<stdin>", line 6, in <module>
17.26   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
17.26     return _bootstrap._gcd_import(name[level:], package, level)
17.26            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17.26   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
17.26   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
17.26   File "<frozen importlib._bootstrap>", line 1126, in _find_and_load_unlocked
17.26   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
17.26   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
17.26   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
17.26   File "<frozen importlib._bootstrap>", line 1126, in _find_and_load_unlocked
17.26   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
17.26   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
17.26   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
17.26   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
17.26   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
17.26   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
17.26   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
17.26   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/__init__.py", line 15, in <module>
17.26     from nemo.collections.asr import data, losses, models, modules
17.26   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/models/__init__.py", line 15, in <module>
17.26     from nemo.collections.asr.models.aed_multitask_models import EncDecMultiTaskModel  # noqa: F401
17.26     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17.26   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/models/aed_multitask_models.py", line 32, in <module>
17.26     from nemo.collections.asr.metrics import MultiTaskMetric
17.26   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/metrics/__init__.py", line 15, in <module>
17.27     from nemo.collections.asr.metrics.bleu import BLEU
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/metrics/bleu.py", line 23, in <module>
17.27     from nemo.collections.asr.parts.submodules.ctc_decoding import AbstractCTCDecoding
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/submodules/ctc_decoding.py", line 25, in <module>
17.27     from nemo.collections.asr.parts.submodules import ctc_beam_decoding, ctc_greedy_decoding
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/submodules/ctc_beam_decoding.py", line 24, in <module>
17.27     from nemo.collections.asr.parts.context_biasing import BoostingTreeModelConfig, GPUBoostingTreeModel
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/context_biasing/__init__.py", line 19, in <module>
17.27     from nemo.collections.asr.parts.context_biasing.context_biasing_utils import (
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/context_biasing/context_biasing_utils.py", line 22, in <module>
17.27     from nemo.collections.asr.parts.utils import rnnt_utils
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/utils/__init__.py", line 15, in <module>
17.27     from nemo.collections.asr.parts.utils.rnnt_utils import Hypothesis, NBestHypotheses
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/utils/rnnt_utils.py", line 34, in <module>
17.27     from nemo.collections.asr.parts.context_biasing.biasing_multi_model import BiasingRequestItemConfig
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/context_biasing/biasing_multi_model.py", line 258, in <module>
17.27     class GPUBiasingMultiModel(GPUBiasingMultiModelBase):
17.27   File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/parts/context_biasing/biasing_multi_model.py", line 340, in GPUBiasingMultiModel
17.28     def _extend_buffer_or_param(buffer_or_param: nn.Buffer | nn.Parameter, add_len: int):
17.28                                                  ^^^^^^^^^
17.28 AttributeError: module 'torch.nn' has no attribute 'Buffer'
------
Dockerfile:81
--------------------
  80 |     # 8. Validate required Nemotron class exists
  81 | >>> RUN python3.11 - <<'EOF'
  82 | >>> import importlib
  83 | >>>
  84 | >>> module_name = "nemo.collections.asr.models.rnnt_bpe_models_prompt"
  85 | >>> class_name = "EncDecRNNTBPEModelWithPrompt"
  86 | >>>
  87 | >>> mod = importlib.import_module(module_name)
  88 | >>> cls = getattr(mod, class_name)
  89 | >>>
  90 | >>> print("NeMo Nemotron prompt RNNT class found:", cls)
  91 | >>> EOF
  92 |
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python3.11 - <<'EOF'\nimport importlib\n\nmodule_name = \"nemo.collections.asr.models.rnnt_bpe_models_prompt\"\nclass_name = \"EncDecRNNTBPEModelWithPrompt\"\n\nmod = importlib.import_module(module_name)\ncls = getattr(mod, class_name)\n\nprint(\"NeMo Nemotron prompt RNNT class found:\", cls)\nEOF" did not complete successfully: exit code: 1
