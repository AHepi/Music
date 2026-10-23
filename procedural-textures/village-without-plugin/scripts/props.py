"""Mediaeval props: every function returns an MB (local coordinates, ground at z=0)."""
import math
import numpy as np
from common import *
from buildings import CM, stone_block, beam, straw_litter, bucket_mesh, rect_courses

def _mb(rng):
    mb = MB()
    mb.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    return mb

def barrel(rng, r=0.33, h=0.92):
    mb = _mb(rng)
    rad = lambda t: r * (0.78 + 0.22 * math.sin(math.pi * min(max(t, 0), 1)))
    ts = np.linspace(0, 1, 9)
    prof = [(0.001, 0.0), (rad(0) * 0.96, 0.0)] + [(rad(t), h * t) for t in ts] + [(rad(1) - 0.025, h), (rad(1) - 0.025, h - 0.05), (0.001, h - 0.05)]
    mb.lathe(prof, sides=18, mat=CM['plank'], smooth=False, swap_uv=True)
    for t in (0.07, 0.27, 0.73, 0.93):
        R = rad(t) + 0.006
        z = h * t
        mb.lathe([(R - 0.004, z - 0.022), (R + 0.006, z - 0.018), (R + 0.006, z + 0.018), (R - 0.004, z + 0.022)], sides=18, mat=CM['iron'], smooth=False)
    return mb

def crate(rng, w=0.7, d=0.55, h=0.5):
    mb = _mb(rng)
    t = 0.03
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * (w / 2 - 0.03), sy * (d / 2 - 0.03), h / 2), (0.06, 0.06, h), None, CM['timber'], grain=2)
    nb = 3
    bh = (h - 0.04) / nb
    for k in range(nb):
        z = 0.03 + k * bh + bh / 2
        for sy in (-1, 1):
            mb.box((0, sy * (d / 2 - t / 2), z), (w - 0.1, t, bh - 0.012), None, CM['plank'], grain=0)
        for sx in (-1, 1):
            mb.box((sx * (w / 2 - t / 2), 0, z), (t, d - 0.1, bh - 0.012), None, CM['plank'], grain=1)
    for k in range(4):
        x = -w / 2 + 0.1 + k * (w - 0.2) / 3
        mb.box((x, 0, h - 0.01), (0.15, d - 0.02, t), None, CM['plank'], grain=1)
    return mb

def sack(rng, h=0.8, r=0.27, tied=True):
    mb = _mb(rng)
    prof = [(0.001, 0.0), (r * 0.8, 0.0), (r, 0.12 * h), (r * 1.02, 0.35 * h), (r * 0.9, 0.58 * h), (r * 0.55, 0.78 * h), (r * 0.2 if tied else r * 0.45, 0.9 * h), (r * 0.13, 0.93 * h),
            (r * 0.3, 0.99 * h), (r * 0.12, 1.03 * h), (0.001, 1.01 * h)]
    seed = int(rng.randint(1000))
    mb.lathe(prof, sides=16, mat=CM['sack'], smooth=True,
             wobble=lambda th, z: 1.0 + 0.10 * perlin2(th * 1.6 + seed, z * 3.0) + 0.04 * np.sin(th * 3 + z * 5))
    return mb

def bulged_box(mb, c, size, mat, n=6, bulge=0.035, R=None):
    sx, sy, sz = size
    for axis in range(3):
        for sg in (-1, 1):
            a1, a2 = [i for i in range(3) if i != axis]
            us = np.linspace(-0.5, 0.5, n + 1)
            U, V = np.meshgrid(us, us, indexing='ij')
            P = np.zeros((n + 1, n + 1, 3))
            dims = np.array(size)
            P[:, :, axis] = sg * dims[axis] / 2 + sg * bulge * (1 - (2 * U) ** 2) * (1 - (2 * V) ** 2)
            P[:, :, a1] = U * dims[a1]
            P[:, :, a2] = V * dims[a2]
            uv = np.stack([U * dims[a1] + 7.0, V * dims[a2] + 3.0], axis=-1)
            Pr = P if R is None else P @ np.asarray(R).T
            flip = (sg > 0) != ((axis + 1) % 3 == a1)
            mb.grid(Pr + np.asarray(c), uv, mat, True, flip=bool(flip))

