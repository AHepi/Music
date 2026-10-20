#!/bin/bash
# What this does (plain words): bakes pictures of the COLOUR AND FADE layer alone (LAYOUT + this layer + dark joints; see layer_only_recipe.py)
# at a small size, quickly, for looking. Several views (each with its own settings) in one Blender run.
# Use: dev.sh OUT_NAME SIZE 'JSON {view name: {settings...}}' ['JSON settings used by every view'] [Colour,Height]
HERE="$(cd "$(dirname "$0")" && pwd)"
"$HERE/../blender.sh" "$HERE/../bake_tools.py" -- "$HERE/layer_only_recipe.py" "$HERE/dev/$1" "$2" 4 "$3" "${4:-{\}}" "${5:-Colour}" 2>&1 | grep -E "Saved|Error|Traceback|File |Exception" 
