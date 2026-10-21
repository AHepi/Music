#!/bin/bash
# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Runs ONE Blender run for a job file made by make_job_lists.py (the street file or the film's lockout shot file, which is opened read-only and never saved), then measures
# every new picture (joint visibility, study/tools/b05_measure_folder.py) and turns the pictures into JPEGs. One Blender process at a time; stops if free disk space is under 1.25 GB.
# Use:   bash run_jobs_here.sh JOB_FILE            (the folder is the job file's folder; the kind comes from its name: jobs_street.json or jobs_lockout.json)
# Run it in the background for anything long (the shell tool stops a foreground command after 10 minutes), and wait for the line "RUN FINISHED" in <folder>/run_<kind>.log.
HERE="$(cd "$(dirname "$0")" && pwd)"
STUDY="$(cd "$HERE/../../study/tools" && pwd)"
S="$(cd "$HERE/../../.." && pwd)"                    # street_wet
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
LOCKOUT=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
JOBS="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(dirname "$JOBS")"
KIND=$(basename "$JOBS" .json); KIND=${KIND#jobs_}
free_mb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_mb)" -lt 1250 ]; then echo "STOP: free disk space is below 1.25 GB"; exit 1; fi
if [ "$KIND" = street ]; then FILE=$S/set_copy/street.blend; else FILE=$LOCKOUT; fi
cd "$S"
START=$(date +%s)
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 "$FILE" --python "$STUDY/b03_render_jobs.py" -- "$JOBS" "$OUT" > "$OUT/log_$KIND.txt" 2>&1
python3 -I "$STUDY/b05_measure_folder.py" "$OUT" "$JOBS" --convert > "$OUT/measure_$KIND.txt" 2>&1
echo "RUN FINISHED $KIND after $(( $(date +%s) - START )) s; free disk $(free_mb) MB" | tee "$OUT/run_$KIND.log"
