#!/bin/bash
# RunPod round 5: final pictures of the light stage alone after the warmer sky. Cycles on the card, 960x640, 192 samples; hero real also writes the light-group EXR.
B=/workspace/blender/blender
G=scratchpad
S=$G/astra-work/out/courtyard_final.blend
D=$G/proc-work/garden/light
O=$D/out/rp/r5
mkdir -p $O
run() { name=$1; shift; echo "=== $name"; $B -b --disable-autoexec $S -P $D/render_job.py -- "$@" --out $O/$name 2>&1 | grep -E "RENDER_JOB_DONE|GROUP_CHECK|Error|Traceback|rror:" | cut -c1-300 ; }
run hero_real     --apply-stage real    --camera photo   --size 960x640 --samples 192 --require-gpu --exr --check-groups
run hero_painted  --apply-stage painted --camera photo   --size 960x640 --samples 192 --require-gpu
run ver_real      --apply-stage real    --camera veranda --size 960x640 --samples 192 --require-gpu
run ver_painted   --apply-stage painted --camera veranda --size 960x640 --samples 192 --require-gpu
run pano_real     --apply-stage real    --pano 3.5,-2.5,1.7 --size 2400x1000 --samples 64 --require-gpu
run pano_painted  --apply-stage painted --pano 3.5,-2.5,1.7 --size 2400x1000 --samples 64 --require-gpu
ls $O
