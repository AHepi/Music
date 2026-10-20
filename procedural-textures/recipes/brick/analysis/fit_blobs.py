import sys; sys.path.insert(0, "."); sys.path.insert(0, "../generator")
# What this does (plain words): the "patches" fitting step. Starting from the brick layout painted in one colour per brick, it looks at the
# flat-colour patches of the reference (the same label picture as the tracing step) and, for the patches that would fix the most dots, writes down a
# ragged ellipse (centre, two radii, turn, colour, raggedness, random seed) instead of the traced outline. It keeps the best N ellipses to hit a size
# budget (S = 8 KB, M = 64 KB, or any number you give) and paints them biggest first. Writes ../generator/descriptions/<name>.json.
# Analysis only (reads the reference through the label picture made in fit_stage1.py).
import json, os
from region_tools import *
import shape_stack as ss

K = 16
labels = np.load('labels_k16.npy')
base = json.load(open('../generator/descriptions/stage1_bricks_only.json'))
L1 = mode_filter(labels, K, 3)


def raster_labels(shapes, size=1254, background=0):
    canvas = np.full((size, size), background, np.uint8)
    for sh in shapes:
        cv2.fillPoly(canvas, [np.round(sh['points']).astype(np.int32)], int(sh['colour']))
        for h in sh.get('holes', []):
            pass
    return canvas


def ellipse_candidates(regions_ids, region_label, region_area, ids, min_area):
    """For every connected patch: centre, radii, angle (from its moments), raggedness (from how far its edge strays from the ellipse)."""
    cands = []
    objs = cv2.connectedComponentsWithStats  # placeholder to keep the import visible
    return cands


def make_candidates(L2, min_area):
    ids, rlabel, rarea = regions_of(L2, K)
    cands = []
    # per region moments through bounding boxes
    ys, xs = np.mgrid[0:1254, 0:1254]
    order = np.argsort(-rarea[1:]) + 1
    flat_ids = ids.ravel()
    # use cv2 moments per region via bounding boxes from findContours on each label component: simpler to sort pixel indices by id
    sort = np.argsort(flat_ids, kind='stable')
    sorted_ids = flat_ids[sort]
    starts = np.searchsorted(sorted_ids, np.arange(len(rlabel) + 1))
    for rid in order:
        a = rarea[rid]
        if a < min_area:
            continue
        idx = sort[starts[rid]:starts[rid + 1]]
        py, px = np.divmod(idx, 1254)
        cx, cy = px.mean() + 0.5, py.mean() + 0.5
        cov = np.cov(np.stack([px - cx, py - cy]))
        evals, evecs = np.linalg.eigh(cov)
        evals = np.maximum(evals, 0.3)
        ry, rx = 2 * np.sqrt(evals)          # eigh ascending: smaller first
        v = evecs[:, 1]
        angle = float(np.degrees(np.arctan2(v[1], v[0])))
        # raggedness: spread of the patch's radial extent about the ellipse
        d = np.stack([px - cx, py - cy])
        c, s = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        u = (c * d[0] + s * d[1]) / rx
        w = (-s * d[0] + c * d[1]) / ry
        rad = np.sqrt(u * u + w * w)
        ragged = float(np.clip(np.percentile(rad, 98) - 1.0 + 0.2, 0.1, 0.9)) if a > 20 else 0.2
        cands.append({'rid': int(rid), 'area': int(a), 'label': int(rlabel[rid]), 'cx': cx, 'cy': cy, 'rx': float(rx), 'ry': float(ry), 'angle': angle, 'ragged': ragged})
    return cands


def gain_of(canvas, truth, cand, seed):
    pts = ss.ragged_ellipse(cand['cx'], cand['cy'], cand['rx'], cand['ry'], cand['angle'], cand['ragged'], seed)
    x0, y0 = np.floor(pts.min(0)).astype(int) - 1
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 2
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, 1254), min(y1, 1254)
    if x1 <= x0 or y1 <= y0:
        return -1, None
    sub_truth = truth[y0:y1, x0:x1]
    sub_canvas = canvas[y0:y1, x0:x1]
    mask = np.zeros(sub_truth.shape, np.uint8)
    cv2.fillPoly(mask, [np.round(pts - [x0, y0]).astype(np.int32)], 1)
    before = (sub_canvas == sub_truth)
    after = np.where(mask > 0, cand['label'], sub_canvas) == sub_truth
    return int(after.sum() - before.sum()), (x0, y0, x1, y1, mask)


def fit(bytes_budget, name, min_area=40, ring=True):
    L2, _ = remove_small(L1, K, 12)
    cands = make_candidates(L2, min_area)
    base_stack = ss.build_shape_stack(base, wrap=True)
    canvas = np.zeros((1254, 1254), np.uint8)
    for sh in base_stack:
        cv2.fillPoly(canvas, [np.round(sh['points']).astype(np.int32)], int(sh['colour']))
    truth = L2
    scored = []
    for i, cnd in enumerate(cands):
        seed = (i * 7919) % 997
        g, _ = gain_of(canvas, truth, cnd, seed)
        scored.append((g, i, seed))
    scored.sort(reverse=True)
    lo, hi = 1, len(scored)
    best = None
    def make_description(n):
        chosen = [s for s in scored[:n] if s[0] > 0]
        chosen.sort(key=lambda s: -cands[s[1]]['area'])
        items = []
        for g, i, seed in chosen:
            c = cands[i]
            items.append([int(round(c['cx'])), int(round(c['cy'])), round(c['rx'], 1), round(c['ry'], 1), int(round(c['angle'])), c['label'], round(c['ragged'], 1), int(seed)])
        desc = {k: base[k] for k in ('format', 'surface', 'tile', 'seed', 'palette', 'maps', 'backdrop')}
        desc['palette'] = base['palette'] + [[60, 43, 34, 0.9]]
        desc['layers'] = [base['layers'][0], {'type': 'blobs', 'items': items}]
        if ring:
            desc['layers'].append({'type': 'outlines', 'colour': 16, 'corner_radius': 9.0, 'inside': [1.0, 1.0, 1.0, 1.5], 'outside': [1.0, 0.0, 1.5, 3.0], 'rows': base['layers'][0]['rows']})
        return desc
    while lo <= hi:
        mid = (lo + hi) // 2
        d = make_description(mid)
        size = len(json.dumps(d, separators=(',', ':')))
        if size <= bytes_budget:
            best, lo = d, mid + 1
        else:
            hi = mid - 1
    path = f'../generator/descriptions/{name}.json'
    json.dump(best, open(path, 'w'), separators=(',', ':'))
    print(name, os.path.getsize(path), 'bytes', len(best['layers'][1]['items']), 'blobs of', len(cands), 'candidates')


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            continue
        parts = arg.split(':')
        fit(int(parts[1]), parts[0], min_area=int(parts[2]) if len(parts) > 2 else 40, ring='--noring' not in sys.argv)
