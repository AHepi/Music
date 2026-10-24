"""What this does: the GROUND part of the forest village (owner ground_and_roads). It is built first, alone, and frozen as ground.blend; every other part is seated on it.
It makes, in one idempotent stage:
  * the ground: one continuous height field in seven objects that share their border vertices and never overlap: 'Ground forest floor' (a disc of 190 m round the middle, the whole forest the trees
    stand in), 'Ground clearing', 'Ground road high_road', 'Ground road stable_lane', 'Ground yard', 'Ground verge high_road', 'Ground verge stable_lane'. One constrained Delaunay triangulation of a point
    cloud that is fine where the cameras look (road-aligned rows, the yard) and coarse far away; the lines between regions (road edge, verge edge, lane, yard, clearing edge) are found as contour lines
    of the region fields and kept as mesh edges, so every border is exact and shared, and every triangle goes to the object whose region holds its centre.
  * level pads (flat to within 0.25 m) under each building and 1.5 m round it, a level yard in front of the stable doorway, soft large relief (the clearing falls about 1 m from the north-east to the
    south-west), a few low hollows, 3 potholes on the high road, 2 in the yard, and hoof prints and a turning loop of ruts across the yard.
  * the kit's roads step (pk.shape_roads) on the roads of place-settings.json: ruts a cart's gauge apart, banks, hoof prints, grass crown, puddle hollows.
  * the world round the place: three closed rings of hills (role backdrop: paint that takes the light, no emission, casting no shadow) and, in the same mesh as the near ring, the plain ground from the floor's
    edge out to 900 m (so the ground-role objects stay small enough for the audit's plants and litter counts; see R_FLOOR), a gradient sky with no haze, one sun lamp from the south-east.
  * the four view cameras (clip end 3000 m), the render size 1200 x 800, and the kit's plan pictures (so pk.is_keep_clear answers on this ground).
The ground code is plain numpy (testable without Blender); the Blender part is from `YARD_ROADS` down (apply is at the bottom). Every object gets its owner and its role as it is made.
A concrete example: apply({}) twice gives the same scene: the stage first forgets everything it made (found by place_owner), then builds again with the same seeds.
"""
import json
import math
import os
import sys
import time

import numpy as np

OWNER = 'ground_and_roads'
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(os.path.dirname(HERE), 'plan')
KIT_FALLBACK = '/home/user/Music/plugins/explainer-film/kit/place-kit'

# ------------------------------------------------------------------ the plan's numbers (metres; x east, y north, z up)
HALF = 900.0                                     # the plain runs out to this (the far skirt, role backdrop)
R_FLOOR = 190.0                                  # the ground objects (role ground.*) are a disc of this radius round the middle: the trees stand inside it (30 to 150 m). Measured: the audit asks for
                                                 # 20 plants and 30 litter pieces per 100 square metres of ground, so a ground of 3,240,000 square metres (900 m each way) would need 648,000 plants and
                                                 # 972,000 litter pieces against a cap of 400,000 pieces (and the growth step ran over 11 minutes without finishing on it). The plain beyond R_FLOOR is the skirt of the backdrop.
N_CIRCLE = 480                                   # points on the floor's round edge (and the same points start the skirt, so the two share their edge)
CLEARING = (-50.0, -32.0, 60.0, 50.0)            # x0, y0, x1, y1
YARD = (14.0, 24.0, 34.0, 36.0)
# footprints from the plan (the lean-to of A reaches x -40.05); each pad is the footprint and 1.5 m round it
PAD_MARGIN = 1.5
PADS = {
    'cottage A': (-40.05, 7.6, -26.45, 12.4),
    'cottage B': (-9.2, 7.2, -2.8, 11.8),
    'cottage C': (-29.7, -12.8, -22.3, -8.2),
    'cottage D': (2.15, -10.2, 5.85, -5.8),
    'stable': (19.1, 36.0, 28.9, 42.0),
}
DOORWAY = (21.4, 34.6, 26.6, 36.8)
PAD_BLEND = 3.5                                  # metres over which a pad runs back into the land
NOISE_SEED = 7

ROAD_RIBBON_HALF = {'high_road': 4.25, 'stable_lane': 3.4}
ROAD_EDGE = {'high_road': 2.5, 'stable_lane': 1.7}          # half widths of the dirt strips
VERGE_WIDTH = 1.2
CAMERA_SPOTS = {                                 # where the cameras stand (x, y), for how fine the ground is near them
    'road_eye': (-62.0, -3.7), 'cottage_close': (-12.764, 3.033), 'stable_close': (28.5, 25.5), 'wide': (-50.145, -27.903),
}
S0 = 0.07                                        # the finest lattice spacing; level k is S0 * 2**k (nested lattices)
LEVELS = 11


# ------------------------------------------------------------------ small maths
def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _hash(ix, iy, seed):
    n = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF) / float(0xFFFFFF) * 2.0 - 1.0


def vnoise(x, y, scale, seed):
    """Smooth value noise in [-1, 1] (repeatable)."""
    xs, ys = np.asarray(x, dtype=np.float64) / scale, np.asarray(y, dtype=np.float64) / scale
    xi, yi = np.floor(xs), np.floor(ys)
    fx, fy = xs - xi, ys - yi
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(xi, yi, seed), _hash(xi + 1, yi, seed)
    c, d = _hash(xi, yi + 1, seed), _hash(xi + 1, yi + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, scales, weights, seed):
    total = np.zeros(np.shape(x))
    for index, (scale, weight) in enumerate(zip(scales, weights)):
        total = total + weight * vnoise(x, y, scale, seed + 17 * index)
    return total / float(sum(weights))


class Poly:
    """A polyline with its distance function (distance, signed lateral offset (+ left), arclength, nearest segment)."""

    def __init__(self, points):
        self.p = np.asarray(points, dtype=np.float64)
        d = np.diff(self.p, axis=0)
        self.len = np.hypot(d[:, 0], d[:, 1])
        self.u = d / self.len[:, None]
        self.n = np.stack([-self.u[:, 1], self.u[:, 0]], axis=1)
        self.cum = np.concatenate([[0.0], np.cumsum(self.len)])
        self.total = float(self.cum[-1])

    def query(self, P):
        P = np.asarray(P, dtype=np.float64).reshape(-1, 2)
        best = np.full(len(P), np.inf)
        signed = np.zeros(len(P))
        along = np.zeros(len(P))
        index = np.zeros(len(P), dtype=np.int64)
        for i in range(len(self.len)):
            a, u = self.p[i], self.u[i]
            t = np.clip((P - a) @ u, 0.0, self.len[i])
            q = a + t[:, None] * u
            d = np.hypot(P[:, 0] - q[:, 0], P[:, 1] - q[:, 1])
            side = u[0] * (P[:, 1] - a[1]) - u[1] * (P[:, 0] - a[0])
            closer = d < best
            best = np.where(closer, d, best)
            signed = np.where(closer, np.where(side >= 0, d, -d), signed)
            along = np.where(closer, self.cum[i] + t, along)
            index = np.where(closer, i, index)
        return best, signed, along, index

    def dist(self, P):
        return self.query(P)[0]

    def point_and_direction(self, s):
        """Point and unit direction at arclength s (the end segments are extended in a straight line)."""
        s = np.asarray(s, dtype=np.float64)
        i = np.clip(np.searchsorted(self.cum, s, side='right') - 1, 0, len(self.len) - 1)
        t = s - self.cum[i]
        return self.p[i] + t[:, None] * self.u[i], self.u[i], i


