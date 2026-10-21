#!/bin/bash
# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The same job as run_jobs_here.sh, but written for the RENTED machine (the one with the RTX 4090 graphics card): one Blender run for a job file made by make_job_lists.py,
# then the joint measuring of every new picture, and the pictures turned into JPEG (the big PNG is deleted). It is started ON the rented machine by rent_and_render.py, which also
# uploads the tools first and downloads the finished folder afterwards. There is no xvfb and no "-t 2" there (the machine has 152 processor cores and a graphics card).
# Use (on the rented machine):   bash run_jobs_rented.sh JOB_FILE
HERE="$(cd "$(dirname "$0")" && pwd)"
STUDY="$(cd "$HERE/../../study/tools" && pwd)"
S="$(cd "$HERE/../../.." && pwd)"                    # street_wet
BLENDER=/workspace/blender/blender
LOCKOUT=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
JOBS="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(dirname "$JOBS")"
KIND=$(basename "$JOBS" .json); KIND=${KIND#jobs_}
if [ "$KIND" = street ]; then FILE=$S/set_copy/street.blend; else FILE=$LOCKOUT; fi
cd "$S"
START=$(date +%s)
$BLENDER -b --disable-autoexec "$FILE" --python "$STUDY/b03_render_jobs.py" -- "$JOBS" "$OUT" > "$OUT/log_$KIND.txt" 2>&1
python3 -I "$STUDY/b05_measure_folder.py" "$OUT" "$JOBS" --convert > "$OUT/measure_$KIND.txt" 2>&1
echo "RUN FINISHED $KIND after $(( $(date +%s) - START )) s" | tee "$OUT/run_$KIND.log"