def hay_bale(rng, size=(0.95, 0.5, 0.42)):
    mb = _mb(rng)
    bulged_box(mb, (0, 0, size[2] / 2), size, CM['straw'], 6, 0.03)
    for x in (-size[0] * 0.28, size[0] * 0.28):
        for (ax, off) in ((0, size[2] / 2 + 0.032), (1, 0)):
            pass
        mb.box((x, 0, size[2] + 0.028), (0.014, size[1] + 0.06, 0.012), None, CM['rope'], grain=1)
        mb.box((x, 0, -0.0 + 0.002), (0.014, size[1] + 0.06, 0.012), None, CM['rope'], grain=1)
        for sy in (-1, 1):
            mb.box((x, sy * (size[1] / 2 + 0.03), size[2] / 2), (0.014, 0.012, size[2] + 0.04), None, CM['rope'], grain=2)
    return mb

def haystack(rng, r=1.45, h=2.9):
    mb = _mb(rng)
    prof = [(0.001, 0.0), (r * 0.93, 0.0), (r, 0.3), (r * 1.03, 0.9), (r * 0.9, 1.6), (r * 0.62, 2.15), (r * 0.28, 2.6), (r * 0.08, h * 0.97), (0.001, h)]
    seed = int(rng.randint(1000))
    prof = [tuple(p_) for p_ in np.array([np.interp(t, np.linspace(0, 1, len(prof)), [q[0] for q in prof]) for t in np.linspace(0, 1, 28)]).reshape(-1, 1).repeat(2, axis=1)] if False else prof
    zz = np.array([q[1] for q in prof]); rr = np.array([q[0] for q in prof])
    zs = np.linspace(zz[0], zz[-1], 26)
    prof = [(float(np.interp(z_, zz, rr)), float(z_)) for z_ in zs]
    mb.lathe(prof, sides=40, mat=CM['straw'], smooth=True,
             wobble=lambda th, z: 1.0 + 0.07 * perlin2(th * 1.3 + seed, z * 1.6) + 0.03 * perlin2(th * 5 + seed, z * 4))
    mb.tube([(0, 0, 2.2), (0.01, 0, 3.4), (0.0, 0.01, 3.9)], 0.035, sides=6, mat=CM['timber'], smooth=True, cap1=True)
    straw_litter(mb, rng, -r * 1.5, r * 1.5, -r * 1.5, r * 1.5, 160, z=0.01, length=(0.2, 0.5))
    return mb

def wheel(mb, center, radius, width, rng, axis='y', spokes=12):
    sub = MB(); sub.rng = np.random.RandomState(int(rng.randint(1 << 30)))
    ang = np.linspace(0, 2 * math.pi, 28, endpoint=False)
    ring = np.stack([radius * np.cos(ang), np.zeros_like(ang), radius * np.sin(ang)], axis=1)
    ring = np.vstack([ring, ring[:1]])
    sub.tube(ring, width * 0.5, sides=4, mat=CM['plank'], smooth=False)
    ring2 = ring * (1.0 + 0.045 / radius)
    sub.tube(ring2, 0.016, sides=4, mat=CM['iron'], smooth=False)
    sub.lathe([(0.001, -width * 1.5), (0.07, -width * 1.5), (0.1, -width * 0.6), (0.12, 0.0), (0.1, width * 0.6), (0.07, width * 1.5), (0.001, width * 1.5)], sides=12, mat=CM['timber'], smooth=True)
    n0 = len(sub.V) - 1
    sub.xform_since((n0, 0, 0), rotx(math.pi / 2), (0, 0, 0))
    for i in range(spokes):
        a = 2 * math.pi * i / spokes + rng.uniform(-0.02, 0.02)
        d = np.array([math.cos(a), 0.0, math.sin(a)])
        beam(sub, d * 0.09, d * (radius - 0.03), 0.045, width * 0.9, CM['plank'], up=(0, 1, 0))
    mb.extend(sub, None, center)

