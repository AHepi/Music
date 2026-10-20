#!/bin/bash
# What this does: bakes the painted gravel demo with stone sizes taken from the measured reference (4 layers: earth speckle, small, medium, big stones), smooths height 0.8 px, scores against gravel.
cd proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
OUTF=$R/data/gravel_demo/spec
$B -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $R/scripts/r16_painted_gravel_demo.py $OUTF --size 1254 --params '{"layers":4,"earth_scale":110,"scales":[64,30,13],"coverage":[0.62,0.5,0.4],"rim_px":[1.5,2.5,4],"facet_scale":[1.6,2.0,2.5]}' --normal-reference gravel > $R/data/gravel_demo/bake_spec.log 2>&1
$B -b --disable-autoexec -t 2 --python $R/scripts/post_smooth_height.py -- $OUTF 0.8 gravel > $R/data/gravel_demo/post_spec.log 2>&1
python3 -I lib/texture_compare.py gravel ${OUTF}_smooth --json ${OUTF}_smooth/score.json --sheet ${OUTF}_smooth/sheet.png > /dev/null 2>&1
echo "spec done"
