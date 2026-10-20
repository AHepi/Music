import sys; sys.path.insert(0, "."); sys.path.insert(0, "../generator")
import json, time, os
from region_tools import *
import derive_maps as dm
d = json.load(open('derivation_ceiling.json'))
maps = {'blur_sigma': 0.7, 'curve_x': d['tone_curve_and_blur']['curve_x'], 'curve_y': d['tone_curve_and_blur']['curve_y']}
bgr = load_reference()
nref = cv2.imread('../../../reference/brick/normal.png')[..., ::-1].astype(float) / 255 * 2 - 1
def angle(n):
    a = n * 2 - 1
    return float(np.degrees(np.arccos(np.clip((a * nref).sum(-1), -1, 1))).mean())
rows = []
for K, mode, amin, eps in [(16, 3, 20, 2.0), (16, 3, 10, 2.0), (16, 3, 6, 2.0), (24, 3, 12, 2.0), (32, 3, 12, 2.0), (16, 0, 12, 2.0)]:
    labels, centres = kmeans_labels(bgr, K, 'bilateral')
    pal = cv2.cvtColor(centres.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)
    L1 = mode_filter(labels, K, mode) if mode else labels
    L2, _ = remove_small(L1, K, amin)
    t = time.time()
    regs = trace_regions(L2, K, epsilon=eps)
    img = raster_regions(regs, pal, ss=2, background=int(np.bincount(L2.ravel()).argmax()))
    size = len(json.dumps(encode_regions(regs), separators=(',', ':')))
    s = score_colour(img, 'tmp3')
    h = dm.height_from_colour(img[..., ::-1].astype(float), maps)
    angles = {st: round(angle(dm.normal_from_height(h, float(st))), 2) for st in (3, 4, 6)}
    rows.append({'K': K, 'mode': mode, 'amin': amin, 'eps': eps, 'regions': len(regs), 'bytes': size, **s, 'normal_angle_by_strength': angles, 'seconds': round(time.time() - t, 1)})
    print(rows[-1], flush=True)
json.dump(rows, open('explore_L_normals.json', 'w'), indent=1)
