# What this file does (plain words)
# Looks at the reference slate picture ONCE to measure the general character of the dark joints and the shadow band:
# how dark the black line under a slate row is, how thick, how far the shadow band reaches below it, how bright the lip above it is,
# and how thick the dark joints between slates are. It only writes down a handful of averages. It does not trace any slate.
# Run with: python3 -I measure_reference_profile.py
import cv2
import numpy as np
import json
ROOT = 'proc-work/'
img = cv2.imread(ROOT + 'reference/slate/colour.png')
grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)   # brightness 0..255 (sRGB)
h, w = grey.shape
# ---- horizontal black band: for each column find runs of dark dots (< 22) that are 5..22 dots long, remember where they start
profiles = []
core_lengths = []
for x in range(0, w):
    col = grey[:, x]
    dark = col < 22
    y = 0
    while y < h:
        if dark[y]:
            y0 = y
            while y < h and dark[y]:
                y += 1
            length = y - y0
            if 6 <= length <= 22 and 45 < y0 < h - 70:
                core_lengths.append(length)
                profile = col[y0 - 30:y0 + length + 45]
                # align: store as function of distance above the core top (negative) and below the core bottom (positive)
                profiles.append((length, y0, col[y0 - 30:y0].copy(), col[y:y + 45].copy()))
        else:
            y += 1
print('columns with a clean black core:', len(profiles), ' median core length', np.median(core_lengths))
above = np.array([p[2] for p in profiles])          # 30 values above the core, last one touches the core
below = np.array([p[3] for p in profiles])          # 45 values below the core, first one touches the core
print('above the core (30 dots up to the core), median brightness at distance 1,2,3,4,6,8,12,20,30:')
for d in (1, 2, 3, 4, 6, 8, 12, 20, 30):
    print(f'  {d:3d}', round(float(np.median(above[:, -d])), 1))
print('below the core, median brightness at distance 1,2,4,6,8,10,14,18,22,26,30,40:')
for d in (1, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 40):
    print(f'  {d:3d}', round(float(np.median(below[:, d - 1])), 1))
# slate body brightness (median of all dots that are not dark): the shadow band depth is measured against it
body = float(np.median(grey[grey > 30]))
print('median brightness of everything not dark:', round(body, 1))
# ---- vertical joints: for each row of dots find dark runs 2..12 dots wide between dots of the slate body (not on the horizontal band)
widths = []
for y in range(0, h):
    row = grey[y, :]
    dark = row < 26
    x = 0
    while x < w:
        if dark[x]:
            x0 = x
            while x < w and dark[x]:
                x += 1
            L = x - x0
            if 2 <= L <= 12 and x0 > 5 and x < w - 5:
                # must be a vertical line: dark also 8 dots above and below
                if y > 8 and y < h - 8 and grey[y - 8, x0:x].mean() < 40 and grey[y + 8, x0:x].mean() < 40:
                    widths.append(L)
        else:
            x += 1
print('vertical joint dark width (dots): median', np.median(widths), ' 10th..90th percentile', np.percentile(widths, [10, 90]), ' count', len(widths))
# ---- slate edge darkening: brightness of slate dots by distance to the nearest dark dot (<26), excluding the horizontal band region
dark_mask = (grey < 26).astype(np.uint8)
dist = cv2.distanceTransform(1 - dark_mask, cv2.DIST_L2, 3)
non_dark = grey > 26
print('brightness by distance from a dark (joint/shadow) dot:')
for d0, d1 in ((1, 2), (2, 4), (4, 6), (6, 9), (9, 14), (14, 22), (22, 35), (35, 60)):
    sel = non_dark & (dist >= d0) & (dist < d1)
    print(f'  {d0:3d}-{d1:3d} dots: median {np.median(grey[sel]):.1f}  mean {grey[sel].mean():.1f}')
out = {'core_length_median': float(np.median(core_lengths)),
       'vertical_joint_width_median': float(np.median(widths))}
json.dump(out, open(ROOT + 'recipes/slate_layers/outline_work/reference_profile_measure.json', 'w'), indent=1)
