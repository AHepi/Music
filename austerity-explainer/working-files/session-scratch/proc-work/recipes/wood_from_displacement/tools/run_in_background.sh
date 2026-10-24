#!/bin/bash
# What this does (plain words): runs ONE Blender job list (tools/run_jobs.py) with 2 threads, writes the log next to the jobs file name and a ".done" marker
# file when it has finished, so that a long run can be waited for with a single "until" loop. Only one Blender at a time on this machine.
# Use: bash tools/run_in_background.sh JOBS.json LOGNAME     (from anywhere; JOBS.json relative to the recipe folder, e.g. tests/jobs_r2_c.json)
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work || exit 1
W=recipes/wood_from_displacement
( time $BL -b --disable-autoexec -t 2 --python $W/tools/run_jobs.py -- $W/$1 ) > $W/tests/r2/$2.log 2>&1
echo finished > $W/tests/r2/$2.done
