#!/bin/bash
# What this does (plain words): the bakes added after the restart, one Blender at a time (2 threads):
#  1. "what does this control do" strips of the WHOLE recipe at the final tuned settings (768 dots, colour), five controls x four values;
#  2. three more sets of seeds of the default settings at 1254 dots (colour), to measure how much the "same kind" colour score moves with the seed alone;
#  3. the 4 x 4 area (recipe.tiles_across 4 = 5016 dots, colour only) and its seam and repeat measures.
# NOTE (added later): only step 1 ran from this script; its shell was stopped while the strip bake ran, and steps 2 and 3 were run by run_chain_g.sh instead (beside the strips, to save time).
SL=proc-work/recipes/slate_layers
B="/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py --"
cd $SL
while [ ! -f integration/takeover/chain_d.done ]; do sleep 20; done
$B $SL/recipe/slate_recipe.py $SL/controls_sweeps/whole_recipe/tiles 768 4 "$(cat controls_sweeps/whole_recipe/views.json)" '{}' Colour > controls_sweeps/whole_recipe/bake.log 2>&1
$B $SL/recipe/slate_recipe.py $SL/variations/seed_spread 1254 4 "$(cat variations/seed_spread/views.json)" '{}' Colour > variations/seed_spread/bake.log 2>&1
python3 -I area/make_area.py all 4 > area/run4.log 2>&1
echo done > integration/takeover/chain_f.done
