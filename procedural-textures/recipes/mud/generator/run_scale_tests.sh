#!/bin/bash
# What this does (plain words): the SCALE tests that need Blender: (1) AREA: one description made for a 2508 x 2508 dot picture (four tiles' worth of NEW unique mud, wrapped at 2508),
# baked at 2508; (2) RESOLUTION: one tile description (seed 101) baked at 512, 1254 (already done by the variation run) and 2508 dots, with timings; (3) the half-tile SEAM test: the same
# description baked slid by half a tile in both directions, to be compared with the first bake rolled by half a tile.
# Use: generator/run_scale_tests.sh (about 10 minutes). Results: area/, resolution/ and the numbers in scores/scale_tests.json (made by analysis/scale_report.py).
cd "$(dirname "$0")/.."
while [ ! -f variations/variation_scores.json ]; do sleep 15; done
python3 -I - <<'PY'
import sys, json
sys.path.insert(0, 'generator')
import sampler
json.dump(sampler.sample_description(201, tile=2508), open('area/description_area_2508.json', 'w'), separators=(',', ':'))
PY
generator/bake_one.sh area/description_area_2508.json area/area_2508 2508 8 > area/bake.log 2>&1
generator/bake_one.sh variations/description_101.json resolution/size_512 512 8 > resolution/bake_512.log 2>&1
generator/bake_one.sh variations/description_101.json resolution/size_2508 2508 8 > resolution/bake_2508.log 2>&1
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python generator/mud_generator.py -- variations/description_101.json resolution/shifted_half --size 1254 --samples 8 --shift 0.5 0.5 > resolution/bake_shift.log 2>&1
echo SCALE_DONE
