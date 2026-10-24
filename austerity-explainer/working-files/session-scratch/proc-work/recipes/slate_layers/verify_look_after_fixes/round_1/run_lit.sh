#!/bin/bash
# What this does (plain words): renders the checker's raking-light pictures (verify_look/lit_preview.py, unchanged) for the reference, the BEFORE tile
# and the AFTER tile, once for the whole tile and once zoomed in, one Blender run after another (never two at once, 2 threads each).
P=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
R=$P/recipes/slate_layers
T=$R/verify_look_after_fixes/round_1/lit_tmp
cd $P
run() { # name colour normal rough window
  for kind in full zoom; do
    if [ $kind = full ]; then W=1.0; else W=0.4; fi
    $B -b --disable-autoexec -t 2 --python $R/verify_look/lit_preview.py -- $T/${1}_$kind.png $2 $3 $4 $W 0.5 0.5 900 > $T/${1}_$kind.log 2>&1
  done
}
run reference $P/reference/slate/colour.png $P/reference/slate/normal.png none
run before $R/outputs/default_before_look_fixes/colour.png $R/outputs/default_before_look_fixes/normal.png $R/outputs/default_before_look_fixes/roughness.png
run after $R/outputs/default/colour.png $R/outputs/default/normal.png $R/outputs/default/roughness.png
echo ALL_DONE > $T/done.txt
