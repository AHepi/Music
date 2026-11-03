#!/usr/bin/env python3
"""A suburban townhouse at dusk, in the film's look.
Run:  python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
Everything (building the scene, lighting, drawing, finishing) is in this one file.
"""
import sys, os, math, random, time
import numpy as np
import bpy
from mathutils import Vector

W = int(sys.argv[1]) if len(sys.argv) > 1 else 540
H = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 64
OUT = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else 'out.png'
HERE = os.path.dirname(os.path.abspath(__file__))
EXPO = float(os.environ.get('TH_EXPO', '1.25'))

rng = random.Random(11)


def hx(s):
    """hex colour -> linear rgb"""
    s = s.lstrip('#')
    c = [int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c]
    return tuple(lin)


# ----------------------------------------------------------------- mesh builder
class MB:
    """collects faces (unshared vertices) with per-corner colours"""

    def __init__(s):
        s.v = []
        s.f = []
        s.c = []

    def add(s, pts, col=None, cols=None):
        i = len(s.v)
        s.v.extend(pts)
        s.f.append(tuple(range(i, i + len(pts))))
        if cols is None:
            cc = tuple(col) if col is not None else (1, 1, 1, 1)
            if len(cc) == 3:
                cc = cc + (1.0,)
            cols = [cc] * len(pts)
        s.c.append(cols)

    def poly_out(s, pts, centre, col=None):
        p = [Vector(q) for q in pts]
        n = Vector((0, 0, 0))
        for i in range(len(p)):
            a, b = p[i], p[(i + 1) % len(p)]
            n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
        fc = sum(p, Vector()) / len(p)
        if n.dot(fc - Vector(centre)) < 0:
            pts = pts[::-1]
        s.add(list(pts), col)

    def box(s, x0, x1, y0, y1, z0, z1, col=None):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if z1 < z0: z0, z1 = z1, z0
        p = {}
        for i, x in enumerate((x0, x1)):
            for j, y in enumerate((y0, y1)):
                for k, z in enumerate((z0, z1)):
                    p[(i, j, k)] = (x, y, z)
        F = [((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
             ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
             ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
             ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
             ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
             ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))]
        for f in F:
            s.add([p[k] for k in f], col)

    def tube(s, a, b, ra, rb=None, n=8, col=None, caps=True):
        a = Vector(a); b = Vector(b)
        rb = ra if rb is None else rb
        d = (b - a)
        L = d.length
        d.normalize()
        ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        p1 = d.cross(ref).normalized()
        p2 = d.cross(p1).normalized()
        ring_a = []
        ring_b = []
        for i in range(n):
            t = 2 * math.pi * (i + 0.5) / n
            o = p1 * math.cos(t) + p2 * math.sin(t)
            ring_a.append(a + o * ra)
            ring_b.append(b + o * rb)
        centre = (a + b) / 2
        for i in range(n):
            j = (i + 1) % n
            s.poly_out([ring_a[i], ring_a[j], ring_b[j], ring_b[i]], centre, col)
        if caps:
            s.poly_out(ring_a, centre, col)
            s.poly_out(ring_b, centre, col)

    def beam(s, a, b, r, col=None):
        s.tube(a, b, r, r, n=4, col=col)

    def build(s, name, mat, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in s.v], [], s.f)
        me.update()
        ca = me.color_attributes.new(name='Col', type='FLOAT_COLOR', domain='CORNER')
        arr = np.ones((len(me.loops), 4), dtype=np.float32)
        li = 0
        for fc in s.c:
            for c in fc:
                arr[li] = c
                li += 1
        ca.data.foreach_set('color', arr.ravel())
        for p in me.polygons:
            p.use_smooth = smooth
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        if mat is not None:
            ob.data.materials.append(mat)
        return ob


class Fr:
    """local frame: u outward from facade, v along the facade, z up"""

    def __init__(s, fn, parity):
        s.fn = fn
        s.p = parity

    def box(s, mb, u0, u1, v0, v1, z0, z1, col=None):
        a = s.fn(u0, v0, z0)
        b = s.fn(u1, v1, z1)
        mb.box(a[0], b[0], a[1], b[1], a[2], b[2], col)

    def poly(s, mb, pts, hint, col=None, cols=None):
        n = Vector((0, 0, 0))
        P = [Vector(q) for q in pts]
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
        if n.dot(Vector(hint)) < 0:
            pts = pts[::-1]
            if cols is not None: cols = cols[::-1]
        if s.p < 0:
            pts = pts[::-1]
            if cols is not None: cols = cols[::-1]
        mb.add([s.fn(*q) for q in pts], col, cols)

    def beam(s, mb, a, b, r, col=None):
        mb.beam(s.fn(*a), s.fn(*b), r, col)

    def tube(s, mb, a, b, ra, rb=None, n=8, col=None, caps=True):
        mb.tube(s.fn(*a), s.fn(*b), ra, rb, n, col, caps)

    def prism_roof(s, mb, sect, v0, v1, col=None):
        """closed prism: sect = [(u,z)...] cross-section, extruded along v"""
        cen = (sum(p[0] for p in sect) / len(sect), (v0 + v1) / 2, sum(p[1] for p in sect) / len(sect))
        n = len(sect)
        for i in range(n):
            j = (i + 1) % n
            q = [(sect[i][0], v0, sect[i][1]), (sect[j][0], v0, sect[j][1]),
                 (sect[j][0], v1, sect[j][1]), (sect[i][0], v1, sect[i][1])]
            s.poly(mb, q, s._away(q, cen), col)
        for v in (v0, v1):
            q = [(p[0], v, p[1]) for p in sect]
            s.poly(mb, q, (0, 1 if v == v1 else -1, 0), col)

    def _away(s, q, cen):
        fc = [sum(p[i] for p in q) / len(q) for i in range(3)]
        return (fc[0] - cen[0], fc[1] - cen[1], fc[2] - cen[2])


# ----------------------------------------------------------------- colours
WARM = [(1.0, 0.52, 0.19), (1.0, 0.60, 0.25), (1.0, 0.46, 0.16), (0.95, 0.55, 0.28)]
PAINT_CREAM = hx('#6f6a5c')
PAINT_TEAL = hx('#2d4a4c')
PAINT_OX = hx('#4d2118')
PAINT_GREEN = hx('#283b33')
PAINT_BLACK = hx('#16191a')
STONE = hx('#5e605b')

# ----------------------------------------------------------------- the street plan (metres)
# x right, y away from the camera, z up.
# Road (cobbles) |x| < 2.2, kerbs, pavements to |x| 3.4, forecourts to the house fronts at |x| 4.8.
# Two terraces face each other (y 4..19); the hero row closes the street at y = 19.
FX = 4.25     # facade distance (side rows)
FY = 15.0     # end row facade
DW = 1.2      # forecourt depth
RD = 1.7      # half width of the cobbled road
KERB_Y = FY - DW - 1.3
PVX = FX - DW  # outer edge of the pavements
EZ = 8.62     # eaves height
HW = 4.0      # house width in the terraces

B = {k: MB() for k in ['brick', 'stone', 'slate', 'paint', 'iron', 'glassL', 'glassD', 'terra', 'brass',
                      'flag', 'earth', 'lampglass', 'wood', 'plaster', 'grit']}


def frame_left():
    return Fr(lambda u, v, z: (-FX + u, v, z), +1)


def frame_right():
    return Fr(lambda u, v, z: (FX - u, v, z), -1)


def frame_end():
    return Fr(lambda u, v, z: (v, FY - u, z), +1)


def wall_with_holes(fr, v0, v1, z0, z1, holes, ut0=-0.4, ut1=0.0):
    brks = sorted(set([v0, v1] + [h[0] for h in holes] + [h[1] for h in holes]))
    for a, b in zip(brks[:-1], brks[1:]):
        if b - a < 1e-4: continue
        here = sorted([h for h in holes if h[0] <= a + 1e-6 and h[1] >= b - 1e-6], key=lambda h: h[2])
        cur = z0
        for h in here:
            if h[2] > cur + 1e-4:
                fr.box(B['brick'], ut0, ut1, a, b, cur, h[2])
            cur = max(cur, h[3])
        if cur < z1 - 1e-4:
            fr.box(B['brick'], ut0, ut1, a, b, cur, z1)


def glass_quad(fr, u, va, vb, za, zb, lit, k=1.0, grad=True, col=None):
    """one pane: lit (warm emission) or dark glass; faces outward (+u)"""
    pts = [(u, va, za), (u, vb, za), (u, vb, zb), (u, va, zb)]
    if lit:
        c = col if col is not None else rng.choice(WARM)
        top = (c[0] * k, c[1] * k, c[2] * k, 1.0)
        bot_k = 0.35 if grad else 1.0
        bot = (c[0] * k * bot_k, c[1] * k * bot_k * 0.9, c[2] * k * bot_k * 0.8, 1.0)
        fr.poly(B['glassL'], pts, (1, 0, 0), cols=[bot, bot, top, top])
    else:
        fr.poly(B['glassD'], pts, (1, 0, 0), col=(1, 1, 1, 1))


def window(fr, va, vb, za, zb, lit, k=1.0, paint=PAINT_CREAM, bars=True):
    t = 0.07
    fr.box(B['paint'], -0.22, -0.09, va, vb, za, za + t, paint)
    fr.box(B['paint'], -0.22, -0.09, va, vb, zb - t, zb, paint)
    fr.box(B['paint'], -0.22, -0.09, va, va + t, za, zb, paint)
    fr.box(B['paint'], -0.22, -0.09, vb - t, vb, za, zb, paint)
    mid = za + (zb - za) * 0.52
    fr.box(B['paint'], -0.20, -0.07, va, vb, mid - 0.03, mid + 0.03, paint)
    if bars and (vb - va) > 1.0:
        vm = (va + vb) / 2
        fr.box(B['paint'], -0.20, -0.07, vm - 0.03, vm + 0.03, za, zb, paint)
    glass_quad(fr, -0.24, va + t, vb - t, za + t, zb - t, lit, k)
    # stone sill and lintel
    fr.box(B['stone'], -0.4, 0.13, va - 0.07, vb + 0.07, za - 0.10, za, STONE)
    fr.box(B['stone'], -0.4, 0.07, va - 0.10, vb + 0.10, zb, zb + 0.17, STONE)


