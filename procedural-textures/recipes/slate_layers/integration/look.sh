#!/bin/bash
# What this does (plain words): bakes only the COLOUR picture of the whole slate recipe for several settings variations in one go,
# quickly (default 640 dots), so that a person can look at them. Each variation is a name and a JSON of settings.
# Use: look.sh FOLDER_NAME SIZE 'JSON {"name": {"layer.setting": value, ...}, ...}' [Colour,Height]
# The pictures go to integration/looks/FOLDER_NAME/<name>_colour.png
SL=proc-work/recipes/slate_layers
mkdir -p $SL/integration/looks/$1
exec /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python $SL/tests/bake_tools.py -- $SL/recipe/slate_recipe.py $SL/integration/looks/$1 $2 4 "$3" '{}' "${4:-Colour}" > $SL/integration/looks/$1/log.txt 2>&1
