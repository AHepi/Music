#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
M=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/metal
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
for n in S0 L M S; do
  start=$(date +%s)
  $B -b --disable-autoexec -t 2 --python $M/generator/metal_generator.py -- $M/description/$n.json $M/verify/$n --samples 8 --channels colour > $M/verify/log_$n.txt 2>&1
  echo "$n done in $(( $(date +%s) - start )) s" >> $M/verify/times.txt
done
