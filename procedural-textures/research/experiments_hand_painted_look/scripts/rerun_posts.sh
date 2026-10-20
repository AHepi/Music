#!/bin/bash
# What this does: after fixing the grey-image save bug, redoes the "smooth the height 0.8 px, rebuild the normal, score" step for the slate tuning folders
# and the Kuwahara consistency sets, then for the gravel demo folders.
cd proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
for i in 0 1 2 3; do
  OUTF=$R/data/slate_demo/tune$i
  $B -b --disable-autoexec -t 2 --python $R/scripts/post_smooth_height.py -- $OUTF 0.8 slate > $R/data/slate_demo/tune_post$i.log 2>&1
  python3 -I lib/texture_compare.py slate ${OUTF}_smooth --json ${OUTF}_smooth/score.json --sheet ${OUTF}_smooth/sheet.png > /dev/null 2>&1
  echo "slate tune $i rescored"
done
$B -b --disable-autoexec -t 2 --python $R/scripts/c14_kuwahara_and_consistency.py > $R/data/slate_demo/c14_rerun.log 2>&1
for n in stage5_aniso_h1 stage5_aniso_h1_smooth08 stage5_aniso_h2 stage5_aniso_h3 stage5_classic_h1; do
  python3 -I lib/texture_compare.py slate $R/data/slate_demo/$n --json $R/data/slate_demo/$n/score.json --sheet $R/data/slate_demo/$n/sheet.png > /dev/null 2>&1
  echo "slate $n rescored"
done
