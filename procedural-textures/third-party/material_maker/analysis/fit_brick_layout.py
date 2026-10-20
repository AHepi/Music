# Plain note: ANALYSE step for the brick reference. Finds every brick (position, size, average colour) in the reference picture and writes
# a short description file (brick_layout.json): the row boundaries (as fractions of the tile) and, for each row, the positions of the
# vertical mortar joints, plus every brick's average colour. Also writes a picture of the fitted bricks to check by eye and prints how well
# redrawing them matches the reference's mortar picture (overlap score).
# Method: mortar = grey-brown dots (low colour strength). Horizontal mortar lines = peaks of the row profile; vertical joints = peaks of the
# column profile inside each row. (Everything is treated as wrapping round the tile edges.)
# Run: python3 -I fit_brick_layout.py OUT_FOLDER
import sys, os, json
import numpy as np, cv2
REF = 'proc-work/reference/brick/colour.png'
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
img = cv2.imread(REF)
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
s, v = hsv[..., 1] / 255, hsv[..., 2] / 255
mortar = ((s < 0.42) & (v > 0.30)).astype(np.uint8)
mortar = cv2.morphologyEx(mortar, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
mortar = cv2.morphologyEx(mortar, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))


def runs_circular(profile, thresh):
    """return list of (start, end) of stretches where profile > thresh, on a circle (end may exceed len)"""
    n = len(profile)
    above = profile > thresh
    if above.all() or not above.any():
        return []
    start = int(np.argmin(above))  # first False
    idx = [(start + i) % n for i in range(n)]
    runs, cur = [], None
    for k, i in enumerate(idx):
        if above[i] and cur is None:
            cur = k
        if (not above[i]) and cur is not None:
            runs.append((idx[cur] if True else 0, k - cur, idx[cur]))
            cur = None
    if cur is not None:
        runs.append((idx[cur], len(idx) - cur, idx[cur]))
    return [(r[0], r[1]) for r in runs]  # (first index, length)


def smooth_circ(a, k):
    ker = np.ones(k) / k
    ext = np.r_[a[-k:], a, a[:k]]
    return np.convolve(ext, ker, 'same')[k:-k]


# 1. horizontal mortar lines
rowfrac = smooth_circ(mortar.mean(axis=1), 5)
hruns = [r for r in runs_circular(rowfrac, 0.45) if 8 <= r[1] <= 45]
hlines = sorted((r[0] + r[1] / 2.0) % H for r in hruns)
hthick = float(np.median([r[1] for r in hruns]))
print('horizontal mortar lines:', len(hlines), 'at', [int(y) for y in hlines], '| typical thickness px', hthick)
# 2. rows between lines; vertical joints in each row
bricks = []
nlines = len(hlines)
for k in range(nlines):
    y_top_line = hlines[k]
    y_bot_line = hlines[(k + 1) % nlines] + (H if k + 1 == nlines else 0)
    y0 = y_top_line + hthick / 2.0
    y1 = y_bot_line - hthick / 2.0
    # row band interior (rows with wrap)
    ys = (np.arange(int(y0) + 4, int(y1) - 4) % H)
    prof = smooth_circ(mortar[ys].mean(axis=0), 5)
    vr = [r for r in runs_circular(prof, 0.40) if 8 <= r[1] <= 50]
    joints = sorted(((r[0] + r[1] / 2.0) % W, r[1]) for r in vr)
    for j in range(len(joints)):
        xa, wa = joints[j]
        xb, wb = joints[(j + 1) % len(joints)]
        if j + 1 == len(joints):
            xb += W
        bx0, bx1 = xa + wa / 2.0, xb - wb / 2.0
        if bx1 - bx0 < 60:
            continue
        # average colour of the brick area (shrunk 6 px)
        xs = (np.arange(int(bx0) + 6, int(bx1) - 6) % W)
        yy = (np.arange(int(y0) + 6, int(y1) - 6) % H)
        patch = img[np.ix_(yy, xs)][..., ::-1].reshape(-1, 3).mean(axis=0) / 255.0
        bricks.append({'row': k, 'x0': round(bx0 / W, 4), 'x1': round(bx1 / W, 4), 'y0': round(y0 / H, 4), 'y1': round(y1 / H, 4), 'rgb': [round(float(c), 3) for c in patch]})
mean_mortar = img[mortar == 1][:, ::-1].mean(axis=0) / 255.0
desc = {'tile_px': W, 'rows': nlines, 'brick_count': len(bricks), 'mortar_rgb': [round(float(c), 3) for c in mean_mortar], 'horizontal_mortar_thickness_px': hthick, 'bricks': bricks}
json.dump(desc, open(out + '/brick_layout.json', 'w'))
print('bricks found:', len(bricks), '| rows:', nlines, '| json bytes:', os.path.getsize(out + '/brick_layout.json'))
# 3. redraw and compare
fit = np.zeros((H, W), np.uint8)
for b in bricks:
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            p0 = (int(round((b['x0'] + dx) * W)), int(round((b['y0'] + dy) * H)))
            p1 = (int(round((b['x1'] + dx) * W)), int(round((b['y1'] + dy) * H)))
            cv2.rectangle(fit, p0, p1, 1, -1)
# reference brick mask = not mortar, closed to fill soot / chips (large mortar network only)
n, lab, stats, _ = cv2.connectedComponentsWithStats(np.tile(mortar, (3, 3)), connectivity=8)
keep = np.zeros((3 * H, 3 * W), np.uint8)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] > 20000:
        keep[lab == i] = 1
brick_mask = (keep[H:2 * H, W:2 * W] == 0)
inter = np.logical_and(fit == 1, brick_mask).sum(); union = np.logical_or(fit == 1, brick_mask).sum()
print('brick-area overlap (IoU) between fitted rectangles and the reference bricks: %.3f' % (inter / union))
vis = img.copy()
vis[fit == 0] = (vis[fit == 0] * 0.35 + np.array([0, 0, 140]) * 0.65).astype(np.uint8)
cv2.imwrite(out + '/brick_layout_check.png', vis)
