# What this does (plain words): gives a few summary numbers of one or more colour pictures, measured exactly the way measure_reference_once.py
# measured the reference (share of dots that are earth, stone or water by nearest of the 16 stored mud palette colours; the average colour of each
# kind; the brightness percentiles of the earth), so that a tuning picture can be compared with the reference by number as well as by eye.
# Use: python3 -I look_numbers.py picture1.png [picture2.png ...]      (the reference itself is always printed first)
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
with open(os.path.join(PROC, 'recipes', 'mud', 'generator', 'fitted_distributions_mud.json')) as handle:
    stats = json.load(handle)['stats']
palette = np.array(stats['palette_rgb'], dtype=np.float64)
kinds = np.array(stats['palette_kinds'])


def numbers(path):
    colour = cv2.imread(path)[..., ::-1].astype(np.float64)
    grey = 0.299 * colour[..., 0] + 0.587 * colour[..., 1] + 0.114 * colour[..., 2]
    label = (((colour[:, :, None, :] - palette[None, None, :, :]) ** 2).sum(axis=-1)).argmin(axis=-1)
    kind = kinds[label]
    out = {k: round(float((kind == k).mean()), 3) for k in ('earth', 'stone', 'water')}
    out['water rgb'] = [round(float(c)) for c in colour[kind == 'water'].mean(axis=0)] if (kind == 'water').any() else None
    out['stone rgb'] = [round(float(c)) for c in colour[kind == 'stone'].mean(axis=0)] if (kind == 'stone').any() else None
    out['earth rgb'] = [round(float(c)) for c in colour[kind == 'earth'].mean(axis=0)]
    out['earth brightness 5/25/50/75/95'] = [round(float(np.percentile(grey[kind == 'earth'], p))) for p in (5, 25, 50, 75, 95)]
    out['mean brightness'] = round(float(grey.mean()), 1)
    return out


print('reference', numbers(os.path.join(PROC, 'reference', 'mud', 'colour.png')))
for path in sys.argv[1:]:
    print(os.path.relpath(path, HERE), numbers(path))
