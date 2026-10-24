#!/bin/bash
M=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/metal
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$B -b --disable-autoexec -t 2 --python $M/verify/sweep_check.py > $M/verify/log_sweep.txt 2>&1
$B -b --disable-autoexec -t 2 --python $M/generator/metal_generator.py -- $M/description/hull_plates.json $M/verify/hull --samples 8 --channels colour > $M/verify/log_hull.txt 2>&1
echo moredone > $M/verify/more_done.txt
