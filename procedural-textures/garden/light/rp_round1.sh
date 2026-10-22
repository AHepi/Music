#!/bin/bash
# RunPod round 1 (previews): hero + veranda in both looks, one evening look, one light-group check. Cycles on the card, 960x640, 96 samples.
B=/workspace/blender/blender
G=scratchpad
S=$G/astra-work/out/courtyard_final.blend
D=$G/proc-work/garden/light
O=$D/out/rp/r1
mkdir -p $O
run() { name=$1; shift; echo "=== $name"; $B -b --disable-autoexec $S -P $D/render_job.py -- "$@" --out $O/$name 2>&1 | grep -E "DEVICES|RENDER_JOB_DONE|GROUP_CHECK|Error|Traceback|rror:" ; }
run hero_real    --apply-stage real    --camera photo    --size 960x640 --samples 96 --require-gpu
run hero_painted --apply-stage painted --camera photo    --size 960x640 --samples 96 --require-gpu
run ver_real     --apply-stage real    --camera veranda  --size 960x640 --samples 96 --require-gpu
run ver_painted  --apply-stage painted --camera veranda  --size 960x640 --samples 96 --require-gpu
run hero_evening --apply-stage real --evening --camera photo --size 960x640 --samples 96 --require-gpu
run groups_real  --apply-stage real    --camera photo    --size 480x320 --samples 48 --no-denoise --check-groups --require-gpu
ls -la $O
