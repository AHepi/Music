#!/bin/bash
# What this does (plain words): bakes the BRICK reuse test: the finished brick wall (colour and height at 1254 dots), each layer's mask on the brick layout, and the slate default
# next to it for the sheet. Use: reuse/run_reuse.sh
SL=proc-work/recipes/slate_layers
cd $SL
VIEWS='{"brick_all": {}, "brick_colour_and_fade_only": {"only": "colour_and_fade"}, "mask_damage": {"mask_of": "damage"}, "mask_moss": {"mask_of": "moss"}, "mask_outline": {"mask_of": "outline_and_shadow"}}'
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py -- $SL/reuse/brick_layers_recipe.py $SL/reuse/baked 1254 4 "$VIEWS" '{}' Colour,Height > reuse/bake.log 2>&1
python3 -I integration/make_normal.py reuse/baked/brick_all_height.png reuse/baked/brick_all_normal.png 7
echo done > reuse/done
