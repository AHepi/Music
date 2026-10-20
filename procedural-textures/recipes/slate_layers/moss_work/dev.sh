#!/bin/bash
# What this does (plain words): bakes pictures of the MOSS layer alone (see moss_only_recipe.py) at a small size, for looking.
# Several views (each with its own settings) in one Blender run; the pictures land in moss_work/dev/OUT_NAME/VIEW_colour.png.
# Use: dev.sh OUT_NAME SIZE 'JSON {view name: {settings...}}' ['JSON settings used by every view'] [Colour,Height]
HERE="$(cd "$(dirname "$0")" && pwd)"
SL="$HERE/.."
"$SL/tests/blender.sh" "$SL/tests/bake_tools.py" -- "$HERE/moss_only_recipe.py" "$HERE/dev/$1" "$2" 4 "$3" "${4:-{\}}" "${5:-Colour}" 2>&1 | grep -E "Saved|Error|Traceback|File |Exception|error" 
