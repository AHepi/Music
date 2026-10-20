#!/bin/bash
# What this does (plain words): runs the long chain of gravel bakes and scores one after the other (S_v4 at 1254, the half-tile seamless test, 8 variations,
# the 2 x 2 area picture, the three resolutions, the real-geometry route, the pebbles transfer, the stone-only trace hybrid, the sweep strips for the guide).
# A step whose flag file scores/flags/NAME.done exists is skipped, so the chain can be started again after a stop. Run it in the background.
cd "$(dirname "$0")"
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p scores/flags variations/out area/out resolution/out transfer/out guide_pictures/sweeps
step() { NAME=$1; shift; if [ ! -f scores/flags/$NAME.done ]; then "$@" > scores/flags/$NAME.txt 2>&1; touch scores/flags/$NAME.done; fi; }
step S_v4 ./run_bake_and_score.sh S_v4
step half_tile python3 -I analysis/half_tile_test.py description/S_v4.json
step variations_bake $BL -b --disable-autoexec -t 2 --python generator/gravel_generator.py -- --batch variations/jobs.json
step variations_score bash -c 'for k in 01 02 03 04 05 06 07 08; do python3 -I analysis/score_folder.py variations/out/sample_$k var_sample_$k; done'
step area_bake $BL -b --disable-autoexec -t 2 --python generator/gravel_generator.py -- --batch area/jobs.json
step resolution_bake $BL -b --disable-autoexec -t 2 --python generator/gravel_generator.py -- --batch resolution/jobs.json
step geometry_route $BL -b --disable-autoexec -t 2 --python generator/geometry_route.py -- description/S_v4.json outputs/S_v4 outputs/S_v4_geometry --size 1254
step transfer_bake $BL -b --disable-autoexec -t 2 --python generator/gravel_generator.py -- --batch transfer/jobs.json
step TS_a300 ./run_bake_and_score.sh TS_k24_a300
step sweeps $BL -b --disable-autoexec -t 2 --python generator/sweeps_for_guide.py -- guide_pictures/sweeps
touch scores/flags/all.done
