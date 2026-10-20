#!/bin/bash
# ROUND 1 TOOL (kept for the record; round 2: tools/run_round2_chain.sh).
# What this does (plain words): runs the last two Blender jobs of the wood-from-maps work one after the other: (1) the lit pictures of the reference and
# the new tile (tools/lit_preview_multi.py, jobs in tests/jobs_lit.json), (2) the sweeps for the guide and the 4 x 4 height pictures with parts of the
# recipe switched off (tests/jobs_final_h.json). Only ONE Blender at a time, 2 threads. Log: tests/extras_chain.log
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd proc-work || exit 1
W=recipes/wood_from_displacement
$BL -b --disable-autoexec -t 2 --python $W/tools/lit_preview_multi.py -- $W/tests/jobs_lit.json > $W/tests/lit.log 2>&1
echo "lit done $(date +%H:%M:%S)" >> $W/tests/extras_chain.log
$BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/tests/jobs_final_h.json > $W/tests/final_h.log 2>&1
echo "sweeps done $(date +%H:%M:%S)" >> $W/tests/extras_chain.log