def door(fr, d0, d1, lit, k, paint, hero=False):
    z0, zt, zf = 0.46, 2.50, 3.02
    # stone surround
    fr.box(B['stone'], -0.4, 0.09, d0 - 0.16, d0, z0 - 0.02, zf + 0.05, STONE)
    fr.box(B['stone'], -0.4, 0.09, d1, d1 + 0.16, z0 - 0.02, zf + 0.05, STONE)
    fr.box(B['stone'], -0.4, 0.11, d0 - 0.2, d1 + 0.2, zf, zf + 0.2, STONE)
    # leaf
    fr.box(B['paint'], -0.22, -0.12, d0, d1, z0, zt, paint)
    pd = tuple(c * 0.7 for c in paint)
    vm = (d0 + d1) / 2
    for (a, b) in ((d0 + 0.1, vm - 0.04), (vm + 0.04, d1 - 0.1)):
        fr.box(B['paint'], -0.12, -0.08, a, b, 0.62, 1.30, pd)
        fr.box(B['paint'], -0.12, -0.08, a, b, 1.42, 2.36, pd)
    fr.box(B['paint'], -0.22, -0.09, d0, d1, zt, zt + 0.07, paint)
    # fanlight
    glass_quad(fr, -0.2, d0 + 0.05, d1 - 0.05, zt + 0.07, zf - 0.05, lit, k * 1.2, grad=False,
               col=(1.0, 0.62, 0.26))
    for f in (0.25, 0.5, 0.75):
        v = d0 + (d1 - d0) * f
        fr.box(B['paint'], -0.19, -0.1, v - 0.015, v + 0.015, zt + 0.07, zf - 0.05, paint)
    # brass: knob, letterbox, number plate
    fr.box(B['brass'], -0.12, 0.0, vm - 0.04, vm + 0.04, 1.36, 1.44)
    fr.box(B['brass'], -0.12, -0.05, vm - 0.14, vm + 0.14, 1.05, 1.11)
    fr.box(B['brass'], -0.12, -0.05, d1 - 0.3, d1 - 0.12, 1.75, 1.9)
    # steps
    fr.box(B['stone'], 0.0, 0.85, d0 - 0.2, d1 + 0.2, -0.1, 0.27, STONE)
    fr.box(B['stone'], 0.0, 0.42, d0 - 0.1, d1 + 0.1, 0.27, 0.46, STONE)


def bay(fr, vc, w, depth, z0, z1, lit, k, paint, storeys=1):
    v0, v1 = vc - w / 2, vc + w / 2
    # brick dado
    fr.box(B['brick'], 0.0, depth, v0, v1, -0.1, z0 + 0.72)
    fr.box(B['stone'], 0.0, depth + 0.07, v0 - 0.04, v1 + 0.04, z0 + 0.72, z0 + 0.8, STONE)
    zg0, zg1 = z0 + 0.8, z1
    p = 0.09
    # posts
    for v in (v0, v1 - p):
        fr.box(B['paint'], depth - p, depth, v, v + p, zg0, zg1, paint)
    # transom + head
    fr.box(B['paint'], depth - 0.08, depth, v0, v1, zg1 - 0.1, zg1, paint)
    fr.box(B['paint'], depth - 0.08, depth, v0, v1, zg0, zg0 + 0.07, paint)
    for f in (1 / 3, 2 / 3):
        v = v0 + w * f
        fr.box(B['paint'], depth - 0.07, depth, v - 0.03, v + 0.03, zg0, zg1, paint)
    zm = zg0 + (zg1 - zg0) * 0.55
    fr.box(B['paint'], depth - 0.07, depth, v0, v1, zm - 0.03, zm + 0.03, paint)
    # glass front (3 panes) and sides
    n = 3
    for i in range(n):
        a = v0 + p + (w - 2 * p) * i / n
        b = v0 + p + (w - 2 * p) * (i + 1) / n
        glass_quad(fr, depth - 0.1, a + 0.03, b - 0.03, zg0 + 0.07, zg1 - 0.1, lit, k)
    # side panes (face along +-v) : thin quads, emit outward
    for side in (-1, +1):
        v = v0 + 0.03 if side < 0 else v1 - 0.03
        pts = [(0.02, v, zg0 + 0.07), (depth - 0.1, v, zg0 + 0.07), (depth - 0.1, v, zg1 - 0.1), (0.02, v, zg1 - 0.1)]
        c = rng.choice(WARM)
        top = (c[0] * k, c[1] * k, c[2] * k, 1.0)
        bot = (c[0] * k * 0.4, c[1] * k * 0.35, c[2] * k * 0.3, 1.0)
        if lit:
            fr.poly(B['glassL'], pts, (0, side, 0), cols=[bot, bot, top, top])
        else:
            fr.poly(B['glassD'], pts, (0, side, 0), col=(1, 1, 1, 1))
    # flat roof / cornice
    fr.box(B['stone'], -0.0, depth + 0.16, v0 - 0.1, v1 + 0.1, z1, z1 + 0.14, STONE)
    fr.box(B['slate'], 0.0, depth + 0.12, v0 - 0.06, v1 + 0.06, z1 + 0.14, z1 + 0.2, hx('#2a3238'))


def forecourt(fr, v0, v1, gate=None, tall=False):
    """dwarf wall, piers, railings, ground; gate = (g0, g1) opening"""
    ud0, ud1 = DW - 0.06, DW + 0.14
    segs = [(v0, v1)]
    if gate is not None:
        segs = [(v0, gate[0]), (gate[1], v1)]
    for (a, b) in segs:
        fr.box(B['brick'], ud0, ud1, a, b, -0.1, 0.55)
        fr.box(B['stone'], ud0 - 0.03, ud1 + 0.03, a, b, 0.55, 0.62, STONE)
        # railing
        r0 = a + 0.2
        r1 = b - 0.2
        if r1 > r0:
            ux = (ud0 + ud1) / 2
            fr.box(B['iron'], ux - 0.015, ux + 0.015, a + 0.1, b - 0.1, 0.72, 0.76)
            fr.box(B['iron'], ux - 0.02, ux + 0.02, a + 0.1, b - 0.1, 1.18, 1.23)
            nb = max(2, int((r1 - r0) / 0.125))
            for i in range(nb + 1):
                v = r0 + (r1 - r0) * i / nb
                fr.box(B['iron'], ux - 0.012, ux + 0.012, v - 0.012, v + 0.012, 0.62, 1.2)
                fr.box(B['iron'], ux - 0.02, ux + 0.02, v - 0.02, v + 0.02, 1.2, 1.28)
    # piers
    pv = [v0, v1] if gate is None else [v0, gate[0], gate[1], v1]
    for v in pv:
        vv = v + (0.15 if v == v0 else (-0.15 if v == v1 else (-0.0 if v == (gate[0] if gate else 9e9) else 0.0)))
        if gate and v == gate[0]: vv = v - 0.02
        if gate and v == gate[1]: vv = v + 0.02
        fr.box(B['brick'], ud0 - 0.08, ud1 + 0.08, vv - 0.15, vv + 0.15, -0.1, 0.98)
        fr.box(B['stone'], ud0 - 0.12, ud1 + 0.12, vv - 0.19, vv + 0.19, 0.98, 1.08, STONE)
        fr.box(B['stone'], ud0 - 0.04, ud1 + 0.04, vv - 0.11, vv + 0.11, 1.08, 1.16, STONE)
    # ground: earth with a paved path to the door
    fr.box(B['earth'], 0.0, DW, v0, v1, -0.3, 0.10)
    if gate is not None:
        fr.box(B['flag'], 0.0, DW + 0.14, gate[0] + 0.04, gate[1] - 0.04, -0.3, 0.115)


def roof_and_stacks(fr, v0, v1, stacks, ridge_u=-3.4):
    ez = EZ + 0.12
    rz = ez + (0.38 - ridge_u) * 0.72
    sect = [(0.38, ez), (ridge_u, rz), (ridge_u - 3.78, ez), (ridge_u - 3.78, ez - 0.4), (0.38, ez - 0.4)]
    fr.prism_roof(B['slate'], sect, v0, v1, hx('#2e3a41'))
    # cornice + gutter along the row
    fr.box(B['stone'], -0.4, 0.34, v0, v1, EZ - 0.28, EZ, hx('#3a3c39'))
    fr.box(B['iron'], 0.30, 0.46, v0, v1, EZ - 0.06, EZ + 0.1)
    for v in stacks:
        fr.box(B['brick'], ridge_u - 0.36, ridge_u + 0.36, v - 0.42, v + 0.42, rz - 0.7, rz + 1.7)
        fr.box(B['stone'], ridge_u - 0.42, ridge_u + 0.42, v - 0.48, v + 0.48, rz + 1.7, rz + 1.82, STONE)
        for dv in (-0.2, 0.2):
            fr.tube(B['terra'], (ridge_u, v + dv, rz + 1.82), (ridge_u, v + dv, rz + 2.3), 0.12, 0.10, 10, None)
            fr.tube(B['terra'], (ridge_u, v + dv, rz + 2.3), (ridge_u, v + dv, rz + 2.38), 0.145, 0.145, 10, None)
    return rz


def downpipe(fr, v):
    fr.tube(B['iron'], (0.12, v, 0.0), (0.12, v, EZ), 0.045, 0.045, 8)
    for z in (1.0, 2.5, 4.0, 5.5, 7.0):
        fr.box(B['iron'], 0.0, 0.14, v - 0.05, v + 0.05, z, z + 0.05)


FLOORS = [(3.45, 5.3), (6.15, 7.75)]


