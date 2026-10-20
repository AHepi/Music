# What this does (plain Python, no Blender): reads the pictures made by 04_colour_ratios.py and prints, for every material, the wet colour as a share of the dry colour.
# Run: python3 -I tools/04b_colour_ratios.py work/r04
import json
import sys

import numpy as np
from PIL import Image

folder = sys.argv[1]
ids = json.load(open(f'{folder}/material_ids.json'))
result = {}
for camera in ('main', 'wall_lamp'):
    id_map = np.asarray(Image.open(f'{folder}/{camera}_id.png').convert('RGB'))[..., 0].astype(int)
    pics = {k: np.asarray(Image.open(f'{folder}/{camera}_colour_{k}.png')).astype(float) / 65535.0 for k in ('dry', 'wet', 'heavy')}
    for name, index in ids.items():
        mask = id_map == index
        if mask.sum() < 40:
            continue
        dry = pics['dry'][mask].mean()
        result.setdefault(name, {})[camera] = {'pixels': int(mask.sum()), 'dry': round(float(dry), 4), 'wet_ratio': round(float(pics['wet'][mask].mean() / dry), 3),
                                               'heavy_ratio': round(float(pics['heavy'][mask].mean() / dry), 3)}
print(f"{'material':32s} {'camera':10s} {'pixels':>7s} {'dry':>7s} {'wet/dry':>8s} {'heavy/dry':>10s}")
for name, cams in sorted(result.items()):
    for camera, row in cams.items():
        print(f"{name:32s} {camera:10s} {row['pixels']:7d} {row['dry']:7.3f} {row['wet_ratio']:8.2f} {row['heavy_ratio']:10.2f}")
json.dump(result, open(f'{folder}/colour_ratios.json', 'w'), indent=1)
