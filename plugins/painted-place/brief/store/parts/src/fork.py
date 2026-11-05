"""
fork: a farm hand fork of about 1900, of two kinds. A pitch fork: a long straight ash shaft, an iron socket strapped
and riveted to it, and long round tines that spring from a forged crotch and curve a little forward, for pitching hay
and sheaves. A root fork: a shorter shaft with a D handle (two wooden cheeks and a grip, an iron ring where the shaft
splits) and short broad flat tines on a cross bar, for lifting and loading mangolds and swedes. The shaft is greyed,
polished paler where hands hold it; the iron rusted. Leaning, it stands against a wall at +Y as people leave them: a
pitch fork on the end of its shaft with its tines up, a root fork on its tines with its handle up; lying, it lies flat on
the ground along X, its tines towards +X.

Options:
    kind     'pitch' (default): long shaft, long round tines; 'root': D handle, short broad flat tines
    pose     'leaning' (default): leaning back on a wall at +Y, its foot at the origin; 'lying': flat on the ground along X
    tines    how many tines (default 0, which gives the kind its own: 3 on a pitch fork, 4 on a root fork); a pitch fork
             of 2 tines is the sheaf fork, of 4 or 5 the muck fork
    seed     the lean, the tines' small bends, the shaft's wear

Where it came from: the pitchfork in '/home/claude/build-54-barn/first pass/render_final.py' (lines 842-855): a
cylinder shaft and three tines of straight cylinders with a cross bar; and the root fork with a D handle in
'/home/claude/build-54-barn/dress/render_final.py' (lines 1096-1112): cylinders for the shaft, cheeks, bar and tines.
Rebuilt here with turned shafts, a strapped socket, curved tapering tines (round on the pitch fork, flat on the root
fork), a bent D handle, and a shaft rubbed pale where it is held.
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

PART = 'fork'
RUST = 'RUST • rain-aged iron'
NAILS = 'MADE • rusty nail heads'
KINDS = ('pitch', 'root')
POSES = ('leaning', 'lying')

CARD = {
    'name': PART,
    'what': 'a farm fork: a pitch fork (long ash shaft, long round tines) or a root fork (D handle, short broad flat tines), iron socket '
            'strapped on, shaft rubbed pale where held; leaning back on a wall at +Y, or lying flat',
    'size_m': (0.18, 0.43, 1.61),
    'options': {
        'kind': "'pitch' (default): a long shaft and long round tines, leaning on the end of its shaft with its tines up; 'root': a D handle "
                "and short broad flat tines, leaning on its tines with its handle up",
        'pose': "'leaning' (default): leaning back on a wall at +Y, its foot at the origin; 'lying': flat on the ground along X, tines towards +X",
        'tines': 'how many tines (default 0; 0 gives the kind its own: 3 on a pitch fork, 4 on a root fork); 2 makes the sheaf fork, 4 or 5 the muck fork',
        'seed': "the lean, the tines' small bends, the shaft's wear (default 0)",
    },
    'materials': ['PART • fork: ash shaft, rubbed pale where held', RUST, NAILS],
    'source': "the pitchfork in '/home/claude/build-54-barn/first pass/render_final.py' (lines 842-855); the root fork with a D handle in "
              "'/home/claude/build-54-barn/dress/render_final.py' (lines 1096-1112)",
    'views': 'reads from every side; leaning, it needs the wall at +Y (drawn alone it leans on air); its tines spread along X',
    'trap': "leaning, it slopes back about 16 degrees: the pitch fork's tines rest on the wall about 0.4 m behind (+Y) its foot, the root "
            "fork's handle about 0.35 m behind; its shaft is 3 cm thick, so from far off only its outline against something lighter shows",
}

PITCH_SHAFT = 1.32
ROOT_SHAFT = 0.70


def shaft_material():
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        held = nodes.new('ShaderNodeAttribute')
        held.attribute_name = 'held'
        stretch = nodes.new('ShaderNodeMapping')
        stretch.inputs['Scale'].default_value = (40.0, 40.0, 1.6)
        links.new(vec, stretch.inputs['Vector'])
        grain = shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 1.0, detail=5.0)
        grey = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.35, 0.65), (0.055, 0.048, 0.038), (0.12, 0.1, 0.075))
        dirt = shapes.noise_fac(nodes, links, vec, 8.0, detail=3.0)
        grey = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, dirt, 0.5, 0.75, 0.0, 0.6), grey, (0.04, 0.032, 0.022))
        pale = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.35, 0.65), (0.16, 0.125, 0.085), (0.24, 0.19, 0.13))
        colour = shapes.mix_colour(nodes, links, held.outputs['Fac'], grey, pale)
        links.new(colour, principled.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, held.outputs['Fac'], 0.0, 1.0, 0.72, 0.38), principled.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, grain, 0.2, 0.002), principled.inputs['Normal'])
        m.diffuse_color = (0.1, 0.085, 0.06, 1.0)
    return shapes.part_material(PART, 'ash shaft, rubbed pale where held', maker)


def _bumps(z, centres):
    """How much a point along the shaft is held: 1 in the middle of a hand's place, fading over 12 cm."""
    return max([0.0] + [max(0.0, 1.0 - abs(z - c) / w) for (c, w) in centres])


