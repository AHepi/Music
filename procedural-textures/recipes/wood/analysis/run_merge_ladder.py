# What this does (plain words): the experiment for the smarter "join the least-different neighbours" tracing: builds the merge order once for the WOOD colour
# picture, then for several patch counts paints a numpy preview, makes the height and normal from it, and prints description size against every
# dot-for-dot accuracy number, so it can be compared with the plain "drop small areas" ladder (trace_ladder.py). Analysis only (reads the reference).
# Run: python3 -I run_merge_ladder.py
import json
import os
import pickle
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import merge_trace as mt  # noqa: E402
import score_tools as st  # noqa: E402
import trace_tools as tt  # noqa: E402

bgr = cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
out = os.path.join(HERE, 'merge_ladder')
os.makedirs(out, exist_ok=True)
tree_path = os.path.join(out, 'tree.pkl')
started = time.time()
comp, lab = mt.initial_regions(bgr, colour_count=32)
print('initial regions', int(comp.max()) + 1, round(time.time() - started, 1), 's', flush=True)
if os.path.exists(tree_path):
    tree = pickle.load(open(tree_path, 'rb'))
else:
    tree = mt.build_merge_tree(comp, lab)
    pickle.dump(tree, open(tree_path, 'wb'))
print('merge tree built', round(time.time() - started, 1), 's', flush=True)
rows = []
for target in [int(a) for a in sys.argv[1:]] or [30000, 15000, 8000, 4000, 2000, 1000, 400]:
    for palette_size in (48,):
        for epsilon in (0.8, 1.2):
            t0 = time.time()
            region_labels, count = mt.labels_at(comp, tree, target)
            means, area = mt.region_colours(region_labels, lab, count)
            centres, index = mt.squeeze_palette(means, area, palette_size)
            regions = mt.trace_labelled_regions(region_labels, count, index, epsilon)
            palette_bgr = tt.palette_to_bgr(centres)
            picture = tt.draw_regions(regions, palette_bgr)
            folder = os.path.join(out, 'tmp')
            st.write_folder(picture, folder)
            report = st.score_folder(folder, texture=False)
            row = dict(target=target, palette=palette_size, epsilon=epsilon, patches=len(regions), vertices=sum(len(r['p']) for r in regions),
                       kilobytes=round(tt.json_size(regions, palette_bgr.tolist()) / 1024, 1))
            for key in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached'):
                row[key] = report[key]
            row['seconds'] = round(time.time() - t0, 1)
            print(json.dumps(row), flush=True)
            rows.append(row)
            json.dump(rows, open(os.path.join(out, 'merge_ladder.json'), 'w'), indent=1)
