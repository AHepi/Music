#!/bin/bash
# What this does (plain words): the "what does each layer buy" ladder at 1254 dots (colour and height), the link and stack-order pictures at 768, and the tone-blend height pictures at 640.
SL=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate_layers
B="/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py --"
cd $SL
$B $SL/recipe/slate_recipe.py $SL/ladder 1254 4 "$(cat ladder/ladder_views.json)" '{}' Colour,Height > ladder/bake.log 2>&1
$B $SL/recipe/slate_recipe.py $SL/links_and_order 768 4 "$(cat links_and_order/links_views.json)" '{}' Colour > links_and_order/bake_links.log 2>&1
$B $SL/recipe/slate_recipe.py $SL/links_and_order 640 4 "$(cat links_and_order/tone_blend_views.json)" '{}' Height > links_and_order/bake_tb.log 2>&1
echo done > integration/chain_c.done
