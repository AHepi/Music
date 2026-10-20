#!/bin/bash
# verifier: score one bake folder with lib/pixel_compare.py and lib/texture_compare.py; $1 = folder, $2 = reference name (mud or mud_golden)
cd proc-work
export PYTHONDONTWRITEBYTECODE=1
V=$1; R=${2:-mud}
python3 -I lib/pixel_compare.py $R $V --json $V/pixel.json --sheet $V/diff.png > $V/pixel.out 2>&1
python3 -I lib/texture_compare.py $R $V --json $V/texture.json --sheet $V/sheet.png > $V/texture.out 2>&1
python3 -I recipes/mud/verify/summ.py $V
