# What this does (plain words): ANALYSIS script (reads the reference picture; the generator never does). It finds the individual stones in the
# gravel colour picture: (1) every dot is called "soil" (orange-brown) or "stone" (blue-grey / black) by its colour; (2) holes in stones are
# filled and crumbs removed; (3) stones that touch are cut apart at their narrowest neck (a "watershed" on the distance to the soil);
# (4) each piece is measured: middle, size, long and short side, angle, outline. Stones near the tile edge are found on a wrapped copy
# so they are whole. Writes stones_found.json and a picture of the pieces.
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trace_tools as tt

TILE = 1254
PAD = 130


def find_stones(bgr, h_dynamic=2.0, smooth=2.0, min_area=14):
    bp = np.pad(bgr, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='wrap')
    lab = cv2.cvtColor(bp.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    chroma = np.hypot(a, b)
    soil = ((b > 5.0) & (a > 2.0) & (chroma > 6.5)).astype(np.uint8) * 255
    soil = cv2.medianBlur(soil, 7) > 0
    stone = (~soil).astype(np.uint8)
    n, comp, stats, _ = cv2.connectedComponentsWithStats(soil.astype(np.uint8), connectivity=4)
    small_soil = np.zeros(n, bool)
    small_soil[1:] = stats[1:, cv2.CC_STAT_AREA] < 250
    stone[small_soil[comp]] = 1                       # a small soil-coloured hole inside stone is a facet of the stone
    stone = cv2.morphologyEx(stone, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    dist = cv2.distanceTransform(stone, cv2.DIST_L2, 5)
    ds = cv2.GaussianBlur(dist, (0, 0), smooth)
    marker = ds - h_dynamic
    kernel = np.ones((3, 3), np.uint8)
    for _ in range(2000):
        nxt = np.minimum(cv2.dilate(marker, kernel), ds)
        if np.abs(nxt - marker).max() < 1e-4:
            break
        marker = nxt
    peaks = ((ds - marker) >= h_dynamic - 1e-3) & (ds > 2.5)
    n_mark, markers = cv2.connectedComponents(peaks.astype(np.uint8))
    markers = markers.astype(np.int32)
    inv = (255 - 255 * np.sqrt(np.clip(ds / max(ds.max(), 1e-6), 0, 1))).astype(np.uint8)
    inv[stone == 0] = 255
    cv2.watershed(cv2.merge([inv, inv, inv]), markers)
    seg = markers.copy()
    seg[(seg < 1) | (stone == 0)] = 0
    return bp, stone, seg


if __name__ == '__main__':
    bgr = tt.load_reference_colour()
    bp, stone, seg = find_stones(bgr)
    print('stone share', stone[PAD:-PAD, PAD:-PAD].mean(), 'labelled share', (seg[PAD:-PAD, PAD:-PAD] > 0).mean())
    stones = []
    for label in np.unique(seg):
        if label == 0:
            continue
        ys, xs = np.nonzero(seg == label)
        cx, cy = xs.mean(), ys.mean()
        if not (PAD <= cx < PAD + TILE and PAD <= cy < PAD + TILE) or len(xs) < 14:
            continue
        mask = (seg == label).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contour = max(contours, key=cv2.contourArea)
        (_, _), (w, h), angle = cv2.minAreaRect(contour)
        stones.append(dict(x=float(cx - PAD), y=float(cy - PAD), area=int(len(xs)), long=float(max(w, h)), short=float(min(w, h)), angle=float(angle),
                           mean_bgr=bp[ys, xs].astype(np.float64).mean(axis=0).round(1).tolist(),
                           contour=(cv2.approxPolyDP(contour, 1.3, True)[:, 0, :] - PAD).tolist()))
    areas = np.array([s['area'] for s in stones])
    print('stones in the tile:', len(stones), 'area percentiles 10/50/90/99:', np.percentile(areas, [10, 50, 90, 99]).round(0), 'share', areas.sum() / TILE ** 2)
    json.dump(stones, open(os.path.join(HERE, 'stones_found.json'), 'w'))
    rng = np.random.default_rng(3)
    cols = rng.integers(60, 255, (seg.max() + 2, 3)).astype(np.uint8)
    colored = cols[seg]
    colored[seg == 0] = 0
    vis = np.where((seg > 0)[..., None], (0.5 * bp + 0.5 * colored).astype(np.uint8), (0.8 * bp).astype(np.uint8))
    edge = cv2.dilate(seg.astype(np.float32), np.ones((3, 3))) != cv2.erode(seg.astype(np.float32), np.ones((3, 3)))
    vis[edge] = (255, 255, 255)
    vis = vis[PAD:-PAD, PAD:-PAD]
    cv2.imwrite(os.path.join(HERE, 'crops', 'seg3_overlay.png'), cv2.resize(vis, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_AREA))
    np.save(os.path.join(HERE, 'seg3.npy'), seg)
