#!/bin/bash
# one card job: build the combined garden with the fixed pond stage (build_fixpond.py), saved on the store only; prints the job id
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/pond
START=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/direction/start/garden_real_fixed.blend
mkdir -p $D/out
cd /tmp; python3 -I $R/render_client_serverless.py run "mkdir -p $D/out && /workspace/blender/blender -b --disable-autoexec $START -P $D/build_fixpond.py -- $D/jobs/build_fixpond.json" --cwd $D --timeout 3000
