"""
corrugated_sheet: a sheet of corrugated iron of about 1900 (3-inch corrugations, 19 mm deep, a little over a millimetre
thick), galvanised once and gone to rust: rust in patches and in runs down the corrugations, worst at the edges and
under the nails, the grey zinc showing where it has held; nailed through the crests along its top and bottom (and across
its middle when long) with domed nail heads on lead washers; a little out of true where it was nailed over uneven
boards. Very rusty sheets are eaten through along the bottom edge. It stands upright with its back on a wall at +Y (the
wall's face is the plane y = 0, the corrugations run up and down), its bottom edge's middle at the origin; or it lies
flat on the ground, its back down, its corrugations running along Y (its top edge towards +Y), its middle at the origin.

Options:
    width    across the corrugations, metres (default 0.76; a 2 ft 6 in sheet)
    height   along the corrugations, metres (default 1.83; a 6 ft sheet)
    rust     how rusty, 0 (galvanised grey, rust only at the nails and edges) to 1 (rusted all over, eaten through along
             the bottom edge) (default 0.7)
    warp     how far out of true: 0 flat, 1 badly buckled (default 0.3; a slight bow between the nail rows, curled corners)
    lying    False (default): upright, its back on a wall at +Y; True: lying flat on the ground, top edge towards +Y
    seed     where the rust lies, the warp's shape, where the corrugations are cut at the edges

Where it came from: '/home/claude/build-54-barn/dress/render_final.py', tin_sheet() (line 1193) and its nail heads
(line 1227): a corrugated grid given thickness by a modifier, a copy of the store's rusty corrugated iron, and nail
heads as small boxes off the sheet; rebuilt here as a solid sheet with real corrugations, nails on the crests with
washers, a rust dial that mixes the photograph's rust with grey zinc, and runs of rust under each nail.
"""

import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils import noise as mnoise

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402

PART = 'corrugated_sheet'
NAILS = 'MADE • rusty nail heads'
PITCH = 0.0762         # 3 inches, crest to crest
DEPTH = 0.019          # crest to trough
THICK = 0.0012

CARD = {
    'name': PART,
    'what': 'a sheet of rusty corrugated iron: real 3-inch corrugations, rust in patches and runs with grey zinc between, nail heads on '
            'lead washers along the crests; upright with its back on a wall at +Y, or lying flat',
    'size_m': (0.76, 0.03, 1.83),
    'options': {
        'width': 'across the corrugations, metres (default 0.76; a 2 ft 6 in sheet)',
        'height': 'along the corrugations, metres (default 1.83; a 6 ft sheet)',
        'rust': 'how rusty, 0 grey zinc with rust only at the nails and edges, to 1 rusted all over and eaten through along the bottom edge (default 0.7)',
        'warp': 'how far out of true, 0 flat to 1 badly buckled (default 0.3; a slight bow between the nail rows, curled corners)',
        'lying': 'False (default): upright, its back on a wall at +Y, corrugations up and down; True: lying flat on the ground, corrugations along Y',
        'seed': 'where the rust lies, the shape of the warp, where the corrugations are cut at the edges (default 0)',
    },
    'materials': ['SURFACE • rusty_corrugated_iron (corrugated_sheet), mixed with grey zinc by the rust dial', NAILS,
                  'PART • corrugated_sheet: lead washers'],
    'source': "'/home/claude/build-54-barn/dress/render_final.py', tin_sheet() (line 1193) and its nail heads (line 1227)",
    'views': 'reads from every side; upright, its back is flat for the wall at +Y',
    'trap': 'upright, its origin is the middle of its bottom edge on the wall face (y = 0): to nail it over a wall, put the origin on the wall '
            'face at the height of the bottom edge; lying, its origin is its middle on the ground',
}


