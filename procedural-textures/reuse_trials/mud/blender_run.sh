#!/bin/bash
# What this does (plain words): starts ONE Blender run for the mud trial (always with 2 threads, as the house rules say) and writes one line to
# blender_runs.log first, so the number of Blender starts can be counted. Use: ./blender_run.sh "what this run is for" SCRIPT.py -- script arguments
# (run it from reuse_trials/mud; the log is in the same folder).
cd "$(dirname "$0")"
echo "$(date '+%Y-%m-%d %H:%M:%S') | $1 | $2" >> blender_runs.log
shift
SCRIPT="$1"; shift
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python "$SCRIPT" "$@"
