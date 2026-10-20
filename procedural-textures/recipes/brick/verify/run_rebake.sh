#!/bin/bash
# verifier: re-bake S, M, L, L+grain from the descriptions in fresh Blender processes; write only into verify/
B=proc-work
R=$B/recipes/brick
V=$R/verify
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $V
for pair in "S:description_S.json" "M:description_M.json" "L:description_L.json" "Lg14:L12_g0.14.json"; do
  name=${pair%%:*}; file=${pair#*:}
  $BL -b --disable-autoexec -t 2 --python $R/generator/brick_generator.py -- $R/generator/descriptions/$file $V/bake_$name --size 1254 --samples 16 > $V/bake_$name.log 2>&1
  (cd $B; python3 -I lib/pixel_compare.py brick recipes/brick/verify/bake_$name --json recipes/brick/verify/bake_${name}_pixel.json --sheet recipes/brick/verify/bake_${name}_diff.png > /dev/null 2>&1; python3 -I lib/texture_compare.py brick recipes/brick/verify/bake_$name --json recipes/brick/verify/bake_${name}_texture.json --sheet recipes/brick/verify/bake_${name}_texsheet.png > /dev/null 2>&1)
done
echo done > $V/rebake_done.flag
