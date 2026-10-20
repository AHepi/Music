# What this does (plain words): compares the pictures the independent checker re-baked (verify/rebake/SURFACE/colour.png, height.png) with the
# trial's stored final/seeds_1 pictures, dot by dot, and prints how many dots differ and by how much (0 differences = the stored picture is exactly
# what the recipe makes). Colour is out of 255; height is shown out of 255 too (the 16 bit height divided by 257).
# Use: python3 -I rebake_compare.py SURFACE [SURFACE ...]
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
results = {}
for surface in sys.argv[1:]:
    row = {}
    for name in ('colour', 'height'):
        new_path = os.path.join(HERE, 'rebake', surface, name + '.png')
        old_path = os.path.join(PROC, 'reuse_trials', surface, 'final', 'seeds_1', name + '.png')
        if not os.path.exists(new_path):
            continue
        new, old = cv2.imread(new_path, cv2.IMREAD_UNCHANGED), cv2.imread(old_path, cv2.IMREAD_UNCHANGED)
        scale = 257.0 if new.dtype == np.uint16 else 1.0
        difference = np.abs(new.astype(np.float64) - old.astype(np.float64)) / scale
        row[name] = {'same_size': bool(new.shape == old.shape), 'dots_that_differ_percent': round(float((difference.max(axis=-1) if difference.ndim == 3 else difference).__gt__(0.0).mean() * 100), 4),
                     'mean_difference_of_255': round(float(difference.mean()), 4), 'largest_difference_of_255': round(float(difference.max()), 2)}
    results[surface] = row
    print(surface, json.dumps(row))
with open(os.path.join(HERE, 'rebake_compare_results.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
