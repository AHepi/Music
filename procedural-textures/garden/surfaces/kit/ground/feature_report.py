# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WRITES feature_report.json: where the strongest flag crack is in the first 12 m, so the harness can aim the close view `flag_close` at it (cameras.py reads
# report['strongest_flag_crack']['position']). Plain Python (OpenCV, numpy), no Blender: it reads the plan pictures that ground/plan_views.py draws from straight above.
#     python3 -I ground/feature_report.py PLAN_FOLDER OUT_FOLDER [first_m=12] [--min-x X] [--min-y Y]
# (--min-x / --min-y: only cracks at or beyond that position count, for a close view whose camera stands on one side and looks one way)
# PLAN_FOLDER holds plan_groundcracks_flag_fine.png, plan_groundcracks_flag_broken.png and plan_class.png (made with the same plan_info.json). The strongest crack is the longest
# connected line of fine or broken crack inside the flags of the first stretch of the picture area, away from its edges.
import json
import os
import sys

import cv2
import numpy as np


def load(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a.ndim == 3:
        a = a[..., 0]
    return a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)


def main():
    plan, out = sys.argv[1], sys.argv[2]
    opts = {sys.argv[i]: float(sys.argv[i + 1]) for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    first_m = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else 12.0
    info = json.load(open(os.path.join(plan, 'plan_info.json')))
    x0, x1 = info['ground_bounds']['x']
    y0, y1 = info['ground_bounds']['y']
    h, w = info['size'][1], info['size'][0]
    dot_x, dot_y = (x1 - x0) / w, (y1 - y0) / h
    mask = None
    for name in ('flag_fine', 'flag_broken'):
        a = load(os.path.join(plan, f'plan_groundcracks_{name}.png')) > 0.08                   # a crack is thinner than one plan pixel: partly covered pixels count
        mask = a if mask is None else (mask | a)
    classes = np.round(load(os.path.join(plan, 'plan_class.png')) * 64.0).astype(int)
    rows = np.arange(h)[:, None]
    y_of_row = y1 - (rows + 0.5) * dot_y
    band = (y_of_row >= max(0.5, opts.get('--min-y', 0.5))) & (y_of_row <= first_m - 0.5)
    x_of_col = x0 + (np.arange(w)[None, :] + 0.5) * dot_x
    band = band & (x_of_col >= opts.get('--min-x', -1e9))
    mask = cv2.dilate((mask & band).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0                    # join the pieces of one line
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    best, best_len = None, 0
    for i in range(1, n):
        length = max(stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]) * min(dot_x, dot_y)      # the longest side, in metres
        if length > best_len and stats[i, cv2.CC_STAT_AREA] >= 6:
            best, best_len = i, length
    report = {}
    if best is not None:
        cx, cy = centroids[best]
        report['strongest_flag_crack'] = dict(position=[round(float(x0 + (cx + 0.5) * dot_x), 3), round(float(y1 - (cy + 0.5) * dot_y), 3), 0.1], length_m=round(float(best_len), 2),
                                              pixels=int(stats[best, cv2.CC_STAT_AREA]), within_first_m=first_m, found_cracks=int(n - 1), source='ground/feature_report.py on the plan pictures')
    os.makedirs(out, exist_ok=True)
    json.dump(report, open(os.path.join(out, 'feature_report.json'), 'w'), indent=1)
    print(report)


if __name__ == '__main__':
    main()
