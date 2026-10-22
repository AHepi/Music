"""wood_geo.py - pure numpy geometry for the wood builder (no bpy). Everything is built in WORLD metres.
A MeshData collects vertices, faces (n-gons allowed), a material slot per face, UV per face corner and float attributes per vertex.
Plank builder: one plank = rounded-box loft (worn top edges, 3 mm underside chamfer, bow, cup, twist, dish, chipped corner, end check),
at most 400 vertices. Prisms (posts, bearers, rails, footings) are chamfered extrusions of convex plans.
"""
import math
import numpy as np


# ---------------------------------------------------------------- small helpers
def perp(v):
    return np.array([-v[1], v[0]], dtype=float)


def unit(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


def rot2(v, ang):
    c, s = math.cos(ang), math.sin(ang)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def srgb_to_lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def hex_to_lin(h):
    h = h.lstrip('#')
    return srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]))


def convex_hull(pts):
    pts = sorted(map(tuple, pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1], float)


def poly_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def inset_poly(poly, d):
    """Offset a convex CCW polygon inwards by d (intersection of shifted edge lines)."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        e0, e1 = unit(p1 - p0), unit(p2 - p1)
        n0, n1 = perp(e0), perp(e1)          # inward for CCW
        a = p1 + n0 * d
        b = p1 + n1 * d
        # intersect line (a, e0) with line (b, e1)
        M = np.array([e0, -e1]).T
        det = np.linalg.det(M)
        if abs(det) < 1e-9:
            out.append(a)
        else:
            t = np.linalg.solve(M, b - a)
            out.append(a + e0 * t[0])
    return np.array(out)


# ---------------------------------------------------------------- mesh container
class MeshData:
    def __init__(self):
        self.V = []
        self.F = []
        self.mat = []
        self.uv = []
        self.attr = {}
        self.part = []          # per vertex part id (int)

    def nv(self):
        return len(self.V)

    def add_part(self, V, F, mat, uv, attrs=None, part_id=0):
        base = len(self.V)
        n = len(V)
        self.V.extend([tuple(map(float, v)) for v in V])
        for f in F:
            self.F.append(tuple(base + i for i in f))
        self.mat.extend(mat)
        self.uv.extend(uv)
        self.part.extend([int(part_id)] * n)
        attrs = attrs or {}
        for k in set(list(self.attr.keys()) + list(attrs.keys())):
            col = self.attr.setdefault(k, [0.0] * base)
            if len(col) < base:
                col.extend([0.0] * (base - len(col)))
            v = attrs.get(k, 0.0)
            if np.isscalar(v):
                col.extend([float(v)] * n)
            else:
                col.extend([float(x) for x in v])
        return base

    def bbox(self):
        a = np.array(self.V)
        return a.min(0), a.max(0)


def fix_winding(V, F, centre):
    """Flip faces whose normal points to the given interior point."""
    V = np.asarray(V)
    out = []
    for f in F:
        p = V[list(f)]
        n = np.zeros(3)
        for i in range(len(f)):
            a, b = p[i], p[(i + 1) % len(f)]
            n[0] += (a[1] - b[1]) * (a[2] + b[2])
            n[1] += (a[2] - b[2]) * (a[0] + b[0])
            n[2] += (a[0] - b[0]) * (a[1] + b[1])
        c = p.mean(0)
        if np.dot(n, c - centre) < 0:
            f = tuple(reversed(f))
        out.append(f)
    return out


def unmirror_uv(uv):
    """box UV on the back of a box comes out mirrored; negate u on every face whose UV winding is clockwise so no island is mirrored."""
    out = []
    for f in uv:
        a = 0.0
        for i in range(len(f)):
            x0, y0 = f[i]
            x1, y1 = f[(i + 1) % len(f)]
            a += x0 * y1 - x1 * y0
        out.append([(-u, v) for (u, v) in f] if a < 0 else f)
    return out


def box_uv_for_faces(V, F, tile=1.0, off=(0.0, 0.0)):
    """Box UV per corner: the two axes that are not the face's dominant normal axis, divided by tile (1 UV unit = tile metres)."""
    V = np.asarray(V)
    uv = []
    for f in F:
        p = V[list(f)]
        n = np.zeros(3)
        for i in range(len(f)):
            a, b = p[i], p[(i + 1) % len(f)]
            n[0] += (a[1] - b[1]) * (a[2] + b[2])
            n[1] += (a[2] - b[2]) * (a[0] + b[0])
            n[2] += (a[0] - b[0]) * (a[1] + b[1])
        ax = int(np.argmax(np.abs(n)))
        if ax == 2:
            cols = (0, 1)
        elif ax == 0:
            cols = (1, 2)
        else:
            cols = (0, 2)
        uv.append([((q[cols[0]] / tile) + off[0], (q[cols[1]] / tile) + off[1]) for q in p])
    return unmirror_uv(uv)


