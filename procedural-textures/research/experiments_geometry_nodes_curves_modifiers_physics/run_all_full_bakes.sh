#!/bin/bash
# What this does: runs the six geometry recipes at full size (1254 x 1254) one after the other, with timing, then scores each against its reference.
# Run: bash run_all_full_bakes.sh        (takes about 15-20 minutes on 2 CPU threads)
cd "$(dirname "$0")"
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
LIB=../../lib
mkdir -p out/full
for spec in "brick:recipe_brick_layout.py:brick" "slate:recipe_slate_layout.py:slate" "gravel:recipe_gravel_rigidbody.py:gravel" "mud:recipe_curve_ruts.py:mud" "metal:recipe_riveted_metal.py:metal" "wood:recipe_wood_planks.py:wood"; do
  IFS=: read name script ref <<< "$spec"
  start=$(date +%s)
  $B -b --disable-autoexec -t 2 --python $script -- out/full/$name --size 1254 --ao 0.8 > out/full/$name.log 2>&1
  end=$(date +%s)
  echo "$name took $((end-start)) s wall-clock" | tee -a out/full/timings.txt
  python3 -I $LIB/texture_compare.py $ref out/full/$name --json out/full/$name/score.json --sheet out/full/$name/sheet.png > /dev/null 2>&1
done
echo ALL DONE >> out/full/timings.txt
