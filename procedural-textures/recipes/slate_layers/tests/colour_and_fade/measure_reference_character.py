# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# A ONE-TIME look at the reference slate picture to choose the DEFAULT SETTINGS of the COLOUR AND FADE layer. It measures only general
# character (never one particular slate or patch): the blue-grey palette (which colours, how bright, how common), how the tone of the
# blue-grey paint changes from the top of a slate to its bottom (the fade), and how far apart neighbouring slates are in tone.
# It does NOT feed anything into the recipe: the numbers are read by a person (me), who then types rounded values into the layer's
# CONTROLS by hand. Run with the system python (python3 -I): it reads reference/slate/colour.png and writes character.json and prints.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
image = cv2.imread(os.path.join(PROC, 'reference', 'slate', 'colour.png'))            # BGR, 8 bit
rgb = image[:, :, ::-1].astype(np.float32) / 255.0
lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)                                            # L 0..100, a, b
grey = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) * 255.0      # "brightness" 0..255 (sRGB numbers)

# which dots are blue-grey slate paint? not joint-black (grey < 24), not moss/lichen (yellowish: b* high)
body = (grey > 24) & (lab[..., 2] < 4.0)
print('blue-grey share of all dots:', float(body.mean()))
print('brightness percentiles of blue-grey dots (1, 10, 25, 50, 75, 90, 99):', np.percentile(grey[body], [1, 10, 25, 50, 75, 90, 99]).round(1).tolist())

# palette by k-means in Lab (a handful of colours)
dots = lab[body].reshape(-1, 3)
rng = np.random.default_rng(0)
sample = dots[rng.choice(len(dots), 60000, replace=False)]
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.5)
results = {}
for k in (8, 10, 12):
    _, labels, centres = cv2.kmeans(sample, k, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
    shares = np.bincount(labels.ravel(), minlength=k) / len(sample)
    rgb_centres = cv2.cvtColor(centres.reshape(1, k, 3).astype(np.float32), cv2.COLOR_Lab2RGB).reshape(k, 3)
    order = np.argsort(centres[:, 0])
    entries = []
    for index in order:
        r, g, b = (np.clip(rgb_centres[index], 0, 1) * 255).round().astype(int)
        entries.append({'hex': f'#{r:02x}{g:02x}{b:02x}', 'share': round(float(shares[index]), 3), 'L': round(float(centres[index][0]), 1),
                        'a': round(float(centres[index][1]), 1), 'b': round(float(centres[index][2]), 1)})
    results[k] = entries
    print(f'--- {k} colours (dark to light)')
    for e in entries:
        print('  ', e)

# the top-to-bottom change of tone inside slates: the joints are dark lines; between two rows' bands we cut the rows using the dark band
# rows by the horizontal dark bands (average darkness per picture row)
row_mean = grey.mean(axis=1)
smooth = np.convolve(np.r_[row_mean[-15:], row_mean, row_mean[:15]], np.ones(9) / 9, mode='same')[15:-15]
minima = [y for y in range(1, 1253) if smooth[y] < smooth[y - 1] and smooth[y] <= smooth[y + 1] and smooth[y] < np.percentile(smooth, 30)]
# keep one minimum per 156 dots
rows, last = [], -999
for y in minima:
    if y - last > 100:
        rows.append(y)
        last = y
print('row bands found at y =', rows)
profile = []
for a, b in zip(rows[:-1], rows[1:]):
    segment = grey[a + 12:b - 8, :]
    mask = body[a + 12:b - 8, :]
    height = segment.shape[0]
    values = []
    for step in range(10):
        s, e = int(step * height / 10), int((step + 1) * height / 10)
        m = mask[s:e]
        values.append(float(segment[s:e][m].mean()) if m.any() else float('nan'))
    profile.append(values)
profile = np.nanmean(np.array(profile), axis=0)
print('mean blue-grey brightness in ten bands from the top of a slate to its bottom:', profile.round(1).tolist())
print('top-to-bottom rise (last band minus first):', round(float(profile[-1] - profile[0]), 1))
json.dump({'palette': results, 'top_to_bottom_profile': profile.round(2).tolist()}, open(os.path.join(HERE, 'character.json'), 'w'), indent=1)
