#!/bin/bash
# What this does (plain words): after the grain was made to slide with the shifted pattern, repeats the half-tile seamless tests for S1, a sampled tile and the 2508 area, then reruns the 8 variations.
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
python3 -I "$HERE/analysis/run_variations.py" > "$HERE/variations/run.log" 2>&1; echo "variations done $(date +%T)"
mkdir -p "$HERE/scores/half_tile"
for pair in "S1_layout_paint_grain:$HERE/description/S1_layout_paint_grain.json:$HERE/outputs/ladder_S1_layout_paint_grain" "sample_101:$HERE/variations/sample_101.json:$HERE/variations/sample_101" "deck_boards:$HERE/transfer/deck_boards_seed1.json:$HERE/transfer/deck_boards_seed1"; do
  IFS=: read name desc normal <<< "$pair"
  $BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/wood_generator.py" -- "$desc" "$HERE/scores/half_tile/${name}_shifted" --size 1254 --shift 0.5 0.5 > /dev/null 2>&1
  python3 -I "$HERE/analysis/half_tile_test.py" "$normal" "$HERE/scores/half_tile/${name}_shifted" --json "$HERE/scores/half_tile/${name}.json"
done
echo "half tile done $(date +%T)"
python3 -I "$HERE/analysis/run_resolution_area.py" area > "$HERE/area/run.log" 2>&1; echo "area done $(date +%T)"
echo SEAM_ALL_DONE
