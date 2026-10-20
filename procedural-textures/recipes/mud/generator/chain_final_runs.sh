#!/bin/bash
# What this does (plain words): after the first scale tests finish, re-runs the 8 variations and the scale tests with the FINAL sampler settings, so that every number in the guide
# comes from the same sampler. Order: variations (bake + score) -> area, resolution, seam test (Blender) -> scale report (plain Python).
cd "$(dirname "$0")/.."
while ! grep -q SCALE_DONE scores/scale_run.log 2>/dev/null; do sleep 20; done
rm -rf variations/tile_* variations/variation_scores.json variations/description_*.json area/area_2508 area/quadrant_* resolution/size_* resolution/shifted_half scores/scale_tests.json
python3 -I generator/run_variations.py > variations/run.log 2>&1
generator/run_scale_tests.sh > scores/scale_run2.log 2>&1
python3 -I analysis/scale_report.py > scores/scale_report.log 2>&1
echo CHAIN_DONE
