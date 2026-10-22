#!/bin/bash
# RunPod round 2: sun-strength variants, rim and roof-lift check through light-group passes, evening v2, veranda. Cycles on the card, 960x640, 96 samples.
B=/workspace/blender/blender
G=scratchpad
S=$G/astra-work/out/courtyard_final.blend
D=$G/proc-work/garden/light
O=$D/out/rp/r2
mkdir -p $O
run() { name=$1; shift; echo "=== $name"; $B -b --disable-autoexec $S -P $D/render_job.py -- "$@" --out $O/$name 2>&1 | grep -E "DEVICES|RENDER_JOB_DONE|GROUP_CHECK|Error|Traceback|rror:" | cut -c1-400 ; }
run hero_A_sun8   --apply-stage real --camera photo --size 960x640 --samples 96 --require-gpu
run hero_B_sun10  --apply-stage real --camera photo --size 960x640 --samples 96 --require-gpu --stage-opts '{"sun_energy": 10, "fill_energy": 3000}'
run hero_C_sun12  --apply-stage real --camera photo --size 960x640 --samples 96 --require-gpu --stage-opts '{"sun_energy": 12, "fill_energy": 2600}'
run groups_B      --apply-stage real --camera photo --size 960x640 --samples 64 --no-denoise --check-groups --require-gpu --stage-opts '{"sun_energy": 10, "fill_energy": 3000}'
run ver_B         --apply-stage real --camera veranda --size 960x640 --samples 96 --require-gpu --stage-opts '{"sun_energy": 10, "fill_energy": 3000}'
run hero_evening  --apply-stage real --evening --camera photo --size 960x640 --samples 96 --require-gpu
ls $O
