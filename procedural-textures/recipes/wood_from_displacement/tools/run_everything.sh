#!/bin/bash
# ROUND 1 TOOL (kept for the record; round 2: tools/run_round2_chain.sh).
# What this does (plain words): the one-go version of the final bakes (tests/jobs_final_all.json: three seeds of the default tile with all maps, the comparison
# colours, the area bakes, crops, shift test, source-unchanged check, sweeps), then the lit pictures. ONE Blender at a time, 2 threads.
# Use: bash tools/run_everything.sh      Log: tests/everything.log (one line per finished part)
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd proc-work || exit 1
W=recipes/wood_from_displacement
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_final_all.json > $W/tests/final_all.log 2>&1
echo "all bakes done $(date +%H:%M:%S)" >> $W/tests/everything.log
$BL -b --disable-autoexec -t 2 --python $W/tools/lit_preview_multi.py -- $W/tests/jobs_lit.json > $W/tests/lit.log 2>&1
echo "lit done $(date +%H:%M:%S)" >> $W/tests/everything.log
