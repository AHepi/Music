# What this does (plain Python, no Blender): measures the four main pictures (A today, B new materials dry, C wet, D heavier rain). For each kind of surface (found with the material-number picture made by
# 04_colour_ratios.py for the same camera) it gives the average brightness of the dots of that surface in each picture (the pictures are the finished 8-bit pictures, so these are brightness as
# shown, 0 to 1, not light energy), the ratios wet / dry, the share of the surface that is nearly black ("black holes": brightness under 0.06) and a noise measure (average difference between a dot and its
# neighbours' average, a rough "how grainy"). Run: python3 -I tools/10_numbers.py
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ids = json.load(open(f'{ROOT}/work/r04/material_ids.json'))
id_map = np.asarray(Image.open(f'{ROOT}/work/r04/main_id.png').convert('RGB'))[..., 0].astype(int)
GROUPS = {'road setts': ['street_setts'], 'pavement flags': ['pavement_flags'], 'kerb + gutter stones': ['kerb_stone', 'channel_stones'],
          'cottage walls': ['cottage_brick_door_left', 'cottage_brick_door_right', 'cottage_stone_door_left', 'cottage_stone_door_right'],
          'dressed stone': ['dressed_stone', 'dark_dressed_stone'], 'roofs': ['roof_slate'], 'colliery brick': ['colliery_brick']}
pics = {k: np.asarray(Image.open(f'{ROOT}/work/r07/main_{k}.png').convert('RGB')).astype(float) / 255 for k in ('today', 'dry', 'wet', 'heavy')}
luma = {k: 0.2126 * p[..., 0] + 0.7152 * p[..., 1] + 0.0722 * p[..., 2] for k, p in pics.items()}


def noise(grey, mask):
    blur = (np.roll(grey, 1, 0) + np.roll(grey, -1, 0) + np.roll(grey, 1, 1) + np.roll(grey, -1, 1)) / 4
    inner = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    return float(np.abs(grey - blur)[inner].mean()) if inner.sum() else float('nan')


result = {}
print(f"{'surface':22s} {'dots':>7s} | brightness A / B / C / D           | C/B   D/B   B/A | black-hole share B / C / D  | noise A / B / C / D")
for label, names in GROUPS.items():
    mask = np.isin(id_map, [ids[n] for n in names])
    if mask.sum() < 50:
        continue
    mean = {k: float(luma[k][mask].mean()) for k in luma}
    dark = {k: float((luma[k][mask] < 0.06).mean()) for k in luma}
    grain = {k: noise(luma[k], mask) for k in luma}
    result[label] = {'dots': int(mask.sum()), 'brightness': {k: round(v, 3) for k, v in mean.items()}, 'wet_over_dry': round(mean['wet'] / mean['dry'], 2),
                     'heavy_over_dry': round(mean['heavy'] / mean['dry'], 2), 'dry_over_today': round(mean['dry'] / mean['today'], 2),
                     'black_hole_share': {k: round(v, 3) for k, v in dark.items()}, 'noise': {k: round(v, 4) for k, v in grain.items()}}
    print(f"{label:22s} {mask.sum():7d} | {mean['today']:.3f} {mean['dry']:.3f} {mean['wet']:.3f} {mean['heavy']:.3f} | {mean['wet'] / mean['dry']:.2f}  {mean['heavy'] / mean['dry']:.2f}  {mean['dry'] / mean['today']:.2f} | "
          f"{dark['dry']:.3f} {dark['wet']:.3f} {dark['heavy']:.3f} | {grain['today']:.4f} {grain['dry']:.4f} {grain['wet']:.4f} {grain['heavy']:.4f}")
whole = {k: float(luma[k].mean()) for k in luma}
print('whole picture mean brightness', {k: round(v, 3) for k, v in whole.items()})
result['whole picture'] = {k: round(v, 3) for k, v in whole.items()}
json.dump(result, open(f'{ROOT}/work/r07/main_numbers.json', 'w'), indent=1)
