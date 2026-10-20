# What this does (plain words): ANALYSIS. Picks a small "shape library" of REAL patch outlines from the trace of the reference: k outlines of paint patches,
# each simplified to at most 10 corners and written as whole numbers from -50 to 50 across its own bounding box (so it can be stretched to any wanted width
# and height). The generator can then stamp these real outlines instead of the made-up drips (paint.shape = "library"). The library is part of the
# DESCRIPTION (it is shape data, about 2 KB), so the generator still never reads the reference. Writes analysis/shape_library.json.
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
trace = json.load(open(os.path.join(HERE, 'trace_full.json')))
rng = np.random.default_rng(7)
K = int(sys.argv[1]) if len(sys.argv) > 1 else 32
candidates = [p for p in trace['patches'] if 60 <= p['area'] <= 4000 and len(p['p']) >= 6]
bands = [(60, 150), (150, 400), (400, 1000), (1000, 4000)]
per_band = [K // 4] * 4
library = []
for (lo, hi), n in zip(bands, per_band):
    pool = [p for p in candidates if lo <= p['area'] < hi]
    for index in rng.choice(len(pool), min(n, len(pool)), replace=False):
        pts = np.array(pool[index]['p'], np.float64)
        low, high = pts.min(0), pts.max(0)
        size = np.maximum(high - low, 1.0)
        unit = ((pts - low) / size - 0.5) * 100.0                      # -50 .. 50 across the bounding box
        epsilon = 2.0
        simple = unit
        for epsilon in (2.0, 3.0, 4.5, 6.5, 9.0, 12.0):
            simple = cv2.approxPolyDP(unit.astype(np.float32).reshape(-1, 1, 2), epsilon, True)[:, 0, :]
            if len(simple) <= 10:
                break
        library.append({'a': round(float(size[1] / size[0]), 2), 'p': [int(round(v)) for v in simple.ravel()]})
json.dump(library, open(os.path.join(HERE, 'shape_library.json'), 'w'), separators=(',', ':'))
print(len(library), 'shapes,', os.path.getsize(os.path.join(HERE, 'shape_library.json')), 'bytes')
