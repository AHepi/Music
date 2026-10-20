#!/bin/bash
# What this does (plain words): bakes and scores the four "what does one layer buy?" extras: S1 without grain, S0 with grain only, L2 and M3 with the grain added on top.
HERE="$(cd "$(dirname "$0")" && pwd)"
for name in X1_S1_without_grain X2_S0_with_grain X3_L2_with_grain X4_M3_with_grain; do
  "$HERE/run_bake_and_score.sh" "$HERE/description/$name.json" "$HERE/outputs/extra_$name" 1254 --no-sheets > "$HERE/scores/extra_$name.log" 2>&1
  cp "$HERE/outputs/extra_$name/score.json" "$HERE/scores/extra_$name.json" 2>/dev/null
  echo "$name done"
done
