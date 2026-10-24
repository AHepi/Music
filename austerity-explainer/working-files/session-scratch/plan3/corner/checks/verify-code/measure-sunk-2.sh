#!/usr/bin/env bash
# Measures the pail sunk 0.10 m and the drum sunk 0.30 m with the current shot_facts.py, waiting while any other Blender job runs.
set -u
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-code
K=/home/user/work/paper-pop-up-film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $K
while pgrep -f "blender-5.2.2-linux-x64/blender -b" > /dev/null; do sleep 5; done
echo "start $(date +%T)"
DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
  --python paper-film/blender/tests/break_scene.py --python paper-film/blender/shot_facts.py -- --view end \
  --check examples/notice-corner/shot-check.json --facts $V/m-sunk-2 --break "wooden-pail:0,0,-0.10;brazier:0,0,-0.30" > $V/m-sunk-2.log 2>&1
echo "measured: $(grep -c 'shot_facts: done' $V/m-sunk-2.log) $(date +%T)"
