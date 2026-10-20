# What this does (plain words): the honesty checker's OWN, independent (not the builder's code) quick checks that the 4 x 4 area is not the default tile repeated:
#  (a) correlation of every one of the 16 tiles of the area (height, shrunk to 1254) with the default tile of seed 1 and with the other tiles,
#  (b) correlation of the area with itself slid by exactly one tile (627 dots at 2508 across) across, down and diagonally, against slides by odd amounts (the background),
#  (c) the same for the plain repeat of the uploaded height map (control: must give 1.0).
# Use: python3 -I own_repeat_check.py
import json
import cv2
import numpy as np
BASE = 'proc-work/recipes/wood_from_displacement'
cv2.setNumThreads(1)
def grey(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    a = a[..., 0] if a.ndim == 3 else a
    return a.astype(np.float64) / (65535.0 if a.dtype == np.uint16 else 255.0)
def corr(a, b):
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))
def slide(g, dx, dy):
    h, w = g.shape
    a = g[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]
    b = g[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    return corr(a, b)
area = grey(BASE + '/area/area_4x4/height.png')
tile = grey(BASE + '/outputs/main_seed1/height.png')
out = {'what_this_is': "Honesty checker's own repeat checks (see own_repeat_check.py)."}
tiles = {}
t = area.shape[0] // 4
for j in range(4):
    for i in range(4):
        sub = area[j * t:(j + 1) * t, i * t:(i + 1) * t]
        tiles[(i, j)] = cv2.resize(sub, (1254, 1254), interpolation=cv2.INTER_AREA)
out['each_area_tile_vs_default_tile_seed1'] = {f'{i},{j}': round(corr(tiles[(i, j)], tile), 3) for (i, j) in tiles}
pairs = [corr(tiles[a], tiles[b]) for a in tiles for b in tiles if a < b]
out['tile_vs_tile_within_area_max_abs_corr_of_120_pairs'] = round(max(abs(p) for p in pairs), 3)
rng = np.random.default_rng(5)
def shifts(g, tp):
    res = {'one_tile_across': slide(g, tp, 0), 'one_tile_down': slide(g, 0, tp), 'diagonal': slide(g, tp, tp)}
    bg = []
    while len(bg) < 150:
        dx, dy = rng.integers(-3 * tp, 3 * tp, 2)
        if abs(dx) < 0.3 * tp and abs(dy) < 0.3 * tp: continue
        if min(abs(dx - tp * round(dx / tp)), 1e9) < 0.08 * tp or min(abs(dy - tp * round(dy / tp)), 1e9) < 0.08 * tp: continue
        bg.append(slide(g, int(dx), int(dy)))
    res['background_random_shift_max'] = max(bg)
    res['background_random_shift_mean'] = float(np.mean(bg))
    return {k: round(v, 3) for k, v in res.items()}
out['shift_area_4x4_height_tile_627'] = shifts(area, 627)
ref = grey('proc-work/reference/wood/height_as_uploaded.png')
plain = np.tile(cv2.resize(ref, (313, 313), interpolation=cv2.INTER_AREA), (4, 4))
out['shift_plain_repeat_control_tile_313'] = shifts(plain, 313)
json.dump(out, open(BASE + '/check_honesty/round2/own_repeat_check.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
