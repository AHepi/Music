"""Procedural trees: broadleaf (oak, beech, birch, hazel bush) and conifer (spruce)."""
import numpy as np
import math
from mathutils import Vector, Matrix, Quaternion
import common as C
from plants import lin


class TreeGeo:
    def __init__(self):
        self.bark = C.MeshBuilder()
        self.lv = []    # leaf verts
        self.lf = []    # leaf faces
        self.lc = []    # leaf colours (per vertex)

    def leaf_quad(self, base, d, side, n, L, W, col, fold=0.25):
        """Folded diamond leaf: base -> tip along d, side vector, normal n."""
        b = len(self.lv)
        p0 = base
        p2 = base + d * L
        mid = base + d * (L * 0.45)
        p1 = mid + side * (W * 0.5) + n * (W * fold)
        p3 = mid - side * (W * 0.5) + n * (W * fold)
        self.lv.extend([tuple(p0), tuple(p1), tuple(p2), tuple(p3)])
        self.lf.append([b, b + 1, b + 2])
        self.lf.append([b, b + 2, b + 3])
        self.lc.extend([col] * 4)


def _perp(d):
    p = d.orthogonal()
    p.normalize()
    return p


def _rotate(v, axis, ang):
    return Quaternion(axis, ang) @ v


def _branch_polyline(rng, p0, d0, length, nseg, up, wobble, gravity=0.0):
    pts = [Vector(p0)]
    d = Vector(d0).normalized()
    seg = length / nseg
    for i in range(nseg):
        rnd = Vector((rng.normal(), rng.normal(), rng.normal())) * wobble
        d = (d + rnd + Vector((0, 0, up - gravity * (i / nseg)))).normalized()
        pts.append(pts[-1] + d * seg)
    return pts


def _ellipsoid_dist(p, d, centre, rx, rz):
    """Distance along ray p + t*d to the ellipsoid surface (centre, radii rx, rx, rz)."""
    q = (p - centre)
    a = (d.x / rx) ** 2 + (d.y / rx) ** 2 + (d.z / rz) ** 2
    b = 2 * ((q.x * d.x) / rx ** 2 + (q.y * d.y) / rx ** 2 + (q.z * d.z) / rz ** 2)
    c = (q.x / rx) ** 2 + (q.y / rx) ** 2 + (q.z / rz) ** 2 - 1
    disc = b * b - 4 * a * c
    if disc < 0:
        return 0.5
    t = (-b + math.sqrt(disc)) / (2 * a)
    return max(t, 0.3)


def _interp(pts, radii, t):
    n = len(pts) - 1
    x = t * n
    i = min(int(x), n - 1)
    f = x - i
    p = pts[i].lerp(pts[i + 1], f)
    r = radii[i] + (radii[i + 1] - radii[i]) * f
    d = (pts[i + 1] - pts[i]).normalized()
    return p, r, d


BROADLEAF = {
    "oak": dict(height=(12.0, 16.0), crown_base=0.30, crown_r=(5.2, 7.0), trunk_r=(0.40, 0.55),
                limbs=(7, 10), limb_elev=(0.8, 1.3), sub=(9, 13), twigs=(9, 13), wobble=0.2, leader=False,
                leaf_len=0.2, leaf_w=0.14, leaves_per_twig=46, cluster=0.28, leaf_col=(0.13, 0.22, 0.05), bark="bark_oak"),
    "beech": dict(height=(16.0, 21.0), crown_base=0.36, crown_r=(4.6, 6.0), trunk_r=(0.32, 0.45),
                  limbs=(8, 11), limb_elev=(0.45, 0.85), sub=(8, 12), twigs=(9, 12), wobble=0.12, leader=True,
                  leaf_len=0.18, leaf_w=0.12, leaves_per_twig=44, cluster=0.25, leaf_col=(0.19, 0.31, 0.06), bark="bark_beech"),
    "birch": dict(height=(11.0, 15.0), crown_base=0.33, crown_r=(2.6, 3.6), trunk_r=(0.15, 0.22),
                  limbs=(9, 12), limb_elev=(0.5, 0.9), sub=(6, 9), twigs=(7, 10), wobble=0.12, leader=True, droop=0.6,
                  leaf_len=0.13, leaf_w=0.1, leaves_per_twig=40, cluster=0.2, leaf_col=(0.29, 0.39, 0.08), bark="bark_birch"),
    "hazel": dict(height=(3.5, 5.0), crown_base=0.12, crown_r=(2.0, 2.8), trunk_r=(0.04, 0.06), stems=(6, 10),
                  limbs=(2, 3), limb_elev=(0.3, 0.6), sub=(5, 7), twigs=(5, 7), wobble=0.12, leader=False,
                  leaf_len=0.15, leaf_w=0.13, leaves_per_twig=30, cluster=0.2, leaf_col=(0.16, 0.29, 0.06), bark="bark_beech"),
}


