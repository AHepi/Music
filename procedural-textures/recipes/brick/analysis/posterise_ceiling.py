# What this does (plain words): answers "if the colour picture were described as flat patches of only K colours, how close to the reference
# could that ever get?" It squeezes the reference colour into K colours (k-means in Lab), optionally smooths the label picture, rebuilds the
# colour picture from the K colours, makes height and normal with the derivation rule, and scores it with lib/pixel_compare.py. This is the
# ceiling for any description that is a palette plus patch shapes. Analysis only (reads the reference).
import sys, json, os
sys.path.insert(0, '../generator'); sys.path.insert(0, '../../../lib')
import numpy as np, cv2
import derive_maps as dm
import pixel_compare as pc
import texture_compare as tc
ref = cv2.imread('../../../reference/brick/colour.png')
rgb = ref[..., ::-1]
lab = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB).astype(np.float32)
d = json.load(open('derivation_ceiling.json'))
maps = {'blur_sigma': 0.7, 'curve_x': d['tone_curve_and_blur']['curve_x'], 'curve_y': d['tone_curve_and_blur']['curve_y']}
rows = []
for K in (8, 16, 32, 64, 128):
    sample = lab.reshape(-1, 3)[::7]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, centres = cv2.kmeans(sample, K, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    dist = ((lab.reshape(-1, 1, 3) - centres[None]) ** 2).sum(-1)
    labels = dist.argmin(1).reshape(1254, 1254).astype(np.uint8)
    for smooth in (0, 3):
        lab_img = labels if smooth == 0 else cv2.medianBlur(labels, smooth)
        pal_bgr = cv2.cvtColor(centres.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)
        out = pal_bgr[lab_img]
        folder = f'../scores/posterise/K{K}_s{smooth}'
        os.makedirs(folder, exist_ok=True)
        cv2.imwrite(folder + '/colour.png', out)
        h = dm.height_from_colour(out[..., ::-1].astype(np.float64), maps)
        cv2.imwrite(folder + '/height.png', (h * 65535).astype(np.uint16))
        n = dm.normal_from_height(h, 6.0)
        cv2.imwrite(folder + '/normal.png', (n[..., ::-1] * 255 + .5).astype(np.uint8))
        r = pc.pixel_report('brick', folder)
        r.pop('tier_rules')
        regions = 0
        for k in range(K):
            regions += cv2.connectedComponents((lab_img == k).astype(np.uint8))[0] - 1
        r['regions'] = int(regions)
        rows.append({'K': K, 'smooth': smooth, **{k: v for k, v in r.items() if k in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'regions')}})
        print(rows[-1], flush=True)
json.dump(rows, open('posterise_ceiling.json', 'w'), indent=1)
