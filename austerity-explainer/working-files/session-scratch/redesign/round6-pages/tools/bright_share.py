"""What this does: measures on filmed stills where the brightest parts of the picture are: the brightest 3% of the
pixels below the words (from 0.25 down) are found, and the share of them inside the subject's box (the gate and the
people at it, or the doorway) is printed, with the subject box's average brightness against the whole frame's, and
the bottom 30% of the frame's, so "the subject is the brightest thing" can be judged on the film itself.
Use: python3 -I bright_share.py STILL x0 y0 x1 y1 [NAME]   (the subject box in shares of the frame)
"""
import sys

import numpy as np
from PIL import Image

path = sys.argv[1]
x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
name = sys.argv[6] if len(sys.argv) > 6 else path
a = np.asarray(Image.open(path).convert('L')).astype(float)
H, W = a.shape
below = a[int(0.25 * H):]
limit = np.percentile(below, 97)
mask = np.zeros_like(a, bool)
mask[int(0.25 * H):] = a[int(0.25 * H):] >= limit
box = np.zeros_like(a, bool)
box[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = True
inside = (mask & box).sum() / mask.sum()
# where the rest of the brightest pixels are, by a 4 x 4 grid of the frame below the words
ys, xs = np.nonzero(mask & ~box)
grid = np.zeros((4, 4), int)
for y, x in zip(ys, xs):
    grid[min(3, int((y / H - 0.25) / 0.75 * 4)), min(3, int(x / W * 4))] += 1
print(f'{name}: brightest 3% (at or above {limit:.0f}) inside the subject box {100 * inside:.0f}%; subject box average '
      f'{a[box].mean():.0f}, whole frame {a.mean():.0f} (box {a[box].mean() / a.mean():.2f} times), bottom 30% {a[int(0.7 * H):].mean():.0f}')
print('  the rest of the brightest pixels, rows from 0.25 down in quarters, columns in quarters:')
for row in grid: print('   ', ' '.join(f'{v:6d}' for v in row))
