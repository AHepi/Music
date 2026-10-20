# Plain note: FIT step that improves the brick list from fit_brick_layout.py. For every brick it moves each of the four edges (left, right,
# top, bottom) up to 4 dots either way to the place where the rectangle best covers the reference's brick area (not mortar), repeating until
# nothing improves, and never lets a brick overlap its neighbours (a first version without this rule let bricks swell over the mortar and
# merge, while the overlap score still rose, because the score counts the union of all bricks; found by looking at the picture). Writes a new description file and prints the overlap score before and after.
# Run: python3 -I refine_brick_layout.py IN_LAYOUT.json OUT_LAYOUT.json OUT_CHECK.png
import sys, json
import numpy as np, cv2
REF = 'proc-work/reference/brick/colour.png'
d = json.load(open(sys.argv[1]))
img = cv2.imread(REF)
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
s, v = hsv[..., 1] / 255, hsv[..., 2] / 255
mortar = ((s < 0.42) & (v > 0.30)).astype(np.uint8)
mortar = cv2.morphologyEx(mortar, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
mortar = cv2.morphologyEx(mortar, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(np.tile(mortar, (3, 3)), connectivity=8)
keep = np.zeros((3 * H, 3 * W), np.uint8)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] > 20000:
        keep[lab == i] = 1
brick_big = (1 - keep).astype(np.int32)       # 1 = brick, 0 = mortar (3x3 tiled so wrap-around bricks work)
# integral image for fast box sums
ii = cv2.integral(brick_big.astype(np.float64))


def box(x0, y0, x1, y1):
    """sum of brick pixels in the box [x0,x1) x [y0,y1) in tile pixels (tile origin offset by one tile in the big picture)"""
    x0, x1, y0, y1 = int(round(x0)) + W, int(round(x1)) + W, int(round(y0)) + H, int(round(y1)) + H
    return ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]


def score(r):
    """overlap-based quality of one rectangle: brick pixels inside minus mortar pixels inside (so it neither grows nor shrinks too much)"""
    x0, y0, x1, y1 = r
    area = max(1.0, (x1 - x0) * (y1 - y0))
    inside = box(x0, y0, x1, y1)
    # reward brick inside, penalise mortar inside; slightly reward size so it does not collapse
    return inside - 1.0 * (area - inside)


def total_iou(bricks):
    fit = np.zeros((H, W), np.uint8)
    for b in bricks:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cv2.rectangle(fit, (int(round((b['x0'] + dx) * W)), int(round((b['y0'] + dy) * H))), (int(round((b['x1'] + dx) * W)), int(round((b['y1'] + dy) * H))), 1, -1)
    bm = (keep[H:2 * H, W:2 * W] == 0)
    return np.logical_and(fit == 1, bm).sum() / np.logical_or(fit == 1, bm).sum(), fit


def overlaps_others(me, t):
    """True if rectangle t (pixels) overlaps another brick by more than 3 dots in both directions (tile wrap-around included)"""
    for o in d['bricks']:
        if o is me:
            continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                ox0, oy0, ox1, oy1 = (o['x0'] + dx) * W, (o['y0'] + dy) * H, (o['x1'] + dx) * W, (o['y1'] + dy) * H
                if min(t[2], ox1) - max(t[0], ox0) > 3 and min(t[3], oy1) - max(t[1], oy0) > 3:
                    return True
    return False


iou0, _ = total_iou(d['bricks'])
for b in d['bricks']:
    r = [b['x0'] * W, b['y0'] * H, b['x1'] * W, b['y1'] * H]
    r_start = list(r)
    for _ in range(6):
        changed = False
        for k in range(4):
            best, best_val = r[k], score(r)
            for dlt in range(-4, 5):
                t = list(r)
                t[k] = r[k] + dlt
                if abs(t[k] - r_start[k]) > 6:   # never drift more than 6 dots from the first fit
                    continue
                if t[2] - t[0] < 40 or t[3] - t[1] < 40:
                    continue
                if overlaps_others(b, t):
                    continue
                sc = score(t)
                if sc > best_val:
                    best, best_val = t[k], sc
            if best != r[k]:
                r[k] = best
                changed = True
        if not changed:
            break
    b['x0'], b['y0'], b['x1'], b['y1'] = [round(r[0] / W, 4), round(r[1] / H, 4), round(r[2] / W, 4), round(r[3] / H, 4)]
iou1, fit = total_iou(d['bricks'])
print('overlap with the reference bricks: before %.3f, after %.3f' % (iou0, iou1))
json.dump(d, open(sys.argv[2], 'w'))
vis = img.copy()
vis[fit == 0] = (vis[fit == 0] * 0.35 + np.array([0, 0, 140]) * 0.65).astype(np.uint8)
cv2.imwrite(sys.argv[3], vis)
