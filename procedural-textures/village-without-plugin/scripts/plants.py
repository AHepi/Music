"""Procedural plants: deciduous trees, conifers, bushes, ferns, grass tufts (all numpy meshes)."""
import math
import numpy as np
from common import *

PM = dict(bark=0, leaf=1, needle=2, birchbark=3, grass=4, fern=5, leafbirch=6, leafdry=7, flower=8)
PM_NAMES = ['Bark', 'Leaf', 'Needles', 'BarkBirch', 'Grass', 'Fern', 'LeafBirch', 'LeafDry', 'Flower']

def unit(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)

def add_leaves(mb, c, a, n, size, wratio, mat, rnd, hgt=None, kite=0.45):
    """kite-shaped leaves. c: (N,3) base points, a: (N,3) leaf axis, n: (N,3) preferred normal."""
    N = len(c)
    if N == 0:
        return
    a = unit(a)
    n = n - a * np.sum(n * a, axis=1, keepdims=True)
    n = unit(n)
    b = np.cross(n, a)
    size = np.broadcast_to(np.asarray(size, float), (N,))
    W = size * wratio
    B = c
    L = c + a * (kite * size)[:, None] - b * (0.5 * W)[:, None] + n * (0.05 * size)[:, None]
    T = c + a * size[:, None] + n * (0.10 * size)[:, None]
    R = c + a * (kite * size)[:, None] + b * (0.5 * W)[:, None] + n * (0.05 * size)[:, None]
    P4 = np.stack([B, L, T, R], axis=1)
    uv = np.broadcast_to(np.array([[0.5, 0.0], [0.0, kite], [0.5, 1.0], [1.0, kite]]), (N, 4, 2))
    at = dict(rnd=np.asarray(rnd, float))
    if hgt is not None:
        at['hgt'] = np.asarray(hgt, float)
    mb.quads_hard(P4, uv, mat, True, **at)

def branch_path(rng, p0, d0, length, n, bend, up, grav):
    pts = [np.asarray(p0, float)]
    d = unit(d0)
    ds = length / n
    for i in range(n):
        d = d + rng.normal(0, bend, 3) * np.array([1.0, 1.0, 0.6]) + np.array([0, 0, up]) - np.array([0, 0, grav * (i / n)])
        d = unit(d)
        pts.append(pts[-1] + d * ds)
    return np.array(pts)

def taper(n, r0, r1, power=0.8):
    t = np.linspace(0, 1, n + 1)
    return r0 + (r1 - r0) * t ** power

def rot_about(v, axis, ang):
    axis = unit(axis)
    return v * math.cos(ang) + np.cross(axis, v) * math.sin(ang) + axis * np.dot(axis, v) * (1 - math.cos(ang))

