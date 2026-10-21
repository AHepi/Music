#!/bin/bash
B=/workspace/blender/blender
W=proc-work/skills_test/22b
export PYTHONDONTWRITEBYTECODE=1
for w in 60 150 300; do
  $B -b --disable-autoexec $W/street_copy/door_before.blend --python $W/34_render_with_light.py -- $w $W/out/light main today 540 960 48 tag=_w$w 2>&1 | grep -E "DRAWN|Error|Traceback"
done