def leaves_np(rng, pts, centre, P, scale, n_leaf):
    """Vectorised foliage cluster around a twig polyline. Returns verts (4n,3), faces, colours."""
    pts = np.array([tuple(p) for p in pts])
    nseg = len(pts) - 1
    tt = rng.uniform(0.05, 1.0, n_leaf) * nseg
    i = np.minimum(tt.astype(int), nseg - 1)
    f = (tt - i)[:, None]
    base = pts[i] * (1 - f) + pts[i + 1] * f
    c = np.array(tuple(centre))
    out = base - np.array([c[0], c[1], base[:, 2].mean() * 0 + 0])[None, :]
    out[:, 2] = 0.0
    out = base - np.stack([np.full(n_leaf, c[0]), np.full(n_leaf, c[1]), base[:, 2]], 1)
    on = np.linalg.norm(out, axis=1, keepdims=True) + 1e-6
    out = out / on
    jitter = rng.normal(0, 1, (n_leaf, 3))
    jitter /= np.linalg.norm(jitter, axis=1, keepdims=True)
    rad = P.get("cluster", 0.22) * rng.uniform(0.2, 1.0, (n_leaf, 1)) ** 0.7
    base = base + (jitter * 0.7 + out * 0.5 + np.array([0, 0, 0.25])) * rad
    d = out * 0.5 + rng.normal(0, 0.6, (n_leaf, 3)) + np.array([0, 0, -0.1 - P.get("droop", 0.0) * 0.6])
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    nrm = np.array([0, 0, 0.8]) + out * 0.45 + rng.normal(0, 0.45, (n_leaf, 3))
    side = np.cross(d, nrm)
    side /= np.linalg.norm(side, axis=1, keepdims=True) + 1e-9
    nrm = np.cross(side, d)
    Ls = P["leaf_len"] * rng.uniform(0.7, 1.3, (n_leaf, 1)) * (0.7 + 0.3 * scale)
    Ws = P["leaf_w"] * rng.uniform(0.7, 1.3, (n_leaf, 1)) * (0.7 + 0.3 * scale)
    p0 = base
    p2 = base + d * Ls
    mid = base + d * (Ls * 0.45)
    p1 = mid + side * (Ws * 0.5) + nrm * (Ws * 0.25)
    p3 = mid - side * (Ws * 0.5) + nrm * (Ws * 0.25)
    V = np.stack([p0, p1, p2, p3], 1).reshape(-1, 3)
    # colour: inner leaves darker, a few yellowing
    col = np.array(lin(P["leaf_col"]))
    k = rng.uniform(0.72, 1.28, (n_leaf, 1))
    dist_c = np.linalg.norm(base - c[None, :], axis=1, keepdims=True)
    cols = col[None, :] * k
    yel = rng.uniform(size=n_leaf) < 0.035
    cols[yel] = np.array(lin((0.45, 0.40, 0.10)))[None, :] * rng.uniform(0.8, 1.1, (yel.sum(), 1))
    cols = np.repeat(cols, 4, axis=0)
    return V, cols


