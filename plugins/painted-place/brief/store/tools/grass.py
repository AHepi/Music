"""
What this file does: grows grass on a ground the ground tool made, within an area you give: a short turf of small
tufts, bigger tussocks, tall dry weeds with seed heads, and low herbs (nettles, dandelions). Turf, tussocks and herbs
are the store's scanned plants (real meadow grass, nettles and dandelions photographed and measured, from Poly Haven)
when they are in the store, otherwise grass made in code (look='made' asks for that). It reads the ground as it is: no grass where the tracks tool
carved a groove, heaved fresh mud or trod a path (the ground's 'bare' and 'wear' numbers), none under standing water;
a little thinner at the torn edge of a rut or a path, and leaning out over it; lusher and greener in the damp dips,
sparser and straw-coloured on the dry crowns and when the whole place is dry. Wet grass is darker, with a sheen. It decides nothing
about where a verge, a field or the strip between two ruts is: the area and the amount are yours; the ground's own
marks decide only where grass cannot grow and how it looks where it does.

From your own script, after the tracks are carved (grass keeps out of them) and before or after stones:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import ground, tracks, grass
    grass.grow(yard)                                                  # everywhere on the ground that grass can grow
    grass.grow(yard, area=(-6, 0, -1.5, 20), layers=('turf', 'tussocks'), amount=1.3, seed=4)    # in a rectangle
    grass.grow(yard, area=my_verges, layers=('weeds',), seed=5)       # my_verges: (n, 2) points -> 0..1

    python3 grass.py --help
    python3 grass.py --blend IN.blend --ground ground --out OUT.blend [--area x0 y0 x1 y1] [--layers turf tussocks] [--amount 1]

Options:
    area        where grass may grow: None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or
                a function taking an (n, 2) array of points and giving each a weight 0 to 1 (None)
    layers      any of 'turf' (clumps 8 to 20 cm, a close carpet), 'tussocks' (clumps 18 to 45 cm), 'weeds' (tall stalks
                40 to 100 cm with dry seed heads, in clumps), 'herbs' (nettles and dandelions 8 to 25 cm, scanned only)
                (all four)
    look        'scanned' (the store's scanned plants, when they are there) or 'made' (grass made in code) ('scanned')
    amount      1 is a full meadow; 0.5 thin; 2 thick (1.0)
    seed        the same seed grows the same grass (0)
    collection  where the grass objects go (a new collection 'grass')
    material    the blades' material ('MADE • grass')

What it makes: one object per layer, 'grass turf', 'grass tussocks', 'grass weeds': a cloud of points, one per tuft,
carrying its size, turn and lean, its shape, its shade ('grass_tone'), how dry it is ('grass_dry') and the wetness of
the ground under it ('wetness'); a Geometry Nodes modifier puts a live copy of one of a dozen tuft shapes on each point.
obj['tufts'] is the count. The ground's numbers it reads: 'bare', 'wear', 'water', 'wetness', 'hollow' (a ground
without them is all growable, level and dry).
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
import numpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import ground as ground_tool  # noqa: E402
import stones  # noqa: E402
import _noise  # noqa: E402

MATERIAL = 'MADE • grass'
SHAPE_COUNT = 12
ORDER = ('turf', 'tussocks', 'weeds', 'herbs')
# each layer: heights in metres (low, high), tufts per square metre at amount 1, root spread and blade width as shares
# of the height, blades per tuft, how far the blades lean out (degrees), how much it thins at a track's torn edge
LAYERS = {
    'turf': {'heights': (0.05, 0.14), 'density': 60.0, 'spread': 2.4, 'width': 0.045, 'blades': (80, 120), 'lean': (6.0, 45.0),
             'edge': 0.35, 'clumped': 0.0},
    'tussocks': {'heights': (0.15, 0.4), 'density': 6.0, 'spread': 0.5, 'width': 0.03, 'blades': (40, 64), 'lean': (5.0, 55.0),
                 'edge': 0.8, 'clumped': 0.3},
    'weeds': {'heights': (0.4, 1.0), 'density': 0.5, 'spread': 0.18, 'width': 0.025, 'blades': (4, 7), 'lean': (2.0, 20.0),
              'edge': 0.9, 'clumped': 0.75},
    'herbs': {'heights': (0.08, 0.25), 'density': 1.6, 'spread': 0.5, 'width': 0.03, 'blades': (0, 0), 'lean': (0.0, 0.0),
              'edge': 0.5, 'clumped': 0.6},
}
# the store's scanned plants (store/scans, from Poly Haven), used when they are there: real clumps of meadow grass, and
# nettles and dandelions for the herbs; heights and densities for them (their clumps are wider than the made tufts)
SCANNED = {
    'turf': {'sources': [('grass_medium_01', ['small', 'mid', 'tiny_a', 'tiny_e', 'tiny_f']), ('grass_medium_02', ['_a', '_b'])],
             'heights': (0.08, 0.2), 'density': 90.0},
    'tussocks': {'sources': [('grass_medium_01', ['large', 'tall']), ('grass_medium_02', ['_c', '_d', '_e'])],
                 'heights': (0.18, 0.45), 'density': 5.0},
    'herbs': {'sources': [('nettle_plant', ['nettle']), ('dandelion_01', ['dandelion'])], 'heights': (0.08, 0.25), 'density': 1.6},
}

TOOL = {
    'name': 'grass',
    'what': 'grows grass within an area you give: a close turf, tussocks and tall dry weeds; none in carved ruts, on fresh '
            'mud, trodden paths or under water, short and leaning at their torn edges, straw-coloured where dry, dark and '
            'shining where wet',
    'call': "grass.grow(yard, area=my_verges, layers=('turf', 'tussocks', 'weeds'), amount=1.0, seed=2)",
    'options': {
        'area': 'None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or a function of an (n, 2) '
                'array of points giving weights 0..1 (None)',
        'layers': "'turf' (8 to 20 cm, a carpet), 'tussocks' (18 to 45 cm), 'weeds' (40 to 100 cm, seed heads), 'herbs' (nettles, dandelions) (all four)",
        'look': "'scanned' (real plants from Poly Haven, when the store has them) or 'made' ('scanned')",
        'amount': '1 a full meadow, 0.5 thin, 2 thick (1.0)',
        'seed': 'the same seed grows the same grass (0)',
        'material': "the blades' material ('MADE • grass')",
    },
    'materials': [MATERIAL],
    'source': 'made for the store (log 53), after the owner\'s picture of a wet field track with grass verges and a grassy strip between the ruts',
    'trap': 'carve the tracks first: grass grown before them stands in the ruts; a whole field of turf is many thousand '
            'tufts, so give big grounds an area',
}


# ----------------------------------------------------------------------------------------------- the tuft shapes

def _mark_vert(vertex, layers, height, tone, head):
    vertex[layers[0]] = height
    vertex[layers[1]] = tone
    vertex[layers[2]] = head


def _blade(bm, root, heading, lean, length, width, droop, twist, rows, tone, layers):
    """One blade: a tapering strip from the root, leaning out along `heading` and bending over at the tip."""
    out = Vector((math.cos(heading), math.sin(heading), 0.0))
    side = Vector((-out.y, out.x, 0.0))
    verts = []
    for row in range(rows + 1):
        t = row / rows
        rise = math.cos(lean) * t - droop * t * t * 0.6
        reach = math.sin(lean) * t + droop * t * t
        centre = root + (out * reach + Vector((0.0, 0.0, rise))) * length
        half = 0.5 * width * (1.0 - t) ** 0.7 + 0.0005
        turn = twist * t
        across = side * math.cos(turn) + Vector((0.0, 0.0, 1.0)) * math.sin(turn) * 0.3
        for sign in (-1.0, 1.0):
            vertex = bm.verts.new(centre + across * half * sign)
            _mark_vert(vertex, layers, t, tone, 0.0)
            verts.append(vertex)
    for row in range(rows):
        a, b, c, d = verts[2 * row], verts[2 * row + 1], verts[2 * row + 3], verts[2 * row + 2]
        bm.faces.new((a, b, c, d))


def _seed_head(bm, top, size, pick, layers):
    """A dry seed head: a loose cluster of small husks round the top of a stalk."""
    for _ in range(pick.randint(10, 18)):
        offset = Vector((pick.gauss(0, size * 0.5), pick.gauss(0, size * 0.5), pick.uniform(-size * 0.8, size * 0.5)))
        made = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=size * pick.uniform(0.07, 0.13))
        squash = pick.uniform(1.6, 2.6)
        tone = pick.random()
        for vertex in made['verts']:
            vertex.co.z *= squash
            vertex.co += top + offset
            _mark_vert(vertex, layers, 1.0, tone, 1.0)


def _tuft_mesh(name, layer, index):
    """One tuft 1 m tall: blades from a spread of roots, leaning out and bending over (weeds: stalks with seed heads and
    a few leaves at their foot). The same layer and index give the same tuft whatever the seed of the growing."""
    spec = LAYERS[layer]
    pick = random.Random(7300 + 31 * index + 1000 * ORDER.index(layer))
    bm = bmesh.new()
    attrs = tuple(bm.verts.layers.float.new(name) for name in ('blade_height', 'blade_random', 'blade_head'))
    count = pick.randint(*spec['blades'])
    for _ in range(count):
        radius = spec['spread'] * 0.5 * math.sqrt(pick.random())
        angle = pick.uniform(0.0, 2.0 * math.pi)
        root = Vector((radius * math.cos(angle), radius * math.sin(angle), 0.0))
        outer = radius / max(spec['spread'] * 0.5, 1e-6)
        lean = math.radians(pick.uniform(*spec['lean']) * (0.4 + 0.6 * outer))
        heading = angle + pick.gauss(0.0, 0.5)
        if layer == 'weeds':
            length = pick.uniform(0.7, 1.0)
            _blade(bm, root, heading, lean * 0.4, length, spec['width'] * 0.35, pick.uniform(0.0, 0.08), 0.0, 6, pick.random(), attrs)
            top = root + Vector((math.cos(heading) * math.sin(lean * 0.4) * length, math.sin(heading) * math.sin(lean * 0.4) * length,
                                 math.cos(lean * 0.4) * length))
            _seed_head(bm, top, pick.uniform(0.04, 0.07), pick, attrs)
            for _leaf in range(pick.randint(2, 4)):            # leaves at the foot
                _blade(bm, root, pick.uniform(0, 2 * math.pi), math.radians(pick.uniform(30, 70)), pick.uniform(0.15, 0.3),
                       spec['width'] * 1.6, pick.uniform(0.1, 0.4), pick.uniform(-0.8, 0.8), 3, pick.random(), attrs)
        else:
            length = pick.uniform(0.55, 1.0)
            droop = pick.uniform(0.0, 0.35) * (0.5 + outer)
            _blade(bm, root, heading, lean, length, spec['width'] * pick.uniform(0.7, 1.3), droop, pick.uniform(-1.2, 1.2),
                   4, pick.random(), attrs)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _shapes(layer, material, collection):
    """The hidden collection of a dozen tuft shapes for one layer and material (made once, then shared)."""
    name = 'grass shapes • %s • %s' % (layer, material.name)
    shapes = bpy.data.collections.get(name)
    if shapes is None:
        shapes = bpy.data.collections.new(name)
    if shapes.name not in collection.children:
        collection.children.link(shapes)
    shapes.hide_render = True
    shapes.hide_viewport = True
    for index in range(len(shapes.objects), SHAPE_COUNT):
        shape_name = '%s tuft %02d' % (layer, index)
        mesh = _tuft_mesh(shape_name, layer, index)
        mesh.materials.append(material)
        shapes.objects.link(bpy.data.objects.new(shape_name, mesh))
    return shapes


def _live_copies(obj, shapes):
    """Geometry Nodes put a live copy of the tuft each point names on the point, sized, turned and leant by it."""
    group = bpy.data.node_groups.new(obj.name + ' • live copies', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    info = nodes.new('GeometryNodeCollectionInfo')
    info.inputs['Collection'].default_value = shapes
    info.inputs['Separate Children'].default_value = True
    info.inputs['Reset Children'].default_value = True
    instance.inputs['Pick Instance'].default_value = True
    links.new(group_in.outputs['Geometry'], instance.inputs['Points'])
    links.new(info.outputs['Instances'], instance.inputs['Instance'])
    for attribute, socket, kind in (('grass_scale', 'Scale', 'FLOAT_VECTOR'), ('grass_rotation', 'Rotation', 'FLOAT_VECTOR'),
                                    ('grass_shape', 'Instance Index', 'INT')):
        named = nodes.new('GeometryNodeInputNamedAttribute')
        named.data_type = kind
        named.inputs['Name'].default_value = attribute
        links.new(named.outputs['Attribute'], instance.inputs[socket])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('live grass', 'NODES')
    modifier.node_group = group
    return modifier


# ----------------------------------------------------------------------------------------------- reading the ground

def _field(xy, values, cell=0.05, sigma=0.15):
    """The values (given on the ground's points) smoothed over `sigma` metres, as a function of places seen from above
    that gives (value, slope along x, slope along y)."""
    from scipy import ndimage
    low = xy.min(axis=0) - cell
    shape = (numpy.ceil((xy.max(axis=0) - low) / cell).astype(int) + 2)[::-1]
    column = numpy.clip(((xy[:, 0] - low[0]) / cell).astype(int), 0, shape[1] - 1)
    row = numpy.clip(((xy[:, 1] - low[1]) / cell).astype(int), 0, shape[0] - 1)
    flat = row * shape[1] + column
    sums = numpy.bincount(flat, weights=values, minlength=shape[0] * shape[1]).reshape(shape)
    counts = numpy.bincount(flat, minlength=shape[0] * shape[1]).reshape(shape).astype(float)
    filled = ndimage.gaussian_filter(sums, sigma / cell) / numpy.maximum(ndimage.gaussian_filter(counts, sigma / cell), 1e-9)
    slope_y, slope_x = numpy.gradient(filled, cell)

    def read(places):
        coordinates = numpy.vstack([(places[:, 1] - low[1]) / cell - 0.5, (places[:, 0] - low[0]) / cell - 0.5])
        return tuple(ndimage.map_coordinates(grid, coordinates, order=1, mode='nearest') for grid in (filled, slope_x, slope_y))
    return read


# ----------------------------------------------------------------------------------------------- growing

def grow(ground, area=None, layers=ORDER, amount=1.0, seed=0, collection=None, material=MATERIAL, look='scanned'):
    """Grow grass on the ground within the area (see the note at the top). Returns {'turf': obj, 'tussocks': obj,
    'weeds': obj, 'herbs': obj}, only the layers asked for and the store can grow; each object's obj['tufts'] is its
    count and obj['look'] whether its tufts are 'scanned' plants or 'made' ones."""
    if look not in ('scanned', 'made'):
        raise ValueError("look is 'scanned' (the store's scanned plants, when they are there) or 'made', not %r" % (look,))
    import _scans
    layers = (layers,) if isinstance(layers, str) else tuple(layers)
    unknown = [layer for layer in layers if layer not in LAYERS]
    if unknown:
        raise ValueError('no grass layer %s; the layers are %s' % (', '.join(repr(u) for u in unknown), ', '.join(ORDER)))
    amount = float(amount)
    if not 0.0 <= amount <= 5.0:
        raise ValueError('amount is 0 to 5 (1 a full meadow), not %r' % (amount,))
    bpy.context.view_layer.update()
    surface = stones._Surface(ground)
    weigh, box = stones._area(area)
    mesh = ground.data
    xy = surface.points[:, :2]
    numbers = {name: numpy.clip(numpy.nan_to_num(ground_tool.numbers(mesh, name)), 0.0, None)
               for name in ('bare', 'wear', 'water', 'wetness', 'hollow')}
    dial = float(ground.get('wetness_dial', 0.5))
    standing = (numbers['water'] > 0.0) | (numbers['wetness'] >= ground_tool.FLOODED)
    growable = numpy.clip(1.0 - numbers['bare'], 0.0, 1.0) * (1.0 - 0.9 * numpy.clip(numbers['wear'], 0.0, 1.0)) * (~standing)
    edge = _field(xy, 1.0 - growable, cell=0.04, sigma=0.12)           # how near a rut, a path or water each place is
    near_edge = numpy.clip(edge(xy)[0], 0.0, 1.0)
    patches = 0.5 + 0.5 * _noise.wander(xy[:, 0], xy[:, 1], scale=1.6, seed=seed + 5, layers=2)
    target = collection
    if target is None:
        target = bpy.data.collections.new('grass')
        bpy.context.scene.collection.children.link(target)
    blade_material = store.material(material) if isinstance(material, str) else material
    made = {}
    for number, layer in enumerate(ORDER):
        if layer not in layers:
            continue
        spec = dict(LAYERS[layer])
        shapes = None
        if look == 'scanned' and layer in SCANNED:
            shapes = _scans.shapes(SCANNED[layer]['sources'], target, 'grass ' + layer, size=1.0)
            if shapes is not None:
                spec.update(heights=SCANNED[layer]['heights'], density=SCANNED[layer]['density'])
        if shapes is None and layer == 'herbs':                   # herbs are scanned plants only
            print('note: no scanned plants in the store for the herbs; none grown')
            continue
        clumps = 0.5 + 0.5 * _noise.wander(xy[:, 0], xy[:, 1], scale=0.9, seed=seed + 41 + number, layers=2)
        clumped = (1.0 - spec['clumped']) + spec['clumped'] * 2.2 * _smoothstep(0.45, 0.75, clumps)
        density = spec['density'] * growable * (0.4 + 0.6 * patches) * clumped * (1.0 - spec['edge'] * near_edge)
        tri, bary, choices = surface.sample(density, amount, lambda block: numpy.random.default_rng([seed, 77, number, block]), weigh, box)
        count = len(tri)
        positions = surface.at(surface.points, tri, bary)
        places = positions[:, :2]
        here_edge, slope_x, slope_y = edge(places) if count else (numpy.zeros(0),) * 3
        here_edge = numpy.clip(here_edge, 0.0, 1.0)
        hollow = surface.at(numbers['hollow'], tri, bary) if count else numpy.zeros(0)
        wet = numpy.clip(surface.at(numbers['wetness'], tri, bary), 0.0, 1.0) if count else numpy.zeros(0)
        low, high = spec['heights']
        heights = (low + (high - low) * choices['size'] ** 1.3) * (1.0 - 0.25 * here_edge) * (0.85 + 0.35 * numpy.clip(hollow, 0.0, 1.0))
        heights = heights * (0.8 + 0.4 * choices['thick'])
        # lean over towards the bare ground next to it (a rut's torn edge), otherwise a little this way and that
        towards = numpy.column_stack([slope_x, slope_y]) if count else numpy.zeros((0, 2))
        strength = numpy.linalg.norm(towards, axis=1) if count else numpy.zeros(0)
        towards = towards / numpy.maximum(strength, 1e-9)[:, None]
        lean = numpy.radians(35.0) * numpy.clip(strength * 0.25, 0.0, 1.0) + numpy.radians(4.0) * numpy.abs(choices['tilt'][:, 0])
        rotation = numpy.column_stack([-lean * towards[:, 1], lean * towards[:, 0], choices['turn']])
        # dry: on the crowns and when the place is dry, straw-coloured; in the damp dips, green
        dry = numpy.clip(0.12 + 0.55 * (1.0 - dial) + 0.3 * (1.0 - numpy.clip(hollow, 0.0, 1.0)) - 0.3 * wet + 0.25 * (choices['narrow'] - 0.89) / 0.11, 0.0, 1.0)
        if layer == 'weeds':
            dry = numpy.clip(dry + 0.45, 0.0, 1.0)
        positions = positions.copy()
        positions[:, 2] -= 0.004 + 0.02 * heights * 0.1           # roots a little into the soil: no gap under a tuft
        scales = numpy.repeat(heights[:, None], 3, axis=1)
        columns = {
            'grass_scale': ('FLOAT_VECTOR', scales),
            'grass_rotation': ('FLOAT_VECTOR', rotation),
            'grass_shape': ('INT', choices['shape'] % (len(shapes.objects) if shapes is not None else SHAPE_COUNT)),
            'grass_tone': ('FLOAT', (choices['sink'] - 0.65) / 0.7),
            'grass_dry': ('FLOAT', dry),
            'wetness': ('FLOAT', wet),
        }
        scanned = shapes is not None
        if shapes is None:
            shapes = _shapes(layer, blade_material, target)
        obj_mesh = bpy.data.meshes.new('grass ' + layer)
        obj_mesh.vertices.add(count)
        if count:
            obj_mesh.vertices.foreach_set('co', numpy.asarray(positions, dtype=numpy.float32).ravel())
        obj_mesh.update()
        for column, (kind, values) in columns.items():
            stones._write(obj_mesh, column, kind, values)
        obj = bpy.data.objects.new('grass ' + layer, obj_mesh)
        target.objects.link(obj)
        _live_copies(obj, shapes)
        obj['tufts'] = count
        obj['look'] = 'scanned' if scanned else 'made'
        store.mark(obj)
        made[layer] = obj
    return made


def _smoothstep(low, high, value):
    t = numpy.clip((numpy.asarray(value, dtype=numpy.float64) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ----------------------------------------------------------------------------------------------- command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Grow grass on a ground the ground tool made (see the note at the top of grass.py).')
    parser.add_argument('--blend', help='the .blend file holding the ground')
    parser.add_argument('--ground', default='ground', help="the ground object's name; default 'ground'")
    parser.add_argument('--area', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='a rectangle to grow in (default: everywhere)')
    parser.add_argument('--layers', nargs='+', default=list(ORDER), help='turf, tussocks, weeds; default all three')
    parser.add_argument('--amount', type=float, default=1.0, help='1 a full meadow; default 1')
    parser.add_argument('--seed', type=int, default=0, help='the same seed grows the same grass; default 0')
    parser.add_argument('--out', help='save the result here')
    args = parser.parse_args(argv)
    if not args.blend:
        parser.error('give --blend (a file with the ground)')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    if args.ground not in bpy.data.objects:
        parser.error('no object %r in the file; its objects are: %s' % (args.ground, ', '.join(o.name for o in bpy.data.objects)))
    made = grow(bpy.data.objects[args.ground], area=tuple(args.area) if args.area else None, layers=args.layers,
                amount=args.amount, seed=args.seed)
    print('grew', ', '.join('%s: %d tufts' % (name, obj['tufts']) for name, obj in made.items()))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
