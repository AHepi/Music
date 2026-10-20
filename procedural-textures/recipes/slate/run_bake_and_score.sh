#!/bin/bash
# What this does (plain words): bakes one description with the Blender generator, then scores it against the reference slate with both comparison
# tools (analysis/score_folder.py). Use:  ./run_bake_and_score.sh NAME [SIZE]   (description/NAME.json -> outputs/NAME, scores/NAME_summary.json)
NAME=$1; SIZE=${2:-1254}
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$BLENDER -b --disable-autoexec -t 2 --python "$HERE/generator/slate_generator.py" -- "$HERE/description/$NAME.json" "$HERE/outputs/$NAME" --size $SIZE 2>&1 | grep -E "bake\]|Error|error" | cut -c1-500
python3 -I "$HERE/analysis/score_folder.py" "$HERE/outputs/$NAME" "$NAME"
