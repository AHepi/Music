#!/bin/bash
# usage: rr.sh JOBFILE  -> submits a render job on the card, prints the job id (job files are in jobs/)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond
python3 -I $R/render_client_serverless.py run "/workspace/blender/blender -b --disable-autoexec -P $D/render_pond.py -- $D/jobs/$1" --cwd $D --timeout 3000