def cart(rng, tilt_deg=6.0):
    mb = _mb(rng)
    az = 0.62
    for sy in (-1, 1):
        wheel(mb, (0, sy * 0.78, az), 0.6, 0.07, rng)
    mb.box((0, 0, az), (0.1, 1.9, 0.1), None, CM['timber'], grain=1)
    zb = az + 0.28
    for sy in (-1, 1):
        mb.box((0.0, sy * 0.5, zb - 0.07), (2.4, 0.1, 0.12), None, CM['timber'], grain=0)
    for k in range(6):
        y = -0.57 + k * 0.228
        mb.box((0, y, zb + 0.0), (2.3, 0.21, 0.04), None, CM['plank'], grain=0)
    for sy in (-1, 1):
        for k in range(2):
            mb.box((0, sy * 0.61, zb + 0.14 + k * 0.15), (2.3, 0.035, 0.135), None, CM['plank'], grain=0)
        for x in (-1.12, -0.37, 0.37, 1.12):
            mb.box((x, sy * 0.61, zb + 0.22), (0.06, 0.06, 0.42), None, CM['timber'], grain=2)
    for k in range(2):
        mb.box((1.15, 0, zb + 0.14 + k * 0.15), (0.035, 1.22, 0.135), None, CM['plank'], grain=1)
    # tailgate dropped on chains
    mb.box((-1.2, 0, zb - 0.1), (0.04, 1.2, 0.3), None, CM['plank'], grain=1)
    # shafts
    for sy in (-1, 1):
        mb.tube([(-0.5, sy * 0.52, zb - 0.1), (1.0, sy * 0.52, zb - 0.06), (2.1, sy * 0.5, zb - 0.28), (3.3, sy * 0.46, zb - 0.62)], [0.05, 0.045, 0.038, 0.03], sides=7, mat=CM['timber'], smooth=True, cap1=True)
    mb.box((2.2, 0, zb - 0.32), (0.06, 1.0, 0.07), None, CM['timber'], grain=1)
    # rotate about the axle so the shafts nearly touch the ground
    R = roty(math.radians(tilt_deg))
    mb.xform_since((0, 0, 0), R, (0, 0, 0))
    return mb

def stone_ring(mb, r_out, z0, z1, rng, th=0.28, ch=0.2, n_per=None):
    nc = max(1, int(round((z1 - z0) / ch)))
    h = (z1 - z0) / nc
    for c in range(nc):
        n = n_per or int(2 * math.pi * (r_out - th / 2) / 0.42)
        off = (c % 2) * 0.5
        for i in range(n):
            a = 2 * math.pi * (i + off) / n
            rr = r_out - th / 2
            cx, cy = rr * math.cos(a), rr * math.sin(a)
            arc = 2 * math.pi * rr / n
            stone_block(mb, (cx, cy, z0 + c * h + h / 2), (arc * 0.97, th * rng.uniform(0.85, 1.05), h * rng.uniform(0.9, 1.05)), rotz(a + math.pi / 2 + rng.uniform(-0.05, 0.05)), rng, CM['stone'], rough=0.08)

