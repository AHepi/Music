#!/bin/bash
# What this does: the measured-size gravel demo plus per-stone brightness jitter (0.35) and fine grain (0.15): does variation INSIDE the flat palette help the score?
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
OUTF=$R/data/gravel_demo/spec_jitter
$B -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $R/scripts/r16_painted_gravel_demo.py $OUTF --size 1254 --params '{"layers":4,"earth_scale":110,"scales":[64,30,13],"coverage":[0.62,0.5,0.4],"rim_px":[1.5,2.5,4],"facet_scale":[1.6,2.0,2.5],"value_jitter":0.35,"grain":0.15}' --normal-reference gravel > $R/data/gravel_demo/bake_spec_jitter.log 2>&1
$B -b --disable-autoexec -t 2 --python $R/scripts/post_smooth_height.py -- $OUTF 0.8 gravel > $R/data/gravel_demo/post_spec_jitter.log 2>&1
python3 -I lib/texture_compare.py gravel ${OUTF}_smooth --json ${OUTF}_smooth/score.json --sheet ${OUTF}_smooth/sheet.png > /dev/null 2>&1
echo "spec_jitter done"
