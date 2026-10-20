#!/bin/bash
# What this does (plain words): bakes the golden-puddle mud descriptions (S, M and the traced L class) with the same generator at 1254 dots and scores their colour against the golden
# picture (it has colour only, so only colour measures exist). Output: outputs_golden/<row>/ and scores/golden_<row>.json.
cd "$(dirname "$0")/.."
mkdir -p outputs_golden
for name in S_layout_ruts_clods M_puddle_tones_stone_faces L_traced_ground_5000_patches; do
  generator/bake_one.sh description_mud_golden/$name.json outputs_golden/$name 1254 8 > scores/golden_bake_$name.log 2>&1
  python3 -I analysis/score_golden.py outputs_golden/$name > scores/golden_$name.line 2>&1
  echo "$name $(cat scores/golden_$name.line)"
done
echo GOLDEN_BAKES_DONE
