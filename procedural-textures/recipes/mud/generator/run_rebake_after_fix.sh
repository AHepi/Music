#!/bin/bash
# What this does (plain words): re-bakes the ladder rows that contain ruts and clods (R3, S, M) with the FINAL generator code (the rut ends now fade out), re-bakes the 2508 area with the
# distance grid that scales with the tile, and repeats the half-tile seam test on M and L so that every number comes from one version of the code.
cd "$(dirname "$0")/.."
generator/bake_score_rows.sh description outputs analysis/score_folder.py R3_plus_ruts S_layout_ruts_clods M_puddle_tones_stone_faces > scores/rebake_rows.log 2>&1
rm -rf area/area_2508 area/quadrant_*
python3 -I - <<'PY'
import sys, json
sys.path.insert(0, 'generator')
import sampler
json.dump(sampler.sample_description(201, tile=2508), open('area/description_area_2508.json', 'w'), separators=(',', ':'))
PY
generator/bake_one.sh area/description_area_2508.json area/area_2508 2508 8 > area/bake.log 2>&1
python3 -I analysis/scale_report.py > scores/scale_report.log 2>&1
echo CHAIN_DONE > scores/chain_after.log
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
echo REBAKE_DONE
