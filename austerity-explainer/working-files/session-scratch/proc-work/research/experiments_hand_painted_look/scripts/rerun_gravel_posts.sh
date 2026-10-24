#!/bin/bash
# What this does: redoes smoothing + scoring for the gravel demo folders g0..g3 (after the grey-save bug fix), then bakes and scores the measured-size variant.
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
for i in 0 1 2 3; do
  OUTF=$R/data/gravel_demo/g$i
  $B -b --disable-autoexec -t 2 --python $R/scripts/post_smooth_height.py -- $OUTF 0.8 gravel > $R/data/gravel_demo/post$i.log 2>&1
  python3 -I lib/texture_compare.py gravel ${OUTF}_smooth --json ${OUTF}_smooth/score.json --sheet ${OUTF}_smooth/sheet.png > /dev/null 2>&1
  echo "gravel g$i rescored"
done
$R/scripts/run_gravel_spec.sh
