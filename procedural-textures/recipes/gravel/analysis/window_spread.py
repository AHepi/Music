# What this does (plain words): ANALYSIS script (reads the reference). It cuts the reference into 3 x 3 windows of 418 dots and measures, in each, the share of
# stone dots, the share of big stone (surviving a radius-16 opening), the edge density and the mean lightness. How much these differ from window to window
# tells the sampler how different two tiles of the same gravel may honestly be (it uses these spreads as the size of its random jitter).
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
sys.path.insert(0, HERE)
import preview_tools as pt
import trace_tools as tt
bgr = tt.load_reference_colour()
soil, stone = pt.soil_stone_masks(bgr)
big = pt.wrap_open(stone, 16)
big_soil = pt.wrap_open(soil, 6)
grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(grey, 50, 150) > 0
lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
rows = []
step = 418
for j in range(3):
    for i in range(3):
        sl = (slice(j * step, (j + 1) * step), slice(i * step, (i + 1) * step))
        rows.append([float(stone[sl].mean()), float(big[sl].mean()), float(big_soil[sl].mean()), float(edges[sl].mean()), float(lab[..., 0][sl].mean())])
rows = np.array(rows)
names = ['stone_share', 'big_stone_share', 'soil_clump_share', 'edge_density', 'mean_lightness']
out = {n: {'mean': float(rows[:, k].mean()), 'std': float(rows[:, k].std(ddof=1)), 'relative_spread': float(rows[:, k].std(ddof=1) / rows[:, k].mean())} for k, n in enumerate(names)}
for n, v in out.items():
    print(f'{n:18s} mean {v["mean"]:.3f}  spread {v["std"]:.3f}  relative {v["relative_spread"]*100:.1f}%')
json.dump(out, open(os.path.join(HERE, '..', 'scores', 'window_spread.json'), 'w'), indent=1)