# ---------------------------------------------------------------- prisms
def prism(poly, z0, z1, ch=0.0, cb=None, shear=None):
    """Chamfered prism of a convex CCW plan polygon. ch: top chamfer, cb: bottom chamfer (default ch).
    shear: (dx, dy) horizontal drift per metre of height (out of plumb). Returns V, F (outward) ."""
    poly = np.asarray(poly, float)
    if poly_area(poly) < 0:
        poly = poly[::-1]
    cb = ch if cb is None else cb
    rings = []
    if cb > 0:
        rings.append((z0, cb))
        rings.append((z0 + cb, 0.0))
    else:
        rings.append((z0, 0.0))
    if ch > 0:
        rings.append((z1 - ch, 0.0))
        rings.append((z1, ch))
    else:
        rings.append((z1, 0.0))
    V = []
    idx = []
    n = len(poly)
    for z, d in rings:
        pl = inset_poly(poly, d) if d > 0 else poly
        ring = []
        for p in pl:
            x, y = p
            if shear is not None:
                x += (z - z0) * shear[0]
                y += (z - z0) * shear[1]
            V.append((x, y, z))
            ring.append(len(V) - 1)
        idx.append(ring)
    F = []
    for r in range(len(idx) - 1):
        for i in range(n):
            a, b = idx[r][i], idx[r][(i + 1) % n]
            c, d = idx[r + 1][(i + 1) % n], idx[r + 1][i]
            F.append((a, b, c, d))
    F.append(tuple(reversed(idx[0])))
    F.append(tuple(idx[-1]))
    # outward orientation for CCW plan: side quads (a,b,c,d) go CCW seen from outside = outward. caps: bottom reversed, top as is.
    return np.array(V), F


def rect_poly(cx, cy, ax, ay, hl, hw):
    """Rectangle centred (cx, cy), long axis unit vector (ax, ay), half-length hl, half-width hw. CCW."""
    a = np.array([ax, ay], float)
    b = perp(a)
    c = np.array([cx, cy], float)
    return np.array([c - a * hl - b * hw, c + a * hl - b * hw, c + a * hl + b * hw, c - a * hl + b * hw])


def octagon(cx, cy, half, cc, yaw=0.0):
    h = half
    pts = np.array([(h - cc, -h), (h, -h + cc), (h, h - cc), (h - cc, h), (-h + cc, h), (-h, h - cc), (-h, -h + cc), (-h + cc, -h)])
    c, s = math.cos(yaw), math.sin(yaw)
    R = np.array([[c, -s], [s, c]])
    return pts @ R.T + np.array([cx, cy])


# ---------------------------------------------------------------- the plank
ZONE_PHIS = (0.0, 30.0, 60.0, 90.0)


