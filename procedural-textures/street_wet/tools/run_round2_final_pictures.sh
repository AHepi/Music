#!/bin/bash
# What this does: waits until the long chain (run_round2_bake_and_plate.sh) has finished (never two Blender runs at once), then draws the pictures of round 2 again with the FINAL settings
# (the first set, work/r31, was drawn before the walls' roughness went from 0.75 to 0.9 and before the dressed stones were darkened): the main camera wet and heavy and the wall close-up, EEVEE.
cd "$(dirname "$0")/.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
until grep -q "ALL DONE" work/r35/progress.txt 2>/dev/null; do sleep 10; done
mkdir -p work/r36
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/29_pictures_round2.py -- work/r36 wall_lamp:wet:640:480:24 main:wet:540:960:16 main:heavy:540:960:16 > work/r36/run.log 2>&1
echo "final pictures finished $(date +%T)" >> work/r36/progress.txt
echo ALL DONE >> work/r36/progress.txt
