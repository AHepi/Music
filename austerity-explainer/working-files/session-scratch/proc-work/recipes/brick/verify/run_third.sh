#!/bin/bash
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/brick
V=$R/verify
B=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
for s in 13 16 12; do
  $BL -b --disable-autoexec -t 2 --python $R/generator/brick_generator.py -- $R/variations/description_$s.json $V/var${s}_again --size 1254 --samples 8 > $V/var${s}_again.log 2>&1
  (cd $B; python3 -I lib/texture_compare.py brick recipes/brick/verify/var${s}_again --json recipes/brick/verify/var${s}_again_texture.json >/dev/null 2>&1; python3 -I lib/pixel_compare.py brick recipes/brick/verify/var${s}_again --json recipes/brick/verify/var${s}_again_pixel.json >/dev/null 2>&1)
done
echo done > $V/third_done.flag
