# What this does (plain words): turns a MUD "description" (a small json-like dictionary: a palette of flat colours and lists of puddles, stones, wheel ruts,
# ground patches and traced patches) into ONE back-to-front list of flat coloured shapes (a shape = a few polygons and a palette number). The Blender generator draws
# that list as real flat geometry and photographs it from above; a quick numpy/OpenCV painter (draw_preview, below) draws the same list without Blender so settings can be
# tried in a second. It never reads a reference picture; everything comes from the description.
# Description format (all corners are whole numbers in picture dots; a polygon is stored as steps: first corner, then the step to each next corner):
#   tile: 1254          palette: [[r,g,b], ...]          ground: {"colour": palette number}
#   puddles: [{"b": base water colour, "p": steps, "t": [[colour, steps], ...]}, ...]       (outline, then flat water tones drawn over it)
#   stones:  [[base colour, steps, [[colour, steps], ...]], ...]                              (outline, then the stone's flat faces)
#   patches: [[colour, steps], ...]                                                          (traced patches painted over everything: the biggest layer)
#   ruts and ground stamps: see their functions below.
import math

import numpy as np


def decode(steps):
    """flat list [x0, y0, dx1, dy1, ...] -> corners (n x 2 whole numbers)."""
    a = np.asarray(steps, np.int64).reshape(-1, 2)
    return np.cumsum(a, axis=0)


def encode(points):
    pts = np.asarray(points, np.int64)
    return np.diff(pts, axis=0, prepend=np.zeros((1, 2), np.int64)).reshape(-1).tolist()


def grow_polygon(points, distance):
    """Push every corner outwards by `distance` dots (mitred; never more than 3 x distance). Works whichever way the corners run."""
    pts = np.asarray(points, np.float64)
    if distance == 0 or len(pts) < 3:
        return pts
    nxt, prv = np.roll(pts, -1, axis=0), np.roll(pts, 1, axis=0)
    area = 0.5 * np.sum(pts[:, 0] * nxt[:, 1] - nxt[:, 0] * pts[:, 1])
    sign = 1.0 if area > 0 else -1.0

    def outward(a, b):
        edge = b - a
        length = np.maximum(np.linalg.norm(edge, axis=1, keepdims=True), 1e-9)
        return sign * np.stack([edge[:, 1], -edge[:, 0]], axis=1) / length

    n1, n2 = outward(prv, pts), outward(pts, nxt)
    scale = 1.0 / np.maximum(1.0 + (n1 * n2).sum(axis=1, keepdims=True), 0.34)
    offset = (n1 + n2) * scale * distance
    length = np.linalg.norm(offset, axis=1, keepdims=True)
    limit = 3.0 * abs(distance)
    offset = np.where(length > limit, offset / np.maximum(length, 1e-9) * limit, offset)
    return pts + offset


def traced_polygon(steps):
    """A traced polygon (corners are dot centres) -> corners in picture dots as the renderer wants them: moved half a dot (dot i spans i to i+1) and grown half a dot."""
    return grow_polygon(decode(steps) + 0.5, 0.5)


def wrap_copy_count(points, tile):
    """Which whole-tile shifts (ox, oy) make a copy of the shape touch the tile (for pictures that repeat)."""
    low, high = np.min(points, axis=0), np.max(points, axis=0)
    shifts = []
    for ox in (-1, 0, 1):
        if high[0] + ox * tile < -1 or low[0] + ox * tile > tile + 1:
            continue
        for oy in (-1, 0, 1):
            if high[1] + oy * tile < -1 or low[1] + oy * tile > tile + 1:
                continue
            shifts.append((ox, oy))
    return shifts


# ----------------------------------------------------------------------------------------------------- wheel ruts and ground clods
def chaikin(points, rounds=2):
    """Round off a polyline (corner cutting) so a rut bends smoothly."""
    pts = np.asarray(points, np.float64)
    for _ in range(rounds):
        a, b = pts[:-1], pts[1:]
        q, r = 0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b
        out = np.empty((2 * len(a), 2))
        out[0::2], out[1::2] = q, r
        pts = np.vstack([pts[:1], out, pts[-1:]])
    return pts


def smooth_noise_1d(rng, count, length_scale_steps, amplitude):
    """A slowly wandering number along a curve (sum of a few random sines), in the range of about +- amplitude."""
    t = np.arange(count) / max(length_scale_steps, 1.0)
    value = np.zeros(count)
    for k, weight in ((1.0, 1.0), (2.3, 0.6), (4.1, 0.35)):
        value += weight * np.sin(2 * math.pi * (k * t + rng.random()))
    return amplitude * value / 1.6


