# What this does (plain words): checks how exactly the MUD height picture and normal picture can be made FROM the wood colour picture
# (the upload was made that way). It fits three small things: which mix of red/green/blue counts as "bright", a tone curve (bright colour -> height),
# a blur size, and the normal-map strength. The accuracy it reaches is the CEILING for any recipe that makes its height and normal out of its own
# colour picture: even a perfect colour could not do better. Plain Python (run with python3 -I). It READS the reference (analysis only; the
# generator never does). Output: analysis/derivation_ceiling.json and printed lines.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(PROC, 'reference', 'mud')

colour = cv2.imread(os.path.join(REF, 'colour.png'))[..., ::-1].astype(np.float64) / 255.0            # RGB 0..1 (sRGB numbers)
height = cv2.imread(os.path.join(REF, 'height_as_uploaded.png'), cv2.IMREAD_UNCHANGED)
height = (height[..., 0] if height.ndim == 3 else height).astype(np.float64)
normal_up = cv2.imread(os.path.join(REF, 'normal.png'))[..., ::-1].astype(np.float64) / 255.0 * 2 - 1    # OpenGL (green up)

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


def tone_curve_fit(grey, target, bins=64):
    """Best curve 'grey -> height': mean target in each of `bins` grey slots (a monotone lookup of 64 numbers)."""
    edges = np.linspace(grey.min(), grey.max(), bins + 1)
    index = np.clip(np.digitize(grey.ravel(), edges) - 1, 0, bins - 1)
    sums = np.bincount(index, weights=target.ravel(), minlength=bins)
    counts = np.bincount(index, minlength=bins)
    means = np.where(counts > 0, sums / np.maximum(counts, 1), np.nan)
    centres = (edges[:-1] + edges[1:]) / 2
    ok = ~np.isnan(means)
    return centres[ok], np.maximum.accumulate(means[ok])


best = None
for name, grey in grey_candidates.items():
    for sigma in (0.0, 0.3, 0.5, 0.8, 1.0, 1.3):
        blurred = cv2.GaussianBlur(grey, (0, 0), sigma) if sigma > 0 else grey
        cx, cy = tone_curve_fit(blurred, height)
        fitted = np.interp(blurred, cx, cy)
        mae = float(np.abs(fitted - height).mean())
        corr = float(np.corrcoef(fitted.ravel(), height.ravel())[0, 1])
        print(f'{name:22s} blur {sigma:3.1f}  mean error {mae:6.2f} levels  correlation {corr:.4f}')
        if best is None or mae < best[0]:
            best = (mae, name, sigma, cx, cy, corr)
mae, name, sigma, cx, cy, corr = best
print('BEST:', name, 'blur', sigma, 'mean error', round(mae, 2), 'correlation', round(corr, 4))
report['height_from_colour'] = {'grey': name, 'blur_sigma': sigma, 'mae_levels': round(mae, 2), 'correlation': round(corr, 4),
                                'curve_points': [[round(float(a), 4), round(float(b), 2)] for a, b in zip(cx[::4], cy[::4])]}

grey = cv2.GaussianBlur(grey_candidates[name], (0, 0), sigma) if sigma > 0 else grey_candidates[name]
# a straight-line stretch with cut-offs (the simplest recipe a generator can use): height = clip((grey*255 - low) * gain)
best_line = None
g255 = grey * 255.0
for low in np.arange(0, 60, 2.0):
    for high in np.arange(80, 200, 2.0):
        fitted = np.clip((g255 - low) / (high - low), 0, 1) * 255.0
        e = np.abs(fitted - height).mean()
        if best_line is None or e < best_line[0]:
            best_line = (e, low, high)
print('straight-line stretch: grey_low', best_line[1], 'grey_high', best_line[2], 'mean error', round(best_line[0], 2))
report['straight_line'] = {'grey_low': float(best_line[1]), 'grey_high': float(best_line[2]), 'mae_levels': round(float(best_line[0]), 2)}
for n_points in (2, 3, 4, 6, 8):
    px = np.quantile(grey, np.linspace(0, 1, n_points))
    py = [height[(grey >= px[max(i - 1, 0)]) & (grey <= px[min(i + 1, n_points - 1)])].mean() for i in range(n_points)]
    small = np.interp(grey, px, py)
    report[f'curve_{n_points}_points_mae'] = round(float(np.abs(small - height).mean()), 2)
    print(f'  tone curve with {n_points} control points: mean error {report[f"curve_{n_points}_points_mae"]}')


def sobel_normal(h, strength, kernel='central'):
    if kernel == 'central':
        hx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
        hy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2.0
    else:
        padded = np.pad(h, 2, mode='wrap')
        hx = cv2.Sobel(padded, cv2.CV_64F, 1, 0, ksize=3)[2:-2, 2:-2] / 8.0
        hy = cv2.Sobel(padded, cv2.CV_64F, 0, 1, ksize=3)[2:-2, 2:-2] / 8.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h)
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def mean_angle(a, b):
    a = a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)
    b = b / np.maximum(np.linalg.norm(b, axis=-1, keepdims=True), 1e-9)
    return float(np.degrees(np.arccos(np.clip((a * b).sum(-1), -1, 1))).mean())


best_normal = None
for kernel in ('central', 'sobel'):
    for strength in (3, 4, 5, 6, 7, 8, 9, 10, 12, 16):
        angle = mean_angle(sobel_normal(height, strength, kernel), normal_up)
        if best_normal is None or angle < best_normal[0]:
            best_normal = (angle, kernel, strength)
        if strength in (7, 8, 9):
            print(f'   normal from the UPLOADED height, {kernel}, strength {strength}: mean angle {angle:.2f} degrees')
print('best normal from the uploaded height:', best_normal)
report['normal_from_uploaded_height'] = {'kernel': best_normal[1], 'strength': best_normal[2], 'mean_angle_degrees': round(best_normal[0], 3)}

fitted_height = np.interp(grey, cx, cy)
line_height = np.clip((g255 - best_line[1]) / (best_line[2] - best_line[1]), 0, 1) * 255.0
for label, h in (('tone curve', fitted_height), ('straight line', line_height)):
    for kernel in ('central', 'sobel'):
        results = [(mean_angle(sobel_normal(h, strength, kernel), normal_up), strength) for strength in (4, 6, 8, 10, 12, 16, 20)]
        angle, strength = min(results)
        print(f'chain colour -> {label} height -> normal, {kernel}: best strength {strength}, mean angle {angle:.2f} degrees')
        report[f'chain_normal_{label.replace(" ", "_")}_{kernel}'] = {'strength': strength, 'mean_angle_degrees': round(angle, 3)}
flat = np.zeros_like(normal_up)
flat[..., 2] = 1
report['flat_normal_angle'] = round(mean_angle(flat, normal_up), 3)
print('a flat normal map would be wrong by', report['flat_normal_angle'], 'degrees')
json.dump(report, open(os.path.join(HERE, 'derivation_ceiling.json'), 'w'), indent=1)