def well(rng):
    mb = _mb(rng)
    stone_ring(mb, 0.92, 0.0, 0.95, rng, th=0.3, ch=0.19)
    mb.lathe([(0.001, 0.8), (0.64, 0.8), (0.64, 0.95), (0.001, 0.95)], sides=20, mat=CM['roofdark'], smooth=False)
    # cap stones ring on top
    stone_ring(mb, 0.98, 0.95, 1.07, rng, th=0.38, ch=0.12, n_per=15)
    for sx in (-1, 1):
        mb.box((sx * 1.08, 0, 1.2), (0.16, 0.16, 2.4), None, CM['timber'], grain=2)
        beam(mb, (sx * 1.08, 0.0, 0.3), (sx * 1.08, 0.0, 0.3 + 0.001), 0.01, 0.01, CM['timber'])
    mb.box((0, 0, 2.28), (2.5, 0.17, 0.15), None, CM['timber'], grain=0)
    # little plank roof
    th = math.radians(36)
    for sg in (-1, 1):
        R = rotx(sg * th)
        mb.box((0, sg * 0.5, 2.55), (2.7, 1.25, 0.045), R, CM['plank'], grain=0)
    mb.box((0, 0, 2.86), (2.72, 0.07, 0.07), None, CM['timber'], grain=0)
    # windlass with crank and rope
    mb.tube([(-1.12, 0, 1.75), (1.12, 0, 1.75)], 0.075, sides=10, mat=CM['timber'], smooth=True, cap0=True, cap1=True)
    mb.tube([(1.12, 0, 1.75), (1.22, 0.0, 1.75), (1.22, 0.32, 1.75), (1.3, 0.32, 1.75)], 0.025, sides=6, mat=CM['iron'], smooth=True)
    turns = 7
    pts = [(-0.35 + 0.5 * t / (turns * 12), 0.095 * math.cos(2 * math.pi * t / 12), 1.75 + 0.095 * math.sin(2 * math.pi * t / 12)) for t in range(turns * 12 + 1)]
    mb.tube(pts, 0.02, sides=5, mat=CM['rope'], smooth=True)
    mb.tube([(0.15, 0.0, 1.655), (0.15, 0.01, 1.2), (0.15, 0.03, 0.62)], 0.014, sides=5, mat=CM['rope'], smooth=True)
    bucket_mesh(mb, (0.15, 0.03, 0.34), rng, 0.0)
    return mb

def trough(rng, L=2.2):
    mb = _mb(rng)
    w, h = 0.55, 0.42
    z = 0.28
    mb.box((0, 0, z + 0.03), (L, w, 0.06), None, CM['plank'], grain=0)
    for sy in (-1, 1):
        mb.box((0, sy * (w / 2 - 0.035), z + h / 2), (L, 0.07, h), None, CM['plank'], grain=0)
    for sx in (-1, 1):
        mb.box((sx * (L / 2 - 0.04), 0, z + h / 2), (0.08, w, h), None, CM['plank'], grain=1)
    mb.box((0, 0, z + 0.1), (L - 0.12, w - 0.12, 0.012), None, CM['roofdark'])
    for sx in (-1, 1):
        stone_block(mb, (sx * (L / 2 - 0.35), 0, z / 2), (0.34, w + 0.1, z), np.eye(3), rng, CM['stone'], rough=0.06)
    return mb

def pointed_post(mb, x, y, h, w, rng, lean=0.0):
    sub = _mb(rng)
    sub.box((0, 0, h / 2), (w, w, h), None, CM['timber'], grain=2)
    top = h
    P = np.array([[-w / 2, -w / 2, top], [w / 2, -w / 2, top], [w / 2, w / 2, top], [-w / 2, w / 2, top]])
    apex = np.array([0, 0, top + w * 0.7])
    for i in range(4):
        sub.tris_hard(np.array([[P[i], P[(i + 1) % 4], apex]]), None, CM['timber'], False)
    mb.extend(sub, rotx(lean * 0.7) @ roty(lean), (x, y, 0.0))

