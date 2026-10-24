#!/bin/bash
# verifier: scores one verify/out/NAME folder with the two lib tools (as baked) and prints a one-line summary
P=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work
V=$P/recipes/slate/verify
n=$1; src=${2:-$V/out/$n}
mkdir -p $V/scores
python3 -I $P/lib/pixel_compare.py slate $src --json $V/scores/${n}_pixel.json --sheet $V/scores/${n}_diff.png > /dev/null 2>&1
python3 -I $P/lib/texture_compare.py slate $src --json $V/scores/${n}_texture.json --sheet $V/scores/${n}_sheet.png > /dev/null 2>&1
python3 -I - <<PY
import json
n='$n'; V='$V'
p=json.load(open(f'{V}/scores/{n}_pixel.json')); t=json.load(open(f'{V}/scores/{n}_texture.json'))
print(f"{n:18s} tier={p['tier_reached']:6s} ssim={p['colour_ssim']:.4f} dE={p['colour_mean_delta_e']:.2f} edge={p['edge_skill_2px']:.3f} hmae={p['height_mae_best_fit_levels']:.2f} nrm={p['normal_mean_angle_degrees']:.2f} tex={t['overall']:.3f}")
PY
