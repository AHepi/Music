"""
window_box: a timber window box on a tenement sill, about 1915, with red clay pots of zonal geraniums standing in it:
a box of rough sawn boards gone grey (each board its own shade), corner battens, two wedges under its front to keep it
level on the sloping stone sill; in it, clay pots with dark earth, each a geranium of round scalloped leaves with the
dark ring of the zonal kind on stalks, and heads of small red flowers held up above the leaves on long stalks, a few
heads going over and brown.

The origin is the middle of the box's foot on the sill; its back is towards the window at +Y (the back board on the
plane y = 0).

Options:
    length   the box's length along the sill, metres (default 1.06; about the window's width and 10 cm)
    pots     how many pots stand in it (default 4)
    flowers  how many flower heads: 1 a box in full flower, 0.5 a few heads (default 1.0; 0.1 to 2)
    seed     the plants' leaves and heads, the boards' shades

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', geranium() (lines 1635-1660: a cone pot,
leaves as flat boxes on stalks, flower heads as single boxes) and the window box over the hero shop (lines 1721-1730: a
box with four geraniums). Rebuilt here with round scalloped zoned leaves, heads of many small flowers, real pots with
earth and a box made of boards.
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
import _shapes_street_shop as street  # noqa: E402

PART = 'window_box'

CARD = {
    'name': PART,
    'what': 'a grey timber window box on a sill with red clay pots of zonal geraniums: round scalloped leaves with their dark ring, '
            'heads of small red flowers on long stalks, a few gone brown',
    'size_m': (1.10, 0.31, 0.53),
    'options': {
        'length': "the box's length along the sill, metres (default 1.06; about the window's width and 10 cm)",
        'pots': 'how many pots stand in it (default 4)',
        'flowers': 'how many flower heads: 1 a box in full flower, 0.5 a few heads (default 1.0; 0.1 to 2)',
        'seed': "the plants' leaves and heads, the boards' shades (default 0)",
    },
    'materials': ['SURFACE • rough_wood (window_box), each board its own shade', 'MADE • dirt, dark', 'PART • window_box: clay pot',
                  'PART • window_box: geranium leaves', 'PART • window_box: geranium flowers'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', geranium() (lines 1635-1660) and the window box (lines 1721-1730)",
    'views': 'reads from every side; the flowers are made to show from the street below, from the front and the sides',
    'trap': "red flower heads go near-black at dusk unless a light reaches them (a lit window's own light, a lamp); the leaves "
            "stand 8 cm out past the box's front, over the sill's edge",
}

BOX_D, BOX_H, T = 0.20, 0.16, 0.022


def clay(part):
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vec, sep.inputs[0])
        n = shapes.noise_fac(nodes, links, vec, 14.0, detail=4.0)
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, n, 0.3, 0.7), (0.15, 0.045, 0.02), (0.24, 0.08, 0.035))
        salt = shapes.math_node(nodes, links, 'MULTIPLY', shapes.map_range(nodes, links, n, 0.55, 0.75),
                                shapes.map_range(nodes, links, sep.outputs['Z'], 0.12, 0.2))
        col = shapes.mix_colour(nodes, links, salt, col, (0.30, 0.26, 0.21))
        green = shapes.map_range(nodes, links, sep.outputs['Z'], 0.10, 0.05, 0.0, 0.8)
        col = shapes.mix_colour(nodes, links, green, col, (0.03, 0.045, 0.02))
        links.new(col, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.85
        links.new(shapes.bump(nodes, links, n, 0.2, 0.002), p.inputs['Normal'])
        m.diffuse_color = (0.2, 0.065, 0.03, 1.0)
    return shapes.part_material(part, 'clay pot', maker)


def leaves(part):
    """Zonal geranium leaves: mid green, a dark brownish ring part way out (the point number 'ring': 0 at the leaf's
    middle, 1 at its edge), each leaf its own shade and a few yellowing ('tone')."""
    def maker(m, nodes, links, p):
        ring = nodes.new('ShaderNodeAttribute')
        ring.attribute_type = 'GEOMETRY'
        ring.attribute_name = 'ring'
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'GEOMETRY'
        tone.attribute_name = 'tone'
        base = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, tone.outputs['Fac'], 0.0, 0.85), (0.02, 0.05, 0.014), (0.045, 0.085, 0.022))
        base = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, tone.outputs['Fac'], 0.88, 0.95), base, (0.11, 0.10, 0.025))
        band = shapes.math_node(nodes, links, 'MULTIPLY', shapes.map_range(nodes, links, ring.outputs['Fac'], 0.42, 0.52),
                                shapes.map_range(nodes, links, ring.outputs['Fac'], 0.68, 0.6))
        col = shapes.mix_colour(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', band, 0.7), base, (0.024, 0.026, 0.009))
        links.new(col, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.6
        p.inputs['Specular IOR Level'].default_value = 0.3
        m.diffuse_color = (0.03, 0.06, 0.018, 1.0)
    return shapes.part_material(part, 'geranium leaves', maker)


def flowers_material(part):
    def maker(m, nodes, links, p):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'GEOMETRY'
        tone.attribute_name = 'tone'
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, tone.outputs['Fac'], 0.0, 0.8), (0.62, 0.035, 0.02), (0.45, 0.02, 0.03))
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, tone.outputs['Fac'], 0.82, 0.9), col, (0.09, 0.03, 0.015))
        links.new(col, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.6
        p.inputs['Sheen Weight'].default_value = 0.5
        m.diffuse_color = (0.55, 0.03, 0.02, 1.0)
    return shapes.part_material(part, 'geranium flowers', maker)


def build(collection, seed=0, length=1.06, pots=4, flowers=1.0):
    L = barn.number('window_box length', length, 0.4, 3.0)
    count = int(round(barn.number('window_box pots', pots, 1, 12)))
    flowers = barn.number('window_box flowers', flowers, 0.1, 2.0)
    rng = shapes.rng_for(PART, seed)
    objects = []
    wood = barn.shaded_surface('rough_wood', PART, low=0.65, high=1.15, Grime=0.55, Wet=0.12)

    # ------------------------------------------------------------------ the box: boards, battens, wedges
    y0, y1 = -BOX_D, 0.0
    z0 = 0.02                                   # on its wedges
    pieces = [((-L / 2, y0 + T / 2, z0 + BOX_H / 2), (L / 2, y0 + T / 2, z0 + BOX_H / 2), T, BOX_H, (0, -1, 0)),     # front
              ((-L / 2, y1 - T / 2, z0 + BOX_H / 2), (L / 2, y1 - T / 2, z0 + BOX_H / 2), T, BOX_H, (0, -1, 0)),     # back
              ((-L / 2 + T / 2, y0 + T, z0 + BOX_H / 2), (-L / 2 + T / 2, y1 - T, z0 + BOX_H / 2), T, BOX_H, (1, 0, 0)),
              ((L / 2 - T / 2, y0 + T, z0 + BOX_H / 2), (L / 2 - T / 2, y1 - T, z0 + BOX_H / 2), T, BOX_H, (1, 0, 0)),
              ((-L / 2 + T, (y0 + y1) / 2, z0 + T / 2), (L / 2 - T, (y0 + y1) / 2, z0 + T / 2), BOX_D - 2 * T, T, (0, 0, 1))]
    for k, (a, b, w, h, _) in enumerate(pieces):
        # each board along its own length: `w` level across it, `h` up (the grain of the photographed wood runs along it)
        objects.append(shapes.timber(collection, 'window_box board %d' % (k + 1), a, b, w, h, wood, rng=rng, chamfer=0.003, shift=0.3))
    for x in (-L / 2 - 0.004, L / 2 + 0.004):
        objects.append(shapes.timber(collection, 'window_box batten %s' % ('left' if x < 0 else 'right'), (x, y0 - 0.004, z0),
                                     (x, y0 - 0.004, z0 + BOX_H), 0.03, 0.03, wood, rng=rng, chamfer=0.003, shift=0.3))
    wedges = shapes.Shape()
    for x in (-L * 0.3, L * 0.3):
        wedges.prism([(0.0, 0.0), (0.12, 0.0), (0.12, 0.022), (0.0, 0.0)][:3], -0.03, 0.03,
                     matrix=Matrix(((0.0, 0.0, 1.0, x), (-1.0, 0.0, 0.0, y1 - 0.02), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))))
    objects.append(wedges.finish('window_box wedges', collection, wood, smooth=False))

    # ------------------------------------------------------------------ pots, earth, geraniums
    pot_shape = shapes.Shape()
    earth = shapes.Shape()
    leaf_shape = shapes.Shape()
    barn.number_layers(leaf_shape, points=('ring', 'tone'))
    bloom = shapes.Shape()
    barn.number_layers(bloom, points=('tone',))
    floor = z0 + T
    pot_h, rim_r = 0.15, 0.072
    step = (L - 2 * T) / count
    for k in range(count):
        cx = -L / 2 + T + step * (k + 0.5) + rng.uniform(-0.01, 0.01)
        cy = (y0 + y1) / 2 + rng.uniform(-0.006, 0.006)
        m = Matrix.Translation((cx, cy, floor))
        pot_shape.lathe([(0.0, 0.0), (0.05, 0.0), (rim_r - 0.008, pot_h - 0.035), (rim_r, pot_h - 0.034), (rim_r + 0.004, pot_h),
                         (rim_r - 0.006, pot_h), (rim_r - 0.01, pot_h - 0.03), (0.0, pot_h - 0.03)], segments=18, matrix=m)
        earth.lathe([(0.0, pot_h - 0.022), (rim_r - 0.008, pot_h - 0.022), (rim_r - 0.008, pot_h - 0.014), (0.0, pot_h - 0.012)],
                    segments=14, matrix=m)
        base = Vector((cx, cy, floor + pot_h - 0.015))
        # leaves on stalks
        for j in range(24):
            a = rng.uniform(0, 2 * math.pi)
            reach = rng.uniform(0.02, 0.12) * min(1.0, step / 0.25 + 0.3)
            hgt = rng.uniform(0.04, 0.15) * (1.0 - 0.4 * reach / 0.12) + 0.02
            centre = base + Vector((math.cos(a) * reach, math.sin(a) * reach * 0.9 - 0.02, hgt))
            leaf_shape.sweep([base, base + (centre - base) * 0.5 + Vector((0, 0, 0.03)), centre], 0.003, sides=4)
            r = rng.uniform(0.036, 0.056)
            normal = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45 - 0.25, 1.0)).normalized()
            frame = shapes.frame_along(normal)
            tone = rng.random()
            ring_pts = []
            for q in range(14):
                t = 2 * math.pi * q / 14
                scallop = 1.0 + 0.08 * math.cos(7 * t) - (0.25 if q == 0 else 0.0)
                cup = 0.15 * r
                ring_pts.append(centre + frame @ Vector((math.cos(t) * r * scallop, math.sin(t) * r * scallop, cup)))
            verts = leaf_shape._verts(ring_pts)
            middle = leaf_shape._verts([centre])[0]
            for q in range(14):
                leaf_shape._face([middle, verts[q], verts[(q + 1) % 14]])
            barn.point_numbers(leaf_shape, verts, ring=1.0, tone=tone)
            barn.point_numbers(leaf_shape, [middle], ring=0.0, tone=tone)
        # flower heads on long stalks
        heads = max(1, int(round(rng.uniform(3, 5) * flowers)))
        for j in range(heads):
            a = rng.uniform(0, 2 * math.pi)
            reach = rng.uniform(0.0, 0.09)
            top = base + Vector((math.cos(a) * reach, math.sin(a) * reach * 0.8 - 0.03, rng.uniform(0.22, 0.29)))
            leaf_shape.sweep(shapes.smooth_path([base + Vector((0, 0, 0.05)), base.lerp(top, 0.5) + Vector((0.01, -0.01, 0.0)), top], steps=3),
                             0.0025, sides=4)
            tone = rng.random() if rng.random() > 0.15 else 0.95
            head_r = rng.uniform(0.035, 0.05)
            for q in range(13):
                d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 1))).normalized()
                c = top + d * head_r * rng.uniform(0.5, 1.0) + Vector((0, 0, head_r * 0.4))
                start = len(bloom.bm.verts)
                bloom.sphere(c, rng.uniform(0.011, 0.016), segments=6, rings=3, squash=(1.0, 1.0, 0.6))
                bloom.bm.verts.ensure_lookup_table()
                barn.point_numbers(bloom, [bloom.bm.verts[i] for i in range(start, len(bloom.bm.verts))], tone=tone)
    objects.append(pot_shape.finish('window_box pots', collection, clay(PART), smooth=True, sharp=50))
    objects.append(earth.finish('window_box earth', collection, 'MADE • dirt, dark', smooth=False))
    objects.append(leaf_shape.finish('window_box geranium leaves', collection, leaves(PART), smooth=True, sharp=None))
    objects.append(bloom.finish('window_box geranium flowers', collection, flowers_material(PART), smooth=True, sharp=None))
    return objects