def side_house(fr, v0, Wd, flip, lit_ground, lit_first, k_ground=1.0, pal=None):
    def V(t):
        return v0 + (Wd - t if flip else t)

    def span(ta, tb):
        a, b = V(ta), V(tb)
        return (min(a, b), max(a, b))

    door_t = (0.25, 1.25)
    bay_c, bay_w = 2.75, 1.9
    d0, d1 = span(*door_t)
    paint = pal if pal is not None else rng.choice([PAINT_OX, PAINT_GREEN, PAINT_TEAL, PAINT_BLACK])
    wpaint = rng.choice([PAINT_CREAM, PAINT_CREAM, hx('#8a8a7e')])
    w1 = span(0.75 - 0.43, 0.75 + 0.43)
    w2 = span(bay_c - 0.62, bay_c + 0.62)
    holes = [(d0, d1, 0.46, 3.02)]
    for (za, zb) in FLOORS:
        holes += [(w1[0], w1[1], za, zb), (w2[0], w2[1], za, zb)]
    wall_with_holes(fr, v0, v0 + Wd, -0.1, EZ - 0.2, holes)
    fr.box(B['stone'], -0.4, 0.04, v0, v0 + Wd, -0.1, 0.5, STONE)  # plinth
    fr.box(B['stone'], -0.4, 0.05, v0, v0 + Wd, 5.5, 5.62, STONE)  # string course
    fr.box(B['stone'], -0.4, 0.05, v0, v0 + Wd, 3.12, 3.22, STONE)
    door(fr, d0, d1, lit_ground and rng.random() < 0.8, 1.0, paint)
    bc = V(bay_c)
    bay(fr, bc, bay_w, 0.62, 0.46, 2.95, lit_ground, k_ground * rng.uniform(0.8, 1.2), wpaint)
    for fi, (za, zb) in enumerate(FLOORS):
        window(fr, w1[0], w1[1], za, zb, lit_first[fi][0], rng.uniform(0.7, 1.1), wpaint)
        window(fr, w2[0], w2[1], za, zb, lit_first[fi][1], rng.uniform(0.7, 1.1), wpaint)
    forecourt(fr, v0, v0 + Wd, gate=(d0 - 0.05, d1 + 0.05))


def hero_house(fr):
    v0, v1 = -2.8, 2.8
    bay_c, bay_w, depth = -1.1, 2.7, 0.8
    d0, d1 = 1.25, 2.25
    w1 = (1.3, 2.2)
    holes = [(d0, d1, 0.46, 3.02), (w1[0], w1[1], 3.45, 5.3), (w1[0], w1[1], 6.15, 7.75)]
    wall_with_holes(fr, v0, v1, -0.1, EZ - 0.2, holes)
    fr.box(B['stone'], -0.4, 0.04, v0, v1, -0.1, 0.5, STONE)
    fr.box(B['stone'], -0.4, 0.05, v0, v1, 5.5, 5.62, STONE)
    paint = PAINT_OX
    door(fr, d0, d1, True, 1.8, paint, hero=True)
    # porch lamp (small lantern over the door)
    wp = PAINT_CREAM
    # two-storey bay
    z0 = 0.46
    bay(fr, bay_c, bay_w, depth, z0, 2.95, True, 2.1, wp)
    # upper bay
    v_a, v_b = bay_c - bay_w / 2, bay_c + bay_w / 2
    fr.box(B['brick'], 0.0, depth, v_a, v_b, 3.2, 3.62)
    p = 0.09
    zg0, zg1 = 3.62, 5.5
    for v in (v_a, v_b - p):
        fr.box(B['paint'], depth - p, depth, v, v + p, zg0, zg1, wp)
    fr.box(B['paint'], depth - 0.08, depth, v_a, v_b, zg1 - 0.1, zg1, wp)
    fr.box(B['paint'], depth - 0.08, depth, v_a, v_b, zg0, zg0 + 0.07, wp)
    for f in (1 / 3, 2 / 3):
        v = v_a + bay_w * f
        fr.box(B['paint'], depth - 0.07, depth, v - 0.03, v + 0.03, zg0, zg1, wp)
    zm = zg0 + (zg1 - zg0) * 0.55
    fr.box(B['paint'], depth - 0.07, depth, v_a, v_b, zm - 0.03, zm + 0.03, wp)
    for i in range(3):
        a = v_a + p + (bay_w - 2 * p) * i / 3
        b = v_a + p + (bay_w - 2 * p) * (i + 1) / 3
        glass_quad(fr, depth - 0.1, a + 0.03, b - 0.03, zg0 + 0.07, zg1 - 0.1, i != 0, 1.0 + 0.3 * i)
    for side in (-1, 1):
        v = v_a + 0.03 if side < 0 else v_b - 0.03
        pts = [(0.02, v, zg0 + 0.07), (depth - 0.1, v, zg0 + 0.07), (depth - 0.1, v, zg1 - 0.1), (0.02, v, zg1 - 0.1)]
        fr.poly(B['glassD'], pts, (0, side, 0), col=(1, 1, 1, 1))
    fr.box(B['stone'], -0.0, depth + 0.16, v_a - 0.1, v_b + 0.1, 3.1, 3.2, STONE)
    # second floor of the bay
    fr.box(B['brick'], 0.0, depth, v_a, v_b, 5.5, 6.0)
    fr.box(B['stone'], 0.0, depth + 0.1, v_a - 0.06, v_b + 0.06, 5.5, 5.62, STONE)
    zh0, zh1 = 6.0, 7.9
    for v in (v_a, v_b - p):
        fr.box(B['paint'], depth - p, depth, v, v + p, zh0, zh1, wp)
    fr.box(B['paint'], depth - 0.08, depth, v_a, v_b, zh1 - 0.1, zh1, wp)
    fr.box(B['paint'], depth - 0.08, depth, v_a, v_b, zh0, zh0 + 0.07, wp)
    for f in (1 / 3, 2 / 3):
        v = v_a + bay_w * f
        fr.box(B['paint'], depth - 0.07, depth, v - 0.03, v + 0.03, zh0, zh1, wp)
    zm2 = zh0 + (zh1 - zh0) * 0.55
    fr.box(B['paint'], depth - 0.07, depth, v_a, v_b, zm2 - 0.03, zm2 + 0.03, wp)
    for i in range(3):
        a = v_a + p + (bay_w - 2 * p) * i / 3
        b = v_a + p + (bay_w - 2 * p) * (i + 1) / 3
        glass_quad(fr, depth - 0.1, a + 0.03, b - 0.03, zh0 + 0.07, zh1 - 0.1, i == 1, 1.1)
    for side in (-1, 1):
        v = v_a + 0.03 if side < 0 else v_b - 0.03
        pts = [(0.02, v, zh0 + 0.07), (depth - 0.1, v, zh0 + 0.07), (depth - 0.1, v, zh1 - 0.1), (0.02, v, zh1 - 0.1)]
        fr.poly(B['glassD'], pts, (0, side, 0), col=(1, 1, 1, 1))
    fr.box(B['stone'], 0.0, depth + 0.18, v_a - 0.12, v_b + 0.12, 7.9, 8.12, STONE)
    window(fr, w1[0], w1[1], 3.45, 5.3, True, 0.8, wp)
    window(fr, w1[0], w1[1], 6.15, 7.75, False, 0.8, wp)
    # gable over the bay: plaster triangle with dark timber, slate sides
    gz0 = 8.12
    gv0, gv1 = v_a - 0.12, v_b + 0.12
    gh = (gv1 - gv0) / 2 * 0.78
    gvc = (gv0 + gv1) / 2
    uf = depth + 0.1
    fr.poly(B['plaster'], [(uf, gv0, gz0), (uf, gv1, gz0), (uf, gvc, gz0 + gh)], (1, 0, 0), col=(1, 1, 1, 1))
    tim = hx('#1e1a16')
    fr.box(B['wood'], uf, uf + 0.05, gvc - 0.05, gvc + 0.05, gz0, gz0 + gh - 0.15, tim)
    fr.box(B['wood'], uf, uf + 0.05, gv0, gv1, gz0 + 0.0, gz0 + 0.12, tim)
    fr.box(B['wood'], uf, uf + 0.05, gv0 + 0.5, gv1 - 0.5, gz0 + 0.62, gz0 + 0.70, tim)
    # attic window (lit)
    glass_quad(fr, uf + 0.01, gvc - 0.22, gvc + 0.22, gz0 + 0.18, gz0 + 0.62, True, 1.4, grad=False, col=(1.0, 0.6, 0.25))
    for dv in (-0.22, 0.0, 0.22):
        fr.box(B['wood'], uf + 0.01, uf + 0.045, gvc + dv - 0.015, gvc + dv + 0.015, gz0 + 0.18, gz0 + 0.62, tim)
    fr.box(B['wood'], uf + 0.01, uf + 0.045, gvc - 0.24, gvc + 0.24, gz0 + 0.38, gz0 + 0.41, tim)
    # roof of the gable
    ov = 0.18
    sect_v = [(gv0 - ov, gz0 - 0.1), (gvc, gz0 + gh + ov * 0.78 + 0.0), (gv1 + ov, gz0 - 0.1)]
    ub, ue = uf + 0.28, -1.9
    # build prism extruded along u: use polys directly
    L = [(ub, sect_v[0][0], sect_v[0][1]), (ub, sect_v[1][0], sect_v[1][1]), (ub, sect_v[2][0], sect_v[2][1])]
    Lb = [(ue, p_[1], p_[2]) for p_ in L]
    cen = (0, gvc, gz0 + 0.5)
    slc = hx('#2e3a41')
    for i in range(3):
        j = (i + 1) % 3
        q = [L[i], L[j], Lb[j], Lb[i]]
        fr.poly(B['slate'], q, fr._away(q, cen), col=slc)
    fr.poly(B['slate'], L, (1, 0, 0), col=slc)
    # bargeboards (dark), along the two sloped edges at the front
    for sgn in (-1, 1):
        a = (ub + 0.02, sect_v[1][0], sect_v[1][1])
        b = (ub + 0.02, sect_v[0][0] if sgn < 0 else sect_v[2][0], sect_v[0][1])
        fr.beam(B['wood'], a, b, 0.045, tim)
    forecourt(fr, v0, v1, gate=(d0 - 0.05, d1 + 0.05))


LAMPS = [(-2.45, 5.2), (2.45, 8.4), (-2.45, 11.4)]


