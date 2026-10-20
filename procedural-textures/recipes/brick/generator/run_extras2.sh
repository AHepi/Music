#!/bin/bash
# What this does (plain words): second batch after run_extras.sh: the three final classes baked once more as outputs/final_S, final_M, final_L (grain 0, 16 samples)
# with both comparison tools, two more patch-list sizes (ellipses at 200 and 376 KB), and the Geometry Nodes version of the patch layer for the route comparison.
B=proc-work
R=$B/recipes/brick
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $R
until [ -f extras_done.flag ]; do sleep 5; done
for c in S M L; do
  bash generator/bake_and_score.sh generator/descriptions/description_$c.json final_$c 1254 16 > scores/final_${c}_log.txt 2>&1
done
for n in Mb200_blobs Lb_blobs; do
  bash generator/bake_and_score.sh generator/descriptions/$n.json $n 1254 8 > scores/${n}_log.txt 2>&1
done
$BL -b --disable-autoexec -t 2 --python generator/gn_blobs_route.py -- generator/descriptions/M_blobs.json outputs/gn_route 1254 > scores/gn_route_log.txt 2>&1
(cd $B; python3 -I lib/pixel_compare.py brick recipes/brick/outputs/gn_route --json recipes/brick/scores/gn_route_pixel.json --sheet recipes/brick/scores/gn_route_diff.png > /dev/null 2>&1)
echo extras2_done > extras2_done.flag