def _round_tine(shape, root, spread, length, forward, rng, radius=0.0058):
    """A round tine from the crotch: out sideways to `spread`, then up, curving forward (-Y), tapering to a point."""
    pts, radii = [], []
    steps = 14
    jig = Vector((rng.uniform(-0.004, 0.004), rng.uniform(-0.004, 0.004), 0.0))
    for i in range(steps + 1):
        t = i / steps
        side = spread * (1.0 - (1.0 - min(1.0, t / 0.28)) ** 2) if spread else 0.0      # out to the side over the first quarter
        p = root + Vector((side, -forward * t * t, length * t)) + jig * t * t
        pts.append(p)
        radii.append(radius * (1.0 - 0.78 * t ** 1.4))
    shape.sweep(pts, radius, sides=7, radii=radii)


def _flat_tine(shape, root, length, forward, rng):
    """A flat broad tine (root fork): a strip up from the bar, broad across (X), tapering and curving forward, its end rounded."""
    steps = 10
    rings = []
    jig = rng.uniform(-0.003, 0.003)
    for i in range(steps + 1):
        t = i / steps
        w = 0.02 * (1.0 - 0.42 * t)
        th = 0.0072 * (1.0 - 0.4 * t)
        if t > 0.92:
            w *= 0.55 + 0.45 * (1.0 - t) / 0.08
        c = root + Vector((jig * t * t, -forward * t * t, length * t))
        rings.append(shape._verts([c + Vector((-w / 2, -th / 2, 0)), c + Vector((w / 2, -th / 2, 0)), c + Vector((w / 2, th / 2, 0)),
                                   c + Vector((-w / 2, th / 2, 0))]))
    shape._rings(rings, True, True, True)


