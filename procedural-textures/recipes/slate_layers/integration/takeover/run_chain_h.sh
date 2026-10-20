#!/bin/bash
# What this does (plain words): the last bakes, started after tuning round 14 was judged (its result: keep the first integrator's settings):
#  1. the 4 x 4 area (recipe.tiles_across 4 = 5016 dots, colour only) and its measures;
#  2. beside it, the third extra seed set of the default settings (seeds_d) at 1254 dots (seeds_b and seeds_c were baked in round 14).
SL=proc-work/recipes/slate_layers
B="/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py --"
cd $SL
(python3 -I area/make_area.py all 4 > area/run4.log 2>&1; echo done > integration/takeover/area4.done) &
$B $SL/recipe/slate_recipe.py $SL/variations/seed_spread 1254 4 '{"seeds_d": {"layout.seed": 303, "colour_and_fade.seed": 313, "damage.seed": 323, "moss.seed": 333, "outline_and_shadow.seed": 343}}' '{}' Colour > variations/seed_spread/bake.log 2>&1
echo done > integration/takeover/seeds.done
wait
echo done > integration/takeover/chain_h.done