def rect_signed_distance(x, y, rect):
    """Negative inside the rectangle, positive outside (the distance to it)."""
    dx = np.maximum(rect[0] - x, x - rect[2])
    dy = np.maximum(rect[1] - y, y - rect[3])
    outside = np.hypot(np.maximum(dx, 0.0), np.maximum(dy, 0.0))
    inside = np.minimum(np.maximum(dx, dy), 0.0)
    return outside + inside


def rect_outside_distance(x, y, rect):
    return np.maximum(rect_signed_distance(x, y, rect), 0.0)


def clearing_edge(x, y):
    """Signed distance to the clearing's wandering edge (negative inside): the plan's rectangle, pushed in and out by a couple of metres so the meadow meets the forest floor like a real clearing."""
    return rect_signed_distance(x, y, CLEARING) + 2.6 * vnoise(x, y, 19.0, 51) + 1.3 * vnoise(x, y, 6.5, 52)


# ------------------------------------------------------------------ the land (height before the roads step)
BASINS = [(-40.0, -4.5, 6.0, 0.15), (-8.0, 1.2, 5.0, 0.12), (12.0, 0.2, 5.0, 0.11), (-31.0, -22.0, 8.0, 0.15), (33.0, 14.0, 6.0, 0.10)]   # x, y, radius, depth: the low hollows the ruts drain to
# potholes on the high road (x, y, half length a, half width b, depth, turn in degrees); y is the road's own centre line there
POTHOLES_ROAD = [(-54.0, None, 0.30, 0.22, 0.09, 20.0, 0.20), (-33.0, None, 0.24, 0.20, 0.07, 70.0, -1.90), (-6.0, None, 0.32, 0.22, 0.10, 110.0, 1.30)]
POTHOLES_YARD = [(21.0, 28.0, 0.30, 0.24, 0.08, 40.0), (27.6, 29.8, 0.26, 0.22, 0.07, 120.0)]


def smooth_land(x, y):
    """The large soft relief: the clearing falls about 1.0 m from the north-east to the south-west, a few low hollows, lumps that stay under 0.25 m (0.11 m inside the clearing)."""
    u = ((x - 5.0) + (y - 9.0)) / math.sqrt(2.0)
    slope = 0.784 * np.tanh(u / 90.0)                           # falls 1.0 m from the clearing's north-east corner to its south-west corner, then levels off outside
    sd = rect_signed_distance(x, y, CLEARING)
    amp = 0.11 + (0.25 - 0.11) * smoothstep(0.0, 30.0, sd)
    lumps = amp * fbm(x, y, (46.0, 23.0, 11.5), (0.6, 0.3, 0.1), NOISE_SEED)
    z = slope + lumps
    for bx, by, radius, depth in BASINS:
        z = z - depth * np.exp(-(((x - bx) ** 2 + (y - by) ** 2) / (radius * 0.55) ** 2))
    return z


def pad_rect(name):
    x0, y0, x1, y1 = PADS[name]
    return (x0 - PAD_MARGIN, y0 - PAD_MARGIN, x1 + PAD_MARGIN, y1 + PAD_MARGIN)


def pad_heights():
    """Each pad's height: the smooth land at its middle (the least cutting and filling)."""
    out = {}
    for name in PADS:
        r = pad_rect(name)
        out[name] = float(smooth_land(np.array([(r[0] + r[2]) / 2.0]), np.array([(r[1] + r[3]) / 2.0]))[0])
    return out


def potholes_dz(x, y, holes):
    dz = np.zeros(np.shape(x))
    for hx, hy, a, b, depth, turn in holes:
        t = math.radians(turn)
        dx, dy = x - hx, y - hy
        u = (dx * math.cos(t) + dy * math.sin(t)) / a
        v = (-dx * math.sin(t) + dy * math.cos(t)) / b
        r2 = u * u + v * v
        dz = dz - depth * np.exp(-(r2 ** 1.5)) + 0.18 * depth * np.exp(-(((np.sqrt(r2) - 1.35) / 0.3) ** 2))      # a flat-ish bottom and a small lip
    return dz


def base_height(x, y, ctx):
    """The ground height BEFORE the roads step: relief, pads, potholes and the yard's own hoof prints and turning ruts."""
    from_roads = ctx['yard_roads']
    z = smooth_land(x, y)
    for name, pad_z in ctx['pad_z'].items():
        r = pad_rect(name)
        w = 1.0 - smoothstep(0.0, PAD_BLEND, rect_outside_distance(x, y, r))
        z = z + (pad_z - z) * w
    z = z + potholes_dz(x, y, ctx['holes_road'])
    z = z + potholes_dz(x, y, POTHOLES_YARD)
    P = np.stack([np.ravel(x), np.ravel(y)], axis=1)
    for road in ctx.get('hoof_roads', []):
        # the kit digs a hoof print 2 cm deep; a loaded horse in damp ground leaves 4 to 6 cm, so the same prints (same places, found with the kit's own function) are dug 3 cm deeper
        near = ctx['polys'][road['name']].dist(P) < road['width'] / 2.0 + 0.5
        if near.any():
            only_hoof = {'polyline': road['polyline'], 'width': road['width'], 'gauge': road.get('gauge', 1.4), 'rut_depth': 0.0, 'hoof': True, 'centre_grass': False}
            extra = np.zeros(len(P))
            extra[near] = ctx['hoof_function'](P[near], only_hoof, 1)[0]
            z = z + extra.reshape(np.shape(x))
    if from_roads:
        near = (P[:, 0] > YARD[0] - 3) & (P[:, 0] < YARD[2] + 3) & (P[:, 1] > YARD[1] - 3) & (P[:, 1] < YARD[3] + 1)
        if near.any():
            extra = np.zeros(len(P))
            for road in from_roads:
                dz, _ = ctx['road_function'](P[near], road, 5)
                extra[near] += dz
            z = z + extra.reshape(np.shape(x))
    return z


# ------------------------------------------------------------------ what each place is made of (the region of every point; each region's edge is a contour that the mesh follows exactly)
LABELS = ['forest', 'clearing', 'road_high', 'road_lane', 'yard', 'verge_high', 'verge_lane']
LANE_STOPS_AT = YARD[3]                      # the lane's round end does not reach in under the stable


def field_road_high(x, y, ctx):
    return ctx['high'].dist(np.stack([np.ravel(x), np.ravel(y)], axis=1)).reshape(np.shape(x)) - (ROAD_EDGE['high_road'] + 0.10 * vnoise(x, y, 6.0, 31))


def field_verge_high(x, y, ctx):
    return ctx['high'].dist(np.stack([np.ravel(x), np.ravel(y)], axis=1)).reshape(np.shape(x)) - (ROAD_EDGE['high_road'] + VERGE_WIDTH + 0.32 * vnoise(x, y, 9.0, 33))


def field_road_lane(x, y, ctx):
    d = ctx['lane'].dist(np.stack([np.ravel(x), np.ravel(y)], axis=1)).reshape(np.shape(x))
    return np.maximum(d - (ROAD_EDGE['stable_lane'] + 0.08 * vnoise(x, y, 5.0, 35)), y - LANE_STOPS_AT)


def field_verge_lane(x, y, ctx):
    d = ctx['lane'].dist(np.stack([np.ravel(x), np.ravel(y)], axis=1)).reshape(np.shape(x))
    return np.maximum(d - (ROAD_EDGE['stable_lane'] + VERGE_WIDTH + 0.28 * vnoise(x, y, 7.0, 37)), y - LANE_STOPS_AT)


