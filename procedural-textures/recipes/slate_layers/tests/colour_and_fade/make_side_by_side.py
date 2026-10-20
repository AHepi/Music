# What this file does (plain words): puts a crop of the reference picture and the same-sized crop of one of our pictures side by side
# (reference on the left), for looking at paint character. It is only for looking: nothing is measured or fitted from it.
# Use (plain python): python3 -I make_side_by_side.py OURS.png OUT.png [x y width height] [zoom]
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'reference', 'slate', 'colour.png'))
ours = cv2.imread(sys.argv[1])
out = sys.argv[2]
x, y, w, h = (int(v) for v in sys.argv[3:7]) if len(sys.argv) >= 7 else (0, 80, 700, 480)
zoom = float(sys.argv[7]) if len(sys.argv) >= 8 else 1.0
ref = cv2.imread(REFERENCE)
if ours.shape[0] != ref.shape[0]:
    ours = cv2.resize(ours, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_CUBIC)
a, b = ref[y:y + h, x:x + w], ours[y:y + h, x:x + w]
if zoom != 1.0:
    a = cv2.resize(a, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_NEAREST)
    b = cv2.resize(b, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_NEAREST)
gap = np.full((a.shape[0], 8, 3), 255, np.uint8)
cv2.imwrite(out, np.hstack([a, gap, b]))
print(out)
