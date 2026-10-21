#!/bin/bash
# Trial 22b round 2 (rented machine): lit door pictures, the skill's checks, the masks, and the 512 test bake with a rebuilt-from-maps picture.
B=/workspace/blender/blender
W=proc-work/skills_test/22b
T=proc-work/street_wet/tools
export PYTHONDONTWRITEBYTECODE=1
cd $W
echo "== pictures (before, addwear) EEVEE + Cycles"
for v in before addwear; do
  $B -b --disable-autoexec $W/street_copy/door_$v.blend --python $T/22_render_eevee.py -- $W/out/r2 main today 540 960 64 tag=_${v}_eevee 2>&1 | grep -E "DRAWN|Error|Traceback"
  $B -b --disable-autoexec $W/street_copy/door_$v.blend --python $W/21_render_cycles.py -- $W/out/r2/main_${v}_cycles.png 540 960 96 2>&1 | grep -E "DRAWN|Error|Traceback"
done
echo "== skill checks and masks"
$B -b --disable-autoexec $W/street_copy/door_addwear.blend --python $W/31_checks.py -- $W/out/checks 2>&1 | grep -E "VALUE_REPORT|PREVIEW|MASKS|DONE|Error|Traceback|rror" | cut -c1-1500
echo "== bake 512"
$B -b --disable-autoexec $W/street_copy/door_addwear.blend --python $W/30_bake_door.py -- 512 $W/out/bake512 2>&1 | grep -E "LAP|UNWRAP|UV_QA|UV_VERDICT|BAKE|SANITY|DONE|Error|Traceback|rror|File \"" | cut -c1-1800
echo "== baked picture"
$B -b --disable-autoexec $W/street_copy/door_baked_512.blend --python $T/22_render_eevee.py -- $W/out/r2 main today 540 960 64 tag=_baked512_eevee 2>&1 | grep -E "DRAWN|Error|Traceback"
ls -la $W/out/r2 $W/out/bake512 $W/out/checks
