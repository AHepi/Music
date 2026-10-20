# What this does (plain words): checks how exactly the slate's height picture and normal picture can be made FROM the slate's colour
# picture (the upload was made that way). It fits three small things: a brightness recipe (which mix of red, green, blue counts as
# "bright"), a tone curve (bright colour -> height), a blur size, and a normal-map strength. The accuracy it reaches is the CEILING for
# any recipe that makes height and normal from its own colour picture: if my colour were perfect, my height and normal could be no better
# than this. Plain Python (run with python3 -I), reads the reference pictures (analysis only, never used inside the generator).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(PROC, 'reference', 'slate')

colour = cv2.imread(os.path.join(REF, 'colour.png'))[..., ::-1].astype(np.float64) / 255.0       # RGB 0..1 (sRGB numbers)
height = cv2.imread(os.path.join(REF, 'height_as_uploaded.png'), cv2.IMREAD_UNCHANGED)
height = (height[..., 0] if height.ndim == 3 else height).astype(np.float64)
normal_up = cv2.imread(os.path.join(REF, 'normal.png'))[..., ::-1].astype(np.float64) / 255.0 * 2 - 1   # OpenGL

# 1. brightness recipe: linear least squares of height on the three colour numbers (before any curve)
design = np.concatenate([colour.reshape(-1, 3), np.ones((colour.size // 3, 1))], axis=1)
weights = np.linalg.lstsq(design, height.ravel(), rcond=None)[0]
print('plain linear fit weights (r, g, b, offset):', weights.round(2))
grey_candidates = {
    'rec709_srgb_numbers': colour @ np.array([0.2126, 0.7152, 0.0722]),
    'rec601_srgb_numbers': colour @ np.array([0.299, 0.587, 0.114]),
    'plain_average': colour.mean(axis=-1),
    'fitted_weights': (colour @ weights[:3]) / 255.0,
}
report = {'linear_weights': weights.round(3).tolist()}


def tone_curve_fit(grey, target, bins=64, smooth_sigma=0.0):
    """Best curve 'grey -> height': the mean target in each of `bins` grey slots, interpolated (a monotone-ish lookup of 64 numbers)."""
    edges = np.linspace(grey.min(), grey.max(), bins + 1)
    index = np.clip(np.digitize(grey.ravel(), edges) - 1, 0, bins - 1)
    sums = np.bincount(index, weights=target.ravel(), minlength=bins)
    counts = np.bincount(index, minlength=bins)
    means = np.where(counts > 0, sums / np.maximum(counts, 1), np.nan)
    centres = (edges[:-1] + edges[1:]) / 2
    ok = ~np.isnan(means)
    curve_x, curve_y = centres[ok], means[ok]
    # enforce monotone with a running max after a light pooling (isotonic-ish)
    curve_y = np.maximum.accumulate(curve_y)
    return curve_x, curve_y


best = None
for name, grey in grey_candidates.items():
    for sigma in (0.0, 0.5, 0.8, 1.0, 1.3):
        blurred = cv2.GaussianBlur(grey, (0, 0), sigma) if sigma > 0 else grey
        cx, cy = tone_curve_fit(blurred, height)
        fitted = np.interp(blurred, cx, cy)
        mae = float(np.abs(fitted - height).mean())
        corr = float(np.corrcoef(fitted.ravel(), height.ravel())[0, 1])
        print(f'{name:22s} blur {sigma:3.1f}  mae {mae:6.2f} levels  corr {corr:.4f}')
        if best is None or mae < best[0]:
            best = (mae, name, sigma, cx, cy, corr)
mae, name, sigma, cx, cy, corr = best
print('BEST:', name, 'blur', sigma, 'mae', round(mae, 2), 'corr', round(corr, 4))
report['height_from_colour'] = {'grey': name, 'blur_sigma': sigma, 'mae_levels': round(mae, 2), 'correlation': round(corr, 4),
                                'curve_points': [[round(float(a), 4), round(float(b), 2)] for a, b in zip(cx[::4], cy[::4])]}

# 2. a very small tone curve (4 control points) to see how little is needed
ctrl_x = np.quantile(grey_candidates[name], [0.0, 0.25, 0.6, 1.0])
grey = cv2.GaussianBlur(grey_candidates[name], (0, 0), sigma)
for n_points in (2, 3, 4, 6, 8):
    px = np.quantile(grey, np.linspace(0, 1, n_points))
    py = [height[(grey >= px[max(i - 1, 0)]) & (grey <= px[min(i + 1, n_points - 1)])].mean() for i in range(n_points)]
    small = np.interp(grey, px, py)
    print(f'  tone curve with {n_points} control points: mae {np.abs(small - height).mean():.2f}')
    report[f'curve_{n_points}_points_mae'] = round(float(np.abs(small - height).mean()), 2)

# 3. normal map from the reference height itself (the uploaded 8-bit): which strength?
def sobel_normal(h, strength, kernel='central'):
    if kernel == 'central':
        hx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
        hy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2.0
    else:   # real Sobel 3 x 3 (divided by 8 = 4 rows weighting x 2 gap)
        padded = np.pad(h, 2, mode='wrap')
        hx = cv2.Sobel(padded, cv2.CV_64F, 1, 0, ksize=3)[2:-2, 2:-2] / 8.0
        hy = cv2.Sobel(padded, cv2.CV_64F, 0, 1, ksize=3)[2:-2, 2:-2] / 8.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h)   # hy is per step DOWN the picture; up = minus
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def mean_angle(a, b):
    a = a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)   # the 8-bit reference normals are not exactly length 1
    b = b / np.maximum(np.linalg.norm(b, axis=-1, keepdims=True), 1e-9)
    return float(np.degrees(np.arccos(np.clip((a * b).sum(-1), -1, 1))).mean())

best_normal = None
for kernel in ('central', 'sobel'):
    for strength in (3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 25, 30):
        n = sobel_normal(height, strength, kernel)
        a = mean_angle(n, normal_up)
        if best_normal is None or a < best_normal[0]:
            best_normal = (a, kernel, strength)
        if kernel == 'sobel' and strength in (6, 7, 8, 16, 20, 30):
            print(f'   normal from the UPLOADED height, {kernel}, strength {strength}: mean angle {a:.2f} deg')
print('best normal from the uploaded height:', best_normal)
report['normal_from_uploaded_height'] = {'kernel': best_normal[1], 'strength': best_normal[2], 'mean_angle_degrees': round(best_normal[0], 3)}

# 4. the whole chain: reference COLOUR -> fitted height -> normal
fitted_height = np.interp(grey, cx, cy)
for kernel in ('central', 'sobel'):
    results = []
    for strength in (3, 5, 7, 9, 12, 16, 20, 25, 30, 40):
        n = sobel_normal(fitted_height, strength, kernel)
        results.append((mean_angle(n, normal_up), strength))
    angle, strength = min(results)
    print(f'chain colour -> height -> normal, {kernel}: best strength {strength}, mean angle {angle:.2f} deg')
    report[f'chain_normal_{kernel}'] = {'strength': strength, 'mean_angle_degrees': round(angle, 3)}
# the "do nothing" angle for comparison: a flat normal
flat = np.zeros_like(normal_up)
flat[..., 2] = 1
report['flat_normal_angle'] = round(mean_angle(flat, normal_up), 3)
print('a completely flat normal map is off by', report['flat_normal_angle'], 'degrees on average')
os.makedirs(os.path.join(HERE, '..', 'scores'), exist_ok=True)
json.dump(report, open(os.path.join(HERE, '..', 'scores', 'derivation_ceiling.json'), 'w'), indent=1)
