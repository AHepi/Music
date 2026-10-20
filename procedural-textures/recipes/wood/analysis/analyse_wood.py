# What this does (plain words): ANALYSIS of the wood colour picture (reads the reference; the generator never does). It measures, with numbers:
#   - the palette (24 colours: red-green-blue, share of the picture, brightness) and which "family" each belongs to (dark, rust-brown, brown, tan, grey-blue, ...);
#   - the boards: where the dark gaps run and how tall each board is;
#   - the patches: connected same-colour areas, in size classes that double each time: how many, what share of the picture, how long and how tall;
#   - the thin dark cracks (long thin very dark areas) and the round dark-brown blotches;
#   - the knots (round ring patterns): centre and ring radii.
# Output: analysis/wood_measurements.json (used to write the description and the sampler) and printed lines. Plain Python (python3 -I).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, HERE)
import trace_tools as tt  # noqa: E402

bgr = cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
H, W = bgr.shape[:2]
rgb = bgr[..., ::-1]
grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
lab = tt.srgb_to_lab_float(bgr)
report = {}

# ------------------------------------------------------------------ palette
count = 24
centres = tt.make_palette(bgr, count)
palette_bgr = tt.palette_to_bgr(centres)
labels = tt.mode_filter(tt.assign_labels(bgr, centres), count, 1)
share = np.bincount(labels.ravel(), minlength=count) / labels.size
order = np.argsort(centres[:, 0])                            # dark to light
palette_info = []
for k in order:
    L, a, b = centres[k]
    r, g, bb = int(palette_bgr[k][2]), int(palette_bgr[k][1]), int(palette_bgr[k][0])
    chroma = float(np.hypot(a, b))
    hue = float(np.degrees(np.arctan2(b, a)))
    if L < 12:
        family = 'black'
    elif chroma < 7 and L < 45:
        family = 'grey'
    elif b < 4 and L > 25 and chroma < 14:
        family = 'blue-grey'
    elif L < 30:
        family = 'dark-brown'
    elif L < 42:
        family = 'brown'
    else:
        family = 'tan'
    palette_info.append(dict(index=int(k), rgb=[r, g, bb], lab=[round(float(L), 1), round(float(a), 1), round(float(b), 1)], share=round(float(share[k]), 4), family=family))
    print(f'palette {k:2d} rgb ({r:3d},{g:3d},{bb:3d}) L {L:5.1f} a {a:5.1f} b {b:5.1f} chroma {chroma:5.1f}  share {share[k]*100:5.2f} %  family {family}')
report['palette24'] = palette_info
fam_share = {}
for p in palette_info:
    fam_share[p['family']] = fam_share.get(p['family'], 0) + p['share']
report['family_share'] = {k: round(v, 4) for k, v in fam_share.items()}
print('family shares', report['family_share'])

# ------------------------------------------------------------------ boards (dark gap rows)
dark = (grey < 35)
dark_rows = dark.mean(axis=1)
bands, start = [], None
for y in range(H):
    inside = dark_rows[y] > 0.30
    if inside and start is None:
        start = y
    if not inside and start is not None:
        bands.append((start, y - 1))
        start = None
print('gap bands (rows with over 30 % very dark dots):', bands)
report['gap_bands'] = bands
# gap centre line per column (darkest 9-row window), to see how wavy each gap is
for (y0, y1) in bands:
    centre = []
    for x in range(0, W, 62):
        col = grey[max(y0 - 12, 0):y1 + 13, x:x + 62].mean(axis=1)
        centre.append(int(max(y0 - 12, 0) + np.argmin(np.convolve(col, np.ones(7) / 7, mode='same'))))
    print(f'  gap {y0}-{y1}: centre y along x:', centre)
report['board_tops_bottoms'] = [(bands[i][1] + 1, bands[(i + 1) % len(bands)][0] - 1) for i in range(len(bands))]
print('boards between gaps:', report['board_tops_bottoms'])

# ------------------------------------------------------------------ patches by size class
class_edges = [1, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 16384, 10 ** 7]
areas_all, aspect_by_class = [], {}
rows = []
for k in range(count):
    n, comp, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        areas_all.append((area, w, h, k))
