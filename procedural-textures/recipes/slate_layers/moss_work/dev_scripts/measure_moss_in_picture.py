# What this file does (plain words): the same measurements as measure_reference_moss.py, but on ANY picture given on the command line (so the baked tile can be compared with the reference by the same numbers).
# Use: python3 -I measure_moss_in_picture.py PICTURE.png
# Run with:  python3 -I measure_reference_moss.py
import json
import cv2
import numpy as np

import sys
REF = sys.argv[1]
bgr = cv2.imread(REF)
N = bgr.shape[0]                      # the picture size in dots; lengths are reported as if the picture were 1254 dots
SCALE = 1254.0 / N
rgb = bgr[:, :, ::-1].astype(np.float32)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
bright = rgb.mean(axis=2)
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)   # H 0..179
hue, sat, val = hsv[..., 0] * 2.0, hsv[..., 1] / 255.0, hsv[..., 2]

dark = bright < 28   # joints
# olive moss: green >= blue + 6 and red close to green (yellow-green hue 45..90 deg)
olive = (hue > 45) & (hue < 95) & (sat > 0.16) & (~dark)
# tan lichen: hue 20..45, warm, bright
tan = (hue >= 15) & (hue <= 45) & (sat > 0.10) & (bright > 80) & (~dark)
slate = ~dark
print('share of all dots: olive %.3f  tan %.3f  joint-dark %.3f' % (olive.mean(), tan.mean(), dark.mean()))
print('share of slate dots: olive %.3f tan %.3f' % (olive.sum() / slate.sum(), tan.sum() / slate.sum()))

def families(mask, k):
    data = rgb[mask]
    if len(data) < 100:
        return []
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    sample = data[np.random.RandomState(0).choice(len(data), min(60000, len(data)), replace=False)]
    _, labels, centres = cv2.kmeans(sample, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    order = np.argsort(-counts)
    return [(tuple(int(round(v)) for v in centres[i]), round(float(counts[i]) / counts.sum(), 3), int(round(centres[i].mean()))) for i in order]

print('olive families (rgb, share, brightness):', families(olive, 5))
print('tan families:', families(tan, 3))

# clump sizes (connected pieces of olive, after closing 1 dot gaps)
m = cv2.morphologyEx(olive.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, stats, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
areas = stats[1:, cv2.CC_STAT_AREA]
w = stats[1:, cv2.CC_STAT_WIDTH]; h = stats[1:, cv2.CC_STAT_HEIGHT]
big = areas > 150
print('olive pieces over 150 dots: %d ; area-weighted median width %.0f height %.0f ; median h/w %.2f' % (
    big.sum(), np.median(np.repeat(w[big], areas[big] // 50)), np.median(np.repeat(h[big], areas[big] // 50)), np.median(h[big] / w[big])))
print('area percentiles (dots): ', np.percentile(areas[big], [10, 50, 90, 99]).tolist())
# tan discs
mt = cv2.morphologyEx(tan.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
nt, labt, st, ct = cv2.connectedComponentsWithStats(mt, connectivity=8)
at = st[1:, cv2.CC_STAT_AREA]
print('tan pieces: %d, area percentiles %s' % (len(at), np.percentile(at, [10, 50, 90, 99]).tolist()))

# where on the slate: use the row period 156.75 and find the joint band (darkest row average) to know the top of a slate
profile = dark.mean(axis=1)
period = N / 8.0
best, best_off = -1, 0
for off in range(int(period)):
    idx = (np.arange(N) - off) % period
    score = profile[idx < 6 / SCALE].mean()
    if score > best:
        best, best_off = score, off
frac = ((np.arange(N) - best_off) % period) / period       # 0 at the start of the dark band; slate body is roughly 0.07..1
row_pos = np.repeat(frac[:, None], N, axis=1)
bins = np.linspace(0, 1, 11)
olive_share, tan_share = [], []
for i in range(10):
    sel = (row_pos >= bins[i]) & (row_pos < bins[i + 1]) & slate
    olive_share.append(round(float(olive[sel].mean()), 3)); tan_share.append(round(float(tan[sel].mean()), 3))
print('olive share by tenth of the row (top -> bottom of row, band offset %d): %s' % (best_off, olive_share))
print('tan   share by tenth of the row: %s' % tan_share)

# drip length: run length (down) of olive columns that start in the top 40% of a slate
runs = []
for x in range(0, N, 2):
    col = olive[:, x]
    y = 0
    while y < N:
        if col[y]:
            s = y
            while y < N and col[y]:
                y += 1
            runs.append(y - s)
        y += 1
runs = np.array(runs) * SCALE
print('vertical run of olive: percentiles 50/75/90/99 =', np.percentile(runs, [50, 75, 90, 99]).tolist())
hruns = []
for y in range(0, N, 2):
    row = olive[y, :]
    x = 0
    while x < N:
        if row[x]:
            s = x
            while x < N and row[x]:
                x += 1
            hruns.append(x - s)
        x += 1
print('horizontal run of olive: percentiles 50/75/90/99 =', (np.percentile(hruns, [50, 75, 90, 99]) * SCALE).tolist())
# how patchy: share of olive per 1/6 x 1/8 block
bh, bw = N // 8, N // 6
shares = np.array([olive[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw].mean() for i in range(8) for j in range(6)])
print('olive share per block (48 blocks): mean %.3f, std %.3f, share of blocks under 2%%: %.2f, over 15%%: %.2f' % (shares.mean(), shares.std(), (shares < 0.02).mean(), (shares > 0.15).mean()))
