"""Small plants: grass clumps, weeds, flowers, ferns, rocks. Each generator returns (verts, faces, colors)."""
import numpy as np
import math
from mathutils import Vector, Matrix, Quaternion
import common as C


def lin(c):
    def f(x):
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return np.array([f(c[0]), f(c[1]), f(c[2])])


class Geo:
    """Accumulates verts/faces/colours (per vertex) and a per-face material slot."""

    def __init__(self):
        self.v = []
        self.f = []
        self.c = []
        self.m = []

    def add(self, verts, faces, cols, mat=0):
        base = len(self.v)
        self.v.extend([tuple(p) for p in verts])
        for f in faces:
            self.f.append([base + i for i in f])
            self.m.append(mat)
        if isinstance(cols, np.ndarray) and cols.ndim == 1:
            cols = [cols] * len(verts)
        self.c.extend([tuple(c) + (1.0,) if len(c) == 3 else tuple(c) for c in cols])

    def arrays(self):
        return np.array(self.v), self.f, np.array(self.c), np.array(self.m)


def blade(geo, rng, base, h, w, lean, lean_dir, droop, twist, col_base, col_tip, nseg=5, mat=0, tip_round=False):
    """A grass blade as a tapered strip."""
    pos = np.array(base, dtype=float)
    dirH = np.array([math.cos(lean_dir), math.sin(lean_dir), 0.0])
    side0 = np.array([-math.sin(lean_dir), math.cos(lean_dir), 0.0])
    seg = h / nseg
    verts = []
    cols = []
    theta = lean
    for i in range(nseg + 1):
        t = i / nseg
        width = w * (1 - t ** 1.6) if not tip_round else w * math.sqrt(max(1 - t ** 2, 0.0))
        tw = twist * t
        side = side0 * math.cos(tw) + np.array([0, 0, 1.0]) * math.sin(tw) * 0.3
        side = side / np.linalg.norm(side)
        verts.append(pos + side * width * 0.5)
        verts.append(pos - side * width * 0.5)
        col = col_base + (col_tip - col_base) * (t ** 1.2)
        cols.append(col)
        cols.append(col)
        theta = lean + droop * t
        step = dirH * math.sin(theta) + np.array([0, 0, 1.0]) * math.cos(theta)
        pos = pos + step * seg
    faces = []
    for i in range(nseg):
        a, b = 2 * i, 2 * i + 1
        c, d = 2 * i + 3, 2 * i + 2
        faces.append([a, b, c, d])
    geo.add(verts, faces, cols, mat)


