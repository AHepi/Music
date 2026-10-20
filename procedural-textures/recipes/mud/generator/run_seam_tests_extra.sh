#!/bin/bash
# What this does (plain words): the half-tile SEAM test for the reference-fitted descriptions (the traced L class and the M class): bakes each slid by half a tile in both directions and
# compares it with the first bake rolled by half a tile (a perfectly periodic recipe differs only at shape edges). Writes scores/seam_tests_extra.json. Use after the ladder is baked.
cd "$(dirname "$0")/.."
while ! grep -q CHAIN_DONE scores/chain.log 2>/dev/null; do sleep 20; done
for name in M_puddle_tones_stone_faces L_final_traced_ground_plus_corrections; do
  /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python generator/mud_generator.py -- description/$name.json outputs/shift_$name --size 1254 --samples 8 --shift 0.5 0.5 > scores/shift_$name.log 2>&1
done
python3 -I - <<'PY'
import json, cv2, numpy as np
out = {}
for name in ('M_puddle_tones_stone_faces', 'L_final_traced_ground_plus_corrections'):
    a = cv2.imread(f'outputs/{name}/colour.png').astype(float); b = cv2.imread(f'outputs/shift_{name}/colour.png').astype(float)
    d = np.abs(np.roll(a, (627, 627), axis=(0, 1)) - b).mean(axis=-1)
    out[name] = {'mean_abs_difference': round(float(d.mean()), 3), 'share_differing_by_more_than_8_levels': round(float((d > 8).mean()), 5)}
json.dump(out, open('scores/seam_tests_extra.json', 'w'), indent=1); print(out)
PY
rm -rf outputs/shift_*
echo SEAM_EXTRA_DONE
