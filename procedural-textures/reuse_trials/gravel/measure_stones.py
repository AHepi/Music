# What this does (plain words): measures how the stones of a picture are shared out, to compare with what was measured once on the gravel
# reference (recipes/gravel/scores/measurements.json: stone share, and "what survives opening with a disc" at several radii). It takes the grey
# picture of the layout's stone mask (a 'bundle.piece_mask' view; white = stone), and prints the stone share and the share left after
# erasing everything a disc of the given radius cannot fit inside (radii are those of the 1254-dot reference, scaled to the picture size).
# The reference numbers are only a GUIDE for hand tuning: nothing is optimised against them.
# Use: python3 -I measure_stones.py MASK.png [more masks ...]
import json
import os
import sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
with open(os.path.join(PROC, 'recipes', 'gravel', 'scores', 'measurements.json')) as handle:
    reference = json.load(handle)
radii = reference['granulometry_radii']
reference_curve = reference['granulometry']['stone']
want = [r for r in (8, 16, 24, 32, 48)]
print('reference stone share %.3f; left after opening at radius (1254 dots) %s' % (
    reference['stone_share'], ', '.join('%d: %.3f' % (r, reference_curve[radii.index(r)]) for r in want)))
for path in sys.argv[1:]:
    mask = cv2.imread(path, 0) > 127
    size = mask.shape[0]
    scale = size / 1254.0
    row = ['%s  size %d  stone share %.3f' % (os.path.basename(path), size, mask.mean())]
    for r in want:
        pixels = max(1, int(round(r * scale)))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pixels + 1, 2 * pixels + 1))
        padded = np.pad(mask.astype(np.uint8), pixels, mode='wrap')
        opened = cv2.morphologyEx(padded, cv2.MORPH_OPEN, kernel)[pixels:-pixels, pixels:-pixels]
        row.append('%d: %.3f' % (r, opened.mean()))
    print('  '.join(row))
