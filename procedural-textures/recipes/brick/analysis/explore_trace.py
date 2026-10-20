import sys; sys.path.insert(0, ".")
import json, time
from region_tools import *
bgr = load_reference()
K = 16
labels, centres = kmeans_labels(bgr, K, 'bilateral')
pal = cv2.cvtColor(centres.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)
L1 = mode_filter(labels, K, 3)
rows = []
for amin in (20, 80, 300):
    L2, _ = remove_small(L1, K, amin)
    t = time.time()
    for eps in (0.7, 1.2, 2.0):
        regs = trace_regions(L2, K, epsilon=eps)
        enc = encode_regions(regs)
        size = len(json.dumps(enc, separators=(',', ':')))
        verts = sum(len(r['points']) for r in regs)
        img = raster_regions(regs, pal, ss=2, background=int(np.bincount(L2.ravel()).argmax()))
        s = score_colour(img, 'tmp2')
        rows.append({'amin': amin, 'eps': eps, 'regions': len(regs), 'vertices': verts, 'bytes': size, **s, 'trace_seconds': round(time.time() - t, 1)})
        print(rows[-1], flush=True)
json.dump(rows, open('explore_trace.json', 'w'), indent=1)
