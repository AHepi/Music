#!/bin/bash
# What this does (plain words): after chain 9, draws the road's puddle and wet masks (a checking view, plain light) for the wet and heavy states on the main and close cameras, so that the study
# can say how much of the joints lie under puddles. Then it works that out with b12_puddles_over_joints.py.
S=proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S
until grep -q "CHAIN 9 DONE" $R/work/logs/chain9.log 2>/dev/null; do sleep 15; done
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b03_render_jobs.py -- $R/work/jobs/puddle_masks_street.json $R/work/r10 > $R/work/logs/puddle_masks.log 2>&1
python3 -I $R/tools/b12_puddles_over_joints.py $R/work/r10 > $R/work/logs/puddles_over_joints.txt 2>&1
echo "CHAIN 10 DONE $(date +%T)" >> $R/work/logs/chain10.log
