#!/bin/bash
# usage: rm.sh JOBFILE OUTDIRNAME -> render job then mask analysis (masks.json) on the card; the mask PNGs stay on the store (never downloaded)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond
O=$D/previews/$2
python3 -I $R/render_client_serverless.py run "/workspace/blender/blender -b --disable-autoexec -P $D/render_pond.py -- $D/jobs/$1 && /workspace/blender/blender -b --factory-startup -P $D/test_pond.py -- masks $O/masks.json $O" --cwd $D --timeout 3000
