# What this does (plain words): looks for a SMALL rule (a few numbers) that turns the reference colour into the reference height, so the
# generator can make its own height from its own colour with that rule. It tries: a straight mix of red, green, blue (sRGB numbers) with cut-offs,
# the same after a gamma, and a mix with one bend. Plain Python for analysis only (reads the reference; the generator never does).
import os, json
import cv2
import numpy as np


class _Result:
    pass


def least_squares(function, start, steps=60):
    """A tiny Levenberg-Marquardt fitter (no scipy here): nudges the numbers until the squared error stops falling."""
    p = np.array(start, dtype=np.float64)
    damping = 1e-2
    r = function(p)
    cost = float((r ** 2).sum())
    for _ in range(steps):
        jacobian = np.empty((r.size, p.size))
        for k in range(p.size):
            step = 1e-4 * max(abs(p[k]), 1e-2)
            q = p.copy(); q[k] += step
            jacobian[:, k] = (function(q) - r) / step
        gradient = jacobian.T @ r
        hessian = jacobian.T @ jacobian
        improved = False
        for _try in range(8):
            try:
                delta = np.linalg.solve(hessian + damping * np.diag(np.diag(hessian) + 1e-9), -gradient)
            except np.linalg.LinAlgError:
                damping *= 10
                continue
            r_new = function(p + delta)
            cost_new = float((r_new ** 2).sum())
            if cost_new < cost:
                p, r, cost = p + delta, r_new, cost_new
                damping = max(damping / 3, 1e-9)
                improved = True
                break
            damping *= 4
        if not improved:
            break
    out = _Result()
    out.x = p
    return out
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, '..', '..', '..', 'reference', 'gravel')
colour = cv2.imread(os.path.join(REF, 'colour.png'))[..., ::-1].astype(np.float64) / 255.0
height = cv2.imread(os.path.join(REF, 'height_as_uploaded.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
height = height[..., 0] if height.ndim == 3 else height
colour = cv2.GaussianBlur(colour, (0, 0), 0.5)   # the reference height is made from a slightly blurred colour
rng = np.random.default_rng(1)
idx = rng.choice(colour.shape[0] * colour.shape[1], 200000, replace=False)
flat = colour.reshape(-1, 3)[idx]
target = height.reshape(-1)[idx]

def model_linear(p, c):
    return np.clip(p[0] * c[:, 0] + p[1] * c[:, 1] + p[2] * c[:, 2] + p[3], 0, 255)
def model_gamma(p, c):
    g = np.clip(c, 1e-4, 1) ** p[4]
    return np.clip(p[0] * g[:, 0] + p[1] * g[:, 1] + p[2] * g[:, 2] + p[3], 0, 255)
for name, fn, p0 in (('linear', model_linear, [100, 100, 100, 0]), ('gamma', model_gamma, [300, 300, 300, 0, 1.0])):
    res = least_squares(lambda p: fn(p, flat) - target, p0)
    err = np.abs(fn(res.x, flat) - target).mean()
    print(name, res.x.round(3), 'mae', round(err, 2))
# rule 2: grey = weights . colour, then smooth tone curve y = 255 * smoothstep-like (power on clipped)
def model_curve(p, c):
    g = p[0] * c[:, 0] + p[1] * c[:, 1] + p[2] * c[:, 2]
    t = np.clip((g - p[3]) / max(p[4] - p[3], 1e-3), 0, 1)
    return 255 * t ** p[5]
res = least_squares(lambda p: model_curve(p, flat) - target, [0.3, 0.3, 0.3, 0.0, 1.0, 1.0])
print('mix + stretch + power', res.x.round(3), 'mae', round(np.abs(model_curve(res.x, flat) - target).mean(), 2))
json.dump({'mix_stretch_power': res.x.tolist()}, open(os.path.join(HERE, '..', 'scores', 'derivation_parametric.json'), 'w'))
