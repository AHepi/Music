#!/bin/bash
# What this does: bakes the painted gravel demo with 1, 2, 3 layers (facets on) and 3 layers without facets at 1254, smooths the height 0.8 px, scores against gravel.
cd proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
i=0
for params in '{"layers":1}' '{"layers":2}' '{"layers":3}' '{"layers":3,"facets":0}'; do
  OUTF=$R/data/gravel_demo/g$i
  mkdir -p $R/data/gravel_demo
  $B -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $R/scripts/r16_painted_gravel_demo.py $OUTF --size 1254 --params "$params" --normal-reference gravel > $R/data/gravel_demo/bake$i.log 2>&1
  $B -b --disable-autoexec -t 2 --python $R/scripts/post_smooth_height.py -- $OUTF 0.8 gravel > $R/data/gravel_demo/post$i.log 2>&1
  python3 -I lib/texture_compare.py gravel ${OUTF}_smooth --json ${OUTF}_smooth/score.json --sheet ${OUTF}_smooth/sheet.png > /dev/null 2>&1
  echo "$params" > ${OUTF}_smooth/params.txt
  echo "g$i done $params"
  i=$((i+1))
done
