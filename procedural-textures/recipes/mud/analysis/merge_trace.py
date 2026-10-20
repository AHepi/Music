# What this does (plain words): a SMARTER way to cut the mud colour picture (copied from the wood work, unchanged) into flat colour patches than "keep every same-colour area bigger than N dots".
# It starts from the tiny same-colour areas (about 100,000 of them), and repeatedly joins the two NEIGHBOURING areas whose joining would change the
# picture least (the "Ward" rule: the change is the two areas' sizes multiplied by how different their average colours are). It stops when only
# the wanted number of patches is left. So a dark speck on a light patch survives (joining would hurt a lot) while a faint colour change between
# two nearly equal browns disappears (joining costs nothing). Every patch gets the average colour of the dots it holds; the patch colours are
# then squeezed into a short palette. It is an ANALYSIS tool (reads the reference); the generator only ever sees the resulting list of outlines.
# Use:  from merge_trace import build_merge_tree, labels_at, ...   (see run_merge_ladder.py for the experiment)
import heapq

import cv2
import numpy as np

import trace_tools as tt


def initial_regions(bgr, colour_count=32, seed=1):
    """Same-colour connected areas of a palette-snapped picture (the starting point of the merging). Returns (region id per dot, Lab picture)."""
    centres = tt.make_palette(bgr, colour_count, seed)
    labels = tt.assign_labels(bgr, centres)
    comp = np.zeros(labels.shape, np.int32)
    next_id = 1
    for k in range(colour_count):
        n, c = cv2.connectedComponents((labels == k).astype(np.uint8), connectivity=4)
        mask = c > 0
        comp[mask] = c[mask] + next_id - 1
        next_id += n - 1
    return comp - 1, tt.srgb_to_lab_float(bgr)


def build_merge_tree(comp, lab, wrap=True):
    """Run the whole merging once and remember the order. Returns dict(parent_pairs=[(a, b, cost)], area, mean_lab) for the initial regions."""
    n = int(comp.max()) + 1
    flat = comp.ravel()
    area = np.bincount(flat, minlength=n).astype(np.float64)
    sums = np.stack([np.bincount(flat, weights=lab[..., c].ravel(), minlength=n) for c in range(3)], axis=1)
    mean = sums / area[:, None]
    # neighbour pairs (4-neighbourhood, wrap-around edges because the tile repeats)
    pairs = []
    right = np.roll(comp, -1, axis=1) if wrap else comp[:, 1:]
    down = np.roll(comp, -1, axis=0) if wrap else comp[1:, :]
    for a, b in ((comp, right), (comp, down)):
        if not wrap:
            a = a[:b.shape[0], :b.shape[1]]
        sel = a != b
        lo, hi = np.minimum(a[sel], b[sel]), np.maximum(a[sel], b[sel])
        pairs.append(lo.astype(np.int64) * n + hi.astype(np.int64))
    key, shared = np.unique(np.concatenate(pairs), return_counts=True)
    neighbours = [dict() for _ in range(n)]
    for k, s in zip(key.tolist(), shared.tolist()):
        a, b = divmod(k, n)
        neighbours[a][b] = s
        neighbours[b][a] = s
    area_l, mean_l = area.tolist(), [m for m in mean]
    alive = [True] * n
    version = [0] * n

    def cost(a, b):
        d = mean_l[a] - mean_l[b]
        return area_l[a] * area_l[b] / (area_l[a] + area_l[b]) * float(d @ d)

    heap = []
    for a in range(n):
        for b in neighbours[a]:
            if a < b:
                heap.append((cost(a, b), a, b, 0, 0))
    heapq.heapify(heap)
    merges = []                                       # (kept id, absorbed id, cost) in merge order
    while heap:
        c, a, b, va, vb = heapq.heappop(heap)
        if not (alive[a] and alive[b]) or va != version[a] or vb != version[b]:
            continue
        # merge b into a
        total = area_l[a] + area_l[b]
        mean_l[a] = (mean_l[a] * area_l[a] + mean_l[b] * area_l[b]) / total
        area_l[a] = total
        alive[b] = False
        version[a] += 1
        for c_id, s in neighbours[b].items():
            if c_id == a:
                continue
            neighbours[c_id].pop(b, None)
            neighbours[a][c_id] = neighbours[a].get(c_id, 0) + s
            neighbours[c_id][a] = neighbours[a][c_id]
        neighbours[a].pop(b, None)
        neighbours[b] = {}
        for c_id in neighbours[a]:
            heapq.heappush(heap, (cost(a, c_id), min(a, c_id), max(a, c_id), version[min(a, c_id)], version[max(a, c_id)]))
        merges.append((a, b, c))
    return {'merges': merges, 'n': n}