def fence(rng, pts, h=1.1, gap=2.3, rails=2, broken=0.12, z0=0.0):
    """pts: list of (x,y,z) polyline; ground height supplied per point (z); posts follow linear interpolation"""
    mb = _mb(rng)
    pts = np.asarray(pts, float)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = np.linalg.norm(b[:2] - a[:2])
        n = max(1, int(round(L / gap)))
        yaw = math.atan2(b[1] - a[1], b[0] - a[0])
        for k in range(n + (1 if i == len(pts) - 2 else 0)):
            t = k / n
            p = a + (b - a) * t
            lean = rng.uniform(-0.06, 0.06)
            pointed_post(mb, p[0], p[1] + 0, h, 0.11, rng, lean) if False else None
            sub = _mb(rng)
            sub.box((0, 0, h / 2 - 0.1), (0.11, 0.11, h + 0.2), None, CM['timber'], grain=2)
            P = np.array([[-0.055, -0.055, h + 0.1], [0.055, -0.055, h + 0.1], [0.055, 0.055, h + 0.1], [-0.055, 0.055, h + 0.1]])
            apex = np.array([0, 0, h + 0.18])
            for q in range(4):
                sub.tris_hard(np.array([[P[q], P[(q + 1) % 4], apex]]), None, CM['timber'], False)
            mb.extend(sub, rotz(rng.uniform(0, 3)) @ rotx(lean) @ roty(rng.uniform(-0.05, 0.05)), (p[0], p[1], p[2]))
        for k in range(n):
            p0 = a + (b - a) * (k / n)
            p1 = a + (b - a) * ((k + 1) / n)
            for r in range(rails):
                if rng.rand() < broken:
                    continue
                z = h * (0.38 + 0.5 * r / max(rails - 1, 1)) if rails > 1 else h * 0.7
                q0 = p0 + np.array([0, 0, z]) + np.array([0, 0, rng.uniform(-0.03, 0.03)])
                q1 = p1 + np.array([0, 0, z]) + np.array([0, 0, rng.uniform(-0.03, 0.03)])
                if rng.rand() < 0.1:
                    q1 = q1 + np.array([0, 0, -0.5])
                beam(mb, q0, q1, 0.05, 0.09, CM['plank'], up=(0, 0, 1))
    return mb

def log_piece(mb, p0, p1, r, rng):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    pts = np.linspace(p0, p1, 3)
    mb.tube(pts, r, sides=9, mat=CM['bark'], smooth=True, cap0=False, cap1=False)
    d = (p1 - p0) / (np.linalg.norm(p1 - p0) + 1e-9)
    for p, sgn in ((p0, -1), (p1, 1)):
        ang = np.linspace(0, 2 * math.pi, 9, endpoint=False)
        B = basis_from_dir(d)
        ring = np.array([p + B[:, 0] * r * math.cos(a) + B[:, 1] * r * math.sin(a) for a in ang])
        uv = np.stack([ring[:, 0] * 3, ring[:, 1] * 3], axis=1)
        c = p
        base = mb.verts(np.vstack([c[None], ring]))
        i = np.arange(9)
        tri = np.stack([np.full(9, base), base + 1 + i, base + 1 + (i + 1) % 9], axis=1)
        if sgn > 0:
            tri = tri[:, [0, 2, 1]]
        mb.tris(tri, None, CM['plank'], False)

def woodpile(rng, L=1.0, rows=4, cols=7):
    mb = _mb(rng)
    for r in range(rows):
        nc = cols - r
        for k in range(nc):
            rad = rng.uniform(0.065, 0.1)
            y = (k - (nc - 1) / 2) * 0.185 + rng.uniform(-0.01, 0.01)
            z = rad + r * 0.165
            ln = L * rng.uniform(0.9, 1.05)
            xo = rng.uniform(-0.05, 0.05)
            log_piece(mb, (-ln / 2 + xo, y, z), (ln / 2 + xo, y + rng.uniform(-0.01, 0.01), z), rad, rng)
    for sy in (-1, 1):
        mb.box((L / 2 + 0.06, sy * (cols * 0.185 / 2 + 0.05), 0.4), (0.07, 0.07, 0.8), None, CM['timber'], grain=2)
        mb.box((-L / 2 - 0.06, sy * (cols * 0.185 / 2 + 0.05), 0.4), (0.07, 0.07, 0.8), None, CM['timber'], grain=2)
    return mb

