# What this does (plain words): compares the colour of the slate faces only (no moss, no chips, no joints) between the reference,
# the BEFORE tile and the AFTER tile, and how much the slate colour varies from slate to slate in hue (teal/green versus blue).
import cv2
import numpy as np
P = 'proc-work/'
S = {'reference': P + 'reference/slate/colour.png', 'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png', 'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
for name, path in S.items():
    bgr = cv2.imread(path)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(float)
    L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    moss = (hsv[..., 0] >= 22) & (hsv[..., 0] <= 45) & (hsv[..., 1] >= 45)
    tan = (hsv[..., 0] >= 5) & (hsv[..., 0] <= 22) & (hsv[..., 1] >= 35)
    face = (L > 14) & ~moss & ~tan & (B < 4)
    print('%-10s slate faces only: L %.1f  a* %.2f  b* %.2f  | spread L %.1f a* %.2f b* %.2f | share of face dots with b* < -4 (clearly blue): %.0f%%, with b* > 1 (green/neutral): %.0f%%' % (
        name, L[face].mean(), A[face].mean(), B[face].mean(), L[face].std(), A[face].std(), B[face].std(), (B[face] < -4).mean() * 100, (B[face] > 1).mean() * 100))
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mask = cv2.erode((grey > 30).astype(np.uint8), np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] > 5000]
    bm = []
    for i in keep:
        f = cv2.erode((labels == i).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~moss & ~tan
        if f.sum() > 1500:
            bm.append((A[f].mean(), B[f].mean()))
    bm = np.array(bm)
    print('           slate-to-slate hue: std of a* %.2f, std of b* %.2f; b* range %.1f .. %.1f' % (bm[:, 0].std(), bm[:, 1].std(), bm[:, 1].min(), bm[:, 1].max()))
