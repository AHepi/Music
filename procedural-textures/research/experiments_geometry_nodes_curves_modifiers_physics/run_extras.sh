#!/bin/bash
# What this does: re-bakes the geometry-nodes-only gravel at full size (timed), then draws the "what does this setting do" strips. Run: bash run_extras.sh
cd "$(dirname "$0")"
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
start=$(date +%s)
$B -b --disable-autoexec -t 2 --python recipe_gravel_scatter_gn.py -- out/full/gravel_gn --size 1254 --ao 0.8 > out/full/gravel_gn.log 2>&1
echo "gravel_gn took $(( $(date +%s)-start )) s wall-clock" >> out/full/timings.txt
python3 -I ../../lib/texture_compare.py gravel out/full/gravel_gn --json out/full/gravel_gn/score.json --sheet out/full/gravel_gn/sheet.png > /dev/null 2>&1
python3 -I hybrid_height_experiment.py gravel out/full/gravel_gn out/hybrid/gravel_gn > out/hybrid/gravel_gn.log 2>&1
start=$(date +%s)
$B -b --disable-autoexec -t 2 --python fig_settings_strips.py > out/strips.log 2>&1
echo "strips took $(( $(date +%s)-start )) s wall-clock" >> out/full/timings.txt
for d in out/strips/*/; do python3 -I ../../lib/make_strip.py $d out/strips/$(basename $d).png > /dev/null; done
echo EXTRAS DONE >> out/full/timings.txt
