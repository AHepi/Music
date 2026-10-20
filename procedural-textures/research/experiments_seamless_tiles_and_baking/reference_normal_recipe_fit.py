# What this does: finds out how each reference normal map was made from its (8-bit, as uploaded) height map. For each surface it tries two filters (central difference over 2 pixels,
# and the 3 x 3 Sobel kernel) with wrap-around, searches the strength that fits best, and prints the average error in 8-bit steps (0 = identical to the reference normal map).
# Run (plain Python):  python3 -I reference_normal_recipe_fit.py
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import normal_map_tools as nm  # noqa: E402

REF = os.path.join(HERE, '..', '..', 'reference')


def sobel3(height, strength):
    padded = np.pad(height, 1, mode='wrap')
    gx = cv2.Sobel(padded.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)[1:-1, 1:-1] / 8.0       # per-pixel slope (weights 1 2 1 / 2 normalisation)
    gy = cv2.Sobel(padded.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)[1:-1, 1:-1] / 8.0
    nx, ny, nz = -strength * gx, strength * gy, np.ones_like(gx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5


def best(filter_function, height, target):
    lows, highs = 0.5, 30.0
    for _ in range(30):
        a, b = lows + (highs - lows) / 3, highs - (highs - lows) / 3
        ea = np.abs(filter_function(height, a)[..., :2] - target[..., :2]).mean()
        eb = np.abs(filter_function(height, b)[..., :2] - target[..., :2]).mean()
        if ea < eb:
            highs = b
        else:
            lows = a
    s = (lows + highs) / 2
    return s, float(np.abs(filter_function(height, s) - target).mean() * 255)


print(f"{'surface':8s} {'central difference: strength, error':40s} {'3x3 Sobel: strength, error':40s}")
for name in ('brick', 'slate', 'wood', 'metal', 'mud', 'gravel'):
    target, _ = nm.load_unit_picture(os.path.join(REF, name, 'normal.png'))
    h8, _ = nm.load_unit_picture(os.path.join(REF, name, 'height_as_uploaded.png'))
    h8 = h8 if h8.ndim == 2 else h8[..., 0]
    sc, ec = best(nm.sobel_normal, h8, target)
    ss, es = best(sobel3, h8, target)
    print(f'{name:8s} strength {sc:6.3f}  error {ec:6.3f} 8-bit steps      strength {ss:6.3f}  error {es:6.3f} 8-bit steps')
