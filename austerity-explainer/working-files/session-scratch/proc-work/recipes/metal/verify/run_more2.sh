#!/bin/bash
M=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/metal
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
G="$B -b --disable-autoexec -t 2 --python $M/generator/metal_generator.py --"
$G $M/description/hull_plates.json $M/verify/hull_shift --samples 8 --channels colour --shift 627 > $M/verify/log_hull_shift.txt 2>&1
$G $M/verify/var1/description.json $M/verify/var1 --samples 8 --channels colour > $M/verify/log_var1.txt 2>&1
$G $M/verify/var8/description.json $M/verify/var8 --samples 8 --channels colour > $M/verify/log_var8.txt 2>&1
$G $M/verify/var3_nograin/description.json $M/verify/var3_nograin --samples 8 --channels colour > $M/verify/log_ng.txt 2>&1
$G $M/verify/var3_nograin/description.json $M/verify/var3_nograin_shift --samples 8 --channels colour --shift 627 > $M/verify/log_ng_shift.txt 2>&1
echo done > $M/verify/more2_done.txt