def ribbon(centre, offset_low, offset_high):
    """A flat band along a polyline: left edge at `offset_low` (array per point) and right edge at `offset_high`, measured across the line (positive = lit side)."""
    tang = np.gradient(centre, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    normal = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
    light = np.array([-0.7071, -0.7071])
    flip = (normal @ light).mean() < 0
    if flip:
        normal = -normal
    low = centre + normal * np.asarray(offset_low)[:, None]
    high = centre + normal * np.asarray(offset_high)[:, None]
    return np.vstack([low, high[::-1]])


def rut_shapes(layer, tile, seed):
    """Every wheel rut as a stack of flat bands along its curve, back to front: lit bank (light earth), the broad dark band, the darker groove, and a few grey wet streaks.
    layer: {'items': [{'p': [[x, y], ...], 'w': band width, 'bw': bank width, 'gw': groove width, 'band': colour, 'groove': colour, 'bank': colour, 'wet': colour or -1}], 'wobble': dots}"""
    rng = np.random.default_rng(seed)
    out = []
    wobble = float(layer.get('wobble', 2.0))
    for item in layer['items']:
        pts = chaikin(np.asarray(item['p'], np.float64), 2)
        # resample about every 3 dots
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        n = max(int(s[-1] / 3.0), 4)
        centre = np.stack([np.interp(np.linspace(0, s[-1], n), s, pts[:, 0]), np.interp(np.linspace(0, s[-1], n), s, pts[:, 1])], axis=1)
        w, bw, gw = float(item['w']), float(item.get('bw', 8)), float(item.get('gw', 6))
        wob = lambda amp: smooth_noise_1d(rng, n, 9.0, amp) + rng.normal(0, amp * 0.25, n)
        # the rut fades out at both ends (its width shrinks to nothing over the last ~70 dots) so it does not end in a square cut
        along = np.linspace(0, s[-1], n)
        taper = np.clip(np.minimum(along, s[-1] - along) / min(70.0, s[-1] / 2.5), 0.0, 1.0) ** 0.7
        if item.get('bank', -1) >= 0:
            out.append(([ribbon(centre, (w / 2 + wob(wobble) - 1) * taper, (w / 2 + bw + wob(wobble * 1.5)) * taper)], int(item['bank'])))
        out.append(([ribbon(centre, (-w / 2 + wob(wobble)) * taper, (w / 2 + wob(wobble)) * taper)], int(item['band'])))
        if item.get('groove', -1) >= 0:
            shift = wob(wobble * 1.5)
            out.append(([ribbon(centre, (-gw / 2 + shift) * taper, (gw / 2 + shift + np.abs(wob(wobble))) * taper)], int(item['groove'])))
        if item.get('wet', -1) >= 0:
            # a few short grey streaks along the groove
            for _ in range(max(int(s[-1] / 90), 1)):
                a = rng.integers(0, max(n - 8, 1)); b = min(n, a + rng.integers(8, 28))
                sw = rng.uniform(1.5, 3.5)
                out.append(([ribbon(centre[a:b], np.full(b - a, -sw) + wob(1.0)[:b - a] if False else np.full(b - a, -sw), np.full(b - a, sw))], int(item['wet'])))
    return out


def distance_field(rut_items, tile, cells=160):
    """Distance (in picture dots) from every spot of a coarse grid to the nearest rut centre line, whether the spot is on the lit side, and the local rut direction.
    The picture wraps around (the shortest way round counts). Plain numpy: the rut lines are turned into a cloud of points about 6 dots apart and every grid spot looks
    for its nearest point. Returns (distance, lit side 0/1, direction) arrays of shape (cells, cells[, 2])."""
    points, tangents = [], []
    for item in rut_items:
        pts = np.asarray(item['p'], np.float64)
        for i in range(len(pts) - 1):
            seg = pts[i + 1] - pts[i]
            length = float(np.linalg.norm(seg))
            if length < 1e-6:
                continue
            n = max(int(length / 6.0), 1)
            t = seg / length
            for k in range(n):
                points.append(pts[i] + seg * (k + 0.5) / n)
                tangents.append(t)
    if not points:
        return np.full((cells, cells), 1e6), np.zeros((cells, cells), np.int8), np.zeros((cells, cells, 2))
    points = np.mod(np.array(points), tile)
    tangents = np.array(tangents)
    gx = (np.arange(cells) + 0.5) / cells * tile
    gxx, gyy = np.meshgrid(gx, gx)
    grid = np.stack([gxx.ravel(), gyy.ravel()], axis=1)
    best = np.full(len(grid), 1e18); best_index = np.zeros(len(grid), np.int64)
    for start in range(0, len(points), 400):
        chunk = points[start:start + 400]
        delta = grid[:, None, :] - chunk[None, :, :]
        delta -= tile * np.round(delta / tile)
        d2 = (delta ** 2).sum(-1)
        j = d2.argmin(1)
        v = d2[np.arange(len(grid)), j]
        better = v < best
        best[better] = v[better]; best_index[better] = start + j[better]
    delta = grid - points[best_index]
    delta -= tile * np.round(delta / tile)
    side = ((delta @ np.array([-0.7071, -0.7071])) > 0).astype(np.int8)
    return np.sqrt(best).reshape(cells, cells), side.reshape(cells, cells), tangents[best_index].reshape(cells, cells, 2)


def smooth_field(rng, tile, length_scale, cells=256):
    """A slowly changing random number field over the tile that repeats exactly (white noise blurred with wrap-around, done with an FFT), scaled to mean 0 and spread 1;
    returns a function (x, y arrays in picture dots) -> values."""
    noise = rng.normal(size=(cells, cells))
    sigma = max(length_scale / tile * cells, 0.5)
    freq = np.fft.fftfreq(cells)
    gauss = np.exp(-2.0 * (math.pi * sigma) ** 2 * (freq[:, None] ** 2 + freq[None, :] ** 2))
    blurred = np.real(np.fft.ifft2(np.fft.fft2(noise) * gauss))
    blurred = (blurred - blurred.mean()) / max(blurred.std(), 1e-9)

    def value(x, y):
        i = np.mod((np.asarray(x) / tile * cells).astype(int), cells)
        j = np.mod((np.asarray(y) / tile * cells).astype(int), cells)
        return blurred[j, i]
    return value


def normal_cdf(z):
    return 0.5 * (1.0 + np.vectorize(math.erf, otypes=[float])(np.asarray(z) / math.sqrt(2.0)))


def clod_shapes(layer, rut_items, tile, seed):
    """Flat ground clods ("crumbly ground"): many small irregular polygons in earth colours. Where a clod is, and what colour it gets, follows the ruts: the chance of each
    colour depends on the distance from the nearest rut and on which side (lit / shaded) it is; clods are stretched along the rut. Numbers come from the description:
    {'count': n, 'tones': [palette numbers], 'bins': [distance edges], 'chances': [side][bin][tone], 'area_log_mean', 'area_log_sd', 'aspect_median', 'along': 0..1}"""
    rng = np.random.default_rng(seed)
    n = int(layer['count'])
    if n <= 0:
        return []
    dist, side, tang = distance_field(rut_items, tile, cells=int(round(160 * tile / 1254.0)))     # the grid has the same dots-per-cell at every tile size
    cells = dist.shape[0]
    tones = np.asarray(layer['tones'])
    chances = np.asarray(layer['chances'], np.float64)          # side x bin x tone
    bins = np.asarray(layer['bins'], np.float64)
    skip = set(layer.get('skip', []))
    xs, ys = rng.uniform(0, tile, n), rng.uniform(0, tile, n)
    ci, cj = np.minimum((xs / tile * cells).astype(int), cells - 1), np.minimum((ys / tile * cells).astype(int), cells - 1)
    d, sd, tg = dist[cj, ci], side[cj, ci], tang[cj, ci]
    b = np.clip(np.searchsorted(bins, d, side='right') - 1, 0, chances.shape[1] - 1)
    cdf = np.cumsum(chances[sd, b], axis=1)
    cdf /= np.maximum(cdf[:, -1:], 1e-9)
    # which tone: a number q between 0 and 1 that is partly slowly changing over the picture (zones of similar tone) and partly random per clod; the tones are listed from
    # dark to light, so a slowly changing q gives patches of dark clods and patches of light clods. q is uniform overall, so the chance table is kept.
    zone = layer.get('zone', {'scale': 30.0, 'weight': 0.0})
    mix = float(zone.get('weight', 0.0))
    field = smooth_field(rng, tile, float(zone.get('scale', 30.0)))
    q = normal_cdf(math.sqrt(mix) * field(xs, ys) + math.sqrt(1.0 - mix) * rng.normal(size=n))
    tone_index = (q[:, None] > cdf).sum(axis=1).clip(0, len(tones) - 1)
    area = np.exp(rng.normal(layer['area_log_mean'], layer['area_log_sd'], n)).clip(6, 900)
    aspect = np.exp(rng.normal(math.log(layer.get('aspect_median', 1.9)), 0.35, n)).clip(1.0, 6.0)
    major = np.sqrt(area * aspect / math.pi)
    minor = np.sqrt(area / aspect / math.pi)
    flow = np.arctan2(tg[:, 1], tg[:, 0])
    near = (d < layer.get('flow_range', 60)) & (np.linalg.norm(tg, axis=1) > 0.5)
    along = float(layer.get('along', 0.8))
    angle = np.where(near & (rng.random(n) < along), flow + rng.normal(0, 0.35, n), rng.uniform(0, math.pi, n))
    sides = rng.integers(5, 9, n)
    order = np.argsort(-area)                                    # big clods first, small ones on top
    out = []
    for i in order:
        colour = int(tones[tone_index[i]])
        if colour in skip:
            continue
        k = int(sides[i])
        ang = np.linspace(0, 2 * math.pi, k, endpoint=False) + rng.uniform(0, 2 * math.pi / k)
        rad = rng.uniform(0.75, 1.25, k)
        px, py = major[i] * rad * np.cos(ang), minor[i] * rad * np.sin(ang)
        c, s_ = math.cos(angle[i]), math.sin(angle[i])
        pts = np.stack([xs[i] + c * px - s_ * py, ys[i] + s_ * px + c * py], axis=1)
        out.append(([pts], colour))
    return out


def make_shape_list(description):
    """[(list of polygons (n x 2, tile dots, y down), palette index), ...] back to front. The first shape is the whole-tile ground."""
    tile = float(description['tile'])
    shapes = []
    ground = description.get('ground', {'colour': 0})
    shapes.append(([np.array([[0, 0], [tile, 0], [tile, tile], [0, tile]], np.float64)], int(ground['colour'])))
    for layer in description.get('layers', []):
        kind = layer['type']
        if kind == 'puddles':
            for p in layer['items']:
                shapes.append(([traced_polygon(p['p'])], int(p['b'])))
                for colour, steps in p.get('t', []):
                    shapes.append(([traced_polygon(steps)], int(colour)))
        elif kind == 'stones':
            for base, outline, faces in layer['items']:
                shapes.append(([traced_polygon(outline)], int(base)))
                for colour, steps in faces:
                    shapes.append(([traced_polygon(steps)], int(colour)))
        elif kind == 'patches':
            for colour, steps in layer['items']:
                shapes.append(([traced_polygon(steps)], int(colour)))
        elif kind == 'ruts':
            shapes.extend(rut_shapes(layer, tile, int(layer.get('seed', description.get('seed', 1)))))
        elif kind == 'clods':
            rut_layer = next((l for l in description['layers'] if l['type'] == 'ruts'), {'items': []})
            shapes.extend(clod_shapes(layer, rut_layer['items'], tile, int(layer.get('seed', description.get('seed', 1)) + 1)))
        elif kind == 'shapes':
            # ready-made flat polygons made by a sampler (floating-point dot corners): [[colour, [[x, y], ...]], ...]
            for colour, pts in layer['items']:
                shapes.append(([np.asarray(pts, np.float64)], int(colour)))
    return shapes


def draw_preview(description, size=1254, scale=3, shapes=None):
    """Numpy/OpenCV painter: the same shapes drawn at `scale` x the resolution and shrunk back. Returns a BGR picture. Quick look, no Blender."""
    import cv2
    tile = float(description['tile'])
    shapes = shapes if shapes is not None else make_shape_list(description)
    palette = np.array(description['palette'], np.uint8)[:, ::-1]
    k = scale * size / tile
    canvas = np.zeros((int(size * scale), int(size * scale), 3), np.uint8)
    for polygons, index in shapes:
        colour = tuple(int(v) for v in palette[index])
        for pts in polygons:
            pts = np.asarray(pts, np.float64)
            pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
            for ox, oy in wrap_copy_count(pts, tile):
                q = ((pts + [ox * tile, oy * tile]) * k).round().astype(np.int32)
                cv2.fillPoly(canvas, [q], colour, lineType=cv2.LINE_8)
    return cv2.resize(canvas, (size, size), interpolation=cv2.INTER_AREA)
