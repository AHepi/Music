# What this does (plain words): analysis experiment. For a few palette sizes, smallest-patch sizes and outline tolerances it traces the gravel
# colour picture into flat polygons, draws them back to front, and reports the size of the list (KB) and how close the drawing is (SSIM, Delta E).
# It is the "tracing the picture" end of the rate-distortion curve. Reads the reference (analysis only).
import json, os, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'lib'))
import trace_tools as tt
import pixel_compare as pc

bgr = tt.load_reference_colour()
rows = []
grey = lambda x: cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
ref = bgr.astype(np.float64)
lab_ref = pc.tc.srgb_to_lab(ref[..., ::-1] / 255.0)
for count in (16, 24):
    centres = tt.make_palette(bgr, count)
    palette_bgr = tt.palette_to_bgr(centres)
    raw = tt.assign_labels(bgr, centres)
    filtered = tt.mode_filter(raw, count, 1)
    for min_area in (12, 30, 80, 250):
        cleaned = tt.remove_small_areas(filtered, count, min_area)
        for epsilon in (1.0, 1.6):
            started = time.time()
            regions = tt.trace_regions(cleaned, count, epsilon, min_area)
            picture = tt.draw_regions(regions, palette_bgr)
            cand = picture.astype(np.float64)
            lab_c = pc.tc.srgb_to_lab(cand[..., ::-1] / 255.0)
            de = float(np.sqrt(((lab_ref - lab_c) ** 2).sum(-1)).mean())
            row = dict(colours=count, min_area=min_area, epsilon=epsilon, patches=len(regions), vertices=sum(len(r['p']) for r in regions),
                       kilobytes=round(tt.json_size(regions, palette_bgr.tolist()) / 1024, 1), ssim=round(pc.ssim(grey(ref), grey(cand)), 3),
                       delta_e=round(de, 2), seconds=round(time.time() - started, 1))
            print(row, flush=True)
            rows.append(row)
json.dump(rows, open(os.path.join(HERE, '..', 'scores', 'trace_experiment.json'), 'w'), indent=1)
