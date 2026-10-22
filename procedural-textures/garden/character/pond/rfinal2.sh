#!/bin/bash
# the final round: render (final proofs 2400x1600 at 512 samples + crops + masks), then the picture analysis, the mask analysis and small JPGs, all on the card (one job)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond
O=$D/previews/final
BL="/workspace/blender/blender -b --factory-startup -P $D/test_pond.py --"
CMD="/workspace/blender/blender -b --disable-autoexec -P $D/render_pond.py -- $D/jobs/final2.json"
CMD="$CMD && $BL analyze $O/analysis.json $O/before_hero.png photo $O/A_hero.png photo $O/before_veranda.png veranda $O/A_veranda.png veranda"
CMD="$CMD && $BL masks $O/masks.json $O"
for f in A_hero A_veranda before_hero before_veranda; do CMD="$CMD && $BL jpg $O/$f.png $O/${f}_1600.jpg 1600 80"; done
python3 -I $R/render_client_serverless.py run "$CMD" --cwd $D --timeout 3000