def grass_clump(rng, n, h_range, radius, w_range=(0.005, 0.009), dry=0.15, green=None, seedheads=0, lean_max=0.7):
    geo = Geo()
    g0 = lin((0.10, 0.16, 0.04)) if green is None else green[0]
    g1 = lin((0.30, 0.42, 0.11)) if green is None else green[1]
    d1 = lin((0.62, 0.55, 0.30))
    for b in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        r = radius * math.sqrt(rng.uniform())
        base = (r * math.cos(ang), r * math.sin(ang), -0.01)
        h = rng.uniform(*h_range)
        lean = rng.uniform(0.05, lean_max) * (0.4 + 0.6 * r / max(radius, 1e-6))
        ld = ang + rng.normal(0, 0.6)
        droop = rng.uniform(0.2, 1.0) * (h / max(h_range[1], 1e-6))
        w = rng.uniform(*w_range)
        isdry = rng.uniform() < dry
        tip = d1 * rng.uniform(0.85, 1.1) if isdry else g1 * rng.uniform(0.75, 1.25)
        basec = g0 * rng.uniform(0.7, 1.2)
        if isdry:
            basec = basec * 0.6 + d1 * 0.4 * 0.6
        blade(geo, rng, base, h, w, lean, ld, droop, rng.uniform(-1.2, 1.2), basec, tip)
    for s in range(seedheads):
        ang = rng.uniform(0, 2 * math.pi)
        r = radius * 0.5 * math.sqrt(rng.uniform())
        base = np.array([r * math.cos(ang), r * math.sin(ang), -0.01])
        h = rng.uniform(h_range[1] * 1.1, h_range[1] * 1.7)
        ld = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.0, 0.35)
        stalk_c = lin((0.45, 0.45, 0.22))
        blade(geo, rng, base, h, 0.0022, lean, ld, rng.uniform(0.1, 0.4), 0.0, stalk_c * 0.7, stalk_c, nseg=6)
        # seed head: a spike of little scales near the top
        dirH = np.array([math.cos(ld), math.sin(ld), 0.0])
        top = base + dirH * math.sin(lean) * h + np.array([0, 0, math.cos(lean) * h])
        axis = (dirH * math.sin(lean + 0.2) + np.array([0, 0, math.cos(lean + 0.2)]))
        hc = lin((0.55, 0.47, 0.30)) * rng.uniform(0.7, 1.1)
        L = rng.uniform(0.04, 0.09)
        for k in range(8):
            t = k / 8.0
            p = top - axis * L * (1 - t)
            a2 = rng.uniform(0, 2 * math.pi)
            sd = np.array([math.cos(a2), math.sin(a2), 0.0])
            q0 = p + sd * 0.004
            q1 = p - sd * 0.004
            q2 = p + axis * 0.014 - sd * 0.002
            q3 = p + axis * 0.014 + sd * 0.002
            geo.add([q0, q1, q2, q3], [[0, 1, 2, 3]], [hc] * 4)
    return geo


def leaf_outline(length, width, n=6, serr=0.0, rng=None, shape='oval'):
    """Leaf polygon outline in local XY: base at origin, tip along +Y. Returns list of 2D points (closed)."""
    pts_r = []
    pts_l = []
    for i in range(1, n):
        t = i / n
        if shape == 'oval':
            wv = math.sin(math.pi * t) ** 0.8 * width * 0.5
        elif shape == 'heart':
            wv = (math.sin(math.pi * (t ** 0.75)) ** 0.9) * width * 0.5
        elif shape == 'lance':
            wv = math.sin(math.pi * t ** 1.3) * width * 0.5
        else:
            wv = math.sin(math.pi * t) * width * 0.5
        if serr > 0 and rng is not None:
            wv *= (1.0 + serr * (1 if i % 2 else -1))
        pts_r.append((wv, t * length))
        pts_l.append((-wv, t * length))
    return [(0.0, 0.0)] + pts_r + [(0.0, length)] + pts_l[::-1]


def add_leaf(geo, origin, direction, normal, length, width, col, n=6, serr=0.0, rng=None, shape='oval', fold=0.15, curl=0.0, mat=0, colvar=None):
    """Place a leaf (fan triangulated polygon with a slight central fold)."""
    d = Vector(direction).normalized()
    nn = Vector(normal)
    nn = (nn - d * nn.dot(d))
    if nn.length < 1e-6:
        nn = d.orthogonal()
    nn.normalize()
    s = d.cross(nn).normalized()
    outline = leaf_outline(length, width, n, serr, rng, shape)
    verts = []
    o = Vector(origin)
    for (x, y) in outline:
        t = y / length
        # fold along the midrib and curl along the length
        z = abs(x) * fold + curl * (t ** 2) * length
        p = o + s * x + d * y + nn * z
        verts.append(tuple(p))
    # midrib centre point for a nicer fan
    mid = o + d * (length * 0.5) + nn * (curl * 0.25 * length)
    verts.append(tuple(mid))
    ci = len(verts) - 1
    faces = []
    m = len(outline)
    for i in range(m):
        faces.append([ci, i, (i + 1) % m])
    cols = [col] * len(verts) if colvar is None else [col * colvar] * len(verts)
    geo.add(verts, faces, cols, mat)


