#!/bin/bash
B=/workspace/blender/blender
W=proc-work/skills_test/22b
T=proc-work/street_wet/tools
export PYTHONDONTWRITEBYTECODE=1
cd $W
mkdir -p out/r4
{
$B -b --disable-autoexec $W/street_copy/door_curv2.blend --python $T/22_render_eevee.py -- $W/out/r4 main today 540 960 64 tag=_curv2_eevee 2>&1 | grep -E "DRAWN|Error|Traceback"
$B -b --disable-autoexec $W/street_copy/door_baked_512.blend --python $W/34_render_with_light.py -- 100 $W/out/r4 main today 540 960 64 tag=_baked512_sharp30_eevee 2>&1 | grep -E "DRAWN|Error|Traceback"
$B -b --disable-autoexec $W/street_copy/door_addwear.blend --python $W/35_layers_mute.py -- $W/out/r4 2>&1 | grep -E "LAYERS|Error|Traceback"
} > $W/out/r4/log.txt 2>&1
cat $W/out/r4/log.txt
