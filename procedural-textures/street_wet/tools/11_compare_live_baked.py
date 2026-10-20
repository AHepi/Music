# What this does (plain Python, no Blender): compares the LIVE wet picture (Blender working the WETNESS layer out at every dot, work/r07/main_wet.png) with the BAKED one (the same camera
# and lights, but the street wearing only the baked maps and flat numbers that went into the .glb, work/r10/main_baked.png). For each kind of surface: how bright the baked one is as a share
# of the live one, the average difference (0..1 scale of the finished 8-bit pictures) and the correlation (1 = the same pattern). Run: python3 -I tools/11_compare_live_baked.py
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ids = json.load(open(f'{ROOT}/work/r04/material_ids.json'))
id_map = np.asarray(Image.open(f'{ROOT}/work/r04/main_id.png').convert('RGB'))[..., 0].astype(int)
live = np.asarray(Image.open(f'{ROOT}/work/r07/main_wet.png').convert('RGB')).astype(float) / 255
baked = np.asarray(Image.open(f'{ROOT}/work/r10/main_baked.png').convert('RGB')).astype(float) / 255
dry = np.asarray(Image.open(f'{ROOT}/work/r07/main_dry.png').convert('RGB')).astype(float) / 255
GROUPS = {'road setts': ['street_setts'], 'pavement flags': ['pavement_flags'], 'kerb + gutter stones': ['kerb_stone', 'channel_stones'],
          'cottage walls': ['cottage_brick_door_left', 'cottage_brick_door_right', 'cottage_stone_door_left', 'cottage_stone_door_right'],
          'dressed stone': ['dressed_stone', 'dark_dressed_stone'], 'roofs': ['roof_slate'], 'colliery brick': ['colliery_brick']}
luma = lambda p: 0.2126 * p[..., 0] + 0.7152 * p[..., 1] + 0.0722 * p[..., 2]  # noqa: E731
L, B, D = luma(live), luma(baked), luma(dry)
result = {}
print(f"{'surface':22s} {'dots':>7s} {'live':>6s} {'baked':>6s} {'baked/live':>10s} {'mean diff':>9s} {'correlation':>11s} | dry-vs-live correlation (for comparison)")
for label, names in GROUPS.items():
    mask = np.isin(id_map, [ids[n] for n in names])
    if mask.sum() < 50:
        continue
    l, b, d = L[mask], B[mask], D[mask]
    row = {'dots': int(mask.sum()), 'live': round(float(l.mean()), 3), 'baked': round(float(b.mean()), 3), 'baked_over_live': round(float(b.mean() / l.mean()), 2),
           'mean_abs_difference': round(float(np.abs(l - b).mean()), 3), 'correlation': round(float(np.corrcoef(l, b)[0, 1]), 3), 'dry_vs_live_correlation': round(float(np.corrcoef(l, d)[0, 1]), 3)}
    result[label] = row
    print(f"{label:22s} {row['dots']:7d} {row['live']:6.3f} {row['baked']:6.3f} {row['baked_over_live']:10.2f} {row['mean_abs_difference']:9.3f} {row['correlation']:11.3f} | {row['dry_vs_live_correlation']:.3f}")
json.dump(result, open(f'{ROOT}/work/r10/live_vs_baked.json', 'w'), indent=1)
