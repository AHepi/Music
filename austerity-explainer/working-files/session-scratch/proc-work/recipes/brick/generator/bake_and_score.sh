#!/bin/bash
# What this does (plain words): bakes one description in Blender, then scores the result with both comparison tools.
# Use: bake_and_score.sh DESCRIPTION.json NAME [SIZE] [SAMPLES]      -> outputs/NAME, scores/NAME_pixel.json, scores/NAME_texture.json, scores/NAME_diff.png
B=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
R=$B/recipes/brick
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$BL -b --disable-autoexec -t 2 --python $R/generator/brick_generator.py -- "$1" $R/outputs/$2 --size ${3:-1254} --samples ${4:-8} 2>&1 | grep -E "^\[bake\]|Error|Traceback"
cd $B
python3 -I lib/pixel_compare.py brick recipes/brick/outputs/$2 --json recipes/brick/scores/$2_pixel.json --sheet recipes/brick/scores/$2_diff.png | grep -E "colour_ssim|delta_e\"|edge_skill|best_fit_levels|normal_mean_angle|tier_reached" | tr -d '\n '; echo
python3 -I lib/texture_compare.py brick recipes/brick/outputs/$2 --json recipes/brick/scores/$2_texture.json --sheet recipes/brick/scores/$2_texsheet.png > /dev/null 2>&1
python3 -I -c "
import json; d=json.load(open('recipes/brick/scores/$2_texture.json')); print('texture overall', d.get('overall'), {k:v for k,v in d.items() if isinstance(v,(int,float))})" 2>&1 | head -3
