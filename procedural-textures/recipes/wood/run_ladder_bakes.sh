#!/bin/bash
# What this does (plain words): bakes every description of the wood ladder (S0, S1, M1-3, L1-3) with the Blender generator at 1254 dots, scores each with both tools
# (pixel_compare = same picture dot for dot, texture_compare = same kind of surface) and keeps the pictures in outputs/ladder_<name>/ and the numbers in scores/ladder_<name>.json.
HERE="$(cd "$(dirname "$0")" && pwd)"
for name in S0_layout_only S1_layout_paint_grain M1_trace_20k M2_trace_40k M3_trace_62k L1_trace_150k L2_trace_300k L3_trace_480k; do
  "$HERE/run_bake_and_score.sh" "$HERE/description/$name.json" "$HERE/outputs/ladder_$name" 1254 > "$HERE/scores/ladder_$name.log" 2>&1
  cp "$HERE/outputs/ladder_$name/score.json" "$HERE/scores/ladder_$name.json" 2>/dev/null
  echo "$name done"
done