def build_plank(spec):
    """One plank as a rounded-box loft (<= 400 vertices).
    spec keys (metres, radians where noted):
      O (x,y)      world position of the local origin (X=0 at end 0, Y=0 on the centre line)
      ax (x,y)     unit vector of the long axis (local +X); across axis = perp(ax)
      zb           world z of the underside
      L, w, T      length, width, thickness          r: top edge rounding radius     b: underside chamfer
      bow, cup, twist_deg, sweep, dish, dish_x         warps
      chip         None | dict(end 0/1, side -1/+1, cx, cy, depth)
      check        None | dict(end 0/1, y, length, width, depth)
      clip         (x0n, x0f, x1n, x1f) local X of end 0 / end 1 on the near (-w/2) and far (+w/2) long edge
      n_top        number of flat top points across (4 or 5)
      uvoff        random (u, v) UV offset
      attrs        dict plank_id, plank_tone ; damp_fn / wear_fn : f(x, y, z) -> 0..1
    Returns W (verts, world), F, mat (0 top / 1 side / 2 end grain), uv (per corner), attrs, V2 (local after warps)."""
    L, w, T = spec['L'], spec['w'], spec['T']
    r = min(spec.get('r', 0.009), w * 0.3, T * 0.4)
    b = spec.get('b', 0.003)
    n_top = spec.get('n_top', 5)
    clip = spec.get('clip') or (0.0, 0.0, L, L)
    x0n, x0f, x1n, x1f = clip
    ax = unit(spec['ax'])
    ay = perp(ax)
    O = np.array(spec['O'], float)
    zb = spec['zb']
    chk = spec.get('check')
    zone = [r * (1 - math.cos(math.radians(p))) for p in ZONE_PHIS]
    rho_f = [math.sin(math.radians(p)) for p in ZONE_PHIS]
    x0c, x1c = (x0n + x0f) / 2, (x1n + x1f) / 2
    Lc = x1c - x0c
    half = 0.5 * min(x1n - x0n, x1f - x0f)
    mids = [m for m in (0.03, 0.06, 0.10, 0.18, 0.30, 0.42) if r + 0.004 < m < half * 0.9]
    t = 0.42
    while t + 0.45 < half:
        t += 0.45
        mids.append(t)
    first = [(0, z, f, True) for z, f in zip(zone, rho_f)] + [(0, m, 1.0, False) for m in mids]
    st = list(first) + [(2, 0.0, 1.0, False)] + [(1, o, f, zz) for (_, o, f, zz) in reversed(first)]
    ns = len(st)
    yi = w / 2 - r
    zt = T - r
    zbb = b
    ntop_pts = n_top + (3 if chk is not None else 0)
    npr = ntop_pts + 10

    def profile(rho, rho_b, xs):
        ys = list(np.linspace(-yi, yi, n_top))
        pts = [[y, zt + rho] for y in ys]
        if chk is not None:
            d_end = xs if chk['end'] == 0 else (L - xs)
            k = max(1.0 - d_end / chk['length'], 0.0)
            hw, dep = 0.5 * chk['width'] * k, chk['depth'] * k
            yc = chk['y']
            pts += [[yc - hw - 1e-5, zt + rho], [yc, zt + rho - dep], [yc + hw + 1e-5, zt + rho]]
            pts.sort(key=lambda p: p[0])
        for th in (30.0, 60.0):
            tr = math.radians(th)
            pts.append([yi + rho * math.sin(tr), zt + rho * math.cos(tr)])
        pts.append([yi + rho, zt])
        pts.append([yi + rho, zbb])
        pts.append([yi + rho - rho_b, zbb - rho_b])
        pts.append([-(yi + rho - rho_b), zbb - rho_b])
        pts.append([-(yi + rho), zbb])
        pts.append([-(yi + rho), zt])
        for th in (60.0, 30.0):
            tr = math.radians(th)
            pts.append([-(yi + rho * math.sin(tr)), zt + rho * math.cos(tr)])
        return pts

    seg_mat = [0 if not (ntop_pts + 2 <= i <= ntop_pts + 6) else 1 for i in range(npr)]
    V, ring_idx = [], []
    for (side, off, f, is_zone) in st:
        xs_nom = off if side == 0 else (L - off if side == 1 else L / 2)
        pr = profile(r * f, b * f, xs_nom)
        assert len(pr) == npr, (len(pr), npr)
        ring = []
        for (y, z) in pr:
            fr = min(max((y + w / 2) / w, 0.0), 1.0)
            X0 = x0n + (x0f - x0n) * fr
            X1 = x1n + (x1f - x1n) * fr
            X = X0 + off if side == 0 else (X1 - off if side == 1 else 0.5 * (X0 + X1))
            V.append([X, y, z])
            ring.append(len(V) - 1)
        ring_idx.append(ring)
    V = np.array(V, float)
    X, Y, Z = V[:, 0], V[:, 1], V[:, 2].copy()
    tpar = (X - x0c) / max(Lc, 1e-6)
    arch = 1.0 - (2 * tpar - 1) ** 2
    Z += spec.get('bow', 0.0) * arch
    Z += spec.get('cup', 0.0) * (2 * Y / w) ** 2
    Z += Y * np.sin(math.radians(spec.get('twist_deg', 0.0)) * (2 * tpar - 1))
    Y2 = Y + spec.get('sweep', 0.0) * arch
    dish = spec.get('dish', 0.0)
    if dish:
        dx = spec.get('dish_x', x0c + Lc / 2)
        Z -= dish * np.exp(-((X - dx) / 0.17) ** 2) * (V[:, 2] > T * 0.5) * np.exp(-((Y / (w * 0.55)) ** 2))
    ch = spec.get('chip')
    if ch:
        if ch['end'] == 0:
            ex = x0n if ch['side'] < 0 else x0f
            dxe = X - ex
        else:
            ex = x1n if ch['side'] < 0 else x1f
            dxe = ex - X
        dye = (Y + w / 2) if ch['side'] < 0 else (w / 2 - Y)
        pp = dxe / ch['cx'] + dye / ch['cy']
        zlow = T - ch['depth']
        zcut = zlow + ch['depth'] * pp
        m = (pp < 1.0) & (V[:, 2] > zlow - 0.002)
        Z = np.where(m, np.minimum(Z, np.maximum(zcut, zlow)), Z)
    V2 = np.stack([X, Y2, Z], axis=1)
    F, Mt = [], []
    for si in range(ns - 1):
        a, bq = ring_idx[si], ring_idx[si + 1]
        end_band = si < 3 or si >= ns - 4
        for i in range(npr):
            j = (i + 1) % npr
            F.append((a[i], a[j], bq[j], bq[i]))
            Mt.append(2 if end_band else seg_mat[i])
    F.append(tuple(ring_idx[0]))
    Mt.append(2)
    F.append(tuple(reversed(ring_idx[-1])))
    Mt.append(2)
    F = fix_winding(V2, F, np.array([x0c + Lc / 2, 0.0, T / 2]))
    xw = O[0] + V2[:, 0] * ax[0] + V2[:, 1] * ay[0]
    yw = O[1] + V2[:, 0] * ax[1] + V2[:, 1] * ay[1]
    W = np.stack([xw, yw, zb + V2[:, 2]], axis=1)
    uo, vo = spec.get('uvoff', (0.0, 0.0))
    uv = []
    for fi, f in enumerate(F):
        cls = Mt[fi]
        pu = []
        for k in f:
            X_, Y_, Z_ = V2[k]
            pu.append((X_ + uo, Y_ + vo) if cls == 0 else ((X_ + uo, Z_ + vo) if cls == 1 else (Y_ + uo, Z_ + vo)))
        uv.append(pu)
    at = spec.get('attrs', {})
    dfn, wfn = spec.get('damp_fn'), spec.get('wear_fn')
    damp = np.array([dfn(x, y, z) for x, y, z in W]) if dfn else np.zeros(len(W))
    wear = np.array([wfn(x, y, z) for x, y, z in W]) if wfn else np.zeros(len(W))
    attrs = {'wear': wear, 'damp': damp, 'plank_id': np.full(len(W), at.get('plank_id', 0.0)),
             'plank_tone': np.full(len(W), at.get('plank_tone', 0.0))}
    return W, F, Mt, uv, attrs, V2


