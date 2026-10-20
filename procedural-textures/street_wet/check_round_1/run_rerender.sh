#!/bin/bash
# What this does: checker's own re-draw of the two close-ups (wet state only), one Blender run after the other, 2 threads, same settings as the builder (640x480, 40 samples).
# Reads the builder's street copy and tools; writes only into check_round_1/rerender.
cd proc-work/street_wet
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
OUT=check_round_1/rerender
for cam in wall_lamp close_road; do
  $BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/05_render_views.py -- $OUT $cam wet 640 480 40 300 > $OUT/run_$cam.log 2>&1
  echo "$cam finished $(date +%T)" >> $OUT/progress.txt
done
echo ALL DONE >> $OUT/progress.txt
