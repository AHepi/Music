# What this does (plain words): for the baked classes, tries different normal-map strengths (how steep the slopes look) and measures the average angle to the reference normal map, to
# see whether a LOWER strength than the reference's own (9) gives a smaller error when the colour picture is not exact. Analysis only (reads the reference normal map).
import os, sys, json
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ref = cv2.imread(PROC + '/reference/mud/normal.png')[..., ::-1].astype(np.float64) / 255 * 2 - 1
def normal_from(h8, strength, kernel):
    h = h8.astype(np.float64)
    if kernel == 'central':
        hx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2.0; hy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2.0
    else:
        p = np.pad(h, 2, mode='wrap'); hx = cv2.Sobel(p, cv2.CV_64F, 1, 0, ksize=3)[2:-2, 2:-2] / 8.0; hy = cv2.Sobel(p, cv2.CV_64F, 0, 1, ksize=3)[2:-2, 2:-2] / 8.0
    n = np.stack([-strength * hx / 255, strength * hy / 255, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)
def angle(a, b):
    return float(np.degrees(np.arccos(np.clip((a * b).sum(-1), -1, 1))).mean())
out = {}
for name in sys.argv[1:]:
    h16 = cv2.imread(f'outputs/{name}/height.png', cv2.IMREAD_UNCHANGED); h16 = (h16[..., 0] if h16.ndim == 3 else h16).astype(np.float64)
    h8 = np.round(h16 / 65535 * 255)
    out[name] = {}
    for kernel in ('central', 'sobel'):
        for s in (2, 3, 4, 5, 6, 7, 9):
            out[name][f'{kernel}_{s}'] = round(angle(normal_from(h8, s, kernel), ref), 2)
    best = min(out[name], key=out[name].get)
    print(name, 'strength 9 central:', out[name]['central_9'], '| best:', best, out[name][best])
json.dump(out, open('scores/normal_strength_test.json', 'w'), indent=1)
