#!/bin/bash
# usage: dl.sh SUBDIR name1 name2 ...   (downloads out/SUBDIR/name.jpg from the store into the same local place)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof
sub=$1; shift
mkdir -p $D/out/$sub
for n in "$@"; do python3 -I $R/render_client_serverless.py download $D/out/$sub/$n.jpg --local $D/out/$sub/$n.jpg >/dev/null 2>&1 || echo "FAILED $n"; done
ls -la $D/out/$sub | head -50
