# What this does (plain words): compares the verifier's point-sampled half-tile bakes. 'shifted' must equal 'plain' rolled by half the picture in
# both directions. Reports the mean difference (steps of 255), the share of dots that differ at all and by more than 10 steps (of 255), and a
# CONTROL (the same comparison rolled 7 dots too far, which must differ a lot).
# Use: python3 -I analyse_half_tile.py FOLDER
import json
import os
import sys

import cv2
import numpy as np

folder = sys.argv[1]
names = ['colour', 'height'] + ['mask_' + n for n in ('colour_and_fade_mask', 'damage_mask', 'moss_mask', 'outline_and_shadow_mask', 'bundle_piece_id')]
results = {}
for name in names:
    a = cv2.imread(os.path.join(folder, f'plain_{name}.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    b = cv2.imread(os.path.join(folder, f'shifted_{name}.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    scale = 255.0 / (65535.0 if a.max() > 255 else 255.0)
    a, b = a * scale, b * scale
    if a.ndim == 3:
        a, b = a.max(axis=2) if name != 'colour' else a, b.max(axis=2) if name != 'colour' else b
    half = a.shape[0] // 2
    rolled = np.roll(np.roll(a, half, axis=0), half, axis=1)
    wrong = np.roll(np.roll(a, half + 7, axis=0), half + 7, axis=1)
    diff = np.abs(rolled - b)
    diff = diff.max(axis=2) if diff.ndim == 3 else diff
    control = np.abs(wrong - b)
    control = control.max(axis=2) if control.ndim == 3 else control
    results[name] = {'mean difference (of 255)': round(float(diff.mean()), 4), 'share differing at all (> 0.5 step) %': round(100 * float((diff > 0.5).mean()), 4),
                     'share > 10 steps %': round(100 * float((diff > 10).mean()), 4), 'largest': round(float(diff.max()), 2),
                     'control mean': round(float(control.mean()), 2), 'control share > 10 %': round(100 * float((control > 10).mean()), 2)}
    print(name, json.dumps(results[name]))
json.dump(results, open(os.path.join(folder, 'half_tile_point_results.json'), 'w'), indent=1)
