"""Village layout: base ground height, road network (with ruts, hoof prints, puddles), building pads.
Pure numpy + mathutils KDTree; no bpy data is touched here."""
import math
import numpy as np
from mathutils import kdtree
from common import smoothstep, perlin2, fbm2, lerp

GX = 200.0          # half extent of the road-mask grid (1 m cells)
GN = 400
CENTER = (18.0, 8.0)

# ------------------------------------------------------------------ base ground
BLOBS = [(-39.3, -12.0, 15.0), (-10.4, -21.8, 14.0), (19.6, 5.6, 16.0), (39.2, -9.4, 14.0), (60.6, 40.1, 15.0), (14.5, 41.0, 20.0)]
def base_height(X, Y):
    X = np.asarray(X, float); Y = np.asarray(Y, float)
    qx = (X - CENTER[0]) / 70.0
    qy = (Y - CENTER[1]) / 50.0
    q = np.sqrt(qx * qx + qy * qy) + 0.10 * fbm2(X * 0.03, Y * 0.03, 3, seed=3)
    clearing = 1.0 - smoothstep(0.80, 1.05, q)
    for (bx, by, br) in BLOBS:
        clearing = np.maximum(clearing, 1.0 - smoothstep(br * 0.7, br * 1.25, np.hypot(X - bx, Y - by)))
    hills = 3.2 * fbm2(X * 0.011, Y * 0.011, 4, seed=1) + 0.9 * fbm2(X * 0.045, Y * 0.045, 3, seed=2)
    amp = 0.22 + 0.78 * (1.0 - clearing)
    r = np.hypot(X - CENTER[0], Y - CENTER[1])
    bowl = 0.0011 * np.maximum(r - 30.0, 0.0) ** 2
    z = hills * amp + bowl + 0.012 * (Y - CENTER[1]) * clearing
    return z, clearing

# ------------------------------------------------------------------ roads
def catmull(ctrl, per=40):
    P = np.asarray(ctrl, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    t = np.linspace(0, 1, per, endpoint=False)[:, None]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2][None, :])
    return np.vstack(out)

def _dilate(mask, r):
    out = mask.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(mask, dx, axis=0), dy, axis=1)
    return out

