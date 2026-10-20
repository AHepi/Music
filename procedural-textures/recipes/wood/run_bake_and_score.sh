#!/bin/bash
# What this does (plain words): bakes one wood description with the Blender generator and scores the result with both comparison tools.
# Use: ./run_bake_and_score.sh DESCRIPTION.json OUTPUT_FOLDER [SIZE] [--no-sheets]
# Blender needs about 15 to 40 seconds for a 1254 dot picture set; scoring takes about 20 seconds more.
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
HERE="$(cd "$(dirname "$0")" && pwd)"
DESC="$1"; OUT="$2"; SIZE="${3:-1254}"
$BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/wood_generator.py" -- "$DESC" "$OUT" --size "$SIZE" 2>&1 | grep -E "bake\]|Error|Traceback|error" 
if [ "$SIZE" = "1254" ]; then python3 -I "$HERE/analysis/score_folder.py" "$OUT" $4; fi
