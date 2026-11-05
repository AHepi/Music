"""
stone_lantern: a Japanese stone lantern (toro) of grey granite, stacked from separate stones the way they are carved and
set: either a tall Kasuga lantern on a post (a hexagonal base with a ring of lotus petals, a round post with three bands
at its middle, a middle platform with lotus petals under it, a hexagonal fire box, a wide hexagonal roof cap whose
corners sweep up into curls, and a jewel-shaped finial on a lotus cup) or a low snow-viewing lantern (yukimi) on three
bent legs under a broad cap. The fire box has openings: a square window at the front and back with paper set behind
it, a round sun window and a smaller round moon window on the two front corners, and a sunk panel in each back corner.
Weathered: rain streaks run down every stone, moss sits on what faces up (the cap's top, the base, the platform) and
round the foot; each stone shows its own part of the photographed rock.

Options:
    kind   'kasuga' (default): the tall lantern on a post, 1.8 m; 'yukimi': the low snow-viewing lantern on three legs
           with a broad cap, 0.95 m tall and 1.1 m across
    lit    (default False) a warm light inside the fire box: the paper windows glow, the round windows let it out, and
           it lights what is round the lantern; False: cold paper, no light
    seed   how each stone sits on the one below (a little off true), the cap's turn, the moss and streaks

Where it came from: the builders' stone lantern in '/home/claude/build-57-garden/first pass/render_final.py' (the
stone lantern, lines 940-1046: hexagonal prisms, a post, six corner pillars round a glowing paper ring, a cap with
lifted corners, a finial, 'SURFACE • dark_rock_02' with moss), kept in '/home/claude/build-57-garden/second pass/
render_final.py' (lines 1096-1171). Rebuilt here from the board's photographs 06 and 07: separate stones with lotus
petals, a banded post, a fire box with real walls and windows, a cap with curls at its corners, and the yukimi kind.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_garden as garden  # noqa: E402

PART = 'stone_lantern'
KINDS = ('kasuga', 'yukimi')

CARD = {
    'name': PART,
    'what': 'a Japanese stone lantern of weathered granite: a tall Kasuga lantern on a banded post (lotus base, fire box with '
            'paper and round windows, wide cap with curled corners, jewel finial) or a low snow-viewing lantern on three legs '
            'under a broad cap; moss on its cap and foot, rain streaks; lit warm inside or dark',
    'size_m': (0.93, 0.80, 1.80),
    'options': {
        'kind': "'kasuga' (default): the tall lantern on a post, 1.8 m; 'yukimi': the low snow-viewing lantern on three legs, 0.95 m tall, 1.1 m across",
        'lit': 'False (default): cold paper, no light; True: a warm 18 W light in the fire box, the paper windows glowing and the round ones letting it out',
        'seed': "how each stone sits on the one below, the cap's turn, the moss and streaks (default 0)",
    },
    'materials': ['SURFACE • dark_rock_02 (garden stone, wet 0.45, moss 1.00)', 'PART • garden: lantern paper',
                  'PART • garden: lantern paper, lit'],
    'source': "the stone lantern in '/home/claude/build-57-garden/first pass/render_final.py' (lines 940-1046), kept in "
              "'/home/claude/build-57-garden/second pass/render_final.py' (lines 1096-1171); rebuilt from the board's photographs 06 and 07",
    'views': 'reads from every side; the paper window faces -Y (and +Y), the round sun and moon windows the two front corners',
    'trap': "lit, its light is only 18 W, inside the fire box (the object 'stone_lantern light'): it lights the stones and moss round "
            "its foot; in a wide scene turn it up rather than brightening the paper; the yukimi's legs reach 0.42 m out from its middle",
}


# ---------------------------------------------------------------------------------------------------- the fire box

def _hit_rect(theta, half_w, z_low, z_high):
    """Where a ray from (0, 0) at angle theta (in the face's own x across, z up) leaves the rectangle."""
    c, s = math.cos(theta), math.sin(theta)
    tx = half_w / abs(c) if abs(c) > 1e-9 else 1e9
    tz = ((z_high / s) if s > 0 else (z_low / s)) if abs(s) > 1e-9 else 1e9
    t = min(tx, tz)
    return c * t, s * t


def _panel(shape, o0, o1, i0, i1, z0, z1, hole):
    """One wall of the fire box between two corners (outer o0, o1 and inner i0, i1, in plan), from z0 to z1, with a
    window through it: hole is None, ('rect', half width, half height, centre z) or ('circle', radius, centre z)."""
    if hole is None:
        bottom = shape._verts([o0 + Vector((0, 0, z0)), o1 + Vector((0, 0, z0)), i1 + Vector((0, 0, z0)), i0 + Vector((0, 0, z0))])
        top = shape._verts([o0 + Vector((0, 0, z1)), o1 + Vector((0, 0, z1)), i1 + Vector((0, 0, z1)), i0 + Vector((0, 0, z1))])
        shape._rings([bottom, top], True, True, True)
        return
    across = (o1 - o0).normalized()
    centre_out, centre_in = (o0 + o1) / 2, (i0 + i1) / 2
    half_out, half_in = (o1 - o0).length / 2, (i1 - i0).length / 2
    zc = hole[-1]
    angles = {2 * math.pi * k / 32 for k in range(32)}
    for (x, z) in ((-half_out, z0 - zc), (half_out, z0 - zc), (half_out, z1 - zc), (-half_out, z1 - zc)):
        angles.add(math.atan2(z, x) % (2 * math.pi))
    if hole[0] == 'rect':
        hw, hh = hole[1], hole[2]
        for (x, z) in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            angles.add(math.atan2(z, x) % (2 * math.pi))
    angles = sorted(angles)
    up = Vector((0.0, 0.0, 1.0))
    rings = {'bo': [], 'bi': [], 'ho': [], 'hi': []}
    for theta in angles:
        x, z = _hit_rect(theta, half_out, z0 - zc, z1 - zc)
        rings['bo'].append(centre_out + across * x + up * (z + zc))
        x, z = _hit_rect(theta, half_in, z0 - zc, z1 - zc)
        rings['bi'].append(centre_in + across * x + up * (z + zc))
        if hole[0] == 'rect':
            hx, hz = _hit_rect(theta, hole[1], -hole[2], hole[2])
        else:
            hx, hz = hole[1] * math.cos(theta), hole[1] * math.sin(theta)
        rings['ho'].append(centre_out + across * hx + up * (hz + zc))
        rings['hi'].append(centre_in + across * hx + up * (hz + zc))
    v = {k: shape._verts(p) for k, p in rings.items()}
    shape._rings([v['bo'], v['ho']], True)      # the outer face round the window
    shape._rings([v['hi'], v['bi']], True)      # the inner face
    shape._rings([v['ho'], v['hi']], True)      # the window's reveal
    shape._rings([v['bi'], v['bo']], True)      # the wall's edges: its top, bottom and the joints at the corners


def fire_box(shape, z0, z1, r_out, r_in, window, sun, moon):
    """Six walls on a hexagon with a flat face to -Y: square windows front and back, the sun and the moon on the two
    front corners, solid at the back corners. Returns the paper windows' outlines (front and back) for the paper."""
    outer = garden.hex_ring(r_out, 0.0)
    inner = garden.hex_ring(r_in, 0.0)
    zc = (z0 + z1) / 2
    sunk = ('rect', window[0] * 1.15, window[1] * 1.05, zc)
    holes = {1: ('rect', window[0], window[1], zc), 4: ('rect', window[0], window[1], zc), 3: ('circle', sun, zc), 5: ('circle', moon, zc + 0.01),
             0: sunk, 2: sunk}
    papers = []
    for k in range(6):
        j = (k + 1) % 6
        _panel(shape, outer[k], outer[j], inner[k], inner[j], z0, z1, holes[k])
        if holes[k] is sunk:
            # the back corners are not cut through: a panel sunk 8 mm into the face, where a deer would be carved
            centre_out, centre_in = (outer[k] + outer[j]) / 2, (inner[k] + inner[j]) / 2
            normal = (centre_out - centre_in).normalized()
            across = (outer[j] - outer[k]).normalized()
            front, back = centre_out - normal * 0.008, centre_in + normal * 0.001
            hw, hh = sunk[1] + 0.001, sunk[2] + 0.001
            corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
            lo = shape._verts([back + across * sx * hw + Vector((0, 0, zc + sz * hh)) for (sx, sz) in corners])
            hi = shape._verts([front + across * sx * hw + Vector((0, 0, zc + sz * hh)) for (sx, sz) in corners])
            shape._rings([lo, hi], True, True, True)
        if holes[k] is not None and holes[k][0] == 'rect':
            centre_in = (inner[k] + inner[j]) / 2
            inward = -centre_in.normalized()
            across = (inner[j] - inner[k]).normalized()
            c = centre_in + inward * 0.004
            hw, hh = window[0] + 0.012, window[1] + 0.012
            papers.append([c + across * sx * hw + Vector((0, 0, zc + sz * hh)) for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    return papers


# ---------------------------------------------------------------------------------------------------- the cap

def _cap_point(angle, u, z_base, r_edge, r_top, height, lift, power):
    """A point of the cap's top at `angle`, `u` of the way from the eave (0) to the top (1)."""
    sector = (angle % (math.pi / 3)) - math.pi / 6
    corner = abs(sector) / (math.pi / 6)                      # 1 at a corner, 0 mid-edge
    radius = (r_edge * (1 - u) + r_top * u) * math.cos(math.pi / 6) / math.cos(sector)
    z = z_base + height * (u ** power) + lift * ((1 - u) ** 3) * (corner ** 2.5)
    return Vector((radius * math.cos(angle), radius * math.sin(angle), z))


def cap(shape, z_base, r_edge, r_top, height, lift, lip, under, curl, power=2.0, per=6):
    """The roof cap: hexagonal, its top sweeping up from a thin eave to a small flat top, the corners lifted, a lip at
    the eave, a flat underside, and a curl (warabite) at each corner. Returns the top's height."""
    n = 6 * per
    angles = [2 * math.pi * j / n for j in range(n)]
    us = [0.0, 0.06, 0.15, 0.27, 0.42, 0.58, 0.74, 0.88, 1.0]
    rings = []
    inner = shape._verts([Vector((under * math.cos(a), under * math.sin(a), z_base - lip - 0.002)) for a in angles])
    rings.append(inner)
    lip_ring = [_cap_point(a, 0.0, z_base, r_edge, r_top, height, lift, power) - Vector((0, 0, lip)) for a in angles]
    rings.append(shape._verts(lip_ring))
    for u in us:
        rings.append(shape._verts([_cap_point(a, u, z_base, r_edge, r_top, height, lift, power) for a in angles]))
    shape._rings(rings, True, True, True)
    # the curls at the corners: a scroll turning out, up and back over the eave
    for j in range(6):
        a = angles[j * per]
        tip = _cap_point(a, 0.0, z_base, r_edge, r_top, height, lift, power)
        out = Vector((math.cos(a), math.sin(a), 0.0))
        up = Vector((0.0, 0.0, 1.0))
        centre = tip + up * curl - out * curl * 0.35
        pts, radii = [], []
        steps = 12
        for k in range(steps + 1):
            f = k / steps
            phi = -math.pi / 2 + f * 1.25 * math.pi
            rho = curl * (1.0 - 0.45 * f)
            pts.append(centre + rho * (math.cos(phi) * out + math.sin(phi) * up))
            radii.append(lip * 0.62 * (1.0 - 0.45 * f))
        shape.sweep(pts, lip * 0.6, sides=8, radii=radii)
    return z_base + height


def jewel(shape, z, scale, petals=10):
    """The finial: a lotus cup and the jewel (hoju) on it, its point up."""
    s = scale
    shape.lathe([(0.0, z), (0.055 * s, z), (0.07 * s, z + 0.012 * s, 0.0), (0.085 * s, z + 0.03 * s, 0.18), (0.09 * s, z + 0.045 * s, 0.22),
                 (0.07 * s, z + 0.05 * s, 0.1), (0.0, z + 0.05 * s)], segments=40, flutes=petals)
    z += 0.045 * s
    shape.lathe([(0.0, z), (0.05 * s, z), (0.075 * s, z + 0.035 * s), (0.08 * s, z + 0.07 * s), (0.068 * s, z + 0.105 * s), (0.045 * s, z + 0.135 * s),
                 (0.02 * s, z + 0.158 * s), (0.008 * s, z + 0.175 * s), (0.0, z + 0.182 * s)], segments=24)
    return z + 0.182 * s


# ---------------------------------------------------------------------------------------------------- the two kinds

def _kasuga(shape, rng):
    pieces = []

    def piece(fn):
        shape.begin()
        out = fn()
        shape.end(rng.random())
        return out

    # the base: a hexagonal block, a ring of lotus petals turned back on it, a round step for the post
    def base():
        outer = garden.hex_ring(0.30, 0.0)
        ring_low = shape._verts(outer)
        ring_top = shape._verts([p + Vector((0, 0, 0.13)) for p in garden.hex_ring(0.30, 0.0)])
        ring_in = shape._verts([p + Vector((0, 0, 0.15)) for p in garden.hex_ring(0.27, 0.0)])
        shape._rings([ring_low, ring_top, ring_in], True, True, True)
        shape.lathe([(0.25, 0.145), (0.255, 0.165, 0.10), (0.235, 0.2, 0.22), (0.19, 0.232, 0.22), (0.14, 0.248, 0.1), (0.12, 0.25), (0.0, 0.25)], segments=48, flutes=12)
        shape.lathe([(0.0, 0.245), (0.125, 0.245), (0.125, 0.275), (0.11, 0.285), (0.0, 0.285)], segments=32)
    piece(base)
    # the post: round, narrowing a little, three bands at its middle
    def post():
        z0, z1, mid = 0.28, 0.93, 0.6
        prof = [(0.0, z0), (0.088, z0), (0.086, mid - 0.06)]
        for k, zz in enumerate((mid - 0.04, mid, mid + 0.04)):
            prof += [(0.085, zz - 0.012), (0.097, zz - 0.006), (0.097, zz + 0.006), (0.084, zz + 0.012)]
        prof += [(0.08, mid + 0.07), (0.077, z1), (0.0, z1)]
        shape.lathe(prof, segments=28)
    piece(post)
    # the middle platform: lotus petals pointing down under a hexagonal slab
    def platform():
        shape.lathe([(0.0, 0.92), (0.085, 0.92), (0.11, 0.935, 0.1), (0.165, 0.965, 0.22), (0.21, 1.0, 0.2), (0.235, 1.02, 0.08), (0.0, 1.02)], segments=48, flutes=12)
        low = shape._verts(garden.hex_ring(0.25, 1.015))
        top = shape._verts(garden.hex_ring(0.25, 1.065))
        top_in = shape._verts(garden.hex_ring(0.22, 1.08))
        shape._rings([low, top, top_in], True, True, True)
    piece(platform)
    papers = piece(lambda: fire_box(shape, 1.08, 1.36, 0.19, 0.145, (0.06, 0.085), 0.05, 0.04))
    turn = rng.uniform(-0.04, 0.04)
    def roof():
        top = cap(shape, 1.4, 0.42, 0.085, 0.17, 0.04, 0.035, 0.19, 0.021)
        shape.lathe([(0.0, 1.355), (0.21, 1.355), (0.21, 1.372), (0.0, 1.372)], segments=6, phase=0.0)
        return top
    top = piece(roof)
    shape.begin()
    jewel(shape, top - 0.004, 1.0)
    shape.end(rng.random())
    return papers, (0.0, 0.0, 1.22), turn


def _yukimi(shape, rng):
    def piece(fn):
        shape.begin()
        out = fn()
        shape.end(rng.random())
        return out

    def legs():
        for k, a in enumerate((math.radians(-150), math.radians(-30), math.radians(90))):
            out = Vector((math.cos(a), math.sin(a), 0.0))
            pts = [out * 0.13 + Vector((0, 0, 0.36)), out * 0.2 + Vector((0, 0, 0.33)), out * 0.29 + Vector((0, 0, 0.25)),
                   out * 0.35 + Vector((0, 0, 0.14)), out * 0.375 + Vector((0, 0, 0.05)), out * 0.38 + Vector((0, 0, 0.0))]
            pts = shapes.smooth_path(pts, steps=4)
            radii = [0.045 + 0.02 * (i / (len(pts) - 1)) for i in range(len(pts))]
            shape.sweep(pts, 0.05, sides=7, radii=radii)
            shape.lathe([(0.0, 0.0), (0.075, 0.0), (0.07, 0.03), (0.0, 0.035)], segments=7, matrix=Matrix.Translation(out * 0.38))
    piece(legs)
    def platform():
        low = shape._verts(garden.hex_ring(0.2, 0.34))
        mid = shape._verts(garden.hex_ring(0.24, 0.37))
        top = shape._verts(garden.hex_ring(0.24, 0.41))
        top_in = shape._verts(garden.hex_ring(0.215, 0.42))
        shape._rings([low, mid, top, top_in], True, True, True)
    piece(platform)
    papers = piece(lambda: fire_box(shape, 0.42, 0.63, 0.2, 0.155, (0.065, 0.065), 0.05, 0.04))
    turn = rng.uniform(-0.04, 0.04)
    def roof():
        shape.lathe([(0.0, 0.625), (0.22, 0.625), (0.22, 0.645), (0.0, 0.645)], segments=6)
        return cap(shape, 0.68, 0.55, 0.09, 0.13, 0.03, 0.04, 0.22, 0.022, power=1.35)
    top = piece(roof)
    shape.begin()
    jewel(shape, top - 0.004, 0.75)
    shape.end(rng.random())
    return papers, (0.0, 0.0, 0.525), turn


def build(collection, seed=0, kind='kasuga', lit=False):
    if kind not in KINDS:
        raise ValueError("kind is one of %s, not %r" % (', '.join(repr(k) for k in KINDS), kind))
    rng = shapes.rng_for(PART, seed)
    shape = garden.Shape()
    papers, light_at, turn = (_kasuga if kind == 'kasuga' else _yukimi)(shape, rng)
    # the stones settle a little off true: a slight lean of the whole, about its foot
    lean = Matrix.Rotation(rng.uniform(-0.012, 0.012), 4, 'X') @ Matrix.Rotation(rng.uniform(-0.012, 0.012), 4, 'Y') @ Matrix.Rotation(turn, 4, 'Z')
    shape.transform(lean)
    stone = shape.finish('%s stone' % PART, collection, garden.garden_stone(), smooth=True, sharp=40.0, chamfer=0.004)
    made = [stone]
    sheet = garden.Shape()
    for quad in papers:
        sheet.poly([lean @ p for p in quad])
    paper = sheet.finish('%s paper' % PART, collection, garden.paper(bool(lit)))
    paper.visible_shadow = False
    made.append(paper)
    if lit:
        made.append(garden.hidden_light(collection, '%s light' % PART, lean @ Vector(light_at), 18.0, (1.0, 0.52, 0.2), 0.03))
    return made
