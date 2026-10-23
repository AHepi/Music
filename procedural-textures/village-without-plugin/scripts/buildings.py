"""Parametric cottage and stable generators (numpy meshes, multi-material)."""
import math
import numpy as np
from common import *

# material slot indices shared by all building meshes
CM = dict(plaster=0, timber=1, stone=2, roof=3, roofdark=4, glass=5, iron=6, plank=7, mortar=8, shingle=9, straw=10, bark=11, rope=12, sack=13, clay=14, muck=15, rock=16, leather=17)
CM_NAMES = ['Plaster', 'Timber', 'Stone', 'Thatch', 'ThatchDark', 'WindowGlass', 'Iron', 'Planks', 'Mortar', 'Shingle', 'Straw', 'Bark', 'Rope', 'Sack', 'Clay', 'Muck', 'Rock', 'Leather']

CORNERS = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], dtype=np.float64)
FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5)]
FAXES = [(0, 1), (0, 1), (0, 2), (0, 2), (1, 2), (1, 2)]

# ---------------------------------------------------------------------------- stone work
def stone_block(mb, c, size, R, rng, mat, rough=0.07):
    h = np.asarray(size, float) / 2.0
    cor = CORNERS * h * (1.0 + rough * (rng.rand(8, 3) * 2 - 1))
    P4 = np.zeros((6, 4, 3)); UV = np.zeros((6, 4, 2))
    off = rng.rand(2) * 30
    for fi, (f, (a, b)) in enumerate(zip(FACES, FAXES)):
        P4[fi] = cor[list(f)]
        UV[fi, :, 0] = P4[fi][:, a] + off[0]
        UV[fi, :, 1] = P4[fi][:, b] + off[1]
    P4 = P4 @ np.asarray(R, float).T + np.asarray(c, float)
    mb.quads_hard(P4, UV, mat, False, rnd=rng.rand())