def labels_at(comp, tree, target_count):
    """Region id per dot after merging until only `target_count` regions are left (replays the remembered merge order)."""
    n = tree['n']
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    steps = max(0, n - target_count)
    for a, b, _ in tree['merges'][:steps]:
        parent[find(b)] = find(a)
    roots = np.array([find(i) for i in range(n)], np.int64)
    unique, inverse = np.unique(roots, return_inverse=True)
    return inverse[comp].astype(np.int32), len(unique)


def region_colours(region_labels, lab, count):
    """Average Lab colour of every region (count x 3)."""
    flat = region_labels.ravel()
    area = np.bincount(flat, minlength=count).astype(np.float64)
    return np.stack([np.bincount(flat, weights=lab[..., c].ravel(), minlength=count) for c in range(3)], axis=1) / area[:, None], area


def squeeze_palette(means, area, palette_size, seed=1):
    """Area-weighted k-means of region mean colours into a short palette. Returns (palette in Lab, palette index per region)."""
    rng = np.random.default_rng(seed)
    probability = area / area.sum()
    sample_index = rng.choice(len(means), size=min(200000, 20 * len(means)), p=probability)
    sample = means[sample_index].astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.01)
    cv2.setRNGSeed(seed)
    _, _, centres = cv2.kmeans(sample, palette_size, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    index = ((means[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
    return centres, index


def trace_labelled_regions(region_labels, count, palette_index, epsilon, min_area=1):
    """Outline (RETR_EXTERNAL) of every region. A region is connected by construction. Returns [{'c': palette index, 'p': corners, 'a': filled area}] big to small.
    The outlines are found on a picture padded by 1 dot so regions touching the tile edge are closed."""
    regions = []
    objects = cv2.findContours  # noqa: F841
    boxes = np.zeros((count, 4), np.int64)
    # bounding boxes per region without a Python loop over dots
    ys, xs = np.mgrid[0:region_labels.shape[0], 0:region_labels.shape[1]]
    flat = region_labels.ravel()
    order = np.argsort(flat, kind='stable')
    sorted_labels = flat[order]
    starts = np.searchsorted(sorted_labels, np.arange(count))
    ends = np.searchsorted(sorted_labels, np.arange(count), side='right')
    width = region_labels.shape[1]
    for r in range(count):
        idx = order[starts[r]:ends[r]]
        if len(idx) < min_area:
            continue
        y, x = idx // width, idx % width
        x0, x1, y0, y1 = x.min(), x.max(), y.min(), y.max()
        sub = np.zeros((y1 - y0 + 3, x1 - x0 + 3), np.uint8)
        sub[y - y0 + 1, x - x0 + 1] = 1
        contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            if isinstance(epsilon, (tuple, list)):
                # outline looseness that follows the thickness of the patch: thin patches (cracks) are traced finely, fat ones loosely
                e_min, e_max, k = epsilon
                perimeter = max(cv2.arcLength(contour, True), 1.0)
                eps_here = float(np.clip(k * 2.0 * len(idx) / perimeter, e_min, e_max))
            else:
                eps_here = epsilon
            simple = cv2.approxPolyDP(contour, eps_here, True)[:, 0, :] + np.array([x0 - 1, y0 - 1])
            if len(simple) < 3:
                # a one-dot or straight-line region: make a tiny box so it still paints its dots
                simple = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]) if len(simple) < 3 else simple
            # painting order key = the size of THIS piece (a region that crosses the tile edge has two pieces, each traced on its own, both with the colour of the whole region)
            filled = max(abs(cv2.contourArea(simple.astype(np.int32))), abs(cv2.contourArea(contour)))
            regions.append({'c': int(palette_index[r]), 'p': simple.astype(int).tolist(), 'a': float(filled + 0.5 * cv2.arcLength(contour, True))})
    regions.sort(key=lambda reg: -reg['a'])
    return regions
