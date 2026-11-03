"""
gas_lamp: a cast-iron street gas lamp of about 1900, as the street's lamp posts were. A round fluted base with a small
door for the gas tap, a fluted column, the ladder bar a lamplighter leant his ladder on, and a square lantern widening
upwards: four glass panes in an iron frame, a curved roof with a vent and finial, and inside it three gas mantles
hanging from the burner under a china hood.

Options:
    lit      True (default): the panes glow ('Lantern • glowing imperfect amber glass'), the mantles burn
             ('LAMP • honey flame glow') and a small warm point light sits among the mantles, in the part's collection.
             The panes and mantles cast no shadow, so that light comes out through the glass; the iron frame and roof
             still throw their shadows.
             False: cold, sooty glass and grey mantles, no light.

Where it came from: "46 townhouse - render_final.py" (procedural-textures/46 Pictures-only builders - three places),
the lamp posts in build_ground() (line 570), materials mat_iron (1072) and mat_lampglass (1201); rebuilt here as a whole
lamp that reads from every side (the source was tubes and a tapered glass box seen from one camera).
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_town as shapes  # noqa: E402

IRON = 'IRON • soot-black lamp posts'
GLOW_GLASS = 'Lantern • glowing imperfect amber glass'
FLAME = 'LAMP • honey flame glow'
CHINA = 'MADE • glazed china'

CARD = {
    'name': 'gas_lamp',
    'what': 'a cast-iron street gas lamp: fluted base and column, ladder bar, square lantern with glass panes and lit mantles',
    'size_m': (0.76, 0.44, 3.57),
    'options': {
        'lit': 'True (default): glowing panes and mantles and a warm point light (150 W) inside the lantern; False: cold glass, no light',
    },
    'materials': [IRON, GLOW_GLASS, FLAME, CHINA, 'PART • gas_lamp: soot-black iron, rusting at the foot',
                  'PART • gas_lamp: cold sooty glass', 'PART • gas_lamp: unlit mantle'],
    'source': '"46 townhouse - render_final.py", build_ground() lamp posts (line 570), mat_iron (1072), mat_lampglass (1201); '
              'builder\'s report "46 Townhouse builder\'s report.md"',
    'views': 'reads from every side; the base door faces -Y, the ladder bar runs along X',
    'trap': 'lit=True brings its own point light: a street of many lamps adds up; turn the light down rather than the panes',
}

LIGHT_POWER = 150.0


def _cold_glass(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    soot = shapes.map_range(nodes, links, shapes.noise_fac(nodes, links, vec, 9.0, detail=5.0, roughness=0.6), 0.40, 0.72)
    colour = shapes.mix_colour(nodes, links, soot, (0.16, 0.17, 0.17), (0.018, 0.017, 0.015))
    links.new(colour, principled.inputs['Base Color'])
    links.new(shapes.map_range(nodes, links, soot, 0.0, 1.0, 0.02, 0.40), principled.inputs['Roughness'])
    links.new(shapes.map_range(nodes, links, soot, 0.0, 1.0, 0.85, 0.0), principled.inputs['Transmission Weight'])
    principled.inputs['IOR'].default_value = 1.5
    m.diffuse_color = (0.03, 0.03, 0.03, 1.0)


def _foot_iron(m, nodes, links, principled):
    """The street's soot-black iron (same colour, gloss and metal as 'IRON • soot-black lamp posts'), with rust coming
    through in patches near the foot, where rain and road water sit, and road grime in the lowest few centimetres."""
    vec = shapes.own_coordinates(nodes)
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(vec, separate.inputs['Vector'])
    height = separate.outputs['Z']
    patches = shapes.noise_fac(nodes, links, vec, 16.0, detail=7.0, roughness=0.62, distortion=0.3)
    near_foot = shapes.map_range(nodes, links, height, 0.0, 0.30, 0.12, -0.10)
    rust = shapes.map_range(nodes, links, shapes.math_node(nodes, links, 'ADD', patches, near_foot), 0.60, 0.70, 0.0, 0.85)
    specks = shapes.map_range(nodes, links, shapes.noise_fac(nodes, links, vec, 55.0, detail=3.0), 0.72, 0.77, 0.0, 0.6)
    rust = shapes.math_node(nodes, links, 'MAXIMUM', rust, specks)
    shade = shapes.noise_fac(nodes, links, vec, 40.0, detail=4.0)
    rust_colour = shapes.mix_colour(nodes, links, shade, (0.026, 0.013, 0.007), (0.055, 0.024, 0.009))
    colour = shapes.mix_colour(nodes, links, rust, (0.018, 0.025, 0.026), rust_colour)
    grime = shapes.map_range(nodes, links, height, 0.0, 0.045, 1.0, 0.0)
    colour = shapes.mix_colour(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', grime, 0.55), colour, (0.021, 0.020, 0.018))
    links.new(colour, principled.inputs['Base Color'])
    rough = shapes.math_node(nodes, links, 'MAXIMUM', shapes.map_range(nodes, links, rust, 0.0, 1.0, 0.27, 0.78),
                             shapes.math_node(nodes, links, 'MULTIPLY', grime, 0.85))
    links.new(rough, principled.inputs['Roughness'])
    links.new(shapes.map_range(nodes, links, shapes.math_node(nodes, links, 'MAXIMUM', rust, grime), 0.0, 1.0, 0.68, 0.05),
              principled.inputs['Metallic'])
    links.new(shapes.bump(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', rust, shade), 0.35, 0.002),
              principled.inputs['Normal'])
    m.diffuse_color = (0.018, 0.025, 0.026, 1.0)


def _unlit_mantle(m, nodes, links, principled):
    principled.inputs['Base Color'].default_value = (0.20, 0.19, 0.17, 1.0)
    principled.inputs['Roughness'].default_value = 0.95
    m.diffuse_color = (0.2, 0.19, 0.17, 1.0)


def build(collection, seed=0, lit=True):
    rng = shapes.rng_for('gas_lamp', seed)
    objects = []

    # ------------------------------------------------------------------ base and column (cast iron, one object)
    iron = shapes.Shape()
    base = [
        (0.000, 0.000), (0.205, 0.000), (0.205, 0.028), (0.196, 0.036), (0.182, 0.040), (0.182, 0.056),
        (0.170, 0.066), (0.156, 0.084), (0.150, 0.100), (0.149, 0.112, 0.0), (0.147, 0.124, 0.10),
        (0.130, 0.505, 0.10), (0.128, 0.517, 0.0), (0.141, 0.528), (0.141, 0.548), (0.122, 0.562),
        (0.104, 0.600), (0.093, 0.680), (0.106, 0.694), (0.106, 0.712), (0.088, 0.726), (0.080, 0.820),
        (0.092, 0.834), (0.092, 0.852), (0.072, 0.866), (0.000, 0.866),
    ]
    iron.lathe(base, segments=64, flutes=16)
    # the door for the gas tap on the front of the base, its hinge and its keyhole boss
    iron.box((0.0, -0.140, 0.335), (0.108, 0.026, 0.200))
    iron.box((0.0, -0.152, 0.335), (0.088, 0.008, 0.176))
    iron.cylinder((0.0, -0.156, 0.300), (0.0, -0.166, 0.300), 0.010, segments=10)
    iron.cylinder((-0.050, -0.150, 0.250), (-0.050, -0.150, 0.420), 0.0065, segments=8)
    foot = shapes.part_material('gas_lamp', 'soot-black iron, rusting at the foot', _foot_iron)
    objects.append(iron.finish('gas_lamp base', collection, foot, smooth=True, sharp=40))

    iron = shapes.Shape()
    column = [
        (0.000, 0.850), (0.066, 0.850), (0.066, 0.880), (0.063, 0.890, 0.0), (0.062, 0.905, 0.075),
        (0.047, 2.560, 0.075), (0.047, 2.575, 0.0), (0.056, 2.585), (0.056, 2.600), (0.000, 2.600),
    ]
    iron.lathe(column, segments=48, flutes=12)
    # the capital, the collar the ladder bar passes through, and the cup the lantern sits in
    head = [
        (0.000, 2.595), (0.050, 2.595), (0.064, 2.612), (0.064, 2.650), (0.052, 2.662), (0.046, 2.690),
        (0.058, 2.702), (0.058, 2.716), (0.050, 2.726), (0.054, 2.760), (0.064, 2.788), (0.068, 2.804),
        (0.068, 2.814), (0.000, 2.814),
    ]
    iron.lathe(head, segments=32)
    # the ladder bar, with a ball at each end and a small scroll under each arm
    bar_z = 2.632
    iron.cylinder((-0.335, 0.0, bar_z), (0.335, 0.0, bar_z), 0.0165, segments=12)
    for sx in (-1, 1):
        iron.sphere((sx * 0.352, 0.0, bar_z), 0.028, segments=14, rings=8)
        iron.cylinder((sx * 0.322, 0.0, bar_z), (sx * 0.330, 0.0, bar_z), 0.024, segments=12)
        scroll = []
        for k in range(13):
            t = k / 12.0
            a = math.pi * 1.25 * t
            r = 0.095 * (1.0 - 0.55 * t)
            scroll.append((sx * (0.06 + 0.11 * t), 0.0, bar_z - 0.012 - r * math.sin(a) * 0.9))
        iron.sweep(scroll, 0.0085, sides=6)
    objects.append(iron.finish('gas_lamp column', collection, IRON, smooth=True, sharp=40))

    # ------------------------------------------------------------------ the lantern
    zb, zt = 2.862, 3.268          # bottom and top of the glass
    hb, ht = 0.112, 0.172          # half widths of the frame at bottom and top of the glass

    def half(z):
        return hb + (ht - hb) * (z - zb) / (zt - zb)

    frame = shapes.Shape()
    # bottom: four struts from the cup out to the bottom rail (the bottom is glazed, so the lamp lights the ground)
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for (sx, sy) in corners:
        frame.beam((sx * 0.040, sy * 0.040, 2.806), (sx * (hb - 0.004), sy * (hb - 0.004), zb - 0.014), 0.012, 0.012)
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
        frame.beam((ax * hb, ay * hb, zb - 0.004), (bx * hb, by * hb, zb - 0.004), 0.020, 0.026, extend=0.010)
        frame.beam((ax * ht, ay * ht, zt + 0.006), (bx * ht, by * ht, zt + 0.006), 0.020, 0.030, extend=0.010)
        # a thin glazing bar across each face, a third of the way up
        zm = zb + (zt - zb) * 0.36
        hm = half(zm)
        frame.beam((ax * hm, ay * hm, zm), (bx * hm, by * hm, zm), 0.008, 0.010)
    for (sx, sy) in corners:
        frame.beam((sx * hb, sy * hb, zb - 0.020), (sx * ht, sy * ht, zt + 0.022), 0.017, 0.017)
        # small cast knobs at the top corners
        frame.sphere((sx * (ht + 0.010), sy * (ht + 0.010), zt + 0.030), 0.013, segments=10, rings=6)
    # the cornice and the curved roof rising to the vent
    frame.box((0.0, 0.0, zt + 0.034), (2 * ht + 0.060, 2 * ht + 0.060, 0.014))
    roof_steps = [(0.205, zt + 0.041), (0.186, zt + 0.062), (0.150, zt + 0.092), (0.110, zt + 0.120),
                  (0.075, zt + 0.146), (0.056, zt + 0.162)]
    rings = []
    for (h, z) in roof_steps:
        rings.append(frame._verts([(-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z)]))
    frame._rings(rings, True, True, True)
    # roof ribs down each hip
    for (sx, sy) in corners:
        rib = [(sx * h, sy * h, z + 0.006) for (h, z) in roof_steps]
        frame.sweep(rib, 0.0065, sides=6)
    # the vent drum, its cap and the finial
    vent = [(0.000, zt + 0.158), (0.048, zt + 0.158), (0.048, zt + 0.172), (0.042, zt + 0.176),
            (0.042, zt + 0.204), (0.050, zt + 0.208), (0.078, zt + 0.222), (0.074, zt + 0.230),
            (0.040, zt + 0.250), (0.016, zt + 0.262), (0.012, zt + 0.272), (0.000, zt + 0.272)]
    frame.lathe(vent, segments=24)
    frame.sphere((0.0, 0.0, zt + 0.282), 0.015, segments=12, rings=8)
    frame.cylinder((0.0, 0.0, zt + 0.292), (0.0, 0.0, zt + 0.305), 0.006, 0.001, segments=8)
    # the gas pipe down from the roof to the burner
    frame.cylinder((0.0, 0.0, zt + 0.04), (0.0, 0.0, 3.135), 0.0075, segments=10)
    frame.cylinder((0.0, 0.0, 3.150), (0.0, 0.0, 3.128), 0.015, segments=12)
    lantern_obj = frame.finish('gas_lamp lantern frame', collection, IRON, smooth=True, sharp=38)
    objects.append(lantern_obj)

    # the white china hood over the mantles
    hood = shapes.Shape()
    hood.lathe([(0.012, 3.130), (0.024, 3.126), (0.052, 3.108), (0.056, 3.100), (0.050, 3.100), (0.022, 3.116),
                (0.010, 3.122)], segments=24)
    objects.append(hood.finish('gas_lamp mantle hood', collection, CHINA, smooth=True, sharp=50, shadow=not lit))

    # three inverted mantles hanging from the burner
    mantles = shapes.Shape()
    for k in range(3):
        a = math.radians(90 + 120 * k)
        cx, cy = 0.024 * math.cos(a), 0.024 * math.sin(a)
        prof = [(0.000, 3.108), (0.008, 3.106), (0.013, 3.096), (0.015, 3.080), (0.013, 3.064), (0.008, 3.056),
                (0.000, 3.054)]
        mantles.lathe(prof, segments=12, matrix=Matrix.Translation((cx, cy, 0.0)))
        mantles.cylinder((cx * 0.6, cy * 0.6, 3.124), (cx, cy, 3.106), 0.003, segments=6)
    if lit:
        mantle_material = FLAME
    else:
        mantle_material = shapes.part_material('gas_lamp', 'unlit mantle', _unlit_mantle)
    objects.append(mantles.finish('gas_lamp mantles', collection, mantle_material, smooth=True, shadow=not lit))

    # four glass panes, set just inside the frame
    panes = shapes.Shape()
    inset, thick = 0.004, 0.003
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
        nx, ny = (ax + bx) / 2, (ay + by) / 2          # outward direction of this face
        pts = []
        for (z, k) in ((zb + 0.004, 0), (zb + 0.004, 1), (zt - 0.002, 1), (zt - 0.002, 0)):
            h = half(z)
            px = (ax if k == 0 else bx) * (h - 0.002)
            py = (ay if k == 0 else by) * (h - 0.002)
            pts.append(Vector((px - nx * inset, py - ny * inset, z)))
        outer = panes._verts(pts)
        inner = panes._verts([p - Vector((nx, ny, 0.0)) * thick for p in pts])
        panes._rings([outer, inner], True, True, True)
    panes.box((0.0, 0.0, zb - 0.006), (2 * hb - 0.012, 2 * hb - 0.012, 0.003))
    if lit:
        glass = GLOW_GLASS
    else:
        glass = shapes.part_material('gas_lamp', 'cold sooty glass', _cold_glass)
    objects.append(panes.finish('gas_lamp glass panes', collection, glass, shadow=not lit))

    if lit:
        objects.append(shapes.point_light(collection, 'gas_lamp light', (0.0, 0.0, 3.080), LIGHT_POWER,
                                          (1.0, 0.62, 0.28), 0.03))

    # seeded differences: the post leans a little, the lantern sits a touch turned on its cup
    lantern_parts = objects[2:]
    turn = math.radians(rng.uniform(-2.5, 2.5))
    shapes.tilt_all(lantern_parts, rz=turn)
    lean = math.radians(rng.uniform(0.0, 0.7))
    direction = rng.uniform(0.0, 2 * math.pi)
    shapes.tilt_all(objects, rx=lean * math.cos(direction), ry=lean * math.sin(direction))
    lift = Matrix.Translation((0.0, 0.0, 0.205 * math.sin(lean)))    # the low edge of the base stays on the ground
    for obj in objects:
        obj.matrix_world = lift @ obj.matrix_world
    return objects
