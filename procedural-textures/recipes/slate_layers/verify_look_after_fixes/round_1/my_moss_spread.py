# What this does (plain words): checks how the moss is spread across the slates: does a few slates carry thick moss clouds (like the reference),
# or does every slate carry a little scatter? Prints, per picture, the share of slates with real moss and how much of all moss sits in the 8 mossiest slates.
import cv2
import numpy as np
P = 'proc-work/'
S = {'reference': P + 'reference/slate/colour.png', 'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png', 'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
for name, path in S.items():
    bgr = cv2.imread(path)
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h_, s_, v_ = [hsv[..., k].astype(int) for k in range(3)]
    moss = (h_ >= 22) & (h_ <= 45) & (s_ >= 45) & (v_ >= 40) & (v_ <= 150)
    mask = cv2.erode((grey > 30).astype(np.uint8), np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] > 5000]
    shares = np.array([moss[labels == i].mean() * 100 for i in keep])
    total = np.array([moss[labels == i].sum() for i in keep], float)
    order = np.argsort(-total)
    print('%-10s slates %d | slates with >1%% moss: %d (%.0f%%) | >5%%: %d | top-8 slates hold %.0f%% of the moss | mossiest slate %.1f%% | median slate %.2f%%' % (
        name, len(keep), (shares > 1).sum(), (shares > 1).mean() * 100, (shares > 5).sum(), total[order[:8]].sum() / total.sum() * 100, shares.max(), np.median(shares)))