areas_all = np.array(areas_all, dtype=np.float64)
print('number of connected same-colour areas:', len(areas_all))
class_table = []
for lo, hi in zip(class_edges[:-1], class_edges[1:]):
    sel = (areas_all[:, 0] >= lo) & (areas_all[:, 0] < hi)
    if sel.sum() == 0:
        continue
    sub = areas_all[sel]
    row = dict(area_from=lo, area_to=hi, count=int(sel.sum()), share_of_picture=round(float(sub[:, 0].sum() / labels.size), 4),
               median_width=float(np.median(sub[:, 1])), median_height=float(np.median(sub[:, 2])),
               median_width_over_height=round(float(np.median(sub[:, 1] / np.maximum(sub[:, 2], 1))), 2))
    class_table.append(row)
    print(row)
report['patch_size_classes'] = class_table

# ------------------------------------------------------------------ the thin horizontal runs: how long and how tall is a run of one colour?
runs_h, runs_v = [], []
for y in range(0, H, 3):
    row = labels[y]
    change = np.flatnonzero(np.diff(row) != 0)
    edges = np.concatenate([[-1], change, [W - 1]])
    runs_h.extend(np.diff(edges))
for x in range(0, W, 3):
    col = labels[:, x]
    change = np.flatnonzero(np.diff(col) != 0)
    edges = np.concatenate([[-1], change, [H - 1]])
    runs_v.extend(np.diff(edges))
runs_h, runs_v = np.array(runs_h), np.array(runs_v)
report['runs'] = dict(horizontal_median=float(np.median(runs_h)), horizontal_area_weighted_median=float(np.sort(np.repeat(runs_h, runs_h))[len(np.repeat(runs_h, runs_h)) // 2]) if len(runs_h) < 50000 else None,
                      vertical_median=float(np.median(runs_v)))
w_h = np.sort(runs_h)
cum = np.cumsum(w_h) / w_h.sum()
w_v = np.sort(runs_v)
cum_v = np.cumsum(w_v) / w_v.sum()
report['runs']['horizontal_dot_weighted_median'] = float(w_h[np.searchsorted(cum, 0.5)])
report['runs']['vertical_dot_weighted_median'] = float(w_v[np.searchsorted(cum_v, 0.5)])
print('run lengths (same colour in a row): horizontal median', np.median(runs_h), 'dot-weighted median', report['runs']['horizontal_dot_weighted_median'],
      '; vertical median', np.median(runs_v), 'dot-weighted median', report['runs']['vertical_dot_weighted_median'])

# ------------------------------------------------------------------ cracks: very dark, long and thin
very_dark = (lab[..., 0] < 14).astype(np.uint8)
n, comp, stats, cent = cv2.connectedComponentsWithStats(very_dark, connectivity=8)
cracks = []
for i in range(1, n):
    x, y, w, h, area = stats[i]
    if area >= 40:
        cracks.append(dict(x=int(x), y=int(y), w=int(w), h=int(h), area=int(area), mean_thickness=round(float(area / max(w, h)), 2)))
cracks.sort(key=lambda c: -c['area'])
report['dark_components'] = dict(total_dark_share=round(float(very_dark.mean()), 4), components_over_40_dots=len(cracks), biggest=cracks[:25])
print('very dark (L < 14) share', round(float(very_dark.mean()), 4), '; components over 40 dots:', len(cracks))
for c in cracks[:12]:
    print('   ', c)
long_thin = [c for c in cracks if max(c['w'], c['h']) >= 60 and c['mean_thickness'] < 7]
print('long thin dark lines (cracks) at least 60 long and under 7 thick on average:', len(long_thin), ' total length', sum(max(c['w'], c['h']) for c in long_thin))
report['cracks_long_thin'] = dict(count=len(long_thin), total_length=int(sum(max(c['w'], c['h']) for c in long_thin)),
                                  median_thickness=float(np.median([c['mean_thickness'] for c in long_thin])) if long_thin else 0)

# ------------------------------------------------------------------ tone along the boards (how much do big areas change tone?)
for (y0, y1) in report['board_tops_bottoms']:
    if y1 > y0:
        board = grey[y0:y1 + 1] if y1 > y0 else None
        print(f'board rows {y0}-{y1}: mean brightness {board.mean():.1f}  spread {board.std():.1f}  tan share {(lab[y0:y1+1,:,0] > 45).mean():.3f}')
json.dump(report, open(os.path.join(HERE, 'wood_measurements.json'), 'w'), indent=1)
