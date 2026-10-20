import sys; sys.path.insert(0, ".")
# What this does (plain words): collects the plain numbers that go into analysis_findings.md: how much of the tile is mortar and how much brick, how much each palette
# colour covers on bricks and in mortar, how big the flat patches are (area spread), how thick the dark outline is, how dark the soot gets.
import json
from region_tools import *
labels = np.load('labels_k16.npy'); pal = np.load('palette_k16.npy')
W = 1254
base = json.load(open('../generator/descriptions/stage1_bricks_only.json'))
rows = base['layers'][0]['rows']
mask = np.zeros((W, W), np.uint8)
for r in rows:
    for x0, x1, c in r['bricks']:
        for dx in (-W, 0, W):
            cv2.rectangle(mask, (x0 + dx, r['y0']), (x1 + dx, r['y1']), 1, -1)
brick_share = float(mask.mean())
L1 = mode_filter(labels, 16, 3)
L2, _ = remove_small(L1, 16, 12)
ids, rl, ra = regions_of(L2, 16)
areas = ra[1:]
out = {'brick_face_share': round(brick_share, 3), 'mortar_share': round(1 - brick_share, 3),
       'palette_rgb': pal.tolist(),
       'palette_share_on_bricks': [round(float(((labels == k) & (mask > 0)).sum() / (mask > 0).sum()), 3) for k in range(16)],
       'palette_share_in_mortar': [round(float(((labels == k) & (mask == 0)).sum() / (mask == 0).sum()), 3) for k in range(16)],
       'patch_count_area_ge_12': int(len(areas)),
       'patch_area_percentiles_dots': {p: float(np.percentile(areas, p)) for p in (10, 25, 50, 75, 90, 99)},
       'area_weighted_median_patch_area': float(np.sort(areas)[np.searchsorted(np.cumsum(np.sort(areas)), areas.sum() / 2)]),
       'dark_share_luma_lt_70': float(((pal @ np.array([.299, .587, .114]))[labels] < 70).mean())}
json.dump(out, open('element_stats.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'palette_rgb'}))
