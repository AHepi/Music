#!/bin/bash
# What this does: bakes the painted slate demo at stages 0 to 4 (1254 x 1254) and scores each against the slate reference with lib/texture_compare.py.
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=research/experiments_hand_painted_look
for s in 0 1 2 3 4; do
  OUTF=$R/data/slate_demo/stage$s
  $B -b --disable-autoexec -t 2 --python lib/bake_harness.py -- $R/scripts/r12_painted_slate_demo.py $OUTF --size 1254 --params "{\"stage\":$s}" --normal-reference slate > $R/data/slate_demo/bake_stage$s.log 2>&1
  python3 -I lib/texture_compare.py slate $OUTF --json $OUTF/score.json --sheet $OUTF/sheet.png > $R/data/slate_demo/score_stage$s.log 2>&1
  echo "stage $s done"
done