class Road:
    def __init__(self, rid, name, ctrl, half_w=2.0, gauge=1.45, depth=0.11, ruts=True, hoof=True,
                 fade0=False, fade1=False, verge=1.0, spacing=0.2, reach=3.5):
        self.rid, self.name = rid, name
        self.half_w, self.gauge, self.depth = half_w, gauge, depth
        self.ruts, self.hoof, self.fade0, self.fade1, self.verge = ruts, hoof, fade0, fade1, verge
        dense = catmull(ctrl)
        seg = np.linalg.norm(np.diff(dense, axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(seg)])
        self.L = cum[-1]
        S = np.arange(0, self.L, spacing)
        P = np.stack([np.interp(S, cum, dense[:, 0]), np.interp(S, cum, dense[:, 1])], axis=1)
        self.P, self.S = P, S
        T = np.gradient(P, axis=0)
        T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
        # smooth tangents a bit
        k = 5
        T = np.stack([np.convolve(np.pad(T[:, i], (k, k), mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), mode='valid') for i in range(2)], axis=1)
        T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
        self.T = T
        self.N = np.stack([-T[:, 1], T[:, 0]], axis=1)
        self.kd = kdtree.KDTree(len(P))
        for i, p in enumerate(P):
            self.kd.insert((p[0], p[1], 0.0), i)
        self.kd.balance()
        # influence mask grid
        g = np.zeros((GN, GN), bool)
        ix = np.clip((P[:, 0] + GX).astype(int), 0, GN - 1)
        iy = np.clip((P[:, 1] + GX).astype(int), 0, GN - 1)
        g[ix, iy] = True
        self.mask = _dilate(g, int(math.ceil(half_w + reach)) + 1)
        # centre-line height: smoothed base ground
        z0, _ = base_height(P[:, 0], P[:, 1])
        w = 61
        zp = np.pad(z0, (w, w), mode='edge')
        self.zc = np.convolve(zp, np.ones(2 * w + 1) / (2 * w + 1), mode='valid')
        self.puddles = []   # (s0, side, length, extra_depth)
        self.pads_z = None

    def flatten_for_puddles(self):
        for (s0, side, Lp, ex) in self.puddles:
            z0 = float(np.interp(s0, self.S, self.zc))
            w = smoothstep(Lp + 4.0, Lp * 0.6, np.abs(self.S - s0))
            self.zc = self.zc + (z0 - self.zc) * w

    # --- geometry queries
    def point(self, s):
        s = float(np.clip(s, 0, self.L - 1e-6))
        x = np.interp(s, self.S, self.P[:, 0]); y = np.interp(s, self.S, self.P[:, 1])
        tx = np.interp(s, self.S, self.T[:, 0]); ty = np.interp(s, self.S, self.T[:, 1])
        n = math.hypot(tx, ty)
        return x, y, tx / n, ty / n

    def s_at_x(self, x):
        i = int(np.argmin(np.abs(self.P[:, 0] - x)))
        return self.S[i]

    def zc_at(self, s):
        return np.interp(s, self.S, self.zc)

    def wob(self, s):
        """lateral wander of the cart track centre relative to the polyline"""
        return 0.10 * perlin2(np.asarray(s) * 0.12, 7.7 + self.rid)

    def query(self, X, Y):
        n = len(X)
        d = np.full(n, 1e3); l = np.zeros(n); s = np.zeros(n)
        ix = np.clip((X + GX).astype(int), 0, GN - 1)
        iy = np.clip((Y + GX).astype(int), 0, GN - 1)
        sel = np.nonzero(self.mask[ix, iy])[0]
        if len(sel) == 0:
            return d, l, s
        ks = np.empty(len(sel), dtype=np.int64)
        find = self.kd.find
        Xs, Ys = X[sel], Y[sel]
        for t in range(len(sel)):
            ks[t] = find((Xs[t], Ys[t], 0.0))[1]
        m = len(self.P)
        best_d = np.full(len(sel), 1e9); best_l = np.zeros(len(sel)); best_s = np.zeros(len(sel))
        q = np.stack([Xs, Ys], axis=1)
        for off in (-1, 0):
            a_i = np.clip(ks + off, 0, m - 2)
            b_i = a_i + 1
            a = self.P[a_i]; b = self.P[b_i]
            ab = b - a
            ab2 = (ab ** 2).sum(axis=1) + 1e-12
            t = np.clip(((q - a) * ab).sum(axis=1) / ab2, 0, 1)
            foot = a + ab * t[:, None]
            dv = q - foot
            dist = np.sqrt((dv ** 2).sum(axis=1))
            abn = ab / np.sqrt(ab2)[:, None]
            lat = abn[:, 0] * dv[:, 1] - abn[:, 1] * dv[:, 0]
            sv = self.S[a_i] + t * np.sqrt(ab2)
            better = dist < best_d
            best_d = np.where(better, dist, best_d)
            best_l = np.where(better, lat, best_l)
            best_s = np.where(better, sv, best_s)
        d[sel] = best_d; l[sel] = best_l; s[sel] = best_s
        return d, l, s

    # --- cross-section
    def half_width_at(self, s, X, Y):
        return self.half_w * (1 + 0.20 * perlin2(s * 0.05, self.rid * 3.1)) + 0.38 * fbm2(X * 0.8, Y * 0.8, 3, seed=40 + self.rid)

    def fade(self, s):
        f = np.ones_like(s)
        if self.fade0:
            f = f * smoothstep(0.0, 6.0, s)
        if self.fade1:
            f = f * smoothstep(0.0, 6.0, self.L - s)
        return f

    def detail(self, d, l, s, X, Y):
        """returns dz, cover, rut, wet, centre"""
        W = self.half_width_at(s, X, Y)
        cov = smoothstep(W + 0.30, W - 0.45, d)
        fade = self.fade(s)
        dz = -0.045 * cov
        verge = np.exp(-((d - (W + 0.55)) / 0.5) ** 2) * (0.5 + 0.5 * perlin2(X * 0.4, Y * 0.4, 5))
        dz += 0.06 * verge * self.verge
        rut_f = np.zeros_like(d)
        wet = np.zeros_like(d)
        centre = np.zeros_like(d)
        if self.ruts:
            g = self.gauge * (1 + 0.04 * perlin2(s * 0.1, 3.3 + self.rid))
            wob = self.wob(s)
            for sg in (-1, 1):
                c = sg * g / 2 + wob + 0.06 * perlin2(s * 0.31, 1.1 * sg + self.rid)
                sw = 0.13 + 0.05 * (0.5 + 0.5 * perlin2(s * 0.2, 4.4 + sg + self.rid))
                dep = self.depth * (0.55 + 0.45 * (0.5 + 0.5 * perlin2(s * 0.15, 2.2 * sg + 9 + self.rid)))
                dep *= (0.7 + 0.5 * (0.5 + 0.5 * perlin2(s * 0.045, 1.7 * sg + self.rid)))
                dep *= fade
                u = (l - c) / sw
                ru = np.exp(-u * u)
                dz -= dep * ru
                ub = (l - (c + sg * sw * 2.1)) / (sw * 0.9)
                dz += 0.30 * dep * np.exp(-ub * ub)
                rut_f = np.maximum(rut_f, ru * fade * cov)
                # puddle basins
                for (s0, side, Lp, ex) in self.puddles:
                    if side == sg:
                        ps = np.exp(-(((s - s0) / (Lp * 0.5)) ** 4))
                        dz -= ex * ps * ru
                        wet = np.maximum(wet, ps * np.exp(-((l - c) / (sw * 3.0)) ** 2))
            ctr_w = np.exp(-((l - wob) / 0.42) ** 2)
            centre = ctr_w * cov * fade
            wetness = smoothstep(0.35, 0.8, 0.5 + 0.5 * perlin2(s * 0.09, 5.5 + self.rid))
            wet = np.maximum(wet, rut_f * (0.12 + 0.88 * wetness))
        else:
            # single worn path
            centre = np.exp(-(l / 0.28) ** 2) * cov
            dz -= 0.03 * centre
        dz += cov * (0.014 * fbm2(X * 7, Y * 7, 3, seed=21) + 0.006 * perlin2(X * 23, Y * 23, 9))
        return dz, cov, rut_f, wet, centre

    def hoof_centres(self, rng, s_from=0.0, s_to=None, step=0.42):
        s_to = self.L if s_to is None else s_to
        out = []
        s = s_from
        i = 0
        while s < s_to:
            sg = 1 if i % 2 == 0 else -1
            lat = self.wob(s) + sg * (0.20 + 0.10 * abs(rng.randn())) + 0.05 * rng.randn()
            ds = s + 0.08 * rng.randn()
            x, y, tx, ty = self.point(min(max(ds, 0), self.L - 1e-3))
            nx, ny = -ty, tx
            px, py = x + nx * lat, y + ny * lat
            ang = math.atan2(ty, tx) + 0.14 * rng.randn() + (math.pi if rng.rand() < 0.25 else 0.0)
            depth = 0.05 + 0.04 * rng.rand()
            out.append((px, py, ang, depth, 0.085 + 0.015 * rng.rand()))
            s += step * (0.8 + 0.4 * rng.rand())
            i += 1
        return out