# ----------------------------------------------------------------- build the rows
def build_buildings():
    # side rows
    for side, fr in (('L', frame_left()), ('R', frame_right())):
        y = 3.0
        nh = int(round((FY - 3.0) / HW))
        plan = {'L': [(False, [[False, False], [False, False]], 1.0),
                      (True, [[False, True], [False, False]], 0.85),
                      (False, [[False, False], [True, False]], 1.0)],
                'R': [(True, [[False, False], [False, False]], 0.55),
                      (False, [[True, False], [False, False]], 1.0),
                      (True, [[False, False], [False, True]], 1.0)]}[side]
        for i in range(nh):
            lit_g, lit_f, kg = plan[i]
            side_house(fr, y, HW, flip=(i % 2 == 1), lit_ground=lit_g, lit_first=lit_f, k_ground=kg)
            y += HW
        stacks = [3.0 + HW * i for i in range(1, nh + 1)]
        roof_and_stacks(fr, 3.0, FY, stacks)
        for i in range(0, nh + 1):
            downpipe(fr, 3.0 + HW * i + (0.06 if i < nh else -0.06))
    # end row
    fe = frame_end()
    hero_house(fe)
    for (v0, flip, lg, lf) in ((-6.8, False, True, [[True, False], [False, False]]), (2.8, True, False, [[False, True], [False, False]])):
        side_house(fe, v0, HW, flip, lg, lf, 0.9)
    roof_and_stacks(fe, -6.8, 6.8, [-2.8, 2.8])
    for v in (-2.75, 2.75, -6.75, 6.75):
        downpipe(fe, v)