def build(collection, seed=0, kind='pitch', pose='leaning', tines=0):
    if kind not in KINDS:
        raise ValueError("fork kind is 'pitch' or 'root', not %r" % (kind,))
    if pose not in POSES:
        raise ValueError("fork pose is 'leaning' or 'lying', not %r" % (pose,))
    tines = int(round(barn.number('fork tines', tines, 0, 8)))
    if tines == 0:
        tines = 3 if kind == 'pitch' else 4
    tines = max(2, tines)
    rng = shapes.rng_for(PART, seed)
    objects = []
    wood = shaft_material()
    shaft = shapes.Shape()
    barn.number_layers(shaft, points=('held',))
    iron = shapes.Shape()
    rivets = shapes.Shape()
    # built standing up in its own frame: handle end at z = 0, working end up; tines spread along X, curving towards -Y

    if kind == 'pitch':
        top = PITCH_SHAFT
        shaft.lathe([(0.0, 0.0), (0.0115, 0.0), (0.0142, 0.007), (0.015, 0.04), (0.0152, top * 0.5), (0.0158, top - 0.1), (0.0162, top), (0.0, top)],
                    segments=12)
        held = [(0.22, 0.14), (0.78, 0.18)]
        # the socket: a cone up from the shaft into the crotch, two straps riveted down the shaft
        iron.lathe([(0.0, top - 0.135), (0.0172, top - 0.135), (0.0178, top - 0.05), (0.0145, top + 0.02), (0.0105, top + 0.05), (0.0, top + 0.06)],
                   segments=12)
        for sy in (-1, 1):
            iron.box((0.0, sy * 0.0175, top - 0.2), (0.013, 0.003, 0.15))
            for z in (top - 0.25, top - 0.17):
                rivets.sphere((0.0, sy * 0.0195, z), 0.0042, segments=8, rings=4, squash=(1.0, 0.6, 1.0))
        crotch = Vector((0.0, 0.0, top + 0.045))
        length = 0.3 + rng.uniform(-0.01, 0.01)
        width = 0.1 if tines == 2 else min(0.28, 0.085 * (tines - 1))
        for k in range(tines):
            x = -width / 2 + width * k / (tines - 1)
            _round_tine(iron, crotch, x, length, 0.035 + rng.uniform(-0.006, 0.006), rng)
        foot_kind = 'shaft'
    else:
        grip_z, split_z = 0.022, 0.16
        top = split_z + ROOT_SHAFT
        # the D handle: a round grip between two bent cheeks, the cheeks meeting the shaft at an iron ring
        shaft.cylinder((-0.058, 0.0, grip_z), (0.058, 0.0, grip_z), 0.0148, segments=10)
        for sx in (-1, 1):
            path = [Vector((sx * 0.062, 0.0, grip_z - 0.006)), Vector((sx * 0.066, 0.0, 0.06)), Vector((sx * 0.05, 0.0, 0.11)),
                    Vector((sx * 0.018, 0.0, 0.15)), Vector((sx * 0.004, 0.0, split_z + 0.02))]
            section = [(0.0075 * math.cos(a), 0.0105 * math.sin(a)) for a in (2 * math.pi * k / 8 for k in range(8))]
            shaft.sweep(shapes.smooth_path(path, steps=5), 0.01, section=section, up=Vector((0.0, 1.0, 0.0)))
        shaft.lathe([(0.0, split_z), (0.0155, split_z), (0.016, split_z + 0.3), (0.0165, top), (0.0, top)], segments=12)
        held = [(0.06, 0.12), (0.62, 0.16)]
        iron.lathe([(0.0, split_z - 0.012), (0.0185, split_z - 0.012), (0.0192, split_z + 0.03), (0.0172, split_z + 0.04), (0.0, split_z + 0.04)],
                   segments=12)
        iron.lathe([(0.0, top - 0.12), (0.0175, top - 0.12), (0.018, top - 0.04), (0.014, top + 0.01), (0.0, top + 0.012)], segments=12)
        for sy in (-1, 1):
            iron.box((0.0, sy * 0.017, top - 0.17), (0.013, 0.003, 0.13))
            for z in (top - 0.21, top - 0.14):
                rivets.sphere((0.0, sy * 0.019, z), 0.0042, segments=8, rings=4, squash=(1.0, 0.6, 1.0))
        bar_z = top + 0.022
        span = 0.2 if tines <= 4 else 0.2 + 0.04 * (tines - 4)
        iron.box((0.0, 0.0, bar_z), (span, 0.012, 0.024))
        iron.box((0.0, 0.0, top + 0.006), (0.04, 0.014, 0.02))
        length = 0.27 + rng.uniform(-0.01, 0.01)
        inner = span - 0.024
        for k in range(tines):
            x = -inner / 2 + inner * k / (tines - 1)
            _flat_tine(iron, Vector((x, 0.0, bar_z + 0.006)), length, 0.03 + rng.uniform(-0.005, 0.005), rng)
        foot_kind = 'tines'
    barn.point_numbers(shaft, shaft.bm.verts, held=lambda v: _bumps(v.co.z, held))
    objects.append(shaft.finish('fork shaft', collection, wood, smooth=True, sharp=50))
    objects.append(iron.finish('fork head', collection, RUST, smooth=True, sharp=40))
    objects.append(rivets.finish('fork rivets', collection, NAILS, smooth=True, sharp=None))

    # ------------------------------------------------------------------ pose it
    if pose == 'leaning':
        if foot_kind == 'tines':
            # stand it on its tines, handle up: turned over end to end, the tines' tips on the ground at the origin
            tips = max(v.co.z for o in objects for v in o.data.vertices)
            shapes.tilt_all(objects, ry=math.pi, pivot=(0.0, 0.0, 0.0))
            for o in objects:
                o.matrix_world = Matrix.Translation((0.0, 0.0, tips)) @ o.matrix_world
        lean = math.radians(16.0 + rng.uniform(-1.5, 1.5))
        shapes.tilt_all(objects, rx=-lean, rz=math.radians(rng.uniform(-8, 8)), pivot=(0.0, 0.0, 0.0))
    else:
        turn = Matrix.Rotation(math.pi / 2, 4, 'Y') @ Matrix.Rotation(-math.pi / 2, 4, 'Z')
        for o in objects:
            o.matrix_world = turn @ o.matrix_world
    # its lowest point on the ground; lying, its middle on the origin
    points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    low = min(p.z for p in points)
    shift = Vector((0.0, 0.0, -low))
    if pose == 'lying':
        shift.x = -(min(p.x for p in points) + max(p.x for p in points)) / 2
        shift.y = -(min(p.y for p in points) + max(p.y for p in points)) / 2
    for o in objects:
        o.matrix_world = Matrix.Translation(shift) @ o.matrix_world
    return objects
