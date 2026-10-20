# What this does (plain words): looks at the MUD colour picture and finds its palette: the handful of flat colours it is made of. It snaps every dot to the
# nearest of K palette colours (K = 8, 12, 16, 24, 32) and reports the mean colour difference (Delta E) so we know how "painted" the picture is, then saves the
# label map of K=16 (analysis only, never used by the generator) and prints how big the same-colour areas are. Plain Python (run with python3 -I).
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
img = cv2.imread(PROC + '/reference/mud/colour.png')            # BGR
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
lab_true = lab.copy(); lab_true[..., 0] *= 100 / 255.0; lab_true[..., 1:] -= 128.0   # proper Lab units
h, w = img.shape[:2]
flat = lab_true.reshape(-1, 3)
rng = np.random.default_rng(1)
sample = flat[rng.choice(len(flat), 120000, replace=False)]
report = {}
for K in (8, 12, 16, 24, 32):
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.2)
    _, lbl, centres = cv2.kmeans(sample, K, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    d = ((flat[:, None, :] - centres[None]) ** 2).sum(-1)
    idx = d.argmin(1)
    de = np.sqrt(d[np.arange(len(flat)), idx]).mean()
    report[K] = round(float(de), 2)
    print('K', K, 'mean Delta E (Lab distance)', round(float(de), 2))
    if K == 16:
        order = np.argsort(-np.bincount(idx, minlength=K))
        rgb = []
        for k in order:
            c = centres[k].astype(np.float32).reshape(1, 1, 3).copy(); c[..., 0] *= 255 / 100.0; c[..., 1:] += 128
            bgr = cv2.cvtColor(c.astype(np.uint8), cv2.COLOR_LAB2BGR)[0, 0]
            rgb.append([int(bgr[2]), int(bgr[1]), int(bgr[0])])
            print('   share %5.1f%%  rgb %s' % (100 * (idx == k).mean(), rgb[-1]))
        remap = np.zeros(K, np.int32); remap[order] = np.arange(K)
        labels = remap[idx].reshape(h, w)
        np.save('labels_k16.npy', labels.astype(np.uint8))
        json.dump({'palette_rgb_sorted_by_share': rgb, 'centres_lab': [centres[k].tolist() for k in order]}, open('palette_k16.json', 'w'))
        # same-colour area sizes
        areas = []
        for k in range(K):
            n, cc, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
            areas.append(stats[1:, cv2.CC_STAT_AREA])
        areas = np.concatenate(areas)
        print('number of same-colour areas (4-connected):', len(areas))
        for lo, hi in ((1, 4), (4, 16), (16, 64), (64, 256), (256, 1024), (1024, 4096), (4096, 10**7)):
            m = (areas >= lo) & (areas < hi)
            print('   areas of %6d..%-8d dots: %6d areas holding %5.1f%% of the picture' % (lo, hi, m.sum(), 100 * areas[m].sum() / (h * w)))
json.dump(report, open('palette_error_by_K.json', 'w'))