# ------------------------------------------------------------------ the road network
ROADS = {}
def make_roads():
    ROADS.clear()
    ROADS['R1'] = Road(1, 'Main road', [(-135, -50), (-105, -40), (-82, -36), (-64, -27), (-50, -24), (-36, -22), (-22, -15), (-8, -12),
                                         (6, -6), (20, -5), (34, -1), (48, 3), (60, 10), (74, 11), (92, 17), (120, 22), (150, 30)],
                       half_w=2.1, gauge=1.45, depth=0.12)
    ROADS['R2'] = Road(2, 'Stable lane', [(6.5, -6.0), (4.5, 1.5), (3.5, 9.5), (6.0, 17.5), (9.5, 24.5), (13.0, 30.5), (14.0, 33.0)],
                       half_w=1.8, gauge=1.40, depth=0.10, fade1=True)
    ROADS['R3'] = Road(3, 'Farm track', [(48, 3), (49, 12), (52, 21), (55.5, 28), (58, 32)],
                       half_w=1.5, gauge=1.35, depth=0.09, fade1=True)
    return ROADS

# building definitions: name -> dict(road, s (via x), side, offset, W, D, kind)
BUILDINGS = []
def make_buildings():
    BUILDINGS.clear()
    R1, R2, R3 = ROADS['R1'], ROADS['R2'], ROADS['R3']

    def place(road, s, side, off):
        x, y, tx, ty = road.point(s)
        nx, ny = -ty, tx
        px, py = x + side * nx * off, y + side * ny * off
        fx, fy = -side * nx, -side * ny      # facing direction (towards the road)
        yaw = math.atan2(fx, -fy)
        return px, py, yaw

    spec = [
        ('Cottage1', R1, R1.s_at_x(-36), +1, 10.5, 7.2, 4.8, 'cottage', 0),
        ('Cottage2', R1, R1.s_at_x(-12), -1, 9.0, 6.4, 4.6, 'cottage', 1),
        ('Cottage3', R1, R1.s_at_x(22), +1, 10.5, 8.0, 5.0, 'cottage', 2),
        ('Cottage4', R1, R1.s_at_x(37), -1, 9.5, 6.0, 4.4, 'cottage', 3),
    ]
    for name, road, s, side, off, W, D, kind, var in spec:
        px, py, yaw = place(road, s, side, off)
        BUILDINGS.append(dict(name=name, x=px, y=py, yaw=yaw, W=W, D=D, kind=kind, var=var, road=road.name))
    # cottage 5 at the end of the farm track (faces down the track)
    x, y, tx, ty = R3.point(R3.L - 0.5)
    BUILDINGS.append(dict(name='Cottage5', x=x + tx * 8.5 + 0.0, y=y + ty * 8.5, yaw=math.atan2(-tx, ty), W=7.0, D=4.8, kind='cottage', var=4, road='Farm track'))
    # stable at the end of the lane
    x, y, tx, ty = R2.point(R2.L - 0.5)
    BUILDINGS.append(dict(name='Stable', x=14.5, y=41.0, yaw=0.0, W=12.0, D=6.0, kind='stable', var=0, road='Stable lane'))
    return BUILDINGS

