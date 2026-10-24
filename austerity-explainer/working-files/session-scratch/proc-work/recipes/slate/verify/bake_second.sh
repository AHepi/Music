#!/bin/bash
# verifier: second batch (after the first finished): re-bake two variations at 1254 (determinism), half-tile shift test at 512 for var_103 and cedar, area description at 2508 is separate
export PYTHONDONTWRITEBYTECODE=1
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S/verify
while [ ! -f flag_all ]; do sleep 5; done
for n in var_101 var_105; do
  $B -b --disable-autoexec -t 2 --python $S/generator/slate_generator.py -- $S/variations/$n.json $S/verify/out/$n --size 1254 2>&1 | grep -E "bake\]|Error|error|Traceback" | cut -c1-300
done
for n in variations/var_103 transfer/cedar_shingles_1 transfer/fish_scale_clay_1; do
  b=$(basename $n)
  $B -b --disable-autoexec -t 2 --python $S/generator/slate_generator.py -- $S/$n.json $S/verify/half/${b}_a --size 512 2>&1 | grep -E "Error|error|Traceback" | cut -c1-300
  $B -b --disable-autoexec -t 2 --python $S/generator/slate_generator.py -- $S/$n.json $S/verify/half/${b}_b --size 512 --shift 0.5 0.5 2>&1 | grep -E "Error|error|Traceback" | cut -c1-300
done
echo done > flag_second