def field_yard(x, y, ctx=None):
    """The trodden yard: the plan's rectangle with three wandering edges; the edge along the stable stays straight."""
    return np.maximum.reduce([YARD[0] + 0.3 * vnoise(x, y, 5.0, 41) - x, x - YARD[2] - 0.3 * vnoise(x, y, 5.0, 42), YARD[1] + 0.3 * vnoise(x, y, 5.0, 43) - y, y - YARD[3]])


def field_clearing(x, y, ctx=None):
    return clearing_edge(x, y)


def region_labels(P, ctx):
    """The label number (index in LABELS) of each point (n, 2)."""
    x, y = P[:, 0], P[:, 1]
    label = np.full(len(P), LABELS.index('forest'), dtype=np.int64)
    label[field_clearing(x, y) < 0] = LABELS.index('clearing')
    label[field_verge_lane(x, y, ctx) < 0] = LABELS.index('verge_lane')
    label[field_verge_high(x, y, ctx) < 0] = LABELS.index('verge_high')
    label[field_road_lane(x, y, ctx) < 0] = LABELS.index('road_lane')
    label[field_yard(x, y) < 0] = LABELS.index('yard')
    label[field_road_high(x, y, ctx) < 0] = LABELS.index('road_high')
    return label


def contour(f, x0, y0, x1, y1, cell):
    """The zero line of a scalar field f(x, y) over a box, by marching squares: (points (n, 2), segments (m, 2) as point numbers). Neighbouring cells share their crossing points, so the
    line is one connected chain of edges about `cell` long."""
    nx, ny = int(math.ceil((x1 - x0) / cell)), int(math.ceil((y1 - y0) / cell))
    xs, ys = x0 + np.arange(nx + 1) * cell, y0 + np.arange(ny + 1) * cell
    X, Y = np.meshgrid(xs, ys)
    F = f(X, Y)
    positive = F > 0
    cross_h = positive[:, :-1] != positive[:, 1:]
    th = F[:, :-1] / np.where(cross_h, F[:, :-1] - F[:, 1:], 1.0)
    hp = np.stack([X[:, :-1] + th * cell, Y[:, :-1]], axis=-1)[cross_h]
    cross_v = positive[:-1, :] != positive[1:, :]
    tv = F[:-1, :] / np.where(cross_v, F[:-1, :] - F[1:, :], 1.0)
    vp = np.stack([X[:-1, :], Y[:-1, :] + tv * cell], axis=-1)[cross_v]
    id_h = -np.ones(cross_h.shape, dtype=np.int64)
    id_h[cross_h] = np.arange(cross_h.sum())
    id_v = -np.ones(cross_v.shape, dtype=np.int64)
    id_v[cross_v] = len(hp) + np.arange(cross_v.sum())
    bottom, top, left, right = id_h[:-1, :], id_h[1:, :], id_v[:, :-1], id_v[:, 1:]
    ids = np.stack([bottom, right, top, left], axis=-1)
    present = ids >= 0
    count = present.sum(axis=-1)
    segments = []
    two = np.nonzero(count == 2)
    if len(two[0]):
        sel = ids[two]
        pres = present[two]
        order = np.argsort(~pres, axis=1, kind='stable')[:, :2]
        segments.append(np.take_along_axis(sel, order, axis=1))
    four = np.nonzero(count == 4)
    if len(four[0]):
        sel = ids[four]
        centre = 0.25 * (F[:-1, :-1] + F[:-1, 1:] + F[1:, 1:] + F[1:, :-1])[four]
        same = (centre > 0) == positive[:-1, :-1][four]
        # an ambiguous cell: join (bottom,right) and (top,left) when its middle agrees with its first corner, else (bottom,left) and (right,top)
        pairs_a = np.where(same[:, None], sel[:, [0, 1]], sel[:, [0, 3]])
        pairs_b = np.where(same[:, None], sel[:, [2, 3]], sel[:, [1, 2]])
        segments.append(pairs_a)
        segments.append(pairs_b)
    points = np.concatenate([hp, vp], axis=0)
    if not segments:
        return np.zeros((0, 2)), np.zeros((0, 2), dtype=np.int64)
    segs = np.concatenate(segments, axis=0)
    used = np.unique(segs)
    remap = -np.ones(len(points), dtype=np.int64)
    remap[used] = np.arange(len(used))
    return points[used], remap[segs]


def contour_pool(ctx, cell=0.12):
    """The edges between the regions: the line along which each region field is zero (the road edge, the verge's outer edge, the lane's, the yard's, the clearing's)."""
    jobs = []
    for fn, poly in ((field_road_high, ctx['high']), (field_verge_high, ctx['high'])):
        low, high = poly.p.min(axis=0) - 7.0, poly.p.max(axis=0) + 7.0
        jobs.append((lambda X, Y, fn=fn: fn(X, Y, ctx), low, high))
    for fn in (field_road_lane, field_verge_lane):
        poly = ctx['lane']
        low, high = poly.p.min(axis=0) - 5.0, poly.p.max(axis=0) + 5.0
        jobs.append((lambda X, Y, fn=fn: fn(X, Y, ctx), low, high))
    jobs.append((lambda X, Y: field_yard(X, Y), np.array([YARD[0] - 3.0, YARD[1] - 3.0]), np.array([YARD[2] + 3.0, YARD[3] + 1.0])))
    jobs.append((lambda X, Y: field_clearing(X, Y), np.array([CLEARING[0] - 14.0, CLEARING[1] - 14.0]), np.array([CLEARING[2] + 14.0, CLEARING[3] + 14.0])))
    pts, edges, offset = [], [], 0
    for f, low, high in jobs:
        p, e = contour(f, float(low[0]), float(low[1]), float(high[0]), float(high[1]), cell)
        pts.append(p)
        edges.append(e + offset)
        offset += len(p)
    return np.concatenate(pts, axis=0), np.concatenate(edges, axis=0)


