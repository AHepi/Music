#!/bin/bash
# What this does (plain words): bakes one gravel description in Blender (1254 dots unless a size is given) and scores the result with both comparison tools.
# Use: ./run_bake_and_score.sh NAME [SIZE]      (looks for description/NAME.json, writes outputs/NAME and scores/NAME_*)
cd "$(dirname "$0")"
NAME=$1; SIZE=${2:-1254}
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$BL -b --disable-autoexec -t 2 --python generator/gravel_generator.py -- description/$NAME.json outputs/$NAME --size $SIZE > scores/run_$NAME.log 2>&1
grep "^\[bake\]" scores/run_$NAME.log
if [ "$SIZE" = "1254" ]; then python3 -I analysis/score_folder.py outputs/$NAME $NAME | python3 -I -c "
import json,sys
d=json.loads(sys.stdin.read().strip().split('\n')[-1]); p=d['pixel']
print('$NAME', 'tier', p.get('tier_reached'), 'ssim', round(p['colour_ssim'],3), 'dE', round(p['colour_mean_delta_e'],2), 'edge', round(p['edge_skill_2px'],3), 'h_mae_fit', round(p['height_mae_best_fit_levels'],1), 'normal_deg', round(p['normal_mean_angle_degrees'],1), 'texture', round(d['texture_as_baked']['overall'],3), 'texture_view', round(d['texture_view']['overall'],3), 'seam', d['seam_ratio'])
"; fi
