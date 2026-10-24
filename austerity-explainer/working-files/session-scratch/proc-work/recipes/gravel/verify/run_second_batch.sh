#!/bin/bash
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/gravel
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$BL -b --disable-autoexec -t 2 --python $G/generator/gravel_generator.py -- $G/variations/descriptions/sample_03.json $G/verify/var_03 --size 1254 > $G/verify/bake_var_03.log 2>&1
$BL -b --disable-autoexec -t 2 --python $G/generator/gravel_generator.py -- $G/description/transfer_pebbles.json $G/verify/pebbles --size 1254 > $G/verify/bake_pebbles.log 2>&1
$BL -b --disable-autoexec -t 2 --python $G/generator/gravel_generator.py -- $G/area/descriptions/sample_101.json $G/verify/area_2508 --size 2508 > $G/verify/bake_area.log 2>&1
touch $G/verify/second_batch_done.flag
