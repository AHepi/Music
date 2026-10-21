#!/bin/bash
# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Runs ONE Blender run for a job file written by write_jobs.py (the street copy, or the film's lockout shot file opened read-only and never saved), then measures the pictures and turns
# them into JPEG files. It is meant to be started ON the rented machine (the one with the RTX 4090 card) by rent_run.py, which uploads the tools first and downloads the folder after.
# Use (on the rented machine, or here with HERE=local):   bash run_rubbish_jobs.sh JOB_FILE
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$(cd "$HERE/../../.." && pwd)"                    # street_wet
if [ -x /workspace/blender/blender ]; then BLENDER=/workspace/blender/blender; XV=""; else BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender; XV="xvfb-run -a"; THREADS="-t 2"; fi
LOCKOUT=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
JOBS="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(dirname "$JOBS")"
KIND=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['kind'])" "$JOBS")
if [ "$KIND" = street ]; then FILE=$S/set_copy/street.blend; else FILE=$LOCKOUT; fi
cd "$S"
START=$(date +%s)
$XV $BLENDER -b --disable-autoexec $THREADS "$FILE" --python "$HERE/rubbish_runner.py" -- "$JOBS" "$OUT" > "$OUT/log_$KIND.txt" 2>&1
python3 -I "$HERE/measure_rubbish_folder.py" "$OUT" "$JOBS" --convert > "$OUT/measure_$KIND.txt" 2>&1
echo "RUN FINISHED $KIND after $(( $(date +%s) - START )) s" | tee "$OUT/run_$KIND.log"