def building_pad_z(b):
    xs = np.array([b['x']])
    ys = np.array([b['y']])
    z, _ = base_height(xs, ys)
    return float(z[0])

def pad_flatten(X, Y, z_base):
    """flatten the ground under every building; returns new z and a yard (trampled) factor"""
    z = z_base.copy()
    yard = np.zeros_like(z)
    for b in BUILDINGS:
        c, s_ = math.cos(-b['yaw']), math.sin(-b['yaw'])
        dx, dy = X - b['x'], Y - b['y']
        u = dx * c - dy * s_
        v = dx * s_ + dy * c
        hx, hy = b['W'] / 2 + 0.3, b['D'] / 2 + 0.3
        ex = np.maximum(np.abs(u) - hx, 0)
        ey = np.maximum(np.abs(v) - hy, 0)
        dist = np.hypot(ex, ey)
        w = smoothstep(3.0, 0.3, dist)
        pz = b.get('pad_z')
        if pz is None:
            pz = building_pad_z(b)
            b['pad_z'] = pz
        z = lerp(z, pz, w)
        yard = np.maximum(yard, smoothstep(2.6, 0.6, dist) * (0.55 if b['kind'] == 'cottage' else 0.8))
    return z, yard

# trampled yards (stable forecourt etc.): (cx, cy, rx, ry, rot, strength)
YARDS = [(14.0, 32.0, 8.5, 4.6, 0.0, 1.0), (7.0, -1.0, 4.0, 3.0, 0.4, 0.6)]

def yard_factor(X, Y):
    out = np.zeros_like(X)
    for cx, cy, rx, ry, rot, k in YARDS:
        c, s_ = math.cos(rot), math.sin(rot)
        dx, dy = X - cx, Y - cy
        u = (dx * c + dy * s_) / rx
        v = (-dx * s_ + dy * c) / ry
        r = np.sqrt(u * u + v * v) + 0.12 * fbm2(X * 0.5, Y * 0.5, 3, seed=77)
        out = np.maximum(out, k * smoothstep(1.0, 0.55, r))
    return out

