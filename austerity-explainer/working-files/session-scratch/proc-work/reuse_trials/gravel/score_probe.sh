#!/bin/bash
# What this does (plain words): scores one tuning picture pair at the like-for-like size. Takes the folder and the file stem of a probe made by
# run_views.py at 1254 dots (STEM_colour.png and STEM_height.png), makes the normal map from the height at strength 10, and prints the same-kind
# score (overall and the groups) and the weakest measures. Use: bash score_probe.sh FOLDER STEM
F=$1; S=$2; D=$F/${S}_set
mkdir -p $D
cp $F/${S}_colour.png $D/colour.png; cp $F/${S}_height.png $D/height.png
python3 -I /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate_layers/integration/make_normal.py $D/height.png $D/normal.png 10
python3 -I /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/lib/texture_compare.py gravel $D --json $D/score.json > /dev/null
python3 -I - <<PY
import json
r=json.load(open('$D/score.json'))
print('overall', r['overall'], r['groups'])
print({k:round(v,3) for k,v in r['scores'].items()})
PY
