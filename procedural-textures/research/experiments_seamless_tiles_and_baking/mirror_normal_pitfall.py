# What this does: shows why a mirror-tiled NORMAL map must not just be a mirrored picture. A height picture is mirrored into a 2 x 2 block. Normal map A is made from the
# mirrored height (correct). Normal map B is the normal map of the original height with its picture mirrored the same way (naive). They differ because a mirrored slope
# changes direction: in the left-right mirrored copy the red channel must be inverted (and in the up-down mirrored copy the green channel).
# Run (plain Python):  python3 -I mirror_normal_pitfall.py
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import normal_map_tools as nm  # noqa: E402

height, _ = nm.load_unit_picture(os.path.join(HERE, 'out', 'normal', 'A_height_256.png'))
height = height if height.ndim == 2 else height[..., 0]
normal = nm.sobel_normal(height, 20.0)
top = np.hstack([height, height[:, ::-1]])
mirrored_height = np.vstack([top, top[::-1]])
correct = nm.sobel_normal(mirrored_height, 20.0)
topn = np.hstack([normal, normal[:, ::-1]])
naive = np.vstack([topn, topn[::-1]])
n = height.shape[0]
quarters = {'original (top left)': (slice(0, n), slice(0, n)), 'mirrored left-right (top right)': (slice(0, n), slice(n, 2 * n)),
            'mirrored up-down (bottom left)': (slice(n, 2 * n), slice(0, n)), 'mirrored both (bottom right)': (slice(n, 2 * n), slice(n, 2 * n))}
print('naive mirrored normal map versus the correct one, mean absolute difference per channel (red, green, blue):')
for name, (rows, cols) in quarters.items():
    difference = np.abs(naive[rows, cols] - correct[rows, cols]).mean(axis=(0, 1))
    print(f'  {name:36s} {difference.round(4)}')