def broadleaf(kind, seed, leaves=True, scale=1.0):
    P = BROADLEAF[kind]
    rng = np.random.RandomState(seed)
    g = TreeGeo()
    H = rng.uniform(*P["height"]) * scale
    Rc = rng.uniform(*P["crown_r"]) * scale
    cb = H * P["crown_base"]
    centre = Vector((rng.normal(0, 0.3), rng.normal(0, 0.3), cb + (H - cb) * 0.55))
    rz = (H - cb) * 0.55
    leafc = lin(P["leaf_col"])
    twig_list = []

    def add_tube(pts, radii, sides, rnd):
        if radii[0] < 0.004:
            return
        v, f, uv = C.tube(pts, radii, sides=sides, uv_scale=1.0)
        g.bark.add(v, f, uv, mat=0, rnd=rnd)

    def grow(p0, d0, length, r0, level, max_level, nseg):
        up = 0.05 if level > 0 else 0.02
        grav = P.get("droop", 0.0) * 0.25 * level
        pts = _branch_polyline(rng, p0, d0, length, nseg, up, P["wobble"] * (1 + 0.5 * level), gravity=grav)
        radii = [r0 * (1 - 0.75 * (i / nseg)) for i in range(nseg + 1)]
        radii[-1] = max(radii[-1], 0.003)
        sides = 8 if level == 1 else (6 if level == 2 else 4)
        add_tube(pts, radii, sides, rng.uniform())
        if level >= max_level:
            twig_list.append((pts, radii))
            return
        nkids = rng.randint(*P["sub"]) if level == 1 else rng.randint(*P["twigs"])
        rot0 = rng.uniform(0, 2 * math.pi)
        for k in range(nkids):
            t = rng.uniform(0.25, 0.95) if level == 1 else rng.uniform(0.15, 0.98)
            p, r, d = _interp(pts, radii, t)
            az = rot0 + k * 2.39996
            perp = _perp(d)
            perp = _rotate(perp, d, az)
            ang = rng.uniform(0.5, 0.95)
            cd = (d * math.cos(ang) + perp * math.sin(ang)).normalized()
            cd = (cd + Vector((0, 0, 0.25 if level == 1 else 0.1))).normalized()
            if level == 1:
                Lmax = _ellipsoid_dist(p, cd, centre, Rc, rz)
                L = min(Lmax * rng.uniform(0.55, 0.95), length * 0.85)
                grow(p, cd, max(L, 0.4), r * 0.6, level + 1, max_level, 5)
            else:
                L = rng.uniform(0.5, 1.2) * scale
                grow(p, cd, L, max(r * 0.55, 0.004), level + 1, max_level, 3)

    stems = P.get("stems")
    if stems:
        nst = rng.randint(*stems)
        for s in range(nst):
            az = rng.uniform(0, 2 * math.pi)
            lean = rng.uniform(0.15, 0.55)
            d = Vector((math.cos(az) * math.sin(lean), math.sin(az) * math.sin(lean), math.cos(lean)))
            base = Vector((rng.normal(0, 0.12), rng.normal(0, 0.12), -0.05))
            L = H * rng.uniform(0.75, 1.0)
            grow(base, d, L, rng.uniform(*P["trunk_r"]) * scale, 1, 3, 6)
    else:
        # trunk with root flare
        r0 = rng.uniform(*P["trunk_r"]) * scale
        top = H * (0.92 if P["leader"] else 0.55)
        n = 12
        pts = []
        lean_dir = Vector((rng.normal(), rng.normal(), 0)) * 0.03
        for i in range(n + 1):
            t = i / n
            z = -0.25 + (top + 0.25) * t
            sway = Vector((math.sin(t * 3.1 + seed) * 0.15, math.cos(t * 2.3 + seed) * 0.15, 0)) * t + lean_dir * z
            pts.append(Vector((0, 0, z)) + sway)
        radii = []
        for i in range(n + 1):
            t = i / n
            z = pts[i].z
            rr = r0 * (1 - 0.8 * t) + 0.01
            rr *= 1 + 0.55 * math.exp(-max(z, 0) / 0.45)
            radii.append(rr)
        lobes = rng.randint(4, 7)
        phase = rng.uniform(0, 6.28)

        def rn(i, k):
            z = pts[i].z
            a = 2 * math.pi * k / 14
            return 1.0 + 0.22 * math.cos(lobes * a + phase) * math.exp(-max(z, 0) / 0.6) + 0.03 * math.sin(3 * a + i)
        v, f, uv = C.tube(pts, radii, sides=14, uv_scale=1.0, radius_noise=rn)
        g.bark.add(v, f, uv, mat=0, rnd=rng.uniform())
        trunk_pts, trunk_r = pts, radii
        nl = rng.randint(*P["limbs"])
        rot0 = rng.uniform(0, 6.28)
        for k in range(nl):
            if P["leader"]:
                t = rng.uniform(P["crown_base"] * 1.0 / 0.92, 0.97)
            else:
                t = rng.uniform(0.7, 1.0)
            p, r, d = _interp(trunk_pts, trunk_r, min(t, 1.0))
            az = rot0 + k * 2.39996 + rng.normal(0, 0.3)
            el = rng.uniform(*P["limb_elev"])
            cd = Vector((math.cos(az) * math.sin(el), math.sin(az) * math.sin(el), math.cos(el)))
            L = _ellipsoid_dist(p, cd, centre, Rc, rz) * rng.uniform(0.8, 1.0)
            grow(p, cd, max(L, 1.0), r * rng.uniform(0.45, 0.65), 1, 3, 7)
    if leaves:
        allV = []
        allC = []
        for pts, radii in twig_list:
            V, cols = leaves_np(rng, pts, centre, P, scale, P["leaves_per_twig"])
            allV.append(V)
            allC.append(cols)
        if allV:
            V = np.concatenate(allV)
            cols = np.concatenate(allC)
            b0 = len(g.lv)
            n = len(V) // 4
            g.lv.extend(map(tuple, V))
            idx = b0 + np.arange(n) * 4
            g.lf.extend(np.stack([idx, idx + 1, idx + 2], 1).tolist())
            g.lf.extend(np.stack([idx, idx + 2, idx + 3], 1).tolist())
            g.lc.extend(map(tuple, cols))
    return g, dict(height=H, crown=Rc, bark=P["bark"], kind=kind)


