#!/bin/bash
# plain note: my own re-run of the half-tile test (one Blender run, 2 threads), writing only into mask_test/check/
cd proc-work
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python mask_test/tools/bake_jobs.py -- mask_test/check/jobs_half_check.json > mask_test/check/half_run.log 2>&1
echo FINISHED >> mask_test/check/half_run.log