def sheet_material():
    """The store's rusty corrugated iron, mixed with dull grey zinc where the sheet has not rusted: the point number 'rust'
    (the dial) pushes rust over all of it; patches, runs down the corrugations, the edges ('edge') and the nails ('nail')
    rust first."""
    material = shapes.surface_copy('rusty_corrugated_iron', PART, Grime=0.45, Wet=0.2)
    if material.get('pp_zinc'):
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    weather = nodes['Weather']
    principled = nodes.get('Principled BSDF')

    def attribute(name):
        node = nodes.new('ShaderNodeAttribute')
        node.attribute_name = name
        return node.outputs['Fac']

    def madd(a, b, c):
        node = nodes.new('ShaderNodeMath')
        node.operation = 'MULTIPLY_ADD'
        for socket, value in zip(node.inputs, (a, b, c)):
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, socket)
            else:
                socket.default_value = value
        return node.outputs[0]

    vec = shapes.own_coordinates(nodes)
    blot = shapes.noise_fac(nodes, links, vec, 3.5, detail=6.0, roughness=0.6)
    fine = shapes.noise_fac(nodes, links, vec, 26.0, detail=4.0)
    down = nodes.new('ShaderNodeMapping')
    down.inputs['Scale'].default_value = (16.0, 16.0, 1.4)
    links.new(vec, down.inputs['Vector'])
    streak = shapes.noise_fac(nodes, links, down.outputs['Vector'], 1.0, detail=3.0)
    level = madd(streak, 0.4, blot)
    level = madd(fine, 0.2, level)
    level = madd(attribute('nail'), 0.6, level)
    level = madd(attribute('edge'), 0.4, level)
    level = shapes.math_node(nodes, links, 'ADD', attribute('rust'), level)
    rusty = shapes.map_range(nodes, links, level, 1.35, 1.5)
    zinc = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fine, 0.35, 0.65), (0.07, 0.075, 0.08), (0.12, 0.125, 0.13))
    bloom = shapes.noise_fac(nodes, links, vec, 9.0, detail=3.0)
    zinc = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, bloom, 0.55, 0.75, 0.0, 0.55), zinc, (0.17, 0.17, 0.16))
    colour = shapes.mix_colour(nodes, links, rusty, zinc, weather.outputs['Base Color'])
    links.new(colour, principled.inputs['Base Color'])
    links.new(shapes.mix_float(nodes, links, rusty, shapes.map_range(nodes, links, fine, 0.3, 0.7, 0.38, 0.6), weather.outputs['Roughness']),
              principled.inputs['Roughness'])
    links.new(shapes.mix_float(nodes, links, rusty, 0.6, 0.0), principled.inputs['Metallic'])
    material['pp_zinc'] = True
    return material


def washer_material():
    def maker(m, nodes, links, principled):
        principled.inputs['Base Color'].default_value = (0.06, 0.062, 0.065, 1.0)
        principled.inputs['Roughness'].default_value = 0.7
        m.diffuse_color = (0.06, 0.062, 0.065, 1.0)
    return shapes.part_material(PART, 'lead washers', maker)


