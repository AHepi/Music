# What this does (plain Python, no Blender): reads the three "puddle depth" pictures made by 02_puddle_sweep.py and works out, for each setting of the
# Puddles dial, what share of the road (and of the pavements) is puddle, using the same formula as the WETNESS layer. Then it finds the three numbers
# (top, range, curve) of the layer's dial formula  threshold = top - range * dial ** curve  that make the road coverage in the main camera hit the targets
# 3 % at 0.3, 8 % at 0.5, 15 % at 0.65, 30 % at 0.8, and prints the table for all three cameras with the old and the new dial.
# Run: python3 -I tools/02b_puddle_fit.py work/r02 [top range curve]
import json
import sys

import numpy as np
from PIL import Image

folder = sys.argv[1]
TARGETS = {0.3: 0.03, 0.5: 0.08, 0.65: 0.15, 0.8: 0.30}


def load(name):
    pic = np.asarray(Image.open(f'{folder}/{name}_depth.png').convert('RGB')).astype(float) / 255.0
    road = pic[..., 1] > 0.5
    pavement = pic[..., 2] > 0.5
    return pic[..., 0], road, pavement


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def coverage(depth, region, dial, top, rng, curve, scale=1.0):
    p = dial * scale
    thr = top - rng * (max(p, 1e-4) ** curve)
    mask = smooth((depth[region] - thr) / 0.06) * np.clip(p / 0.05, 0, 1)
    return float(mask.mean())


pics = {name: load(name) for name in ('main', 'lockout', 'notice', 'overhead')}
depth, road, pavement = pics['main']
print('road pixels in the main camera:', int(road.sum()), ' pavement pixels:', int(pavement.sum()))
print('depth on the main road: percentiles 5 25 50 75 95 99 =', np.round(np.percentile(depth[road], [5, 25, 50, 75, 95, 99]), 3))
# required thresholds for the targets (bisection on the coverage of the main camera's road)
required = {}
for dial, target in TARGETS.items():
    lo, hi = 0.0, 1.2
    for _ in range(50):
        mid = (lo + hi) / 2
        mask = smooth((depth[road] - mid) / 0.06).mean()
        if mask > target:
            lo = mid
        else:
            hi = mid
    required[dial] = (lo + hi) / 2
print('threshold needed for each target:', {k: round(v, 3) for k, v in required.items()})
# fit top, range, curve by a small grid search
best = None
dials = np.array(list(required))
need = np.array(list(required.values()))
for top in np.arange(0.5, 1.2, 0.01):
    for rng in np.arange(0.2, 1.2, 0.01):
        for curve in np.arange(0.4, 2.5, 0.05):
            err = float(np.sum((top - rng * dials ** curve - need) ** 2))
            if best is None or err < best[0]:
                best = (err, top, rng, curve)
_, top, rng, curve = best
if len(sys.argv) > 4:
    top, rng, curve = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
print(f'fitted dial: threshold = {top:.2f} - {rng:.2f} * dial ** {curve:.2f}')
# the pavement should hold about 0.4 times what the road holds: find the bias (added to the threshold) that gives that at the four target dials, over all pavement pixels
bias_best = None
for bias in np.arange(0.0, 0.4, 0.005):
    err = 0.0
    for dial, target in TARGETS.items():
        pooled = np.concatenate([d[pv] for d, _, pv in pics.values()])
        thr = top - rng * dial ** curve + bias
        got = float(smooth((pooled - thr) / 0.06).mean())
        err += (got - 0.4 * target) ** 2
    if bias_best is None or err < bias_best[0]:
        bias_best = (err, bias)
bias = bias_best[1]
print(f'pavement bias (Puddle Bias input) = {bias:.3f}')
result = {'fit': {'top': round(top, 3), 'range': round(rng, 3), 'curve': round(curve, 3), 'pavement_bias': round(float(bias), 3)}, 'old': {}, 'new': {}}
for label, (t, r, c, b) in (('old', (0.97, 0.70, 1.0, 0.0)), ('new', (top, rng, curve, 0.0)), ('new+bias', (top, rng, curve, bias))):
    print(f'\n{label} dial (top {t:.2f}, range {r:.2f}, curve {c:.2f}, pavement bias {b:.3f}) - share of the ROAD / of the PAVEMENTS that is puddle, per cent (overhead = share of the area, the rest = share of the picture)')
    print('dial   ' + '   '.join(f'{n:>14s}' for n in pics))
    for dial in (0.1, 0.2, 0.3, 0.4, 0.5, 0.65, 0.8, 0.9, 1.0):
        row = []
        for name, (d, rd, pv) in pics.items():
            road_cover = 100 * coverage(d, rd, dial, t, r, c)
            pave_cover = 100 * coverage(d, pv, dial, t + b if False else t, r, c, 1.0) if b == 0 else 100 * float((smooth((d[pv] - (t - r * max(dial, 1e-4) ** c + b)) / 0.06) * np.clip(dial / 0.05, 0, 1)).mean())
            row.append(f'{road_cover:5.1f} /{pave_cover:5.1f}   ')
            result.setdefault(label, {}).setdefault(str(dial), {})[name] = [round(road_cover, 2), round(pave_cover, 2)]
        print(f'{dial:4.2f}   ' + '  '.join(row))
json.dump(result, open(f'{folder}/puddle_fit.json', 'w'), indent=1)
