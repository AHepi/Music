"""
wooden_bucket: a Japanese wooden bucket (oke, the hand kind, te-oke) as coopers make it: cedar staves standing side by
side round a round bottom set in a groove, held by two copper hoops, two staves left long at the sides with a bar
through them for a handle; water standing in it, a bamboo dipper (hishaku) laid across its rim. Each stave shows its
own part of the photographed wood, its grain running up it; the rim a little uneven where the staves were trimmed.

Options:
    handle   (default True) the two long staves and the bar across them; False: a plain round tub, all staves level
    dipper   (default True) the bamboo dipper laid across the rim; False: none
    seed     the staves' widths, heights and shades, where the dipper lies

Where it came from: the wooden bucket in '/home/claude/build-57-garden/second pass/render_final.py' (lines 1772-1798: a
lathe of 'SURFACE • old_planks_02' with two copper hoops, a water disc and a dipper of two cylinders), rebuilt stave by
stave with a bottom, the handle staves and bar, and a dipper with a hollow cup.
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

PART = 'wooden_bucket'
COPPER = 'MADE • old copper'
R_TOP, R_FOOT, HEIGHT, WALL = 0.168, 0.152, 0.26, 0.014
WATER = 0.2

CARD = {
    'name': PART,
    'what': 'a Japanese wooden hand bucket (te-oke): cedar staves round a set-in bottom, two copper hoops, two long staves with a '
            'bar for a handle, water in it, a bamboo dipper across the rim',
    'size_m': (0.37, 0.46, 0.38),
    'options': {
        'handle': 'True (default): two long staves at the sides with a bar across; False: a plain round tub',
        'dipper': 'True (default): the bamboo dipper laid across the rim; False: none',
        'seed': "the staves' widths, heights and shades, where the dipper lies (default 0)",
    },
    'materials': ['SURFACE • rough_wood (wooden_bucket)', COPPER, 'PART • wooden_bucket: still water', 'PART • garden: bamboo, weathered'],
    'source': "the wooden bucket in '/home/claude/build-57-garden/second pass/render_final.py' (lines 1772-1798)",
    'views': 'reads from every side; the handle staves stand at the sides (+X, -X), the dipper lies across front to back',
    'trap': 'pale new wood would read as a cardboard tub: it is wet cedar, darker than the path; the copper hoops are what catch a lamp',
}


def radius_at(z):
    return R_FOOT + (R_TOP - R_FOOT) * z / HEIGHT


def build(collection, seed=0, handle=True, dipper=True):
    rng = shapes.rng_for(PART, seed)
    wood = shapes.surface_copy('SURFACE • rough_wood', PART, Darken=0.62, Wet=0.35, Grime=0.5)
    staves = garden.Shape()
    count = 18
    widths = [rng.uniform(0.8, 1.2) for _ in range(count)]
    total = sum(widths)
    a = rng.uniform(0, 2 * math.pi / count)
    gap = 0.0025                                   # radians: the dark joint between two staves
    long_at = []
    for k in range(count):
        span = 2 * math.pi * widths[k] / total
        a0, a1 = a + gap / 2, a + span - gap / 2
        mid = (a0 + a1) / 2
        top = HEIGHT + rng.uniform(-0.004, 0.002)
        is_long = handle and (abs(math.cos(mid)) > 0.985)
        if is_long:
            top = HEIGHT + 0.12
            long_at.append(mid)
        staves.begin()
        rings = []
        for z, inset in ((0.0, 0.003), (0.006, 0.0), (top - 0.004, 0.0), (top, 0.002)):
            outer = []
            inner = []
            for j in range(4):
                t = a0 + (a1 - a0) * j / 3
                ro = radius_at(min(z, HEIGHT)) - inset
                ri = radius_at(min(z, HEIGHT)) - WALL + inset * 0.5
                outer.append(Vector((ro * math.cos(t), ro * math.sin(t), z)))
                inner.append(Vector((ri * math.cos(t), ri * math.sin(t), z)))
            rings.append(outer + list(reversed(inner)))
        staves._rings([staves._verts(r) for r in rings], True, True, True)
        staves.end(rng.random())
        a += span
    # the bottom, set in a groove a little up the staves
    staves.begin()
    staves.cylinder((0.0, 0.0, 0.012), (0.0, 0.0, 0.03), radius_at(0.02) - WALL + 0.004, segments=36)
    staves.end(rng.random())
    if handle and len(long_at) >= 2:
        # the bar through the two long staves
        staves.begin()
        z = HEIGHT + 0.085
        staves.box((0.0, 0.0, z), (2 * R_TOP + 0.03, 0.024, 0.026))
        staves.end(rng.random())
    made = [staves.finish('%s staves' % PART, collection, wood, smooth=False, chamfer=0.0015)]
    hoops = garden.Shape()
    for z, h in ((0.045, 0.022), (0.205, 0.024)):
        r0, r1 = radius_at(z - h / 2) + 0.0005, radius_at(z + h / 2) + 0.0005
        hoops.lathe([(r0 - 0.002, z - h / 2), (r0 + 0.0025, z - h / 2), (r1 + 0.0025, z + h / 2), (r1 - 0.002, z + h / 2)], segments=48)
    made.append(hoops.finish('%s hoops' % PART, collection, COPPER, smooth=True, sharp=40.0))
    water = garden.Shape()
    water.lathe([(0.0, WATER), (radius_at(WATER) - WALL + 0.001, WATER)], segments=36, open_ends=True)
    made.append(water.finish('%s water' % PART, collection, garden.still_water(PART), smooth=True))
    if dipper:
        dip = garden.Shape()
        turn = rng.uniform(-0.35, 0.35) + math.pi / 2
        d = Vector((math.cos(turn), math.sin(turn), 0.0))
        # the cup stands in the water against one side, the handle rising over the far rim and out
        c = d * (R_TOP - 0.065)
        start = c - d * 0.03 + Vector((0, 0, WATER + 0.03))
        rest = -d * (R_TOP - 0.004) + Vector((0, 0, HEIGHT + 0.007))
        end = rest + (rest - start).normalized() * 0.13
        garden.culm(dip, start, end, 0.0065, rng, node_gap=0.5, sides=6)
        dip.lathe([(0.0, WATER - 0.03), (0.034, WATER - 0.03), (0.035, WATER + 0.045), (0.03, WATER + 0.045), (0.029, WATER - 0.024), (0.0, WATER - 0.024)],
                  segments=20, matrix=Matrix.Translation((c.x, c.y, 0.0)))
        made.append(dip.finish('%s dipper' % PART, collection, garden.bamboo('weathered'), smooth=True, sharp=50.0))
    return made
