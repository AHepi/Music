#!/bin/bash
# usage: go.sh KIND JOBFILE   KIND = render (render_fix.py on the card) | build (build_fix.py on the card, opens the start scene)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/direction/start/garden_real_fixed.blend
C=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/garden_character.blend
B=/workspace/blender/blender
case "$1" in
 stages) CMD="$B -b --disable-autoexec $S -P $D/render_fix.py -- $D/jobs/$2" ;;
 before) CMD="$B -b --disable-autoexec $C -P $D/render_fix.py -- $D/jobs/$2" ;;
 build)  CMD="$B -b --disable-autoexec $S -P $D/build_fix.py -- $D/jobs/$2" ;;
 *) echo bad kind; exit 1 ;;
esac
python3 -I $R/render_client_serverless.py run "$CMD" --cwd $D --timeout 3000
