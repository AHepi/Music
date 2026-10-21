#!/bin/bash
# STUDY ONLY: times the existing picture runner (tools/22_render_eevee.py) on the rented machine: a small street picture set, a plate-size picture, and the lockout shot file.
# Draws nothing new and changes nothing but its own output folder. Run there with: bash run_timing_rented.sh
OUT=proc-work/street_wet/grime_and_growth/study/out/rented_timing
SW=proc-work/street_wet
B=/workspace/blender/blender
rm -rf "$OUT"; mkdir -p "$OUT"
t() { local label=$1; shift; local s=$(date +%s%N); "$@" > "$OUT/log_$label.txt" 2>&1; local e=$(date +%s%N); echo "$label: Blender run wall seconds $(( (e - s) / 1000000 ))e-3"; }
t A_small_street $B -b --disable-autoexec $SW/set_copy/street.blend --python $SW/tools/22_render_eevee.py -- $OUT/small main today,dry,wet,heavy 540 960 16
t B_plate_street $B -b --disable-autoexec $SW/set_copy/street.blend --python $SW/tools/22_render_eevee.py -- $OUT/plate main today,wet 1536 2730 48
t C_lockout_small $B -b --disable-autoexec /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $SW/tools/22_render_eevee.py -- $OUT/lockout lockout today,wet 540 960 16
for f in $OUT/*/*_seconds.txt; do echo "picture $(basename $f) $(cat $f)"; done
grep -h "GPU BACKEND\|NVIDIA" $OUT/log_A_small_street.txt | head -2
