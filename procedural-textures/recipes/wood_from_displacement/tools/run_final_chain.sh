#!/bin/bash
# What this does (plain words): runs the final bakes of the wood-from-maps recipe one after the other (only ONE Blender at a time, 2 threads):
#   1. seed 1 with the plain harness command line (proof that the standard command works),
#   2. seeds 2 and 3 (all maps) and the COMPARISON colours for the three seeds,
#   3. the area bakes (2 x 2, 4 x 4, repeated tile, exact debug pictures),
#   4. full-size crops of the 4 x 4 area, the half-tile shift test and the source-unchanged check.
# Use: bash tools/run_final_chain.sh [from3]   (from3 = skip steps 1 and 2, which are already done)   (from anywhere; it changes into the proc-work folder itself). Log: tests/final_chain.log
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd proc-work || exit 1
W=recipes/wood_from_displacement
[ "$1" = "from3" ] || $BL -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $W/recipe/wood_from_maps_recipe.py $W/outputs/main_seed1 --size 1254 --params '{"recipe.seed": 1}' > $W/tests/final_cli_seed1.log 2>&1
echo "step 1 done $(date +%H:%M:%S)" >> $W/tests/final_chain.log
[ "$1" = "from3" ] || $BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_final_a.json > $W/tests/final_a.log 2>&1
echo "step 2 done $(date +%H:%M:%S)" >> $W/tests/final_chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_final_b.json > $W/tests/final_b.log 2>&1
echo "step 3 done $(date +%H:%M:%S)" >> $W/tests/final_chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_final_c.json > $W/tests/final_c.log 2>&1
echo "step 4 done $(date +%H:%M:%S)" >> $W/tests/final_chain.log
