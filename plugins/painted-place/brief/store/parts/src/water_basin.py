"""
water_basin: a stone water basin (tsukubai) as it is set in a tea garden: a rough round stone hollowed out on top, or a
carved square block with a round bowl, standing low with water still in its bowl; behind it a bamboo spout (kakei): a
bamboo pipe on two bamboo posts, bound with cord, its mouth cut on the slant, pouring a thin stream into the bowl, the
water ringed where it lands; a bamboo ladle (hishaku) laid across the bowl; round its foot the stones that belong to it
(a flat stone in front to crouch on, a taller one either side), wet pebbles in the hollow between them, and cushions of
moss. Weathered granite like the stone lantern's: rain streaks, moss on what faces up and round the foot.

Options:
    stone    'round' (default): a rough round stone with its hollow worn smooth; 'square': a carved square block with
             chamfered edges and a round bowl
    spout    (default True) the bamboo spout on its posts behind the basin (at +Y), pouring into the bowl; False: none
    ladle    (default True) the bamboo ladle laid across the bowl; False: none
    seed     the stone's shape, the foot stones, the pebbles, the moss

Where it came from: the builders' basin in '/home/claude/build-57-garden/first pass/render_final.py' (the stone water
basin with its spout, falling water and ladle), kept in '/home/claude/build-57-garden/second pass/render_final.py'
(lines 1021-1069: a lathe of 'SURFACE • dark_rock_02' with moss, a water disc, a bamboo pipe on one post, a stream, a
ladle). Rebuilt here with the photograph 07's carved square basin as a second kind, a pipe on two bound posts with a
cut mouth, the stream landing in rings, and the stones, pebbles and moss a basin is set among.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_garden as garden  # noqa: E402

PART = 'water_basin'
STONES = ('round', 'square')
PEBBLES = 'MADE • pebbles, wet'

CARD = {
    'name': PART,
    'what': 'a stone water basin (tsukubai): a rough round stone hollowed on top or a carved square block, water standing in its '
            'bowl, a bamboo spout on two bound bamboo posts pouring a thin stream into it, a bamboo ladle across it, the flat '
            'and side stones round its foot, wet pebbles and moss',
    'size_m': (1.25, 1.35, 0.95),
    'options': {
        'stone': "'round' (default): a rough round stone with its hollow worn smooth; 'square': a carved square block with a round bowl",
        'spout': 'True (default): the bamboo spout on its posts behind the basin (+Y), pouring into the bowl; False: none',
        'ladle': 'True (default): the bamboo ladle laid across the bowl; False: none',
        'seed': "the stone's shape, the foot stones, the pebbles, the moss (default 0)",
    },
    'materials': ['SURFACE • dark_rock_02 (garden stone, wet 0.45, moss 1.00)',
                  'PART • garden: bamboo, weathered', 'PART • water_basin: still water', 'PART • garden: falling water',
                  'PART • garden: dark cord', PEBBLES, 'PART • garden: moss cushions'],
    'source': "the basin, spout, falling water and ladle in '/home/claude/build-57-garden/first pass/render_final.py', kept in "
              "'/home/claude/build-57-garden/second pass/render_final.py' (lines 1021-1069); the carved square basin from the board's photograph 07",
    'views': 'reads from every side; the front stone (to crouch on) is at -Y, the spout comes from behind (+Y)',
    'trap': 'the front stone reaches 0.72 m in front (-Y) of the origin and the spout post 0.56 m behind it; the stream is a few '
            'millimetres thick, so from far off only its glint and the rings in the bowl show',
}

RIM = 0.42            # the basin's rim height
WATER = 0.395         # the water's surface in the bowl


def _round_stone(shape, rng):
    """A rough boulder with a hollow worn smooth in its top."""
    profile = [(0.0, -0.03), (0.24, -0.03), (0.3, 0.05), (0.32, 0.15), (0.31, 0.26), (0.285, 0.34), (0.25, 0.395), (0.215, RIM),
               (0.185, RIM - 0.003), (0.17, RIM - 0.03), (0.15, RIM - 0.075), (0.11, RIM - 0.11), (0.05, RIM - 0.125), (0.0, RIM - 0.128)]
    shape.begin()
    shape.lathe(profile, segments=44)
    verts = shape.new_verts()
    lobes = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    salt = Vector((rng.uniform(0, 50), rng.uniform(0, 50), 0.0))
    for v in verts:
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6:
            continue
        a = math.atan2(v.co.y, v.co.x)
        outside = v.co.z < RIM - 0.002 and r > 0.2
        if outside:
            wob = 1.0 + 0.07 * math.sin(2 * a + lobes[0]) + 0.05 * math.sin(3 * a + lobes[1]) + 0.04 * mnoise.noise(v.co * 4.0 + salt)
            v.co.x *= wob
            v.co.y *= wob * 0.92
            v.co.z += 0.025 * math.sin(a + lobes[2]) * min(1.0, max(0.0, v.co.z / RIM))
        else:
            v.co.y *= 0.95
    garden.roughen(shape, [v for v in verts if math.hypot(v.co.x, v.co.y) > 0.21 and v.co.z < RIM - 0.01], 0.022, 6.0, seed=rng.randint(0, 99))
    shape.end(rng.random())


def _square_stone(shape, rng):
    """A carved square block, edges chamfered, a round bowl cut in its top."""
    half, bowl, top, depth, cham = 0.24, 0.15, RIM, 0.12, 0.025
    angles = {2 * math.pi * k / 48 for k in range(48)}
    for a in (45, 135, 225, 315):
        for d in (-6.0, 6.0):
            angles.add(math.radians(a + d) % (2 * math.pi))
    angles = sorted(angles)

    def square(h, z):
        pts = []
        for a in angles:
            c, s = math.cos(a), math.sin(a)
            t = h / max(abs(c), abs(s))
            pts.append(Vector((c * t, s * t, z)))
        return pts

    def circle(r, z):
        return [Vector((r * math.cos(a), r * math.sin(a), z)) for a in angles]

    shape.begin()
    rings = [square(half - 0.01, -0.03), square(half, 0.02), square(half, top - cham), square(half - cham, top),
             circle(bowl + 0.012, top), circle(bowl, top - 0.012), circle(bowl * 0.95, top - 0.05), circle(bowl * 0.78, top - 0.095),
             circle(bowl * 0.45, top - depth + 0.006), circle(0.0001, top - depth)]
    shape._rings([shape._verts(r) for r in rings], True, True, True)
    shape.end(rng.random())
    # a low rough stone it stands on, a little wider
    shape.begin()
    verts = shape.rock(Vector((0.0, 0.0, -0.01)), 0.3, rng, squash=(1.05, 1.0, 0.12), jitter=0.12, subdivisions=2)
    for v in verts:
        if v.co.z < 0:
            v.co.z *= 0.3          # sunk no deeper than the round stone's foot (it reached 0.137 m under the ground)
    shape.end(rng.random())


def _foot_stones(shape, rng, square):
    """The front stone to crouch on, a stone either side, low and sunk, each its own piece of the photograph."""
    places = [((0.0, -0.56, 0.0), 0.25, (1.0, 0.72, 0.28)), ((-0.47, -0.16, 0.0), 0.17, (0.9, 0.85, 1.2)),
              ((0.46, -0.2, 0.0), 0.14, (1.0, 0.9, 0.9))]
    for (centre, size, squash) in places:
        shape.begin()
        c = Vector(centre) + Vector((rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0.0))
        verts = shape.rock(c, size, rng, squash=squash, jitter=0.18, subdivisions=2)
        low = min(v.co.z for v in verts)
        for v in verts:
            v.co.z -= low + size * squash[2] * 0.25           # sunk a quarter of its height into the ground
            if v.co.z < 0:
                v.co.z *= 0.3
        shape.end(rng.random())


def build(collection, seed=0, stone='round', spout=True, ladle=True):
    if stone not in STONES:
        raise ValueError("stone is one of %s, not %r" % (', '.join(repr(k) for k in STONES), stone))
    rng = shapes.rng_for(PART, seed)
    made = []
    basin = garden.Shape()
    (_round_stone if stone == 'round' else _square_stone)(basin, rng)
    made.append(basin.finish('%s stone' % PART, collection, garden.garden_stone(), smooth=True, sharp=50.0))
    feet = garden.Shape()
    _foot_stones(feet, rng, stone == 'square')
    made.append(feet.finish('%s foot stones' % PART, collection, garden.garden_stone(), smooth=True, sharp=60.0))

    # the water standing in the bowl, ringed where the stream lands
    landing = Vector((0.03, 0.05, WATER))
    water = garden.Shape()
    radius = 0.165 if stone == 'round' else 0.148
    water.lathe([(0.0, WATER), (radius, WATER)], segments=40, open_ends=True)
    made.append(water.finish('%s water' % PART, collection, garden.still_water(PART, landing if spout else None), smooth=True))

    # pebbles in the hollow between the stones, and moss cushions round the foot
    pebbles = garden.Shape()
    for k in range(34):
        a = rng.uniform(math.radians(200), math.radians(340))
        r = rng.uniform(0.33, 0.5)
        c = Vector((r * math.cos(a), r * math.sin(a) * 0.95, 0.0))
        size = rng.uniform(0.014, 0.03)
        verts = pebbles.rock(c, size, rng, squash=(1.0, 0.85, 0.55), jitter=0.2)
        low = min(v.co.z for v in verts)
        for v in verts:
            v.co.z -= low + size * 0.15
    made.append(pebbles.finish('%s pebbles' % PART, collection, PEBBLES, smooth=True))
    cushions = garden.Shape()
    for k in range(6):
        a = rng.uniform(0, 2 * math.pi)
        if -2.0 < a - math.pi * 1.5 < 0.6 and k < 3:
            a += 1.4
        r = rng.uniform(0.3, 0.42)
        c = Vector((r * math.cos(a), r * math.sin(a), 0.0))
        size = rng.uniform(0.08, 0.14)
        verts = cushions.rock(c, size, rng, squash=(1.0, 0.8, 0.28), jitter=0.12, subdivisions=2)
        low = min(v.co.z for v in verts)
        for v in verts:
            v.co.z -= low + size * 0.08
    made.append(cushions.finish('%s moss' % PART, collection, garden.moss_cushion(), smooth=True))

    old = garden.bamboo('weathered')
    if spout:
        bam = garden.Shape()
        post = Vector((0.13, 0.5, 0.0))
        garden.culm(bam, post + Vector((0, 0, -0.04)), post + Vector((0, 0, 0.93)), 0.042, rng, node_gap=0.3)
        start = Vector((post.x, post.y + 0.07, 0.86))
        mouth = Vector((0.05, 0.13, 0.64))
        garden.culm(bam, start, mouth, 0.026, rng, node_gap=0.32, slant=1.2)
        # the second, shorter post under the pipe's middle, the pipe resting in its notch
        mid = start.lerp(mouth, 0.5)
        garden.culm(bam, Vector((mid.x + 0.02, mid.y, -0.04)), Vector((mid.x + 0.02, mid.y, mid.z - 0.026)), 0.03, rng, node_gap=0.25)
        made.append(bam.finish('%s spout' % PART, collection, old, smooth=True, sharp=50.0))
        # the dark hollow inside the pipe's mouth, the bindings at the posts
        dark = garden.Shape()
        d = (mouth - start).normalized()
        garden.culm(dark, mouth - d * 0.09, mouth - d * 0.003, 0.02, rng, node_gap=5.0)
        for centre, r in ((Vector((mid.x + 0.02, mid.y, mid.z - 0.005)), 0.034), (Vector((post.x, post.y + 0.02, 0.86)), 0.048)):
            dark.cylinder(centre - Vector((0, 0, 0.012)), centre + Vector((0, 0, 0.012)), r, segments=14)
        made.append(dark.finish('%s spout bindings' % PART, collection, garden.cord(), smooth=True))
        # the stream: from the mouth's lower lip, falling into the bowl
        lip = mouth + d * 0.026 * 1.2 * 0.6 - Vector((0, 0, 0.024))
        flow = Vector((d.x, d.y, 0.0)).normalized()
        pts, radii = [], []
        drop = lip.z - WATER
        for k in range(12):
            f = k / 11.0
            pts.append(lip + flow * (0.05 * f) - Vector((0, 0, drop * f * f + 0.002 * f)))
            radii.append(0.006 - 0.0025 * f)
        landing.x, landing.y = pts[-1].x, pts[-1].y
        stream = garden.Shape()
        stream.sweep(pts, 0.005, sides=8, radii=radii)
        obj = stream.finish('%s stream' % PART, collection, garden.falling_water(), smooth=True)
        obj.visible_shadow = False
        made.append(obj)
    if ladle:
        dip = garden.Shape()
        a0 = Vector((-0.3, -0.12, RIM + 0.012))
        a1 = Vector((0.17, -0.06, RIM + 0.012))
        garden.culm(dip, a0, a1, 0.0065, rng, node_gap=0.5, sides=6)
        cup = a1 + (a1 - a0).normalized() * 0.03
        dip.lathe([(0.0, RIM - 0.002), (0.036, RIM - 0.002), (0.037, RIM + 0.075), (0.032, RIM + 0.075), (0.031, RIM + 0.006), (0.0, RIM + 0.006)],
                  segments=20, matrix=Matrix.Translation((cup.x, cup.y, 0.0)))
        made.append(dip.finish('%s ladle' % PART, collection, old, smooth=True, sharp=50.0))
    return made
