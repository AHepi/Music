# What this does (plain words): ANALYSIS (reads the reference picture). Finds the LAYOUT of the wood picture and writes it as numbers in analysis/layout_fit.json:
#   - boards: the 5 dark gaps between planks as smooth centre lines (height of the gap at 52 evenly spaced places across the tile), and each board's
#     average colour;
#   - knots: for each of the 4 round knots, its centre, its size, and the colour of each ring (read from the picture around the centre);
#   - blobs: the round dark-brown splatters, found as small compact areas of the dark-brown colours and grouped into clouds;
#   - pebbles: the small grey stones lying in the gaps (count, size, where) for each gap.
# Run: python3 -I fit_layout.py     Plain Python.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import trace_tools as tt  # noqa: E402

bgr = cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
H, W = bgr.shape[:2]
grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
lab = tt.srgb_to_lab_float(bgr)
out = {}

# ---------------------------------------------------------------------------------------------- boards: gap centre lines
nominal = [188, 470, 706, 977, 1157]
samples = 52
x_from, x_to = -25.0, W + 25.0
xs = np.linspace(x_from, x_to, samples)
wrapped = np.pad(grey, ((60, 60), (60, 60)), mode='wrap')
lines = []
for y0 in nominal:
    ys = []
    for x in xs:
        xi = int(round(x)) + 60
        window = wrapped[y0 - 34 + 60:y0 + 35 + 60, xi - 16:xi + 17].mean(axis=1)
        smooth = np.convolve(window, np.ones(7) / 7, mode='same')
        smooth[:4], smooth[-4:] = 255, 255
        ys.append(y0 - 34 + int(np.argmin(smooth)))
    ys = np.array(ys, np.float64)
    # remove jumps to the neighbouring dark line: median filter, then light smoothing
    med = np.array([np.median(ys[max(0, i - 2):i + 3]) for i in range(len(ys))])
    lines.append(np.round(med).astype(int).tolist())
    print(f'gap near {y0}: centre line min {med.min():.0f} max {med.max():.0f}')
out['gap_lines'] = {'x_from': x_from, 'x_to': x_to, 'samples': samples, 'lines': lines}
# the width of each gap: dark dots (brightness under 30) in a 33-dot-wide window around the centre line, within 22 rows of it; at least 2
widths = []
for gi, y0 in enumerate(nominal):
    ws = []
    for x, yc in zip(xs, lines[gi]):
        xi = int(round(x)) + 60
        window = wrapped[int(yc) - 22 + 60:int(yc) + 23 + 60, xi - 16:xi + 17]
        ws.append(float((window < 30).mean(axis=1).sum()))
    widths.append([round(max(w, 2.0), 1) for w in ws])
    print(f'gap {gi}: width min {min(ws):.1f} median {np.median(ws):.1f} max {max(ws):.1f}')
out['gap_widths'] = widths

board_colours = []
yy = np.arange(H)
for i in range(len(lines)):
    top = np.interp(np.arange(W), xs, lines[i])
    bottom = np.interp(np.arange(W), xs, lines[(i + 1) % len(lines)]) + (H if i + 1 == len(lines) else 0)
    mask = np.zeros((H, W), bool)
    for x in range(W):
        a, b = int(top[x]) + 6, int(bottom[x]) - 6
        rows = np.arange(a, b) % H
        mask[rows, x] = True
    mean = lab[mask].mean(axis=0)
    board_colours.append([round(float(v), 1) for v in mean])
    print(f'board {i}: mean Lab {board_colours[-1]}, rows {int(top.mean())}..{int(bottom.mean())}')
out['board_mean_lab'] = board_colours

# ---------------------------------------------------------------------------------------------- knots
knots_guess = [(350, 378, 64, 54), (170, 800, 64, 54), (990, 105, 46, 46), (832, 890, 30, 40)]
knots = []
for gx, gy, rx, ry in knots_guess:
    # refine the centre: darkest compact spot (the knot hole) within 16 dots of the guess
    patch = cv2.GaussianBlur(grey, (0, 0), 2.0)[gy - 16:gy + 17, gx - 16:gx + 17]
    dy, dx = np.unravel_index(np.argmin(patch), patch.shape)
    cx, cy = gx - 16 + dx, gy - 16 + dy
    # mean colour in ellipse-shaped rings from the outside to the inside (12 rings)
    yy_, xx_ = np.mgrid[0:H, 0:W]
    pad = int(max(rx, ry)) + 4
    sub = lab[cy - pad:cy + pad + 1, cx - pad:cx + pad + 1]
    sy, sx = np.mgrid[-pad:pad + 1, -pad:pad + 1]
    radius = np.sqrt((sx / rx) ** 2 + (sy / ry) ** 2)
    edges = np.linspace(0, 1.0, 14)
    ring_lab = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (radius >= a) & (radius < b)
        ring_lab.append([round(float(v), 1) for v in sub[m].mean(axis=0)])
    knots.append({'x': int(cx), 'y': int(cy), 'rx': rx, 'ry': ry, 'ring_lab_outer_last': ring_lab})
    print('knot at', cx, cy, 'ring lightness (centre to rim):', [r[0] for r in ring_lab])
