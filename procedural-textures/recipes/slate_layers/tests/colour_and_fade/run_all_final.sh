#!/bin/bash
# What this does (plain words): runs, one after the other, every picture and test of the COLOUR AND FADE layer that needs Blender: the layer
# tests, the independence test inside the whole recipe, the overview sheets, the control sweeps, the brick reuse test, the final score of
# the colour group, and a full bake of the whole recipe at 1254 dots. Takes about an hour on a shared processor. Log: run_all_final.log
HERE="$(cd "$(dirname "$0")" && pwd)"
PROC="$HERE/../../../.."
cd "$HERE"
echo "== layer tests"; python3 -I layer_tests.py 512
echo "== full stack independence"; python3 -I full_stack_independence.py 384
echo "== sheets"; python3 -I make_sheets.py before_after variations
mkdir -p pictures; echo "== score"; ./score_colour.sh final
echo "== sweeps"; python3 -I run_sweeps.py
echo "== brick reuse"; ../blender.sh ../bake_tools.py -- reuse_brick_recipe.py reuse_brick 1254 4 '{"brick":{}}' '{}' Colour,Height 2>&1 | grep -E "Saved|Error|Trace"
echo "== full recipe, harness, 1254"; mkdir -p full_stack_1254
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python "$PROC/lib/bake_harness.py" -- "$HERE/../../recipe/slate_recipe.py" "$HERE/full_stack_1254" --size 1254 --normal-reference slate 2>&1 | grep -E "Saved|Error|Trace|seconds"
python3 -I "$PROC/lib/texture_compare.py" slate "$HERE/full_stack_1254" --json "$HERE/full_stack_1254/score.json" --sheet "$HERE/full_stack_1254/sheet.png" > /dev/null
echo "== debug views and comparison"; cp dev/final/colour.png pictures/layer_only_colour_1254.png; python3 -I make_debug_and_compare_sheets.py
echo "== resolution crops"; python3 -I make_sheets.py resolution rebake
echo "== timing (user seconds of CPU, 1254 dots, colour only): layout alone, then layout + this layer"
( time ../blender.sh ../bake_tools.py -- ../layout_only_recipe.py dev/time_layout 1254 4 '{"j":{"view":"joints"}}' '{}' Colour >/dev/null 2>&1 ) 2>&1 | grep -E "real|user" | tr '\n' ' '; echo
( time ../blender.sh ../bake_tools.py -- layer_only_recipe.py dev/time_layer 1254 4 '{"j":{}}' '{}' Colour >/dev/null 2>&1 ) 2>&1 | grep -E "real|user" | tr '\n' ' '; echo
../blender.sh count_nodes.py 2>&1 | grep NODES
echo "== controls table and settings"; ../blender.sh make_my_controls_table.py 2>&1 | grep wrote; ../blender.sh write_my_settings.py 2>&1 | grep wrote
python3 -I "$PROC/lib/description_audit.py" settings_colour_and_fade.json --limit-kilobytes 8 | grep -E "bytes|numbers|problems"
echo ALL DONE
