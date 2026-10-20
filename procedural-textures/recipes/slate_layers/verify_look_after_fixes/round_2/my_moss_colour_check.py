# What this does (plain words): my own check of how much olive moss each tile shows and how strongly coloured it is.
# For slate-face dots (lighter than L 9, away from joints) it reports the share with a yellow tint (Lab b* above 0, above 4, above 8),
# the average colour of the dots my moss rule picks (Lab b* above 5 and a* below 2), and the share of slates (whole slate faces) that carry
# more than 1 % / 5 % / 15 % moss. Reference, BEFORE and AFTER side by side.
# Use: python3 -I my_moss_colour_check.py   (prints a table, writes my_moss_colour_check.json)
import json
import cv2
import numpy as np
P = 'proc-work/'
SETS = {'reference': P + 'reference/slate/colour.png',
        'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png',
        'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
res = {}
for name, path in SETS.items():
    rgb = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(float)
    light, a, b = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
    mask = (light > 9).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    face = cv2.erode(mask, np.ones((9, 9), np.uint8)).astype(bool)
    n = face.sum()
    out = {}
    for t in (0, 4, 8):
        out['slate_dots_with_b*_above_%d_%%' % t] = round(float((b[face] > t).sum() / n * 100), 2)
    moss = face & (b > 5) & (a < 2) & (light < 45)
    out['moss_rule_share_%'] = round(float(moss.sum() / n * 100), 2)
    out['moss_mean_Lab'] = [round(float(light[moss].mean()), 1), round(float(a[moss].mean()), 1), round(float(b[moss].mean()), 1)]
    out['moss_mean_chroma'] = round(float(np.hypot(a[moss], b[moss]).mean()), 2)
    out['slate_face_mean_Lab'] = [round(float(light[face].mean()), 1), round(float(a[face].mean()), 2), round(float(b[face].mean()), 2)]
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    shares = []
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] > 4000:
            sl = cv2.erode((labels == i).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
            if sl.sum() > 1500:
                shares.append((moss & sl).sum() / sl.sum() * 100)
    shares = np.array(shares)
    out['slates_counted'] = len(shares)
    for t in (1, 5, 15):
        out['slates_with_moss_over_%d%%_(share of slates)' % t] = round(float((shares > t).mean() * 100), 1)
    out['most_mossy_slate_%'] = round(float(shares.max()), 1)
    res[name] = out
json.dump(res, open('my_moss_colour_check.json', 'w'), indent=1)
keys = list(res['reference'].keys())
print('measure'.ljust(52) + ''.join(k.rjust(22) for k in res))
for k in keys:
    print(k.ljust(52) + ''.join(str(res[n][k]).rjust(22) for n in res))
