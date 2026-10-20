#!/bin/bash
# What this does (plain words): runs, one after the other, every check and picture-making job of the MOSS layer with the FINAL default settings:
# independence test, half-tile test, debug views and before/after, the full-stack bake at 1254 with the harness (all maps + timing), then all the control strips.
# Logs go to moss_work/dev/final_log.txt. Use: moss_work/run_final.sh   (takes about an hour on the shared machine)
HERE="$(cd "$(dirname "$0")" && pwd)"
SL="$HERE/.."
LOG="$HERE/dev/final_log.txt"
echo "start $(date)" > "$LOG"
mkdir -p "$SL/tests/moss" "$SL/outputs/moss_default"
export MOSS_FROZEN=1          # the independence, half-tile, before/after and full-stack bakes use the frozen copy of the whole stack (see frozen/README.txt)
"$HERE/refresh_frozen.sh" >> "$LOG" 2>&1
echo "start $(date)" > "$LOG"
python3 -I "$HERE/moss_independence.py" 384 "$SL/tests/moss/independence" >> "$LOG" 2>&1; echo "independence done $(date)" >> "$LOG"
python3 -I "$HERE/moss_half_tile.py" 512 "$SL/tests/moss/half_tile" >> "$LOG" 2>&1; echo "half tile done $(date)" >> "$LOG"
python3 -I "$HERE/make_debug_and_before_after.py" 1254 >> "$LOG" 2>&1; echo "debug and before/after done $(date)" >> "$LOG"
S=$(date +%s)
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python "$SL/../../lib/bake_harness.py" -- "$HERE/frozen/recipe/slate_recipe.py" "$SL/outputs/moss_default" --size 1254 --normal-reference slate > "$SL/outputs/moss_default/log.txt" 2>&1
echo "full-stack harness bake seconds: $(( $(date +%s) - S ))" >> "$LOG"
python3 -I "$HERE/dev_scripts/measure_moss_in_picture.py" "$SL/outputs/moss_default/colour.png" > "$SL/tests/moss/final_tile_moss_measure.txt" 2>&1
python3 -I "$HERE/dev_scripts/run_all_sweeps.py" 512 >> "$LOG" 2>&1; echo "sweeps done $(date)" >> "$LOG"
echo "ALL DONE $(date)" >> "$LOG"
