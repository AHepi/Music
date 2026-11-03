"""
rails: a straight piece of narrow-gauge mine track (two-foot gauge, 600 mm between the rail heads): two flat-bottomed
rails spiked to timber sleepers, the sleepers bedded in a heap of ballast. The rails' tops are bright where wheels
have run on them; their sides are rust. The track runs along Y; pieces join end to end along Y (the sleepers keep
their spacing across the join). The store's ore_car stands with its wheels on these rails when both are placed at the
same point.

Options:
    length   metres of track along Y (default 4.8); the sleepers are spaced about 0.6 m apart. From 3.6 m up the
             rails have a joint in the middle, with fishplates bolted across it.

Where it came from: "46 desert-mine - render_final.py" (procedural-textures/46 Pictures-only builders - three places),
rails_and_ties() (line 1030): boxes for ties and bars for rails along the scene's curving track; rebuilt here straight,
at real size, with rail sections, spikes, fishplates and ballast.
"""

import math
import os
import sys

import bpy
import mathutils
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_town as shapes  # noqa: E402

RUST = 'RUST • rain-aged iron'

CARD = {
    'name': 'rails',
    'what': 'a straight piece of two-foot mine track: rails spiked to timber sleepers in ballast; runs along Y',
    'size_m': (1.90, 4.80, 0.18),
    'options': {
        'length': 'metres of track along Y (default 4.8); sleepers about 0.6 m apart; a fishplated joint in the middle from 3.6 m',
    },
    'materials': ['SURFACE • rough_wood (rails)', 'PART • rails: ballast (gravel_road photograph, greyed)', RUST,
                  'PART • rails: wheel-polished steel'],
    'source': '"46 desert-mine - render_final.py", rails_and_ties() (line 1030); builder\'s report "46 Desert mine builder\'s report.md"',
    'views': 'reads from every side; the ends are cut square through the ballast so pieces can be laid end to end',
    'trap': 'rail tops are 0.18 m above the part\'s foot: the ore car is built to stand there; other wheeled things are not',
}

SPACING = 0.6
BALLAST_HALF = 0.95       # the ballast's shoulders run out to here either side
SLEEPER_LENGTH = 1.12
RAIL_SECTION = [           # (across, up) from the middle of the rail's foot, anticlockwise seen from the -Y end
    (-0.035, 0.000), (0.035, 0.000), (0.035, 0.004), (0.010, 0.010), (0.0055, 0.016), (0.0055, 0.050),
    (0.020, 0.056), (0.022, 0.060), (0.022, 0.075), (0.019, 0.0793), (0.014, 0.080), (-0.014, 0.080),
    (-0.019, 0.0793), (-0.022, 0.075), (-0.022, 0.060), (-0.020, 0.056), (-0.0055, 0.050), (-0.0055, 0.016),
    (-0.010, 0.010), (-0.035, 0.004),
]
TOP_EDGES = (9, 10, 11)    # the faces of the section that wheels run on


def _polished_steel(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    streak = shapes.noise_fac(nodes, links, vec, 30.0, detail=3.0)
    links.new(shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, streak, 0.3, 0.7), (0.20, 0.20, 0.21), (0.11, 0.10, 0.10)),
              principled.inputs['Base Color'])
    principled.inputs['Metallic'].default_value = 1.0
    links.new(shapes.map_range(nodes, links, streak, 0.2, 0.8, 0.18, 0.38), principled.inputs['Roughness'])
    m.diffuse_color = (0.18, 0.18, 0.19, 1.0)


def ballast_material():
    """The store's gravel road photograph, greyed and darkened into crushed stone: a copy of 'SURFACE • gravel_road'
    with a hue and saturation step put in front of its Weather dials (so it is named as this part's own material)."""
    name = 'PART • rails: ballast (gravel_road photograph, greyed)'
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    m = shapes.material('SURFACE • gravel_road').copy()
    m.name = name
    nodes, links = m.node_tree.nodes, m.node_tree.links
    weather = nodes['Weather']
    source = next(l for l in links if l.to_node == weather and l.to_socket.name == 'Color').from_socket
    grey = nodes.new('ShaderNodeHueSaturation')
    grey.inputs['Saturation'].default_value = 0.38
    grey.inputs['Value'].default_value = 0.8
    links.new(source, grey.inputs['Color'])
    links.new(grey.outputs['Color'], weather.inputs['Color'])
    weather.inputs['Grime'].default_value = 0.5
    weather.inputs['Darken'].default_value = 0.42
    nodes['Picture size'].inputs['Scale'].default_value = 1.6
    m.diffuse_color = (0.07, 0.06, 0.05, 1.0)
    return m


def ballast_height(x, y, seed_offset):
    """The top of the ballast at (x, y): level between the sleeper ends, sloping out to the ground, lumpy."""
    ax = abs(x)
    if ax < 0.62:
        base = 0.074
    else:
        t = min(1.0, (ax - 0.62) / (BALLAST_HALF - 0.62))
        base = 0.074 * (1.0 - t) ** 1.3 - 0.012 * t
    lump = mathutils.noise.noise(Vector((x * 9.0, y * 9.0, seed_offset))) * 0.010 + \
        mathutils.noise.noise(Vector((x * 23.0, y * 23.0, seed_offset + 7.3))) * 0.005
    return base + lump


