#!/bin/bash
# What this does: bakes a few settings of the painted slate demo (stage 4) at 1254, smooths the height by 0.8 px, rebuilds the normal, and scores each with lib/texture_compare.py.
cd proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
i=0
for params in '{"stage":4,"drip_u":34,"drip_v":5}' '{"stage":4,"drip_u":22,"drip_v":9}' '{"stage":4,"drip_u":16,"drip_v":8}' '{"stage":4,"drip_u":12,"drip_v":5,"drip_amount":0.9}'; do
  OUTF=$R/data/slate_demo/tune$i
  $B -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $R/scripts/r12_painted_slate_demo.py $OUTF --size 1254 --params "$params" --normal-reference slate > $R/data/slate_demo/tune_bake$i.log 2>&1
  $B -b --disable-autoexec -t 2 --python $R/scripts/post_smooth_height.py -- $OUTF 0.8 slate > $R/data/slate_demo/tune_post$i.log 2>&1
  python3 -I lib/texture_compare.py slate ${OUTF}_smooth --json ${OUTF}_smooth/score.json --sheet ${OUTF}_smooth/sheet.png > /dev/null 2>&1
  echo "$params" > ${OUTF}_smooth/params.txt
  echo "tune $i done $params"
  i=$((i+1))
done
