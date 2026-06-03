 => => transferring context: 17.04kB                                                                               0.0s
 => [2/9] WORKDIR /app                                                                                             0.4s
 => ERROR [3/9] RUN apt-get update && apt-get install -y     build-essential     libsndfile1     ffmpeg     curl   8.2s
------
 > [3/9] RUN apt-get update && apt-get install -y     build-essential     libsndfile1     ffmpeg     curl     && rm -rf /var/lib/apt/lists/*:
0.649 Ign:1 http://deb.debian.org/debian trixie InRelease
0.690 Ign:2 http://deb.debian.org/debian trixie-updates InRelease
0.730 Ign:3 http://deb.debian.org/debian-security trixie-security InRelease
1.772 Ign:3 http://deb.debian.org/debian-security trixie-security InRelease
1.812 Ign:2 http://deb.debian.org/debian trixie-updates InRelease
1.851 Ign:1 http://deb.debian.org/debian trixie InRelease
3.892 Ign:1 http://deb.debian.org/debian trixie InRelease
3.932 Ign:2 http://deb.debian.org/debian trixie-updates InRelease
3.972 Ign:3 http://deb.debian.org/debian-security trixie-security InRelease
8.011 Err:3 http://deb.debian.org/debian-security trixie-security InRelease
8.011   Connection failed [IP: 151.101.54.132 80]
8.054 Err:2 http://deb.debian.org/debian trixie-updates InRelease
8.054   Connection failed [IP: 151.101.54.132 80]
8.093 Err:1 http://deb.debian.org/debian trixie InRelease
8.093   Connection failed [IP: 151.101.54.132 80]
8.098 Reading package lists...
8.113 W: Failed to fetch http://deb.debian.org/debian/dists/trixie/InRelease  Connection failed [IP: 151.101.54.132 80]
8.113 W: Failed to fetch http://deb.debian.org/debian/dists/trixie-updates/InRelease  Connection failed [IP: 151.101.54.132 80]
8.113 W: Failed to fetch http://deb.debian.org/debian-security/dists/trixie-security/InRelease  Connection failed [IP: 151.101.54.132 80]
8.113 W: Some index files failed to download. They have been ignored, or old ones used instead.
8.131 Reading package lists...
8.142 Building dependency tree...
8.143 Reading state information...
8.144 E: Unable to locate package build-essential
8.144 E: Unable to locate package libsndfile1
8.144 E: Unable to locate package ffmpeg
8.144 E: Unable to locate package curl
------
Dockerfile:8
--------------------
   7 |
   8 | >>> RUN apt-get update && apt-get install -y \
   9 | >>>     build-essential \
  10 | >>>     libsndfile1 \
  11 | >>>     ffmpeg \
  12 | >>>     curl \
  13 | >>>     && rm -rf /var/lib/apt/lists/*
  14 |
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c apt-get update && apt-get install -y     build-essential     libsndfile1     ffmpeg     curl     && rm -rf /var/lib/apt/lists/*" did not complete successfully: exit code: 100
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/gladia_asr_realtime#
