#!/bin/bash
# What this does (plain words): the final sequence of Blender runs with the final sampler: the sweep pictures for the guide, the 8 variations (bake + score), the area / resolution / seam
# tests and the scale report, and the extra half-tile seam tests on the reference-fitted descriptions. One step after the other (about 40 minutes on a shared computer).
cd "$(dirname "$0")/.."
rm -rf guide_pictures/sweep_* guide_pictures/strip_* variations/tile_* variations/variation_scores.json variations/description_*.json area/area_2508 area/quadrant_* resolution/size_* resolution/shifted_half scores/scale_tests.json
python3 -I generator/sweeps_for_guide.py prepare guide_pictures > guide_pictures/sweeps_prepare.log 2>&1
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python generator/sweeps_for_guide.py -- bake guide_pictures > guide_pictures/sweeps_run.log 2>&1
echo SWEEPS_DONE
python3 -I generator/run_variations.py > variations/run.log 2>&1
echo VARIATIONS_DONE
generator/run_scale_tests.sh > scores/scale_run2.log 2>&1
python3 -I analysis/scale_report.py > scores/scale_report.log 2>&1
echo SCALE_DONE_2
echo CHAIN_DONE
