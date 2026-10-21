#!/bin/bash
# What this does: on the rented machine, runs the five review jobs of review_run.py and then the street's own EEVEE tool for two cameras. Writes into proc-work/skills_test/22a/out_machine. Changes nothing else.
B=/workspace/blender/blender
W=proc-work/skills_test/22a
T=proc-work/street_wet/tools
mkdir -p $W/out_machine
cd $W
$B --version | head -1
for j in stock focus camera cull_off cull_on; do
  $B -b --disable-autoexec --factory-startup --python-exit-code 1 $W/set_copy/street.blend -P $W/scripts/review_run.py -- $j $W/out_machine/$j > $W/out_machine/$j.log 2>&1
  echo "review job $j exit code $?"
  grep -E "REVIEW_DONE|Error|Traceback|rror:" $W/out_machine/$j.log | head -5
done
for cam in main wall_lamp; do
  $B -b --disable-autoexec --python-exit-code 1 $W/set_copy/street.blend --python $T/22_render_eevee.py -- $W/out_machine/eevee $cam today 540 960 32 > $W/out_machine/eevee_$cam.log 2>&1
  echo "eevee $cam exit code $?"
  grep -E "DRAWN|Error|Traceback|rror:" $W/out_machine/eevee_$cam.log | head -5
done
ls -la $W/out_machine $W/out_machine/eevee
