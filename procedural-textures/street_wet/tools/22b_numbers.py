# What this does (plain Python, no Blender): the numbers table for a set of MAIN-camera pictures (540 x 960) drawn by tools/22_render_eevee.py or 05_render_views.py.
# For each kind of surface (found with the material-number picture of the same camera, work/r04/main_id.png) and each picture: average brightness as shown (0..1 of the
# finished 8-bit picture, not light energy), the ratio to the "today" picture and to the "dry" picture, the share of nearly black dots under 0.06 ("black holes"), the share of
# nearly white dots over 0.97 (clipped), and the grain (average difference between a dot and the average of its four neighbours: higher = more speckle). Road grain is given for
# the left, middle and right thirds of the road separately (the checker's aim: under 0.008 everywhere).
# Run: python3 -I tools/22b_numbers.py FOLDER STATE [STATE ...]        e.g.  python3 -I tools/22b_numbers.py work/r25 today dry wet heavy
# reads FOLDER/main_<state>.png, writes FOLDER/numbers.json
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from importlib import import_module  # noqa: E402

grain_tool = import_module('21b_grain_numbers')
ROOT = grain_tool.ROOT
id_map, ids = grain_tool.id_map, grain_tool.ids
SURFACES = {'road setts': 'street_setts', 'pavement flags': 'pavement_flags', 'kerb + gutter': 'kerb+gutter', 'cottage walls': 'walls'}
EXTRA = {'dressed stone': ['dressed_stone', 'dark_dressed_stone'], 'roofs': ['roof_slate'], 'colliery brick': ['colliery_brick']}


def luma(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float) / 255
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


folder, states = sys.argv[1], sys.argv[2:]
pictures = {s: luma(f'{folder}/main_{s}.png') for s in states}
result = {}
rows = dict((k, np.isin(id_map, [ids[n] for n in grain_tool.GROUPS[v]])) for k, v in SURFACES.items())
for label, names in EXTRA.items():
    rows[label] = np.isin(id_map, [ids[n] for n in names])
print(f"{'surface':16s} {'state':7s} {'bright':>7s} {'/today':>7s} {'/dry':>6s} {'black':>6s} {'white':>6s} {'grain':>7s}")
for label, mask in rows.items():
    result[label] = {}
    base = {s: float(pictures[s][mask].mean()) for s in states}
    for state in states:
        p = pictures[state]
        row = dict(brightness=round(base[state], 3), black=round(float((p[mask] < 0.06).mean()), 3), white=round(float((p[mask] > 0.97).mean()), 4))
        if 'today' in base:
            row['over_today'] = round(base[state] / base['today'], 2)
        if 'dry' in base:
            row['over_dry'] = round(base[state] / base['dry'], 2)
        blur = (np.roll(p, 1, 0) + np.roll(p, -1, 0) + np.roll(p, 1, 1) + np.roll(p, -1, 1)) / 4
        inner = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
        row['grain'] = round(float(np.abs(p - blur)[inner].mean()), 4)
        if label in ('road setts', 'pavement flags'):
            for part in ('left', 'middle', 'right'):
                m = grain_tool.part_mask(mask, part)
                i2 = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
                row[f'grain_{part}'] = round(float(np.abs(p - blur)[i2].mean()), 4) if i2.sum() > 50 else None
        result[label][state] = row
        print(f"{label:16s} {state:7s} {row['brightness']:7.3f} {row.get('over_today', float('nan')):7.2f} {row.get('over_dry', float('nan')):6.2f} {row['black'] * 100:5.1f}% {row['white'] * 100:5.2f}% {row['grain']:7.4f}"
              + (f"   thirds L/M/R {row['grain_left']}/{row['grain_middle']}/{row['grain_right']}" if 'grain_left' in row else ''))
json.dump(result, open(f'{folder}/numbers.json', 'w'), indent=1)
