#!/bin/bash
# verifier: fresh Blender process per description, outputs into verify/out/NAME
export PYTHONDONTWRITEBYTECODE=1
S=proc-work/recipes/slate
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S/verify
for n in S0_layout_only S1_layout_stamps S2_stamps_grain M_trace_tiny M_trace_small M_trace_coarse L_trace_small L_trace_medium L_trace_fine; do
  $B -b --disable-autoexec -t 2 --python $S/generator/slate_generator.py -- $S/description/$n.json $S/verify/out/$n --size 1254 2>&1 | grep -E "bake\]|Error|error|Traceback" | cut -c1-400
  touch $S/verify/flag_$n
done
echo done > $S/verify/flag_all