def build(collection, seed=0, width=0.76, height=1.83, rust=0.7, warp=0.3, lying=False):
    width = barn.number('corrugated_sheet width', width, 0.12, 4.0)
    height = barn.number('corrugated_sheet height', height, 0.12, 4.0)
    rust = barn.clamp(barn.number('corrugated_sheet rust', rust, 0.0, 2.0), 0.0, 1.0)
    warp = barn.number('corrugated_sheet warp', warp, 0.0, 3.0)
    if not isinstance(lying, bool):
        raise ValueError('corrugated_sheet lying is True or False, not %r' % (lying,))
    rng = shapes.rng_for(PART, seed)
    half = width / 2.0
    phase = rng.uniform(0.0, PITCH)
    seed_at = Vector((rng.uniform(0, 80), rng.uniform(0, 80), rng.uniform(0, 80)))
    bow = rng.uniform(0.6, 1.0)
    curl = [rng.uniform(0.3, 1.0) for _ in range(4)]

    def back_y(x, z):
        """The sheet's back face at (x, z): troughs on the wall (y = 0), crests DEPTH out, lifted off by the warp."""
        corr = -DEPTH * (1.0 - math.cos(2 * math.pi * (x - phase) / PITCH)) / 2.0
        zn, xn = z / height, (x + half) / width
        lift = 0.028 * math.sin(math.pi * zn) * bow * (0.7 + 0.3 * mnoise.noise(Vector((x * 1.5, z * 1.5, 0.0)) + seed_at))
        corner = (curl[0] * (1 - xn) * (1 - zn) + curl[1] * xn * (1 - zn) + curl[2] * (1 - xn) * zn + curl[3] * xn * zn)
        lift += 0.02 * corner * max(abs(2 * xn - 1), abs(2 * zn - 1)) ** 3
        lift += 0.004 * (0.5 + 0.5 * mnoise.noise(Vector((x * 6.0, z * 6.0, 1.0)) + seed_at))
        return corr - warp * lift

    # nails along the crests: top and bottom rows (and the middle on a long sheet), every second crest
    rows = [0.05, height - 0.05] + ([height / 2.0] if height > 1.4 else [])
    crests = []
    k = math.floor((-half - phase) / PITCH) - 1
    while True:
        x = phase + PITCH / 2.0 + k * PITCH
        k += 1
        if x > half - 0.02:
            break
        if x > -half + 0.02:
            crests.append(x)
    nails = [(x, z) for z in rows for x in crests[::2]] if height > 0.2 else [(x, height / 2) for x in crests[::2]]

    # ------------------------------------------------------------------ the sheet: a corrugated surface given its thickness
    sheet = shapes.Shape()
    barn.number_layers(sheet, points=('rust', 'nail', 'edge'))
    cols = max(8, int(width / (PITCH / 14.0)))
    nrows = max(3, int(height / 0.05))
    grid = []
    for i in range(cols + 1):
        x = -half + width * i / cols
        column = []
        for j in range(nrows + 1):
            z = height * j / nrows
            column.append(sheet.bm.verts.new((x, back_y(x, z), z)))
        grid.append(column)
    faces = []
    eat = (rust - 0.82) * 2.4 if rust > 0.82 else -1.0     # rusted through along the bottom edge
    for i in range(cols):
        for j in range(nrows):
            x = -half + width * (i + 0.5) / cols
            z = height * (j + 0.5) / nrows
            if eat > 0 and z < 0.16:
                holes = 0.5 + 0.5 * mnoise.noise(Vector((x * 14.0, z * 14.0, 3.0)) + seed_at) + (0.16 - z) / 0.16 * 0.7
                if holes > 1.55 - eat:
                    continue
            faces.append(sheet._face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]))
    loose = [v for v in sheet.bm.verts if not v.link_faces]
    for v in loose:
        sheet.bm.verts.remove(v)
    rust_layer = sheet.bm.verts.layers.float['rust']
    nail_layer = sheet.bm.verts.layers.float['nail']
    edge_layer = sheet.bm.verts.layers.float['edge']
    for v in sheet.bm.verts:
        x, z = v.co.x, v.co.z
        run = 0.0
        for (nx, nz) in nails:
            dx = (x - nx) / 0.014
            dz = nz - z                                 # below the nail: positive
            if abs(dx) < 3.0 and -0.03 < dz < 0.6:
                fall = math.exp(-dz / 0.2) if dz >= 0 else math.exp(dz / 0.012)
                run = max(run, math.exp(-dx * dx) * fall)
        v[rust_layer] = rust
        v[nail_layer] = run
        v[edge_layer] = max(math.exp(-z / 0.12), math.exp(-(height - z) / 0.06) * 0.6, math.exp(-(half - abs(x)) / 0.03) * 0.7)
    bmesh.ops.solidify(sheet.bm, geom=sheet.bm.faces[:], thickness=THICK)
    # solidify may push the back past the wall: the whole sheet stays in front of y = 0
    over = max(v.co.y for v in sheet.bm.verts)
    if over > 0.0:
        for v in sheet.bm.verts:
            v.co.y -= over
    objects = [sheet.finish('corrugated_sheet', collection, sheet_material(), smooth=True, sharp=None, normals=True)]

    # ------------------------------------------------------------------ nail heads on lead washers
    heads = shapes.Shape()
    washers = shapes.Shape()
    for (x, z) in nails:
        y = min(v for v in (back_y(x - 0.003, z), back_y(x, z), back_y(x + 0.003, z))) - THICK - over
        washers.cylinder((x, y + 0.0004, z), (x, y - 0.0018, z), 0.0105, segments=12)
        heads.sphere((x, y - 0.0018, z), 0.0068, segments=10, rings=5, squash=(1.0, 0.5, 1.0))
    objects.append(washers.finish('corrugated_sheet washers', collection, washer_material(), smooth=True, sharp=50))
    objects.append(heads.finish('corrugated_sheet nail heads', collection, NAILS, smooth=True, sharp=None))

    if lying:
        flat = Matrix.Translation((0.0, -height / 2.0, 0.0)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
        for o in objects:
            o.matrix_world = flat @ o.matrix_world
        low = min((o.matrix_world @ v.co).z for o in objects for v in o.data.vertices)
        for o in objects:
            o.matrix_world = Matrix.Translation((0.0, 0.0, -low)) @ o.matrix_world
    return objects
