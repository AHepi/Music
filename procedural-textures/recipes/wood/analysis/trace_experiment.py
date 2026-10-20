# What this does (plain words): tries many settings of the picture-tracing tool on the WOOD colour picture (number of palette colours, smallest area kept,
# how closely the outlines follow the dots) and prints, for each, how big the description would be and how close a numpy painter's preview gets
# (picture-structure score SSIM, mean colour difference Delta E, share of edges in place). Plain Python, analysis only.
# Run:  python3 -I trace_experiment.py [colours ...]   Output: trace_experiment/experiment_<colours>.json
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, HERE)
import pixel_compare as pc  # noqa: E402
import trace_tools as tt  # noqa: E402

bgr = cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
out = os.path.join(HERE, 'trace_experiment')
os.makedirs(out, exist_ok=True)
ref = bgr.astype(np.float64)
grey = lambda x: cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
lab_ref = pc.tc.srgb_to_lab(ref[..., ::-1] / 255.0)
ref_edges = pc.edge_map(grey(ref))
colour_counts = [int(a) for a in sys.argv[1:]] or [24]
for count in colour_counts:
    centres = tt.make_palette(bgr, count)
    palette_bgr = tt.palette_to_bgr(centres)
    raw = tt.assign_labels(bgr, centres)
    rows = []
    for radius in (0, 1):
        filtered = tt.mode_filter(raw, count, radius) if radius else raw
        for min_area in (3, 8, 20, 50, 120, 300, 800):
            cleaned = tt.remove_small_areas(filtered, count, min_area)
            for epsilon in (0.7, 1.2):
                started = time.time()
                regions = tt.trace_regions(cleaned, count, epsilon, min_area)
                picture = tt.draw_regions(regions, palette_bgr)
                cand = picture.astype(np.float64)
                lab_cand = pc.tc.srgb_to_lab(cand[..., ::-1] / 255.0)
                _, recall, f1 = pc.edge_f1(ref_edges, pc.edge_map(grey(cand)), 2)
                row = dict(colours=count, mode_radius=radius, min_area=min_area, epsilon=epsilon, patches=len(regions), vertices=sum(len(r['p']) for r in regions),
                           kilobytes=round(tt.json_size(regions, palette_bgr.tolist()) / 1024, 1), ssim=round(pc.ssim(grey(ref), grey(cand)), 3),
                           delta_e=round(float(np.sqrt(((lab_ref - lab_cand) ** 2).sum(-1)).mean()), 2), edge_f1=round(f1, 3), seconds=round(time.time() - started, 1))
                print(row, flush=True)
                rows.append(row)
    json.dump(rows, open(os.path.join(out, f'experiment_{count}.json'), 'w'), indent=1)