def remove_near(P, C, radius):
    """The points of P that are not within `radius` of a point of C (a hashed grid of cells `radius` wide; the contour points are further apart than that, so a cell holds one)."""
    big = 1 << 20
    key_c = (np.floor(C[:, 0] / radius).astype(np.int64) + big) * (2 * big) + (np.floor(C[:, 1] / radius).astype(np.int64) + big)
    order = np.argsort(key_c)
    key_sorted, C_sorted = key_c[order], C[order]
    ix, iy = np.floor(P[:, 0] / radius).astype(np.int64) + big, np.floor(P[:, 1] / radius).astype(np.int64) + big
    near = np.zeros(len(P), dtype=bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            k = (ix + dx) * (2 * big) + (iy + dy)
            pos = np.clip(np.searchsorted(key_sorted, k), 0, len(key_sorted) - 1)
            match = key_sorted[pos] == k
            d = np.hypot(P[:, 0] - C_sorted[pos, 0], P[:, 1] - C_sorted[pos, 1])
            near |= match & (d < radius)
    return P[~near]


# ------------------------------------------------------------------ the point cloud (fine where the eye is, coarse far away)
def camera_distance(P):
    d = np.full(len(P), np.inf)
    for key, (cx, cy) in CAMERA_SPOTS.items():
        dd = np.hypot(P[:, 0] - cx, P[:, 1] - cy)
        d = np.minimum(d, dd * (1.8 if key == 'wide' else 1.0))
    return d


def size_field(P, ctx):
    """How far apart the points should be at each place (metres)."""
    x, y = P[:, 0], P[:, 1]
    sd = rect_signed_distance(x, y, CLEARING)
    far_cap = np.clip(0.08 * np.maximum(sd, 0.0), 4.0, 12.0)
    outside = np.minimum(0.28 + 0.25 * np.maximum(sd - 2.5, 0.0), far_cap)
    inside = np.minimum(0.56, 0.28 + 0.3 * np.maximum(-sd, 0.0))
    h = np.where(sd > 0, outside, inside)
    dh = ctx['high'].dist(P) - ROAD_RIBBON_HALF['high_road']
    dl = ctx['lane'].dist(P) - ROAD_RIBBON_HALF['stable_lane']
    nearest_ribbon = np.minimum(dh, dl)
    h = np.minimum(h, 0.2 + 0.3 * np.maximum(nearest_ribbon, 0.0))
    # the yard: 0.14 everywhere, 0.07 down the trodden strip from the lane to the doorway
    yard_d = rect_outside_distance(x, y, (YARD[0] - 0.4, YARD[1] - 0.4, YARD[2] + 0.4, YARD[3] + 0.4))
    h = np.minimum(h, 0.14 + 0.3 * yard_d)
    strip_d = rect_outside_distance(x, y, (22.8, 23.2, 25.8, 36.0))
    h = np.minimum(h, 0.07 + 0.25 * strip_d)
    return h


def level_of(h):
    return np.clip(np.rint(np.log2(np.maximum(h, S0) / S0)), 0, LEVELS - 1).astype(np.int64)


def lattice_points(ctx):
    """Nested square lattices (spacing S0 * 2**k, every point a multiple of its spacing): level k is used where the size field asks for about that spacing."""
    tile = 4.0
    # which 4 m tiles hold anything finer than level k: from the size field at the tile centres, less what it can fall by across a tile
    centres_axis = np.arange(-R_FLOOR + tile / 2.0, R_FLOOR, tile)
    cx, cy = np.meshgrid(centres_axis, centres_axis)
    C = np.stack([cx.ravel(), cy.ravel()], axis=1)
    h_tile = size_field(C, ctx) - 0.35 * tile * 0.75
    k_tile = level_of(np.maximum(h_tile, S0))
    pieces = []
    for k in range(LEVELS):
        s = S0 * (2 ** k)
        if s < tile:
            flagged = np.nonzero(k_tile <= k)[0]
            if len(flagged) == 0:
                continue
            per = int(math.ceil(tile / s))
            offs = np.arange(per) * s
            gx, gy = np.meshgrid(offs, offs)
            local = np.stack([gx.ravel(), gy.ravel()], axis=1)
            origin = C[flagged] - tile / 2.0
            # snap the tile origin to the lattice so every point is a multiple of s
            origin = np.round(origin / s) * s
            P = (origin[:, None, :] + local[None, :, :]).reshape(-1, 2)
        else:
            n = int(R_FLOOR // s)
            axis = np.arange(-n, n + 1) * s
            gx, gy = np.meshgrid(axis, axis)
            P = np.stack([gx.ravel(), gy.ravel()], axis=1)
        P = P[np.hypot(P[:, 0], P[:, 1]) <= R_FLOOR - 0.7]
        if len(P) == 0:
            continue
        want = level_of(size_field(P, ctx))
        # a point of lattice k is wanted here when the local level is k or finer-or-equal and the point belongs to no coarser lattice
        multiple_of_next = (np.abs(np.round(P[:, 0] / (2 * s)) * 2 * s - P[:, 0]) < 1e-9) & (np.abs(np.round(P[:, 1] / (2 * s)) * 2 * s - P[:, 1]) < 1e-9)
        keep = (want <= k) & (~multiple_of_next if k < LEVELS - 1 else True)
        pieces.append(P[keep])
    P = np.concatenate(pieces, axis=0)
    # no duplicates (a point can be generated by two overlapping tiles)
    key = np.round(P / 1e-4).astype(np.int64)
    _, unique = np.unique(key, axis=0, return_index=True)
    return P[np.sort(unique)]


# ------------------------------------------------------------------ the road ribbons (anisotropic, aligned with the road: fine where the cameras are)
def ribbon_profile(level):
    """Lateral offsets (both sides) for a ribbon of this fidelity (0 finest). Level 0 leaves out the middle strip (|t| < 0.28): that is made separately, finer, for the hoof prints."""
    if level == 0:
        spans = [(0.30, 1.10, 0.080), (1.10, 2.50, 0.28), (2.50, 4.25, 0.44)]
    elif level == 1:
        spans = [(0.0, 0.36, 0.10), (0.36, 1.10, 0.10), (1.10, 2.50, 0.28), (2.50, 4.25, 0.42)]
    else:
        spans = [(0.0, 0.40, 0.20), (0.40, 1.10, 0.14), (1.10, 2.50, 0.45), (2.50, 4.25, 0.60)]
    offsets = [] if level == 0 else [0.0]
    for index, (lo, hi, step) in enumerate(spans):
        count = max(1, int(round((hi - lo) / step)))
        values = np.linspace(lo, hi, count + 1)
        offsets.extend(values if (level == 0 and index == 0) else values[1:])
    offsets = np.array(offsets)
    return np.unique(np.round(np.concatenate([-offsets, offsets]), 6))


HOOF_STRIP = (0.23, 11, 0.046)          # half width of the middle strip, points across it, and the spacing along the road (finest ribbon only): a hoof print is 9 cm wide, so it needs points 4 to 5 cm apart


def ribbon_points(poly, half_width, ctx, is_lane=False):
    """Points on a road-aligned grid along a polyline (rows across the road, the spacing along it by how near a camera is), plus rows beyond both ends to cover the round ends."""
    ext = half_width + 0.3

    def position(s):
        s = float(s)
        if s < 0:
            return poly.p[0] + poly.u[0] * s
        if s > poly.total:
            return poly.p[-1] + poly.u[-1] * (s - poly.total)
        return poly.point_and_direction(np.array([s]))[0][0]

    stations = []
    s = -ext
    while s <= poly.total + ext:
        dc = float(camera_distance(np.array([position(s)]))[0])
        level = 0 if dc < 22.0 else (1 if dc < 62.0 else 2)
        stations.append((s, level))
        s += (0.09, 0.18, 0.42)[level]
    S = np.array([a for a, _ in stations])
    L = np.array([b for _, b in stations])

    def frame(S):
        inside = np.clip(S, 0.0, poly.total)
        base, direction, seg = poly.point_and_direction(inside)
        base = base + direction * (S - inside)[:, None]
        return base, np.stack([-direction[:, 1], direction[:, 0]], axis=1), seg

    base, normal, seg = frame(S)
    out = []
    for level in (0, 1, 2):
        offsets = ribbon_profile(level)
        sel = np.nonzero(L == level)[0]
        if len(sel) == 0:
            continue
        pts = base[sel][:, None, :] + normal[sel][:, None, :] * offsets[None, :, None]
        out.append((pts.reshape(-1, 2), np.repeat(seg[sel][:, None], len(offsets), axis=1).reshape(-1)))
    # the middle strip, where the rows are the finest
    half, count, along = HOOF_STRIP
    fine = []
    s = -ext
    while s <= poly.total + ext:
        if float(camera_distance(np.array([position(s)]))[0]) < 22.0:
            fine.append(s)
        s += along
    if fine:
        base2, normal2, seg2 = frame(np.array(fine))
        offsets = np.linspace(-half, half, count)
        pts = base2[:, None, :] + normal2[:, None, :] * offsets[None, :, None]
        out.append((pts.reshape(-1, 2), np.repeat(seg2[:, None], count, axis=1).reshape(-1)))
    P = np.concatenate([a for a, _ in out], axis=0)
    G = np.concatenate([b for _, b in out], axis=0)
    d, _, _, nearest = poly.query(P)
    keep = (d <= half_width) & (nearest == G)
    return P[keep]


def hex_to_linear(text, gain=1.0):
    text = text.lstrip('#')
    v = [int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in v]
    return (lin[0] * gain, lin[1] * gain, lin[2] * gain, 1.0)


def circle_points(n=N_CIRCLE, radius=R_FLOOR):
    """The floor's round edge: the same points are the first ring of the skirt."""
    t = 2.0 * math.pi * np.arange(n) / n
    return np.stack([radius * np.cos(t), radius * np.sin(t)], axis=1).astype(np.float32).astype(np.float64)


def assemble_points(ctx):
    high, lane = ctx['high'], ctx['lane']
    ribbon_h = ribbon_points(high, ROAD_RIBBON_HALF['high_road'], ctx)
    ribbon_l = ribbon_points(lane, ROAD_RIBBON_HALF['stable_lane'], ctx, is_lane=True)
    # the lane ribbon does not enter the high road's ribbon or the yard (they have their own points)
    dh = high.dist(ribbon_l)
    in_yard = ((ribbon_l[:, 0] > YARD[0] - 0.3) & (ribbon_l[:, 0] < YARD[2] + 0.3) & (ribbon_l[:, 1] > YARD[1] - 0.1))
    ribbon_l = ribbon_l[(dh > ROAD_RIBBON_HALF['high_road'] + 0.05) & ~in_yard]
    lat = lattice_points(ctx)
    s_here = S0 * (2 ** level_of(size_field(lat, ctx)))
    near_h = high.dist(lat) < ROAD_RIBBON_HALF['high_road'] + 0.35 * s_here
    dl = lane.dist(lat)
    yard_zone = ((lat[:, 0] > YARD[0] - 0.3) & (lat[:, 0] < YARD[2] + 0.3) & (lat[:, 1] > YARD[1] - 0.1))
    near_l = (dl < ROAD_RIBBON_HALF['stable_lane'] + 0.35 * s_here) & ~yard_zone & (high.dist(lat) > ROAD_RIBBON_HALF['high_road'])
    lat = lat[~near_h & ~near_l]
    edge = circle_points()
    C, E = contour_pool(ctx)
    P = np.concatenate([ribbon_h, ribbon_l, lat, edge], axis=0)
    # drop points closer than 2.5 cm to another (two ribbons or a ribbon and a lattice meeting), and the ones that lie on a region's edge line (the line's own points stay)
    key = np.round(P / 0.025).astype(np.int64)
    _, unique = np.unique(key, axis=0, return_index=True)
    P = P[np.sort(unique)]
    P = remove_near(P, C, 0.05)
    P = np.concatenate([C, P], axis=0)           # the contour points come first, so the edge numbers are their own
    return P, E, {'ribbon_high': len(ribbon_h), 'ribbon_lane': len(ribbon_l), 'lattice': len(lat), 'edge': len(edge), 'contour_points': len(C), 'contour_edges': len(E), 'points_total': len(P)}


def make_context(settings_roads=None):
    from_roads = []
    ctx = {'pad_z': pad_heights(), 'holes_road': [], 'yard_roads': from_roads}
    roads = settings_roads
    if roads is None:
        data = json.load(open(os.path.join(PLAN, 'place-settings.json')))
        roads = data['roads']
    by_name = {r['name']: r for r in roads}
    ctx['roads'] = roads
    ctx['high'] = Poly(by_name['high_road']['polyline'])
    ctx['lane'] = Poly(by_name['stable_lane']['polyline'])
    # potholes on the high road: y is the road's own centre line plus a side offset
    holes = []
    for hx, _, a, b, depth, turn, side in POTHOLES_ROAD:
        p, u, _ = ctx['high'].point_and_direction(np.array([0.0]))
        d, signed, along, idx = ctx['high'].query(np.array([[hx, 0.0]]))
        # walk along the polyline to the point whose x is hx
        s_guess = along[0]
        for _ in range(8):
            q, uu, _ = ctx['high'].point_and_direction(np.array([s_guess]))
            s_guess += (hx - q[0, 0]) / max(uu[0, 0], 0.2)
        q, uu, _ = ctx['high'].point_and_direction(np.array([s_guess]))
        n = np.array([-uu[0, 1], uu[0, 0]])
        c = q[0] + n * side
        holes.append((float(c[0]), float(c[1]), a, b, depth, turn))
    ctx['holes_road'] = holes
    return ctx


SKIRT_RINGS = 18
SKIRT_COLOUR = '#58492F'                         # forest-floor brown, a little lighter than the kit's own (the plain is far away and flat)
SKIRT_GAINS = (0.95, 0.95, 1.05)


def skirt_arrays(ctx_unused=None):
    """The plain beyond the floor: rings of points from the floor's round edge out to HALF (the first ring IS the floor's edge points, so the two meshes share their border). Its height is the land,
    running back to flat by 120 m beyond the edge (the hill rings stand on it). Returns points (n, 3), triangles (m, 3), colour (n, 3) in linear light."""
    n = N_CIRCLE
    t = 2.0 * math.pi * np.arange(n) / n
    radii = R_FLOOR * (HALF / R_FLOOR) ** (np.arange(SKIRT_RINGS + 1) / SKIRT_RINGS)
    X = radii[None, :] * np.cos(t)[:, None]
    Y = radii[None, :] * np.sin(t)[:, None]
    ring0 = circle_points()
    X[:, 0], Y[:, 0] = ring0[:, 0], ring0[:, 1]
    X32, Y32 = X.astype(np.float32).astype(np.float64), Y.astype(np.float32).astype(np.float64)
    fade = 1.0 - smoothstep(R_FLOOR, R_FLOOR + 120.0, np.hypot(X32, Y32))
    Z = smooth_land(X32, Y32) * fade
    index = np.arange(n * (SKIRT_RINGS + 1)).reshape(n, SKIRT_RINGS + 1)
    nxt = np.roll(index, -1, axis=0)
    quads = np.stack([index[:, :-1], nxt[:, :-1], nxt[:, 1:], index[:, 1:]], axis=-1).reshape(-1, 4)
    tris = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], axis=0)
    co = np.column_stack([X32.ravel(), Y32.ravel(), Z.ravel()])
    a_, b_, c_ = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    if np.mean((b_[:, 0] - a_[:, 0]) * (c_[:, 1] - a_[:, 1]) - (b_[:, 1] - a_[:, 1]) * (c_[:, 0] - a_[:, 0])) < 0:
        tris = tris[:, [0, 2, 1]]
    tone = 1.0 + 0.10 * vnoise(co[:, 0], co[:, 1], 90.0, 61) + 0.07 * vnoise(co[:, 0], co[:, 1], 32.0, 62) + 0.04 * vnoise(co[:, 0], co[:, 1], 11.0, 63)
    base = np.array(hex_to_linear(SKIRT_COLOUR))[:3] * np.array(SKIRT_GAINS)
    return co, tris, np.clip(base[None, :] * tone[:, None], 0.0, 1.0)


