#!/bin/bash
# What this does (plain words): scores a baked colour picture against the slate reference with the project's "same kind of surface" tool.
# Only the COLOUR group is meaningful (height and normal are borrowed from an older bake so the tool can run). Use: score_colour.sh PICTURE.png
PROC=proc-work
SL=$PROC/recipes/slate_layers/integration
D=$(mktemp -d $SL/scoretmp_XXXX)
cp "$1" $D/colour.png; cp $SL/bake_round1/height.png $SL/bake_round1/normal.png $D/
python3 -I $PROC/lib/texture_compare.py slate $D --json $D/score.json > /dev/null 2>&1
python3 -I - $D/score.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); print('colour group', d['groups']['colour'], {k:v for k,v in d['scores'].items() if k.startswith('colour')})
PY
rm -rf $D
