#!/bin/bash
# What this does (plain words): bakes the COLOUR AND FADE layer alone (layer-only recipe, colour only) at the real 1254 dots, then runs the
# project's "same kind of surface" scorer on it (lib/texture_compare.py; only the COLOUR group is meaningful: there is no normal or height
# map made from it here) and the paint statistics. Use: score_colour.sh NAME ['JSON settings'] -> dev/NAME/colour.png, score.json
HERE="$(cd "$(dirname "$0")" && pwd)"
PROC="$HERE/../../../.."
mkdir -p "$HERE/dev/$1"
"$HERE/../blender.sh" "$HERE/../bake_tools.py" -- "$HERE/layer_only_recipe.py" "$HERE/dev/$1/raw" 1254 4 '{"colour":{}}' "${2:-{\}}" Colour 2>&1 | grep -E "Error|Traceback"
cp "$HERE/dev/$1/raw/colour_colour.png" "$HERE/dev/$1/colour.png"
python3 -I "$PROC/lib/texture_compare.py" slate "$HERE/dev/$1" --json "$HERE/dev/$1/score.json" > /dev/null
python3 -I - "$HERE/dev/$1/score.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print('colour group', d['groups']['colour'], '| parts', {k: v for k, v in d['scores'].items() if k.startswith('colour')})
PY
python3 -I "$HERE/paint_stats.py" "$HERE/dev/$1/colour.png" | tail -9