def chopping_block(rng):
    mb = _mb(rng)
    log_piece(mb, (0, 0, 0), (0, 0, 0.5), 0.27, rng)
    mb.xform_since((0, 0, 0), None, (0, 0, 0))
    beam(mb, (0.05, 0.0, 0.56), (0.62, 0.0, 1.0), 0.045, 0.045, CM['plank'], up=(0, 1, 0))
    mb.box((-0.02, 0, 0.55), (0.18, 0.025, 0.14), rotx(0) @ roty(math.radians(-35)), CM['iron'], grain=0)
    # split logs lying around
    for k in range(4):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0.5, 0.9)
        log_piece(mb, (r * math.cos(a), r * math.sin(a), 0.07), (r * math.cos(a) + 0.3 * math.cos(a + 1), r * math.sin(a) + 0.3 * math.sin(a + 1), 0.07), 0.07, rng)
    return mb

def arrow_board(mb, L, w, mat):
    P = np.array([[0, -w / 2], [L - 0.2, -w / 2], [L, 0], [L - 0.2, w / 2], [0, w / 2]])
    th = 0.03
    top = np.array([[p[0], 0, p[1]] for p in P])
    bot = top.copy()
    top[:, 1] = th / 2; bot[:, 1] = -th / 2
    uv = P.copy()
    mb.polygon_fan(top, mat, flip=False)
    mb.polygon_fan(bot, mat, flip=True)
    for i in range(5):
        j = (i + 1) % 5
        mb.quads_hard(np.array([[bot[i], bot[j], top[j], top[i]]]), None, mat, False)

def signpost(rng):
    mb = _mb(rng)
    mb.box((0, 0, 1.4), (0.14, 0.14, 2.8), None, CM['timber'], grain=2)
    for (z, ang, L) in ((2.45, 0.25, 1.1), (2.05, -0.5, 0.95)):
        sub = _mb(rng)
        arrow_board(sub, L, 0.2, CM['plank'])
        mb.extend(sub, rotz(ang), (0.0, -0.1, z))
    return mb

