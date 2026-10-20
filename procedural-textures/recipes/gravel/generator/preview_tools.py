# What this does (plain words): quick checks of a gravel description WITHOUT Blender: it makes the shape list, draws it with OpenCV (a fast stand-in for
# the Blender photograph), and measures the same things the reference was measured for (share of soil dots and stone dots, how much stone survives
# opening with bigger and bigger discs). Used to tune the stone and soil counts before the slower real bake. Plain Python (python3 -I).
import json, os, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gravel_layers as gl

RADII = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]


def soil_stone_masks(bgr):
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    soil = ((lab[..., 2] > 5.0) & (lab[..., 1] > 2.0) & (chroma > 6.5)).astype(np.uint8) * 255
    soil = cv2.medianBlur(soil, 5) > 0
    return soil, ~soil


def wrap_open(mask, r, pad=60):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    m = np.pad(mask.astype(np.uint8), pad, mode='wrap')
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, k)[pad:-pad, pad:-pad] > 0


def granulometry(mask):
    return [float(mask.mean())] + [float(wrap_open(mask, r).mean()) for r in RADII]


def measure(bgr):
    soil, stone = soil_stone_masks(bgr)
    return {'stone_share': float(stone.mean()), 'stone_gran': granulometry(stone), 'soil_gran': granulometry(soil)}


def edge_density(bgr):
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return float((cv2.Canny(grey, 50, 150) > 0).mean())


def make_preview(description, scale=2):
    started = time.time()
    shapes = gl.make_shape_list(description)
    t_shapes = time.time() - started
    started = time.time()
    picture = gl.preview(shapes, int(description['tile']), scale)
    return picture, len(shapes), t_shapes, time.time() - started


if __name__ == '__main__':
    description = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    picture, n, t1, t2 = make_preview(description)
    cv2.imwrite(out, picture)
    ref = json.load(open(os.path.join(HERE, '..', 'scores', 'measurements.json')))
    m = measure(picture)
    print(f'{n} shapes (list {t1:.1f}s, draw {t2:.1f}s); stone share {m["stone_share"]:.3f} (reference {ref["stone_share"]:.3f}); edge density {edge_density(picture):.3f}')
    print('stone survives opening radius', [0] + RADII)
    print('  generated', np.round(m['stone_gran'], 3).tolist())
    print('  reference', np.round(ref['granulometry']['stone'], 3).tolist())
    print('soil survives')
    print('  generated', np.round(m['soil_gran'], 3).tolist())
    print('  reference', np.round(ref['granulometry']['soil'], 3).tolist())
