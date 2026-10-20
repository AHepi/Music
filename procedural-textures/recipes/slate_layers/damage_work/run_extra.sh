#!/bin/bash
# What this does (plain words): two extra runs. (1) The whole stack baked with the harness with DAMAGE switched off (Amount 0), so the
# "same kind as the reference" score can be compared with and without damage. (2) Four zoomed windows with different DAMAGE settings
# ("fresh slate", "heavily damaged", "bleached", "cracked but clean edges") to see that the controls give useful, different looks.
cd "$(dirname "$0")"
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p ../tests/damage_looks
$B -b --disable-autoexec -t 2 --python window_render.py -- ../recipe/slate_recipe.py ../tests/damage_looks 500 0.2,0.354,0.4 '{"fresh_slate": {"params": {"damage.amount": 0.15}}, "heavily_damaged": {"params": {"damage.chip_amount": 0.9, "damage.chip_depth": 0.045, "damage.slate_variation": 0.4, "damage.crack_amount": 0.8, "damage.scratch_amount": 0.5, "damage.corner_break_amount": 0.35, "damage.notch_amount": 0.7, "damage.pit_amount": 0.2}}, "bleached_and_scratched": {"params": {"damage.break_colour": "#9a9588", "damage.break_colour_light": "#b4b2ab", "damage.break_colour_dark": "#6f6b62", "damage.scratch_amount": 0.9, "damage.chip_amount": 0.4}}, "cracked_clean_edges": {"params": {"damage.chip_amount": 0.05, "damage.crack_amount": 1.0, "damage.crack_across_share": 0.4, "damage.crack_length": 0.09}}, "defaults": {}}' > logs/looks.txt 2>&1
echo "looks done $(date +%T)" > logs/extra.txt
$B -b --disable-autoexec -t 2 --python ../../../lib/bake_harness.py -- ../recipe/slate_recipe.py stack_bake_1254_damage_off --size 1254 --normal-reference slate --params '{"damage.amount": 0}' > logs/stack_bake_off.txt 2>&1
echo "bake off done $(date +%T)" >> logs/extra.txt
python3 -I ../../../lib/texture_compare.py slate stack_bake_1254_damage_off --json stack_bake_1254_damage_off/score.json --sheet stack_bake_1254_damage_off/sheet.png > logs/score_off.txt 2>&1
echo "ALL DONE $(date +%T)" >> logs/extra.txt