def plank_local_to_world(spec, X, Y, Z):
    ax = unit(spec['ax'])
    ay = perp(ax)
    O = np.array(spec['O'], float)
    return np.array([O[0] + X * ax[0] + Y * ay[0], O[1] + X * ax[1] + Y * ay[1], spec['zb'] + Z])


def plank_top_z(spec, X, Y):
    """Height (world z) of the top surface of the finished plank at local (X, Y) - an analytic copy of the warps (without edge rounding)."""
    L, w, T = spec['L'], spec['w'], spec['T']
    clip = spec.get('clip') or (0.0, 0.0, L, L)
    x0n, x0f, x1n, x1f = clip
    Lc = (x1n + x1f) / 2 - (x0n + x0f) / 2
    tpar = (X - (x0n + x0f) / 2) / max(Lc, 1e-6)
    arch = 1.0 - (2 * tpar - 1) ** 2
    z = T + spec.get('bow', 0.0) * arch + spec.get('cup', 0.0) * (2 * Y / w) ** 2
    z += Y * math.sin(math.radians(spec.get('twist_deg', 0.0)) * (2 * tpar - 1))
    dish = spec.get('dish', 0.0)
    if dish:
        xc = (x0n + x0f) / 2 + Lc / 2
        z -= dish * math.exp(-((X - spec.get('dish_x', xc)) / 0.17) ** 2) * math.exp(-((Y / (w * 0.55)) ** 2))
    return spec['zb'] + z


