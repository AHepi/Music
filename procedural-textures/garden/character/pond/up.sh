#!/bin/bash
# uploads the pond builder's scripts and small inputs to the RunPod store (same absolute paths): up.sh file1 file2 ... (relative to this folder)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond
for f in "$@"; do python3 -I $R/render_client_serverless.py upload $D/$f --remote $D/$f | tail -1; done
