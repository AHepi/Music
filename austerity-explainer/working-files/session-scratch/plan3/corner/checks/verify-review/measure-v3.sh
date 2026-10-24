#!/usr/bin/env bash
# measures three scenes, one Blender job at a time, with my snapshot of the newest shot_facts.py (eaf9f26f)
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-review
K=/home/user/work/paper-pop-up-film-kit; B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $K
run() { name=$1; shift
  while pgrep -f "blender-5.2.2-linux-x64/blender -b" > /dev/null; do sleep 5; done   # wait for any other Blender job
  DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
    --python paper-film/blender/tests/break_scene.py --python $V/shot_facts.v3.py -- --view end \
    --check examples/notice-corner/shot-check.json --facts $V/m3-$name "$@" > $V/m3-$name.log 2>&1
  echo "measured $name: $(grep -c 'shot_facts: done' $V/m3-$name.log) $(date +%T)"
}
run composed-end
run sunk --break "wooden-pail:0,0,-0.10;brazier:0,0,-0.30"
run c-chair-pushed-back --break "kitchen-chair:0,0.45,0"
echo MEASURED ALL
