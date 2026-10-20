# What this does (plain words): ANALYSIS script (reads the reference picture; the generator never does). Builds the TRACED gravel descriptions that have two parts:
# (1) patches: outlines of the big same-colour areas (first corner, then small steps), and (2) stamps: the many tiny specks that are too small to outline, each
# written as just x, y, radius (in half dots) under its colour, in size bands (big first). The stamps are found as the dots where the drawn patches still
# disagree with the palette-snapped picture. Sizes: M (<= 64 KB) and L (<= 512 KB). Run: python3 -I make_trace_stamp_descriptions.py [name ...]
import json, os, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trace_tools as tt

OUT = os.path.join(HERE, '..', 'description')
bgr = tt.load_reference_colour()
K = 24
centres = tt.make_palette(bgr, K)
palette_bgr = tt.palette_to_bgr(centres)
palette_rgb = palette_bgr[:, ::-1].astype(int).tolist()
raw = tt.assign_labels(bgr, centres)
filtered = tt.mode_filter(raw, K, 1)
share = np.bincount(filtered.ravel(), minlength=K)
ground = palette_rgb[int(share.argmax())]
S = 4
# name, smallest patch kept, outline tolerance, smallest stamp
variants = [('M_a600_s40', 600, 2.0, 40), ('M_a600_s120', 600, 2.0, 120), ('M_a400_s100', 400, 1.8, 100), ('L_a250_s12', 250, 1.6, 12), ('L_a250_s8', 250, 1.6, 8), ('L_a100_s12', 100, 1.5, 12), ('L_a100_s8', 100, 1.5, 8),
            ('L_a150_s7', 150, 1.5, 7)]
if len(sys.argv) > 1:
    variants = [v for v in variants if v[0] in sys.argv[1:]]
for name, min_area, epsilon, stamp_min in variants:
    started = time.time()
    cleaned = tt.remove_small_areas(filtered, K, min_area)
    regions = tt.trace_regions(cleaned, K, epsilon, min_area)
    big = np.zeros((1254 * S, 1254 * S), np.uint8)
    for region in regions:
        cv2.fillPoly(big, [((np.array(region['p'], np.float64) + 0.5) * S).round().astype(np.int32)], int(region['c']), lineType=cv2.LINE_8)
    drawn = cv2.resize(big, (1254, 1254), interpolation=cv2.INTER_NEAREST)
    stamps = []
    for k in range(K):
        mask = ((filtered == k) & (drawn != k)).astype(np.uint8)
        n, comp, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for i in range(1, n):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area >= stamp_min:
                stamps.append((area, k, int(round(cents[i][0])), int(round(cents[i][1])), int(round(2 * np.sqrt(area / np.pi)))))
    stamps.sort(reverse=True)
    edges = [10 ** 9, 200, 60, 25, 0]          # size bands (dots of area), big stamps first
    bands = []
    for hi, lo in zip(edges[:-1], edges[1:]):
        band = {}
        for area, k, x, y, r2 in stamps:
            if lo <= area < hi:
                band.setdefault(str(k), []).extend([x, y, r2])
        if band:
            bands.append(band)
    patches = []
    for region in regions:
        pts = np.array(region['p'], dtype=int)
        patches.append([region['c'], np.concatenate([pts[:1], np.diff(pts, axis=0)], axis=0).ravel().tolist()])
    description = {'format': 'gravel_painter_1', 'tile': 1254, 'ground': ground, 'palette': palette_rgb, 'order': ['patches', 'stamps'], 'grow': 0.5,
                   'maps': {'height': {'mix': [267.15, 91.48, 210.5], 'offset': -17.7, 'blur': 0.5}, 'normal': {'strength': 10}}, 'patches': patches, 'stamps': bands}
    text = json.dumps(description, separators=(',', ':'))
    open(os.path.join(OUT, name + '.json'), 'w').write(text)
    print(name, 'patches', len(patches), 'stamps', len(stamps), 'KB', round(len(text) / 1024, 1), 'seconds', round(time.time() - started, 1), flush=True)
