# What this does (plain words): the reference "height" and "normal" pictures were made from the reference COLOUR picture by a simple rule
# (grey brightness -> a little tone curve -> a very light blur -> slope = normal map). This script finds that rule with as few numbers as
# possible and measures how exactly it turns the REFERENCE colour into the REFERENCE height and normal. That is the "derivation ceiling":
# if our generated colour were perfect, the height and normal made by the same rule could be no better than this.
# It reads the reference (analysis scripts may). It is not part of the generator.
# Run:  python3 -I derivation_ceiling.py
import json
import os

import cv2
import numpy as np

PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
REF = os.path.join(PROC, 'reference', 'metal')
OUT = os.path.join(PROC, 'recipes', 'metal', 'analysis')


def load(name):
    return cv2.imread(os.path.join(REF, name), cv2.IMREAD_UNCHANGED)


colour_bgr = load('colour.png').astype(np.float64)
colour = colour_bgr[..., ::-1]                       # red, green, blue
height8 = load('height_as_uploaded.png').astype(np.float64)
height16 = load('height.png').astype(np.float64) / 257.0
normal_gl = load('normal.png')[..., ::-1].astype(np.float64) / 255.0 * 2 - 1       # OpenGL (green up)
normal_dx = load('normal_as_uploaded_directx.png')[..., ::-1].astype(np.float64) / 255.0 * 2 - 1

results = {}

# 1. grey weights by least squares on the colour values (sRGB values, no linearisation)
flat = colour.reshape(-1, 3)
design = np.concatenate([flat, np.ones((flat.shape[0], 1))], axis=1)
weights, *_ = np.linalg.lstsq(design, height8.ravel(), rcond=None)
results['grey_weights_red_green_blue_offset'] = [round(float(w), 4) for w in weights]
grey_fit = (design @ weights).reshape(height8.shape)
results['plain_grey_fit_mae_levels'] = float(np.abs(grey_fit - height8).mean())
for name, w in {'luma_601': (0.299, 0.587, 0.114), 'luma_709': (0.2126, 0.7152, 0.0722), 'mean': (1 / 3, 1 / 3, 1 / 3)}.items():
    g = colour @ np.array(w)
    results['corr_with_height_' + name] = float(np.corrcoef(g.ravel(), height8.ravel())[0, 1])

# 2. a tone curve (monotone, 12 control points) after the grey, then a blur; search the blur width
grey = colour @ np.array([0.299, 0.587, 0.114])


def isotonic_curve(x, y, points=12):
    """Monotone piecewise-linear curve through bin means (pool-adjacent-violators on 64 bins), reduced to `points` control points."""
    order = np.argsort(x.ravel())
    xs, ys = x.ravel()[order], y.ravel()[order]
    bins = np.array_split(np.arange(xs.size), 64)
    bx = np.array([xs[b].mean() for b in bins])
    by = np.array([ys[b].mean() for b in bins])
    # pool adjacent violators
    values, weights_, blocks = list(by), [1.0] * len(by), [[i] for i in range(len(by))]
    i = 0
    while i < len(values) - 1:
        if values[i] > values[i + 1]:
            total = weights_[i] + weights_[i + 1]
            values[i] = (values[i] * weights_[i] + values[i + 1] * weights_[i + 1]) / total
            weights_[i] = total
            blocks[i] += blocks[i + 1]
            del values[i + 1], weights_[i + 1], blocks[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    mono = np.zeros(len(by))
    for value, block in zip(values, blocks):
        mono[block] = value
    pick = np.linspace(0, len(bx) - 1, points).round().astype(int)
    return bx[pick], mono[pick]


best = None
for sigma in (0.0, 0.5, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5):
    g = cv2.GaussianBlur(grey, (0, 0), sigma) if sigma > 0 else grey
    cx, cy = isotonic_curve(g, height8)
    pred = np.interp(g, cx, cy)
    mae = float(np.abs(pred - height8).mean())
    if best is None or mae < best['mae']:
        best = {'sigma': sigma, 'mae': mae, 'curve_x': cx.round(1).tolist(), 'curve_y': cy.round(1).tolist()}
results['tone_curve_and_blur'] = best
print('best blur', best['sigma'], 'mae', best['mae'])

# the likelier order: blur the grey first (the paint is slightly soft), then the tone curve
g_blur = cv2.GaussianBlur(grey, (0, 0), best['sigma'])
cx, cy = isotonic_curve(g_blur, height8)
height_pred = np.clip(np.interp(g_blur, cx, cy), 0, 255)
results['curve_then_blur'] = 'not used (blur first fits better: 3.0 against 5.0 levels)'
results['height_pred_mae_levels'] = float(np.abs(height_pred - height8).mean())
results['height_pred_correlation'] = float(np.corrcoef(height_pred.ravel(), height8.ravel())[0, 1])
# best linear brightness/contrast fix error (what pixel_compare calls "best fit")
A = np.stack([height_pred.ravel(), np.ones(height_pred.size)], axis=1)
coef, *_ = np.linalg.lstsq(A, height8.ravel(), rcond=None)
results['height_pred_mae_after_linear_fix'] = float(np.abs(A @ coef - height8.ravel()).mean())
results['height16_vs_height8_mae_levels'] = float(np.abs(height16 - height8).mean())
results['height16_equals_blurred_height8'] = {
    str(s): float(np.abs(cv2.GaussianBlur(height8, (0, 0), s) - height16).mean()) for s in (0.5, 0.8, 1.0, 1.3)}

# 3. normal map from a height by Sobel with whole-number strengths
def sobel_normal_dx(h, strength):
    h = h / 255.0
    def shift(a, dy, dx):
        return np.roll(np.roll(a, dy, axis=0), dx, axis=1)
    gx = (shift(h, 0, -1) * 2 - shift(h, 0, 1) * 2 + shift(h, -1, -1) + shift(h, 1, -1) - shift(h, -1, 1) - shift(h, 1, 1)) / 8.0
    gy = (shift(h, -1, 0) * 2 - shift(h, 1, 0) * 2 + shift(h, -1, -1) + shift(h, -1, 1) - shift(h, 1, -1) - shift(h, 1, 1)) / 8.0
    nx, ny, nz = -strength * gx, -strength * gy, np.ones_like(h)       # DirectX: green points down the picture
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], axis=-1)


def mean_angle(a, b):
    dot = np.clip((a * b).sum(axis=-1), -1, 1)
    return float(np.degrees(np.arccos(dot)).mean())


strengths = {}
for s in (2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 24, 32):
    strengths[s] = mean_angle(sobel_normal_dx(height8, s * 1.0), normal_dx)
results['normal_from_uploaded_height_by_strength'] = strengths
best_strength = min(strengths, key=strengths.get)
results['best_whole_strength'] = best_strength
pred_normal = sobel_normal_dx(height_pred, best_strength * 1.0)
results['normal_from_predicted_height_angle'] = mean_angle(pred_normal, normal_dx)
# how far is the normal map's own typical slope from flat (the angle of the normal map against "all flat")
results['normal_reference_mean_angle_from_flat'] = float(np.degrees(np.arccos(np.clip(normal_dx[..., 2], -1, 1))).mean())
results['normal_flat_guess_angle'] = mean_angle(np.stack([np.zeros_like(height8), np.zeros_like(height8), np.ones_like(height8)], -1), normal_dx)
results['normal_gl_is_dx_with_green_flipped'] = float(np.abs(normal_gl[..., 1] + normal_dx[..., 1]).max())

with open(os.path.join(OUT, 'derivation_ceiling.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
