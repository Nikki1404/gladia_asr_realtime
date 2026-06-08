
DEBUG: Startup cfg.model_name='/srv/nemotron-3.5-asr-streaming-0.6b.nemo' cfg.asr_backend='nemotron'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
2026-06-08 14:46:52,584 | INFO | asr_server | Server startup initiated
2026-06-08 14:46:52,584 | INFO | asr_server | Preloading ASR engines...
2026-06-08 14:46:52,584 | INFO | asr_server | Initializing engine: nemotron (/srv/nemotron-3.5-asr-streaming-0.6b.nemo)
2026-06-08 14:46:58,754 | WARNING | nv_one_logger.api.config | OneLogger: Setting error_handling_strategy to DISABLE_QUIETLY_AND_REPORT_METRIC_ERROR for rank (rank=0) with OneLogger disabled. To override: explicitly set error_handling_strategy parameter.
2026-06-08 14:46:58,765 | INFO | nv_one_logger.exporter.export_config_manager | Final configuration contains 0 exporter(s)
2026-06-08 14:46:58,765 | WARNING | nv_one_logger.training_telemetry.api.training_telemetry_provider | No exporters were provided. This means that no telemetry data will be collected.
[NeMo I 2026-06-08 14:47:34 mixins:184] Tokenizer SentencePieceTokenizer initialized with 13087 tokens
[NeMo W 2026-06-08 14:47:39 modelPT:288] You tried to register an artifact under config key=tokenizer.model_path but an artifact for it has already been registered.
[NeMo W 2026-06-08 14:47:39 modelPT:288] You tried to register an artifact under config key=tokenizer.vocab_path but an artifact for it has already been registered.
[NeMo I 2026-06-08 14:47:40 mixins:184] Tokenizer SentencePieceTokenizer initialized with 13087 tokens
[NeMo E 2026-06-08 14:47:46 common:644] Model instantiation failed!
    Target class:       nemo.collections.asr.models.rnnt_bpe_models_prompt.EncDecRNNTBPEModelWithPrompt
    Error(s):   The NVIDIA driver on your system is too old (found version 12060). Please update your GPU driver by downloading and installing a new version from the URL: http://www.nvidia.com/Download/index.aspx Alternatively, go to: https://pytorch.org to install a PyTorch version that has been compiled with your version of the CUDA driver.
    Traceback (most recent call last):
      File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 621, in from_config_dict
        instance = imported_cls(cfg=config, trainer=trainer)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/models/rnnt_bpe_models_prompt.py", line 102, in __init__
        super().__init__(cfg=cfg, trainer=trainer)
      File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/models/rnnt_bpe_models.py", line 245, in __init__
        super().__init__(cfg=cfg, trainer=trainer)
      File "/usr/local/lib/python3.11/site-packages/nemo/collections/asr/models/rnnt_models.py", line 63, in __init__
        super().__init__(cfg=cfg, trainer=trainer)
      File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/modelPT.py", line 145, in __init__
        if torch.cuda.is_available() and torch.cuda.current_device() is not None:
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/usr/local/lib/python3.11/site-packages/torch/cuda/__init__.py", line 1167, in current_device
        _lazy_init()
      File "/usr/local/lib/python3.11/site-packages/torch/cuda/__init__.py", line 491, in _lazy_init
        torch._C._cuda_init()
    RuntimeError: The NVIDIA driver on your system is too old (found version 12060). Please update your GPU driver by downloading and installing a new version from the URL: http://www.nvidia.com/Download/index.aspx Alternatively, go to: https://pytorch.org to install a PyTorch version that has been compiled with your version of the CUDA driver.

2026-06-08 14:47:47,278 | ERROR | asr_server | Failed to preload 'nemotron'
Traceback (most recent call last):
  File "/srv/app/main.py", line 47, in preload_engines
    load_sec = engine.load()
               ^^^^^^^^^^^^^
  File "/srv/app/asr_engines/nemotron_asr.py", line 115, in load
    self.model = nemo_asr.models.ASRModel.restore_from(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/modelPT.py", line 490, in restore_from
    instance = cls._save_restore_connector.restore_from(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/nemo/core/connectors/save_restore_connector.py", line 271, in restore_from
INFO:     Application startup complete.
    loaded_params = self.load_config_and_state_dict(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/nemo/core/connectors/save_restore_connector.py", line 192, in load_config_and_state_dict
    instance = calling_cls.from_config_dict(config=conf, trainer=trainer)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 645, in from_config_dict
    raise e
  File "/usr/local/lib/python3.11/site-packages/nemo/core/classes/common.py", line 637, in from_config_dict
    instance = cls(cfg=config, trainer=trainer)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Can't instantiate abstract class ASRModel with abstract methods setup_training_data, setup_validation_data
2026-06-08 14:47:47,281 | INFO | asr_server | All engines preloaded. Available: []
INFO:     Uvicorn running on http://0.0.0.0:8003 (Press CTRL+C to quit)
