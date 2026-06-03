 => => transferring context: 217.58kB                                                                                           0.0s
 => CACHED [ 2/11] WORKDIR /app                                                                                                 0.0s
 => [ 3/11] RUN apt-get update && apt-get install -y     python3     python3-pip     python3-dev     build-essential     git  162.3s
 => ERROR [ 4/11] RUN python3 -m pip install --upgrade pip setuptools wheel                                                     1.8s
------
 > [ 4/11] RUN python3 -m pip install --upgrade pip setuptools wheel:
0.605 error: externally-managed-environment
0.605
0.605 × This environment is externally managed
0.605 ╰─> To install Python packages system-wide, try apt install
0.605     python3-xyz, where xyz is the package you are trying to
0.605     install.
0.605
0.605     If you wish to install a non-Debian-packaged Python package,
0.605     create a virtual environment using python3 -m venv path/to/venv.
0.605     Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
0.605     sure you have python3-full installed.
0.605
0.605     If you wish to install a non-Debian packaged Python application,
0.605     it may be easiest to use pipx install xyz, which will manage a
0.605     virtual environment for you. Make sure you have pipx installed.
0.605
0.605     See /usr/share/doc/python3.12/README.venv for more information.
0.605
0.605 note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
0.605 hint: See PEP 668 for the detailed specification.
------
Dockerfile:30
--------------------
  28 |     # Python base setup
  29 |     # ------------------------------------------------------------
  30 | >>> RUN python3 -m pip install --upgrade pip setuptools wheel
  31 |
  32 |     COPY requirements.txt /app/requirements.txt
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c python3 -m pip install --upgrade pip setuptools wheel" did not complete successfully: exit code: 1
(base) root@EC03-E01-AICOE1:/home/COR