def stone_course(mb, p0, p1, z, h, t, rng, mat, jitter=0.025, lmin=0.30, lmax=0.66, out_n=None, skip=None):
    """Row of rough blocks along the 2D segment p0->p1 (outer face on the segment, depth t inwards).
    skip: optional function(a, b, za, zb, pos_xy_center) -> (keep, new_a, new_b) not used here (clipping done by caller)."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    dn = d / L
    if out_n is None:
        out_n = np.array([dn[1], -dn[0]])
    yaw = math.atan2(dn[1], dn[0])
    R = rotz(yaw)
    pos = 0.0
    while pos < L - 0.05:
        l = rng.uniform(lmin, lmax)
        if L - (pos + l) < lmin * 0.7:
            l = L - pos
        hh = h * rng.uniform(0.86, 1.08)
        tt = t * rng.uniform(0.86, 1.05)
        a, b = pos, pos + l
        if skip is not None:
            ok, a, b = skip(a, b, z, z + h)
            if not ok:
                pos += l
                continue
        cpos = p0 + dn * ((a + b) / 2) - out_n * (tt / 2 - rng.uniform(-jitter, jitter))
        yoff = rng.uniform(-0.012, 0.012)
        stone_block(mb, (cpos[0], cpos[1], z + hh / 2 + yoff), (b - a - 0.015, tt, hh), R @ rotz(rng.uniform(-0.03, 0.03)), rng, mat)
        pos += l

def rect_courses(mb, hx, hy, z0, z1, t, rng, mat, ch=0.21, jitter=0.025, skips=None):
    """Stone courses around the rectangle (outer faces at +-hx, +-hy). skips: dict side -> factory(along0) -> skip fn."""
    n = max(1, int(round((z1 - z0) / ch)))
    h = (z1 - z0) / n
    sk = skips or {}

    def mk(side, along0):
        f = sk.get(side)
        return f(along0) if f else None

    for c in range(n):
        z = z0 + c * h
        fb = 0.0 if c % 2 == 0 else t
        lr = t if c % 2 == 0 else 0.0
        stone_course(mb, (-hx + fb, -hy), (hx - fb, -hy), z, h, t, rng, mat, jitter, out_n=np.array([0.0, -1.0]), skip=mk('F', -hx + fb))
        stone_course(mb, (-hx + fb, hy), (hx - fb, hy), z, h, t, rng, mat, jitter, out_n=np.array([0.0, 1.0]), skip=mk('B', -hx + fb))
        stone_course(mb, (hx, -hy + lr), (hx, hy - lr), z, h, t, rng, mat, jitter, out_n=np.array([1.0, 0.0]), skip=mk('R', -hy + lr))
        stone_course(mb, (-hx, -hy + lr), (-hx, hy - lr), z, h, t, rng, mat, jitter, out_n=np.array([-1.0, 0.0]), skip=mk('L', -hy + lr))

def opening_skipper(openings, along0, margin=0.03):
    """openings: list of (a, b, za, zb) in wall coordinates; along0 = coordinate of the segment start along the wall."""
    def f(a, b, za, zb):
        a += along0; b += along0
        zc = 0.5 * (za + zb)
        for (oa, ob, oza, ozb) in openings:
            if zc > oza - 0.02 and zc < ozb + 0.02:
                if b <= oa - margin or a >= ob + margin:
                    continue
                if a >= oa - margin and b <= ob + margin:
                    return False, a - along0, b - along0
                if a < oa - margin and b > oa - margin:
                    b = oa - margin
                if b > ob + margin and a < ob + margin:
                    a = ob + margin
                if b - a < 0.12:
                    return False, a - along0, b - along0
        return True, a - along0, b - along0
    return f

# ---------------------------------------------------------------------------- wall pieces
def wall_rects(x0, x1, z0, z1, openings):
    xs = sorted(set([x0, x1] + [o[0] for o in openings] + [o[1] for o in openings]))
    rects = []
    for a, b in zip(xs[:-1], xs[1:]):
        if b - a < 1e-4:
            continue
        col = [o for o in openings if o[0] <= a + 1e-6 and o[1] >= b - 1e-6]
        if not col:
            rects.append((a, b, z0, z1))
        else:
            cur = z0
            for o in sorted(col, key=lambda o: o[2]):
                if o[2] > cur + 1e-4:
                    rects.append((a, b, cur, o[2]))
                cur = max(cur, o[3])
            if cur < z1 - 1e-4:
                rects.append((a, b, cur, z1))
    return rects

def wbox(mb, side, W, D, a, b, za, zb, t, mat, d_out=0.0, uvoff=None, grain=None):
    if side == 'F':
        c = (0.5 * (a + b), -D / 2 + t / 2 - d_out, 0.5 * (za + zb)); s = (b - a, t, zb - za)
    elif side == 'B':
        c = (0.5 * (a + b), D / 2 - t / 2 + d_out, 0.5 * (za + zb)); s = (b - a, t, zb - za)
    elif side == 'L':
        c = (-W / 2 + t / 2 - d_out, 0.5 * (a + b), 0.5 * (za + zb)); s = (t, b - a, zb - za)
    else:
        c = (W / 2 - t / 2 + d_out, 0.5 * (a + b), 0.5 * (za + zb)); s = (t, b - a, zb - za)
    if uvoff is None:
        uvoff = (mb.rng.rand() * 20, 0.0) if mat == CM['plaster'] else None
    mb.box(c, s, None, mat, uvoff=uvoff, grain=grain)

def beam(mb, p0, p1, w, h, mat, up=(0, 0, 1), uvoff=None):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    if L < 1e-6:
        return
    z = d / L
    x = np.cross(np.asarray(up, float), z)
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.stack([x, y, z], axis=1)
    mb.box((p0 + p1) / 2, (w, h, L), R, mat, uvoff=uvoff, grain=2)

def wall_point(side, W, D, u, z, off=0.0):
    """3D point on wall `side` at horizontal coordinate u and height z, pushed `off` outwards."""
    if side == 'F':
        return np.array([u, -D / 2 - off, z])
    if side == 'B':
        return np.array([u, D / 2 + off, z])
    if side == 'L':
        return np.array([-W / 2 - off, u, z])
    return np.array([W / 2 + off, u, z])

def side_rot(side):
    return {'F': 0.0, 'B': math.pi, 'L': -math.pi / 2, 'R': math.pi / 2}[side]

# ---------------------------------------------------------------------------- roofs
def thatch_roof(mb, W, D, wall_h, pitch_deg, ov_e, ov_g, T0, seed=0):
    th = math.radians(pitch_deg)
    tn, cs, sn = math.tan(th), math.cos(th), math.sin(th)
    a = D / 2 + ov_e
    ze = wall_h - ov_e * tn
    zr = wall_h + (D / 2) * tn
    Lx = W / 2 + ov_g
    nx = max(8, int(round(2 * Lx / 0.30)))
    xs = np.linspace(-Lx, Lx, nx + 1)
    nt = 14
    ts = np.linspace(0, 1, nt)
    dF = np.array([cs, sn]); nF = np.array([-sn, cs])
    dB = np.array([-cs, sn]); nB = np.array([sn, cs])

    def profile(x):
        T = T0 * (1.0 + 0.16 * perlin2(x * 0.9, 3.3 + seed) + 0.08 * perlin2(x * 3.1, 8.1 + seed))
        eave_shift = 0.05 * perlin2(x * 2.2, 1.7 + seed)
        front = []
        for t in ts:
            base = np.array([-a, ze]) + dF * (t * (a / cs))
            Tt = T * (1.0 + 0.10 * math.cos(math.pi * t) - 0.18 * t)
            bump = 0.025 * perlin2(x * 2.5 + 11.0, t * 4.0 + seed)
            front.append(base + nF * (Tt + bump))
        Tn = T * 1.10
        base0 = np.array([-a, ze]) + np.array([eave_shift * 0.5, -abs(eave_shift) * 0.4])
        C = base0 + nF * (Tn / 2)
        nose = [C + (Tn / 2) * (math.cos(ph) * nF - math.sin(ph) * dF * 1.3) for ph in np.linspace(0, math.pi, 7)[1:-1]]
        top_front = [base0] + nose[::-1] + front
        pf = front[-1]
        pb = np.array([-pf[0], pf[1]])
        ctrl = np.array([0.0, zr + T / cs + 0.30 + 0.05 * perlin2(x * 1.4, 5.5 + seed)])
        ridge = [(1 - u) ** 2 * pf + 2 * u * (1 - u) * ctrl + u * u * pb for u in np.linspace(0, 1, 7)[1:-1]]
        back = []
        for tt in ts[::-1]:
            base = np.array([a, ze]) + dB * (tt * (a / cs))
            Tt = T * (1.0 + 0.10 * math.cos(math.pi * tt) - 0.18 * tt)
            bump = 0.025 * perlin2(x * 2.5 + 41.0, tt * 4.0 + seed + 7)
            back.append(base + nB * (Tt + bump))
        base0b = np.array([a, ze]) + np.array([-eave_shift * 0.5, -abs(eave_shift) * 0.4])
        Cb = base0b + nB * (Tn / 2)
        noseb = [Cb + (Tn / 2) * (math.cos(ph) * nB - math.sin(ph) * dB * 1.3) for ph in np.linspace(0, math.pi, 7)[1:-1]]
        top = top_front + ridge + back + noseb + [base0b]
        under = [base0b, np.array([a * 0.5, ze + (a * 0.5 / cs) * sn]), np.array([0.0, zr]),
                 np.array([-a * 0.5, ze + (a * 0.5 / cs) * sn]), base0]
        return np.array(top), np.array(under)

    tops = []; unders = []
    for x in xs:
        tp, un = profile(x)
        tops.append(tp); unders.append(un)
    tops = np.array(tops); unders = np.array(unders)
    M = tops.shape[1]

    def to3(arr2):
        P = np.zeros((arr2.shape[0], arr2.shape[1], 3))
        P[:, :, 0] = xs[:, None]
        P[:, :, 1] = arr2[:, :, 0]
        P[:, :, 2] = arr2[:, :, 1]
        return P

    PT = to3(tops); PU = to3(unders)
    seg = np.linalg.norm(np.diff(tops[0], axis=0), axis=1)
    vv = np.concatenate([[0.0], np.cumsum(seg)])
    UVt = np.zeros((len(xs), M, 2)); UVt[:, :, 0] = (xs + W)[:, None]; UVt[:, :, 1] = vv[None, :]
    i, j = 1, M // 3
    nrm = np.cross(PT[i + 1, j] - PT[i, j], PT[i, j + 1] - PT[i, j])
    out = PT[i, j] - np.array([PT[i, j, 0], 0.0, wall_h])
    mb.grid(PT, UVt, CM['roof'], True, flip=bool(np.dot(nrm, out) < 0))
    UVu = np.zeros((len(xs), 5, 2)); UVu[:, :, 0] = xs[:, None]; UVu[:, :, 1] = np.array([0.0, 1.0, 2.0, 3.0, 4.0])[None, :]
    nrm = np.cross(PU[1 + 1, 1] - PU[1, 1], PU[1, 2] - PU[1, 1])
    mb.grid(PU, UVu, CM['roofdark'], False, flip=bool(nrm[2] > 0))
    for k, sgn in ((0, -1), (len(xs) - 1, 1)):
        ring = np.vstack([PT[k], PU[k][1:-1]])
        area = 0.5 * np.sum(ring[:, 1] * np.roll(ring[:, 2], -1) - np.roll(ring[:, 1], -1) * ring[:, 2])
        flip = (area < 0) if sgn > 0 else (area > 0)
        mb.polygon_fan(ring, CM['roof'], flip=bool(flip), smooth=False)
    return zr

def roof_pt(side, s, x, a, ze, th):
    """point on the roof surface: s metres up the slope from the eave, x along the ridge"""
    cs, sn = math.cos(th), math.sin(th)
    if side < 0:
        return np.array([x, -a + s * cs, ze + s * sn]), np.array([0.0, -sn, cs]), np.array([0.0, cs, sn])
    return np.array([x, a - s * cs, ze + s * sn]), np.array([0.0, sn, cs]), np.array([0.0, -cs, sn])

def shingle_roof(mb, W, D, wall_h, pitch_deg, ov_e, ov_g, rng, row_pitch=0.165, shw=(0.11, 0.19), shl=0.34, mat=None):
    mat = CM['shingle'] if mat is None else mat
    th = math.radians(pitch_deg)
    tn, cs, sn = math.tan(th), math.cos(th), math.sin(th)
    a = D / 2 + ov_e
    ze = wall_h - ov_e * tn
    zr = wall_h + (D / 2) * tn
    Lx = W / 2 + ov_g
    slope_len = a / cs
    nrows = int(slope_len / row_pitch)
    thk = 0.016
    for side in (-1, 1):
        for r in range(nrows):
            s0 = r * row_pitch
            x = -Lx + rng.uniform(0, 0.1)
            while x < Lx - 0.02:
                w = rng.uniform(*shw)
                xe = min(x + w, Lx)
                wd = xe - x - 0.006
                if wd < 0.03:
                    x = xe
                    continue
                lift = rng.uniform(0.003, 0.03) + 0.004 * (r % 3)
                length = shl * rng.uniform(0.92, 1.05)
                s1 = min(s0 + length, slope_len)
                sk = rng.uniform(-0.012, 0.012)
                p_ll, n_, d_ = roof_pt(side, s0, x, a, ze, th)
                p_lr, _, _ = roof_pt(side, s0, x + wd, a, ze, th)
                p_ur, _, _ = roof_pt(side, s1, x + wd + sk, a, ze, th)
                p_ul, _, _ = roof_pt(side, s1, x + sk, a, ze, th)
                P = np.array([p_ll + n_ * (lift + thk), p_lr + n_ * (lift + thk), p_ur + n_ * 0.004, p_ul + n_ * 0.004])
                nrm = np.cross(P[1] - P[0], P[2] - P[1])
                if np.dot(nrm, n_) < 0:
                    P = P[::-1]
                uv = np.array([[0.0, 0.0], [wd, 0.0], [wd, length], [0.0, length]]) + rng.rand(2) * 10
                rr = rng.rand()
                mb.quads_hard(P[None], uv[None], mat, False, rnd=rr)
                # lower edge (the visible thickness)
                E = np.array([p_ll + n_ * (lift + thk), p_lr + n_ * (lift + thk), p_lr + n_ * lift, p_ll + n_ * lift])
                nrm = np.cross(E[1] - E[0], E[2] - E[1])
                if np.dot(nrm, -d_) < 0:
                    E = E[::-1]
                mb.quads_hard(E[None], None, mat, False, rnd=rr)
                x = xe
    # dark roof deck (hides gaps between shingles)
    for side in (-1, 1):
        y_e = -a if side < 0 else a
        P = np.array([[[-Lx, y_e, ze - 0.012], [Lx, y_e, ze - 0.012]], [[-Lx, 0.0, zr - 0.012], [Lx, 0.0, zr - 0.012]]])
        mb.grid(P, None, CM['roofdark'], False, flip=False)
        mb.grid(P, None, CM['roofdark'], False, flip=True)
    # ridge cap boards
    for side in (-1, 1):
        R = rotx(th) if side < 0 else rotx(math.pi - th)
        w = 0.26
        up = np.array([0.0, cs, sn]) if side < 0 else np.array([0.0, -cs, sn])
        nrm = np.array([0.0, -sn, cs]) if side < 0 else np.array([0.0, sn, cs])
        cen = np.array([0.0, 0.0, zr]) - up * (w / 2 - 0.03) + nrm * 0.03
        mb.box(cen, (2 * Lx + 0.06, w, 0.028), R, CM['plank'], grain=0)
    # rafter tails and a fascia board along the eaves
    for side in (-1, 1):
        y_e = -a if side < 0 else a
        k = int(2 * Lx / 0.62)
        for i in range(k + 1):
            x = -Lx + 0.1 + i * (2 * Lx - 0.2) / max(k, 1)
            mb.box((x, y_e + (0.05 if side < 0 else -0.05), ze - 0.07), (0.06, 0.16, 0.08), None, CM['timber'])
    return zr

# ---------------------------------------------------------------------------- small assemblies
def door_assembly(mb, side, W, D, u, z0, rng, wt, open_w=0.96, open_h=1.92, ajar=0.0, mat_plank=None):
    """Door leaf, frame, strap hinges and threshold on wall `side`; built in local coordinates and rotated."""
    mat_plank = CM['plank'] if mat_plank is None else mat_plank
    sub = MB(); sub.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    # local: wall plane at y=0, outward = -y, door centred at x=0, floor at z=0
    n_pl = 5
    pw = open_w / n_pl
    leaf_y = 0.10
    hinge_x = -open_w / 2
    for i in range(n_pl):
        x0 = hinge_x + i * pw
        h = open_h - 0.04 + rng.uniform(-0.01, 0.01)
        sub.box((x0 + pw / 2, leaf_y, 0.02 + h / 2), (pw - 0.012, 0.045, h), None, mat_plank, grain=2)
    # ledges (visible through gaps) and iron straps
    for zz in (0.35, open_h - 0.38):
        sub.box((0, leaf_y + 0.04, zz), (open_w - 0.04, 0.03, 0.12), None, CM['plank'], grain=0)
        sub.box((-open_w * 0.18, leaf_y - 0.03, zz), (open_w * 0.62, 0.012, 0.075), None, CM['iron'], grain=0)
        sub.box((hinge_x + 0.03, leaf_y - 0.03, zz), (0.07, 0.016, 0.1), None, CM['iron'], grain=2)
    # ring handle / latch
    sub.box((open_w * 0.34, leaf_y - 0.045, open_h * 0.5), (0.03, 0.02, 0.18), None, CM['iron'], grain=2)
    sub.box((open_w * 0.34, leaf_y - 0.045, open_h * 0.5 + 0.11), (0.14, 0.02, 0.025), None, CM['iron'], grain=0)
    # frame: jambs + lintel
    fd = 0.16
    sub.box((-open_w / 2 - 0.07, -0.0, open_h / 2), (0.14, fd, open_h), None, CM['timber'], grain=2)
    sub.box((open_w / 2 + 0.07, -0.0, open_h / 2), (0.14, fd, open_h), None, CM['timber'], grain=2)
    sub.box((0, -0.0, open_h + 0.1), (open_w + 0.48, fd + 0.04, 0.2), None, CM['timber'], grain=0)
    # threshold
    sub.box((0, -0.15, 0.02), (open_w + 0.3, 0.5, 0.06), None, CM['stone'])
    # rotate/translate to the wall
    if ajar != 0.0:
        pass
    R = rotz(side_rot(side))
    P0 = wall_point(side, W, D, u, z0)
    mb.extend(sub, R, P0)

def window_assembly(mb, side, W, D, u, zc, rng, wt, ww=0.76, wh=0.78, shutters=True, open_deg=(160, 150)):
    sub = MB(); sub.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    gy = 0.11
    # glass (dark, slightly reflective) and lead-lines frame
    P = np.array([[[-ww / 2, gy, zc - wh / 2], [ww / 2, gy, zc - wh / 2], [ww / 2, gy, zc + wh / 2], [-ww / 2, gy, zc + wh / 2]]])
    sub.quads_hard(P[:, [0, 3, 2, 1]], np.array([[[0, 0], [0, wh], [ww, wh], [ww, 0]]]), CM['glass'], False)
    # inner dark box (room behind)
    sub.box((0, gy + 0.12, zc), (ww, 0.2, wh), None, CM['mortar'])
    # frame
    ft = 0.07
    sub.box((0, 0.0, zc + wh / 2 + ft / 2 + 0.01), (ww + 2 * ft + 0.1, 0.17, ft + 0.04), None, CM['timber'], grain=0)
    sub.box((0, -0.055, zc - wh / 2 - ft / 2), (ww + 2 * ft + 0.2, 0.26, ft + 0.02), None, CM['timber'], grain=0)
    sub.box((-ww / 2 - ft / 2, 0.0, zc), (ft, 0.17, wh), None, CM['timber'], grain=2)
    sub.box((ww / 2 + ft / 2, 0.0, zc), (ft, 0.17, wh), None, CM['timber'], grain=2)
    # mullions
    sub.box((0, 0.06, zc), (0.035, 0.05, wh), None, CM['timber'], grain=2)
    sub.box((0, 0.06, zc + wh * 0.08), (ww, 0.05, 0.035), None, CM['timber'], grain=0)
    # shutters, hinged on the jambs; they swing outwards and end up (nearly) flat against the wall
    if shutters:
        for k, sg in enumerate((-1, 1)):
            sh = MB(); sh.rng = np.random.RandomState(int(rng.randint(1 << 30)))
            sw = ww / 2 + 0.01
            for i in range(3):
                sh.box((-sg * sw / 2 + (i - 1) * (sw / 3), 0.0, zc), (sw / 3 - 0.01, 0.03, wh + 0.04), None, CM['plank'], grain=2)
            sh.box((-sg * sw / 2, 0.025, zc + wh * 0.3), (sw, 0.02, 0.08), None, CM['plank'], grain=0)
            sh.box((-sg * sw / 2, 0.025, zc - wh * 0.3), (sw, 0.02, 0.08), None, CM['plank'], grain=0)
            beta = math.radians(open_deg[k] + rng.uniform(-8, 8))
            sh.xform_since((0, 0, 0), rotz(beta if sg > 0 else -beta), (sg * (ww / 2 + ft), -0.075, 0.0))
            sub.extend(sh)
    R = rotz(side_rot(side))
    P0 = wall_point(side, W, D, u, 0.0)
    mb.extend(sub, R, P0)

def chimney(mb, cx, cy, hx, hy, z0, z1, rng, t=0.26):
    sub = MB(); sub.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    sub.box((0, 0, (z0 + z1) / 2), (2 * hx - 0.1, 2 * hy - 0.1, z1 - z0), None, CM['mortar'])
    rect_courses(sub, hx, hy, z0, z1, t, rng, CM['stone'], ch=0.22, jitter=0.02)
    # cap slab and pot
    sub.box((0, 0, z1 + 0.05), (2 * hx + 0.18, 2 * hy + 0.18, 0.1), None, CM['stone'])
    sub.box((0, 0, z1 + 0.14), (2 * hx - 0.12, 2 * hy - 0.12, 0.08), None, CM['stone'])
    sub.lathe([(0.2, 0.0), (0.2, 0.2), (0.16, 0.42), (0.17, 0.48), (0.21, 0.5)], sides=12, mat=CM['roofdark'], smooth=True)
    sub.xform_since((len(sub.V) - 1, 0, 0), None, (0, 0, z1 + 0.18))
    mb.extend(sub, None, (cx, cy, 0.0))

def plank_wall(mb, side, W, D, a, b, za, zb, t, rng, gap=0.012, pw=0.2, mat=None, batten=True):
    """vertical board-and-batten wall segment"""
    mat = CM['plank'] if mat is None else mat
    n = max(1, int(round((b - a) / pw)))
    w = (b - a) / n
    for i in range(n):
        jitter = rng.uniform(-0.02, 0.02)
        wbox(mb, side, W, D, a + i * w, a + (i + 1) * w - gap, za + max(jitter, 0) * 0, zb + jitter * 0.5, t, mat, uvoff=(rng.rand() * 20, rng.rand() * 20), grain=2)


# ---------------------------------------------------------------------------- the cottage
def tri_prism(mb, side, W, D, ya, yb, ypk, z0, z1, t, mat, rng):
    """gable triangle on side L/R: base from ya..yb at z0, apex at (ypk, z1); thickness t inwards from the outer plane"""
    sgn = -1.0 if side == 'L' else 1.0
    xo = sgn * W / 2
    xi = xo - sgn * t
    tri = np.array([[ya, z0], [yb, z0], [ypk, z1]])
    # outer face, inner face, three sides
    Po = np.array([[xo, p[0], p[1]] for p in tri])
    Pi = np.array([[xi, p[0], p[1]] for p in tri])
    uv = np.array([[p[0], p[1]] for p in tri]) + rng.rand(2) * 5
    if sgn < 0:
        mb.tris_hard(Po[None][:, [0, 2, 1]], uv[None][:, [0, 2, 1]], mat, False)
        mb.tris_hard(Pi[None], uv[None], mat, False)
    else:
        mb.tris_hard(Po[None], uv[None], mat, False)
        mb.tris_hard(Pi[None][:, [0, 2, 1]], uv[None][:, [0, 2, 1]], mat, False)
    for (i, j) in ((0, 1), (1, 2), (2, 0)):
        q = np.array([Po[i], Po[j], Pi[j], Pi[i]])
        n = np.cross(q[1] - q[0], q[2] - q[1])
        c = q.mean(axis=0) - np.array([xo - sgn * t / 2, 0.5 * (ya + yb), z0 + 0.3 * (z1 - z0)])
        if np.dot(n, c) < 0:
            q = q[::-1]
        mb.quads_hard(q[None], None, mat, False)

def cottage(seed, W=7.0, D=4.8, wall_h=2.75, style='timber', roof='thatch', pitch=46.0, door_x=0.0, win_x=(-2.2, 2.0),
            chim=1, shutters=True, ph=0.42, back_win=(-1.4, 1.6), side_win=True):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = np.random.RandomState(seed + 1000)
    hx, hy = W / 2, D / 2
    wt = 0.26 if style == 'timber' else 0.42
    th = math.radians(pitch)
    # ---- foundation
    mb.box((0, 0, (ph - 0.25) / 2), (W - 0.06, D - 0.06, ph + 0.25), None, CM['mortar'])
    rect_courses(mb, hx + 0.04, hy + 0.04, -0.22, ph, 0.30, rng, CM['stone'], ch=0.21)
    # ---- openings (wall coordinates: x for F/B, y for L/R)
    door_w, door_h = 0.96, 1.86
    op = {'F': [(door_x - door_w / 2, door_x + door_w / 2, ph, ph + door_h)], 'B': [], 'L': [], 'R': []}
    win_w, win_h, win_z = 0.82, 0.92, ph + 1.0
    for wx in win_x:
        op['F'].append((wx - win_w / 2 - 0.07, wx + win_w / 2 + 0.07, win_z - 0.08, win_z + win_h + 0.08))
    for bx in back_win:
        op['B'].append((bx - win_w / 2 - 0.07, bx + win_w / 2 + 0.07, win_z - 0.08, win_z + win_h + 0.08))
    side_win_sides = []
    if side_win:
        sd = 'L' if chim > 0 else 'R'
        op[sd].append((-0.33, 0.33, win_z - 0.02, win_z + 0.62))
        side_win_sides.append(sd)
    # ---- walls
    if style == 'timber':
        for side in ('F', 'B'):
            for (a, b, za, zb) in wall_rects(-hx, hx, ph, wall_h, op[side]):
                wbox(mb, side, W, D, a, b, za, zb, wt, CM['plaster'])
        for side in ('L', 'R'):
            for (a, b, za, zb) in wall_rects(-hy + wt, hy - wt, ph, wall_h, op[side]):
                wbox(mb, side, W, D, a, b, za, zb, wt, CM['plaster'])
    else:
        for side in ('F', 'B'):
            for (a, b, za, zb) in wall_rects(-hx, hx, ph, wall_h, op[side]):
                wbox(mb, side, W, D, a, b, za, zb, wt, CM['mortar'])
        for side in ('L', 'R'):
            for (a, b, za, zb) in wall_rects(-hy + wt, hy - wt, ph, wall_h, op[side]):
                wbox(mb, side, W, D, a, b, za, zb, wt, CM['mortar'])
        skips = {s_: (lambda along0, s_=s_: opening_skipper(op[s_], along0)) for s_ in 'FBLR'}
        rect_courses(mb, hx + 0.015, hy + 0.015, ph, wall_h, 0.22, rng, CM['stone'], ch=0.22, jitter=0.02, skips=skips)
    # ---- timber frame (plaster cottages) / lintels (stone cottages)
    ztp = wall_h - 0.20
    if style == 'timber':
        for side in ('F', 'B'):
            L_ = op[side]
            for (a, b, za, zb) in wall_rects(-hx - 0.02, hx + 0.02, ph, ph + 0.20, [o for o in L_ if o[2] <= ph + 0.01]):
                wbox(mb, side, W, D, a, b, za, zb, 0.14, CM['timber'], d_out=0.06, grain=0)
            for (a, b, za, zb) in wall_rects(-hx - 0.02, hx + 0.02, ph + 0.80, ph + 0.92, [o for o in L_ if o[2] < ph + 0.92 - 1e-3 and o[3] > ph + 0.80]):
                wbox(mb, side, W, D, a, b, za, zb, 0.13, CM['timber'], d_out=0.055, grain=0)
            wbox(mb, side, W, D, -hx - 0.02, hx + 0.02, ztp, wall_h, 0.15, CM['timber'], d_out=0.06, grain=0)
            # studs
            nst = int(W / 0.95)
            for i in range(1, nst):
                x = -hx + i * W / nst
                if any(o[0] - 0.12 < x < o[1] + 0.12 for o in L_):
                    continue
                wbox(mb, side, W, D, x - 0.07, x + 0.07, ph + 0.20, ztp, 0.12, CM['timber'], d_out=0.05, grain=2)
            # a few studs under the windows
            # braces from the corner posts
            for sg in (-1, 1):
                x0 = sg * (hx - 0.1); x1 = sg * (hx - 1.05)
                if not any((min(x0, x1) - 0.1) < o[1] and (max(x0, x1) + 0.1) > o[0] and o[2] < ph + 1.6 for o in L_):
                    p0 = wall_point(side, W, D, x0, ph + 0.2, 0.0); p1 = wall_point(side, W, D, x1, ph + 0.88, 0.0)
                    beam(mb, p0, p1, 0.12, 0.12, CM['timber'])
                    p2 = wall_point(side, W, D, x0, ztp, 0.0); p3 = wall_point(side, W, D, x1, ph + 1.1, 0.0)
                    if not any((min(x0, x1) - 0.1) < o[1] and (max(x0, x1) + 0.1) > o[0] and o[3] > ph + 1.05 for o in L_):
                        beam(mb, p2, p3, 0.12, 0.12, CM['timber'])
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box((sx * (hx - 0.01), sy * (hy - 0.01), (ph + wall_h + 0.1) / 2), (0.23, 0.23, wall_h + 0.1 - ph), None, CM['timber'], grain=2)
        for side in ('L', 'R'):
            wbox(mb, side, W, D, -hy, hy, ztp, wall_h, 0.15, CM['timber'], d_out=0.06, grain=0)
            wbox(mb, side, W, D, -hy, hy, ph, ph + 0.20, 0.14, CM['timber'], d_out=0.06, grain=0)
    else:
        for side in ('F', 'B', 'L', 'R'):
            for o in op[side]:
                wbox(mb, side, W, D, o[0] - 0.14, o[1] + 0.14, o[3], o[3] + 0.17, 0.30, CM['timber'], d_out=0.03, grain=0)
                if o[2] > ph + 0.5:
                    wbox(mb, side, W, D, o[0] - 0.1, o[1] + 0.1, o[2] - 0.08, o[2], 0.3, CM['stone'], d_out=0.06, grain=0)
    # ---- gable ends
    zr_geo = wall_h + hy * math.tan(th)
    for side in ('L', 'R'):
        if style == 'timber':
            tri_prism(mb, side, W, D, -hy, hy, 0.0, wall_h, zr_geo - 0.02, 0.22, CM['plaster'], rng)
            sg = -1.0 if side == 'L' else 1.0
            xo = sg * (hx + 0.05)
            beam(mb, (xo, -hy, wall_h), (xo, 0.0, zr_geo - 0.04), 0.11, 0.13, CM['timber'])
            beam(mb, (xo, hy, wall_h), (xo, 0.0, zr_geo - 0.04), 0.11, 0.13, CM['timber'])
            beam(mb, (xo, 0.0, wall_h), (xo, 0.0, zr_geo - 0.1), 0.12, 0.13, CM['timber'])
            beam(mb, (xo, -hy * 0.5, wall_h + hy * 0.5 * math.tan(th)), (xo, hy * 0.5, wall_h + hy * 0.5 * math.tan(th)), 0.1, 0.12, CM['timber'])
            beam(mb, (xo, -hy * 0.55, wall_h), (xo, -0.05, wall_h + 0.62), 0.08, 0.1, CM['timber'])
            beam(mb, (xo, hy * 0.55, wall_h), (xo, 0.05, wall_h + 0.62), 0.08, 0.1, CM['timber'])
        else:
            tri_prism(mb, side, W, D, -hy, hy, 0.0, wall_h, zr_geo - 0.02, 0.2, CM['plank'], rng)
    # ---- windows and door
    door_assembly(mb, 'F', W, D, door_x, ph, rng, wt, door_w, door_h)
    for wx in win_x:
        window_assembly(mb, 'F', W, D, wx, win_z + win_h / 2, rng, wt, win_w, win_h, shutters, (165, 120) if (wx == win_x[-1] and seed % 2 == 0) else (160, 158))
    for bx in back_win:
        window_assembly(mb, 'B', W, D, bx, win_z + win_h / 2, rng, wt, win_w, win_h, shutters, (150, 160))
    for sd in side_win_sides:
        window_assembly(mb, sd, W, D, 0.0, win_z + 0.3, rng, wt, 0.6, 0.6, False, (160, 160))
    # ---- door steps
    stone_block(mb, (door_x, -hy - 0.31, 0.2), (1.35, 0.52, 0.4), np.eye(3), rng, CM['stone'], rough=0.04)
    stone_block(mb, (door_x + rng.uniform(-0.1, 0.1), -hy - 0.82, 0.1), (1.7, 0.62, 0.2), rotz(rng.uniform(-0.05, 0.05)), rng, CM['stone'], rough=0.05)
    # ---- roof
    if roof == 'thatch':
        zr = thatch_roof(mb, W, D, wall_h, pitch, 0.45, 0.40, 0.38, seed=seed)
    else:
        zr = shingle_roof(mb, W, D, wall_h, pitch, 0.5, 0.32, rng)
    # ---- chimney on the gable
    cx = chim * (hx + 0.36)
    chimney(mb, cx, 0.0, 0.42, 0.56, -0.22, zr + 0.45, rng)
    return mb, dict(zr=zr, W=W, D=D, wall_h=wall_h, ph=ph)


# ---------------------------------------------------------------------------- the stable
def boards_along(mb, p0, p1, normal2, z0, z1, rng, mat=None, w=0.20, gap=0.012, th=0.04, skip_prob=0.0, uneven=0.03, skip=None, top_fn=None):
    """Vertical boards standing along the 2D line p0->p1; normal2 = outward 2D normal (boards sit inside the line)."""
    mat = CM['plank'] if mat is None else mat
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    dn = d / L
    yaw = math.atan2(dn[1], dn[0])
    n = max(1, int(round(L / w)))
    bw = L / n
    for i in range(n):
        if rng.rand() < skip_prob:
            continue
        a, b = i * bw, (i + 1) * bw
        if skip is not None and skip(a, b):
            continue
        ztop = z1 + rng.uniform(-uneven, uneven)
        if top_fn is not None:
            ztop = top_fn((a + b) / 2) + rng.uniform(-uneven, uneven)
        zb = z0 + rng.uniform(0.0, 0.015)
        if ztop - zb < 0.05:
            continue
        c2 = p0 + dn * ((a + b) / 2) - np.asarray(normal2) * (th / 2 + rng.uniform(0, 0.012))
        mb.box((c2[0], c2[1], (zb + ztop) / 2), (bw - gap, th, ztop - zb), rotz(yaw + rng.uniform(-0.012, 0.012)), mat, grain=2)

def plank_leaf(mb, x_hinge, y, z0, z1, w, dirx, beta_deg, rng, mat=None):
    mat = CM['plank'] if mat is None else mat
    sub = MB(); sub.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    n = max(3, int(round(w / 0.19)))
    bw = w / n
    for i in range(n):
        x0 = dirx * (i * bw + bw / 2)
        j = rng.uniform(-0.012, 0.012)
        sub.box((x0, 0.0, (z0 + z1) / 2), (bw - 0.012, 0.04, z1 - z0 + j), None, mat, grain=2)
    for zz in (z0 + 0.2, z1 - 0.2):
        sub.box((dirx * w / 2, 0.038, zz), (w - 0.03, 0.025, 0.13), None, mat, grain=0)
    beam(sub, (dirx * 0.08, 0.045, z0 + 0.2), (dirx * (w - 0.08), 0.045, z1 - 0.2), 0.11, 0.025, mat)
    for zz in (z0 + 0.3, z1 - 0.3):
        sub.box((dirx * w * 0.36, -0.026, zz), (w * 0.72, 0.012, 0.065), None, CM['iron'], grain=0)
    sub.box((dirx * (w - 0.1), -0.03, (z0 + z1) / 2), (0.03, 0.02, 0.2), None, CM['iron'], grain=2)
    beta = math.radians(beta_deg)
    alpha = -beta if dirx > 0 else beta
    mb.extend(sub, rotz(alpha), (x_hinge, y, 0.0))

def straw_litter(mb, rng, x0, x1, y0, y1, n, z=0.02, mat=None, length=(0.15, 0.4), lift=0.04):
    mat = CM['straw'] if mat is None else mat
    c = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)], axis=1)
    ang = rng.uniform(0, math.pi, n)
    ln = rng.uniform(*length, n)
    hz = z + rng.uniform(0, lift, n)
    wdt = 0.006 + 0.004 * rng.rand(n)
    d = np.stack([np.cos(ang), np.sin(ang)], axis=1)
    pn = np.stack([-d[:, 1], d[:, 0]], axis=1)
    P = np.zeros((n, 4, 3))
    for k, (a, b) in enumerate(((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))):
        P[:, k, 0] = c[:, 0] + d[:, 0] * ln * a + pn[:, 0] * wdt * b
        P[:, k, 1] = c[:, 1] + d[:, 1] * ln * a + pn[:, 1] * wdt * b
        P[:, k, 2] = hz + (0.02 * rng.rand(n) if k in (1, 2) else 0.0)
    uv = np.zeros((n, 4, 2)); uv[:, 1, 0] = ln; uv[:, 2, 0] = ln; uv[:, 2, 1] = wdt; uv[:, 3, 1] = wdt
    mb.quads_hard(P, uv, mat, False)

def manger(mb, cx, cy, rng):
    w, d, h = 0.95, 0.5, 0.34
    z = 0.62
    mb.box((cx, cy, z + 0.02), (w, d, 0.04), None, CM['plank'], grain=0)
    mb.box((cx, cy - d / 2 + 0.02, z + h / 2), (w, 0.04, h), None, CM['plank'], grain=0)
    mb.box((cx, cy + d / 2 - 0.02, z + h / 2), (w, 0.04, h), None, CM['plank'], grain=0)
    mb.box((cx - w / 2 + 0.02, cy, z + h / 2), (0.04, d, h), None, CM['plank'], grain=1)
    mb.box((cx + w / 2 - 0.02, cy, z + h / 2), (0.04, d, h), None, CM['plank'], grain=1)
    for sx in (-1, 1):
        mb.box((cx + sx * (w / 2 - 0.06), cy, z / 2), (0.08, 0.08, z), None, CM['timber'], grain=2)
    mb.box((cx, cy - d / 2 - 0.02, z + h - 0.01), (w + 0.04, 0.06, 0.04), None, CM['timber'], grain=0)

def hay_rack(mb, cx, cy_wall, rng, z=1.45):
    w, h, d = 0.95, 0.55, 0.3
    for i in range(8):
        x = cx - w / 2 + (i + 0.5) * w / 8
        # slanted slats
        beam(mb, (x, cy_wall - 0.04, z), (x, cy_wall - d, z + h), 0.03, 0.03, CM['plank'])
    mb.box((cx, cy_wall - 0.03, z + h * 0.5), (w + 0.1, 0.05, 0.06), None, CM['timber'], grain=0)
    mb.box((cx, cy_wall - d, z + h), (w + 0.06, 0.05, 0.05), None, CM['timber'], grain=0)
    mb.box((cx, cy_wall - 0.03, z), (w + 0.06, 0.06, 0.05), None, CM['timber'], grain=0)

def bucket_mesh(mb, c, rng, tip=0.0, mat_w=None, h=0.3, r=0.17):
    sub = MB(); sub.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    sub.lathe([(r * 0.82, 0.0), (r * 0.84, 0.02), (r, h), (r * 1.02, h + 0.01)], sides=14, mat=CM['plank'], smooth=True, cap_bottom=True)
    for zz in (0.07, h - 0.05):
        sub.lathe([(r * (0.82 + (zz / h) * 0.18) + 0.004, zz - 0.012), (r * (0.82 + (zz / h) * 0.18) + 0.012, zz), (r * (0.82 + (zz / h) * 0.18) + 0.004, zz + 0.012)], sides=14, mat=CM['iron'], smooth=False)
    mb.extend(sub, rotx(tip), c)

def stable(seed, L=12.0, D=6.0, wall_h=2.9, pitch=34.0, bays=4):
    rng = np.random.RandomState(seed)
    mb = MB(); mb.rng = np.random.RandomState(seed + 500)
    hx, hy = L / 2, D / 2
    th = math.radians(pitch); tn = math.tan(th)
    bw = L / bays
    px = [-hx + 0.14 + i * (L - 0.28) / bays for i in range(bays + 1)]
    # ---- plinth (stone) around back and sides, and in front between the door bays
    openings_F = [(px[i] + 0.16, px[i + 1] - 0.16, -0.3, 0.6) for i in range(bays)]
    skips = {'F': (lambda along0: opening_skipper(openings_F, along0))}
    mb.box((0, 0, 0.08), (L - 0.04, D - 0.04, 0.5), None, CM['mortar'])
    rect_courses(mb, hx + 0.03, hy + 0.03, -0.2, 0.34, 0.30, rng, CM['stone'], ch=0.18, skips=skips)
    # ---- frame
    for sx_i, x in enumerate(px):
        for y in (-hy + 0.14, hy - 0.14):
            mb.box((x, y, wall_h / 2), (0.24, 0.24, wall_h), None, CM['timber'], grain=2)
    for y in (-hy + 0.14, hy - 0.14):
        mb.box((0, y, wall_h - 0.12), (L + 0.1, 0.22, 0.26), None, CM['timber'], grain=0)
        mb.box((0, y, 0.12), (L + 0.06, 0.2, 0.24), None, CM['timber'], grain=0)
    for x in px:
        mb.box((x, 0, wall_h - 0.12), (0.2, D - 0.2, 0.26), None, CM['timber'], grain=1)
    for x in (-hx + 0.08, hx - 0.08):
        mb.box((x, 0, 0.12), (0.2, D - 0.1, 0.24), None, CM['timber'], grain=1)
    # ---- back wall: boards with a couple of gaps
    boards_along(mb, (-hx, hy), (hx, hy), (0, 1), 0.3, wall_h, rng, skip_prob=0.025)
    # side walls: boards up to eaves; gable above
    rg = hy * tn
    for sgn in (-1, 1):
        xo = sgn * hx
        for (p0, p1) in (((xo, -hy), (xo, hy)),):
            nrm = (sgn, 0)
            def top_fn(t, rg=rg):
                return wall_h
            # eaves-height boards
            if sgn < 0:
                skip_loft = lambda a, b: False
            boards_along(mb, p0, p1, nrm, 0.3, wall_h, rng, skip_prob=0.02)
            # gable boards follow the roof line
            def gtop(t, hy=hy, tn=tn):
                return wall_h + (hy - abs(t - hy)) * tn - 0.07
            if sgn < 0:
                # loft door opening (centre of the west gable)
                def skip_loft(a, b, hy=hy):
                    yc = (a + b) / 2 - hy
                    return abs(yc) < 0.52
                boards_along(mb, p0, p1, nrm, wall_h + 0.01, wall_h + 3.0, rng, skip=skip_loft, top_fn=gtop, w=0.2)
                # short boards above and below the loft door
                for (zb, zt) in ((wall_h + 0.01, wall_h + 0.28), (wall_h + 1.62, None)):
                    for yc in np.arange(-0.5, 0.5, 0.2) + 0.1:
                        top = gtop(yc + hy) if zt is None else zt
                        if top - zb > 0.06:
                            mb.box((xo - nrm[0] * 0.02, yc, (zb + top) / 2), (0.04, 0.188, top - zb), None, CM['plank'], grain=2)
                # loft door frame + dark loft behind + open leaves
                mb.box((xo + 0.1, 0, wall_h + 0.9), (0.2, 1.04, 1.34), None, CM['roofdark'])
                for sy in (-1, 1):
                    mb.box((xo - 0.03, sy * 0.56, wall_h + 0.95), (0.1, 0.1, 1.5), None, CM['timber'], grain=2)
                mb.box((xo - 0.03, 0, wall_h + 1.65), (0.1, 1.2, 0.12), None, CM['timber'], grain=1)
                mb.box((xo - 0.05, 0, wall_h + 0.22), (0.12, 1.2, 0.12), None, CM['timber'], grain=1)
            else:
                boards_along(mb, p0, p1, nrm, wall_h + 0.01, wall_h + 3.0, rng, top_fn=gtop, w=0.2)
    # barge boards and a hoist beam on the west gable
    for sy in (-1, 1):
        ang = th
        beam(mb, (-hx - 0.05, sy * (hy + 0.55), wall_h - 0.55 * tn), (-hx - 0.05, 0.0, wall_h + hy * tn + 0.02), 0.04, 0.22, CM['plank'], up=(1, 0, 0))
    hoist_z = wall_h + hy * tn + 0.05
    mb.box((-hx - 0.7, 0, hoist_z - 0.2), (1.8, 0.16, 0.18), None, CM['timber'], grain=0)
    beam(mb, (-hx - 1.45, 0, hoist_z - 0.2), (-hx - 0.4, 0, hoist_z - 0.85), 0.1, 0.12, CM['timber'], up=(0, 1, 0))
    mb.lathe([(0.001, -0.03), (0.11, -0.03), (0.11, 0.03), (0.001, 0.03)], sides=14, mat=CM['iron'], smooth=False)
    mb.xform_since((len(mb.V) - 1, 0, 0), rotx(math.pi / 2), (-hx - 1.35, 0, hoist_z - 0.34))
    mb.tube([(-hx - 1.35, 0.0, hoist_z - 0.42), (-hx - 1.33, 0.02, hoist_z - 1.8), (-hx - 1.3, 0.03, hoist_z - 3.1)], 0.016, sides=6, mat=CM['straw'], smooth=True)
    mb.tube([(-hx - 1.3, 0.03, hoist_z - 3.1), (-hx - 1.3, 0.03, hoist_z - 3.25), (-hx - 1.22, 0.03, hoist_z - 3.38), (-hx - 1.15, 0.03, hoist_z - 3.3)], 0.018, sides=6, mat=CM['iron'], smooth=True)
    # ---- front: lintels, upper boards, door bays
    zl = 2.3
    for i in range(bays):
        a, b = px[i] + 0.12, px[i + 1] - 0.12
        mb.box(((a + b) / 2, -hy + 0.1, zl + 0.1), (b - a + 0.1, 0.2, 0.2), None, CM['timber'], grain=0)
    boards_along(mb, (-hx, -hy), (hx, -hy), (0, -1), zl + 0.2, wall_h - 0.02, rng, top_fn=lambda t: wall_h - 0.02, skip_prob=0.015)
    # braces
    for i in range(bays):
        for sg in (-1, 1):
            xa = px[i] + 0.12 if sg > 0 else px[i + 1] - 0.12
            beam(mb, (xa, -hy - 0.0, zl + 0.2), (xa + sg * 0.55, -hy - 0.0, zl + 0.2 + 0.0) if False else (xa + sg * 0.5, -hy, zl - 0.35), 0.1, 0.1, CM['timber'])
    # door leaves: bay 0 wide open, bay 1 lower shut/upper open, bay 2 ajar, bay 3 lower shut/upper hanging
    y0 = -hy + 0.03
    zf0, zf1, zmid, ztop = 0.14, 1.2, 1.24, zl - 0.04
    for i in range(bays):
        a, b = px[i] + 0.12, px[i + 1] - 0.12
        w = (b - a) / 2
        if i == 0:
            plank_leaf(mb, a, y0, zf0, ztop, w, +1, 98, rng)
            plank_leaf(mb, b, y0, zf0, ztop, w, -1, 104, rng)
        elif i == 1:
            plank_leaf(mb, a, y0, zf0, zf1, w, +1, 0, rng); plank_leaf(mb, b, y0, zf0, zf1, w, -1, 0, rng)
            plank_leaf(mb, a, y0, zmid, ztop, w, +1, 96, rng); plank_leaf(mb, b, y0, zmid, ztop, w, -1, 100, rng)
        elif i == 2:
            plank_leaf(mb, a, y0, zf0, ztop, w, +1, 0, rng); plank_leaf(mb, b, y0, zf0, ztop, w, -1, 36, rng)
        else:
            plank_leaf(mb, a, y0, zf0, zf1, w, +1, 0, rng); plank_leaf(mb, b, y0, zf0, zf1, w, -1, 0, rng)
            plank_leaf(mb, a, y0, zmid, ztop, w, +1, 0, rng); plank_leaf(mb, b, y0, zmid, ztop, w, -1, 128, rng)
    # ---- interior: partitions, mangers, racks, loft floor, straw, a tipped bucket
    for i in range(1, bays):
        x = px[i]
        boards_along(mb, (x, -hy + 0.3), (x, hy - 0.3), (1, 0), 0.0, 1.55, rng, th=0.04, uneven=0.02)
        mb.box((x, 0, 1.58), (0.08, D - 0.5, 0.06), None, CM['timber'], grain=1)
    for i in range(bays):
        cx = 0.5 * (px[i] + px[i + 1])
        manger(mb, cx, hy - 0.45, rng)
        hay_rack(mb, cx, hy - 0.2, rng)
        straw_litter(mb, rng, px[i] + 0.3, px[i + 1] - 0.3, -hy + 0.4, hy - 0.4, 260)
        straw_litter(mb, rng, px[i] + 0.3, px[i + 1] - 0.3, -hy + 0.4, hy - 0.4, 40, z=0.03, length=(0.4, 0.7))
    # loft floor and joists
    zf = wall_h - 0.3
    for x in px:
        pass
    for k in range(int(L / 0.24)):
        x = -hx + 0.12 + k * 0.24
        if abs(x) < 0.6:
            continue
        mb.box((x, 0, zf + 0.02), (0.22, D - 0.2, 0.04), None, CM['plank'], grain=1)
    # bucket on its side and a loose board
    bucket_mesh(mb, (px[2] + 0.9, -hy + 1.4, 0.17), rng, tip=math.pi / 2 * 0.95)
    bucket_mesh(mb, (px[0] + 0.9, hy - 1.0, 0.0), rng, tip=0.0)
    # ---- roof
    zr = shingle_roof(mb, L, D, wall_h, pitch, 0.95, 0.45, rng, row_pitch=0.17, shl=0.36)
    # ---- hitching rail in front
    yr = -hy - 2.2
    for x in (-3.8, 0.2, 4.0):
        mb.box((x, yr, 0.65), (0.16, 0.16, 1.3), None, CM['timber'], grain=2)
    mb.tube([(-4.1, yr, 1.12), (-1.0, yr + 0.01, 1.11), (2.0, yr - 0.01, 1.12), (4.3, yr, 1.1)], 0.055, sides=8, mat=CM['timber'], smooth=True, cap0=True, cap1=True)
    mb.tube([(-3.8, yr - 0.1, 1.12), (-3.8, yr - 0.16, 0.95), (-3.76, yr - 0.1, 0.9)], 0.01, sides=5, mat=CM['straw'], smooth=True)
    return mb, dict(zr=zr, L=L, D=D, wall_h=wall_h)
