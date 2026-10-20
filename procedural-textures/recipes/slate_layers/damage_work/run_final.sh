#!/bin/bash
# What this does (plain words): the FINAL runs, one after the other, with the finished DAMAGE layer: the four sweep strips, the half-tile test,
# the independence test, the before/after pictures, the timing, the debug views of the layer alone and one full harness bake of the whole stack
# with DAMAGE plugged in. Each step writes its own log in logs/ and a line in logs/chain_final.txt.
cd "$(dirname "$0")"
mkdir -p logs ../debug_views/damage ../tests/damage_timing
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
: > logs/chain_final.txt
python3 -I make_sweeps.py 400 > logs/sweeps_final.txt 2>&1;                       echo "sweeps done $(date +%T)" >> logs/chain_final.txt
python3 -I half_tile_damage.py 512 > logs/half_tile_final.txt 2>&1;               echo "half tile done $(date +%T)" >> logs/chain_final.txt
python3 -I before_after.py 1254 > logs/before_after_final.txt 2>&1;               echo "before/after done $(date +%T)" >> logs/chain_final.txt
$B -b --disable-autoexec -t 2 --python ../tests/bake_tools.py -- ../recipe/slate_recipe.py ../debug_views/damage 1254 4 '{"damage_mask": {"debug_view": "damage.mask"}, "damage_colour": {"debug_view": "damage.colour"}, "damage_height": {"debug_view": "damage.height"}, "damage_roughness": {"debug_view": "damage.roughness"}}' '{}' 'Colour' > logs/debug_views_final.txt 2>&1; echo "debug views done $(date +%T)" >> logs/chain_final.txt
$B -b --disable-autoexec -t 2 --python ../../../lib/bake_harness.py -- ../recipe/slate_recipe.py stack_bake_1254 --size 1254 --normal-reference slate > logs/stack_bake_final.txt 2>&1; echo "stack bake done $(date +%T)" >> logs/chain_final.txt
python3 -I independence_damage.py 384 > logs/independence_final.txt 2>&1;         echo "independence done $(date +%T)" >> logs/chain_final.txt

./run_extra.sh
echo "ALL DONE $(date +%T)" >> logs/chain_final.txt
