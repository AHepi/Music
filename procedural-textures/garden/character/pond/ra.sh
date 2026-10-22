#!/bin/bash
# usage: ra.sh JOBFILE OUTDIR_NAME  -> render job, then analysis of before_*/A_* PNGs in previews/OUTDIR_NAME, on the card (one job); prints the job id
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond
O=$D/previews/$2
python3 -I $R/render_client_serverless.py run "/workspace/blender/blender -b --disable-autoexec -P $D/render_pond.py -- $D/jobs/$1 && /workspace/blender/blender -b --factory-startup -P $D/test_pond.py -- analyze $O/analysis.json $O/before_hero.png photo $O/A_hero.png photo $O/before_veranda.png veranda $O/A_veranda.png veranda" --cwd $D --timeout 3000
