#!/bin/bash
# one card job: build the combined garden with the four fixed stages + stage_final, save garden_character_fix.blend on the store only
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/final
START=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/direction/start/garden_real_fixed.blend
cd /tmp; python3 -I $R/render_client_serverless.py run "mkdir -p $D/out && /workspace/blender/blender -b --disable-autoexec $START -P $D/build_fix_final.py -- $D/jobs/build.json" --cwd $D --timeout 3000