def plantain(rng):
    geo = Geo()
    n = rng.randint(5, 10)
    col = lin((0.20, 0.32, 0.10))
    for i in range(n):
        a = i / n * 2 * math.pi + rng.normal(0, 0.2)
        dirH = Vector((math.cos(a), math.sin(a), 0))
        d = (dirH + Vector((0, 0, rng.uniform(0.15, 0.6)))).normalized()
        L = rng.uniform(0.08, 0.17)
        add_leaf(geo, (0, 0, 0.0), d, (0, 0, 1), L, L * rng.uniform(0.45, 0.6), col * rng.uniform(0.8, 1.2), n=8, shape='oval', fold=0.12, curl=0.15)
    # a couple of seed spikes
    for k in range(rng.randint(0, 3)):
        a = rng.uniform(0, 2 * math.pi)
        h = rng.uniform(0.12, 0.25)
        blade(geo, rng, (0.0, 0.0, 0.0), h, 0.003, rng.uniform(0.0, 0.4), a, 0.1, 0.0, lin((0.3, 0.38, 0.14)), lin((0.35, 0.33, 0.2)), nseg=5)
    return geo


def dandelion(rng, flowers=True):
    geo = Geo()
    n = rng.randint(6, 11)
    col = lin((0.18, 0.30, 0.08))
    for i in range(n):
        a = i / n * 2 * math.pi + rng.normal(0, 0.25)
        d = (Vector((math.cos(a), math.sin(a), 0)) + Vector((0, 0, rng.uniform(0.1, 0.5)))).normalized()
        L = rng.uniform(0.1, 0.2)
        add_leaf(geo, (0, 0, 0), d, (0, 0, 1), L, L * 0.28, col * rng.uniform(0.8, 1.2), n=12, serr=0.6, rng=rng, shape='lance', fold=0.1, curl=0.1)
    if flowers:
        for k in range(rng.randint(1, 3)):
            a = rng.uniform(0, 2 * math.pi)
            h = rng.uniform(0.12, 0.28)
            lean = rng.uniform(0.0, 0.35)
            blade(geo, rng, (0.0, 0.0, 0.0), h, 0.004, lean, a, 0.15, 0.0, lin((0.3, 0.38, 0.16)), lin((0.36, 0.42, 0.18)), nseg=5)
            dirH = np.array([math.cos(a), math.sin(a), 0])
            top = dirH * math.sin(lean) * h + np.array([0, 0, math.cos(lean) * h])
            if rng.uniform() < 0.7:
                flower_head(geo, rng, top, 0.018, lin((0.95, 0.72, 0.05)), petals=22, cup=0.25)
            else:
                puff(geo, rng, top, 0.022)
    return geo