def build(collection, seed=0, length=4.8):
    rng = shapes.rng_for('rails', seed)
    length = max(0.6, float(length))
    half = length / 2
    objects = []
    seed_offset = rng.uniform(0, 100)

    # ------------------------------------------------------------------ sleepers (each its own timber, grain along it)
    wood = shapes.surface_copy('rough_wood', 'rails', Grime=0.55, Darken=0.5, **{'Mud height': 0.05})
    count = max(1, int(round(length / SPACING)))
    spacing = length / count
    sleeper_ys = []
    for k in range(count):
        y = -half + spacing * (k + 0.5) + rng.uniform(-0.03, 0.03)
        sleeper_ys.append(y)
        turn = math.radians(rng.uniform(-2.5, 2.5))
        dx = rng.uniform(-0.03, 0.03)
        long_ = SLEEPER_LENGTH + rng.uniform(-0.05, 0.04)
        wide = rng.uniform(0.145, 0.17)
        a = Vector((-long_ / 2, 0.0, 0.0))
        b = Vector((long_ / 2, 0.0, 0.0))
        r = Matrix.Rotation(turn, 3, 'Z')
        a = r @ a + Vector((dx, y, shapes.SLEEPER_TOP / 2))
        b = r @ b + Vector((dx, y, shapes.SLEEPER_TOP / 2))
        objects.append(shapes.timber(collection, 'rails sleeper %d' % (k + 1), a, b, wide, shapes.SLEEPER_TOP,
                                     wood, rng=rng, chamfer=0.01, roll=0.0))

    # ------------------------------------------------------------------ rails: flat-bottomed sections along Y
    steel = shapes.part_material('rails', 'wheel-polished steel', _polished_steel)
    rails = shapes.Shape()
    joint = length >= 3.6
    pieces = [(-half, -0.003), (0.003, half)] if joint else [(-half, half)]
    rot = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).to_4x4()      # section across X and up Z, run along Y
    for side in (-1, 1):
        x0 = side * shapes.RAIL_CENTRE
        for (y0, y1) in pieces:
            m = Matrix.Translation((x0, 0.0, shapes.SLEEPER_TOP)) @ rot
            bottom, top, sides = rails.prism(RAIL_SECTION, -y1, -y0, m)
            for index in TOP_EDGES:
                if sides[index] is not None:
                    sides[index].material_index = 1
    objects.append(rails.finish('rails rails', collection, [RUST, steel], smooth=False))

    # ------------------------------------------------------------------ spikes, and fishplates at the joint
    iron = shapes.Shape()
    foot_half = 0.035
    for y in sleeper_ys:
        for side in (-1, 1):
            xc = side * shapes.RAIL_CENTRE
            for edge in (-1, 1):
                ys = y + edge * rng.uniform(0.012, 0.03)
                xe = xc + edge * foot_half
                # the head hooks over the edge of the rail's foot; the shank goes down into the sleeper
                iron.box((xe + edge * 0.004, ys, shapes.SLEEPER_TOP + 0.0085), (0.020, 0.016, 0.009))
                iron.box((xe + edge * 0.008, ys, shapes.SLEEPER_TOP + 0.002), (0.012, 0.012, 0.012))
    if joint:
        for side in (-1, 1):
            xc = side * shapes.RAIL_CENTRE
            for face in (-1, 1):
                xp = xc + face * 0.0125
                iron.box((xp, 0.0, shapes.SLEEPER_TOP + 0.034), (0.013, 0.42, 0.036))
                for yb in (-0.15, -0.05, 0.05, 0.15):
                    if face > 0:
                        iron.box((xp + face * 0.012, yb, shapes.SLEEPER_TOP + 0.034), (0.012, 0.024, 0.024))   # nut
                    else:
                        iron.cylinder((xp + face * 0.006, yb, shapes.SLEEPER_TOP + 0.034),
                                      (xp + face * 0.016, yb, shapes.SLEEPER_TOP + 0.034), 0.012, segments=10)
                    iron.cylinder((xc - 0.03, yb, shapes.SLEEPER_TOP + 0.034), (xc + 0.03, yb, shapes.SLEEPER_TOP + 0.034),
                                  0.0055, segments=6)
    objects.append(iron.finish('rails spikes and fishplates', collection, RUST, smooth=False))

    # ------------------------------------------------------------------ ballast: a heaped bed, cut square at both ends
    gravel = ballast_material()
    bed = shapes.Shape()
    step = 0.05
    nx = int(round(2 * BALLAST_HALF / step))
    ny = max(2, int(round(length / step)))
    grid = []
    for i in range(nx + 1):
        x = -BALLAST_HALF + 2 * BALLAST_HALF * i / nx
        column = []
        for j in range(ny + 1):
            y = -half + length * j / ny
            z = ballast_height(x, y, seed_offset)
            if i in (0, nx):
                z = -0.012
            column.append(bed.bm.verts.new((x, y, z)))
        grid.append(column)
    for i in range(nx):
        for j in range(ny):
            bed._face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
    # the cut ends: a wall from the ballast's edge down to the ground at each end
    for j, facing in ((0, -1), (ny, 1)):
        y = -half + length * j / ny
        top = [grid[i][j] for i in range(nx + 1)]
        low = [bed.bm.verts.new((v.co.x, y, -0.012)) for v in top]
        for i in range(nx):
            quad = [top[i], top[i + 1], low[i + 1], low[i]]
            bed._face(quad if facing > 0 else list(reversed(quad)))
    # loose stones lying on the bed and on the shoulders
    for k in range(int(46 * length)):
        x = rng.uniform(-BALLAST_HALF + 0.05, BALLAST_HALF - 0.05)
        y = rng.uniform(-half + 0.04, half - 0.04)
        if abs(abs(x) - shapes.RAIL_CENTRE) < 0.05:
            continue
        r = rng.uniform(0.012, 0.028) if k % 4 else rng.uniform(0.028, 0.05)
        z = ballast_height(x, y, seed_offset)
        bed.rock((x, y, z + r * 0.15), r, rng, squash=(1.0, 0.85, 0.6))
    objects.append(bed.finish('rails ballast', collection, gravel, smooth=False, normals=False))
    return objects
