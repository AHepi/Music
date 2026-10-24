#!/bin/bash
# Sequential render-time tests (each uses all 4 processors, so never run two at once)
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/review-26/research-3d/blender-tests
cd $D
pgrep -f "Xvfb :97" >/dev/null || (Xvfb :97 -screen 0 1920x1080x24 >/dev/null 2>&1 &)
sleep 1
export DISPLAY=:97
run() { name=$1; shift; echo "### $name $(date +%H:%M:%S)" >> $D/matrix.log; NFRAMES=$NF timeout 1800 $B -b --factory-startup --python $D/render_anim.py -- "$@" 2>&1 | grep -E "RENDER_SECONDS|SETUP|MODEL_INFO|GPU|Error|error|KUWAHARA|Traceback|denoiser" >> $D/matrix.log; }
NF=3 run eevee16 EEVEE 16 $D/out/eevee16
NF=2 run eevee64 EEVEE 64 $D/out/eevee64
NF=2 run workbench WORKBENCH 8 $D/out/workbench
NF=2 run eevee16_rt EEVEE 16 $D/out/eevee16rt raytrace
NF=2 run eevee16_kuwahara EEVEE 16 $D/out/eevee16kw kuwahara
NF=2 run eevee16_fog EEVEE 16 $D/out/eevee16fog fog
NF=1 run eevee16_freestyle EEVEE 16 $D/out/eevee16fs freestyle
NF=1 run cycles32 CYCLES 32 $D/out/cycles32
NF=1 run cycles128 CYCLES 128 $D/out/cycles128
echo "### DONE $(date +%H:%M:%S)" >> $D/matrix.log