def flower_head(geo, rng, center, radius, col, petals=8, cup=0.3, centre_col=None):
    c = np.array(center)
    for k in range(petals):
        a = k / petals * 2 * math.pi + rng.normal(0, 0.1)
        d = np.array([math.cos(a), math.sin(a), cup])
        d /= np.linalg.norm(d)
        s = np.array([-math.sin(a), math.cos(a), 0.0])
        w = radius * (2 * math.pi / petals) * 0.65
        p0 = c + s * w * 0.15
        p1 = c - s * w * 0.15
        p2 = c + d * radius - s * w * 0.4
        p3 = c + d * radius + s * w * 0.4
        geo.add([p0, p1, p2, p3], [[0, 1, 2, 3]], [col * rng.uniform(0.85, 1.1)] * 4)
    cc = centre_col if centre_col is not None else col * 0.8
    r = radius * 0.3
    pts = [c + np.array([math.cos(a) * r, math.sin(a) * r, 0.004]) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
    pts.append(c + np.array([0, 0, 0.008]))
    faces = [[6, i, (i + 1) % 6] for i in range(6)]
    geo.add(pts, faces, [cc] * 7)


def puff(geo, rng, center, radius):
    c = np.array(center)
    col = lin((0.85, 0.85, 0.82))
    for k in range(26):
        d = rng.normal(0, 1, 3)
        d /= np.linalg.norm(d)
        s = np.cross(d, [0, 0, 1.0])
        if np.linalg.norm(s) < 1e-3:
            s = np.array([1.0, 0, 0])
        s /= np.linalg.norm(s)
        geo.add([c, c + d * radius + s * 0.003, c + d * radius - s * 0.003], [[0, 1, 2]], [col] * 3)


def clover_patch(rng, n=14, radius=0.12, flowers=2):
    geo = Geo()
    col = lin((0.14, 0.27, 0.07))
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = radius * math.sqrt(rng.uniform())
        base = np.array([r * math.cos(a), r * math.sin(a), 0.0])
        h = rng.uniform(0.03, 0.08)
        top = base + np.array([rng.normal(0, 0.01), rng.normal(0, 0.01), h])
        blade(geo, rng, base, h, 0.0015, 0.1, a, 0.0, 0.0, col, col, nseg=2)
        rot = rng.uniform(0, 2 * math.pi)
        for k in range(3):
            aa = rot + k * 2 * math.pi / 3
            d = Vector((math.cos(aa), math.sin(aa), rng.uniform(-0.1, 0.25))).normalized()
            add_leaf(geo, top, d, (0, 0, 1), 0.016, 0.016, col * rng.uniform(0.85, 1.2), n=6, shape='heart', fold=0.05)
    for k in range(flowers):
        a = rng.uniform(0, 2 * math.pi)
        r = radius * 0.6 * math.sqrt(rng.uniform())
        base = np.array([r * math.cos(a), r * math.sin(a), 0.0])
        h = rng.uniform(0.07, 0.13)
        blade(geo, rng, base, h, 0.002, 0.1, a, 0.1, 0.0, col, col, nseg=3)
        top = base + np.array([0, 0, h])
        fc = lin((0.92, 0.90, 0.85)) if rng.uniform() < 0.7 else lin((0.75, 0.45, 0.6))
        for kk in range(16):
            d = rng.normal(0, 1, 3)
            d[2] = abs(d[2]) * 0.6
            d /= np.linalg.norm(d)
            s = np.cross(d, [0, 0, 1.0])
            s = s / (np.linalg.norm(s) + 1e-9)
            geo.add([top, top + d * 0.011 + s * 0.002, top + d * 0.011 - s * 0.002], [[0, 1, 2]], [fc] * 3)
    return geo


def wildflower(rng, kind):
    """kind: 'yarrow' (white umbel), 'buttercup' (yellow), 'knapweed' (purple), 'campion' (pink)."""
    geo = Geo()
    stem_c = lin((0.22, 0.32, 0.12))
    nst = rng.randint(1, 4)
    for s in range(nst):
        a = rng.uniform(0, 2 * math.pi)
        base = np.array([rng.normal(0, 0.02), rng.normal(0, 0.02), -0.01])
        h = rng.uniform(0.25, 0.6) if kind != 'buttercup' else rng.uniform(0.2, 0.45)
        lean = rng.uniform(0.0, 0.3)
        blade(geo, rng, base, h, 0.003, lean, a, 0.12, 0.0, stem_c, stem_c * 1.1, nseg=6)
        dirH = np.array([math.cos(a), math.sin(a), 0.0])
        # approximate top position (blade() bends slightly)
        top = base + dirH * math.sin(lean + 0.06) * h + np.array([0, 0, math.cos(lean + 0.06) * h])
        # a few stem leaves
        for k in range(rng.randint(2, 5)):
            t = rng.uniform(0.1, 0.6)
            p = base + (top - base) * t
            aa = rng.uniform(0, 2 * math.pi)
            d = Vector((math.cos(aa), math.sin(aa), 0.6)).normalized()
            if kind == 'yarrow':
                add_leaf(geo, p, d, (0, 0, 1), 0.06, 0.012, stem_c * 1.1, n=10, serr=0.8, rng=rng, shape='lance')
            else:
                add_leaf(geo, p, d, (0, 0, 1), 0.05, 0.018, stem_c * 1.1, n=6, shape='lance')
        if kind == 'yarrow':
            col = lin((0.93, 0.91, 0.84))
            for k in range(rng.randint(8, 16)):
                off = np.array([rng.normal(0, 0.016), rng.normal(0, 0.016), rng.uniform(-0.01, 0.005)])
                flower_head(geo, rng, top + off, 0.004, col, petals=5, cup=0.1, centre_col=lin((0.85, 0.8, 0.6)))
        elif kind == 'buttercup':
            flower_head(geo, rng, top, 0.011, lin((0.98, 0.78, 0.04)), petals=5, cup=0.6, centre_col=lin((0.85, 0.65, 0.1)))
        elif kind == 'knapweed':
            col = lin((0.50, 0.22, 0.55))
            flower_head(geo, rng, top, 0.015, col, petals=16, cup=0.9, centre_col=lin((0.35, 0.2, 0.25)))
        else:
            flower_head(geo, rng, top, 0.012, lin((0.86, 0.38, 0.55)), petals=5, cup=0.3, centre_col=lin((0.8, 0.5, 0.6)))
    return geo


def nettle(rng):
    geo = Geo()
    col = lin((0.12, 0.22, 0.06))
    nst = rng.randint(2, 6)
    for s in range(nst):
        a = rng.uniform(0, 2 * math.pi)
        base = np.array([rng.normal(0, 0.06), rng.normal(0, 0.06), -0.01])
        h = rng.uniform(0.45, 1.0)
        lean = rng.uniform(0.0, 0.25)
        blade(geo, rng, base, h, 0.006, lean, a, 0.1, 0.0, col * 0.8, col, nseg=6)
        dirH = np.array([math.cos(a), math.sin(a), 0.0])
        axis = dirH * math.sin(lean) + np.array([0, 0, math.cos(lean)])
        nodes = rng.randint(5, 9)
        rot = rng.uniform(0, math.pi)
        for k in range(nodes):
            t = 0.15 + 0.85 * k / nodes
            p = base + axis * h * t
            size = 0.11 * (1.0 - 0.6 * t) + 0.02
            for side in (0, math.pi):
                aa = rot + side + k * math.pi / 2
                d = Vector((math.cos(aa), math.sin(aa), 0.25)).normalized()
                add_leaf(geo, p, d, (0, 0, 1), size, size * 0.6, col * rng.uniform(0.8, 1.15), n=12, serr=0.35, rng=rng, shape='heart', fold=0.2, curl=-0.2)
    return geo


def fern(rng, size=1.0):
    geo = Geo()
    col = lin((0.16, 0.30, 0.07))
    nf = rng.randint(6, 12)
    for f in range(nf):
        a = f / nf * 2 * math.pi + rng.normal(0, 0.25)
        L = size * rng.uniform(0.45, 0.9)
        rise = rng.uniform(0.9, 1.25)
        pts = []
        tangents = []
        for i in range(13):
            t = i / 12
            ang = rise * (1 - t) - 0.5 * t * t   # arch over
            horiz = L * t
            x = math.cos(a) * horiz
            y = math.sin(a) * horiz
            z = L * 0.55 * math.sin(rise) * t - 0.45 * L * t * t + 0.0
            pts.append(np.array([x, y, max(z, -0.02)]))
        for i in range(13):
            j0, j1 = max(i - 1, 0), min(i + 1, 12)
            tv = pts[j1] - pts[j0]
            tangents.append(tv / np.linalg.norm(tv))
        # rachis
        for i in range(12):
            p0, p1 = pts[i], pts[i + 1]
            s = np.cross(tangents[i], [0, 0, 1.0])
            s = s / (np.linalg.norm(s) + 1e-9) * 0.002
            geo.add([p0 + s, p0 - s, p1 - s, p1 + s], [[0, 1, 2, 3]], [col * 0.7] * 4)
        # pinnae
        for i in range(2, 12):
            t = i / 12
            plen = L * 0.22 * math.sin(math.pi * min(t * 1.1, 1.0)) + 0.01
            tv = tangents[i]
            s = np.cross(tv, [0, 0, 1.0])
            s = s / (np.linalg.norm(s) + 1e-9)
            for side in (-1, 1):
                d = Vector(tuple(s * side + tv * 0.35 + np.array([0, 0, -0.15])))
                add_leaf(geo, tuple(pts[i]), d, (0, 0, 1), plen, plen * 0.32, col * rng.uniform(0.85, 1.15), n=8, serr=0.5, rng=rng, shape='lance', fold=0.08)
    return geo


def rock(rng, size=1.0, flat=0.6, sub=3):
    """Lumpy rock from a subdivided cube with noise. Returns verts, faces."""
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    verts = np.array([v.co[:] for v in bm.verts])
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    seed = rng.randint(0, 10000)
    n1 = C.fbm(verts[:, 0] * 1.2 + verts[:, 2] * 0.7, verts[:, 1] * 1.2 - verts[:, 2] * 0.5, 3, seed)
    n2 = C.fbm(verts[:, 0] * 3.0 + verts[:, 2] * 1.7, verts[:, 1] * 3.0 + verts[:, 2] * 2.1, 2, seed + 7)
    r = 1.0 + 0.28 * n1 + 0.08 * n2
    # flattened facets
    for k in range(4):
        pn = rng.normal(0, 1, 3)
        pn /= np.linalg.norm(pn)
        dd = verts @ pn
        cut = rng.uniform(0.55, 0.85)
        r = np.where(dd * r > cut, r * (cut / np.maximum(dd * r, 1e-6)) ** 0.7, r)
    verts = verts * r[:, None]
    verts[:, 2] *= flat
    verts *= size * np.array([rng.uniform(0.8, 1.3), rng.uniform(0.8, 1.3), 1.0])
    return verts, faces


def twig(rng):
    """A small fallen stick with a side branch."""
    geo = Geo()
    col = lin((0.24, 0.19, 0.14))
    L = rng.uniform(0.12, 0.4)
    pts = []
    d = np.array([1.0, rng.normal(0, 0.2), 0.0])
    p = np.zeros(3)
    for i in range(5):
        pts.append(p.copy())
        d = d + rng.normal(0, 0.25, 3) * np.array([0.2, 1, 0.1])
        d /= np.linalg.norm(d)
        p = p + d * L / 4
    r = rng.uniform(0.004, 0.009)
    for i in range(4):
        a, b = pts[i], pts[i + 1]
        ax = b - a
        ax /= np.linalg.norm(ax)
        s1 = np.cross(ax, [0, 0, 1.0])
        s1 /= np.linalg.norm(s1) + 1e-9
        s2 = np.cross(ax, s1)
        ring_a = [a + (s1 * math.cos(t) + s2 * math.sin(t)) * r for t in np.linspace(0, 2 * math.pi, 5)[:-1]]
        ring_b = [b + (s1 * math.cos(t) + s2 * math.sin(t)) * r * 0.85 for t in np.linspace(0, 2 * math.pi, 5)[:-1]]
        verts = ring_a + ring_b
        faces = [[k, (k + 1) % 4, 4 + (k + 1) % 4, 4 + k] for k in range(4)]
        geo.add(verts, faces, [col * rng.uniform(0.8, 1.2)] * 8)
    return geo


def dung(rng):
    """A small pile of horse droppings: lumpy balls."""
    geo = Geo()
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    bv = np.array([v.co[:] for v in bm.verts])
    bf = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    for k in range(rng.randint(4, 9)):
        r = rng.uniform(0.028, 0.04)
        c = np.array([rng.normal(0, 0.045), rng.normal(0, 0.045), r * 0.6 + (0.035 if k > 4 else 0.0)])
        v = bv * r * np.array([1.0, rng.uniform(0.85, 1.0), rng.uniform(0.75, 0.95)])
        v = v * (1 + 0.12 * C.fbm(v[:, 0] * 40, v[:, 1] * 40 + k, 2, k)[:, None])
        col = lin((0.20, 0.15, 0.08)) * rng.uniform(0.7, 1.2)
        geo.add(v + c, bf, [col] * len(v))
    return geo
