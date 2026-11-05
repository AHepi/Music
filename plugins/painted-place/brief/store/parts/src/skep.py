"""
skep: a round farm skep (a woven willow basket for carrying roots, chaff or muck), about 0.55 m across: rows of willow
rods woven in and out over the stakes on a woven base, a thicker twisted row at the foot and under the rim, a rope-like
border of three twisted strands, and two loop handles of twisted willow rising from the rim at the sides (+X and -X);
greyed and dark with wet, the border and handles rubbed pale by hands. Filled, a heap of mangold roots stands in its
mouth. Foot at z = 0.

Options:
    filled   True (default): mangold roots heaped in its mouth, crowns and tails over the rim; False: empty
    seed     the rods' shades and wobble, the roots

Where it came from: '/home/claude/build-54-barn/dress/render_final.py', skep() (line 1132) and the roots put in it
(line 1185): ten thick woven bands, a rim tube and two loops; rebuilt here with twenty finer rows, twisted rows at the
foot and the top, a three-strand border, twisted handles and a woven base.
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
import _shapes_barn as barn  # noqa: E402

PART = 'skep'

CARD = {
    'name': PART,
    'what': 'a round woven willow skep (farm basket) about 0.55 m across: rods woven in and out over the stakes, a three-strand border '
            'and two twisted loop handles (at +X and -X), greyed and wet, the rim rubbed pale; filled with mangold roots or empty',
    'size_m': (0.58, 0.58, 0.48),
    'options': {
        'filled': 'True (default): mangold roots heaped in its mouth, crowns and tails over the rim; False: empty',
        'seed': "the rods' shades and wobble, the roots (default 0)",
    },
    'materials': ['PART • skep: willow', 'PART • skep: willow rim, rubbed pale', 'PART • skep: dark inside',
                  'PART • skep: mangold, soiled', 'PART • skep: roots below'],
    'source': "'/home/claude/build-54-barn/dress/render_final.py', skep() (line 1132) and the roots put in it (line 1185)",
    'views': 'reads from every side; the handles are at the sides (+X, -X)',
    'trap': 'the rim and handles are rubbed pale on purpose: with the rim as dark as the weave, the mouth of the basket does not show at a distance',
}

R_FOOT = 0.20          # outside radius of the weave at its foot
R_TOP = 0.27           # and under the border
HEIGHT = 0.33          # the weave's top
ROWS = 20
STAKES = 26


def willow_material():
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_name = 'rod_tone'
        along = nodes.new('ShaderNodeMapping')
        along.inputs['Scale'].default_value = (3.0, 3.0, 60.0)
        links.new(vec, along.inputs['Vector'])
        streak = shapes.noise_fac(nodes, links, along.outputs['Vector'], 1.0, detail=4.0)
        blotch = shapes.noise_fac(nodes, links, vec, 6.0, detail=3.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, streak, 0.35, 0.65), (0.065, 0.045, 0.024), (0.16, 0.115, 0.064))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, blotch, 0.4, 0.7, 0.0, 0.5), colour, (0.05, 0.045, 0.035))
        shade = nodes.new('ShaderNodeVectorMath')
        shade.operation = 'SCALE'
        links.new(colour, shade.inputs[0])
        links.new(shapes.map_range(nodes, links, tone.outputs['Fac'], 0.0, 1.0, 0.72, 1.22), shade.inputs['Scale'])
        links.new(shade.outputs[0], principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, blotch, 0.3, 0.7, 0.5, 0.75), principled.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, streak, 0.3, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.1, 0.075, 0.045, 1.0)
    return shapes.part_material(PART, 'willow', maker)


def rim_material():
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        n = shapes.noise_fac(nodes, links, vec, 30.0, detail=4.0)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, n, 0.35, 0.65), (0.13, 0.097, 0.056), (0.25, 0.19, 0.11))
        links.new(colour, principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.45
        links.new(shapes.bump(nodes, links, n, 0.2, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.2, 0.15, 0.09, 1.0)
    return shapes.part_material(PART, 'willow rim, rubbed pale', maker)


def dark_material(what, colour):
    def maker(m, nodes, links, principled):
        principled.inputs['Base Color'].default_value = (*colour, 1.0)
        principled.inputs['Roughness'].default_value = 0.85
        m.diffuse_color = (*colour, 1.0)
    return shapes.part_material(PART, what, maker)


def radius_at(z):
    return R_FOOT + (R_TOP - R_FOOT) * max(0.0, min(1.0, z / HEIGHT))


def build(collection, seed=0, filled=True):
    if not isinstance(filled, bool):
        raise ValueError('skep filled is True or False, not %r' % (filled,))
    rng = shapes.rng_for(PART, seed)
    objects = []
    basket = shapes.Shape()
    barn.number_layers(basket, faces=('rod_tone',))
    tone_layer = basket.bm.faces.layers.float['rod_tone']

    def tone_new(faces, value):
        for f in faces:
            if f is not None:
                f[tone_layer] = value

    # ------------------------------------------------------------------ the woven sides: rows in and out over the stakes
    z0 = 0.024
    bh = (HEIGHT - z0) / ROWS
    wobble = [rng.uniform(-0.002, 0.002) for _ in range(ROWS)]
    for i in range(ROWS):
        z = z0 + bh * (i + 0.5)
        wale = i < 2 or i >= ROWS - 2               # twisted rows at the foot and under the border
        rv = bh * (0.62 if wale else 0.56)
        section = [(0.7 * rv * math.cos(a), rv * math.sin(a)) for a in (2 * math.pi * k / 6 for k in range(6))]
        phase = math.pi * (i % 2) + rng.uniform(-0.15, 0.15)
        pts = []
        count = 104
        for k in range(count):
            th = 2 * math.pi * k / count
            if wale:
                bump = 0.0035 * abs(math.sin(STAKES * 1.5 * th + i))          # three rods twisting
            else:
                bump = 0.0045 * math.sin(STAKES / 2 * th + phase)              # in front of a stake, behind the next
            r = radius_at(z) + bump + wobble[i] + 0.0015 * math.sin(3 * th + i * 1.7)
            pts.append(Vector((r * math.cos(th), r * math.sin(th), z + 0.0012 * math.sin(2 * th + i))))
        before = len(basket.bm.faces)
        basket.material_index = 0
        basket.sweep(pts, rv, closed=True, section=section)
        basket.bm.faces.ensure_lookup_table()
        tone_new(basket.bm.faces[before:], rng.random())

    # ------------------------------------------------------------------ the woven base: a spiral of rod over radial sticks
    before = len(basket.bm.faces)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        basket.cylinder((0.0, 0.0, 0.007), (math.cos(a) * (R_FOOT - 0.006), math.sin(a) * (R_FOOT - 0.006), 0.007), 0.0065, segments=6)
    spiral = []
    turns = 13
    for k in range(turns * 24 + 1):
        s = k / (turns * 24)
        r = 0.015 + (R_FOOT - 0.022) * s
        th = 2 * math.pi * turns * s
        spiral.append(Vector((r * math.cos(th), r * math.sin(th), 0.016 + 0.002 * math.sin(th * 4))))
    basket.sweep(spiral, 0.0062, sides=5)
    basket.bm.faces.ensure_lookup_table()
    tone_new(basket.bm.faces[before:], 0.4)

    # ------------------------------------------------------------------ the border: three strands twisted round the rim
    basket.material_index = 1
    zc = HEIGHT + 0.011
    rc = R_TOP + 0.003
    twists = 38
    for strand in range(3):
        pts = []
        count = twists * 9
        for k in range(count):
            th = 2 * math.pi * k / count
            q = twists * th + 2 * math.pi * strand / 3
            out = Vector((math.cos(th), math.sin(th), 0.0))
            pts.append(Vector((rc * math.cos(th), rc * math.sin(th), zc)) + out * (0.0105 * math.cos(q)) + Vector((0, 0, 0.0105 * math.sin(q))))
        basket.sweep(pts, 0.0085, sides=6, closed=True)
    # the two handles: twisted loops rising from the border at +X and -X
    for side in (0.0, math.pi):
        for strand in range(2):
            pts = []
            count = 60
            for k in range(count + 1):
                s = k / count
                th = side + (s - 0.5) * 0.62
                lift = 0.078 * math.sin(math.pi * s)
                centre = Vector(((rc + 0.004) * math.cos(th), (rc + 0.004) * math.sin(th), zc + lift))
                tangent = Vector((-math.sin(th), math.cos(th), 0.0))
                q = 2 * math.pi * 6 * s + math.pi * strand
                out = Vector((math.cos(th), math.sin(th), 0.0))
                upish = tangent.cross(out).normalized()
                pts.append(centre + out * (0.0062 * math.cos(q)) + upish * (0.0062 * math.sin(q)))
            basket.sweep(pts, 0.0068, sides=6)

    # ------------------------------------------------------------------ a dark lining just inside, so no light shows through
    basket.material_index = 2
    basket.lathe([(R_FOOT - 0.012, 0.02), (R_TOP - 0.011, HEIGHT - 0.004)], segments=40, open_ends=True)
    objects.append(basket.finish('skep basket', collection,
                                 [willow_material(), rim_material(), dark_material('dark inside', (0.025, 0.018, 0.011))],
                                 smooth=True, sharp=None))

    # ------------------------------------------------------------------ roots heaped in its mouth
    if filled:
        bed = shapes.Shape()
        bed.sphere((0.0, 0.0, 0.25), 1.0, segments=24, rings=8, squash=(radius_at(0.25) - 0.015, radius_at(0.25) - 0.015, 0.06))
        objects.append(bed.finish('skep roots below', collection, dark_material('roots below', (0.035, 0.016, 0.01)), smooth=True))
        roots = shapes.Shape()

        def inside(points):
            """Keep a root inside the basket below its rim (above the rim its tail may hang out)."""
            worst = 0.0
            direction = Vector((0.0, 0.0, 0.0))
            for p in points:
                if p.z > HEIGHT + 0.02:
                    continue
                r = math.hypot(p.x, p.y)
                excess = r - (radius_at(p.z) - 0.016)
                if excess > worst:
                    worst = excess
                    direction = Vector((-p.x, -p.y, 0.0)).normalized()
            low = min(p.z for p in points)
            return direction * worst + Vector((0.0, 0.0, max(0.0, 0.25 - low)))

        layers = ((0.0, 0.31, 7), (0.09, 0.37, 5), (0.06, 0.43, 3))
        for (spread, z, count) in layers:
            for k in range(count):
                a = 2 * math.pi * k / count + rng.uniform(-0.4, 0.4)
                d = rng.uniform(0.04, 0.12) if spread == 0.0 else rng.uniform(0.0, spread)
                # the top ones lie across the basket, so from the front their length shows (end on, a root reads as a round fruit)
                turn = rng.choice((0.0, math.pi)) + rng.uniform(-0.7, 0.7) if z > 0.35 else rng.uniform(0, 2 * math.pi)
                tilt = rng.uniform(-0.32, 0.32)
                axis = Vector((math.cos(turn) * math.cos(tilt), math.sin(turn) * math.cos(tilt), math.sin(tilt))).normalized()
                length = rng.uniform(0.26, 0.36)
                radius = rng.uniform(0.045, 0.06)
                centre = Vector((d * math.cos(a), d * math.sin(a), z))
                crown = centre - axis * (0.42 * length)
                matrix = shapes.to4(barn.root_frame(axis, rng.uniform(0, 2 * math.pi)), crown)
                barn.mangold(roots, matrix, length, radius, rng, adjust=inside)
        objects.append(roots.finish('skep roots', collection, barn.mangold_material(PART), smooth=True, sharp=None))
    return objects
