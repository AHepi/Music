#!/bin/bash
# What this does (plain words): replaces the last two steps of run_chain_f.sh so they run beside the strips instead of after them
# (chain F's shell was stopped after it had started the strip bake; the strip bake itself kept running):
#  1. the 4 x 4 area (recipe.tiles_across 4 = 5016 dots, colour only) and its seam and repeat measures, started at once;
#  2. three more sets of seeds of the default settings at 1254 dots (colour), started when the strip bake has finished.
SL=proc-work/recipes/slate_layers
# NOTE (added later): this chain was stopped before either step finished, to free the machine for tuning round 14; both steps were then run by run_chain_h.sh.
B="/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py --"
cd $SL
(python3 -I area/make_area.py all 4 > area/run4.log 2>&1; echo done > integration/takeover/area4.done) &
while pgrep -f "controls_sweeps/whole_recipe/tiles" > /dev/null; do sleep 10; done
$B $SL/recipe/slate_recipe.py $SL/variations/seed_spread 1254 4 "$(cat variations/seed_spread/views.json)" '{}' Colour > variations/seed_spread/bake.log 2>&1
echo done > integration/takeover/seeds.done
wait
echo done > integration/takeover/chain_g.done
