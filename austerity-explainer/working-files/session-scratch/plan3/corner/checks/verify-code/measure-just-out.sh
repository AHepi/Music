#!/usr/bin/env bash
# Measures the pail pushed 0.50 m right (its outline just past the frame's right edge), waiting while any other Blender job runs.
set -u
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-code
K=/home/user/work/paper-pop-up-film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $K
while pgrep -f "blender-5.2.2-linux-x64/blender -b" > /dev/null; do sleep 5; done
echo "start $(date +%T)"
DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
  --python paper-film/blender/tests/break_scene.py --python paper-film/blender/shot_facts.py -- --view end \
  --check examples/notice-corner/shot-check.json --facts $V/m-pail-just-out --break "wooden-pail:0.50,0,0" > $V/m-pail-just-out.log 2>&1
echo "measured: $(grep -c 'shot_facts: done' $V/m-pail-just-out.log) $(date +%T)"
