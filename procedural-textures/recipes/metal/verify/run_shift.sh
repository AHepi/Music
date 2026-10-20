#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
M=proc-work/recipes/metal
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$B -b --disable-autoexec -t 2 --python $M/generator/metal_generator.py -- $M/verify/var3/description.json $M/verify/var3_shift --samples 8 --channels colour --shift 627 > $M/verify/log_var3_shift.txt 2>&1
$B -b --disable-autoexec -t 2 --python $M/generator/metal_generator.py -- $M/description/L.json $M/verify/L_shift --samples 8 --channels colour --shift 627 > $M/verify/log_L_shift.txt 2>&1
$B -b --disable-autoexec -t 2 --python $M/generator/metal_generator.py -- $M/area/area_seed21.json $M/verify/area_at_1254 --samples 8 --channels colour --size 1254 > $M/verify/log_area.txt 2>&1
echo shiftdone > $M/verify/shift_done.txt
