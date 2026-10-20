import sys; sys.path.insert(0, "."); sys.path.insert(0, "../generator"); sys.path.insert(0, "../../../lib")
# What this does (plain words): finds what size and strength of fine dot-to-dot grain makes a painted (flat-patch) picture look like the reference
# to the 'same kind of surface' scorer, using a quick numpy stand-in for the grain. Analysis only (reads the reference).
import json, cv2, numpy as np
import texture_compare as tc
import derive_maps as dm
import os
d = json.load(open('derivation_ceiling.json'))
maps = {'blur_sigma': 0.7, 'curve_x': d['tone_curve_and_blur']['curve_x'], 'curve_y': d['tone_curve_and_blur']['curve_y']}
ref = tc.summarise('../../../reference/brick')
base = cv2.imread('../outputs/L12/colour.png')[..., ::-1].astype(np.float64)
rng = np.random.default_rng(5)
def trial(amount, size, tag):
    noise = rng.standard_normal((1254, 1254))
    noise = dm.gaussian_blur_wrap(noise, size) if size > 0 else noise
    noise /= noise.std()
    img = np.clip(base * (1 + amount * noise[..., None]), 0, 255)
    folder = '../scores/tmp_grain'
    os.makedirs(folder, exist_ok=True)
    cv2.imwrite(folder + '/colour.png', img[..., ::-1].astype(np.uint8))
    h = dm.height_from_colour(img, maps)
    cv2.imwrite(folder + '/height.png', (h * 65535).astype(np.uint16))
    n = dm.normal_from_height(h, 6.0)
    cv2.imwrite(folder + '/normal.png', (n[..., ::-1] * 255 + .5).astype(np.uint8))
    c = tc.summarise(folder)
    dist = tc.distances(ref, c)
    keys = ['colour_gradient', 'height_gradient', 'normal_tilt', 'normal_components', 'height_spectrum', 'colour_spectrum']
    print(tag, {k: round(dist[k], 3) for k in keys}, flush=True)
trial(0.0, 0, 'none')
for size in (0.6, 1.0, 1.5):
    for amount in (0.03, 0.06, 0.10):
        trial(amount, size, f'size{size} amt{amount}')
