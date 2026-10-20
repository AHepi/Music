# What this does (plain words): finds the WHEEL RUTS (long dark grooves) in the ground of the mud picture. It looks at the brightness of the ground (puddles and stones
# painted over first), finds thin dark valleys with the Hessian (the second-derivative "ridge" test), and follows each valley as a curve: start at the strongest spot,
# step along the valley direction, keep centred on the valley, stop when it fades. The result is a list of curves (corner lists in picture dots, may leave the tile:
# the picture wraps around), with the groove's width and darkness measured across the curve. Analysis only (reads the reference).
import math
import cv2
import numpy as np


def ridge_field(grey, sigma):
    """Dark-line strength (how much darker a thin line is than both sides, scale-normalised) and the direction ALONG the line, for every dot (wrap-around edges)."""
    pad = int(6 * sigma) + 2
    g = np.pad(grey.astype(np.float32), pad, mode='wrap')
    s = cv2.GaussianBlur(g, (0, 0), sigma)
    lxx = cv2.Sobel(s, cv2.CV_32F, 2, 0, ksize=3) / 4.0 * sigma ** 2
    lyy = cv2.Sobel(s, cv2.CV_32F, 0, 2, ksize=3) / 4.0 * sigma ** 2
    lxy = cv2.Sobel(s, cv2.CV_32F, 1, 1, ksize=3) / 4.0 * sigma ** 2
    half_trace = (lxx + lyy) / 2.0
    root = np.sqrt(((lxx - lyy) / 2.0) ** 2 + lxy ** 2)
    big = half_trace + root                      # largest eigenvalue: positive across a dark valley
    # direction of the eigenvector of the largest eigenvalue = ACROSS the valley; the line runs perpendicular to it
    angle_across = 0.5 * np.arctan2(2 * lxy, lxx - lyy)
    angle_along = angle_across + math.pi / 2
    crop = (slice(pad, -pad), slice(pad, -pad))
    return np.clip(big[crop], 0, None), angle_along[crop]


def trace_ruts(grey, sigma=3.0, high_percentile=97.0, low_fraction=0.45, step=2.0, max_turn_degrees=35.0, min_length=45.0, simplify=2.0):
    h, w = grey.shape
    strength, along = ridge_field(grey, sigma)
    high = np.percentile(strength, high_percentile)
    low = high * low_fraction
    tx, ty = np.cos(along), np.sin(along)
    # non-maximum suppression across the line: keep a dot only if it is the strongest of the three dots across the valley
    nx, ny = -ty, tx
    def sample(arr, x, y):
        xi = np.mod(np.round(x).astype(int), w); yi = np.mod(np.round(y).astype(int), h)
        return arr[yi, xi]
    yy, xx = np.mgrid[0:h, 0:w]
    s_plus = sample(strength, xx + nx, yy + ny); s_minus = sample(strength, xx - nx, yy - ny)
    seeds_mask = (strength >= high) & (strength >= s_plus) & (strength >= s_minus)
    sy, sx = np.nonzero(seeds_mask)
    order = np.argsort(-strength[sy, sx])
    visited = np.zeros((h, w), np.uint8)
    curves = []

    def trace(x, y, dx, dy):
        pts = [(x, y)]
        for _ in range(4000):
            nxp, nyp = x + dx * step, y + dy * step
            # re-centre across the valley: look at 5 positions across and take the strongest
            best, bx, by = -1, nxp, nyp
            tx_, ty_ = sample(tx, nxp, nyp), sample(ty, nxp, nyp)
            ax_, ay_ = -ty_, tx_
            for o in (-2.0, -1.0, 0.0, 1.0, 2.0):
                cx, cy = nxp + ax_ * o, nyp + ay_ * o
                v = float(sample(strength, cx, cy))
                if v > best:
                    best, bx, by = v, cx, cy
            if best < low:
                break
            # new direction from the local line direction, keeping the heading (never turn round)
            ndx, ndy = float(sample(tx, bx, by)), float(sample(ty, bx, by))
            if ndx * dx + ndy * dy < 0:
                ndx, ndy = -ndx, -ndy
            turn = math.degrees(math.acos(max(-1.0, min(1.0, ndx * dx + ndy * dy))))
            if turn > max_turn_degrees:
                break
            if visited[int(round(by)) % h, int(round(bx)) % w]:
                pts.append((bx, by))
                break
            x, y, dx, dy = bx, by, ndx, ndy
            pts.append((x, y))
        return pts

    for k in order:
        x0, y0 = float(sx[k]), float(sy[k])
        if visited[int(y0) % h, int(x0) % w]:
            continue
        dx, dy = float(tx[int(y0), int(x0)]), float(ty[int(y0), int(x0)])
        forward = trace(x0, y0, dx, dy)
        backward = trace(x0, y0, -dx, -dy)
        pts = backward[::-1] + forward[1:]
        length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
        # mark the curve (and a 3-dot margin) as used, even when it is dropped for being short
        for (px, py) in pts:
            cv2.circle(visited, (int(round(px)) % w, int(round(py)) % h), 3, 1, -1)
        if length < min_length:
            continue
        arr = np.array(pts, np.float32).reshape(-1, 1, 2)
        simple = cv2.approxPolyDP(arr, simplify, False)[:, 0, :]
        if len(simple) >= 2:
            curves.append({'pts': simple.astype(float), 'length': length, 'strength': float(np.mean([strength[int(round(p[1])) % h, int(round(p[0])) % w] for p in pts]))})
    return curves, strength