def build_ground():
    S = B['flag']
    # pavements
    for sx in (-1, 1):
        x0, x1 = sorted((sx * RD, sx * PVX))
        S.box(x0, x1, -3.0, FY - DW, -0.3, 0.13)
    S.box(-PVX, PVX, KERB_Y, FY - DW, -0.3, 0.13)
    # forecourt earth beyond (handled per house); fill up to the walls
    K = B['stone']
    for sx in (-1, 1):
        x0, x1 = sorted((sx * RD, sx * (RD + 0.14)))
        K.box(x0, x1, -3.0, KERB_Y, -0.3, 0.15, STONE)
    K.box(-RD - 0.14, RD + 0.14, KERB_Y - 0.14, KERB_Y, -0.3, 0.15, STONE)
    # the road under the cobbles
    B['grit'].box(-RD - 0.1, RD + 0.1, -3.0, KERB_Y, -0.5, -0.075)
    # earth behind pavements near the camera (out of sight but catches bounce)
    # lamps
    lamps = LAMPS
    for (x, y) in lamps:
        I = B['iron']
        I.tube((x, y, 0.13), (x, y, 0.75), 0.17, 0.12, 8)
        I.tube((x, y, 0.75), (x, y, 0.95), 0.14, 0.12, 8)
        I.tube((x, y, 0.95), (x, y, 3.0), 0.07, 0.045, 8)
        I.tube((x, y, 2.4), (x, y, 2.5), 0.1, 0.1, 8)
        I.box(x - 0.025, x + 0.025, y - 0.5, y + 0.5, 2.55, 2.6) if False else None
        # lantern
        zb, zt = 3.0, 3.55
        I.tube((x, y, zb - 0.1), (x, y, zb + 0.02), 0.07, 0.07, 8)
        for (dx, dy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            I.beam((x + dx * 0.17, y + dy * 0.17, zb), (x + dx * 0.24, y + dy * 0.24, zt), 0.014)
        I.tube((x, y, zt), (x, y, zt + 0.22), 0.30, 0.03, 4, None)
        I.tube((x, y, zt + 0.22), (x, y, zt + 0.34), 0.03, 0.03, 6)
        I.box(x - 0.27, x + 0.27, y - 0.27, y + 0.27, zt - 0.02, zt + 0.02)
        G = B['lampglass']
        for (dx, dy, ax) in ((-1, 0, 'x'), (1, 0, 'x'), (0, -1, 'y'), (0, 1, 'y')):
            a0 = 0.15 if True else 0
            for q in [0]:
                pass
        # glass as a small tapered tube (so it lights from all sides)
        G.tube((x, y, zb + 0.04), (x, y, zt - 0.02), 0.16, 0.22, 4, None, caps=True)


def build_cobbles():
    C = MB()
    y = -2.6
    row = 0
    while y < KERB_Y - 0.01:
        rl = rng.uniform(0.10, 0.145)
        x = -RD - 0.04 - rng.uniform(0, 0.18)
        while x < RD + 0.04:
            wd = rng.uniform(0.12, 0.23)
            x0, x1 = x + 0.006, x + wd - 0.006
            y0, y1 = y + 0.006, y + rl - 0.006
            xc = (x0 + x1) / 2
            cam = -0.055 * (xc / RD) ** 2
            if x1 > -RD and x0 < RD:
                x0c, x1c = max(x0, -RD), min(x1, RD)
                if x1c - x0c > 0.03:
                    x0, x1 = x0c, x1c
                    t = rng.random()
                    tone = hx('#2e3a42')
                    if t < 0.22: tone = hx('#423f3d')
                    elif t < 0.4: tone = hx('#222d35')
                    elif t < 0.48: tone = hx('#4a3a32')
                    sh = rng.uniform(0.7, 1.25)
                    col = (tone[0] * sh, tone[1] * sh, tone[2] * sh, rng.random())
                    ins = 0.022
                    zt = cam + rng.uniform(-0.006, 0.004)
                    zb = zt - 0.02
                    ring0 = [(x0, y0, zt - 0.12), (x1, y0, zt - 0.12), (x1, y1, zt - 0.12), (x0, y1, zt - 0.12)]
                    ring1 = [(x0, y0, zb), (x1, y0, zb), (x1, y1, zb), (x0, y1, zb)]
                    ring2 = [(x0 + ins, y0 + ins, zt + rng.uniform(-.002, .002)), (x1 - ins, y0 + ins, zt + rng.uniform(-.002, .002)),
                             (x1 - ins, y1 - ins, zt + rng.uniform(-.002, .002)), (x0 + ins, y1 - ins, zt + rng.uniform(-.002, .002))]
                    cen = ((x0 + x1) / 2, (y0 + y1) / 2, zt + rng.uniform(0.001, 0.005))
                    ang = rng.uniform(-0.10, 0.10)
                    ca_, sa_ = math.cos(ang), math.sin(ang)
                    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2

                    def R_(p):
                        dx, dy = p[0] - xm, p[1] - ym
                        return (xm + dx * ca_ - dy * sa_, ym + dx * sa_ + dy * ca_, p[2])
                    ring0 = [R_(p) for p in ring0]
                    ring1 = [R_(p) for p in ring1]
                    ring2 = [R_(p) for p in ring2]
                    cen = R_(cen)
                    for i in range(4):
                        j = (i + 1) % 4
                        C.add([ring0[i], ring0[j], ring1[j], ring1[i]], col)
                        C.add([ring1[i], ring1[j], ring2[j], ring2[i]], col)
                        C.add([ring2[i], ring2[j], cen], col)
            x += wd
        y += rl
        row += 1
    return C


def build_puddles():
    P = MB()
    specs = [(-0.9, 2.4, 0.3, 0.5), (0.85, 2.0, 0.28, 0.5), (0.55, 3.4, 0.5, 0.9), (-0.15, 7.6, 0.85, 2.0), (-1.1, 9.8, 0.4, 1.0),
             (1.0, 10.8, 0.45, 1.2), (0.2, 12.0, 0.8, 1.0), (-0.6, 4.4, 0.3, 0.5)]
    for (cx, cy, rx, ry) in specs:
        n = 28
        ph = [rng.uniform(0, 6.28) for _ in range(3)]
        pts = []
        z = -0.055 * (cx / RD) ** 2 + 0.018
        for i in range(n):
            t = 2 * math.pi * i / n
            rr = 1 + 0.22 * math.sin(2 * t + ph[0]) + 0.14 * math.sin(3 * t + ph[1]) + 0.08 * math.sin(5 * t + ph[2])
            px = cx + rx * rr * math.cos(t)
            py = cy + ry * rr * math.sin(t)
            if abs(px) > RD - 0.03: px = math.copysign(RD - 0.03, px)
            pts.append((px, py, z))
        for i in range(n):
            j = (i + 1) % n
            P.add([(cx, cy, z), pts[i], pts[j]], (1, 1, 1, 1))
    # water running in the gutters, broken into lengths
    for sx in (-1, 1):
        y = 0.4
        while y < KERB_Y - 1.0:
            ln = rng.uniform(1.2, 3.2)
            xs = sx * (RD - 0.13)
            npt = 10
            L, R = [], []
            for i in range(npt + 1):
                t = i / npt
                yy = y + ln * t
                wdt = 0.05 + 0.10 * math.sin(math.pi * t) ** 0.7 * rng.uniform(0.8, 1.2)
                xc = xs + 0.02 * math.sin(yy * 3.1)
                z = -0.055 * (xc / RD) ** 2 + 0.014
                L.append((xc - wdt, yy, z))
                R.append((xc + wdt, yy, z))
            for i in range(npt):
                P.add([L[i], R[i], R[i + 1], L[i + 1]], (1, 1, 1, 1))
            y += ln + rng.uniform(0.8, 2.5)
    # fallen leaves (it is November) and coal lumps lying on the setts
    for i in range(46):
        lx = rng.uniform(-RD + 0.15, RD - 0.15)
        ly = rng.uniform(-0.6, 9.0)
        a = rng.uniform(0, 6.28)
        sz = rng.uniform(0.045, 0.085)
        z = -0.055 * (lx / RD) ** 2 + 0.006
        c = rng.choice([hx('#8a4a1c'), hx('#a8702a'), hx('#5a3418'), hx('#704018'), hx('#3a2a18')])
        pts = []
        for (px_, py_) in ((-1.0, 0.0), (-0.3, 0.55), (0.6, 0.45), (1.0, 0.0), (0.6, -0.45), (-0.3, -0.55)):
            pts.append((lx + sz * (px_ * math.cos(a) - py_ * math.sin(a)) * 1.2,
                        ly + sz * (px_ * math.sin(a) + py_ * math.cos(a)) * 1.2, z))
        B['wood'].add(pts[::-1], (c[0], c[1], c[2], 1.0))
    for i in range(40):
        lx = rng.choice([-1, 1]) * rng.uniform(RD - 0.45, RD - 0.05)
        ly = rng.uniform(-0.6, 10.0)
        s_ = rng.uniform(0.02, 0.05)
        z = -0.055 * (lx / RD) ** 2
        B['earth'].box(lx - s_, lx + s_, ly - s_ * 0.8, ly + s_ * 0.8, z, z + s_ * 1.2, hx('#0a0a0b'))
    return P


def merge_rot(dst, src, ang, X, Y):
    ca, sa = math.cos(ang), math.sin(ang)
    off = len(dst.v)
    for (x, y, z) in src.v:
        dx, dy = x - X, y - Y
        dst.v.append((X + dx * ca - dy * sa, Y + dx * sa + dy * ca, z))
    for f in src.f:
        dst.f.append(tuple(i + off for i in f))
    dst.c.extend(src.c)


def build_cart():
    """a coal handcart pulled up crooked in the road: scale from a thing people use"""
    X, Y, ANG = 0.3, 6.3, math.radians(38)
    I, Wd, E = MB(), MB(), MB()
    wood = hx('#4a3424')
    Wd.box(X - 0.55, X + 0.55, Y - 0.8, Y + 0.8, 0.62, 0.70, wood)
    for sx in (-1, 1):
        Wd.box(X + sx * 0.55 - 0.03, X + sx * 0.55 + 0.03, Y - 0.8, Y + 0.8, 0.70, 1.02, wood)
    Wd.box(X - 0.55, X + 0.55, Y - 0.83, Y - 0.77, 0.70, 1.02, wood)
    Wd.box(X - 0.55, X + 0.55, Y + 0.77, Y + 0.83, 0.70, 0.9, wood)
    # coal heap
    for i in range(70):
        cx = X + rng.uniform(-0.48, 0.48)
        cy = Y + rng.uniform(-0.74, 0.74)
        h = 0.95 + 0.28 * (1 - (abs(cx - X) / 0.55) ** 2) * (1 - (abs(cy - Y) / 0.85) ** 2) + rng.uniform(0, 0.06)
        s_ = rng.uniform(0.05, 0.11)
        E.box(cx - s_, cx + s_, cy - s_, cy + s_, 0.7, h, hx('#101012'))
    # shafts
    for sx in (-1, 1):
        Wd.beam((X + sx * 0.4, Y + 0.7, 0.66), (X + sx * 0.4, Y + 2.2, 0.12), 0.04, wood)
    # wheels (axis along x)
    for sx in (-1, 1):
        xw = X + sx * 0.66
        R = 0.5
        zc = R
        nseg = 20
        for i in range(nseg):
            a0 = 2 * math.pi * i / nseg
            a1 = 2 * math.pi * (i + 1) / nseg
            I.beam((xw, Y + R * math.cos(a0), zc + R * math.sin(a0)), (xw, Y + R * math.cos(a1), zc + R * math.sin(a1)), 0.05)
        for i in range(12):
            a0 = 2 * math.pi * i / 12
            Wd.beam((xw, Y, zc), (xw, Y + (R - 0.03) * math.cos(a0), zc + (R - 0.03) * math.sin(a0)), 0.032, wood)
        I.tube((xw - 0.09, Y, zc), (xw + 0.09, Y, zc), 0.07, 0.07, 8)
    I.beam((X - 0.7, Y, 0.5), (X + 0.7, Y, 0.5), 0.025)
    merge_rot(B['iron'], I, ANG, X, Y)
    merge_rot(B['wood'], Wd, ANG, X, Y)
    merge_rot(B['earth'], E, ANG, X, Y)


def build_bin():
    # dustbin and a milk crate by the hero gate give another human scale
    x, y = 2.45, FY - DW - 0.6
    I = B['iron']
    I.tube((x, y, 0.13), (x, y, 0.78), 0.2, 0.22, 12)
    I.tube((x, y, 0.78), (x, y, 0.83), 0.24, 0.2, 12)


# ----------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out


def nd(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def lk(nt, a, b):
    nt.links.new(a, b)


def rgba(c):
    return (c[0], c[1], c[2], 1.0)


def planar(nt, sx=1.0):
    tc = nd(nt, 'ShaderNodeTexCoord')
    sp = nd(nt, 'ShaderNodeSeparateXYZ')
    ad = nd(nt, 'ShaderNodeMath', operation='ADD')
    cb = nd(nt, 'ShaderNodeCombineXYZ')
    lk(nt, tc.outputs['Object'], sp.inputs[0])
    lk(nt, sp.outputs[0], ad.inputs[0])
    lk(nt, sp.outputs[1], ad.inputs[1])
    lk(nt, ad.outputs[0], cb.inputs[0])
    lk(nt, sp.outputs[2], cb.inputs[1])
    return cb.outputs[0], sp, tc


def ramp(nt, stops, inp=None):
    r = nd(nt, 'ShaderNodeValToRGB')
    el = r.color_ramp.elements
    while len(el) > len(stops):
        el.remove(el[-1])
    while len(el) < len(stops):
        el.new(0.5)
    for e, (p, c) in zip(el, stops):
        e.position = p
        e.color = c if len(c) == 4 else (c[0], c[1], c[2], 1.0)
    if inp is not None:
        lk(nt, inp, r.inputs['Fac'])
    return r


def mix_col(nt, fac, a, b):
    m = nd(nt, 'ShaderNodeMix', data_type='RGBA')
    if isinstance(fac, (int, float)):
        m.inputs[0].default_value = fac
    else:
        lk(nt, fac, m.inputs[0])
    for idx, v in ((6, a), (7, b)):
        if isinstance(v, tuple):
            m.inputs[idx].default_value = rgba(v)
        else:
            lk(nt, v, m.inputs[idx])
    return m.outputs[2]


def mulc(nt, a, b, fac=1.0):
    m = nd(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    m.inputs[0].default_value = fac
    for idx, v in ((6, a), (7, b)):
        if isinstance(v, tuple):
            m.inputs[idx].default_value = rgba(v)
        else:
            lk(nt, v, m.inputs[idx])
    return m.outputs[2]


def maprange(nt, val, a0, a1, b0, b1, clamp=True):
    m = nd(nt, 'ShaderNodeMapRange')
    m.clamp = clamp
    lk(nt, val, m.inputs[0])
    m.inputs[1].default_value = a0
    m.inputs[2].default_value = a1
    m.inputs[3].default_value = b0
    m.inputs[4].default_value = b1
    return m.outputs[0]


def noise(nt, vec, scale, detail=4.0, rough=0.55, dist=0.0):
    n = nd(nt, 'ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = dist
    lk(nt, vec, n.inputs['Vector'])
    return n.outputs['Fac']


def principled(nt, out, base, rough, metallic=0.0, normal=None, spec=0.5):
    p = nd(nt, 'ShaderNodeBsdfPrincipled')
    if isinstance(base, tuple):
        p.inputs['Base Color'].default_value = rgba(base)
    else:
        lk(nt, base, p.inputs['Base Color'])
    if isinstance(rough, (int, float)):
        p.inputs['Roughness'].default_value = rough
    else:
        lk(nt, rough, p.inputs['Roughness'])
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Specular IOR Level'].default_value = spec
    if normal is not None:
        lk(nt, normal, p.inputs['Normal'])
    lk(nt, p.outputs[0], out.inputs['Surface'])
    return p


def grime_masks(nt, vec3, planarv, zsock, damp=0.55):
    """returns (grime mask 0..1, wet-streak mask) in object space"""
    # stretched noise for runs: use planar coordinates, squeezed along the run
    mp = nd(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (3.5, 0.55, 1.0)
    lk(nt, planarv, mp.inputs['Vector'])
    n1 = noise(nt, mp.outputs[0], 2.0, 5.0, 0.6, 0.4)
    runs = maprange(nt, n1, 0.42, 0.72, 0.0, 1.0)
    low = maprange(nt, zsock, 0.0, 2.6, 1.0, 0.0)
    soot = maprange(nt, zsock, 5.0, 6.3, 0.0, 0.6)
    n2 = noise(nt, vec3, 1.3, 3.0, 0.5)
    blot = maprange(nt, n2, 0.4, 0.7, 0.0, 0.5)
    m1 = nd(nt, 'ShaderNodeMath', operation='MAXIMUM')
    lk(nt, low, m1.inputs[0]); m1.inputs[1].default_value = 0.0
    sc = nd(nt, 'ShaderNodeMath', operation='MULTIPLY')
    lk(nt, low, sc.inputs[0]); sc.inputs[1].default_value = damp
    m2 = nd(nt, 'ShaderNodeMath', operation='ADD')
    lk(nt, sc.outputs[0], m2.inputs[0]); lk(nt, soot, m2.inputs[1])
    m3 = nd(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    lk(nt, m2.outputs[0], m3.inputs[0])
    rs = nd(nt, 'ShaderNodeMath', operation='MULTIPLY')
    lk(nt, runs, rs.inputs[0]); rs.inputs[1].default_value = 0.8
    m4 = nd(nt, 'ShaderNodeMath', operation='ADD')
    lk(nt, m3.outputs[0], m4.inputs[0]); lk(nt, rs.outputs[0], m4.inputs[1])
    m5 = nd(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True)
    lk(nt, m4.outputs[0], m5.inputs[0]); lk(nt, blot, m5.inputs[1])
    return m5.outputs[0], runs


def ao_factor(nt, dist=0.5, strength=0.6):
    ao = nd(nt, 'ShaderNodeAmbientOcclusion', samples=4)
    ao.inputs['Distance'].default_value = dist
    return maprange(nt, ao.outputs['AO'], 0.0, 1.0, 1.0 - strength, 1.0)


def mat_brick():
    m, nt, out = new_mat('brick')
    pv, sp, tc = planar(nt)
    z = sp.outputs[2]
    br = nd(nt, 'ShaderNodeTexBrick', offset=0.5, offset_frequency=2)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 0.235
    br.inputs['Row Height'].default_value = 0.077
    br.inputs['Mortar Size'].default_value = 0.016
    br.inputs['Mortar Smooth'].default_value = 0.15
    br.inputs['Color1'].default_value = rgba(hx('#a0553a'))
    br.inputs['Color2'].default_value = rgba(hx('#5c3028'))
    br.inputs['Mortar'].default_value = rgba(hx('#5c5a52'))
    br.inputs['Bias'].default_value = 0.1
    lk(nt, pv, br.inputs['Vector'])
    gr, runs = grime_masks(nt, tc.outputs['Object'], pv, z, 0.7)
    nb = noise(nt, tc.outputs['Object'], 3.0, 4.0, 0.5)
    tint = mix_col(nt, maprange(nt, nb, 0.35, 0.65, 0.0, 1.0), (0.85, 0.85, 0.85), (1.25, 1.1, 1.0))
    base = mulc(nt, br.outputs[0], tint)
    soot = (0.018, 0.017, 0.017)
    col = mix_col(nt, gr, base, soot)
    col = mulc(nt, col, ao_factor(nt, 0.6, 0.55))
    bump = nd(nt, 'ShaderNodeBump', invert=True)
    bump.inputs['Strength'].default_value = 0.9
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, br.outputs[1], bump.inputs['Height'])
    bn = noise(nt, tc.outputs['Object'], 60.0, 3.0, 0.6)
    bump2 = nd(nt, 'ShaderNodeBump')
    bump2.inputs['Strength'].default_value = 0.25
    bump2.inputs['Distance'].default_value = 0.01
    lk(nt, bn, bump2.inputs['Height'])
    lk(nt, bump.outputs[0], bump2.inputs['Normal'])
    rough = maprange(nt, runs, 0.0, 1.0, 0.85, 0.42)
    principled(nt, out, col, rough, 0.0, bump2.outputs[0], 0.4)
    return m


def mat_slate():
    m, nt, out = new_mat('slate')
    pv, sp, tc = planar(nt)
    mp = nd(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.7, 1.0)
    lk(nt, pv, mp.inputs['Vector'])
    br = nd(nt, 'ShaderNodeTexBrick', offset=0.5, offset_frequency=2)
    br.inputs['Brick Width'].default_value = 0.32
    br.inputs['Row Height'].default_value = 0.2
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Color1'].default_value = rgba(hx('#2c3c43'))
    br.inputs['Color2'].default_value = rgba(hx('#121a20'))
    br.inputs['Mortar'].default_value = rgba(hx('#0a0f12'))
    br.inputs['Bias'].default_value = 0.0
    lk(nt, mp.outputs[0], br.inputs['Vector'])
    n = noise(nt, tc.outputs['Object'], 0.9, 3.0, 0.5)
    tint = mix_col(nt, maprange(nt, n, 0.3, 0.7, 0.0, 1.0), (0.8, 0.85, 0.9), (1.3, 1.3, 1.25))
    col = mulc(nt, br.outputs[0], tint)
    bump = nd(nt, 'ShaderNodeBump', invert=True)
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, br.outputs[1], bump.inputs['Height'])
    principled(nt, out, col, 0.28, 0.0, bump.outputs[0], 0.5)
    return m


def mat_flag():
    m, nt, out = new_mat('flag')
    pv = nd(nt, 'ShaderNodeCombineXYZ')
    tc = nd(nt, 'ShaderNodeTexCoord')
    sp = nd(nt, 'ShaderNodeSeparateXYZ')
    ad = nd(nt, 'ShaderNodeMath', operation='ADD')
    lk(nt, tc.outputs['Object'], sp.inputs[0])
    lk(nt, sp.outputs[1], ad.inputs[0]); lk(nt, sp.outputs[2], ad.inputs[1])
    lk(nt, sp.outputs[0], pv.inputs[0]); lk(nt, ad.outputs[0], pv.inputs[1])
    br = nd(nt, 'ShaderNodeTexBrick', offset=0.5, offset_frequency=1)
    br.inputs['Brick Width'].default_value = 0.9
    br.inputs['Row Height'].default_value = 0.6
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Color1'].default_value = rgba(hx('#59615f'))
    br.inputs['Color2'].default_value = rgba(hx('#3b4547'))
    br.inputs['Mortar'].default_value = rgba(hx('#14181a'))
    lk(nt, pv.outputs[0], br.inputs['Vector'])
    n = noise(nt, tc.outputs['Object'], 6.0, 5.0, 0.6)
    dirt = mix_col(nt, maprange(nt, n, 0.4, 0.75, 0.0, 0.8), br.outputs[0], hx('#14110e'))
    col = mulc(nt, dirt, ao_factor(nt, 0.4, 0.5))
    wet = maprange(nt, n, 0.35, 0.65, 0.12, 0.45)
    bump = nd(nt, 'ShaderNodeBump', invert=True)
    bump.inputs['Strength'].default_value = 0.7
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, br.outputs[1], bump.inputs['Height'])
    principled(nt, out, col, wet, 0.0, bump.outputs[0], 0.6)
    return m


def mat_stone():
    m, nt, out = new_mat('stone')
    tc = nd(nt, 'ShaderNodeTexCoord')
    sp = nd(nt, 'ShaderNodeSeparateXYZ')
    lk(nt, tc.outputs['Object'], sp.inputs[0])
    vc = nd(nt, 'ShaderNodeVertexColor', layer_name='Col')
    n = noise(nt, tc.outputs['Object'], 9.0, 6.0, 0.6)
    n2 = noise(nt, tc.outputs['Object'], 1.4, 3.0, 0.5)
    col = mulc(nt, vc.outputs[0], mix_col(nt, maprange(nt, n, 0.3, 0.7, 0.0, 1.0), (0.7, 0.72, 0.72), (1.2, 1.2, 1.15)))
    low = maprange(nt, sp.outputs[2], 0.0, 1.0, 0.8, 0.0)
    col = mix_col(nt, maprange(nt, n2, 0.45, 0.7, 0.0, 0.7), col, (0.03, 0.03, 0.03))
    col = mix_col(nt, low, col, (0.02, 0.022, 0.02))
    col = mulc(nt, col, ao_factor(nt, 0.35, 0.5))
    bump = nd(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.5
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, noise(nt, tc.outputs['Object'], 45.0, 4.0, 0.6), bump.inputs['Height'])
    bev = nd(nt, 'ShaderNodeBevel', samples=3)
    bev.inputs['Radius'].default_value = 0.015
    lk(nt, bev.outputs[0], bump.inputs['Normal'])
    principled(nt, out, col, 0.45, 0.0, bump.outputs[0], 0.5)
    return m


def mat_paint():
    m, nt, out = new_mat('paint')
    tc = nd(nt, 'ShaderNodeTexCoord')
    vc = nd(nt, 'ShaderNodeVertexColor', layer_name='Col')
    n = noise(nt, tc.outputs['Object'], 14.0, 6.0, 0.65, 0.3)
    peel = maprange(nt, n, 0.52, 0.62, 0.0, 1.0)
    wood = hx('#3b3328')
    col = mix_col(nt, peel, vc.outputs[0], wood)
    n2 = noise(nt, tc.outputs['Object'], 2.5, 3.0, 0.5)
    col = mix_col(nt, maprange(nt, n2, 0.4, 0.72, 0.0, 0.65), col, (0.02, 0.02, 0.02))
    col = mulc(nt, col, ao_factor(nt, 0.2, 0.5))
    bev = nd(nt, 'ShaderNodeBevel', samples=3)
    bev.inputs['Radius'].default_value = 0.01
    principled(nt, out, col, 0.5, 0.0, bev.outputs[0], 0.5)
    return m


def mat_plaster():
    m, nt, out = new_mat('plaster')
    tc = nd(nt, 'ShaderNodeTexCoord')
    n = noise(nt, tc.outputs['Object'], 18.0, 6.0, 0.65)
    n2 = noise(nt, tc.outputs['Object'], 2.2, 3.0, 0.5)
    base = mix_col(nt, maprange(nt, n, 0.35, 0.65, 0.0, 1.0), hx('#7d7766'), hx('#a49c86'))
    col = mix_col(nt, maprange(nt, n2, 0.4, 0.7, 0.0, 0.7), base, (0.03, 0.03, 0.03))
    bump = nd(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.4
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, noise(nt, tc.outputs['Object'], 70.0, 3.0, 0.6), bump.inputs['Height'])
    principled(nt, out, col, 0.75, 0.0, bump.outputs[0], 0.3)
    return m


def mat_iron():
    m, nt, out = new_mat('iron')
    tc = nd(nt, 'ShaderNodeTexCoord')
    n = noise(nt, tc.outputs['Object'], 25.0, 6.0, 0.65, 0.2)
    rust = maprange(nt, n, 0.44, 0.60, 0.0, 1.0)
    col = mix_col(nt, rust, hx('#14181b'), hx('#7a3a1a'))
    col = mulc(nt, col, ao_factor(nt, 0.2, 0.4))
    rough = maprange(nt, rust, 0.0, 1.0, 0.4, 0.7)
    met = maprange(nt, rust, 0.0, 1.0, 0.7, 0.2)
    p = principled(nt, out, col, rough, 0.0, None, 0.5)
    lk(nt, met, p.inputs['Metallic'])
    return m


def mat_glass_lit(strength=7.0):
    m, nt, out = new_mat('glass_lit')
    vc = nd(nt, 'ShaderNodeVertexColor', layer_name='Col')
    tc = nd(nt, 'ShaderNodeTexCoord')
    # slight unevenness: curtains / panes
    n = noise(nt, tc.outputs['Object'], 30.0, 2.0, 0.5)
    f = maprange(nt, n, 0.3, 0.7, 0.8, 1.15)
    col = nd(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    col.inputs[0].default_value = 1.0
    lk(nt, vc.outputs[0], col.inputs[6])
    lk(nt, f, col.inputs[7]) if False else None
    col.inputs[7].default_value = (1, 1, 1, 1)
    em = nd(nt, 'ShaderNodeEmission')
    em.inputs['Strength'].default_value = strength
    lk(nt, col.outputs[2], em.inputs['Color'])
    lk(nt, em.outputs[0], out.inputs['Surface'])
    return m


def mat_glass_dark():
    m, nt, out = new_mat('glass_dark')
    p = principled(nt, out, hx('#0a1418'), 0.04, 0.0, None, 0.8)
    p.inputs['IOR'].default_value = 1.5
    return m


def mat_terra():
    m, nt, out = new_mat('terra')
    tc = nd(nt, 'ShaderNodeTexCoord')
    n = noise(nt, tc.outputs['Object'], 20.0, 5.0, 0.6)
    col = mix_col(nt, maprange(nt, n, 0.35, 0.65, 0.0, 1.0), hx('#8a4a2a'), hx('#3a2418'))
    principled(nt, out, col, 0.75, 0.0, None, 0.3)
    return m


def mat_brass():
    m, nt, out = new_mat('brass')
    p = principled(nt, out, hx('#b88a3a'), 0.3, 1.0, None, 0.5)
    return m


def mat_earth():
    m, nt, out = new_mat('earth')
    tc = nd(nt, 'ShaderNodeTexCoord')
    vc = nd(nt, 'ShaderNodeVertexColor', layer_name='Col')
    n = noise(nt, tc.outputs['Object'], 8.0, 6.0, 0.6)
    col = mix_col(nt, maprange(nt, n, 0.3, 0.7, 0.0, 1.0), hx('#1a1612'), hx('#2e261c'))
    col = mulc(nt, col, vc.outputs[0])
    bump = nd(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.02
    lk(nt, noise(nt, tc.outputs['Object'], 50.0, 4.0, 0.6), bump.inputs['Height'])
    principled(nt, out, col, 0.65, 0.0, bump.outputs[0], 0.4)
    return m


def mat_wood():
    m, nt, out = new_mat('wood')
    tc = nd(nt, 'ShaderNodeTexCoord')
    vc = nd(nt, 'ShaderNodeVertexColor', layer_name='Col')
    n = noise(nt, tc.outputs['Object'], 15.0, 5.0, 0.6)
    col = mulc(nt, vc.outputs[0], mix_col(nt, maprange(nt, n, 0.3, 0.7, 0.0, 1.0), (0.7, 0.7, 0.7), (1.3, 1.25, 1.2)))
    principled(nt, out, col, 0.6, 0.0, None, 0.4)
    return m


def mat_cobble():
    m, nt, out = new_mat('cobble')
    tc = nd(nt, 'ShaderNodeTexCoord')
    vc = nd(nt, 'ShaderNodeVertexColor', layer_name='Col')
    n = noise(nt, tc.outputs['Object'], 7.0, 5.0, 0.6)
    n2 = noise(nt, tc.outputs['Object'], 1.1, 3.0, 0.5)
    col = mulc(nt, vc.outputs[0], mix_col(nt, maprange(nt, n, 0.3, 0.7, 0.0, 1.0), (0.75, 0.78, 0.82), (1.3, 1.25, 1.15)))
    col = mix_col(nt, maprange(nt, n2, 0.45, 0.75, 0.0, 0.5), col, hx('#100e0c'))
    # wetness: shiny where the second noise is low
    wn = maprange(nt, noise(nt, tc.outputs['Object'], 0.7, 2.0, 0.5), 0.3, 0.65, 0.0, 1.0)
    wm = nd(nt, 'ShaderNodeMath', operation='MULTIPLY')
    lk(nt, vc.outputs['Alpha'], wm.inputs[0]); lk(nt, wn, wm.inputs[1])
    wet = maprange(nt, wm.outputs[0], 0.0, 0.7, 0.10, 0.42)
    bump = nd(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, noise(nt, tc.outputs['Object'], 55.0, 4.0, 0.6), bump.inputs['Height'])
    bev = nd(nt, 'ShaderNodeBevel', samples=4)
    bev.inputs['Radius'].default_value = 0.022
    lk(nt, bev.outputs[0], bump.inputs['Normal'])
    principled(nt, out, col, wet, 0.0, bump.outputs[0], 0.6)
    return m


def mat_puddle():
    m, nt, out = new_mat('puddle')
    tc = nd(nt, 'ShaderNodeTexCoord')
    bump = nd(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.03
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, noise(nt, tc.outputs['Object'], 25.0, 2.0, 0.5), bump.inputs['Height'])
    fr_ = nd(nt, 'ShaderNodeFresnel')
    fr_.inputs['IOR'].default_value = 1.33
    lk(nt, bump.outputs[0], fr_.inputs['Normal'])
    gl = nd(nt, 'ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.025
    gl.inputs['Color'].default_value = (0.85, 0.92, 1.0, 1.0)
    lk(nt, bump.outputs[0], gl.inputs['Normal'])
    tr = nd(nt, 'ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (0.42, 0.52, 0.58, 1.0)
    mx = nd(nt, 'ShaderNodeMixShader')
    fa = maprange(nt, fr_.outputs[0], 0.0, 1.0, 0.04, 1.0)
    lk(nt, fa, mx.inputs[0])
    lk(nt, tr.outputs[0], mx.inputs[1])
    lk(nt, gl.outputs[0], mx.inputs[2])
    lk(nt, mx.outputs[0], out.inputs['Surface'])
    return m


def mat_lampglass():
    m, nt, out = new_mat('lampglass')
    em = nd(nt, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.62, 0.26, 1.0)
    em.inputs['Strength'].default_value = 18.0
    lk(nt, em.outputs[0], out.inputs['Surface'])
    return m


def mat_grit():
    m, nt, out = new_mat('grit')
    tc = nd(nt, 'ShaderNodeTexCoord')
    n = noise(nt, tc.outputs['Object'], 40.0, 5.0, 0.6)
    col = mix_col(nt, maprange(nt, n, 0.3, 0.7, 0.0, 1.0), hx('#24272a'), hx('#3a3a36'))
    bump = nd(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.01
    lk(nt, noise(nt, tc.outputs['Object'], 120.0, 3.0, 0.6), bump.inputs['Height'])
    principled(nt, out, col, 0.4, 0.0, bump.outputs[0], 0.5)
    return m


def mat_haze():
    m, nt, out = new_mat('haze')
    vol = nd(nt, 'ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.42, 0.62, 0.78, 1.0)
    tc = nd(nt, 'ShaderNodeTexCoord')
    sp = nd(nt, 'ShaderNodeSeparateXYZ')
    lk(nt, tc.outputs['Object'], sp.inputs[0])
    hz = maprange(nt, sp.outputs[2], 0.0, 9.0, 1.0, 0.10)
    dm = nd(nt, 'ShaderNodeMath', operation='MULTIPLY')
    lk(nt, hz, dm.inputs[0])
    dm.inputs[1].default_value = float(os.environ.get('TH_HAZE', '0.021'))
    lk(nt, dm.outputs[0], vol.inputs['Density'])
    vol.inputs['Anisotropy'].default_value = 0.4
    lk(nt, vol.outputs[0], out.inputs['Volume'])
    return m


# ----------------------------------------------------------------- scene
def setup_world(scene):
    w = bpy.data.worlds.new('World')
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nd(nt, 'ShaderNodeOutputWorld')
    bg = nd(nt, 'ShaderNodeBackground')
    tc = nd(nt, 'ShaderNodeTexCoord')
    sp = nd(nt, 'ShaderNodeSeparateXYZ')
    lk(nt, tc.outputs['Generated'], sp.inputs[0])
    # sky: horizon slate-teal, zenith blue-black
    g = ramp(nt, [(0.0, hx('#4f6f78')), (0.12, hx('#25444f')), (0.5, hx('#0d2637')), (1.0, hx('#061520'))],
             maprange(nt, sp.outputs[2], -0.05, 0.9, 0.0, 1.0))
    # clouds: wide, dark, soft
    mp = nd(nt, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.4, 1.4, 4.0)
    lk(nt, tc.outputs['Generated'], mp.inputs['Vector'])
    cl = noise(nt, mp.outputs[0], 2.2, 5.0, 0.6, 0.5)
    mask = maprange(nt, cl, 0.38, 0.62, 0.0, 1.0)
    sky = mix_col(nt, mask, g.outputs[0], hx('#030b11'))
    # warm afterglow low in the sky, right behind the end of the street
    az = nd(nt, 'ShaderNodeMath', operation='ABSOLUTE')
    lk(nt, sp.outputs[0], az.inputs[0])
    glow_h = maprange(nt, sp.outputs[2], 0.0, 0.2, 1.0, 0.0)
    glow_w = maprange(nt, az.outputs[0], 0.0, 0.45, 1.0, 0.0)
    gm = nd(nt, 'ShaderNodeMath', operation='MULTIPLY')
    lk(nt, glow_h, gm.inputs[0]); lk(nt, glow_w, gm.inputs[1])
    gm2 = nd(nt, 'ShaderNodeMath', operation='MULTIPLY')
    lk(nt, gm.outputs[0], gm2.inputs[0]); gm2.inputs[1].default_value = 0.55
    sky = mix_col(nt, gm2.outputs[0], sky, hx('#8a5a30'))
    lk(nt, sky, bg.inputs['Color'])
    bg.inputs['Strength'].default_value = float(os.environ.get('TH_SKY', '1.6'))
    bg2 = nd(nt, 'ShaderNodeBackground')
    lk(nt, sky, bg2.inputs['Color'])
    bg2.inputs['Strength'].default_value = float(os.environ.get('TH_SKYLIGHT', '4.4'))
    lp = nd(nt, 'ShaderNodeLightPath')
    mx = nd(nt, 'ShaderNodeMixShader')
    orr = nd(nt, 'ShaderNodeMath', operation='MAXIMUM')
    lk(nt, lp.outputs['Is Camera Ray'], orr.inputs[0])
    lk(nt, lp.outputs['Is Glossy Ray'], orr.inputs[1])
    lk(nt, orr.outputs[0], mx.inputs[0])
    lk(nt, bg2.outputs[0], mx.inputs[1])
    lk(nt, bg.outputs[0], mx.inputs[2])
    lk(nt, mx.outputs[0], out.inputs['Surface'])


def make_light(name, kind, loc, energy, color, size=0.1, rot=None):
    l = bpy.data.lights.new(name, kind)
    l.energy = energy
    l.color = color
    if kind == 'POINT':
        l.shadow_soft_size = size
    ob = bpy.data.objects.new(name, l)
    ob.location = loc
    if rot: ob.rotation_euler = rot
    bpy.context.scene.collection.objects.link(ob)
    return ob


def setup_camera(scene):
    cam = bpy.data.cameras.new('Cam')
    cam.sensor_fit = 'HORIZONTAL'
    cam.sensor_width = 36
    cam.lens = float(os.environ.get('TH_LENS', '28'))
    cam.shift_y = float(os.environ.get('TH_SHIFT', '0.10'))
    cam.clip_start = 0.05
    cam.clip_end = 200
    ob = bpy.data.objects.new('Cam', cam)
    ob.location = (float(os.environ.get('TH_CX', '-0.35')), float(os.environ.get('TH_CY', '0.0')), float(os.environ.get('TH_CZ', '1.62')))
    ob.rotation_euler = (math.radians(90), 0, 0)
    scene.collection.objects.link(ob)
    scene.camera = ob


def main():
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    build_buildings()
    build_ground()
    build_cart()
    build_bin()
    cob = build_cobbles()
    pud = build_puddles()

    mats = {
        'brick': mat_brick(), 'stone': mat_stone(), 'slate': mat_slate(), 'paint': mat_paint(), 'iron': mat_iron(),
        'glassL': mat_glass_lit(float(os.environ.get('TH_WIN', '0.62'))), 'glassD': mat_glass_dark(), 'terra': mat_terra(),
        'brass': mat_brass(), 'flag': mat_flag(), 'earth': mat_earth(), 'lampglass': mat_lampglass(),
        'wood': mat_wood(), 'plaster': mat_plaster(), 'grit': mat_grit(),
    }
    for k, mb in B.items():
        if mb.v:
            mb.build(k, mats[k])
    for o in bpy.data.objects:
        if o.name.startswith('lampglass'):
            o.visible_shadow = False
    cob.build('cobbles', mat_cobble())
    pud.build('puddles', mat_puddle())

    # haze box
    hz = MB()
    hz.box(-9.0, 9.0, -3.0, FY + 5.0, -0.2, 14.0)
    ho = hz.build('haze', mat_haze())

    setup_world(scene)
    setup_camera(scene)

    # lights: three gas lamps (warm), a cool faint sky fill from the end of the street
    LAMP_W = float(os.environ.get('TH_LAMP', '280'))
    for i, (x, y) in enumerate(LAMPS):
        make_light('lamp%d' % i, 'POINT', (x, y, 3.25), LAMP_W, (1.0, 0.62, 0.28), 0.12)
    # a lamp just behind the camera on the right lights the foreground setts (its post is out of frame)
    make_light('lamp_off', 'POINT', (2.45, 1.4, 3.25), float(os.environ.get('TH_LAMPOFF', '170')), (1.0, 0.62, 0.28), 0.12)
    # light from the hero's open hall door and bay (soft spill on the forecourt)
    make_light('hero_spill', 'POINT', (-1.1, FY - 1.6, 1.4), float(os.environ.get('TH_SPILL', '150')), (1.0, 0.55, 0.22), 0.4)
    make_light('hero_door', 'POINT', (1.75, FY - 1.2, 1.5), 60.0, (1.0, 0.5, 0.2), 0.3)
    # cold light from the sky / far end, faint (blue hour)
    sun = bpy.data.lights.new('moon', 'SUN')
    sun.energy = float(os.environ.get('TH_MOON', '1.7'))
    sun.color = (0.50, 0.68, 1.0)
    sun.angle = math.radians(8)
    so = bpy.data.objects.new('moon', sun)
    so.rotation_euler = (math.radians(-55), 0, math.radians(35))
    scene.collection.objects.link(so)

    # render settings
    scene.render.engine = 'CYCLES'
    cy = scene.cycles
    cy.device = 'CPU'
    cy.samples = SAMPLES
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.max_bounces = 7
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 2
    cy.volume_bounces = 1
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.sample_clamp_indirect = 8.0
    cy.sample_clamp_direct = 0.0
    cy.volume_step_rate = 1.5
    cy.volume_max_steps = 256
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.display_settings.display_device = 'sRGB'
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    exr = os.path.splitext(OUT)[0] + '_raw.exr'
    scene.render.filepath = exr
    print('scene built in %.1fs' % (time.time() - t0))
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    print('rendered in %.1fs' % (time.time() - t1))

    from bpy_extras.object_utils import world_to_camera_view
    cam_ob = scene.camera
    smoke_src = []
    rz = EZ + 0.12 + (0.38 + 3.4) * 0.72
    for (vx, dv) in ((2.8, 0.2), (-2.8, 0.2), (2.8, -0.2)):
        co = world_to_camera_view(scene, cam_ob, Vector((vx + dv, FY + 3.4, rz + 2.45)))
        smoke_src.append((co.x * W, (1 - co.y) * H))
    img = bpy.data.images.load(exr)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    arr = arr.reshape(h, w, 4)[::-1, :, :3].copy()
    finish(arr, OUT, smoke_src)
    try:
        os.remove(exr)
    except Exception:
        pass
    print('total %.1fs' % (time.time() - t0))


# ----------------------------------------------------------------- finishing
def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def fbm(shape, cell, seed, octaves=6, stretch=(1.0, 1.0)):
    import cv2
    rs = np.random.RandomState(seed)
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        ch = max(2, int(h / (cell * stretch[0]) * 2 ** o))
        cw = max(2, int(w / (cell * stretch[1]) * 2 ** o))
        a = rs.rand(ch, cw).astype(np.float32)
        out += amp * cv2.resize(a, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.55
    return out / tot


def add_smoke(g, sources, sc):
    import cv2
    h, w, _ = g.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = fbm((h, w), 70 * sc, 21, 6, (2.2, 1.0))
    n2 = fbm((h, w), 40 * sc, 22, 5, (1.6, 1.0))
    total = np.zeros((h, w), np.float32)
    for k, (sx, sy) in enumerate(sources):
        L = (0.40 if k == 0 else 0.27) * h
        t = (sy - yy) / L
        valid = (t > 0) & (t < 1.0)
        tt = np.clip(t, 0, 1)
        sway = (n2 - 0.5) * 50 * sc * tt
        xc = sx + (95 + 25 * k) * sc * tt + 10 * sc * np.sin(tt * 4.0 + k * 1.7) + sway
        wd = (7 + 52 * tt ** 0.9) * sc
        d = (xx - xc) / wd
        core = np.exp(-d * d * 1.1)
        grain = np.clip(n1 * 1.7 - 0.3, 0, 1) * 0.7 + np.clip(n2 * 1.6 - 0.35, 0, 1) * 0.4
        fade = (1 - tt) ** 1.2 * np.clip(tt * 10, 0, 1)
        a = core * (0.22 + grain) * fade * valid
        total = np.maximum(total, a)
    total = cv2.GaussianBlur(total, (0, 0), 1.3 * sc)
    a = np.clip(total * 0.8, 0, 0.55)[..., None]
    smoke = np.array([0.025, 0.05, 0.065], np.float32)
    return g * (1 - a) + smoke * a


def finish(lin, path, smoke_src=()):
    import cv2
    h, w, _ = lin.shape
    sc = w / 540.0
    x = np.clip(lin, 0, 60) * EXPO
    # filmic-ish curve (keeps blacks deep, rolls the lamps off)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    y = np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)
    # grade: shadows go teal / blue-black, lights go amber
    lum = (0.2126 * y[..., 0] + 0.7152 * y[..., 1] + 0.0722 * y[..., 2])[..., None]
    shadow = np.clip(1 - lum * 3.0, 0, 1)
    teal = np.array([0.84, 1.03, 1.08], dtype=np.float32)
    amber = np.array([1.10, 1.0, 0.86], dtype=np.float32)
    hi = np.clip((lum - 0.25) * 2.0, 0, 1)
    y = y * (1 + shadow * (teal - 1) * 0.9) * (1 + hi * (amber - 1) * 0.8)
    y = np.clip(y, 0, 1)
    # blacks are never pure: blue-black away from light
    y = y * 0.96 + np.array([0.008, 0.016, 0.022], dtype=np.float32)
    # gentle S
    y = np.clip(y, 0, 1)
    y = y + 0.12 * (y - 0.5) * (1 - np.abs(2 * y - 1)) * 0.0
    g = srgb(y).astype(np.float32)
    # vignette
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r2 = ((xx - w / 2) / (w / 2)) ** 2 * 0.8 + ((yy - h * 0.52) / (h / 2)) ** 2 * 0.55
    g *= (1 - 0.30 * np.clip(r2, 0, 1.5))[..., None]
    if len(smoke_src):
        g = add_smoke(g, smoke_src, sc)
    # painterly: smooth flat areas, keep edges
    s_ = g.copy()
    for _ in range(2):
        s_ = cv2.bilateralFilter(s_, d=0, sigmaColor=0.07, sigmaSpace=2.2 * sc)
    blur = cv2.GaussianBlur(s_, (0, 0), 1.4 * sc)
    g = np.clip(s_ + (s_ - blur) * 0.9, 0, 1)
    # faint brush marks: short horizontal strokes of slightly different lightness
    bs = fbm((h, w), 9 * sc, 31, 3, (1.0, 5.0))
    bs = (bs - bs.mean()) / (bs.std() + 1e-6)
    g = np.clip(g * (1 + 0.028 * bs[..., None]), 0, 1)
    # rain: sparse thin slanted streaks, brighter where light is
    layer = np.zeros((h, w), dtype=np.float32)
    rr = random.Random(5)
    for _ in range(int(260 * (w * h) / (540 * 960))):
        x0 = rr.uniform(0, w)
        y0 = rr.uniform(0, h * 0.9)
        ln = rr.uniform(14, 34) * sc
        cv2.line(layer, (int(x0), int(y0)), (int(x0 - ln * 0.12), int(y0 + ln)), rr.uniform(0.3, 0.9), max(1, int(round(sc * 0.8))), cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 0.6 * sc)
    amb = np.clip(cv2.GaussianBlur(g.mean(axis=2), (0, 0), 25 * sc) * 2.2 + 0.08, 0, 1)
    rain = (layer * amb * 0.22)[..., None] * np.array([0.8, 0.9, 1.0], dtype=np.float32)
    g = 1 - (1 - g) * (1 - rain)
    # fine grain, like paint on paper
    nz = np.random.RandomState(3).normal(0, 0.012, (h, w)).astype(np.float32)
    nz = cv2.GaussianBlur(nz, (0, 0), 0.7 * sc)
    g = np.clip(g + nz[..., None] * 1.6, 0, 1)
    out = (g * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(path, out[..., ::-1])


if __name__ == '__main__':
    main()