def lantern_post(rng, h=3.2):
    mb = _mb(rng)
    mb.tube([(0, 0, 0), (0.01, 0, h * 0.5), (0, 0, h)], [0.075, 0.06, 0.05], sides=8, mat=CM['timber'], smooth=True, cap1=True)
    beam(mb, (0, 0, h - 0.1), (0.6, 0, h - 0.35), 0.05, 0.05, CM['timber'], up=(0, 1, 0))
    beam(mb, (0, 0, h - 0.5), (0.45, 0, h - 0.34), 0.04, 0.04, CM['timber'], up=(0, 1, 0))
    c = np.array([0.6, 0, h - 0.62])
    mb.tube([(0.6, 0, h - 0.35), (0.6, 0, h - 0.45)], 0.008, sides=5, mat=CM['iron'], smooth=True)
    mb.box(c, (0.17, 0.17, 0.26), None, CM['glass'], grain=2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(c + np.array([sx * 0.085, sy * 0.085, 0]), (0.014, 0.014, 0.28), None, CM['iron'], grain=2)
    mb.box(c + np.array([0, 0, 0.16]), (0.22, 0.22, 0.03), None, CM['iron'], grain=0)
    mb.box(c + np.array([0, 0, -0.15]), (0.2, 0.2, 0.025), None, CM['iron'], grain=0)
    return mb

def bench(rng, L=1.6):
    mb = _mb(rng)
    mb.box((0, 0, 0.46), (L, 0.32, 0.05), None, CM['plank'], grain=0)
    for sx in (-1, 1):
        mb.box((sx * (L / 2 - 0.2), 0, 0.22), (0.06, 0.28, 0.44), None, CM['plank'], grain=2)
    mb.box((0, 0, 0.3), (L - 0.4, 0.05, 0.08), None, CM['timber'], grain=0)
    return mb

def wheelbarrow(rng):
    mb = _mb(rng)
    mb.box((0.05, 0, 0.42), (0.85, 0.5, 0.025), None, CM['plank'], grain=0)
    for sy in (-1, 1):
        mb.box((0.05, sy * 0.27, 0.52), (0.85, 0.025, 0.22), rotx(sy * 0.45) * 1.0 if False else None, CM['plank'], grain=0)
    mb.box((0.5, 0, 0.5), (0.025, 0.5, 0.2), None, CM['plank'], grain=1)
    mb.box((-0.38, 0, 0.5), (0.025, 0.5, 0.2), None, CM['plank'], grain=1)
    for sy in (-1, 1):
        mb.tube([(0.6, sy * 0.15, 0.3), (-0.2, sy * 0.3, 0.38), (-1.0, sy * 0.42, 0.55)], [0.025, 0.025, 0.028], sides=6, mat=CM['timber'], smooth=True, cap1=True)
        mb.box((-0.32, sy * 0.3, 0.2), (0.04, 0.04, 0.4), None, CM['timber'], grain=2)
    wheel(mb, (0.62, 0, 0.18), 0.18, 0.04, rng, spokes=6)
    return mb

def jug(rng, h=0.34, r=0.12):
    mb = _mb(rng)
    prof = [(0.001, 0.0), (r * 0.6, 0.0), (r * 0.9, 0.04 * h / 0.34), (r, 0.3 * h), (r * 0.9, 0.55 * h), (r * 0.45, 0.82 * h), (r * 0.4, 0.92 * h), (r * 0.5, h), (r * 0.42, h * 1.01)]
    mb.lathe(prof, sides=14, mat=CM['clay'], smooth=True)
    mb.tube([(r * 0.42, 0, h * 0.9), (r * 1.25, 0, h * 0.78), (r * 1.2, 0, h * 0.42), (r * 0.95, 0, h * 0.3)], 0.014, sides=6, mat=CM['clay'], smooth=True)
    return mb

def ladder(rng, L=3.2, w=0.45):
    mb = _mb(rng)
    for sy in (-1, 1):
        mb.box((0, sy * w / 2, L / 2), (0.05, 0.07, L), None, CM['plank'], grain=2)
    n = int(L / 0.3)
    for k in range(n):
        mb.box((0, 0, 0.3 + k * 0.3), (0.04, w, 0.04), None, CM['plank'], grain=1)
    return mb

def skep(rng, r=0.28):
    mb = _mb(rng)
    prof = [(0.001, 0.0), (r, 0.0), (r * 1.0, 0.04), (r * 0.98, 0.18), (r * 0.8, 0.3), (r * 0.55, 0.4), (r * 0.25, 0.47), (0.001, 0.5)]
    mb.lathe(prof, sides=14, mat=CM['straw'], smooth=True)
    for k in range(3):
        mb.lathe([(r * (1.0 - 0.18 * k) + 0.004, 0.06 + k * 0.1), (r * (1.0 - 0.18 * k) + 0.012, 0.075 + k * 0.1), (r * (1.0 - 0.18 * k) + 0.004, 0.09 + k * 0.1)], sides=14, mat=CM['rope'], smooth=True)
    mb.box((0, 0, -0.2 + 0.2 - 0.01 - 0.0), (0.0, 0.0, 0.0), None, CM['stone']) if False else None
    return mb

def boulder(rng, r=0.5):
    mb = _mb(rng)
    seed = int(rng.randint(1000))
    n = 9
    prof = [(0.001, -r * 0.55)] + [(r * math.sin(a), -r * 0.55 * math.cos(a) if a < math.pi / 2 else -r * 0.55 * math.cos(a) * 1.0) for a in np.linspace(0.3, math.pi - 0.3, n)] + [(0.001, r * 0.55)]
    prof = [(p[0], p[1] + r * 0.35) for p in prof]
    mb.lathe(prof, sides=14, mat=CM['rock'], smooth=True,
             wobble=lambda th, z: 1.0 + 0.22 * perlin2(th * 1.1 + seed, z * 2.2) + 0.08 * perlin2(th * 3 + seed, z * 5))
    return mb

def muck_heap(rng, r=0.9):
    mb = _mb(rng)
    seed = int(rng.randint(1000))
    prof = [(0.001, 0.0), (r, 0.0), (r * 0.95, 0.12), (r * 0.7, 0.3), (r * 0.38, 0.42), (r * 0.1, 0.46), (0.001, 0.45)]
    mb.lathe(prof, sides=16, mat=CM['muck'], smooth=True, wobble=lambda th, z: 1.0 + 0.18 * perlin2(th * 1.5 + seed, z * 3.0))
    straw_litter(mb, rng, -r * 1.2, r * 1.2, -r * 1.2, r * 1.2, 120, z=0.02, length=(0.15, 0.45))
    return mb

def pitchfork(rng):
    mb = _mb(rng)
    mb.tube([(0, 0, 0), (0.0, 0, 0.9), (0, 0, 1.55)], 0.018, sides=6, mat=CM['plank'], smooth=True)
    mb.box((0, 0, 1.55), (0.2, 0.02, 0.025), None, CM['iron'], grain=0)
    for x in (-0.09, 0, 0.09):
        mb.tube([(x, 0, 1.55), (x, 0, 1.72), (x, 0, 1.9)], 0.007, sides=4, mat=CM['iron'], smooth=True, cap1=True)
    return mb

def broom(rng):
    mb = _mb(rng)
    mb.tube([(0, 0, 0.35), (0, 0, 1.0), (0, 0, 1.6)], 0.016, sides=6, mat=CM['plank'], smooth=True)
    mb.lathe([(0.001, 0.0), (0.13, 0.0), (0.12, 0.2), (0.06, 0.35), (0.02, 0.4)], sides=10, mat=CM['straw'], smooth=True)
    return mb

def log_pile_loose(rng, n=5):
    mb = _mb(rng)
    for k in range(n):
        a = rng.uniform(-0.4, 0.4)
        y = rng.uniform(-0.3, 0.3)
        log_piece(mb, (-0.8, y, 0.1 + 0.1 * (k % 2)), (0.8 * math.cos(a), y + 0.8 * math.sin(a), 0.1 + 0.1 * (k % 2)), rng.uniform(0.08, 0.12), rng)
    return mb

def stone_block_seat(rng):
    mb = _mb(rng)
    stone_block(mb, (0, 0, 0.2), (0.9, 0.7, 0.4), np.eye(3), rng, CM['stone'], rough=0.05)
    stone_block(mb, (0.0, -0.0, 0.46), (0.7, 0.5, 0.12), rotz(0.1), rng, CM['stone'], rough=0.05)
    return mb


def horse_collar(rng):
    """A worn leather horse collar with a rope loop, hanging from a peg at the origin (ring faces -y)."""
    mb = _mb(rng)
    ang = np.linspace(0, 2 * math.pi, 22)
    ring = np.stack([0.17 * np.cos(ang) + 0.0, np.zeros_like(ang), -0.34 + 0.24 * np.sin(ang)], axis=1)
    ring[:, 0] *= 1.0
    mb.tube(ring, 0.062, sides=8, mat=CM['leather'], smooth=True)
    inner = np.stack([0.17 * np.cos(ang), np.zeros_like(ang), -0.34 + 0.24 * np.sin(ang)], axis=1)
    mb.tube(inner * np.array([1.0, 1.0, 1.0]) * 1.0, 0.012, sides=5, mat=CM['rope'], smooth=True)
    mb.tube([(0, 0.0, 0.0), (0.0, -0.01, -0.06), (0.04, 0.0, -0.12), (0.0, 0.0, -0.1)], 0.01, sides=5, mat=CM['rope'], smooth=True)
    mb.box((0, 0.045, -0.34 - 0.24), (0.06, 0.03, 0.04), None, CM['iron'], grain=0)
    return mb

def halter(rng):
    mb = _mb(rng)
    mb.tube([(0, 0, 0), (0.02, 0, -0.18), (-0.05, 0, -0.34), (0.0, 0, -0.5)], 0.011, sides=5, mat=CM['rope'], smooth=True)
    ang = np.linspace(0, 2 * math.pi, 14)
    ring = np.stack([0.09 * np.cos(ang), np.zeros_like(ang), -0.56 + 0.07 * np.sin(ang)], axis=1)
    mb.tube(ring, 0.013, sides=5, mat=CM['leather'], smooth=True)
    return mb
