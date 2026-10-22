#!/bin/bash
B=/workspace/blender/blender
G=proc-work/garden
S=$G/fix/stage
O=$G/fix/out/rp2
mkdir -p $O
$B -b --disable-autoexec -P $S/regrade_fix.py -- $G/final/renders/real_hero.exr $O/tr_real "n=none" "a=0.02,0.004,0.75,1,0.95" "b=0.02,0.008,0.75,1,0.95" "c=0.03,0.014,0.75,1,0.95" "d=0.04,0.024,0.75,1,0.95" 2>&1 | grep -i "REGRADE_FIX_DONE\|error\|Traceback"
