#!/bin/bash
# RunPod round 4: final previews of the light stage alone (after the hill colour tweak), plus the chain (shapes + life + light) for a look at how they sit together.
B=/workspace/blender/blender
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad
S=$G/astra-work/out/courtyard_final.blend
D=$G/proc-work/garden/light
O=$D/out/rp/r4
mkdir -p $O
run() { name=$1; shift; echo "=== $name"; $B -b --disable-autoexec $S -P $D/render_job.py -- "$@" --out $O/$name 2>&1 | grep -E "RENDER_JOB_DONE|GROUP_CHECK|Error|Traceback|rror:" | cut -c1-300 ; }
chain() { name=$1; shift; echo "=== $name"; $B -b --disable-autoexec $S -P $D/chain_job.py -- "$@" --out $O/$name 2>&1 | grep -E "RENDER_JOB_DONE|Error|Traceback|rror:|\[life\] created|\[shapes\]" | cut -c1-300 ; }
run hero_real     --apply-stage real    --camera photo   --size 960x640 --samples 192 --require-gpu --exr
run hero_painted  --apply-stage painted --camera photo   --size 960x640 --samples 192 --require-gpu
run ver_real      --apply-stage real    --camera veranda --size 960x640 --samples 192 --require-gpu
run ver_painted   --apply-stage painted --camera veranda --size 960x640 --samples 192 --require-gpu
run evening_real  --apply-stage real --evening --camera photo --size 960x640 --samples 192 --require-gpu
run evening_painted --apply-stage painted --evening --camera photo --size 960x640 --samples 192 --require-gpu
run pano_real     --apply-stage real    --pano 3.5,-2.5,1.7 --size 2400x1000 --samples 64 --require-gpu
run pano_painted  --apply-stage painted --pano 3.5,-2.5,1.7 --size 2400x1000 --samples 64 --require-gpu
chain chain_hero_real    --apply-stage real    --camera photo   --size 960x640 --samples 192 --require-gpu
chain chain_hero_painted --apply-stage painted --camera photo   --size 960x640 --samples 192 --require-gpu
chain chain_ver_real     --apply-stage real    --camera veranda --size 960x640 --samples 192 --require-gpu
ls $O
