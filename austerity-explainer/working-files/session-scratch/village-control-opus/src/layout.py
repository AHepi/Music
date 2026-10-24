"""Village layout: height field, roads, clearing, building footprints."""
import numpy as np
import math
from common import fbm, perlin, noise1, smoothstep

# ----------------------------------------------------------------------------
# Terrain height
# ----------------------------------------------------------------------------
VILLAGE_C = np.array([0.0, 6.0])


def height(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = np.sqrt((x - VILLAGE_C[0]) ** 2 + (y - VILLAGE_C[1]) ** 2)
    flat = smoothstep(35.0, 85.0, r)
    base = 2.4 * fbm(x / 110.0, y / 110.0, 3, seed=11)
    mid = 0.75 * fbm(x / 28.0, y / 28.0, 3, seed=12)
    small = 0.10 * fbm(x / 5.0, y / 5.0, 2, seed=13)
    tilt = 0.010 * y - 0.004 * x
    return base + mid * (0.30 + 0.70 * flat) + small * (0.55 + 0.45 * flat) + tilt + 1.2 * flat * fbm(x / 45.0, y / 45.0, 2, seed=14)


def clearing_radius(theta):
    c = np.cos(theta)
    s = np.sin(theta)
    return 50.0 + 9.0 * perlin(c * 1.2 + 3.1, s * 1.2 - 1.7, 21) + 4.0 * perlin(c * 2.7, s * 2.7, 22) + 2.0 * perlin(c * 6.0, s * 6.0, 23)


def forest_mask(x, y):
    """0 inside the clearing, 1 in the forest (soft edge)."""
    dx = np.asarray(x) - VILLAGE_C[0]
    dy = np.asarray(y) - VILLAGE_C[1]
    r = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dy, dx)
    rc = clearing_radius(th)
    return smoothstep(rc - 4.0, rc + 6.0, r)


# ----------------------------------------------------------------------------
# Roads
# ----------------------------------------------------------------------------
ROADS = {
    # main carriage road, west -> east
    "main": dict(
        pts=[(-178, -52), (-135, -38), (-95, -27), (-60, -17), (-34, -10), (-12, -5.5), (10, -2.0),
             (31, 4.5), (52, 13.0), (80, 22.0), (118, 29.0), (178, 34.0)],
        edge=2.45, edge_var=0.38, gauge=0.74, rut_depth=0.085, ruts=True, hooves=1.0,
        width_total=3.7, seed=101, fine=(-75, 75), grass_center=0.6, wear=1.0),
    # lane to the stable yard, leaves the main road heading north
    "lane_n": dict(
        pts=[(4.5, -1.3), (4.2, 4.0), (5.0, 11.0), (7.5, 17.5), (9.5, 22.0)],
        edge=1.85, edge_var=0.30, gauge=0.72, rut_depth=0.055, ruts=True, hooves=1.0,
        width_total=3.0, seed=202, fine=(-100, 100), grass_center=0.95, wear=0.75, start_sink=1.3, end_sink=6.0),
    # old forest road heading south
    "lane_s": dict(
        pts=[(-14.5, -7.6), (-15.5, -14.0), (-13.5, -24.0), (-8.0, -36.0), (-2.0, -50.0), (5.0, -68.0),
             (9.0, -95.0), (6.0, -125.0), (10.0, -175.0)],
        edge=2.0, edge_var=0.34, gauge=0.73, rut_depth=0.065, ruts=True, hooves=0.6,
        width_total=3.2, seed=303, fine=(-60, 60), grass_center=1.0, wear=0.7, start_sink=1.3),
    # footpaths (no ruts)
    "path_a": dict(
        pts=[(-27.0, -7.0), (-26.4, -4.5), (-25.2, -1.8), (-24.4, 0.6)],
        edge=0.55, edge_var=0.16, gauge=0.0, rut_depth=0.0, ruts=False, hooves=0.0,
        width_total=1.2, seed=404, fine=(-100, 100), grass_center=0.0, wear=0.4, start_sink=1.4, path=True),
    "path_c": dict(
        pts=[(24.0, 0.8), (23.6, -2.0), (23.0, -5.0), (22.6, -8.0)],
        edge=0.55, edge_var=0.16, gauge=0.0, rut_depth=0.0, ruts=False, hooves=0.0,
        width_total=1.2, seed=505, fine=(-100, 100), grass_center=0.0, wear=0.4, start_sink=1.4, path=True),
    "path_well": dict(
        pts=[(-11.0, -3.8), (-10.0, -0.6), (-8.5, 3.0), (-7.4, 6.2)],
        edge=0.5, edge_var=0.15, gauge=0.0, rut_depth=0.0, ruts=False, hooves=0.0,
        width_total=1.1, seed=606, fine=(-100, 100), grass_center=0.0, wear=0.35, start_sink=1.4, path=True),
    "path_b": dict(
        pts=[(-34.0, -11.6), (-34.3, -13.6), (-34.7, -15.6), (-35.0, -17.6)],
        edge=0.55, edge_var=0.16, gauge=0.0, rut_depth=0.0, ruts=False, hooves=0.0,
        width_total=1.2, seed=707, fine=(-100, 100), grass_center=0.0, wear=0.4, start_sink=1.4, path=True),
    "path_d": dict(
        pts=[(6.6, 19.2), (2.0, 21.5), (-3.5, 24.2), (-8.8, 26.0)],
        edge=0.5, edge_var=0.15, gauge=0.0, rut_depth=0.0, ruts=False, hooves=0.0,
        width_total=1.1, seed=808, fine=(-100, 100), grass_center=0.0, wear=0.35, start_sink=1.4, path=True),
}


