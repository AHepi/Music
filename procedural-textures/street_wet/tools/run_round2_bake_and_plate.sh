#!/bin/bash
# What this does: the long background runs of round 2, one Blender run after another (never two at once):
#   0. a tiny check on the lockout file (270 x 480, 4 samples)
#   1. photographs the maps and writes the wet .glb and the baked .blend (tools/06_bake_maps_and_export.py; Cycles, 2 threads, about 13 minutes in round 1)  -> maps/, glb/, set_copy/street_wet_baked.blend
#   2. draws the BAKED street (only the baked maps and flat numbers) with EEVEE from the main camera, to compare with the live layer (tools/31_compare_baked_live.py)  -> work/r34
#   3. draws the lockout shot (the film's own file, opened read-only, with its props) with EEVEE: today and wet at 540 x 960, then the full-size wet PLATE 1536 x 2730  -> work/r35
cd "$(dirname "$0")/.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
LOCKOUT=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
mkdir -p work/r33 work/r34 work/r35 work/r35check
# 0. a tiny check that the layer goes onto the film's lockout file (so that a mistake shows up in a minute, not after the long runs)
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 $LOCKOUT --python tools/29_pictures_round2.py -- work/r35check main:today:270:480:4 main:wet:270:480:4 > work/r35check/run.log 2>&1
echo "lockout check finished $(date +%T)" >> work/r35/progress.txt
$BLENDER -b --disable-autoexec -t 2 set_copy/street.blend --python tools/06_bake_maps_and_export.py -- maps glb/street-wet.glb set_copy/street_wet_baked.blend > work/r33/bake.log 2>&1
echo "bake finished $(date +%T)" >> work/r35/progress.txt
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 set_copy/street_wet_baked.blend --python tools/22_render_eevee.py -- work/r34 main today 540 960 16 > work/r34/run.log 2>&1
echo "baked picture finished $(date +%T)" >> work/r35/progress.txt
xvfb-run -a $BLENDER -b --disable-autoexec -t 2 $LOCKOUT --python tools/29_pictures_round2.py -- work/r35 main:today:540:960:16 main:wet:540:960:16 main:wet@plate:1536:2730:32 > work/r35/run.log 2>&1
echo "plate finished $(date +%T)" >> work/r35/progress.txt
echo ALL DONE >> work/r35/progress.txt
