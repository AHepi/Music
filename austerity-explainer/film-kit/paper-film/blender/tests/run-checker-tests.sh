#!/usr/bin/env bash
# What this does: tests the shot checker (log 31). It measures the notice corner as it stood before log 31's fixes
# (notice_corner_test_scene.py) and eleven copies broken on purpose, then checks each one and prints the first fix
# of every report. Each report's first fix should name the fault that was planted.
# Use (from the kit's top folder): paper-film/blender/tests/run-checker-tests.sh OUT_FOLDER
# Needs Blender (BLENDER, default the kit's usual place) and a virtual screen (DISPLAY, default :96). About 6 minutes.
set -u
out=${1:?give an output folder}; mkdir -p "$out"
here=$(cd "$(dirname "$0")" && pwd); kit=$(cd "$here/../../.." && pwd)
BLENDER=${BLENDER:-/home/user/work/blender-app/blender-5.2.2-linux-x64/blender}
check=$kit/examples/notice-corner/shot-check.json
run() {   # name, then extra options for the scene, break_scene.py and shot_facts.py
  name=$1; shift
  DISPLAY=${DISPLAY:-:96} timeout 600 "$BLENDER" -b "$kit/assets/models/pit-village/street.blend" \
    --python "$here/notice_corner_test_scene.py" --python "$here/break_scene.py" --python "$kit/paper-film/blender/shot_facts.py" -- \
    --view end --check "$check" --facts "$out/$name" "$@" > "$out/$name.log" 2>&1
  python3 "$kit/paper-film/tools/check_shot.py" --check "$check" --facts "$out/$name" --out "$out/$name-report" --title "$name" > /dev/null
  echo "$name: $(sed -n '/## Fix first/,/## Problems/p' "$out/$name-report/report.md" | sed -n 3p | cut -c1-200)"
}
run good-frame
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
