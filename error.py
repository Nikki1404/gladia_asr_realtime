 => [ 8/13] RUN python3.11 -m pip install --no-cache-dir     "nemo_toolkit[asr] @ git+https://github.com/NVIDIA/NeMo.git@main"           211.1s
 => ERROR [ 9/13] RUN python3.11 -m pip install --no-cache-dir --force-reinstall     torch==2.6.0     torchvision==0.21.0     torchaudi  141.4s
------
 > [ 9/13] RUN python3.11 -m pip install --no-cache-dir --force-reinstall     torch==2.6.0     torchvision==0.21.0     torchaudio==2.6.0     --index-url https://download.pytorch.org/whl/cu124:
1.905 Looking in indexes: https://download.pytorch.org/whl/cu124
2.092 Collecting torch==2.6.0
2.385   Downloading torch-2.6.0%2Bcu124-cp311-cp311-linux_x86_64.whl.metadata (28 kB)
2.499 Collecting torchvision==0.21.0
2.550   Downloading torchvision-0.21.0%2Bcu124-cp311-cp311-linux_x86_64.whl.metadata (6.1 kB)
2.635 Collecting torchaudio==2.6.0
2.666   Downloading torchaudio-2.6.0%2Bcu124-cp311-cp311-linux_x86_64.whl.metadata (6.6 kB)
2.753 Collecting filelock (from torch==2.6.0)
3.678   Downloading filelock-3.29.0-py3-none-any.whl.metadata (2.0 kB)
3.764 Collecting typing-extensions>=4.10.0 (from torch==2.6.0)
3.781   Downloading typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
3.906 Collecting networkx (from torch==2.6.0)
4.048   Downloading networkx-3.6.1-py3-none-any.whl.metadata (6.8 kB)
4.102 Collecting jinja2 (from torch==2.6.0)
4.116   Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
4.188 Collecting fsspec (from torch==2.6.0)
4.206   Downloading fsspec-2026.4.0-py3-none-any.whl.metadata (10 kB)
4.280 Collecting nvidia-cuda-nvrtc-cu12==12.4.127 (from torch==2.6.0)
4.302   Downloading nvidia_cuda_nvrtc_cu12-12.4.127-py3-none-manylinux2014_x86_64.whl (24.6 MB)
4.818      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 24.6/24.6 MB 48.5 MB/s  0:00:00
4.891 Collecting nvidia-cuda-runtime-cu12==12.4.127 (from torch==2.6.0)
4.905   Downloading nvidia_cuda_runtime_cu12-12.4.127-py3-none-manylinux2014_x86_64.whl (883 kB)
4.927      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 883.7/883.7 kB 48.7 MB/s  0:00:00
4.976 Collecting nvidia-cuda-cupti-cu12==12.4.127 (from torch==2.6.0)
4.992   Downloading nvidia_cuda_cupti_cu12-12.4.127-py3-none-manylinux2014_x86_64.whl (13.8 MB)
5.259      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 13.8/13.8 MB 51.7 MB/s  0:00:00
5.326 Collecting nvidia-cudnn-cu12==9.1.0.70 (from torch==2.6.0)
5.341   Downloading nvidia_cudnn_cu12-9.1.0.70-py3-none-manylinux2014_x86_64.whl (664.8 MB)
19.44      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 664.8/664.8 MB 46.5 MB/s  0:00:14
20.00 Collecting nvidia-cublas-cu12==12.4.5.8 (from torch==2.6.0)
20.02   Downloading nvidia_cublas_cu12-12.4.5.8-py3-none-manylinux2014_x86_64.whl (363.4 MB)
29.28      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 363.4/363.4 MB 37.1 MB/s  0:00:09
29.64 Collecting nvidia-cufft-cu12==11.2.1.3 (from torch==2.6.0)
29.66   Downloading nvidia_cufft_cu12-11.2.1.3-py3-none-manylinux2014_x86_64.whl (211.5 MB)
35.00      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 211.5/211.5 MB 39.6 MB/s  0:00:05
35.26 Collecting nvidia-curand-cu12==10.3.5.147 (from torch==2.6.0)
35.28   Downloading nvidia_curand_cu12-10.3.5.147-py3-none-manylinux2014_x86_64.whl (56.3 MB)
36.37      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 56.3/56.3 MB 51.8 MB/s  0:00:01
36.48 Collecting nvidia-cusolver-cu12==11.6.1.9 (from torch==2.6.0)
36.49   Downloading nvidia_cusolver_cu12-11.6.1.9-py3-none-manylinux2014_x86_64.whl (127.9 MB)
38.97      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 127.9/127.9 MB 51.7 MB/s  0:00:02
39.11 Collecting nvidia-cusparse-cu12==12.3.1.170 (from torch==2.6.0)
39.14   Downloading nvidia_cusparse_cu12-12.3.1.170-py3-none-manylinux2014_x86_64.whl (207.5 MB)
43.54      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 207.5/207.5 MB 47.1 MB/s  0:00:04
43.79 Collecting nvidia-cusparselt-cu12==0.6.2 (from torch==2.6.0)
43.80   Downloading nvidia_cusparselt_cu12-0.6.2-py3-none-manylinux2014_x86_64.whl.metadata (6.8 kB)
43.88 Collecting nvidia-nccl-cu12==2.21.5 (from torch==2.6.0)
43.90   Downloading nvidia_nccl_cu12-2.21.5-py3-none-manylinux2014_x86_64.whl (188.7 MB)
48.76      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 188.7/188.7 MB 38.8 MB/s  0:00:04
48.97 Collecting nvidia-nvtx-cu12==12.4.127 (from torch==2.6.0)
48.99   Downloading nvidia_nvtx_cu12-12.4.127-py3-none-manylinux2014_x86_64.whl (99 kB)
49.05 Collecting nvidia-nvjitlink-cu12==12.4.127 (from torch==2.6.0)
49.06   Downloading nvidia_nvjitlink_cu12-12.4.127-py3-none-manylinux2014_x86_64.whl (21.1 MB)
49.60      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 21.1/21.1 MB 39.0 MB/s  0:00:00
49.70 Collecting triton==3.2.0 (from torch==2.6.0)
49.73   Downloading triton-3.2.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (1.4 kB)
49.82 Collecting sympy==1.13.1 (from torch==2.6.0)
49.86   Downloading sympy-1.13.1-py3-none-any.whl.metadata (12 kB)
50.23 Collecting numpy (from torchvision==0.21.0)
50.25   Downloading numpy-2.4.4-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
50.56 Collecting pillow!=8.3.*,>=5.3.0 (from torchvision==0.21.0)
50.57   Downloading pillow-12.2.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (8.8 kB)
50.66 Collecting mpmath<1.4,>=1.1.0 (from sympy==1.13.1->torch==2.6.0)
50.68   Downloading mpmath-1.3.0-py3-none-any.whl.metadata (8.6 kB)
50.75 Collecting MarkupSafe>=2.0 (from jinja2->torch==2.6.0)
50.77   Downloading markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
50.79 Downloading torch-2.6.0%2Bcu124-cp311-cp311-linux_x86_64.whl (768.5 MB)
70.90    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 768.5/768.5 MB 46.4 MB/s  0:00:20
70.95 Downloading torchvision-0.21.0%2Bcu124-cp311-cp311-linux_x86_64.whl (7.3 MB)
71.12    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7.3/7.3 MB 40.9 MB/s  0:00:00
71.16 Downloading torchaudio-2.6.0%2Bcu124-cp311-cp311-linux_x86_64.whl (3.4 MB)
71.23    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.4/3.4 MB 48.3 MB/s  0:00:00
71.25 Downloading nvidia_cusparselt_cu12-0.6.2-py3-none-manylinux2014_x86_64.whl (150.1 MB)
74.35    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 150.1/150.1 MB 48.6 MB/s  0:00:03
74.36 Downloading sympy-1.13.1-py3-none-any.whl (6.2 MB)
74.61    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.2/6.2 MB 26.6 MB/s  0:00:00
74.67 Downloading triton-3.2.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (166.7 MB)
79.03    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 166.7/166.7 MB 38.3 MB/s  0:00:04
79.04 Downloading mpmath-1.3.0-py3-none-any.whl (536 kB)
79.05    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 536.2/536.2 kB 49.0 MB/s  0:00:00
79.06 Downloading pillow-12.2.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (7.1 MB)
79.20    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7.1/7.1 MB 52.1 MB/s  0:00:00
79.26 Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
79.27 Downloading filelock-3.29.0-py3-none-any.whl (39 kB)
79.29 Downloading fsspec-2026.4.0-py3-none-any.whl (203 kB)
79.32 Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
79.35 Downloading markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
79.36 Downloading networkx-3.6.1-py3-none-any.whl (2.1 MB)
79.41    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 44.3 MB/s  0:00:00
79.42 Downloading numpy-2.4.4-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.9 MB)
79.78    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.9/16.9 MB 47.5 MB/s  0:00:00
81.14 Installing collected packages: triton, nvidia-cusparselt-cu12, mpmath, typing-extensions, sympy, pillow, nvidia-nvtx-cu12, nvidia-nvjitlink-cu12, nvidia-nccl-cu12, nvidia-curand-cu12, nvidia-cufft-cu12, nvidia-cuda-runtime-cu12, nvidia-cuda-nvrtc-cu12, nvidia-cuda-cupti-cu12, nvidia-cublas-cu12, numpy, networkx, MarkupSafe, fsspec, filelock, nvidia-cusparse-cu12, nvidia-cudnn-cu12, jinja2, nvidia-cusolver-cu12, torch, torchvision, torchaudio
81.14   Attempting uninstall: triton
81.14     Found existing installation: triton 3.7.0
81.17     Uninstalling triton-3.7.0:
93.27       Successfully uninstalled triton-3.7.0
100.4   Attempting uninstall: mpmath
100.4     Found existing installation: mpmath 1.3.0
100.4     Uninstalling mpmath-1.3.0:
100.6       Successfully uninstalled mpmath-1.3.0
101.0   Attempting uninstall: typing-extensions
101.0     Found existing installation: typing_extensions 4.15.0
101.1     Uninstalling typing_extensions-4.15.0:
105.5       Successfully uninstalled typing_extensions-4.15.0
105.5   Attempting uninstall: sympy
105.5     Found existing installation: sympy 1.14.0
105.7     Uninstalling sympy-1.14.0:
110.7       Successfully uninstalled sympy-1.14.0
116.7   Attempting uninstall: pillow
116.7     Found existing installation: pillow 12.2.0
116.7     Uninstalling pillow-12.2.0:
117.1       Successfully uninstalled pillow-12.2.0
140.7 ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device
140.7
140.7
------
Dockerfile:62
--------------------
  61 |     # cu124 is compatible with host CUDA 12.6 driver.
  62 | >>> RUN python3.11 -m pip install --no-cache-dir --force-reinstall \
  63 | >>>     torch==2.6.0 \
  64 | >>>     torchvision==0.21.0 \
  65 | >>>     torchaudio==2.6.0 \
  66 | >>>     --index-url https://download.pytorch.org/whl/cu124
  67 |
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python3.11 -m pip install --no-cache-dir --force-reinstall     torch==2.6.0     torchvision==0.21.0     torchaudio==2.6.0     --index-url https://download.pytorch.org/whl/cu124" did not complete successfully: exit code: 1
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/nemotron_asr#
