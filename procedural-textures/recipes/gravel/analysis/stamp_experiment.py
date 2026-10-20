# What this does (plain words): analysis experiment. After tracing the big patches of the gravel picture, the many tiny same-colour specks that were dropped
# are added back as cheap "stamps" (a small disc: x, y, radius, colour = 4 numbers instead of an outline of 10-30 numbers). It reports, for several trace sizes,
# the description size and the dot-for-dot scores with and without stamps, using the quick numpy scoring (no Blender). Reads the reference (analysis only).
import json, os, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trace_tools as tt
import numpy_bake as nb

bgr = tt.load_reference_colour()
K = 24
centres = tt.make_palette(bgr, K)
palette_bgr = tt.palette_to_bgr(centres)
raw = tt.assign_labels(bgr, centres)
filtered = tt.mode_filter(raw, K, 1)
S = 4


def draw_labels_and_colour(regions, size=1254):
    big = np.zeros((size * S, size * S), np.uint8)
    for region in regions:
        pts = ((np.array(region['p'], np.float64) + 0.5) * S).round().astype(np.int32)
        cv2.fillPoly(big, [pts], int(region['c']), lineType=cv2.LINE_8)
    return big


def residual_stamps(drawn_label_big, min_area):
    drawn = cv2.resize(drawn_label_big, (1254, 1254), interpolation=cv2.INTER_NEAREST)
    stamps = []
    for k in range(K):
        mask = ((filtered == k) & (drawn != k)).astype(np.uint8)
        n, comp, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_area:
                stamps.append((area, k, float(cents[i][0]), float(cents[i][1])))
    stamps.sort(reverse=True)
    return stamps


rows = []
tmp = os.path.join(HERE, '..', 'scores', 'tmp_numpy_bake')
for trace_area in (250, 100, 50):
    cleaned = tt.remove_small_areas(filtered, K, trace_area)
    regions = tt.trace_regions(cleaned, K, 1.5, trace_area)
    kb_trace = tt.json_size(regions, palette_bgr.tolist()) / 1024
    big = np.zeros((1254 * S, 1254 * S, 3), np.uint8)
    big[:] = palette_bgr[0]
    for region in regions:
        pts = ((np.array(region['p'], np.float64) + 0.5) * S).round().astype(np.int32)
        cv2.fillPoly(big, [pts], tuple(int(v) for v in palette_bgr[region['c']]), lineType=cv2.LINE_8)
    base = cv2.resize(big, (1254, 1254), interpolation=cv2.INTER_AREA)
    rows.append(dict(trace_area=trace_area, stamps=0, kb=round(kb_trace, 1), **nb.score_picture(base, os.path.join(tmp, 'x'))))
    print(rows[-1], flush=True)
    labels_drawn = draw_labels_and_colour(regions)
    for stamp_area in (12, 6):
        stamps = residual_stamps(labels_drawn, stamp_area)
        pic = big.copy()
        for area, k, x, y in stamps:
            r = np.sqrt(area / np.pi)
            cv2.circle(pic, (int(round((x + 0.5) * S)), int(round((y + 0.5) * S))), int(round(r * S)), tuple(int(v) for v in palette_bgr[k]), -1, lineType=cv2.LINE_8)
        shrunk = cv2.resize(pic, (1254, 1254), interpolation=cv2.INTER_AREA)
        kb = kb_trace + len(stamps) * 13 / 1024
        rows.append(dict(trace_area=trace_area, stamps=len(stamps), stamp_min_area=stamp_area, kb=round(kb, 1), **nb.score_picture(shrunk, os.path.join(tmp, 'x'))))
        print(rows[-1], flush=True)
json.dump(rows, open(os.path.join(HERE, '..', 'scores', 'stamp_experiment.json'), 'w'), indent=1)