YARD_ROADS = [
    # a cart that turned in the yard: a loop of ruts 1.4 m apart with hoof prints down its middle, and a horse led away to the west (hoof prints only)
    {'name': 'yard_swing', 'polyline': [[24.0, 30.2], [25.5, 31.9], [27.6, 32.2], [29.0, 30.7], [29.4, 28.3], [28.2, 26.1], [26.0, 24.7], [24.2, 23.5]], 'width': 3.0, 'gauge': 1.4,
     'rut_depth': 0.055, 'hoof': True, 'centre_grass': False},
    {'name': 'yard_west', 'polyline': [[23.4, 34.0], [21.0, 32.6], [19.0, 30.3], [16.6, 27.4]], 'width': 1.6, 'gauge': 1.4, 'rut_depth': 0.0, 'hoof': True, 'centre_grass': False},
]


def _kit_roads_module():
    try:
        from place_kit.surfaces import roads as module
    except ImportError:
        for candidate in (os.path.join(os.environ.get('EXPLAINER_FILM_KIT', ''), 'place-kit'), KIT_FALLBACK):
            if candidate and os.path.isdir(candidate) and candidate not in sys.path:
                sys.path.insert(0, candidate)
        from place_kit.surfaces import roads as module
    return module


def yard_road_function(P, road, seed, radius=0.085, depth=0.03):
    """The kit's own road shaper, with the hoof dimple set to the given size (the yard's coarser mesh wants it a little wider; the settings' roads get 3 cm more depth of the same print)."""
    module = _kit_roads_module()
    old = (module.HOOF_RADIUS, module.HOOF_DEPTH)
    module.HOOF_RADIUS, module.HOOF_DEPTH = radius, depth
    try:
        return module.road_height_offset(P, road, seed)
    finally:
        module.HOOF_RADIUS, module.HOOF_DEPTH = old


