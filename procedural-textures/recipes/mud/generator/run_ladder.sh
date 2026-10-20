#!/bin/bash
# What this does (plain words): bakes every row of the ladder (flat ground ... traced-patches class) with Blender at 1254 dots and scores each with both comparison tools.
# Output: outputs/<row>/ (colour, height, normal, ...), scores/<row>.json. Use: generator/run_ladder.sh   (about 10 minutes on a shared computer)
cd "$(dirname "$0")/.."
for name in R0_flat_ground R1_plus_puddle_outlines R2_plus_40_big_stones R3_plus_ruts S_layout_ruts_clods M_puddle_tones_stone_faces L2_traced_ground_2000_patches L_traced_ground_5000_patches; do
  short=${name%%_*}; case "$name" in S_*) short=S;; M_*) short=M;; esac
  folder="outputs/$name"
  generator/bake_one.sh description/$name.json $folder 1254 8 > scores/bake_$name.log 2>&1
  python3 -I analysis/score_folder.py $folder > scores/$name.line 2>&1
  cp $folder/score.json scores/$name.json
  echo "$name $(cat scores/$name.line)"
done
echo LADDER_DONE
