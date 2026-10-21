#!/bin/bash
# Trial 22b round 1 (runs on the rented machine): the door BEFORE and AFTER add_wear, EEVEE (the film's plate renderer, via the street's own tool) and Cycles.
B=/workspace/blender/blender
W=proc-work/skills_test/22b
T=proc-work/street_wet/tools
export PYTHONDONTWRITEBYTECODE=1
cd $W
for v in before addwear; do
  $B -b --disable-autoexec $W/street_copy/door_$v.blend --python $T/22_render_eevee.py -- $W/out/r1 main today 540 960 64 tag=_${v}_eevee 2>&1 | grep -E "DRAWN|Error|Traceback|GPU BACKEND" 
  $B -b --disable-autoexec $W/street_copy/door_$v.blend --python $W/21_render_cycles.py -- $W/out/r1/main_${v}_cycles.png 540 960 128 2>&1 | grep -E "DRAWN|Error|Traceback|CYCLES DEVICE|device"
done
ls -la $W/out/r1
