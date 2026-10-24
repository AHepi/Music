#!/bin/bash
# What this does (plain words): third batch (after fixing two things found on the way: the real-geometry slabs grew downward instead of upward, and the cobblestone
# test needed the sampler's accent colours written explicitly in the model instead of guessed): re-bakes the geometry-height comparison, the cobblestone transfer
# test, the 8 variation tiles and the area picture with the final sampler.
B=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
R=$B/recipes/brick
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $R
until [ -f extras2_done.flag ]; do sleep 5; done
for mode in hybrid geometry; do
  $BL -b --disable-autoexec -t 2 --python generator/brick_generator.py -- generator/descriptions/M_blobs.json outputs/M_height_$mode --size 1254 --samples 8 --height-mode $mode 2>&1 | grep -E "^\[bake\]"
  (cd $B; python3 -I lib/pixel_compare.py brick recipes/brick/outputs/M_height_$mode --json recipes/brick/scores/M_height_${mode}_pixel.json > /dev/null; python3 -I lib/texture_compare.py brick recipes/brick/outputs/M_height_$mode --json recipes/brick/scores/M_height_${mode}_texture.json > /dev/null)
done
python3 -I transfer/run_transfer.py > transfer/run.log 2>&1
rm -rf variations/tile_* variations/description_* area/picture area/middle
python3 -I generator/run_variations.py 11 8 0.14 > variations/run.log 2>&1
python3 -I generator/run_area.py 101 0.14 > area/run_area.log 2>&1
echo extras3_done > extras3_done.flag
