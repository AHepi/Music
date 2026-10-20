# What this does (plain words): makes the NORMAL map (the picture that tells a game engine which way each dot of the surface faces) from the HEIGHT
# picture, the way the reference's own normal map was made: a 3 x 3 Sobel slope of the 8-bit height with whole-number strength 7 (slate), wrapping
# round the tile edges so the map tiles. (The harness's own normal uses a plain two-neighbour slope; this one matches the reference's way.)
# Output: OpenGL convention (green points UP the picture), 8-bit PNG.
# Use: python3 -I make_normal.py HEIGHT16.png OUT_NORMAL.png [strength 7]
import sys
import cv2
import numpy as np
def sobel_normal_from_height(height_16bit, strength=7.0, eight_bit_first=True):
    h = height_16bit.astype(np.float64) / 65535.0
    if eight_bit_first:
        h = np.round(h * 255.0) / 255.0                 # the reference height is an 8-bit picture; its normal was made from that
    pad = np.pad(h, 2, mode='wrap')
    hx = cv2.Sobel(pad, cv2.CV_64F, 1, 0, ksize=3)[2:-2, 2:-2] / 8.0
    hy = cv2.Sobel(pad, cv2.CV_64F, 0, 1, ksize=3)[2:-2, 2:-2] / 8.0      # per step DOWN the picture
    nx, ny, nz = -strength * hx, strength * hy, np.ones_like(h)           # up the picture = minus the downward slope
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)
if __name__ == '__main__':
    h = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
    h = h[..., 0] if h.ndim == 3 else h
    n = sobel_normal_from_height(h, float(sys.argv[3]) if len(sys.argv) > 3 else 7.0)
    cv2.imwrite(sys.argv[2], ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])
