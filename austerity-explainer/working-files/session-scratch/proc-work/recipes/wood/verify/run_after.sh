#!/bin/bash
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
W=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/wood
V=$W/verify
# wait for the ladder batch to end (wait on its log's final line count of bake lines)
while [ $(grep -c "bake\]" $V/bake_ladder.log) -lt 8 ]; do sleep 5; done
$B -b --disable-autoexec -t 2 --python $W/generator/wood_generator.py -- --batch $V/jobs_b.json > $V/bake_b.log 2>&1
$B -b --disable-autoexec -t 2 --python $W/generator/wood_generator.py -- --batch $V/jobs_shift.json --shift 0.5 0.5 > $V/bake_shift.log 2>&1
echo done > $V/after_done.txt
