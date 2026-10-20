#!/bin/bash
# What this does: draws the four main pictures one after the other (never two Blender programs at once): A = the street as it is today, B = new materials dry,
# C = wet, D = wet with heavier rain. Main camera, 540 x 960, Cycles on the processor with 2 threads, 32 samples (stops sampling after 400 seconds at the latest), noise filter on.
cd "$(dirname "$0")/.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p work/r07
for state in today dry wet heavy; do
  $BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/05_render_views.py -- work/r07 main $state 540 960 32 400 > work/r07/run_$state.log 2>&1
  echo "$state finished $(date +%T)" >> work/r07/progress.txt
done
echo ALL DONE >> work/r07/progress.txt
