#!/bin/bash
# regrade tests on the already drawn EXRs: shadow-lift variants (no new drawing)
B=/workspace/blender/blender
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
S=$G/fix/stage
O=$G/fix/out/rp1
mkdir -p $O
$B -b --disable-autoexec -P $S/regrade_fix.py -- $G/final/renders/real_hero.exr $O/tr_real none "a=0.02,0.004,0.8,1,1" "b=0.02,0.008,0.8,1,1" "c=0.03,0.014,0.8,1,1" 2>&1 | grep -i "REGRADE_FIX_DONE\|error\|Traceback" 
$B -b --disable-autoexec -P $S/regrade_fix.py -- $G/final/renders/painted_hero.exr $O/tr_painted none "b=0.02,0.008,0.8,1,1" 2>&1 | grep -i "REGRADE_FIX_DONE\|error\|Traceback"
