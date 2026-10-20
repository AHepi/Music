#!/bin/bash
# What this does: bakes one recipe (colour, height, roughness, metallic, normal) at a small size, scores it against a reference
# surface with the project's scorer and writes a side-by-side sheet. Plain note: the first word after the script name is the surface
# (brick, slate, wood, metal, mud, gravel), then the recipe file, then a folder name (made under out/), then the size (default 512).
# Use:  ./bake_and_score.sh brick recipes/recipe_brick.py brick_v1 512 '{"mode": "slate"}'   (the last item, recipe settings, is optional)
SURFACE=$1; RECIPE=$2; NAME=$3; SIZE=${4:-512}; PARAMS=${5:-{\}}
HERE="$(cd "$(dirname "$0")" && pwd)"
PROC="$HERE/../.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
OUT="$HERE/out/$NAME"
$BLENDER -b --disable-autoexec -t 2 --python "$PROC/lib/bake_harness.py" -- "$RECIPE" "$OUT" --size $SIZE --normal-reference $SURFACE --params "$PARAMS" 2>&1 | grep -E "bake\]|Error|error|Traceback|File \"" 
python3 -I "$PROC/lib/texture_compare.py" $SURFACE "$OUT" --json "$OUT/score.json" --sheet "$OUT/sheet.png" > "$OUT/score.txt" 2>&1
tail -25 "$OUT/score.txt"
