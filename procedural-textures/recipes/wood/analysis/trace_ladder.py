# What this does (plain words): for the WOOD colour picture, traces it at many settings (palette size, smallest patch kept, outline looseness), paints a
# numpy preview of each, makes the height and normal pictures from the preview the same way the reference ones were made, and scores it with the
# dot-for-dot tool. Prints one line per setting: description size in kilobytes against every accuracy number. It shows how many bytes each
# step of accuracy costs. Plain Python (python3 -I); analysis only (it reads the reference).  Run: python3 -I trace_ladder.py 24 [more colour counts]
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import score_tools as st  # noqa: E402
import trace_tools as tt  # noqa: E402

bgr = cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
out = os.path.join(HERE, 'trace_ladder')
os.makedirs(out, exist_ok=True)
for count in [int(a) for a in sys.argv[1:]] or [24]:
    centres = tt.make_palette(bgr, count)
    palette_bgr = tt.palette_to_bgr(centres)
    raw = tt.assign_labels(bgr, centres)
    rows = []
    for min_area in (6, 10, 16, 24, 40, 80):
        cleaned = tt.remove_small_areas(raw, count, min_area)
        for epsilon in (0.8, 1.2, 1.8):
            started = time.time()
            regions = tt.trace_regions(cleaned, count, epsilon, min_area)
            picture = tt.draw_regions(regions, palette_bgr)
            folder = os.path.join(out, 'tmp')
            st.write_folder(picture, folder)
            report = st.score_folder(folder, texture=False)
            row = dict(colours=count, min_area=min_area, epsilon=epsilon, patches=len(regions), vertices=sum(len(r['p']) for r in regions),
                       kilobytes=round(tt.json_size(regions, palette_bgr.tolist()) / 1024, 1))
            for key in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached'):
                row[key] = report[key]
            row['seconds'] = round(time.time() - started, 1)
            print(json.dumps(row), flush=True)
            rows.append(row)
    json.dump(rows, open(os.path.join(out, f'ladder_{count}.json'), 'w'), indent=1)
