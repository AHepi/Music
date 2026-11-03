"""
bentwood_chair: a bentwood café chair of the classic No. 14 kind, in steam-bent beech under a dark varnish. One long
bent rod makes both back legs and the back hoop; a smaller loop stands inside the hoop; a round seat ring holds a
woven cane seat; two front legs splay out a little; a ring ties all four legs below the seat. The sitter faces -Y.

Options: none.

Where it came from: "44 control builder - render_final.py" (procedural-textures/44 Blind test - a tea house),
chair_curve() and chair_seat_mesh() (lines 709 and 750): bevelled curves facing +Y with a solid seat disc; rebuilt here
facing -Y, with rods that meet the seat ring and leg ring where real ones are screwed, and a cane seat.
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

CARD = {
    'name': 'bentwood_chair',
    'what': 'a bentwood café chair (No. 14 kind): bent hoop back with an inner loop, round cane seat, four splayed legs and a ring; faces -Y',
    'size_m': (0.51, 0.51, 0.90),
    'options': {},
    'materials': ['PART • bentwood_chair: dark varnished beech', 'PART • bentwood_chair: woven cane'],
    'source': '"44 control builder - render_final.py", chair_curve() (line 709) and chair_seat_mesh() (line 750); '
              'builder\'s report "44 Control builder\'s report.md"',
    'views': 'reads from every side',
    'trap': 'dark wood on a dark floor: the chair reads by its outline, so keep something lighter behind it',
}

SEAT_R = 0.205         # to the middle of the seat ring
SEAT_TOP = 0.466
ROD = 0.0135


def _varnished_beech(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    streak = shapes.noise_fac(nodes, links, vec, 40.0, detail=6.0, roughness=0.6, distortion=0.4)
    worn = shapes.noise_fac(nodes, links, vec, 6.0, detail=3.0)
    colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, streak, 0.35, 0.7), (0.020, 0.009, 0.004), (0.042, 0.020, 0.009))
    colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, worn, 0.62, 0.72, 0.0, 0.7), colour, (0.075, 0.042, 0.020))
    links.new(colour, principled.inputs['Base Color'])
    links.new(shapes.map_range(nodes, links, worn, 0.4, 0.8, 0.30, 0.55), principled.inputs['Roughness'])
    principled.inputs['Coat Weight'].default_value = 0.35
    principled.inputs['Coat Roughness'].default_value = 0.18
    links.new(shapes.bump(nodes, links, streak, 0.08, 0.001), principled.inputs['Normal'])
    m.diffuse_color = (0.03, 0.015, 0.007, 1.0)


def _cane(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    weave = nodes.new('ShaderNodeTexVoronoi')
    weave.feature = 'DISTANCE_TO_EDGE'
    weave.inputs['Scale'].default_value = 95.0
    links.new(vec, weave.inputs['Vector'])
    strands = shapes.map_range(nodes, links, weave.outputs['Distance'], 0.02, 0.12)
    dirt = shapes.noise_fac(nodes, links, vec, 9.0, detail=4.0)
    cane = shapes.mix_colour(nodes, links, dirt, (0.120, 0.078, 0.036), (0.070, 0.045, 0.022))
    colour = shapes.mix_colour(nodes, links, strands, (0.012, 0.009, 0.006), cane)
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.5
    links.new(shapes.bump(nodes, links, strands, 0.5, 0.0015), principled.inputs['Normal'])
    m.diffuse_color = (0.09, 0.06, 0.03, 1.0)


def _mirror(points):
    return [(-p[0], p[1], p[2]) for p in points]


def build(collection, seed=0):
    rng = shapes.rng_for('bentwood_chair', seed)
    objects = []
    wood = shapes.part_material('bentwood_chair', 'dark varnished beech', _varnished_beech)
    cane = shapes.part_material('bentwood_chair', 'woven cane', _cane)
    frame = shapes.Shape()

    # ------------------------------------------------------------------ the seat ring and cane
    section = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        x, y = 0.013 * math.cos(a), 0.017 * math.sin(a)
        # a rounded rectangle: push the corners out
        x *= 1.0 + 0.18 * abs(math.sin(2 * a))
        y *= 1.0 + 0.18 * abs(math.sin(2 * a))
        section.append((x, y))
    ring = [(SEAT_R * math.cos(2 * math.pi * k / 64), SEAT_R * math.sin(2 * math.pi * k / 64), SEAT_TOP - 0.017) for k in range(64)]
    frame.sweep(ring, 1.0, closed=True, section=section, up=(0.0, 0.0, 1.0))
    seat = shapes.Shape()
    seat.lathe([(0.0, SEAT_TOP - 0.010), (SEAT_R - 0.006, SEAT_TOP - 0.010), (SEAT_R - 0.004, SEAT_TOP - 0.004),
                (SEAT_R - 0.012, SEAT_TOP - 0.003), (0.0, SEAT_TOP - 0.0045)], segments=48)
    objects.append(seat.finish('bentwood_chair cane seat', collection, cane, smooth=True, sharp=50))

    # ------------------------------------------------------------------ back legs and hoop: one bent rod
    lean = rng.uniform(-0.004, 0.004)
    p0 = Vector((-0.200, 0.255, 0.0))
    p2 = Vector((-0.170, 0.158, SEAT_TOP - 0.018))
    p1 = p0.lerp(p2, 0.25 / p2.z)
    half = [p0, p1, p2, Vector((-0.170, 0.172 + lean, 0.56)), Vector((-0.166, 0.200 + lean, 0.67)),
            Vector((-0.152, 0.228 + lean, 0.77)), Vector((-0.112, 0.246 + lean, 0.845)), Vector((-0.055, 0.254 + lean, 0.880)),
            Vector((0.0, 0.256 + lean, 0.888))]
    hoop = half + [Vector(p) for p in reversed(_mirror(half[:-1]))]
    hoop_path = shapes.smooth_path(hoop, steps=8)
    radii = []
    for p in hoop_path:
        z = p.z
        radii.append(0.0118 + (ROD - 0.0118) * min(1.0, z / 0.45) if z < 0.45 else ROD)
    frame.sweep(hoop_path, ROD, sides=10, radii=radii)

    # the inner loop, from the seat ring up inside the hoop
    q_top = 0.800 + rng.uniform(-0.01, 0.01)
    ring_a = math.radians(29)
    q0 = Vector((-SEAT_R * math.sin(ring_a), SEAT_R * math.cos(ring_a), SEAT_TOP - 0.004))
    inner_half = [q0, Vector((-0.100, 0.170 + lean, 0.56)), Vector((-0.098, 0.196 + lean, 0.66)),
                  Vector((-0.082, 0.218 + lean, q_top - 0.055)), Vector((-0.045, 0.232 + lean, q_top - 0.010)),
                  Vector((0.0, 0.236 + lean, q_top))]
    inner = inner_half + [Vector(p) for p in reversed(_mirror(inner_half[:-1]))]
    frame.sweep(shapes.smooth_path(inner, steps=8), 0.0108, sides=10)

    # ------------------------------------------------------------------ front legs, splayed and tapering
    front = []
    for sx in (-1, 1):
        top = Vector((sx * 0.130, -0.150, SEAT_TOP - 0.012))
        foot = Vector((sx * 0.176, -0.216, 0.0))
        mid = top.lerp(foot, 0.5) + Vector((sx * 0.004, -0.004, 0.0))
        path = shapes.smooth_path([top, mid, foot], steps=8)
        frame.sweep(path, 0.015, sides=10, radii=[0.0155 - 0.0035 * k / (len(path) - 1) for k in range(len(path))])
        front.append(path)

    # ------------------------------------------------------------------ the leg ring, touching all four legs
    ring_z = 0.205 + rng.uniform(-0.012, 0.012)

    def at_height(path, z):
        best = min(range(len(path) - 1), key=lambda i: abs((path[i].z + path[i + 1].z) / 2 - z))
        a, b = path[best], path[best + 1]
        t = 0.0 if abs(b.z - a.z) < 1e-9 else (z - a.z) / (b.z - a.z)
        return a.lerp(b, max(0.0, min(1.0, t)))

    fl = at_height(front[1], ring_z)
    rl = at_height(hoop_path[::-1], ring_z)     # right back leg (the end of the hoop path)
    fx, fy = abs(fl.x), fl.y
    bx, by = abs(rl.x), rl.y
    yc = ((bx * bx + by * by) - (fx * fx + fy * fy)) / (2 * (by - fy))
    reach = math.hypot(fx, fy - yc)
    leg_ring_r = reach - (0.0138 + 0.0095)
    pts = [(leg_ring_r * math.cos(2 * math.pi * k / 56), yc + leg_ring_r * math.sin(2 * math.pi * k / 56), ring_z) for k in range(56)]
    frame.sweep(pts, 0.0095, sides=8, closed=True)

    # screws where the legs meet the rings
    screws = shapes.Shape()
    for path in front:
        p = at_height(path, ring_z)
        d = Vector((p.x, p.y - yc, 0.0)).normalized()
        screws.sphere(p - d * 0.012 + Vector((0, 0, 0.0)), 0.0035, segments=8, rings=4)
    objects.append(frame.finish('bentwood_chair frame', collection, wood, smooth=True, sharp=None))
    objects.append(screws.finish('bentwood_chair screws', collection, 'IRON • soot-black lamp posts', smooth=True))

    shapes.tilt_all(objects, rz=math.radians(rng.uniform(-3, 3)))
    return objects
