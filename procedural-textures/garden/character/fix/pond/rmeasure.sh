#!/bin/bash
# usage: rmeasure.sh METRICSJOB -> one card job: measure_fix.py with jobs/METRICSJOB (pictures already on the store)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/pond
cd /tmp; python3 -I $R/render_client_serverless.py run "/workspace/blender/blender -b --factory-startup -P $D/measure_fix.py -- $D/jobs/$1" --cwd $D --timeout 1500
