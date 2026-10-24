#!/bin/bash
# What this does (plain words): after the machine restart, finishes the RESOLUTION test: bakes the default settings at 2508 dots (colour, height,
# roughness), writes how long it took next to the 512 and 1254 times measured before the restart, then compares the three sizes.
SL=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate_layers
B="/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py --"
cd $SL
START=$(date +%s.%N)
$B $SL/recipe/slate_recipe.py $SL/resolution/whole_recipe/at_2508 2508 4 '{"default": {}}' '{}' Colour,Height,Roughness > resolution/whole_recipe/bake_2508.log 2>&1
END=$(date +%s.%N)
python3 -I - "$START" "$END" <<'PY'
import json, os, sys
seconds = round(float(sys.argv[2]) - float(sys.argv[1]), 1)
times = {'512': {'seconds_for_colour_height_roughness': 34.6, 'load_average_after': 3.93, 'note': 'measured before the restart'},
         '1254': {'seconds_for_colour_height_roughness': 178.7, 'load_average_after': 4.04, 'note': 'measured before the restart'},
         '2508': {'seconds_for_colour_height_roughness': seconds, 'load_average_after': round(os.getloadavg()[0], 2), 'note': 'measured after the restart'}}
json.dump(times, open('resolution/whole_recipe/times.json', 'w'), indent=1)
print(times)
PY
python3 -I resolution/run_resolution.py analyse > resolution/whole_recipe/analyse.log 2>&1
echo done > integration/takeover/chain_d.done
