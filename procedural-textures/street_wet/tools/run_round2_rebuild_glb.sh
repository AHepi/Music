#!/bin/bash
# What this does: rebuilds the wet .glb and the baked .blend from the maps already made (--reuse: no photographing, seconds), with the fitted colour numbers of the flat stand-ins, then draws the baked
# street from the main camera with EEVEE to compare with the live layer again (tools/31_compare_baked_live.py reads work/r34/main_today.png; the first comparison is kept as work/r34/first_baked...).
cd "$(dirname "$0")/.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p work/r37
cp work/r34/main_today.png work/r37/first_baked_picture.png
cp work/r34/live_vs_baked.json work/r37/first_live_vs_baked.json
$BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/06_bake_maps_and_export.py -- maps glb/street-wet.glb set_copy/street_wet_baked.blend --reuse > work/r37/rebuild.log 2>&1
echo "rebuild finished $(date +%T)" >> work/r37/progress.txt
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 set_copy/street_wet_baked.blend --python tools/22_render_eevee.py -- work/r34 main today 540 960 16 > work/r34/run2.log 2>&1
echo "baked picture finished $(date +%T)" >> work/r37/progress.txt
echo ALL DONE >> work/r37/progress.txt
