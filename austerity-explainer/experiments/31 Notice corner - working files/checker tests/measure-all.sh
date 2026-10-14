#!/usr/bin/env bash
# What this does: measures the composed notice corner and eleven broken copies of it, for testing the shot checker.
set -u
C=<working folder>/checks
K=/home/user/work/paper-pop-up-film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $K
run() {   # name, then extra options
  name=$1; shift
  DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
    --python paper-film/blender/tests/break_scene.py --python paper-film/blender/shot_facts.py -- --view end \
    --check examples/notice-corner/shot-check.json --facts $C/$name "$@" > $C/$name.log 2>&1
  echo "measured $name: $(grep -c 'shot_facts: done' $C/$name.log)"
}
run composed-end
run a-camera-too-high --camera-at 3.25,16.6,3.52 --yaw 5.9 --fov 60
run b-pail-in-the-air --break "wooden-pail:0.55,0,5.0"
run c-chair-pushed-back --break "kitchen-chair:0,0.45,0"
run d-pail-out-of-frame --break "wooden-pail:0.25,0,0"
run e-camera-tilted --camera-at 2.96,17.85,3.1882 --yaw 6.87 --pitch 3 --fov 60.4
run f-drum-edge-touches-chair --break "brazier:-0.15,0,0"
run g-lantern-on-the-pavement --break "hurricane-lantern:-0.45,-0.7,-0.53;lantern_flame:-0.45,-0.7,-0.53;lantern_light:-0.45,-0.7,-0.53"
run h-props-sunk --break "wooden-pail:0,0,-0.10;brazier:0,0,-0.30"
run i-lamp-post-along-board --break "gas-lamp-post:-0.53,0,0"
run j-drum-behind-board --break "brazier:0,1.5,0.1048"
run k-lamp-post-across-notice --break "gas-lamp-post:0,-0.95,-0.0664"
echo ALL MEASURED
