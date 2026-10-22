#!/bin/bash
# usage: dl.sh REMOTE_PATH LOCAL_PATH  (downloads one small file from the store)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
cd /tmp; python3 -I $R/render_client_serverless.py download "$1" --local "$2" | tail -1
