#!/bin/bash
# Verifier script: bakes each claimed description in a fresh Blender process into verify/NAME (1254 dots).
G=proc-work/recipes/gravel
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
for NAME in S_v4 L_a100_s8 M_a600_s120 T_k24_a50 L_a250_s12 T_k24_a100 T_k24_a250 TS_k24_a300; do
  if [ ! -f $G/verify/$NAME/colour.png ]; then
    $BL -b --disable-autoexec -t 2 --python $G/generator/gravel_generator.py -- $G/description/$NAME.json $G/verify/$NAME --size 1254 > $G/verify/bake_$NAME.log 2>&1
  fi
done
touch $G/verify/bakes_done.flag
