#!/bin/bash
# usage: rjm.sh BLEND RENDERJOB METRICSJOB -> one card job: render (jobs/RENDERJOB), then measure (jobs/METRICSJOB, measure_fix.py); prints job id
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/pond
CMD="/workspace/blender/blender -b --disable-autoexec $1 -P $D/render_fixpond.py -- $D/jobs/$2"
CMD="$CMD && /workspace/blender/blender -b --factory-startup -P $D/measure_fix.py -- $D/jobs/$3"
cd /tmp; python3 -I $R/render_client_serverless.py run "$CMD" --cwd $D --timeout 3000
