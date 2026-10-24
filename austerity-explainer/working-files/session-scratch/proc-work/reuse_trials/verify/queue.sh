#!/bin/bash
# What this does: runs the independent checker's remaining Blender jobs one after another (never two at once), each with -t 2.
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/reuse_trials/verify || exit 1
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
while ! grep -q "Blender quit" run_gravel.log; do sleep 5; done
for s in brick mud; do $B -b --disable-autoexec -t 2 --python verify_run.py -- $s 1,2 > run_$s.log 2>&1; done
for s in metal brick wood mud gravel; do $B -b --disable-autoexec -t 2 --python rebake_colour.py -- $s > rebake_$s.log 2>&1; done
$B -b --disable-autoexec -t 2 --python rebake_colour.py -- metal heightonly --extra '{"recipe.height_rule": "combine"}' --tag combinerule > rebake_metal_combinerule.log 2>&1
echo queue finished > queue_done.txt
