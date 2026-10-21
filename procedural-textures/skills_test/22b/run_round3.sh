#!/bin/bash
# Trial 22b round 3 (rented machine): 100 W lookdev light; the pictures again; the curvature route; the bake with fewer seams (60 degrees, no sharp-edge flags) at 512 and 1024.
B=/workspace/blender/blender
W=proc-work/skills_test/22b
T=proc-work/street_wet/tools
export PYTHONDONTWRITEBYTECODE=1
cd $W
mkdir -p out/r3
{
echo "== pictures"
for v in before addwear curv; do
  $B -b --disable-autoexec $W/street_copy/door_$v.blend --python $T/22_render_eevee.py -- $W/out/r3 main today 540 960 64 tag=_${v}_eevee 2>&1 | grep -E "DRAWN|Error|Traceback"
  $B -b --disable-autoexec $W/street_copy/door_$v.blend --python $W/21_render_cycles.py -- $W/out/r3/main_${v}_cycles.png 540 960 96 2>&1 | grep -E "DRAWN|Error|Traceback"
done
for r in 512 1024; do
  echo "== bake $r (seams 60 deg, no sharp flags)"
  BAKE_TAG=_a60 $B -b --disable-autoexec $W/street_copy/door_addwear.blend --python $W/30_bake_door.py -- $r $W/out/bake${r}_a60 60 0 2>&1 | grep -E "LAP|UNWRAP|UV_QA|UV_VERDICT|BAKE|SANITY|DONE|Error|Traceback|rror|File \"" | cut -c1-1800
  $B -b --disable-autoexec $W/street_copy/door_baked_${r}_a60.blend --python $T/22_render_eevee.py -- $W/out/r3 main today 540 960 64 tag=_baked${r}_eevee 2>&1 | grep -E "DRAWN|Error|Traceback"
done
echo "== bake 512 with the skill's own first choice again (30 deg + sharp flags), for the record: already in out/bake512"
} > $W/out/r3/log.txt 2>&1
cat $W/out/r3/log.txt | tail -5