def make_context_full(settings_roads=None):
    ctx = make_context(settings_roads)
    ctx['yard_roads'] = YARD_ROADS
    ctx['road_function'] = yard_road_function
    ctx['hoof_roads'] = [r for r in ctx['roads'] if r.get('hoof')]
    ctx['polys'] = {r['name']: Poly(r['polyline']) for r in ctx['roads']}
    ctx['hoof_function'] = lambda P, road, seed: yard_road_function(P, road, seed, radius=0.065, depth=0.03)
    return ctx


def triangulate(P, E):
    """Blender's own constrained Delaunay triangulation of the points: the edges E (the lines between regions) are kept as edges of the mesh, so each region's border is exact and shared."""
    from mathutils import Vector
    from mathutils.geometry import delaunay_2d_cdt
    verts = [Vector((float(x), float(y))) for x, y in P]
    out_v, _, out_f, _, _, _ = delaunay_2d_cdt(verts, [tuple(int(i) for i in e) for e in E], [], 0, 1e-7)
    V = np.array([(v.x, v.y) for v in out_v], dtype=np.float64)
    F = np.array(out_f, dtype=np.int64)
    return V, F


def ground_triangles(ctx):
    """Points, heights, triangles (all facing up) and each triangle's region label."""
    P, E, counts = assemble_points(ctx)
    V, F = triangulate(P, E)
    z = base_height(V[:, 0], V[:, 1], ctx)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    area2 = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    F = np.where((area2 < 0)[:, None], F[:, [0, 2, 1]], F)
    F = F[np.abs(area2) > 1e-10]
    centre = (V[F[:, 0]] + V[F[:, 1]] + V[F[:, 2]]) / 3.0
    labels = region_labels(centre, ctx)
    return V, z, F, labels, counts


# ------------------------------------------------------------------ colours
GROUND_OBJECTS = [
    # label, object name, role, plain colour of the stage's own material (the kit's surface pass replaces it)
    ('forest', 'Ground forest floor', 'ground.forest_floor', '#5B4A34'),
    ('clearing', 'Ground clearing', 'ground.grass', '#6F7A3E'),
    ('road_high', 'Ground road high_road', 'ground.dirt_road', '#8B7653'),
    ('road_lane', 'Ground road stable_lane', 'ground.dirt_road', '#8B7653'),
    ('yard', 'Ground yard', 'ground.mud', '#6E5638'),
    ('verge_high', 'Ground verge high_road', 'ground.grass', '#6A7A3A'),
    ('verge_lane', 'Ground verge stable_lane', 'ground.grass', '#6A7A3A'),
]


def make_mesh(name, V3, F, uv=True):
    import bpy
    used = np.unique(F)
    remap = np.full(len(V3), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    co = V3[used].astype(np.float32)
    tris = remap[F].astype(np.int32)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(co))
    mesh.vertices.foreach_set('co', co.ravel())
    mesh.loops.add(len(tris) * 3)
    mesh.loops.foreach_set('vertex_index', tris.ravel())
    mesh.polygons.add(len(tris))
    mesh.polygons.foreach_set('loop_start', (np.arange(len(tris)) * 3).astype(np.int32))
    mesh.polygons.foreach_set('use_smooth', np.ones(len(tris), dtype=bool))
    mesh.update(calc_edges=True)
    if uv:
        layer = mesh.uv_layers.new(name='UVMap')
        flat = co[tris.ravel()][:, :2].astype(np.float32)           # planar from above, in metres (one UV unit is one metre)
        layer.uv.foreach_set('vector', flat.ravel())
        mesh.uv_layers.active = layer
    return mesh


def plain_material(name, hex_colour, roughness=0.92):
    import bpy
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    shader = tree.nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = hex_to_linear(hex_colour)
    shader.inputs['Roughness'].default_value = roughness
    tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    return material


def build_ground_objects(pk, ctx, report):
    t = time.time()
    V, z, F, labels, counts = ground_triangles(ctx)
    report['points'] = counts
    report['seconds_mesh'] = round(time.time() - t, 1)
    V3 = np.column_stack([V, z])
    made = {}
    for label_index, (label, name, role, colour) in enumerate(GROUND_OBJECTS):
        sel = F[labels == LABELS.index(label)]
        if len(sel) == 0:
            continue
        mesh = make_mesh(name, V3, sel)
        mesh.materials.append(plain_material(f'PK {role} / stage colour', colour))
        obj = pk.new_part_object(OWNER, role, name, mesh)
        obj['pk_regraded'] = 1                      # the stage made this mesh fine itself; the kit's own regrading must leave it alone
        made[name] = len(sel)
    report['triangles_by_object'] = made
    return made


# ------------------------------------------------------------------ the world round the place: three rings of hills
RINGS = [
    # name, inner foot, outer foot (m from the middle), lowest crest, highest crest (m), colour, points round, seed, four tone steps, how jagged the tree-line is,
    # and the gain per colour channel that makes the ring AS LIT come out at its colour (measured with ring_calib: each ring drawn alone, the four views)
    ('Backdrop near ring', 370.0, 545.0, 25.0, 45.0, '#4F6A4A', 900, 101, (0.86, 0.96, 1.05, 1.15), 1.7, (1.12, 1.267, 1.50)),
    ('Backdrop middle ring', 505.0, 700.0, 45.0, 75.0, '#6C8776', 800, 202, (0.90, 0.97, 1.04, 1.12), 1.3, (1.405, 1.415, 1.60)),
    ('Backdrop far ring', 660.0, 820.0, 70.0, 110.0, '#8FA6B5', 700, 303, (0.95, 0.975, 1.0, 1.03), 1.0, (1.70, 1.675, 1.78)),
]
RING_ROWS = 17
FOOT_Z = -2.5                                    # the feet sit under the ground so there is never a gap


