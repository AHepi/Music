#!/bin/bash
# What this does: on the rented machine, draws the street with the litter in EEVEE using the street's own tool (22_render_eevee.py), state "today" only
# (the street as it is, no wetness layer): the film's main camera, then low and 3/4 cameras on the gutter, shipped and heavier litter settings.
W=proc-work/skills_test/22d
cd $W
B=/workspace/blender/blender
mkdir -p out/render
for v in "$@"; do
  $B -b --disable-autoexec --factory-startup set_copy/street_litter_$v.blend --python tools/22_render_eevee.py -- out/render main today ${SIZE:-540 960} 64 tag=_$v 2>&1 | grep -E "DRAWN|Error|Traceback|GPU BACKEND"
done
ls -la out/render
