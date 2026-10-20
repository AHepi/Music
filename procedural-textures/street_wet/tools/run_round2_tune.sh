#!/bin/bash
# What this does: round 2 tuning, two Blender runs one after the other (never two at once), both EEVEE with xvfb-run:
#   1. the cottage-wall close-up, dry and three wet settings (tools/26_wall_variants.py)  -> work/r28
#   2. the main camera, today and two wet road settings at 16 samples (tools/27_road_variants.py) -> work/r29
cd "$(dirname "$0")/.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p work/r28 work/r29
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/26_wall_variants.py -- work/r28 wall_lamp > work/r28/run.log 2>&1
echo "walls finished $(date +%T)" >> work/r29/progress.txt
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/27_road_variants.py -- work/r29 16 today wet_a wet_b wet_c > work/r29/run.log 2>&1
echo "road finished $(date +%T)" >> work/r29/progress.txt
echo ALL DONE >> work/r29/progress.txt