def ring_arrays(r_in, r_out, h_min, h_max, n_theta, seed, steps, jag=1.0):
    theta = np.linspace(0.0, 2.0 * math.pi, n_theta, endpoint=False)
    q = np.concatenate([np.linspace(0.0, 0.30, 5)[:-1], np.linspace(0.30, 0.62, 9)[:-1], np.linspace(0.62, 1.0, 6)])      # more rows round the crest
    q = np.unique(np.round(q, 5))
    mid = 0.5 * (r_in + r_out)
    cx, cy = mid * np.cos(theta), mid * np.sin(theta)
    crest = 0.5 + 0.5 * fbm(cx, cy, (260.0, 110.0, 47.0), (0.55, 0.30, 0.15), seed)             # 0..1 along the ring
    crest = smoothstep(0.08, 0.92, crest)
    top = h_min + (h_max - h_min) * crest
    skyline = 2.6 * vnoise(cx, cy, 21.0, seed + 5) + 1.3 * vnoise(cx, cy, 8.5, seed + 6) + 3.0 * np.maximum(vnoise(cx, cy, 33.0, seed + 7), 0.0)       # tree tops
    top = top + skyline * (h_max / 110.0 + 0.25) * jag
    R, T = np.meshgrid(q, theta)                       # (n_theta, rows)
    radius = r_in + R * (r_out - r_in)
    X, Y = radius * np.cos(T), radius * np.sin(T)
    shape = np.sin(np.pi * R ** 0.85) ** 1.4
    bump = 1.0 + 0.10 * vnoise(X, Y, 38.0, seed + 11) + 0.05 * vnoise(X, Y, 15.0, seed + 12)
    Z = FOOT_Z + (top[:, None] - FOOT_Z) * shape * bump
    Z = np.maximum(Z, FOOT_Z)
    # tone steps: bands of height, shifted by soft patches (tree-line bands, ridge shading); 4 steps from the ring's own multipliers
    fraction = np.clip((Z - FOOT_Z) / np.maximum(top[:, None] - FOOT_Z, 1.0), 0.0, 1.0)
    patch = 0.17 * vnoise(X, Y, 55.0, seed + 21) + 0.09 * vnoise(X, Y, 19.0, seed + 22)
    step_index = np.clip(np.floor((fraction + patch) * len(steps)), 0, len(steps) - 1).astype(np.int64)
    tone = np.array(steps)[step_index] * (1.0 + 0.035 * vnoise(X, Y, 11.0, seed + 23))
    return X, Y, Z, tone


def ring_object(pk, name, r_in, r_out, h_min, h_max, colour, n_theta, seed, steps, jag, gains, extra_gain=1.0, skirt=None):
    import bpy
    X, Y, Z, tone = ring_arrays(r_in, r_out, h_min, h_max, n_theta, seed, steps, jag)
    rows = X.shape[1]
    co = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    index = np.arange(n_theta * rows).reshape(n_theta, rows)
    nxt = np.roll(index, -1, axis=0)
    quads = np.stack([index[:, :-1], nxt[:, :-1], nxt[:, 1:], index[:, 1:]], axis=-1).reshape(-1, 4)
    tris = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], axis=0)
    # face the +z side
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    normal_z = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    if np.mean(normal_z) < 0:
        tris = tris[:, [0, 2, 1]]
    base = np.array(hex_to_linear(colour))[:3] * np.array(gains) * extra_gain
    colours = np.clip(base[None, :] * tone.reshape(-1, 1), 0.0, 1.0)
    ring_triangles = len(tris)
    if skirt is not None:                          # the plain to the horizon rides in the same mesh (a second material), so the backdrop stays three meshes
        s_co, s_tris, s_col = skirt
        tris = np.concatenate([tris, s_tris + len(co)], axis=0)
        co = np.concatenate([co, s_co], axis=0)
        colours = np.concatenate([colours, s_col * extra_gain], axis=0)
    mesh = make_mesh(name, co, tris, uv=False)
    rgba = np.concatenate([colours, np.ones((len(co), 1))], axis=1).astype(np.float32)
    attribute = mesh.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attribute.data.foreach_set('color', rgba.ravel())
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')                 # takes light like paint on a hill; no emission anywhere
    diffuse.inputs['Roughness'].default_value = 1.0
    vertex = tree.nodes.new('ShaderNodeVertexColor')
    vertex.layer_name = 'Color'
    tree.links.new(vertex.outputs['Color'], diffuse.inputs['Color'])
    tree.links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    mesh.materials.append(material)
    if skirt is not None:
        mesh.materials.append(plain_ground_material())
        index = np.zeros(len(tris), dtype=np.int32)
        index[ring_triangles:] = 1
        mesh.polygons.foreach_set('material_index', index)
        mesh.update()
    obj = pk.new_part_object(OWNER, 'backdrop', name, mesh)
    obj.visible_shadow = False
    return obj, len(tris)


def plain_ground_material():
    """The plain ground to the horizon: paint that takes the light, no emission; colour from the vertices and a soft world-space noise at two sizes so no window of it is flat."""
    import bpy
    material = bpy.data.materials.get('Backdrop plain ground') or bpy.data.materials.new('Backdrop plain ground')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    diffuse = tree.nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Roughness'].default_value = 1.0
    vertex = tree.nodes.new('ShaderNodeVertexColor')
    vertex.layer_name = 'Color'
    coord = tree.nodes.new('ShaderNodeTexCoord')
    tints = []
    for scale, weight in ((0.16, 0.16), (0.035, 0.18)):
        noise = tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = scale
        noise.inputs['Detail'].default_value = 2.0
        tree.links.new(coord.outputs['Object'], noise.inputs['Vector'])
        grow = tree.nodes.new('ShaderNodeMath')
        grow.operation = 'MULTIPLY'
        grow.inputs[1].default_value = weight
        tree.links.new(noise.outputs['Fac'], grow.inputs[0])
        tints.append(grow)
    total = tree.nodes.new('ShaderNodeMath')
    total.operation = 'ADD'
    tree.links.new(tints[0].outputs['Value'], total.inputs[0])
    tree.links.new(tints[1].outputs['Value'], total.inputs[1])
    shift = tree.nodes.new('ShaderNodeMath')
    shift.operation = 'ADD'
    shift.inputs[1].default_value = 0.75
    tree.links.new(total.outputs['Value'], shift.inputs[0])
    mix = tree.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    tree.links.new(vertex.outputs['Color'], mix.inputs[6])               # A (colour)
    tree.links.new(shift.outputs['Value'], mix.inputs[7])                # B (colour): the grey tint
    tree.links.new(mix.outputs[2], diffuse.inputs['Color'])              # Result (colour)
    tree.links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    return material


# ------------------------------------------------------------------ cameras, sun, sky, render
SUN_BEARING = 135.0              # compass bearing the sun shines FROM, clockwise from north: south-east
SUN_ELEVATION = 50.0
SUN_STRENGTH = 4.5
SKY_STRENGTH = 0.5
# name, x, y, z (z is a height ABOVE THE GROUND for eye-height views, absolute for the high wide view), looks at (x, y, z), lens mm, ground-relative
CAMERAS = [
    ('View wide', (-50.145, -27.903, 14.0), (-5.0, 14.0, 2.0), 28.0, False),                  # the plan's spot moved 3 m to its left so the lean-to of cottage A and the west end of the road are in the frame
    ('View road_eye', (-62.0, -3.7, 1.7), (-20.0, 0.5, 1.5), 35.0, True),
    ('View stable_close', (28.5, 25.5, 1.7), (24.0, 36.0, 1.4), 28.0, True),
    ('View cottage_close', (-12.764, 3.033, 1.7), (-31.0, 8.0, 1.6), 35.0, True),             # the plan's spot moved 3 m to its right so the well (-17.5, 6) is in the frame with cottage A's front
]
CLIP_END = 3000.0


