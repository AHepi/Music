# What this does: rebuilds the harness's own (two-neighbour) normal map for a stored height picture, the same formula as lib/bake_harness.py sobel_normal,
# so that the two normal-map methods can be scored side by side without a Blender run. Use: python3 -I make_old_harness_normal.py HEIGHT.png OUT_NORMAL.png STRENGTH
import sys
import cv2
import numpy as np
h = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
h = (h[..., 0] if h.ndim == 3 else h).astype(np.float64) / 65535.0
s = float(sys.argv[3])
hx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
hy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2.0
nx, ny, nz = -s * hx, s * hy, np.ones_like(h)
L = np.sqrt(nx * nx + ny * ny + nz * nz)
n = np.stack([nx / L, ny / L, nz / L], axis=-1) * 0.5 + 0.5
cv2.imwrite(sys.argv[2], (np.clip(n, 0, 1) * 255).round().astype(np.uint8)[..., ::-1])
