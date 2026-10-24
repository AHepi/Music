# What this does (plain words): my own check of how "busy" the lower rim of the slates is. For every slate it takes the band of dots from 12 dots
# above to 3 dots below the lowest slate dot in each column, and measures (1) the average step in lightness from one column to the next
# (fine speckle along the rim) and (2) the share of rim dots that are warm orange-pink (Lab a* above 3 and b* above 5) as opposed to cream/grey.
# Reference, BEFORE and AFTER. Higher "step" = a more frayed, speckled-looking rim.
# Use: python3 -I my_rim_texture_check.py   (prints a table, writes my_rim_texture_check.json)
import json
import cv2
import numpy as np
P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
SETS = {'reference': P + 'reference/slate/colour.png',
        'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png',
        'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
res = {}
for name, path in SETS.items():
    rgb = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(float)
    light, a, b = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
    mask = cv2.morphologyEx((light > 9).astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    steps, warm, tot = [], 0, 0
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] < 4000:
            continue
        x0, y0, w, h = stats[i, :4]
        if w < 100 or x0 <= 2 or y0 <= 2 or x0 + w >= 1252 or y0 + h >= 1252:
            continue
        sub = labels[y0:y0 + h, x0:x0 + w] == i
        for c in range(int(w * 0.15), int(w * 0.85)):
            rows = np.where(sub[:, c])[0]
            if len(rows) == 0:
                continue
            yb = y0 + rows.max()
            band_l = light[yb - 12:yb + 4, x0 + c]
            band_next = light[yb - 12:yb + 4, x0 + c + 1]
            steps.append(np.abs(band_l - band_next).mean())
            band_a, band_b = a[yb - 12:yb + 1, x0 + c], b[yb - 12:yb + 1, x0 + c]
            warm += int(((band_a > 3) & (band_b > 5)).sum())
            tot += len(band_a)
    res[name] = {'rim_column_to_column_lightness_step': round(float(np.mean(steps)), 2),
                 'rim_dots_warm_orange_pink_%': round(warm / tot * 100, 2)}
json.dump(res, open('my_rim_texture_check.json', 'w'), indent=1)
for k, v in res.items():
    print(k, v)