def deciduous(seed, H=12.0, spread=1.0, trunk_r=0.34, trunk_frac=0.38, elev=(0.35, 0.95), leaf_size=(0.26, 0.38), clusters=3,
              leaves_per=70, n_limbs=7, birch=False, bare=0.0, lean=0.0):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    bark_m = PM['birchbark'] if birch else PM['bark']
    leaf_m = PM['leafbirch'] if birch else PM['leaf']
    lean_d = np.array([rng.normal(0, lean), rng.normal(0, lean), 1.0])
    th = H * trunk_frac
    trunk = branch_path(rng, (0, 0, -0.2), lean_d, th + 0.2, 12, 0.025, 0.0, 0.0)
    tr_r = taper(12, trunk_r, trunk_r * 0.5, 0.9)
    mb.tube(trunk, tr_r, sides=9, mat=bark_m, cap1=True)
    # roots
    for k in range(0 if birch else 5):
        az = 2 * math.pi * k / 5 + rng.uniform(-0.3, 0.3)
        d = np.array([math.cos(az), math.sin(az), 0])
        p0 = d * trunk_r * 0.4 + np.array([0, 0, 0.6])
        p1 = d * (trunk_r + 0.5) + np.array([0, 0, 0.12])
        p2 = d * (trunk_r + 1.1) + np.array([0, 0, -0.15])
        mb.tube([p0, p1, p2], [trunk_r * 0.45, trunk_r * 0.25, trunk_r * 0.08], sides=6, mat=bark_m, cap1=True)
    leaf_c, leaf_a, leaf_n, leaf_s, leaf_r, leaf_h = [], [], [], [], [], []

    def add_cluster(center, count, radius, hz):
        pos = center + rng.normal(0, 1, (count, 3)) * np.array([radius, radius, radius * 0.7])
        a = rng.normal(0, 1, (count, 3)); a[:, 2] = a[:, 2] * 0.5 + 0.15
        nrm = np.zeros((count, 3)); nrm[:, 2] = 1.0
        nrm += rng.normal(0, 0.45, (count, 3))
        leaf_c.append(pos); leaf_a.append(a); leaf_n.append(nrm)
        leaf_s.append(rng.uniform(*leaf_size, count))
        leaf_r.append(rng.rand(count))
        leaf_h.append(np.full(count, hz))

    golden = 2.39996
    for k in range(n_limbs):
        t = rng.uniform(0.45, 1.0)
        i_t = t * 12
        i0 = int(min(i_t, 11)); f = i_t - i0
        base = trunk[i0] * (1 - f) + trunk[i0 + 1] * f
        r_here = tr_r[i0] * (1 - f) + tr_r[i0 + 1] * f
        az = k * golden + rng.uniform(-0.4, 0.4)
        e = rng.uniform(*elev)
        d = np.array([math.cos(az) * math.cos(e), math.sin(az) * math.cos(e), math.sin(e)])
        L1 = H * spread * rng.uniform(0.38, 0.55) * (1.15 - 0.55 * t)
        n1 = 9
        limb = branch_path(rng, base, d, L1, n1, 0.10, 0.07, 0.10)
        rl = taper(n1, r_here * rng.uniform(0.42, 0.58), r_here * 0.1, 0.9)
        mb.tube(limb, rl, sides=6, mat=bark_m, cap1=True)
        n2 = rng.randint(4, 7)
        for j in range(n2):
            s = rng.uniform(0.25, 0.95)
            ii = int(min(s * n1, n1 - 1)); ff = s * n1 - ii
            p = limb[ii] * (1 - ff) + limb[ii + 1] * ff
            dl = unit(limb[min(ii + 1, n1)] - limb[ii])
            perp = unit(np.cross(dl, rng.normal(0, 1, 3)))
            d2 = rot_about(dl, perp, rng.uniform(0.5, 1.0))
            d2[2] += 0.15
            L2 = L1 * rng.uniform(0.28, 0.5) * (1.1 - 0.6 * s)
            n2s = 6
            sec = branch_path(rng, p, d2, L2, n2s, 0.12, 0.06, 0.07)
            r2 = taper(n2s, max(rl[ii] * 0.55, 0.02), 0.008, 0.9)
            mb.tube(sec, r2, sides=5, mat=bark_m, cap1=True)
            hz = (sec[-1][2]) / H
            if rng.rand() > bare:
                for q in range(clusters):
                    sidx = n2s if q == 0 else int(n2s * rng.uniform(0.5, 0.9))
                    add_cluster(sec[sidx], leaves_per, 0.55 * spread ** 0.3, hz)
            n3 = rng.randint(2, 4)
            for m_ in range(n3):
                s3 = rng.uniform(0.3, 1.0)
                i3 = int(min(s3 * n2s, n2s - 1)); f3 = s3 * n2s - i3
                p3 = sec[i3] * (1 - f3) + sec[i3 + 1] * f3
                dd = unit(sec[min(i3 + 1, n2s)] - sec[i3])
                perp3 = unit(np.cross(dd, rng.normal(0, 1, 3)))
                d3 = rot_about(dd, perp3, rng.uniform(0.5, 1.1))
                d3[2] += 0.1
                L3 = rng.uniform(0.5, 1.1)
                tw = branch_path(rng, p3, d3, L3, 4, 0.15, 0.05, 0.1)
                mb.tube(tw, taper(4, 0.014, 0.004, 1.0), sides=4, mat=bark_m, cap1=True)
                if rng.rand() > bare:
                    add_cluster(tw[-1], leaves_per, 0.5, hz)
                    add_cluster(tw[2], leaves_per // 2, 0.42, hz)
    if leaf_c:
        C = np.concatenate(leaf_c); A = np.concatenate(leaf_a); Nn = np.concatenate(leaf_n)
        S = np.concatenate(leaf_s); R = np.concatenate(leaf_r); Hh = np.concatenate(leaf_h)
        add_leaves(mb, C, A, Nn, S, 0.62 if not birch else 0.7, leaf_m, R, Hh)
    return mb

def bush(seed, r=1.0, leaves=900, leaf_size=(0.07, 0.11), birch=False):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    C = []; A = []; Nn = []
    for k in range(9):
        az = rng.uniform(0, 6.28)
        e = rng.uniform(0.5, 1.2)
        d = np.array([math.cos(az) * math.cos(e), math.sin(az) * math.cos(e), math.sin(e)])
        L = r * rng.uniform(0.9, 1.5)
        pts = branch_path(rng, (0, 0, 0), d, L, 5, 0.12, 0.03, 0.12)
        mb.tube(pts, taper(5, 0.025, 0.005), sides=4, mat=PM['bark'], cap1=True)
        for s in np.linspace(0.3, 1.0, 5):
            p = pts[int(s * 5) if s < 1 else 5]
            cnt = leaves // 45
            pos = p + rng.normal(0, r * 0.16, (cnt, 3))
            C.append(pos)
            A.append(rng.normal(0, 1, (cnt, 3)))
            n_ = np.zeros((cnt, 3)); n_[:, 2] = 1
            Nn.append(n_ + rng.normal(0, 0.5, (cnt, 3)))
    C = np.concatenate(C); A = np.concatenate(A); Nn = np.concatenate(Nn)
    add_leaves(mb, C, A, Nn, rng.uniform(*leaf_size, len(C)), 0.6, PM['leaf'], rng.rand(len(C)), np.full(len(C), 0.2))
    return mb

def fern(seed, fronds=9, length=0.8):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    C = []; A = []; Nn = []; S = []
    for k in range(fronds):
        az = 2 * math.pi * k / fronds + rng.uniform(-0.2, 0.2)
        d0 = np.array([math.cos(az), math.sin(az), 0.0])
        Lf = length * rng.uniform(0.65, 1.1)
        pts = []
        up0 = rng.uniform(0.9, 1.5)
        for i in range(11):
            s = i / 10.0
            pts.append(d0 * (Lf * s * 0.75) + np.array([0, 0, up0 * Lf * (math.sin(s * 1.6) * 0.55)]) - np.array([0, 0, 0.5 * Lf * s ** 2]) + np.array([0, 0, 0.05]))
        pts = np.array(pts)
        mb.tube(pts, taper(10, 0.007, 0.0015), sides=3, mat=PM['fern'], cap1=True)
        side = unit(np.cross(d0, np.array([0, 0, 1.0])))
        for i in range(1, 11):
            s = i / 10.0
            pl = Lf * 0.36 * (1.0 - s) ** 0.8 + 0.03
            tdir = unit(pts[min(i + 1, 10)] - pts[i - 1])
            for sg in (-1, 1):
                a = unit(side * sg * 0.9 + tdir * 0.45 + np.array([0, 0, 0.15]))
                C.append(pts[i][None]); A.append(a[None]); S.append(pl)
                Nn.append(np.array([[0, 0, 1.0]]))
    C = np.concatenate(C); A = np.concatenate(A); Nn = np.concatenate(Nn); S = np.array(S)
    add_leaves(mb, C, A, Nn, S, 0.22, PM['fern'], rng.rand(len(C)), np.zeros(len(C)), kite=0.5)
    return mb

def grass_tuft(seed, blades=10, height=0.3, spread=0.07, width=0.013):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    rows = np.array([0.0, 0.4, 0.75])
    hw = np.array([0.5, 0.46, 0.3]) * width
    for b in range(blades):
        ang = rng.uniform(0, 6.28)
        off = rng.uniform(0, spread)
        base = np.array([math.cos(ang) * off, math.sin(ang) * off, -0.012])
        h = height * rng.uniform(0.55, 1.15)
        lean_a = ang + rng.normal(0, 0.5)
        lean = rng.uniform(0.05, 0.55) * h
        face = rng.uniform(0, 3.14)
        side = np.array([math.cos(face), math.sin(face), 0.0])
        ld = np.array([math.cos(lean_a), math.sin(lean_a), 0.0])
        def pt(s):
            return base + np.array([0, 0, h * s * (1 - 0.15 * s)]) + ld * lean * s ** 2.0
        pts = np.array([pt(s) for s in rows])
        tip_pt = pt(1.0)
        left = pts - side * hw[:, None]
        right = pts + side * hw[:, None]
        rnd = rng.rand()
        V = np.vstack([left, right, tip_pt[None]])
        tipv = np.array([0.0, 0.4, 0.75, 0.0, 0.4, 0.75, 1.0])
        i0 = mb.verts(V, rnd=rnd, tip=tipv)
        q = np.array([[0, 3, 4, 1], [1, 4, 5, 2]]) + i0
        uvq = np.array([[[0, 0], [1, 0], [1, 0.4], [0, 0.4]], [[0, 0.4], [1, 0.4], [1, 0.75], [0, 0.75]]], float)
        mb.quads(q, uvq, PM['grass'], True)
        mb.tris(np.array([[2, 5, 6]]) + i0, np.array([[[0, 0.75], [1, 0.75], [0.5, 1.0]]], float), PM['grass'], True)
    return mb


def ribbon(mb, pts, w_side, w_up, mat, droop=0.35, uscale=1.0, rnd=0.0):
    """Frond ribbon along a branch: rows of (left, spine, right); returns nothing."""
    n = len(pts)
    T = np.zeros_like(pts)
    T[1:-1] = pts[2:] - pts[:-2]; T[0] = pts[1] - pts[0]; T[-1] = pts[-1] - pts[-2]
    T = unit(T)
    side = unit(np.cross(T, np.array([0, 0, 1.0])))
    sp = pts + np.array([0, 0, 1.0]) * (w_up[:, None] * 0.0)
    Lp = pts - side * w_side[:, None] + np.array([0, 0, -droop]) * w_side[:, None]
    Rp = pts + side * w_side[:, None] + np.array([0, 0, -droop]) * w_side[:, None]
    # three columns
    G = np.stack([Lp, pts + np.array([0, 0, 1.0]) * w_up[:, None], Rp], axis=1)      # (n,3,3)
    u = np.linspace(0, 1, n)
    UV = np.zeros((n, 3, 2)); UV[:, :, 0] = u[:, None] * uscale; UV[:, 0, 1] = 0.0; UV[:, 1, 1] = 0.5; UV[:, 2, 1] = 1.0
    mb.grid(G, UV, mat, True, flip=False, rnd=rnd)

def spruce(seed, H=15.0, lowest=0.16, Lmax=0.2, dense=1.0):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    lean = np.array([rng.normal(0, 0.012), rng.normal(0, 0.012), 1.0])
    tr = branch_path(rng, (0, 0, -0.2), lean, H + 0.2, 14, 0.01, 0.0, 0.0)
    mb.tube(tr, taper(14, 0.30 * H / 15.0, 0.012, 1.25), sides=8, mat=PM['bark'], cap1=True)
    z = lowest * H
    k = 0
    while z < H - 0.6:
        t = (z - lowest * H) / (H * (1 - lowest))
        nb = int(rng.randint(5, 8))
        az0 = rng.uniform(0, 6.28)
        for b in range(nb):
            az = az0 + 2 * math.pi * b / nb + rng.uniform(-0.3, 0.3)
            Lb = H * Lmax * (1.0 - t) ** 0.85 * rng.uniform(0.8, 1.15) + 0.35
            d = np.array([math.cos(az), math.sin(az), 0.0])
            base = tr[min(int((z + 0.2) / (H + 0.2) * 14), 14)] + np.array([0, 0, 0])
            base = np.array([base[0], base[1], z])
            n = 8
            ss = np.linspace(0, 1, n + 1)
            droop = 0.28 + 0.3 * (1 - t)
            pts = np.stack([base[0] + d[0] * Lb * ss, base[1] + d[1] * Lb * ss, base[2] - droop * Lb * ss ** 1.6 + 0.35 * Lb * np.maximum(ss - 0.65, 0) ** 2 * 2], axis=1)
            mb.tube(pts, taper(n, 0.035 * (1 - t) + 0.01, 0.006, 1.0), sides=4, mat=PM['bark'], cap1=True)
            wm = np.maximum(Lb * 0.30 * np.sin(np.pi * (0.06 + 0.9 * ss)) ** 0.8, 0.03) * dense
            ribbon(mb, pts, wm, wm * 0.45, PM['needle'], droop=0.55, rnd=rng.rand())
            ribbon(mb, pts + np.array([0, 0, 0.05]), wm * 0.8, wm * 0.8, PM['needle'], droop=-0.2, rnd=rng.rand())
        z += rng.uniform(0.62, 0.9) * (H / 15.0)
        k += 1
    # top leader tuft
    for q in range(4):
        az = q * 1.57 + rng.uniform(0, 0.6)
        d = np.array([math.cos(az) * 0.35, math.sin(az) * 0.35, 0.55])
        pts = np.array([[0, 0, H - 0.8], [d[0] * 0.5, d[1] * 0.5, H - 0.8 + 0.3], [d[0], d[1], H - 0.8 + 0.7], [d[0] * 1.3, d[1] * 1.3, H - 0.8 + 1.1]])
        ribbon(mb, pts, np.array([0.2, 0.18, 0.12, 0.03]), np.array([0.1, 0.1, 0.08, 0.02]), PM['needle'], droop=0.2, rnd=rng.rand())
    return mb

def pine(seed, H=17.0, crown=0.38):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    lean = np.array([rng.normal(0, 0.05), rng.normal(0, 0.05), 1.0])
    tr = branch_path(rng, (0, 0, -0.2), lean, H + 0.2, 16, 0.03, 0.0, 0.0)
    mb.tube(tr, taper(16, 0.26 * H / 17.0, 0.04, 1.0), sides=8, mat=PM['bark'], cap1=True)
    z0 = H * (1 - crown)
    nb = 9
    for b in range(nb):
        t = rng.uniform(0.0, 1.0)
        zb = z0 + t * (H - z0 - 1.0)
        i = min(int((zb + 0.2) / (H + 0.2) * 16), 15)
        base = tr[i]
        az = b * 2.39996 + rng.uniform(-0.3, 0.3)
        e = rng.uniform(0.25, 0.8)
        d = np.array([math.cos(az) * math.cos(e), math.sin(az) * math.cos(e), math.sin(e)])
        Lb = (H * 0.22) * (1.2 - 0.7 * t) * rng.uniform(0.8, 1.1)
        n = 8
        pts = branch_path(rng, base, d, Lb, n, 0.1, 0.05, 0.12)
        mb.tube(pts, taper(n, 0.11 * (1.1 - t * 0.5), 0.015, 0.9), sides=5, mat=PM['bark'], cap1=True)
        for s in (0.55, 0.8, 1.0):
            ii = min(int(s * n), n)
            p = pts[ii]
            for q in range(5):
                ang = rng.uniform(0, 6.28)
                el = rng.uniform(-0.2, 0.9)
                dd = np.array([math.cos(ang) * math.cos(el), math.sin(ang) * math.cos(el), math.sin(el)])
                ln = rng.uniform(0.7, 1.2) * (0.8 if s < 1 else 1.0)
                rr = np.stack([p + dd * ln * ss + np.array([0, 0, -0.18 * ln * ss ** 2]) for ss in np.linspace(0, 1, 5)])
                wm = np.array([0.02, 0.2, 0.26, 0.15, 0.01]) * ln
                ribbon(mb, rr, wm, wm * 0.5, PM['needle'], droop=0.2, rnd=rng.rand())
    return mb

def dead_tree(seed, H=8.0):
    mb = deciduous(seed, H=H, spread=0.8, trunk_r=0.28, trunk_frac=0.55, elev=(0.2, 0.9), n_limbs=5, bare=1.0, lean=0.04)
    return mb


def flower_tuft(seed, stems=3, height=0.3, spread=0.06):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = rng
    for k in range(stems):
        ang = rng.uniform(0, 6.28); off = rng.uniform(0, spread)
        base = np.array([math.cos(ang) * off, math.sin(ang) * off, -0.01])
        h = height * rng.uniform(0.7, 1.2)
        lean_a = rng.uniform(0, 6.28); lean = rng.uniform(0.02, 0.12) * h
        top = base + np.array([math.cos(lean_a) * lean, math.sin(lean_a) * lean, h])
        mid = (base + top) / 2 + np.array([math.cos(lean_a) * lean * 0.2, math.sin(lean_a) * lean * 0.2, 0])
        mb.tube(np.array([base, mid, top]), [0.0025, 0.002, 0.0015], sides=3, mat=PM['grass'], cap1=True, rnd=0.1, tip=0.3)
        n = 5
        C = np.repeat(top[None], n, axis=0)
        a = np.array([[math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), 0.25] for i in range(n)])
        nn = np.zeros((n, 3)); nn[:, 2] = 1.0
        rnd = rng.rand()
        add_leaves(mb, C, a, nn, 0.035, 0.7, PM['flower'], np.full(n, rnd), None)
        add_leaves(mb, top[None] + np.array([[0, 0, 0.003]]), np.array([[1, 0, 0.0]]), np.array([[0, 0, 1.0]]), 0.012, 1.0, PM['flower'], np.array([0.99]), None)
        # two small leaves at the base
        for q in range(2):
            aa = rng.uniform(0, 6.28)
            add_leaves(mb, base[None], np.array([[math.cos(aa), math.sin(aa), 0.5]]), np.array([[0, 0, 1.0]]), 0.09, 0.5, PM['grass'] if False else PM['leaf'], np.array([rng.rand()]), np.array([0.1]))
    return mb
