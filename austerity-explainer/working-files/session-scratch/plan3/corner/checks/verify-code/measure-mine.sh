#!/usr/bin/env bash
# Measures four test scenes for the code check, one Blender job at a time, waiting while any other Blender job runs.
set -u
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-code
K=/home/user/work/paper-pop-up-film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $K
wait_free() { while pgrep -f "blender-5.2.2-linux-x64/blender -b" > /dev/null; do sleep 5; done; }
run() {   # name, check file, extra script (or none), then extra options
  name=$1; check=$2; extra=$3; shift 3
  wait_free
  echo "start $name $(date +%T)"
  if [ "$extra" = none ]; then more=(); else more=(--python "$extra"); fi
  DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
    --python paper-film/blender/tests/break_scene.py "${more[@]}" --python paper-film/blender/shot_facts.py -- --view end \
    --check $check --facts $V/$name "$@" > $V/$name.log 2>&1
  echo "measured $name: $(grep -c 'shot_facts: done' $V/$name.log) $(date +%T)"
}
run m-sunk examples/notice-corner/shot-check.json none --break "wooden-pail:0,0,-0.10;brazier:0,0,-0.30"
run m-pail-cut-bottom examples/notice-corner/shot-check.json none --break "wooden-pail:-0.3,-0.6,-0.042"
run m-rolled examples/notice-corner/shot-check.json $V/roll_camera.py
run m-landscape $V/chk-landscape.json none
echo ALL DONE
