"""
What this file does: lays fallen leaves and twigs on a ground the ground tool made, within an area you give. Leaves are
cupped and curled, ochre, rust, brown and a few still green, lying flat on the slope under them; they gather in the dips
and at the water's edge, float flat on standing water, and are trodden dark into the mud of a rut or path. Twigs are
thin, bent and forked, half sunk in the soil. Both are dark and shining when wet. It decides nothing about where they
lie: the area and the amount are yours; the ground's own dips, water and tracks decide only where more or fewer gather
within it.

From your own script, after the tracks (litter rests on the carved ground) and after ground.wet():

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import ground, litter
    litter.scatter(yard)                                              # leaves and twigs everywhere on the ground
    litter.scatter(yard, area=(-2, 0, 2, 12), kinds=('leaves',), amount=2.0, seed=3)     # a drift of leaves in a rectangle

    python3 litter.py --help
    python3 litter.py --blend IN.blend --ground ground --out OUT.blend [--area x0 y0 x1 y1] [--kinds leaves twigs] [--amount 1]

Options:
    area        where litter may lie: None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or
                a function taking an (n, 2) array of points and giving each a weight 0 to 1 (None)
    kinds       'leaves' (4 to 9 cm, about 12 a square metre at amount 1), 'twigs' (8 to 40 cm, about 1 a square metre)
                (both)
    amount      1 is a scattering after an autumn wind; 3 a thick fall (1.0)
    seed        the same seed lays the same litter (0)
    collection  where the litter objects go (a new collection 'litter')

What it makes: one object per kind, 'litter leaves', 'litter twigs': a cloud of points, one per leaf or twig, carrying
its size, turn and shape, its shade ('litter_tone'), how trodden into the mud it is ('litter_mud') and the wetness of
the ground under it ('wetness'); a Geometry Nodes modifier puts a live copy of one of a dozen shapes on each point.
obj['pieces'] is the count. The ground's numbers it reads: 'hollow', 'wetness', 'water', 'bare', 'wear'.
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

SHAPE_COUNT = 12
ORDER = ('leaves', 'twigs')
KINDS = {
    'leaves': {'sizes': (0.04, 0.09), 'density': 12.0, 'material': 'MADE • fallen leaves'},
    'twigs': {'sizes': (0.08, 0.4), 'density': 1.0, 'material': 'MADE • wet bark'},
}

TOOL = {
    'name': 'litter',
    'what': 'lays fallen leaves and twigs within an area you give: leaves gather in the dips and at the water\'s edge, '
            'float on standing water and are trodden into ruts; twigs half sunk; dark and shining when wet',
    'call': "litter.scatter(yard, area=my_verges, kinds=('leaves', 'twigs'), amount=1.0, seed=3)",
    'options': {
        'area': 'None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or a function of an (n, 2) '
                'array of points giving weights 0..1 (None)',
        'kinds': "'leaves' (4 to 9 cm), 'twigs' (8 to 40 cm) (both)",
        'amount': '1 a scattering after a wind, 3 a thick fall (1.0)',
        'seed': 'the same seed lays the same litter (0)',
    },
    'materials': ['MADE • fallen leaves', 'MADE • wet bark'],
    'source': 'made for the store (log 53), after the owner\'s picture of a wet field track with leaves and twigs in the mud',
    'trap': 'a leaf is a few centimetres: from eye height at 10 m it is a speck; lay litter where the camera is near, '
            'and big enough to be named (Traps: a thing nobody can name is noise)',
}


# ----------------------------------------------------------------------------------------------- the shapes

def _leaf_mesh(name, index):
    """One leaf 1 m long, its stalk at the origin and its tip along +X: an outline (oval, long, broad or lobed), cupped
    across and curled up at the tip, with its own numbers for the veins ('leaf_u' along, 'leaf_v' across)."""
    pick = random.Random(9100 + index)
    kind = index % 4
    width = (0.32, 0.18, 0.42, 0.38)[kind] * pick.uniform(0.85, 1.15)
    cup, curl, twist = pick.uniform(0.02, 0.12), pick.uniform(-0.04, 0.16), pick.uniform(-0.25, 0.25)
    rows, cols = 12, 4
    bm = bmesh.new()
    u_layer = bm.verts.layers.float.new('leaf_u')
    v_layer = bm.verts.layers.float.new('leaf_v')
    grid = []
    for row in range(rows + 1):
        u = row / rows
        half = width * math.sin(math.pi * min(max(u, 0.0), 1.0) ** 0.8) ** 0.9
        if kind == 3:                                          # lobed: the edge waves in and out
            half *= 1.0 - 0.28 * max(0.0, math.sin(u * math.pi * 5.0)) * (0.3 + u)
        half = max(half, 0.004)
        line = []
        for col in range(-cols, cols + 1):
            v = col / cols
            y = v * half
            z = cup * v * v + curl * u * u + twist * v * u * 0.3
            vertex = bm.verts.new((u, y, z))
            vertex[u_layer] = u
            vertex[v_layer] = v
            line.append(vertex)
        grid.append(line)
    for row in range(rows):
        for col in range(2 * cols):
            bm.faces.new((grid[row][col], grid[row][col + 1], grid[row + 1][col + 1], grid[row + 1][col]))
    stalk = [bm.verts.new((-0.14, -0.006, 0.01)), bm.verts.new((-0.14, 0.006, 0.01)), grid[0][cols + 1], grid[0][cols - 1]]
    for vertex in stalk[:2]:
        vertex[u_layer] = 0.0
        vertex[v_layer] = 0.0
    bm.faces.new(stalk)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _twig_mesh(name, index):
    """One twig 1 m long along +X, bent, with a fork or two, a thin round stick tapering to its tips."""
    pick = random.Random(9500 + index)
    bm = bmesh.new()

    def stick(start, direction, length, radius, depth):
        points = []
        position = Vector(start)
        heading = Vector(direction).normalized()
        steps = 8
        for step in range(steps + 1):
            points.append((position.copy(), radius * (1.0 - 0.75 * step / steps)))
            heading = (heading + Vector((pick.gauss(0, 0.12), pick.gauss(0, 0.12), pick.gauss(0, 0.04)))).normalized()
            position = position + heading * (length / steps)
        rings = []
        for centre, r in points:
            ring = []
            for k in range(5):
                angle = 2.0 * math.pi * k / 5
                ring.append(bm.verts.new(centre + Vector((0.0, math.cos(angle) * r, math.sin(angle) * r))))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for k in range(5):
                bm.faces.new((a[k], a[(k + 1) % 5], b[(k + 1) % 5], b[k]))
        if depth < 1:
            for _ in range(pick.randint(1, 2)):
                at = pick.randint(2, 6)
                side = Vector((pick.uniform(0.3, 1.0), pick.choice((-1, 1)) * pick.uniform(0.5, 1.2), 0.0))
                stick(points[at][0], side, length * pick.uniform(0.25, 0.5), points[at][1] * 0.6, depth + 1)
    stick((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 1.0, 0.012 * pick.uniform(0.7, 1.4), 0)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return mesh


def _shapes(kind, material, collection):
    name = 'litter shapes • %s • %s' % (kind, material.name)
    shapes = bpy.data.collections.get(name)
    if shapes is None:
        shapes = bpy.data.collections.new(name)
    if shapes.name not in collection.children:
        collection.children.link(shapes)
    shapes.hide_render = True
    shapes.hide_viewport = True
    for index in range(len(shapes.objects), SHAPE_COUNT):
        shape_name = '%s %02d' % (kind[:-1] if kind == 'twigs' else 'leaf', index)
        mesh = _leaf_mesh(shape_name, index) if kind == 'leaves' else _twig_mesh(shape_name, index)
        mesh.materials.append(material)
        shapes.objects.link(bpy.data.objects.new(shape_name, mesh))
    return shapes


def _live_copies(obj, shapes):
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
    for attribute, socket, kind in (('litter_scale', 'Scale', 'FLOAT_VECTOR'), ('litter_rotation', 'Rotation', 'FLOAT_VECTOR'),
                                    ('litter_shape', 'Instance Index', 'INT')):
        named = nodes.new('GeometryNodeInputNamedAttribute')
        named.data_type = kind
        named.inputs['Name'].default_value = attribute
        links.new(named.outputs['Attribute'], instance.inputs[socket])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('live litter', 'NODES')
    modifier.node_group = group
    return modifier


# ----------------------------------------------------------------------------------------------- scattering

def scatter(ground, area=None, kinds=ORDER, amount=1.0, seed=0, collection=None):
    """Lay leaves and twigs on the ground within the area (see the note at the top). Returns {'leaves': obj, 'twigs':
    obj}, only the kinds asked for; each object's obj['pieces'] is its count."""
    kinds = (kinds,) if isinstance(kinds, str) else tuple(kinds)
    unknown = [kind for kind in kinds if kind not in KINDS]
    if unknown:
        raise ValueError('no litter kind %s; the kinds are %s' % (', '.join(repr(u) for u in unknown), ', '.join(ORDER)))
    amount = float(amount)
    if not 0.0 <= amount <= 6.0:
        raise ValueError('amount is 0 to 6 (1 a scattering, 3 a thick fall), not %r' % (amount,))
    bpy.context.view_layer.update()
    surface = stones._Surface(ground)
    weigh, box = stones._area(area)
    mesh = ground.data
    numbers = {name: numpy.clip(numpy.nan_to_num(ground_tool.numbers(mesh, name)), 0.0, None)
               for name in ('hollow', 'wetness', 'water', 'bare', 'wear')}
    xy = surface.points[:, :2]
    near_water = numpy.clip(numbers['wetness'] - 0.6, 0.0, 0.3) / 0.3              # the wet ring round water
    drifts = 0.5 + 0.5 * _noise.wander(xy[:, 0], xy[:, 1], scale=2.5, seed=seed + 3, layers=2)
    target = collection
    if target is None:
        target = bpy.data.collections.new('litter')
        bpy.context.scene.collection.children.link(target)
    made = {}
    for number, kind in enumerate(ORDER):
        if kind not in kinds:
            continue
        spec = KINDS[kind]
        if kind == 'leaves':
            afloat = numbers['water'] > 0.004                  # fewer settle on open water than at its edge
            gather = (0.35 + 1.3 * numpy.clip(numbers['hollow'], 0.0, 1.0) + 0.8 * near_water) * (0.3 + 1.4 * drifts) * numpy.where(afloat, 0.3, 1.0)
        else:
            gather = 0.6 + 0.8 * drifts
        density = spec['density'] * gather
        tri, bary, choices = surface.sample(density, amount, lambda block: numpy.random.default_rng([seed, 91, number, block]), weigh, box)
        count = len(tri)
        positions = surface.at(surface.points, tri, bary)
        normals = surface.at(surface.normals, tri, bary)
        normals /= numpy.maximum(numpy.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
        water = surface.at(numbers['water'], tri, bary) if count else numpy.zeros(0)
        wet = numpy.clip(surface.at(numbers['wetness'], tri, bary), 0.0, 1.0) if count else numpy.zeros(0)
        trodden = numpy.clip(surface.at(numpy.maximum(numbers['bare'], numbers['wear']), tri, bary), 0.0, 1.0) if count else numpy.zeros(0)
        low, high = spec['sizes']
        sizes = low + (high - low) * choices['size'] ** 1.6
        floating = water > 0.004
        if count:                                             # the water's own level: the highest water surface at the corners round it
            surface_level = numpy.where(numbers['water'] > 0.0, surface.points[:, 2] + numbers['water'], -numpy.inf)
            level = surface_level[surface.tris[tri]].max(axis=1)
            floating &= numpy.isfinite(level)
        else:
            level = numpy.zeros(0)
        if kind == 'leaves':
            positions[:, 2] = numpy.where(floating, numpy.where(floating, level, 0.0) + 0.0015, positions[:, 2] + 0.0015 + 0.002 * choices['thick'])
            normals[floating] = (0.0, 0.0, 1.0)                # a floating leaf lies flat on the water
            upright = stones._upright_to(normals)
            tip = numpy.radians(10.0) * choices['tilt']        # a little this way and that
            turn = upright @ stones._turns('z', choices['turn']) @ stones._turns('x', tip[:, 0] * 0.6) @ stones._turns('y', tip[:, 1] * 0.6)
            mud = trodden * (1.0 - floating) * (choices['narrow'] - 0.78) / 0.22 * 0.7      # some trodden in, most only splashed
        else:
            sunk = (0.004 + 0.006 * choices['thick']) * sizes / 0.2
            positions[:, 2] = numpy.where(floating, numpy.where(floating, level, 0.0) - 0.002, positions[:, 2] - 0.3 * sunk)
            upright = stones._upright_to(normals)
            turn = upright @ stones._turns('z', choices['turn']) @ stones._turns('x', numpy.radians(8.0) * choices['tilt'][:, 0])
            mud = trodden * 0.5
        rotation = stones._euler(turn)
        shapes = None
        if kind == 'twigs':                                    # the store's scanned fallen branches, when they are there
            import _scans
            shapes = _scans.shapes([('dry_branches_medium_01', ['dry_branches'])], target, 'litter twigs', size=1.0, along='length',
                                   turn_to_x=True)
        if shapes is None:
            shapes = _shapes(kind, store.material(spec['material']), target)
        columns = {
            'litter_scale': ('FLOAT_VECTOR', numpy.repeat(sizes[:, None], 3, axis=1)),
            'litter_rotation': ('FLOAT_VECTOR', rotation),
            'litter_shape': ('INT', choices['shape'] % len(shapes.objects)),
            'litter_tone': ('FLOAT', (choices['sink'] - 0.65) / 0.7),
            'litter_mud': ('FLOAT', mud),
            'wetness': ('FLOAT', numpy.maximum(wet, floating * 1.0)),
        }
        obj_mesh = bpy.data.meshes.new('litter ' + kind)
        obj_mesh.vertices.add(count)
        if count:
            obj_mesh.vertices.foreach_set('co', numpy.asarray(positions, dtype=numpy.float32).ravel())
        obj_mesh.update()
        for column, (data_kind, values) in columns.items():
            stones._write(obj_mesh, column, data_kind, values)
        obj = bpy.data.objects.new('litter ' + kind, obj_mesh)
        target.objects.link(obj)
        _live_copies(obj, shapes)
        obj['pieces'] = count
        store.mark(obj)
        made[kind] = obj
    return made


# ----------------------------------------------------------------------------------------------- command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Lay fallen leaves and twigs on a ground the ground tool made (see the note at the top of litter.py).')
    parser.add_argument('--blend', help='the .blend file holding the ground')
    parser.add_argument('--ground', default='ground', help="the ground object's name; default 'ground'")
    parser.add_argument('--area', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='a rectangle to lay them in (default: everywhere)')
    parser.add_argument('--kinds', nargs='+', default=list(ORDER), help='leaves, twigs; default both')
    parser.add_argument('--amount', type=float, default=1.0, help='1 a scattering; default 1')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same litter; default 0')
    parser.add_argument('--out', help='save the result here')
    args = parser.parse_args(argv)
    if not args.blend:
        parser.error('give --blend (a file with the ground)')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    if args.ground not in bpy.data.objects:
        parser.error('no object %r in the file; its objects are: %s' % (args.ground, ', '.join(o.name for o in bpy.data.objects)))
    made = scatter(bpy.data.objects[args.ground], area=tuple(args.area) if args.area else None, kinds=args.kinds,
                   amount=args.amount, seed=args.seed)
    print('laid', ', '.join('%s: %d' % (name, obj['pieces']) for name, obj in made.items()))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
