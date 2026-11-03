"""
marble_table: a café table of about 1900: a round top of warm grey veined marble with a rounded, moulded edge (one
small chip knocked out of it), on a cast-iron base: three scrolled legs ending in curls on small pads, a turned column
with collars, and a three-armed bracket with a centre plate under the marble.

Options: none.

Where it came from: "44 control builder - render_final.py" (procedural-textures/44 Blind test - a tea house),
make_table_mesh() (line 689) and mat_marble() (line 323): one lathed shape for the base and top; rebuilt here with a
tripod base, bracket and a moulded marble top, the marble a warm grey.
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

CARD = {
    'name': 'marble_table',
    'what': 'a round café table: warm grey marble top with a moulded edge on a cast-iron tripod base',
    'size_m': (0.62, 0.62, 0.74),
    'options': {},
    'materials': [IRON, 'PART • marble_table: warm grey marble'],
    'source': '"44 control builder - render_final.py", make_table_mesh() (line 689), mat_marble() (line 323); '
              'builder\'s report "44 Control builder\'s report.md"',
    'views': 'reads from every side',
    'trap': '',
}

TOP_Z = 0.740
TOP_R = 0.310


def _marble(m, nodes, links, principled):
    coords = shapes.own_coordinates(nodes)
    info = nodes.new('ShaderNodeObjectInfo')
    shift = nodes.new('ShaderNodeVectorMath')
    shift.operation = 'MULTIPLY_ADD'
    links.new(info.outputs['Random'], shift.inputs[1])
    shift.inputs[0].default_value = (13.0, 7.0, 5.0)
    links.new(coords, shift.inputs[2])
    vec = shift.outputs['Vector']
    cloud = shapes.noise_fac(nodes, links, vec, 3.0, detail=5.0, roughness=0.6)
    base = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, cloud, 0.35, 0.7), (0.150, 0.138, 0.120), (0.112, 0.103, 0.092))
    for scale, width, colour in ((2.2, 0.012, (0.050, 0.044, 0.037)), (5.5, 0.008, (0.085, 0.077, 0.066))):
        n = nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = 9.0
        n.inputs['Roughness'].default_value = 0.6
        n.inputs['Distortion'].default_value = 1.6
        links.new(vec, n.inputs['Vector'])
        line = shapes.math_node(nodes, links, 'ABSOLUTE', shapes.math_node(nodes, links, 'SUBTRACT', n.outputs['Fac'], 0.5))
        vein = shapes.map_range(nodes, links, line, 0.0, width, 0.7, 0.0)
        base = shapes.mix_colour(nodes, links, vein, base, colour)
    stain = shapes.noise_fac(nodes, links, vec, 7.0, detail=4.0)
    base = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, stain, 0.64, 0.75, 0.0, 0.35), base, (0.120, 0.090, 0.060))
    links.new(base, principled.inputs['Base Color'])
    links.new(shapes.map_range(nodes, links, stain, 0.3, 0.8, 0.10, 0.28), principled.inputs['Roughness'])
    principled.inputs['Specular IOR Level'].default_value = 0.55
    links.new(shapes.bump(nodes, links, cloud, 0.03, 0.001), principled.inputs['Normal'])
    m.diffuse_color = (0.14, 0.13, 0.115, 1.0)


def build(collection, seed=0):
    rng = shapes.rng_for('marble_table', seed)
    objects = []

    # ------------------------------------------------------------------ the marble top, its edge moulded, one chip out of it
    top = shapes.Shape()
    edge = [(0.0, TOP_Z - 0.026), (TOP_R - 0.016, TOP_Z - 0.026), (TOP_R - 0.006, TOP_Z - 0.022), (TOP_R - 0.001, TOP_Z - 0.015),
            (TOP_R, TOP_Z - 0.009), (TOP_R - 0.002, TOP_Z - 0.004), (TOP_R - 0.007, TOP_Z - 0.0008), (TOP_R - 0.014, TOP_Z),
            (TOP_R * 0.66, TOP_Z), (TOP_R * 0.33, TOP_Z), (0.0, TOP_Z)]
    top.lathe(edge, segments=96)
    chip_a = rng.uniform(0, 2 * math.pi)
    chip_w = rng.uniform(0.06, 0.10)
    for v in top.bm.verts:
        r = math.hypot(v.co.x, v.co.y)
        if r < TOP_R - 0.03:
            continue
        a = math.atan2(v.co.y, v.co.x)
        d = (a - chip_a + math.pi) % (2 * math.pi) - math.pi
        if abs(d) < chip_w:
            w = (1.0 - (d / chip_w) ** 2)
            depth = 0.012 * w * min(1.0, (r - (TOP_R - 0.03)) / 0.02)
            k = (r - depth) / r
            v.co.x *= k
            v.co.y *= k
            if v.co.z > TOP_Z - 0.006:
                v.co.z -= 0.004 * w
    marble = shapes.part_material('marble_table', 'warm grey marble', _marble)
    objects.append(top.finish('marble_table top', collection, marble, smooth=True, sharp=30))

    # ------------------------------------------------------------------ the cast-iron base
    iron = shapes.Shape()
    column = [(0.000, 0.090), (0.040, 0.090), (0.056, 0.100), (0.058, 0.122), (0.046, 0.134), (0.050, 0.146), (0.036, 0.160),
              (0.030, 0.200), (0.026, 0.260), (0.024, 0.560), (0.030, 0.600), (0.026, 0.612), (0.038, 0.628), (0.046, 0.650),
              (0.040, 0.668), (0.044, 0.680), (0.034, 0.690), (0.000, 0.690)]
    iron.lathe(column, segments=32)
    iron.torus((0.0, 0.0, 0.300), 0.0255, 0.006, segments=24, sides=6)
    iron.torus((0.0, 0.0, 0.420), 0.0245, 0.005, segments=24, sides=6)
    turn = rng.uniform(0, 2 * math.pi / 3)
    leg_section = [(-0.012, -0.020), (0.012, -0.020), (0.014, 0.0), (0.010, 0.020), (-0.010, 0.020), (-0.014, 0.0)]
    for k in range(3):
        a = turn + 2 * math.pi * k / 3
        c, s = math.cos(a), math.sin(a)

        def P(r, z):
            return (r * c, r * s, z)
        # a scrolled leg: out of the bottom collar, sweeping down to the floor, curling up at the end on a pad
        control = [P(0.030, 0.150), P(0.075, 0.150), P(0.140, 0.118), P(0.200, 0.070), P(0.245, 0.030), P(0.262, 0.018),
                   P(0.280, 0.030), P(0.283, 0.052), P(0.270, 0.060), P(0.258, 0.050)]
        path = shapes.smooth_path(control, steps=6)
        n = len(path)
        scale = [1.0 - 0.55 * (i / (n - 1)) for i in range(n)]
        # build ring by ring so the section can narrow along the leg
        rings = []
        tangents = []
        for i in range(n):
            if i == 0:
                t = path[1] - path[0]
            elif i == n - 1:
                t = path[-1] - path[-2]
            else:
                t = path[i + 1] - path[i - 1]
            tangents.append(t.normalized())
        side = Vector((-s, c, 0.0))
        for i in range(n):
            t = tangents[i]
            up = t.cross(side).normalized()
            right = up.cross(t).normalized()
            pts = [path[i] + right * (x * scale[i]) + up * (y * scale[i]) for (x, y) in leg_section]
            rings.append(iron._verts(pts))
        iron._rings(rings, True, True, True)
        # the pad the curl stands on
        iron.lathe([(0.0, 0.0), (0.020, 0.0), (0.022, 0.006), (0.014, 0.012), (0.0, 0.013)], segments=12,
                   matrix=Matrix.Translation(P(0.262, 0.0)))
        # the bracket arm under the top, and its pad
        arm = shapes.smooth_path([P(0.030, 0.668), P(0.090, 0.684), P(0.160, 0.698), P(0.215, 0.704)], steps=5)
        iron.sweep(arm, 0.010, sides=8, radii=[0.011 - 0.004 * (i / (len(arm) - 1)) for i in range(len(arm))])
        iron.cylinder(P(0.215, 0.700), P(0.215, TOP_Z - 0.026), 0.016, segments=10)
    iron.cylinder((0.0, 0.0, 0.690), (0.0, 0.0, TOP_Z - 0.026), 0.075, 0.070, segments=32)
    objects.append(iron.finish('marble_table base', collection, IRON, smooth=True, sharp=40))
    return objects
