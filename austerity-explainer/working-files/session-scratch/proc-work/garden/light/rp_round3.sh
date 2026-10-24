#!/bin/bash
# RunPod round 3 (final previews of this stage): both looks, hero + veranda, evening (with lantern measurement EXR), 360-degree check, EEVEE proof, regrade source.
B=/workspace/blender/blender
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad
S=$G/astra-work/out/courtyard_final.blend
D=$G/proc-work/garden/light
O=$D/out/rp/r3
mkdir -p $O
run() { name=$1; shift; echo "=== $name"; $B -b --disable-autoexec $S -P $D/render_job.py -- "$@" --out $O/$name 2>&1 | grep -E "DEVICES|RENDER_JOB_DONE|GROUP_CHECK|Error|Traceback|rror:" | cut -c1-420 ; }
run hero_real     --apply-stage real    --camera photo   --size 960x640 --samples 128 --require-gpu --exr --check-groups
run hero_painted  --apply-stage painted --camera photo   --size 960x640 --samples 128 --require-gpu
run ver_real      --apply-stage real    --camera veranda --size 960x640 --samples 128 --require-gpu
run ver_painted   --apply-stage painted --camera veranda --size 960x640 --samples 128 --require-gpu
run evening_real  --apply-stage real --evening --camera photo --size 960x640 --samples 128 --no-denoise --exr --check-groups --require-gpu
run evening_painted --apply-stage painted --evening --camera photo --size 960x640 --samples 128 --require-gpu
run pano_real     --apply-stage real    --pano 3.5,-2.5,1.7 --size 2400x1000 --samples 64 --require-gpu
run pano_painted  --apply-stage painted --pano 3.5,-2.5,1.7 --size 2400x1000 --samples 64 --require-gpu
run eevee_real    --apply-stage real    --camera photo   --size 480x320 --samples 16 --engine BLENDER_EEVEE
ls $O
