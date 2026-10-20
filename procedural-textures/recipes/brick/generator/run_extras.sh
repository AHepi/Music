#!/bin/bash
# What this does (plain words): the extra measurements after the main bake: (1) real-geometry height (slabs with rounded edges) against the colour-derived
# height, (2) the older shader-only brick recipe from the research folder baked and scored with the same tools (the honest comparison of routes),
# (3) the transfer test: three new cobblestone tiles from a second set of numbers, (4) the parameter-sweep pictures for the guide.
B=proc-work
R=$B/recipes/brick
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $R
# wait for the main job
until [ -s area/run_area.log ]; do sleep 5; done
# (1) geometry height routes on the M description (it has brick faces)
for mode in derived hybrid geometry; do
  $BL -b --disable-autoexec -t 2 --python generator/brick_generator.py -- generator/descriptions/M_blobs.json outputs/M_height_$mode --size 1254 --samples 8 --height-mode $mode 2>&1 | grep -E "^\[bake\]"
  (cd $B; python3 -I lib/pixel_compare.py brick recipes/brick/outputs/M_height_$mode --json recipes/brick/scores/M_height_${mode}_pixel.json > /dev/null; python3 -I lib/texture_compare.py brick recipes/brick/outputs/M_height_$mode --json recipes/brick/scores/M_height_${mode}_texture.json > /dev/null)
done
# (2) the shader-only recipe from the research folder through the shared harness
$BL -b --disable-autoexec -t 2 --python $B/lib/bake_harness.py -- $B/research/experiments_how_people_make_each_surface/recipes/recipe_brick.py outputs/shader_route --size 1254 --normal-reference brick 2>&1 | grep -E "^\[bake\]"
(cd $B; python3 -I lib/pixel_compare.py brick recipes/brick/outputs/shader_route --json recipes/brick/scores/shader_route_pixel.json > /dev/null; python3 -I lib/texture_compare.py brick recipes/brick/outputs/shader_route --json recipes/brick/scores/shader_route_texture.json > /dev/null)
# (3) transfer: cobbles
python3 -I transfer/run_transfer.py > transfer/run.log 2>&1
# (4) sweeps
python3 -I generator/make_sweeps.py > guide_pictures/sweeps_run.log 2>&1
echo extras_done > extras_done.flag
