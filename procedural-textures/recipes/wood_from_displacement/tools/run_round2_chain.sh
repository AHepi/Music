#!/bin/bash
# What this does (plain words): runs the final bakes of round 2 of the wood-from-maps recipe one after the other (only ONE Blender at a time, 2 threads):
#   1. seed 1 of the default tile with the plain harness command line (proof that the standard command works),
#   2. seeds 2 and 3 (all maps) and the COMPARISON colours for the three seeds        (tests/jobs_r2_tiles.json),
#   3. the area bakes: 2 x 2, 4 x 4, the tile repeated, the exact debug pictures        (tests/jobs_r2_areas.json),
#   4. full-size crops of the 4 x 4 area, the half-tile slide test, the source-unchanged check   (tests/jobs_r2_extras.json),
#   5. the exact board numbers of the three default tiles (for the joint sheets)       (tests/jobs_r2_joints.json),
#   6. the "what does each part buy" areas   (tests/jobs_r2_switch.json),
#   7. the sweep pictures for the guide      (tests/jobs_r2_sweeps.json),
#   8. the lit pictures                      (tests/jobs_r2_lit.json).
# (A first run of this chain was stopped after step 2 and thrown away: it had a thin wrong strip at the bottom edge of the default tile, see the guide, section 11.)
# Use: bash tools/run_round2_chain.sh      (from anywhere; it changes into the proc-work folder itself). Log: tests/r2/chain.log (one line per finished step)
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd proc-work || exit 1
W=recipes/wood_from_displacement
mkdir -p $W/tests/r2
echo "start of the final chain $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $W/recipe/wood_from_maps_recipe.py $W/outputs/main_seed1 --size 1254 --params '{"recipe.seed": 1}' > $W/tests/r2/chain_cli_seed1.log 2>&1
rm -f $W/outputs/main_seed1/normal_bumpnode.png
echo "step 1 (standard command, seed 1) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_r2_tiles.json > $W/tests/r2/chain_tiles.log 2>&1
echo "step 2 (tiles) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_r2_areas.json > $W/tests/r2/chain_areas.log 2>&1
echo "step 3 (areas) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_r2_extras.json > $W/tests/r2/chain_extras.log 2>&1
echo "step 4 (crops, slide test, source unchanged) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_r2_joints.json > $W/tests/r2/chain_joints.log 2>&1
echo "step 5 (board numbers of the tiles) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_r2_switch.json > $W/tests/r2/chain_switch.log 2>&1
echo "step 6 (switch-off areas) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_r2_sweeps.json > $W/tests/r2/chain_sweeps.log 2>&1
echo "step 7 (sweeps) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/lit_preview_multi.py -- $W/tests/jobs_r2_lit.json > $W/tests/r2/chain_lit.log 2>&1
echo "step 8 (lit pictures) done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
echo "all done $(date +%H:%M:%S)" >> $W/tests/r2/chain.log
touch $W/tests/r2/chain.done
