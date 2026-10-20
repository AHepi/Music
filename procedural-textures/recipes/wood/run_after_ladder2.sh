#!/bin/bash
# What this does (plain words): the rest of the wood test programme, run one step after another once the ladder bakes are finished:
# extras (what does one layer buy), sweeps for the guide, 8 variations, resolution and area, the half-tile seamless tests, the real-geometry comparison, and the transfer bake.
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p "$HERE/guide_pictures"
$BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/sweeps_for_guide.py" -- "$HERE/guide_pictures" > "$HERE/guide_pictures/sweeps_run.log" 2>&1; echo "sweeps done $(date +%T)"
for s in grain_light_cut grain_hair_thickness paint_zone_amp paint_rate cracks_scale plank_count; do
  python3 -I "$HERE/../../lib/make_strip.py" "$HERE/guide_pictures/sweep_$s" "$HERE/guide_pictures/strip_$s.png" --columns 5 --cell 300 --title "$(python3 -I -c "import json;print(json.load(open('$HERE/guide_pictures/sweep_$s/sweep.json'))['title'])")" > /dev/null
done
python3 -I "$HERE/analysis/run_variations.py" > "$HERE/variations/run.log" 2>&1; echo "variations done $(date +%T)"
python3 -I "$HERE/analysis/run_resolution_area.py" > "$HERE/area/run.log" 2>&1; echo "resolution and area done $(date +%T)"
# half-tile tests: S1, L2 and a sampled tile
mkdir -p "$HERE/scores/half_tile"
for pair in "S1_layout_paint_grain:$HERE/description/S1_layout_paint_grain.json:$HERE/outputs/ladder_S1_layout_paint_grain" "L2_trace_300k:$HERE/description/L2_trace_300k.json:$HERE/outputs/ladder_L2_trace_300k" "sample_101:$HERE/variations/sample_101.json:$HERE/variations/sample_101"; do
  IFS=: read name desc normal <<< "$pair"
  $BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/wood_generator.py" -- "$desc" "$HERE/scores/half_tile/${name}_shifted" --size 1254 --shift 0.5 0.5 > /dev/null 2>&1
  python3 -I "$HERE/analysis/half_tile_test.py" "$normal" "$HERE/scores/half_tile/${name}_shifted" --json "$HERE/scores/half_tile/${name}.json"
done
echo "half tile done $(date +%T)"
$BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/geometry_route.py" -- "$HERE/outputs/geometry_route" 5 > "$HERE/outputs/geometry_route/run.log" 2>&1; echo "geometry route done $(date +%T)"
python3 -I "$HERE/transfer/make_deck_boards.py" 1
( time "$HERE/run_bake_and_score.sh" "$HERE/transfer/deck_boards_seed1.json" "$HERE/transfer/deck_boards_seed1" 1254 --no-sheets ) > "$HERE/transfer/deck_boards_seed1.log" 2>&1; echo "transfer done $(date +%T)"
echo ALL_DONE
