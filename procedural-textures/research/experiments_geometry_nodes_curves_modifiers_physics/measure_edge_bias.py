# What this does: for a height picture, prints how much stone (height above the earth level) there is in strips at distance 0-5%, 5-10%, ... from the tile edge,
# to show whether a physics pile is thinner near the seam (one-way pushing by the kinematic ghost copies) than in the middle. Also the seam ratio.
import sys, json
import numpy as np, cv2
sys.path.insert(0, 'proc-work/lib')
import texture_compare as tc
for path in sys.argv[1:]:
    h = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(float)
    h = h[..., 0] if h.ndim == 3 else h
    h /= 65535.0 if h.max() > 255 else 255.0
    earth = np.median(h)
    stone = (h > earth + 0.03).astype(float)
    n = h.shape[1]
    strips = [round(float(stone[:, int(a * n):int((a + 0.05) * n)].mean()), 3) for a in np.arange(0, 0.5, 0.05)]
    strips_y = [round(float(stone[int(a * n):int((a + 0.05) * n), :].mean()), 3) for a in np.arange(0, 0.5, 0.05)]
    # average of both sides
    sides = [round(float((stone[:, int(a * n):int((a + 0.05) * n)].mean() + stone[:, n - int((a + 0.05) * n):n - int(a * n)].mean()) / 2), 3) for a in np.arange(0, 0.5, 0.05)]
    print(path.split('/')[-2], 'seam_ratio', round(tc.seam_ratio(h), 2), 'stone fraction by distance from the left/right edge (0-5%,5-10%,...):', sides, 'overall', round(float(stone.mean()), 3))
