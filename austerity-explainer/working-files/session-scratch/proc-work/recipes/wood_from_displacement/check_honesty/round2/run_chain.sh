#!/bin/sh
# What this does (plain words): the honesty checker's own chain of Blender runs for round 2, one after the other (never two at once).
# 1. the standard harness bake of the default tile (seed 1, 1254 dots) into check_honesty/round2/rebake_default_1254
# 2. the half-tile slide test and one full-size piece of the 4 x 4 area, with the builder's own job driver (not edited)
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work || exit 1
export PYTHONDONTWRITEBYTECODE=1
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
C=recipes/wood_from_displacement/check_honesty/round2
df -h / | tail -1
date +%s > $C/chain_start.time
$B -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/wood_from_displacement/recipe/wood_from_maps_recipe.py $C/rebake_default_1254 --size 1254 --params '{"recipe.seed": 1}' > $C/rebake_default_1254.log 2>&1
date +%s > $C/rebake_done.time
df -h / | tail -1
$B -b --disable-autoexec -t 2 --python recipes/wood_from_displacement/tools/run_jobs.py -- $C/jobs_round2_check.json > $C/jobs_round2_check.log 2>&1
date +%s > $C/chain_end.time
echo done > $C/chain.done
