#!/bin/bash
# What this does: how much does the score move when only the random seed changes? Bakes each of the six recipes with three seeds at 384 px, scores each against its
# reference and prints the three overall scores. (A score that moves by 0.05 from the seed alone means differences smaller than that are noise.)
# Use: ./seed_spread.sh   (writes out/seed_spread/summary.txt)
HERE="$(cd "$(dirname "$0")" && pwd)"; PROC="$HERE/../.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p "$HERE/out/seed_spread"; : > "$HERE/out/seed_spread/summary.txt"
declare -A BASE=( [brick]=3 [slate]=5 [wood]=2 [metal]=4 [mud]=6 [gravel]=9 )
for surface in brick slate wood metal mud gravel; do
  scores=""
  for offset in 0 100 200; do
    seed=$(( ${BASE[$surface]} + offset ))
    folder="$HERE/out/seed_spread/${surface}_$seed"
    $BLENDER -b --disable-autoexec -t 2 --python "$PROC/lib/bake_harness.py" -- "$HERE/recipes/recipe_$surface.py" "$folder" --size 384 --normal-reference $surface --params "{\"seed\": $seed}" > /dev/null 2>&1
    python3 -I "$PROC/lib/texture_compare.py" $surface "$folder" --json "$folder/score.json" > /dev/null 2>&1
    s=$(python3 -I -c "import json;print(round(json.load(open('$folder/score.json'))['overall'],3))")
    scores="$scores $s"
  done
  echo "$surface seeds ${BASE[$surface]}/+100/+200 overall scores:$scores" | tee -a "$HERE/out/seed_spread/summary.txt"
done
