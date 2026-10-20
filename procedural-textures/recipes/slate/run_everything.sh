#!/bin/bash
# What this does (plain words): runs the long Blender jobs one after another (so they do not fight for the processor) and drops a flag file after each.
HERE="$(cd "$(dirname "$0")" && pwd)"
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd "$HERE"
mkdir -p scores/flags
./run_bake_and_score.sh S1_layout_stamps > scores/run_S1_layout_stamps.log 2>&1; touch scores/flags/s1
python3 -I analysis/half_tile_test.py description/S1_layout_stamps.json description/sample_1.json description/L_trace_medium.json > scores/half_tile.log 2>&1; touch scores/flags/half
python3 -I analysis/run_area_resolution.py > scores/area_resolution.log 2>&1; touch scores/flags/area
python3 -I analysis/run_variations.py > scores/variations.log 2>&1; touch scores/flags/variations
$B -b --disable-autoexec -t 2 --python generator/slate_generator.py -- --batch transfer/jobs.json > scores/transfer_bake.log 2>&1; touch scores/flags/transfer
$B -b --disable-autoexec -t 2 --python generator/sweeps_for_guide.py -- guide_pictures/sweeps > scores/sweeps.log 2>&1; touch scores/flags/sweeps
$B -b --disable-autoexec -t 2 --python generator/geometry_route_slabs.py -- description/S1_layout_stamps.json outputs/geometry_route --size 1254 --ao 0.8 > scores/geometry_route.log 2>&1; touch scores/flags/geometry
echo all done > scores/flags/all
