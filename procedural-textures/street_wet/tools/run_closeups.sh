#!/bin/bash
# What this does: draws the four close-up pictures one after the other: the setts (close_road) and the foot of a wall beside the first gas lamp (wall_lamp), each dry and wet.
# Cycles, 2 threads, 640 x 480, 40 samples (sampling stops after 300 seconds at the latest), noise filter on.
cd "$(dirname "$0")/.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p work/r08
for cam in close_road wall_lamp; do
  $BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/05_render_views.py -- work/r08 $cam dry,wet 640 480 40 300 > work/r08/run_$cam.log 2>&1
  echo "$cam finished $(date +%T)" >> work/r08/progress.txt
done
echo ALL DONE >> work/r08/progress.txt
