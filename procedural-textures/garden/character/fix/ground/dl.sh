#!/bin/bash
# usage: dl.sh ROUND name1 name2 ...  -> downloads previews/ROUND/<name>.jpg from the store into previews/ROUND/
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/ground
r=$1; shift
mkdir -p $D/previews/$r
for n in "$@"; do python3 -I $R/render_client_serverless.py download $D/previews/$r/$n --local $D/previews/$r/$n | tail -1; done