def spruce(seed, height=None, low_branch=1.2, dead_lower=0.0, scale=1.0, fronds=True):
    rng = np.random.RandomState(seed)
    g = TreeGeo()
    H = (height or rng.uniform(17.0, 25.0)) * scale
    r0 = (0.24 + 0.006 * H) * scale
    Rmax = rng.uniform(2.4, 3.3) * scale * (H / 21.0) ** 0.5
    # trunk
    n = 14
    pts = []
    for i in range(n + 1):
        t = i / n
        z = -0.25 + (H + 0.25) * t
        pts.append(Vector((math.sin(t * 2.0 + seed) * 0.06 * t, math.cos(t * 1.7 + seed) * 0.06 * t, z)))
    radii = []
    for i in range(n + 1):
        t = i / n
        z = pts[i].z
        rr = r0 * (1 - t) ** 1.1 + 0.008
        rr *= 1 + 0.45 * math.exp(-max(z, 0) / 0.4)
        radii.append(rr)

    def rn(i, k):
        z = pts[i].z
        a = 2 * math.pi * k / 12
        return 1.0 + 0.2 * math.cos(5 * a + seed) * math.exp(-max(z, 0) / 0.5)
    v, f, uv = C.tube(pts, radii, sides=12, uv_scale=1.0, radius_noise=rn)
    g.bark.add(v, f, uv, mat=0, rnd=rng.uniform())
    needle = lin((0.10, 0.165, 0.072))
    z = low_branch * scale
    whorl = 0
    while z < H - 0.35:
        frac = (H - z) / (H - low_branch * scale)
        L = Rmax * (frac ** 0.95) * rng.uniform(0.85, 1.12) + 0.15
        nb = rng.randint(6, 9)
        rot0 = rng.uniform(0, 2 * math.pi)
        dead = (z < dead_lower * H)
        for k in range(nb):
            az = rot0 + k * 2 * math.pi / nb + rng.normal(0, 0.2)
            el = math.radians(rng.uniform(-8, 12) - 18 * (1 - frac))
            d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
            p0 = Vector((0, 0, z))
            nseg = 6
            bp = [p0]
            dd = d.copy()
            for i in range(nseg):
                t = (i + 1) / nseg
                # sag in the middle, tip turns up a little
                dd = (dd + Vector((0, 0, -0.10 * (1 - frac) - 0.03 + 0.12 * t * t))).normalized()
                bp.append(bp[-1] + dd * (L / nseg))
            br = [max(0.06 * scale * (L / 3.0) * (1 - 0.85 * i / nseg), 0.006) for i in range(nseg + 1)]
            vv, ff, uu = C.tube(bp, br, sides=5, uv_scale=1.0)
            g.bark.add(vv, ff, uu, mat=0, rnd=rng.uniform())
            if dead or not fronds:
                continue
            # branchlets hanging from the branch, each a pair of crossed needle strips
            m = max(int(L / 0.12), 2)
            for j in range(m):
                t = (j + 0.5) / m
                if t < 0.15:
                    continue
                p, r, bd = _interp(bp, br, t)
                side = bd.cross(Vector((0, 0, 1)))
                if side.length < 1e-4:
                    side = Vector((1, 0, 0))
                side.normalize()
                for sgn in (-1, 1):
                    cl = (0.45 * (1 - 0.6 * t) + 0.12) * rng.uniform(0.7, 1.15) * min(1.0, L / 1.2 + 0.3)
                    cd = (bd * 0.55 + side * sgn * 0.8 + Vector((0, 0, -0.35 * (1 - frac) - 0.1))).normalized()
                    needle_strip(g, rng, p, cd, cl, 0.15 * scale ** 0.3, needle)
                # hanging curtain of branchlets under the branch (spruce 'comb')
                if frac < 0.85 and rng.uniform() < 0.7:
                    cl = (0.35 * (1 - 0.5 * t) + 0.1) * rng.uniform(0.6, 1.1)
                    cd = (bd * 0.35 + side * rng.normal(0, 0.3) + Vector((0, 0, -0.9))).normalized()
                    needle_strip(g, rng, p, cd, cl, 0.12, needle * 0.85)
            # tip spray
            p, r, bd = _interp(bp, br, 1.0)
            needle_strip(g, rng, p - bd * 0.25, bd, 0.35, 0.12, needle)
        z += rng.uniform(0.26, 0.42) * scale ** 0.5
        whorl += 1
    # leader tip
    tip = Vector((0, 0, H - 0.4))
    needle_strip(g, rng, tip, Vector((0, 0, 1)), 0.6, 0.1, needle)
    return g, dict(height=H, crown=Rmax, bark="bark_spruce", kind="spruce")


def needle_strip(g, rng, p, d, length, width, col):
    """Two crossed jagged strips standing in for a needle-covered twig."""
    d = d.normalized()
    up = Vector((0, 0, 1))
    s1 = d.cross(up)
    if s1.length < 1e-4:
        s1 = Vector((1, 0, 0))
    s1.normalize()
    n1 = s1.cross(d).normalized()
    segs = 4
    c = col * rng.uniform(0.75, 1.3)
    for (sv, nv, wf) in ((s1, n1, 1.0), (n1, s1, 0.6)):
        b = len(g.lv)
        verts = []
        for i in range(segs + 1):
            t = i / segs
            w = width * wf * (0.55 + 0.45 * math.sin(math.pi * min(t * 1.2, 1.0))) * (1.15 if i % 2 else 0.8)
            q = p + d * (length * t) + nv * (-0.02 * t * t)
            verts.append(q + sv * w * 0.5)
            verts.append(q - sv * w * 0.5)
        g.lv.extend([tuple(v) for v in verts])
        for i in range(segs):
            a = b + 2 * i
            g.lf.append([a, a + 1, a + 3, a + 2])
        g.lc.extend([c] * len(verts))