def make_cameras(pk):
    import bpy
    from mathutils import Vector
    scene = bpy.context.scene
    out = {}
    for name, loc, target, lens, relative in CAMERAS:
        ground_here = pk.ground_height_at(loc[0], loc[1])
        ground_there = pk.ground_height_at(target[0], target[1])
        position = Vector((loc[0], loc[1], loc[2] + (ground_here if relative else 0.0)))
        aim = Vector((target[0], target[1], target[2] + (ground_there if relative else 0.0)))
        data = bpy.data.cameras.new(name)
        data.lens = lens
        data.sensor_width = 36.0
        data.sensor_fit = 'AUTO'
        data.clip_start = 0.1
        data.clip_end = CLIP_END
        obj = bpy.data.objects.new(name, data)
        obj.location = position
        obj.rotation_euler = (aim - position).to_track_quat('-Z', 'Y').to_euler()
        pk.new_part_object(OWNER, 'never.helper', name, obj)
        obj['view_size'] = [1200, 800]
        out[name] = (tuple(round(v, 3) for v in position), tuple(round(v, 3) for v in aim), lens)
    scene.camera = bpy.data.objects['View wide']
    return out


def make_sun(pk):
    import bpy
    from mathutils import Vector
    data = bpy.data.lights.new('Sun', 'SUN')
    data.energy = SUN_STRENGTH
    data.color = hex_to_linear('#FFF1D6')[:3]
    data.angle = math.radians(1.5)
    az, el = math.radians(SUN_BEARING), math.radians(SUN_ELEVATION)
    toward = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))     # x east, y north: bearing 135 is south-east
    obj = bpy.data.objects.new('Sun', data)
    obj.location = (0.0, 0.0, 100.0)
    obj.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    pk.new_part_object(OWNER, 'never.light', 'Sun', obj)
    return obj


def make_world():
    """A gradient sky (zenith #9DB7CC to horizon #D9E2E6) for the camera, a softer light from it for the scene (a camera ray sees the full colour, every other ray a little over half),
    a dark warm ground below the horizon for bounce light, and no volume (no haze, no fog)."""
    import bpy
    scene = bpy.context.scene
    world = bpy.data.worlds.get('Sky') or bpy.data.worlds.new('Sky')
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    coord = tree.nodes.new('ShaderNodeTexCoord')
    separate = tree.nodes.new('ShaderNodeSeparateXYZ')
    mapper = tree.nodes.new('ShaderNodeMapRange')
    ramp = tree.nodes.new('ShaderNodeValToRGB')
    path = tree.nodes.new('ShaderNodeLightPath')
    strength = tree.nodes.new('ShaderNodeMath')
    background = tree.nodes.new('ShaderNodeBackground')
    output = tree.nodes.new('ShaderNodeOutputWorld')
    tree.links.new(coord.outputs['Generated'], separate.inputs['Vector'])
    mapper.inputs['From Min'].default_value, mapper.inputs['From Max'].default_value = -1.0, 1.0          # z of the direction runs -1..1; the ramp wants 0..1
    mapper.inputs['To Min'].default_value, mapper.inputs['To Max'].default_value = 0.0, 1.0
    tree.links.new(separate.outputs['Z'], mapper.inputs['Value'])
    tree.links.new(mapper.outputs['Result'], ramp.inputs['Fac'])
    ground_tone = hex_to_linear('#4A4636')
    stops = [(0.0, ground_tone), (0.485, ground_tone), (0.5, hex_to_linear('#D9E2E6')), (0.72, hex_to_linear('#BCCFDB')), (1.0, hex_to_linear('#9DB7CC'))]
    elements = ramp.color_ramp.elements
    while len(elements) > 1:
        elements.remove(elements[-1])
    elements[0].position, elements[0].color = stops[0]
    for position, colour in stops[1:]:
        e = elements.new(position)
        e.color = colour
    ramp.color_ramp.interpolation = 'LINEAR'
    strength.operation = 'MULTIPLY_ADD'
    tree.links.new(path.outputs['Is Camera Ray'], strength.inputs[0])
    strength.inputs[1].default_value = 1.0 - SKY_STRENGTH
    strength.inputs[2].default_value = SKY_STRENGTH
    tree.links.new(strength.outputs['Value'], background.inputs['Strength'])
    tree.links.new(ramp.outputs['Color'], background.inputs['Color'])
    tree.links.new(background.outputs['Background'], output.inputs['Surface'])
    scene.world = world
    return world


def set_render():
    import bpy
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 800, 100
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.film_transparent = False
    for transform in ('Standard',):            # colours stay as painted: hex in, hex out (the Khronos neutral curve darkens and saturates dark greens)
        try:
            scene.view_settings.view_transform = transform
            break
        except TypeError:
            continue
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0


def drop_orphans():
    import bpy
    for collection in (bpy.data.cameras, bpy.data.lights):
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)


def apply(options=None):
    options = options or {}
    import bpy
    try:
        import place_kit as pk
    except ImportError:
        _kit_roads_module()                          # puts the kit's folder on the path
        import place_kit as pk
    started = time.time()
    report = {}
    pk.forget_part(OWNER)
    drop_orphans()
    settings_path = options.get('settings') or os.path.join(PLAN, 'place-settings.json')
    settings = pk.read_settings(settings_path)
    ctx = make_context_full(settings.roads)
    pk.begin_part(OWNER)
    build_ground_objects(pk, ctx, report)
    road_report = pk.shape_roads(settings)                       # the kit's roads step: ruts, banks, hoof prints, crown, puddle hollows, on the roads of place-settings.json
    report['roads'] = road_report.get('summary')
    ring_report = {}
    gain = float(options.get('backdrop_gain', BACKDROP_GAIN))
    for name, r_in, r_out, h_min, h_max, colour, n_theta, seed, steps, jag, gains in RINGS:
        obj, count = ring_object(pk, name, r_in, r_out, h_min, h_max, colour, n_theta, seed, steps, jag, gains, gain, skirt=(skirt_arrays() if name == 'Backdrop near ring' else None))
        ring_report[name] = count
    report['backdrop_triangles'] = ring_report
    make_world()
    set_render()
    make_sun(pk)
    report['cameras'] = make_cameras(pk)
    bpy.context.view_layer.update()
    if options.get('plan_masks', True):
        report['plan_masks'] = write_plan_masks(settings)
    report['seconds'] = round(time.time() - started, 1)
    print('GROUND STAGE:', json.dumps(report, default=str))
    return report


def write_plan_masks(settings):
    """The kit's plan pictures (where the wheel tracks, the crown, the worn paths and the keep-clear shapes of place-settings.json are) made from the ground alone and stored in the scene, so a builder that is
    seated on this ground can ask pk.is_keep_clear(x, y) at once, before it has run its own pass (without them every answer would be 'anywhere'). The integrator's full pass writes them again from the whole place."""
    try:
        from place_kit.wear import masks
        plan, record = masks.build_plan_masks(settings, quick=False)
        images = masks.write_plan_images(plan)
        for image in images:
            image.use_fake_user = True              # nothing uses them until a material does; without this the save would drop them
        masks.forget_loaded()
        return {'cell_metres': round(record['cell_metres'], 3), 'cells': record['cells'], 'seconds': record['seconds']}
    except Exception as problem:                    # noqa: BLE001 - the masks are a service to the other parts, never a reason to lose the ground
        return {'not_made': f'{type(problem).__name__}: {problem}'}


BACKDROP_GAIN = 1.0
