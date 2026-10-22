"""GROUND builder, step 1: grass tuft recipes (12 shapes, several tints), their placement in clumps, small flowers and twigs.
Shapes follow the concept sheet (sheet_grass.jpg): 5 to 9 simple tapered curved blades, chunky (6 mm and more at the base), three kinds of
seed head, a broad-leaf kind for the rock feet, a dry straw clump, a clover patch of flat leaf discs. Colour is a vertex colour (attribute 'Col'):
dark olive base (#2a2d24) to lighter olive tip (#6a6a2e), 20 % straw tips (#8a7a3a), 10 % reddish (#7a4a22).
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from g6_common import (hex_lin, lerp3, mesh_from_arrays, add_object, PFX, get_collection, tag, smoothstep)

# ---------------------------------------------------------------- colours (linear)
C_BASE = hex_lin('#2a2d24')
C_TIP = hex_lin('#5c6c2c')
C_STRAW = hex_lin('#7c6e38')
C_RED = hex_lin('#84522e')
C_MID_OLIVE = hex_lin('#3a4a26')

TINTS = {
    'olive': [(0.0, C_BASE), (0.55, C_MID_OLIVE), (1.0, C_TIP)],
    'straw': [(0.0, C_BASE), (0.42, C_MID_OLIVE), (0.80, hex_lin('#5e6030')), (1.0, C_STRAW)],
    'red':   [(0.0, C_BASE), (0.45, hex_lin('#55432a')), (1.0, C_RED)],
    'dry':   [(0.0, hex_lin('#3a3020')), (0.5, hex_lin('#62552e')), (1.0, hex_lin('#85763e'))],
    'broad': [(0.0, hex_lin('#232b1c')), (0.5, hex_lin('#3e4626')), (1.0, hex_lin('#5e6a30'))],
    'stalk': [(0.0, hex_lin('#33361f')), (1.0, hex_lin('#6e6234'))],
    'head':  [(0.0, hex_lin('#5e5030')), (1.0, hex_lin('#8c7a46'))],
    'leaf':  [(0.0, hex_lin('#222a1a')), (1.0, hex_lin('#566428'))],
}


def grad(kind, t, bright=1.0):
    stops = TINTS[kind]
    t = min(max(t, 0.0), 1.0)
    for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
        if t <= t1:
            f = (t - t0) / max(t1 - t0, 1e-6)
            c = lerp3(c0, c1, f * f * (3 - 2 * f) * 0.5 + f * 0.5)
            return tuple(min(1.0, v * bright) for v in c)
    return tuple(min(1.0, v * bright) for v in stops[-1][1])


class Mesh:
    def __init__(self):
        self.v, self.f, self.c = [], [], []

    def add(self, verts, faces, cols):
        o = len(self.v)
        self.v += [tuple(p) for p in verts]
        self.c += [tuple(c) for c in cols]
        self.f += [tuple(i + o for i in fc) for fc in faces]

    def arrays(self):
        return np.array(self.v, dtype=np.float32), self.f, np.array(self.c, dtype=np.float32)

    def tris(self):
        return sum(len(f) - 2 for f in self.f)


def centreline(H, lean, bend, n=24):
    """arc in the (r, z) plane: angle from vertical = lean + bend * s^1.25 (radians). returns arrays r[0..n], z[0..n]."""
    s = np.linspace(0.0, 1.0, n + 1)
    ang = lean + bend * s ** 1.25
    ds = H / n
    r = np.concatenate([[0.0], np.cumsum(np.sin(ang[:-1] + 0.5 * np.diff(ang)) * ds)])
    z = np.concatenate([[0.0], np.cumsum(np.cos(ang[:-1] + 0.5 * np.diff(ang)) * ds)])
    return r, z


def ring_points(r, z, ts):
    n = len(r) - 1
    out = []
    for t in ts:
        f = t * n
        i = min(int(f), n - 1)
        u = f - i
        out.append((r[i] + (r[i + 1] - r[i]) * u, z[i] + (z[i + 1] - z[i]) * u))
    return out


def add_blade(m, base, az, H, W0, lean_deg, bend_deg, kind='olive', bright=1.0, prof=(1.0, 1.04, 0.62), ts=(0.0, 0.40, 0.76),
              roll_deg=0.0, tint_t0=0.0):
    """one tapered, curved, flat ribbon: 3 rings + a tip = 5 triangles. base = (x, y, z) of the blade foot."""
    r, z = centreline(H, math.radians(lean_deg), math.radians(bend_deg))
    pts = ring_points(r, z, ts + (1.0,))
    d = np.array([math.cos(az), math.sin(az), 0.0])
    w0 = np.array([-math.sin(az), math.cos(az), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    roll = math.radians(roll_deg)
    verts, cols = [], []
    for i, (pr, pz) in enumerate(pts[:-1]):
        c = np.array(base) + d * pr + up * pz
        # the width axis tilts a little (roll) so blades are not all flat to the same side
        w = w0 * math.cos(roll) + d * math.sin(roll)
        hw = W0 * prof[i] * 0.5
        verts += [c - w * hw, c + w * hw]
        t = tint_t0 + (1 - tint_t0) * ts[i]
        col = grad(kind, t, bright)
        cols += [col, col]
    pr, pz = pts[-1]
    verts.append(np.array(base) + d * pr + up * pz)
    cols.append(grad(kind, 1.0, bright))
    faces = [(0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 6)]
    m.add(verts, faces, cols)
    return (np.array(base) + d * pr + up * pz, np.array([math.sin(math.radians(lean_deg) + math.radians(bend_deg)) * d[0],
                                                          math.sin(math.radians(lean_deg) + math.radians(bend_deg)) * d[1],
                                                          math.cos(math.radians(lean_deg) + math.radians(bend_deg))]))


def add_spike(m, tip_pos, axis, L, R, kind='head', bright=1.0, sides=3):
    """chunky seed spike: tapered prism along `axis` starting at tip_pos (the stalk top). 3 sides, 3 rings + a point = 15 triangles."""
    a = np.array(axis, dtype=float)
    a /= np.linalg.norm(a)
    tmp = np.array([0.0, 0.0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(a, tmp)
    u /= np.linalg.norm(u)
    v = np.cross(a, u)
    rings = [(0.0, 0.55), (0.16, 1.0), (0.66, 0.9), (0.90, 0.45)]
    verts, cols = [], []
    for s, rr in rings:
        for k in range(sides):
            ang = 2 * math.pi * k / sides + 0.4
            verts.append(np.array(tip_pos) + a * L * s + (u * math.cos(ang) + v * math.sin(ang)) * R * rr)
            cols.append(grad(kind, s, bright))
    verts.append(np.array(tip_pos) + a * L)
    cols.append(grad(kind, 1.0, bright))
    faces = []
    for ri in range(len(rings) - 1):
        for k in range(sides):
            a0 = ri * sides + k
            a1 = ri * sides + (k + 1) % sides
            faces.append((a0, a1, a1 + sides, a0 + sides))
    last = (len(rings) - 1) * sides
    for k in range(sides):
        faces.append((last + k, last + (k + 1) % sides, len(verts) - 1))
    m.add(verts, faces, cols)


def add_pod(m, pos, length=0.022, R=0.007, kind='head', bright=1.0):
    """a drooping oat-like pod: 4 sided bipyramid hanging down (8 triangles)."""
    pos = np.array(pos)
    top = pos
    mid = pos + np.array([0, 0, -length * 0.45])
    bot = pos + np.array([0, 0, -length])
    verts = [top]
    cols = [grad(kind, 0.1, bright)]
    for k in range(4):
        a = math.pi / 2 * k + 0.3
        verts.append(mid + np.array([math.cos(a) * R, math.sin(a) * R, 0]))
        cols.append(grad(kind, 0.5, bright))
    verts.append(bot)
    cols.append(grad(kind, 1.0, bright))
    faces = [(0, 1 + k, 1 + (k + 1) % 4) for k in range(4)] + [(5, 1 + (k + 1) % 4, 1 + k) for k in range(4)]
    m.add(verts, faces, cols)


def add_leaf_disc(m, centre, radius, tilt_xy=(0.0, 0.0), cup=0.004, kind='leaf', bright=1.0):
    """a small flat trefoil-ish leaf disc (hexagon fan, 6 triangles), a little cupped."""
    c = np.array(centre)
    verts = [c + np.array([0, 0, -cup])]
    cols = [grad(kind, 0.1, bright)]
    for k in range(6):
        a = math.pi / 3 * k
        verts.append(c + np.array([math.cos(a) * radius + tilt_xy[0] * radius, math.sin(a) * radius + tilt_xy[1] * radius, 0.0]))
        cols.append(grad(kind, 0.8, bright))
    faces = [(0, 1 + k, 1 + (k + 1) % 6) for k in range(6)]
    m.add(verts, faces, cols)


# ---------------------------------------------------------------- recipes
def build_recipe(key, tint, seed):
    """returns a Mesh (verts around the origin, foot at z = -0.01) for recipe `key` in tint `tint` ('olive','straw','red','dry')."""
    rng = np.random.default_rng(seed)
    m = Mesh()
    foot = (0.0, 0.0, -0.012)
    kind = {'olive': 'olive', 'straw': 'straw', 'red': 'red', 'dry': 'dry'}[tint]

    def fan(n, H, W, lean, bend, spread=0.012, jitter=0.18, kindx=None, prof=(0.95, 1.4, 0.8), roll=18):
        a0 = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            az = a0 + 2 * math.pi * i / n + rng.uniform(-jitter, jitter) * 2 * math.pi / n * 2
            hh = H * rng.uniform(0.72, 1.12)
            b = (foot[0] + math.cos(az) * spread * rng.uniform(0.3, 1.0), foot[1] + math.sin(az) * spread * rng.uniform(0.3, 1.0), foot[2])
            add_blade(m, b, az + rng.uniform(-0.25, 0.25), hh, W * rng.uniform(0.85, 1.15), rng.uniform(*lean), rng.uniform(*bend),
                      kind=kindx or kind, bright=rng.uniform(0.86, 1.14), prof=prof, roll_deg=rng.uniform(-roll, roll))

    if key == 'fan_short':
        fan(7, 0.17, 0.0140, (28, 48), (10, 30))
    elif key == 'fan_wide':
        fan(9, 0.20, 0.0135, (52, 72), (6, 22), spread=0.02)
    elif key == 'arch_medium':
        fan(6, 0.31, 0.0145, (10, 30), (35, 62))
    elif key == 'upright_tall':
        fan(6, 0.50, 0.0150, (2, 11), (4, 14), spread=0.01, roll=10)
    elif key == 'tall_arch':
        fan(6, 0.54, 0.0150, (8, 18), (28, 55), spread=0.012)
    elif key == 'bent_red':
        fan(6, 0.28, 0.0145, (28, 44), (50, 72), spread=0.016)
    elif key == 'straw_dry':
        fan(8, 0.30, 0.0100, (18, 42), (14, 46), spread=0.016, jitter=0.4, prof=(0.95, 1.2, 0.7))
    elif key == 'broadleaf':
        fan(5, 0.26, 0.036, (32, 52), (18, 40), spread=0.02, kindx='broad', prof=(0.42, 1.0, 0.78), roll=25)
    elif key in ('seed_spike', 'seed_plume', 'seed_nod'):
        fan(5 if key != 'seed_plume' else 6, 0.27 if key != 'seed_nod' else 0.24, 0.0140, (12, 34), (28, 52))
        ns = {'seed_spike': 3, 'seed_plume': 2, 'seed_nod': 3}[key]
        a0 = rng.uniform(0, 2 * math.pi)
        for i in range(ns):
            az = a0 + 2 * math.pi * i / ns + rng.uniform(-0.4, 0.4)
            Hs = {'seed_spike': 0.50, 'seed_plume': 0.44, 'seed_nod': 0.38}[key] * rng.uniform(0.85, 1.1)
            lean = {'seed_spike': (3, 11), 'seed_plume': (6, 14), 'seed_nod': (8, 16)}[key]
            bend = {'seed_spike': (2, 9), 'seed_plume': (22, 40), 'seed_nod': (50, 85)}[key]
            tip, ax = add_blade(m, (foot[0] + math.cos(az) * 0.01, foot[1] + math.sin(az) * 0.01, foot[2]), az, Hs, 0.0068, rng.uniform(*lean),
                                rng.uniform(*bend), kind='stalk', bright=rng.uniform(0.9, 1.1), prof=(1.0, 0.85, 0.62))
            if key == 'seed_spike':
                add_spike(m, tip - np.array(ax) * 0.012, ax, 0.074 * rng.uniform(0.9, 1.1), 0.0085, kind='head', bright=rng.uniform(0.92, 1.1))
            elif key == 'seed_plume':
                a2 = np.array(ax) + np.array([math.cos(az) * 0.5, math.sin(az) * 0.5, -0.25])
                add_spike(m, tip - np.array(ax) * 0.01, a2, 0.085, 0.0075, kind='head', bright=rng.uniform(0.95, 1.12))
            else:
                for j in range(3):
                    off = np.array([math.cos(az) * 0.012 * j, math.sin(az) * 0.012 * j, -0.016 * j])
                    add_pod(m, tip + off + np.array([math.cos(az + 1.57) * 0.004 * (j - 1), math.sin(az + 1.57) * 0.004 * (j - 1), 0]), kind='head',
                            bright=rng.uniform(0.92, 1.1))
    elif key == 'clover':
        n = 6
        a0 = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            az = a0 + 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
            rr = rng.uniform(0.025, 0.065)
            hh = rng.uniform(0.028, 0.05)
            add_blade(m, (foot[0], foot[1], foot[2]), az, hh * 1.3, 0.0055, 55 + rng.uniform(-10, 10), -20, kind='stalk', prof=(1.0, 0.9, 0.8))
            c = (math.cos(az) * rr, math.sin(az) * rr, hh)
            add_leaf_disc(m, c, rng.uniform(0.016, 0.022), tilt_xy=(0.0, 0.0), cup=rng.uniform(0.003, 0.006), bright=rng.uniform(0.9, 1.15))
    else:
        raise ValueError(key)
    return m


# (key, tint, weight, scale min, scale max, name)
VARIANTS = [
    ('fan_short', 'olive', 0.115, 0.72, 1.15),
    ('fan_short', 'straw', 0.045, 0.72, 1.15),
    ('fan_wide', 'olive', 0.07, 0.62, 1.10),
    ('arch_medium', 'olive', 0.115, 0.78, 1.20),
    ('arch_medium', 'straw', 0.035, 0.78, 1.20),
    ('upright_tall', 'olive', 0.025, 0.85, 1.2),
    ('upright_tall', 'straw', 0.02, 0.85, 1.2),
    ('tall_arch', 'olive', 0.03, 0.75, 1.15),
    ('seed_spike', 'olive', 0.085, 0.75, 1.15),
    ('seed_plume', 'olive', 0.055, 0.80, 1.20),
    ('seed_nod', 'olive', 0.06, 0.85, 1.28),
    ('broadleaf', 'olive', 0.06, 0.55, 1.12),
    ('straw_dry', 'dry', 0.06, 0.80, 1.20),
    ('clover', 'olive', 0.045, 0.80, 1.65),
    ('bent_red', 'red', 0.06, 0.80, 1.28),
    ('arch_medium', 'red', 0.025, 0.78, 1.20),
]
RECIPE_SEEDS = {'fan_short': 101, 'fan_wide': 102, 'arch_medium': 103, 'upright_tall': 104, 'tall_arch': 105, 'bent_red': 106, 'straw_dry': 107,
                'broadleaf': 108, 'seed_spike': 109, 'seed_plume': 110, 'seed_nod': 111, 'clover': 112}
SEED_HEAD_KEYS = ('seed_spike', 'seed_plume', 'seed_nod')
STRAW_TIP = ('straw', 'dry')


def build_sources(material):
    """creates the 16 hidden source objects (12 shapes, 4 extra tint variants). returns a list of dicts."""
    out = []
    for i, (key, tint, w, smin, smax) in enumerate(VARIANTS):
        m = build_recipe(key, tint, RECIPE_SEEDS[key] + {'olive': 0, 'straw': 50, 'red': 100, 'dry': 0}[tint])
        v, f, c = m.arrays()
        me = mesh_from_arrays(PFX + 'tuft %02d %s %s' % (i, key, tint), v, f, cols=c)
        ob = add_object(PFX + 'tuft %02d %s %s' % (i, key, tint), me, 'growth', mats=[material], hide_render=True)
        ob['g6_tuft_key'] = key
        ob['g6_tuft_tint'] = tint
        ob['g6_tris'] = m.tris()
        ob['g6_height_m'] = float(v[:, 2].max())
        out.append(dict(obj=ob, key=key, tint=tint, weight=w, smin=smin, smax=smax, tris=m.tris(), verts=len(v), height=float(v[:, 2].max())))
    return out


# ---------------------------------------------------------------- placement
def lawn_clumps(world, fields, rng, target_tufts=1150, verbose=True):
    """returns lists x, y, z, pick, scale, rot for the tufts. Clumps of 2 to 5 tufts (clump radius 15 to 35 cm), denser at rock feet, the
    pond edge, the kerb, path edges and the plinth foot, sparse in the open lawn. Only where a camera can see (plus a margin)."""
    xs, ys = world.grid()
    dR, dW, dK, dP, dL = fields['rock'], fields['water'], fields['kerb'], fields['pathedge'], fields['plinth']
    nW, nV = len(VARIANTS), None
    base = 0.72                                    # clumps per m2 in the open lawn
    dens = base + 6.8 * np.exp(-dR / 0.40) + 4.8 * np.exp(-dW / 0.45) + 4.6 * np.exp(-dK / 0.32) + 5.8 * np.exp(-dP / 0.36) + 3.4 * np.exp(-dL / 0.32)
    cells = []
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            cells.append((i, j, x, y))
    sel = []
    for i, j, x, y in cells:
        if x < -9.5 or x > 9.5 or y < -7.5 or y > 11.5:
            continue
        if not world.visible(x, y, 0.2, margin=0.05):
            continue
        sel.append((i, j, x, y))
    if verbose:
        print('G6 tufts: candidate cells in view', len(sel), 'of', len(cells))
    clumps = []
    for i, j, x, y in sel:
        lam = dens[j, i] * 0.01
        k = rng.poisson(lam)
        for _ in range(k):
            cx = x + rng.uniform(-0.05, 0.05)
            cy = y + rng.uniform(-0.05, 0.05)
            clumps.append((cx, cy, dR[j, i], dW[j, i], dK[j, i], dP[j, i], dL[j, i]))
    if verbose:
        print('G6 tufts: raw clump centres', len(clumps))
    # contextual weights per variant
    base_w = np.array([v[2] for v in VARIANTS], dtype=np.float64)
    keys = [v[0] for v in VARIANTS]
    tints = [v[1] for v in VARIANTS]

    def weights(dr, dw, dk, dp, dl, dcam=9.0):
        w = base_w.copy()
        if dcam < 3.8:
            for q, kq in enumerate(keys):
                if kq in ('upright_tall', 'tall_arch', 'straw_dry'):
                    w[q] *= 0.12
                elif kq in ('seed_spike', 'seed_plume', 'seed_nod', 'arch_medium'):
                    w[q] *= 0.55
        near_rock, near_water, near_edge = dr < 0.55, dw < 0.5, (dk < 0.5) or (dp < 0.45) or (dl < 0.5)
        for q, kq in enumerate(keys):
            if near_rock:
                if kq == 'broadleaf':
                    w[q] *= 4.0
                elif kq in SEED_HEAD_KEYS:
                    w[q] *= 1.5
                elif kq in ('fan_short', 'clover'):
                    w[q] *= 0.5
            if near_water:
                if kq in ('upright_tall', 'tall_arch'):
                    w[q] *= 3.0
                elif kq in ('seed_spike', 'seed_plume'):
                    w[q] *= 1.8
                elif kq == 'clover':
                    w[q] *= 0.2
            if near_edge:
                if kq in ('seed_nod', 'seed_plume', 'straw_dry', 'upright_tall'):
                    w[q] *= 2.0
            if not (near_rock or near_water or near_edge):
                if kq in ('fan_short', 'fan_wide', 'clover'):
                    w[q] *= 1.8
                elif kq in ('tall_arch', 'upright_tall', 'broadleaf'):
                    w[q] *= 0.3
        return w / w.sum()

    X, Y, Z, PK, SC, RT = [], [], [], [], [], []
    n_ok = 0
    for (cx, cy, dr, dw, dk, dp, dl) in clumps:
        if world.mask_at(cx, cy) > 0.32:           # worn path: keep it bare (a few tufts only at its ragged edge)
            continue
        if not world.free(cx, cy, 0.06, zmin=-0.06):
            continue
        n_ok += 1
        n = int(rng.choice([2, 3, 3, 4, 4, 5], p=[0.2, 0.25, 0.2, 0.15, 0.12, 0.08])) if (dr < 0.5 or dw < 0.45 or dp < 0.4) else int(rng.choice([2, 3, 3, 4], p=[0.3, 0.35, 0.2, 0.15]))
        rad = rng.uniform(0.15, 0.35)
        dcam = min(math.hypot(cx - c.location.x, cy - c.location.y) for c in world.cams)
        if dcam < 3.8 and rng.random() < 0.45:
            continue
        w = weights(dr, dw, dk, dp, dl, dcam)
        mains = rng.uniform(0.9, 1.0)
        for m_i in range(n):
            a = rng.uniform(0, 2 * math.pi)
            rr = rad * math.sqrt(rng.uniform(0.02, 1.0)) if m_i else 0.0
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            if world.mask_at(x, y) > 0.4 or not world.free(x, y, 0.04, zmin=-0.06):
                continue
            z = world.ground_z(x, y)
            q = int(rng.choice(nW, p=w))
            _, _, _, smin, smax = VARIANTS[q]
            s = smin + (smax - smin) * rng.beta(1.6, 1.7)
            if m_i:
                s *= rng.uniform(0.62, 0.95)               # clump hierarchy: the first tuft is the biggest
                s = max(s, smin * 0.8)
            X.append(x)
            Y.append(y)
            Z.append(z)
            PK.append(q)
            SC.append(s)
            RT.append(rng.uniform(0, 2 * math.pi))
    if verbose:
        print('G6 tufts: placed', len(X), 'tufts in', n_ok, 'clumps (of', len(clumps), 'raw centres)')
    return dict(x=np.array(X), y=np.array(Y), z=np.array(Z), pick=np.array(PK, dtype=np.int32), scale=np.array(SC, dtype=np.float32),
                rot=np.array(RT, dtype=np.float32))
