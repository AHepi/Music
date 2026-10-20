# What this does (plain words): helper steps for turning a painted colour picture into a short list of flat-colour regions
# ("palette + patches"): squeeze to K colours, tidy the label picture, throw away tiny patches (their dots take the colour of the nearest
# bigger patch), and measure how good the picture rebuilt from the patches is. Analysis only: it reads the reference picture.
import sys, os
sys.path.insert(0, '../generator'); sys.path.insert(0, '../../../lib')
import numpy as np, cv2
import pixel_compare as pc

REF = '../../../reference/brick/colour.png'


def load_reference():
    return cv2.imread(REF)       # blue-green-red, uint8


def kmeans_labels(bgr, K, prefilter='none', seed=1):
    if prefilter == 'bilateral':
        bgr = cv2.bilateralFilter(bgr, 7, 25, 5)
    elif prefilter == 'median3':
        bgr = cv2.medianBlur(bgr, 3)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    sample = lab.reshape(-1, 3)[::7]
    cv2.setRNGSeed(seed)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, centres = cv2.kmeans(sample, K, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    dist = ((lab.reshape(-1, 1, 3) - centres[None]) ** 2).sum(-1)
    labels = dist.argmin(1).reshape(bgr.shape[:2]).astype(np.uint8)
    return labels, centres


def mode_filter(labels, K, size=3):
    """Replace every label by the most common label in a size x size window (a 'majority vote' smoothing)."""
    votes = np.zeros(labels.shape + (K,), np.float32)
    for k in range(K):
        votes[..., k] = cv2.blur((labels == k).astype(np.float32), (size, size))
    return votes.argmax(-1).astype(np.uint8)


def remove_small(labels, K, min_area):
    """Dots in connected patches smaller than min_area take the label of the nearest dot that is in a bigger patch."""
    h, w = labels.shape
    ids = np.zeros((h, w), np.int32)
    next_id = 0
    sizes = [0]
    for k in range(K):
        n, comp, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
        sel = comp > 0
        ids[sel] = comp[sel] + next_id
        sizes.extend(stats[1:, cv2.CC_STAT_AREA].tolist())
        next_id += n - 1
    sizes = np.array(sizes)
    small = sizes[ids] < min_area
    if not small.any():
        return labels, ids
    keep = (~small).astype(np.uint8)
    # distance transform with labels: nearest kept dot for every dot
    dist, nearest = cv2.distanceTransformWithLabels(1 - keep, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(keep)
    # distanceTransformWithLabels labels pixels 1..N for zero pixels in raster order of the zero pixels
    lookup = np.zeros(len(ys) + 1, np.uint8)
    lookup[1:] = labels[ys, xs]
    new_labels = labels.copy()
    new_labels[small] = lookup[nearest[small]]
    # re-run connected components because merged patches may now touch same-label neighbours
    return new_labels, None


def regions_of(labels, K):
    """Connected patches (4-connected) of the label picture: returns id picture and arrays (label, area)."""
    h, w = labels.shape
    ids = np.zeros((h, w), np.int32)
    next_id = 1
    region_label = [0]
    region_area = [0]
    for k in range(K):
        n, comp, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
        sel = comp > 0
        ids[sel] = comp[sel] + next_id - 1
        region_label.extend([k] * (n - 1))
        region_area.extend(stats[1:, cv2.CC_STAT_AREA].tolist())
        next_id += n - 1
    return ids, np.array(region_label), np.array(region_area)


def score_colour(candidate_bgr, tag, folder_root='../scores/tmp'):
    """Write a candidate colour picture and score it against the reference with pixel_compare (colour measures only)."""
    folder = os.path.join(folder_root, tag)
    os.makedirs(folder, exist_ok=True)
    cv2.imwrite(os.path.join(folder, 'colour.png'), candidate_bgr)
    r = pc.pixel_report('brick', folder)
    return {k: r[k] for k in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px')}


def trace_regions(labels, K, epsilon=1.0, grow=1):
    """Turn a label picture into a list of painted regions (outer outline only, simplified), painted in an order that is always correct:
    a patch that sits inside a hole of another patch is painted after it; otherwise big patches first, small ones on top.
    Returns a list of dicts: label, area, depth, points (list of (x, y) in dot units, pixel centres at +0.5)."""
    h, w = labels.shape
    ids, rlabel, rarea = regions_of(labels, K)
    n = len(rlabel) - 1
    # bounding boxes of every region
    objects = {}
    from_slices = None
    out = []
    enclosed_by = {}
    order_ids = np.arange(1, n + 1)
    # find bounding boxes via per label connected components stats (recompute with stats)
    boxes = {}
    next_id = 1
    for k in range(K):
        cnt, comp, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
        for j in range(1, cnt):
            x, y, bw, bh, a = stats[j]
            boxes[next_id] = (x, y, bw, bh)
            next_id += 1
    kernel = np.ones((3, 3), np.uint8)
    for rid in range(1, n + 1):
        x, y, bw, bh = boxes[rid]
        pad = 2
        x0, y0 = max(x - pad, 0), max(y - pad, 0)
        x1, y1 = min(x + bw + pad, w), min(y + bh + pad, h)
        mask = (ids[y0:y1, x0:x1] == rid).astype(np.uint8)
        grown = cv2.dilate(mask, kernel) if grow else mask
        contours, hierarchy = cv2.findContours(grown, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        if not contours:
            continue
        hierarchy = hierarchy[0]
        outers = [i for i in range(len(contours)) if hierarchy[i][3] == -1]
        outer = max(outers, key=lambda i: cv2.contourArea(contours[i]))
        poly = cv2.approxPolyDP(contours[outer], epsilon, True).reshape(-1, 2)
        if len(poly) < 3:
            continue
        pts = poly + np.array([x0, y0]) + 0.5
        # holes: which other patches lie inside
        inside = set()
        for i in range(len(contours)):
            if hierarchy[i][3] != -1:
                hole_mask = np.zeros(mask.shape, np.uint8)
                cv2.fillPoly(hole_mask, [contours[i]], 1)
                found = np.unique(ids[y0:y1, x0:x1][hole_mask > 0])
                inside.update(int(f) for f in found if f != rid and f != 0)
        enclosed_by[rid] = inside
        out.append({'id': rid, 'label': int(rlabel[rid]), 'area': int(rarea[rid]), 'points': pts})
    # depth: a patch inside a hole of another is deeper than it
    parent_of = {}
    for rid, inside in enclosed_by.items():
        for q in inside:
            parent_of.setdefault(q, []).append(rid)
    depth = {}

    def get_depth(q, stack=()):
        if q in depth:
            return depth[q]
        if q in stack:
            return 0
        ps = parent_of.get(q, [])
        d = 0 if not ps else 1 + max(get_depth(p, stack + (q,)) for p in ps)
        depth[q] = d
        return d

    for item in out:
        item['depth'] = get_depth(item['id'])
    out.sort(key=lambda r: (r['depth'], -r['area']))
    return out


def raster_regions(regions, palette_bgr, size=1254, ss=2, background=0):
    """Paint the traced regions in order (supersampled, then averaged down) - the quick stand-in for the Blender render."""
    big = np.zeros((size * ss, size * ss, 3), np.uint8)
    big[:] = palette_bgr[background]
    for r in regions:
        pts = np.round(r['points'] * ss).astype(np.int32)
        cv2.fillPoly(big, [pts], [int(v) for v in palette_bgr[r['label']]], lineType=cv2.LINE_8)
    if ss == 1:
        return big
    return cv2.resize(big, (size, size), interpolation=cv2.INTER_AREA)


def encode_regions(regions):
    """Compact, number-only description of the regions: [palette_index, x0, y0, dx1, dy1, dx2, dy2, ...] with whole-dot steps rounded from half dots."""
    items = []
    for r in regions:
        p = np.round(r['points'] * 2).astype(int)    # half-dot precision
        start = p[0]
        steps = np.diff(p, axis=0).ravel().tolist()
        items.append([r['label'], int(start[0]), int(start[1])] + steps)
    return items
