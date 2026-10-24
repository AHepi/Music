# What this does (plain words): my own check of how straight the horizontal dark bands (the shadow band between two rows) run across the tile.
# For each band it finds the up-down centre of the dark dots in every column, ignores columns where an upright joint crosses the band, and
# reports how much that centre wanders: the standard deviation of the centre after removing a straight-line trend, and the biggest
# up-down jump between neighbouring columns (steps where one slate sits higher than the next). Reference, BEFORE and AFTER.
# Use: python3 -I my_row_wander_check.py   (prints a table, writes my_row_wander_check.json)
import json
import cv2
import numpy as np
P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
SETS = {'reference': P + 'reference/slate/colour.png',
        'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png',
        'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
res = {}
for name, path in SETS.items():
    g = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY).astype(float)
    dark = (g < 24)
    profile = dark.sum(axis=1).astype(float)
    profile = cv2.GaussianBlur(profile.reshape(-1, 1), (1, 0), 3).ravel()
    peaks = [y for y in range(25, g.shape[0] - 25) if profile[y] == profile[y - 20:y + 21].max() and profile[y] > 0.45 * g.shape[1]]
    wanders, jumps = [], []
    for y0 in peaks:
        win = dark[y0 - 22:y0 + 23, :]
        centres = np.full(g.shape[1], np.nan)
        for x in range(g.shape[1]):
            col = win[:, x]
            if col.sum() >= 6 and col.sum() < 40:           # a band is 6-39 dots tall; 40+ means an upright joint is crossing
                centres[x] = np.average(np.arange(len(col)), weights=col.astype(float))
        ok = ~np.isnan(centres)
        if ok.sum() < 700:
            continue
        xs = np.arange(len(centres))[ok]
        coef = np.polyfit(xs, centres[ok], 1)
        wanders.append(float(np.std(centres[ok] - np.polyval(coef, xs))))
        smooth = np.convolve(centres[ok], np.ones(9) / 9, mode='valid')
        jumps.append(float(np.max(np.abs(np.diff(smooth)))))
    res[name] = {'bands_found': len(wanders), 'band_centre_wander_std_dots': round(float(np.mean(wanders)), 2),
                 'biggest_step_between_neighbour_columns_dots': round(float(np.mean(jumps)), 2)}
json.dump(res, open('my_row_wander_check.json', 'w'), indent=1)
for k, v in res.items():
    print(k, v)
