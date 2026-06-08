 => ERROR [ 8/11] RUN python3.11 -m pip install --no-cache-dir     "git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]"     3.6s
------
 > [ 8/11] RUN python3.11 -m pip install --no-cache-dir     "git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]":
0.763 error: invalid-egg-fragment
0.763
0.763 × The 'nemo_toolkit[asr]' egg fragment is invalid
0.763 ╰─> from 'git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]'
0.763
0.763 hint: Try using the Direct URL requirement syntax: 'name[extra] @ URL'
------
Dockerfile:55
--------------------
  54 |     # Required because Nemotron 3.5 ASR uses new prompt-conditioned RNNT classes.
  55 | >>> RUN python3.11 -m pip install --no-cache-dir \
  56 | >>>     "git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]"
  57 |
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python3.11 -m pip install --no-cache-dir     \"git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]\"" did not complete successfully: exit code: 1
