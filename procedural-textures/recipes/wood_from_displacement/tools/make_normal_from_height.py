# What this does (plain words): makes the NORMAL map (the picture that tells a game engine which way each dot of the surface faces) from the
# HEIGHT picture that the recipe baked, the way the uploaded wood normal map was made: the slope at a dot is the difference between the dot on its
# right and the dot on its left (and the same up and down), divided by 2, times a strength of 8. Checked on the uploaded wood maps: this rule on the
# uploaded height gives the uploaded normal to 0.004 on average (a 3 x 3 Sobel filter gives 0.03, strengths 6 and 10 are clearly worse; see the guide).
# The uploaded normal map itself is never read by the recipe. The picture wraps round its edges (for the default tile, so the normal map has no
# seam there). Output: OpenGL convention (green points UP the picture), 8-bit PNG. This is the same rule as the project's bake harness uses for
# its own normal.png (lib/bake_harness.py sobel_normal, which despite its name is this two-neighbour slope); it is repeated here so that this
# recipe's tools stand alone and so the strength and the 8-bit option can be chosen.
# Use: python3 -I make_normal_from_height.py HEIGHT16.png OUT_NORMAL.png [strength 8] [--eight-bit-first] [--no-wrap]
import sys

import cv2
import numpy as np


def normal_from_height(height, strength=8.0, wrap=True, eight_bit_first=False):
    """height: 16-bit or 8-bit picture (rows top to bottom). Returns an array (h, w, 3) of x, y, z of the normal (x right, y up the picture, z out)."""
    h = height.astype(np.float64) / (65535.0 if height.dtype == np.uint16 else 255.0)
    if eight_bit_first:
        h = np.round(h * 255.0) / 255.0
    pad = np.pad(h, 1, mode='wrap' if wrap else 'edge')
    hx = (pad[1:-1, 2:] - pad[1:-1, :-2]) / 2.0
    hy_down = (pad[2:, 1:-1] - pad[:-2, 1:-1]) / 2.0                      # per step DOWN the picture
    nx, ny, nz = -strength * hx, strength * hy_down, np.ones_like(h)      # up the picture = minus the downward slope
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def write_normal(height_path, out_path, strength=8.0, wrap=True, eight_bit_first=False):
    h = cv2.imread(height_path, cv2.IMREAD_UNCHANGED)
    h = h[..., 0] if h.ndim == 3 else h
    n = normal_from_height(h, strength, wrap, eight_bit_first)
    cv2.imwrite(out_path, ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    write_normal(args[0], args[1], float(args[2]) if len(args) > 2 else 8.0, wrap='--no-wrap' not in sys.argv, eight_bit_first='--eight-bit-first' in sys.argv)
