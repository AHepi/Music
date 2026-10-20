#!/bin/bash
# What this does (plain words): after the main test programme, bakes and scores the traced classes made with patches that may join across the tile edge ("w" = wrap-aware,
# so a patch that crosses the tile edge keeps ONE colour: no colour seam), then the half-tile test on one of them.
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
until grep -q ALL_DONE "$HERE/scores/after_ladder.log"; do sleep 10; done
for name in M1_trace_20k M2_trace_40k M3_trace_62k L1_trace_150k L2_trace_300k L3_trace_480k; do
  "$HERE/run_bake_and_score.sh" "$HERE/description/${name}w.json" "$HERE/outputs/ladder_${name}w" 1254 > "$HERE/scores/ladder_${name}w.log" 2>&1
  cp "$HERE/outputs/ladder_${name}w/score.json" "$HERE/scores/ladder_${name}w.json" 2>/dev/null
  echo "${name}w done $(date +%T)"
done
$BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/wood_generator.py" -- "$HERE/description/L2_trace_300kw.json" "$HERE/scores/half_tile/L2w_shifted" --size 1254 --shift 0.5 0.5 > /dev/null 2>&1
python3 -I "$HERE/analysis/half_tile_test.py" "$HERE/outputs/ladder_L2_trace_300kw" "$HERE/scores/half_tile/L2w_shifted" --json "$HERE/scores/half_tile/L2w.json"
echo W_ALL_DONE