def catmull_rom(P, samples_per_seg=60, alpha=0.5):
    P = np.asarray(P, dtype=np.float64)
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** alpha
        t2 = t1 + np.linalg.norm(p2 - p1) ** alpha
        t3 = t2 + np.linalg.norm(p3 - p2) ** alpha
        ts = np.linspace(t1, t2, samples_per_seg, endpoint=(i == len(ext) - 4))
        for t in ts:
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            c = (t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2
            out.append(c)
    return np.array(out)


class RoadCurve:
    def __init__(self, name):
        self.name = name
        self.p = ROADS[name]
        dense = catmull_rom(self.p["pts"], 80)
        seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
        self.s_dense = np.concatenate([[0], np.cumsum(seg)])
        self.dense = dense
        self.length = self.s_dense[-1]

    def at(self, s):
        s = np.asarray(s, dtype=np.float64)
        x = np.interp(s, self.s_dense, self.dense[:, 0])
        y = np.interp(s, self.s_dense, self.dense[:, 1])
        eps = 0.05
        x2 = np.interp(s + eps, self.s_dense, self.dense[:, 0])
        y2 = np.interp(s + eps, self.s_dense, self.dense[:, 1])
        x1 = np.interp(s - eps, self.s_dense, self.dense[:, 0])
        y1 = np.interp(s - eps, self.s_dense, self.dense[:, 1])
        tx = x2 - x1
        ty = y2 - y1
        L = np.sqrt(tx * tx + ty * ty) + 1e-12
        return x, y, tx / L, ty / L

    def edges(self, s):
        """Left / right visual edge distance from the centre line."""
        p = self.p
        sd = p["seed"]
        e0 = p["edge"]
        v = p["edge_var"]
        el = e0 + v * noise1(s / 7.0, sd + 1) + 0.4 * v * noise1(s / 1.9, sd + 2) + 0.12 * v * noise1(s / 0.45, sd + 3)
        er = e0 + v * noise1(s / 7.0, sd + 4) + 0.4 * v * noise1(s / 1.9, sd + 5) + 0.12 * v * noise1(s / 0.45, sd + 6)
        # slightly narrower near the start/end of footpaths
        if p.get("path"):
            taper = 0.75 + 0.25 * smoothstep(0.0, 1.2, s)
            el = el * taper
            er = er * taper
        return el, er

    def wander(self, s):
        sd = self.p["seed"]
        if self.p.get("path"):
            return 0.0 * s
        return 0.26 * noise1(s / 26.0, sd + 11) + 0.10 * noise1(s / 7.0, sd + 13) + 0.03 * noise1(s / 2.2, sd + 12)


def road_curves():
    return {k: RoadCurve(k) for k in ROADS}


# ----------------------------------------------------------------------------
# Buildings and features (centre x, y, rotation degrees, footprint w x d)
# ----------------------------------------------------------------------------
BUILDINGS = {
    "stable":    dict(x=8.0, y=31.5, rot=-4.0, w=11.0, d=6.6),
    "cottage_a": dict(x=-24.5, y=4.8, rot=-7.0, w=8.6, d=5.4),
    "cottage_b": dict(x=-36.0, y=-21.0, rot=156.0, w=7.2, d=5.0),
    "cottage_c": dict(x=23.0, y=-11.8, rot=184.0, w=7.8, d=5.2),
    "cottage_d": dict(x=-10.0, y=29.0, rot=12.0, w=5.6, d=4.4),
}

YARDS = [
    # trampled dirt in front of the stable
    dict(x=8.5, y=24.0, rx=8.5, ry=5.0, rot=-4.0, seed=901, hooves=1.0),
    # small trodden patch at the well
    dict(x=-6.8, y=7.8, rx=2.6, ry=2.4, rot=0.0, seed=902, hooves=0.0),
    # trodden ground in front of each cottage door
    dict(x=-24.3, y=1.0, rx=1.6, ry=1.1, rot=-7.0, seed=903, hooves=0.0),
    dict(x=-34.8, y=-18.1, rx=1.4, ry=1.0, rot=156.0, seed=904, hooves=0.0),
    dict(x=22.6, y=-8.4, rx=1.5, ry=1.0, rot=184.0, seed=905, hooves=0.0),
    dict(x=-8.4, y=26.4, rx=1.3, ry=0.9, rot=12.0, seed=906, hooves=0.0),
]

# vegetable gardens (centre x, y, size w x d, rotation)
GARDENS = [
    dict(x=-24.33, y=11.08, w=6.0, d=4.0, rot=-7.0, seed=951),
    dict(x=-4.76, y=29.6, w=3.2, d=3.6, rot=12.0, seed=952),
]


# (parent road, child road, carts turn here)
JUNCTIONS = [
    ("main", "lane_n", True),
    ("main", "lane_s", True),
    ("main", "path_a", False),
    ("main", "path_c", False),
    ("main", "path_well", False),
    ("main", "path_b", False),
    ("lane_n", "path_d", False),
]

# areas kept free of trees (x0, x1, y0, y1)
OPEN_AREAS = [
    (14.0, 34.0, 21.0, 45.0),     # paddock east of the stable
    (-36.0, -16.0, 7.0, 20.0),    # cottage A's garden plot
]
