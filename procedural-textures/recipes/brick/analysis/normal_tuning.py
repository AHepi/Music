import sys; sys.path.insert(0, "."); sys.path.insert(0, "../generator"); sys.path.insert(0, "../../../lib")
# What this does (plain words): checks whether a different blur or strength for the DERIVED height/normal makes the normal map closer to the
# reference when the colour picture is only an approximation (it is, for every description). Reads a generated colour.png and the reference.
import json, cv2, numpy as np
import derive_maps as dm
import pixel_compare as pc
folder = sys.argv[1]
d = json.load(open('derivation_ceiling.json'))
cand = cv2.imread(folder + '/colour.png')[..., ::-1].astype(np.float64)
ref_h = cv2.imread('../../../reference/brick/height_as_uploaded.png', 0).astype(float)
ref_n = cv2.imread('../../../reference/brick/normal.png')[..., ::-1].astype(float) / 255 * 2 - 1
ref_n /= np.linalg.norm(ref_n, axis=-1, keepdims=True)
def ang(n):
    a = n * 2 - 1
    a /= np.linalg.norm(a, axis=-1, keepdims=True)
    return float(np.degrees(np.arccos(np.clip((a * ref_n).sum(-1), -1, 1))).mean())
for sigma in (0.7, 1.0, 1.5, 2.0):
    maps = {'blur_sigma': sigma, 'curve_x': d['tone_curve_and_blur']['curve_x'], 'curve_y': d['tone_curve_and_blur']['curve_y']}
    h = dm.height_from_colour(cand, maps)
    hb = float(np.abs(h * 255 - ref_h).mean())
    row = {st: round(ang(dm.normal_from_height(h, float(st))), 2) for st in (3, 4, 6, 8)}
    print('sigma', sigma, 'height mae', round(hb, 2), 'normal angle by strength', row)
