#!/bin/bash
# What this does (plain words): after the machine restart, finishes the bakes that were cut off: the rest of the BRICK reuse test (one layer's colour
# and each layer's mask on bricks), the last two rungs of the "what does each layer buy" ladder, the declared-link and stack-order pictures, and the
# tone-blend height pictures. One Blender at a time, 2 threads.
SL=proc-work/recipes/slate_layers
B="/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py --"
cd $SL
VIEWS='{"brick_colour_and_fade_only": {"only": "colour_and_fade"}, "mask_damage": {"mask_of": "damage"}, "mask_moss": {"mask_of": "moss"}, "mask_outline": {"mask_of": "outline_and_shadow"}}'
$B $SL/reuse/brick_layers_recipe.py $SL/reuse/baked 1254 4 "$VIEWS" '{}' Colour > reuse/bake_rest.log 2>&1
python3 -I integration/make_normal.py reuse/baked/brick_all_height.png reuse/baked/brick_all_normal.png 7 >> reuse/bake_rest.log 2>&1
$B $SL/recipe/slate_recipe.py $SL/ladder 1254 4 "$(cat ladder/ladder_views_rest.json)" '{}' Colour,Height > ladder/bake_rest.log 2>&1
$B $SL/recipe/slate_recipe.py $SL/links_and_order 768 4 "$(cat links_and_order/links_views.json)" '{}' Colour > links_and_order/bake_links.log 2>&1
$B $SL/recipe/slate_recipe.py $SL/links_and_order 640 4 "$(cat links_and_order/tone_blend_views.json)" '{}' Height > links_and_order/bake_tb.log 2>&1
echo done > integration/takeover/chain_e.done
