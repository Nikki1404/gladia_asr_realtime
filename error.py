 => [ 4/10] COPY requirements.txt .                                                                                0.5s
 => ERROR [ 5/10] RUN python3 -m pip install --upgrade pip --break-system-packages &&     python3 -m pip install   1.1s
------
 > [ 5/10] RUN python3 -m pip install --upgrade pip --break-system-packages &&     python3 -m pip install -r requirements.txt --break-system-packages:
0.538 Requirement already satisfied: pip in /usr/lib/python3/dist-packages (24.0)
0.739 Collecting pip
0.866   Downloading pip-26.1.2-py3-none-any.whl.metadata (4.6 kB)
0.882 Downloading pip-26.1.2-py3-none-any.whl (1.8 MB)
0.969    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB 27.9 MB/s eta 0:00:00
0.989 Installing collected packages: pip
0.990   Attempting uninstall: pip
0.992     Found existing installation: pip 24.0
0.993 ERROR: Cannot uninstall pip 24.0, RECORD file not found. Hint: The package was installed by debian.
------
Dockerfile:21
--------------------
  20 |
  21 | >>> RUN python3 -m pip install --upgrade pip --break-system-packages && \
  22 | >>>     python3 -m pip install -r requirements.txt --break-system-packages
  23 |
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python3 -m pip install --upgrade pip --break-system-packages &&     python3 -m pip install -r requirements.txt --break-system-packages" did not complete successfully: exit code: 1