out['knots'] = knots

# ---------------------------------------------------------------------------------------------- blobs (rust splatters)
centres = tt.make_palette(bgr, 24)
palette = tt.palette_to_bgr(centres)
labels = tt.assign_labels(bgr, centres)
rust_family = [k for k in range(24) if 12 <= centres[k][0] <= 30 and centres[k][2] > 11 and np.hypot(centres[k][1], centres[k][2]) > 14]
print('rust-coloured palette entries (Lab):', [(k, [round(float(v), 1) for v in centres[k]]) for k in rust_family])
rust = np.isin(labels, rust_family).astype(np.uint8)
rust = cv2.morphologyEx(rust, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
n, comp, stats, cent = cv2.connectedComponentsWithStats(rust, connectivity=8)
blobs = []
for i in range(1, n):
    x, y, w, h, area = stats[i]
    if 14 <= area <= 1500 and max(w, h) / max(min(w, h), 1) < 3.0 and area / (w * h) > 0.45:
        blobs.append((float(cent[i][0]), float(cent[i][1]), float(np.sqrt(area / np.pi)), int(area)))
blobs = np.array(blobs)
print('round-ish rust blobs:', len(blobs), ' radius median', np.median(blobs[:, 2]) if len(blobs) else None)
# group blobs into clouds: a simple greedy grouping, a blob joins the cloud whose centre is within 70 dots of it (the cloud centre follows)
order = np.argsort(-blobs[:, 3])
clouds = []
for k in order:
    x, y, r, a = blobs[k]
    for c in clouds:
        if np.hypot(x - c['x'], y - c['y']) < 70:
            c['members'].append((x, y, r))
            c['x'] = float(np.mean([m[0] for m in c['members']]))
            c['y'] = float(np.mean([m[1] for m in c['members']]))
            break
    else:
        clouds.append({'x': float(x), 'y': float(y), 'members': [(x, y, r)]})
fitted_clouds = []
for c in clouds:
    m = np.array(c['members'])
    if len(m) < 3:
        continue
    fitted_clouds.append({'x': round(c['x']), 'y': round(c['y']), 'n': int(len(m)), 'spread_x': round(float(np.max(np.abs(m[:, 0] - c['x'])) + 4)),
                          'spread_y': round(float(np.max(np.abs(m[:, 1] - c['y'])) + 4)), 'r_min': round(float(m[:, 2].min()), 1), 'r_max': round(float(m[:, 2].max()), 1)})
fitted_clouds.sort(key=lambda c: -c['n'])
print('clouds with at least 3 blobs:', len(fitted_clouds), ' blobs in them', sum(c['n'] for c in fitted_clouds))
out['blob_clouds'] = fitted_clouds
out['blob_stats'] = {'count': int(len(blobs)), 'radius_quantiles': [round(float(v), 1) for v in np.quantile(blobs[:, 2], [0.05, 0.25, 0.5, 0.75, 0.95])],
                     'rust_palette_lab': [[round(float(v), 1) for v in centres[k]] for k in rust_family],
                     'rust_share_of_picture': round(float(rust.mean()), 4)}

# ---------------------------------------------------------------------------------------------- pebbles in the gaps
stone = np.isin(labels, [k for k in range(24) if centres[k][0] > 14 and centres[k][0] < 40 and np.hypot(centres[k][1], centres[k][2]) < 6]).astype(np.uint8)
pebbles = []
for gi, y0 in enumerate(nominal):
    xs_line = np.interp(np.arange(W), xs, lines[gi])
    band = np.zeros((H, W), np.uint8)
    for x in range(W):
        band[int(xs_line[x]) % H - 14:int(xs_line[x]) % H + 15 if int(xs_line[x]) % H + 15 <= H else H, x] = 1
    n, comp, stats, cent = cv2.connectedComponentsWithStats(stone & band, connectivity=8)
    found = [(float(cent[i][0]), float(cent[i][1]), float(np.sqrt(stats[i][4] / np.pi))) for i in range(1, n) if 15 <= stats[i][4] <= 300]
    pebbles.append(found)
    print(f'gap {gi}: {len(found)} pebbles, radius median', round(float(np.median([f[2] for f in found])), 1) if found else None)
out['pebbles'] = [{'gap': i, 'count': len(p), 'x_min': round(min([f[0] for f in p])) if p else 0, 'x_max': round(max([f[0] for f in p])) if p else 0,
                   'radius_median': round(float(np.median([f[2] for f in p])), 1) if p else 0} for i, p in enumerate(pebbles)]
json.dump(out, open(os.path.join(HERE, 'layout_fit.json'), 'w'), indent=1)