# ---------------------------------------------------------------- small parts
def peg_mesh(base, axis, r=0.007, proud=0.007, sink=0.002, n=8):
    """Domed round peg. base: point on the surface, axis: outward unit vector. Ring at the surface (sunk by `sink`), ring at proud*0.7, apex at proud."""
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    helper = np.array([0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(axis, helper); u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    V = []
    for k in range(n):
        a = 2 * math.pi * k / n
        V.append(base - axis * sink + (u * math.cos(a) + v * math.sin(a)) * r)
    for k in range(n):
        a = 2 * math.pi * k / n
        V.append(base + axis * proud * 0.62 + (u * math.cos(a) + v * math.sin(a)) * r * 0.97)
    for k in range(n):
        a = 2 * math.pi * k / n
        V.append(base + axis * proud * 0.93 + (u * math.cos(a) + v * math.sin(a)) * r * 0.62)
    V.append(base + axis * proud)
    F = []
    for ring in range(2):
        for k in range(n):
            a, b = ring * n + k, ring * n + (k + 1) % n
            F.append((a, b, b + n, a + n))
    for k in range(n):
        F.append((2 * n + k, 2 * n + (k + 1) % n, 3 * n))
    return np.array(V), F


def leaf_mesh(centre, yaw, size, curl=0.012, z_lift=0.0, seed=0):
    """A flat maple-leaf outline (5 pointed lobes) with a slight curl. Returns V, F (single double-sided surface, fan)."""
    rng = np.random.default_rng(seed)
    n = 40
    V = [np.array([0.0, 0.0, 0.0])]
    for k in range(n):
        a = 2 * math.pi * k / n
        lobe = abs(math.cos(2.5 * a))
        rr = size * (0.42 + 0.58 * lobe ** 1.3)
        V.append(np.array([rr * math.cos(a), rr * math.sin(a), 0.0]))
    V = np.array(V)
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for p in V:
        x, y = p[0] * c - p[1] * s, p[0] * s + p[1] * c
        rr = math.hypot(p[0], p[1])
        z = curl * (rr / size) ** 2 + z_lift
        out.append((centre[0] + x, centre[1] + y, centre[2] + z))
    F = [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)]
    return np.array(out), F
