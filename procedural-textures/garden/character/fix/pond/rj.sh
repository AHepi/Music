#!/bin/bash
# usage: rj.sh BLEND JOBFILE [then-command...] -> submits one render job on the card (Blender on BLEND with render_fixpond.py and jobs/JOBFILE); prints job id
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/pond
BL=$1; J=$2; shift; shift
CMD="/workspace/blender/blender -b --disable-autoexec $BL -P $D/render_fixpond.py -- $D/jobs/$J"
for extra in "$@"; do CMD="$CMD && $extra"; done
cd /tmp; python3 -I $R/render_client_serverless.py run "$CMD" --cwd $D --timeout 3000