# ------------------------------------------------------------------ full evaluation
HOOF = None
POINTS_HINT = {}
def build_hoof(seed=5):
    global HOOF, HOOF_KD
    rng = np.random.RandomState(seed)
    allc = []
    for r in ROADS.values():
        if r.hoof:
            allc += r.hoof_centres(rng, 0.0, r.L - (6.0 if r.fade1 else 0.0))
    # stable forecourt: random scuffed prints
    for _ in range(90):
        cx, cy = 14.0 + 6.5 * rng.randn() * 0.7, 32.0 + 3.0 * rng.randn() * 0.7
        allc.append((cx, cy, rng.rand() * 6.28, 0.025 + 0.03 * rng.rand(), 0.065 + 0.012 * rng.rand()))
    # a deliberate trail of clear prints on the bare dirt either side of the grass strip near the close-up camera
    if POINTS_HINT.get('sR') is not None:
        r1 = ROADS['R1']
        sR = POINTS_HINT['sR']
        for k in range(18):
            s = sR - 2.2 + k * 0.40
            sg = 1 if k % 2 == 0 else -1
            x, y, tx, ty = r1.point(s)
            lat = r1.wob(s) + sg * (0.46 + 0.05 * rng.randn())
            allc.append((x - ty * lat, y + tx * lat, math.atan2(ty, tx) + 0.1 * rng.randn(), 0.075 + 0.02 * rng.rand(), 0.09 + 0.01 * rng.rand()))
    HOOF = np.array(allc)
    kd = kdtree.KDTree(len(HOOF))
    for i, h in enumerate(HOOF):
        kd.insert((h[0], h[1], 0.0), i)
    kd.balance()
    HOOF_KD = kd
    return kd

HOOF_KD = None
CELL_CHUNK = None
def hoof_dz(X, Y, mask, cell=None):
    """hoof-print depressions at the vertices selected by mask (radius grows on coarse meshes)"""
    out = np.zeros_like(X)
    idx = np.nonzero(mask)[0]
    kd = HOOF_KD
    for q in idx:
        cq = 0.0 if cell is None else float(cell[q])
        if cq > 0.2:
            continue
        reach = max(0.17, 1.4 * cq + 0.1)
        hits = kd.find_range((X[q], Y[q], 0.0), reach)
        if not hits:
            continue
        acc = 0.0
        for co, k, dist in hits:
            cx, cy, ang, dep, rad = HOOF[k]
            rad = max(rad, 0.9 * cq)
            if cq > 0.07:
                dep = dep * 0.7
            ca, sa = math.cos(ang), math.sin(ang)
            dx, dy = X[q] - cx, Y[q] - cy
            a = (dx * ca + dy * sa) / (rad * 1.05)       # along the hoof
            b = (-dx * sa + dy * ca) / (rad * 0.9)       # across
            rho = math.sqrt(a * a + b * b * (1.0 + 0.25 * max(a, 0.0)))
            if rho > 2.6:
                continue
            dish = -dep * (1.0 - min(rho, 1.0) ** 3.0 if rho < 1.0 else 0.0)
            rim = 0.55 * dep * math.exp(-((rho - 1.22) / 0.2) ** 2)
            frog = 0.45 * dep * math.exp(-((a * 1.1) ** 2 + (b * 2.2) ** 2) / 0.12) if rho < 1.0 else 0.0
            acc += dish + rim + frog
        out[q] = acc
    return out

def terrain_eval(X, Y, do_hoof=True, hoof_mask_limit=1.1):
    X = np.asarray(X, float); Y = np.asarray(Y, float)
    z0, clearing = base_height(X, Y)
    zb = z0.copy()
    infl = []
    for r in ROADS.values():
        d, l, s = r.query(X, Y)
        W = r.half_w
        wf = smoothstep(W + 3.4, W + 0.3, d)
        zb = lerp(zb, r.zc_at(s), wf)
        infl.append((r, d, l, s))
    zb, yard_b = pad_flatten(X, Y, zb)
    z = zb.copy()
    cover = np.zeros_like(X); rut = np.zeros_like(X); wet = np.zeros_like(X); centre = np.zeros_like(X)
    pathcov = np.zeros_like(X)
    for r, d, l, s in infl:
        dz, cov, ru, we, ce = r.detail(d, l, s, X, Y)
        z += dz
        cover = np.maximum(cover, cov)
        rut = np.maximum(rut, ru)
        wet = np.maximum(wet, we)
        centre = np.maximum(centre, ce)
    yard = np.maximum(yard_factor(X, Y), yard_b)
    cover = np.maximum(cover, yard)
    # hoof prints on the trampled lane and yards
    if do_hoof and HOOF_KD is not None:
        m = (centre > 0.08) | (yard > 0.5)
        hz = hoof_dz(X, Y, m, CELL_CHUNK)
        z += hz
        wet = np.maximum(wet, np.clip(-hz / 0.045, 0, 1) * 0.9)
    return dict(z=z, clearing=clearing, cover=cover, rut=rut, wet=wet, centre=centre, yard=yard, zbase=zb)
