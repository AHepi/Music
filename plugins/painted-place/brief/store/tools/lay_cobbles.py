"""
What this file does: lays hand-cut stone setts (cobbles) on a flat road object you name, and worn flagstones on a flat
pavement object you name. The stones are the street bundle's ("Rain on the Old Curve"): eighteen chipped eight-sided
sett shapes (eight worn flag shapes), each stone its own small turn, size and height, so nothing repeats. Setts are
laid in courses across the road, a slight crown in the middle, a few true missing setts; the road itself becomes the
dark damp bed 7 cm below them, seen in the joints. Flags are laid in strips along the pavement. Nothing here decides
where the road or pavement is: the stones go only on the object you pass, inside its outline.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import bpy
    import lay_cobbles
    setts = lay_cobbles.lay_setts(my_road, seed=3)              # returns the object 'setts' (one point per stone)
    flags = lay_cobbles.lay_flags(my_pavement, seed=3)          # returns the object 'flags'
    print(len(setts.data.vertices), 'setts')
    import store
    store.fit_stone_pictures(bpy.context.scene)                 # once, when the place is built, before drawing

From the command line:

    python3 lay_cobbles.py --help
    python3 lay_cobbles.py --blend IN.blend --object Road --out OUT.blend [--seed 3]
    python3 lay_cobbles.py --blend IN.blend --object Pavement --flags --out OUT.blend

Options (lay_setts):
    seed            which stones go where (same seed, same road); default 0
    collection      the collection the stones go in; default a new collection 'lay_cobbles'
    sett_material   the stones' material; default 'COBBLES • wet basalt / broken amber-blue reflections'
    bed_material    the road becomes this, the bed seen in the joints; default 'ROAD BED • damp grit' (None: leave it)
    lower_road      how far the road (the bed) is lowered under the stones, metres; default 0.07 (0: leave it)
    crown           how much lower the edges of the road are than its middle, metres; default 0.025
    missing         the share of setts left out (true missing setts); default 0.007
    along           which way the road runs in its own axes: 'x', 'y' or 'auto' (its longer side); default 'auto'
    keep_inside     stones at the road's edge are cut to fit inside it; default True (False: the bundle's ragged edge)

Options (lay_flags): seed, collection, along, keep_inside as above, and
    flag_material   default 'PAVEMENT • damp sandstone slabs'
    strip_width     about how wide each strip of flags is, metres; default 0.7

The road and pavement must be level (flat on top). Stones are laid at the height of the object's top, found by
casting rays down onto it, so a road of any outline works (stones whose middle is off the road are left out).
The stones are live copies (Geometry Nodes) of the shapes kept in a hidden collection 'lay_cobbles shapes';
the point count of 'setts' or 'flags' is the number of stones.
"""

import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import store  # noqa: E402

SETT_MATERIAL = 'COBBLES • wet basalt / broken amber-blue reflections'
BED_MATERIAL = 'ROAD BED • damp grit'
FLAG_MATERIAL = 'PAVEMENT • damp sandstone slabs'

TOOL = {
    'name': 'lay_cobbles',
    'what': 'lays hand-cut setts on a flat road object you name, or worn flagstones on a flat pavement object you name',
    'call': "lay_cobbles.lay_setts(road, seed=3)  /  lay_cobbles.lay_flags(pavement, seed=3)",
    'options': {
        'seed': 'which stones go where; default 0',
        'collection': "the collection the stones go in; default a new collection 'lay_cobbles'",
        'sett_material': "setts' material; default '%s'" % SETT_MATERIAL,
        'bed_material': "the road becomes this bed, seen in the joints; default '%s' (None leaves the road's own)" % BED_MATERIAL,
        'lower_road': 'metres the road (the bed) is lowered under the setts; default 0.07',
        'crown': 'metres the road edges sit lower than its middle; default 0.025',
        'missing': 'share of setts left out; default 0.007',
        'flag_material': "flags' material; default '%s'" % FLAG_MATERIAL,
        'strip_width': 'about how wide each strip of flags is, metres; default 0.7',
        'along': "which way the road or pavement runs in its own axes: 'x', 'y' or 'auto' (its longer side); default 'auto'",
        'keep_inside': 'stones at the edge are cut to fit inside the object; default True',
    },
    'materials': [SETT_MATERIAL, BED_MATERIAL, FLAG_MATERIAL],
    'source': 'plugins/painted-place/materials/lay_setts.py: lay_setts_on, lay_flags_on, _sett_prototypes, _flag_prototypes, _scatter',
    'trap': 'the stone materials project one big picture over the place: call store.fit_stone_pictures(scene) once before drawing',
}

SHAPES_COLLECTION = 'lay_cobbles shapes'


# ----------------------------------------------------------------------------------------------- where the object is

def _frame(obj):
    """The object's placement without its scale (where it stands and how it is turned), and its outline in real metres
    in that frame: (frame matrix, x0, x1, y0, y1, top)."""
    location, rotation, _ = obj.matrix_world.decompose()
    frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_frame = frame.inverted()
    corners = [to_frame @ (obj.matrix_world @ Vector(c)) for c in obj.bound_box]
    xs, ys, zs = [c.x for c in corners], [c.y for c in corners], [c.z for c in corners]
    return frame, min(xs), max(xs), min(ys), max(ys), max(zs)


class _TopFinder:
    """Height of the object's top under a point of its frame (None when the point is off the object)."""

    def __init__(self, obj, frame, top):
        self.obj = obj
        self.frame = frame
        self.top = top
        self.depsgraph = bpy.context.evaluated_depsgraph_get()
        self.to_local = obj.matrix_world.inverted()
        self.down = (self.to_local.to_3x3() @ (frame.to_3x3() @ Vector((0.0, 0.0, -1.0)))).normalized()
        self.to_frame = frame.inverted()

    def height(self, x, y):
        start = self.to_local @ (self.frame @ Vector((x, y, self.top + 0.5)))
        hit, location, normal, _ = self.obj.ray_cast(start, self.down, distance=1.0e4, depsgraph=self.depsgraph)
        if not hit:
            return None
        return (self.to_frame @ (self.obj.matrix_world @ location)).z


# ----------------------------------------------------------------------------------------------- the stone shapes

def _shapes_collection(key, collection):
    """The hidden collection holding one set of stone shapes (made once per set and material, then shared)."""
    name = '%s • %s' % (SHAPES_COLLECTION, key)
    shapes = bpy.data.collections.get(name)
    if shapes is None:
        shapes = bpy.data.collections.new(name)
    if shapes.name not in collection.children:
        collection.children.link(shapes)
    shapes.hide_render = True
    shapes.hide_viewport = True
    return shapes


def _mesh_object(name, verts, faces, material, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if material is not None:
        mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def _sett_shapes(material, collection, count=18):
    """Eighteen worn octagonal stones (1 x 1 m before each copy is sized) with rounded wet shoulders."""
    shapes = _shapes_collection('setts • ' + material.name, collection)
    if len(shapes.objects) >= count:
        return shapes
    for i in range(count):
        shape_random = random.Random(802 + i)          # the bundle's own eighteen shapes, whatever the seed
        cut = shape_random.uniform(0.04, 0.11)
        outline = [(-0.5 + cut, -0.5), (0.5 - cut, -0.5), (0.5, -0.5 + cut), (0.5, 0.5 - cut),
                   (0.5 - cut, 0.5), (-0.5 + cut, 0.5), (-0.5, 0.5 - cut), (-0.5, -0.5 + cut)]
        outline = [(x + shape_random.uniform(-0.018, 0.018), y + shape_random.uniform(-0.020, 0.020)) for x, y in outline]
        top = shape_random.uniform(-0.004, 0.004)
        verts = ([(x, y, -0.075) for x, y in outline]
                 + [(x, y, top - 0.012) for x, y in outline]
                 + [(x * 0.91, y * 0.91, top + shape_random.uniform(-0.002, 0.002)) for x, y in outline])
        faces = ([tuple(range(7, -1, -1)), tuple(range(16, 24))]
                 + [(j, (j + 1) % 8, (j + 1) % 8 + 8, j + 8) for j in range(8)]
                 + [(j + 8, (j + 1) % 8 + 8, (j + 1) % 8 + 16, j + 16) for j in range(8)])
        obj = _mesh_object('sett shape %02d' % i, verts, faces, material, shapes)
        bevel = obj.modifiers.new('rounded wet shoulders', 'BEVEL')
        bevel.width = 0.014
        bevel.segments = 3
    return shapes


def _flag_shapes(material, collection, count=8):
    """Eight flagstone slabs, 1 x 1 x 0.14 m before each copy is sized, with worn softened edges."""
    shapes = _shapes_collection('flags • ' + material.name, collection)
    if len(shapes.objects) >= count:
        return shapes
    x, y, z = 0.5, 0.5, 0.07
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for i in range(count):
        obj = _mesh_object('flag shape %d' % i, verts, faces, material, shapes)
        bevel = obj.modifiers.new('worn softened edges', 'BEVEL')
        bevel.width = 0.03
        bevel.segments = 2
    return shapes


def _laid_stones(name, points, scales, rotations, shapes_index, shapes, collection):
    """One point per stone carrying its size, turn and shape; Geometry Nodes put a live copy of a shape on each."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], [])
    mesh.update()
    for attribute, values in (('stone_scale', scales), ('stone_rotation', rotations)):
        data = mesh.attributes.new(attribute, 'FLOAT_VECTOR', 'POINT')
        data.data.foreach_set('vector', [v for value in values for v in value])
    shape = mesh.attributes.new('stone_shape', 'INT', 'POINT')
    shape.data.foreach_set('value', shapes_index)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    group = bpy.data.node_groups.new(name + ' • stones', 'GeometryNodeTree')
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
    for attribute, socket, kind in (('stone_scale', 'Scale', 'FLOAT_VECTOR'), ('stone_rotation', 'Rotation', 'FLOAT_VECTOR'),
                                    ('stone_shape', 'Instance Index', 'INT')):
        named = nodes.new('GeometryNodeInputNamedAttribute')
        named.data_type = kind
        named.inputs['Name'].default_value = attribute
        links.new(named.outputs['Attribute'], instance.inputs[socket])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('live stones', 'NODES')
    modifier.node_group = group
    return obj


def _output_collection(collection):
    if collection is not None:
        return collection
    made = bpy.data.collections.new('lay_cobbles')
    bpy.context.scene.collection.children.link(made)
    return made


def _material(name_or_material):
    if name_or_material is None:
        return None
    return store.material(name_or_material) if isinstance(name_or_material, str) else name_or_material


def _axes(along, x0, x1, y0, y1):
    """(across low, across high, along low, along high, along is x) in the object's frame."""
    if along == 'auto':
        along = 'x' if (x1 - x0) > (y1 - y0) else 'y'
    if along not in ('x', 'y'):
        raise ValueError("along is 'x', 'y' or 'auto'")
    if along == 'y':
        return x0, x1, y0, y1, False
    return y0, y1, x0, x1, True


def _clip(low, high, edge_low, edge_high, keep_inside, smallest):
    """A stone's extent along one line, cut to the object's edges; None when too little is left."""
    if not keep_inside:
        return low, high
    low, high = max(low, edge_low), min(high, edge_high)
    return (low, high) if high - low >= smallest else None


# ----------------------------------------------------------------------------------------------- setts

def lay_setts(road, seed=0, collection=None, sett_material=SETT_MATERIAL, bed_material=BED_MATERIAL, lower_road=0.07,
              crown=0.025, missing=0.007, along='auto', keep_inside=True):
    """Lay setts over a flat road object. Returns the object 'setts' (one point per stone, live copies on them)."""
    if road is None or road.type != 'MESH':
        raise ValueError('lay_setts needs a mesh object (the road)')
    bpy.context.view_layer.update()
    frame, x0, x1, y0, y1, top = _frame(road)
    a0, a1, b0, b1, swapped = _axes(along, x0, x1, y0, y1)
    finder = _TopFinder(road, frame, top)
    rng = random.Random(seed)
    target = _output_collection(collection)
    stones = _material(sett_material)
    shapes = _sett_shapes(stones, target)
    shape_count = len(shapes.objects)
    half_width = (a1 - a0) / 2
    centre = (a0 + a1) / 2
    turn = Matrix.Rotation(math.pi / 2, 3, 'Z') if swapped else Matrix.Identity(3)
    frame_turn = frame.to_3x3()
    points, scales, rotations, shapes_index = [], [], [], []
    y = b0
    shift = None
    while True:
        depth = rng.uniform(0.125, 0.19)
        if shift is None:
            shift = depth / 2 if keep_inside else 0.0        # the first course's near edge on the road's end
        row = y + shift
        if row - depth / 2 >= b1 or (not keep_inside and y >= b1):
            break
        rows_span = _clip(row - depth / 2, row + depth / 2, b0, b1, keep_inside, 0.07)
        x = a0 - rng.random() * 0.22
        while x < a1:
            width = rng.uniform(0.23, 0.36)
            if not keep_inside and x + width / 2 > a1:
                break
            jitter_a, jitter_b = rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012)
            height_wobble = rng.uniform(-0.006, 0.006)
            keep = rng.random() > missing                  # a few true missing setts
            tilt = (rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008), rng.uniform(-0.016, 0.016))
            span = _clip(x, x + width, a0, a1, keep_inside, 0.07)
            x += width
            if not keep or span is None or rows_span is None:
                continue
            stone_width = span[1] - span[0]
            stone_depth = rows_span[1] - rows_span[0]
            pa = (span[0] + span[1]) / 2 + (jitter_a if keep_inside is False or stone_width > width - 1e-6 else 0.0)
            pb = (rows_span[0] + rows_span[1]) / 2 + (jitter_b if stone_depth > depth - 1e-6 else 0.0)
            px, py = (pb, pa) if swapped else (pa, pb)
            surface = finder.height(px, py)
            if surface is None:
                continue                                    # this stone's middle is off the road
            # a slight crown: the middle of the road a little higher than its edges
            pz = surface + 0.055 + height_wobble - crown * (abs(pa - centre) / max(half_width, 0.5)) ** 1.8
            points.append(tuple(frame @ Vector((px, py, pz))))
            scales.append((stone_width - 0.008, stone_depth - 0.008, 1.0))
            rotations.append(tuple((frame_turn @ turn @ Euler(tilt).to_matrix()).to_euler()))
            shapes_index.append(rng.randrange(shape_count))
        y += depth
    setts = _laid_stones('setts', points, scales, rotations, shapes_index, shapes, target)
    store.mark(setts, ground=frame.translation.z + top)
    setts['stones'] = len(points)
    if bed_material is not None:
        store.use_material(road, _material(bed_material), ground=frame.translation.z + top)
    if lower_road and not road.get('lay_cobbles_lowered'):
        road.matrix_world = Matrix.Translation((0.0, 0.0, -lower_road)) @ road.matrix_world
        road['lay_cobbles_lowered'] = float(lower_road)
    return setts


# ----------------------------------------------------------------------------------------------- flags

def lay_flags(pavement, seed=0, collection=None, flag_material=FLAG_MATERIAL, strip_width=0.7, along='auto', keep_inside=True):
    """Lay worn flagstones over a flat pavement object, in strips along its length. The pavement stays underneath
    as the bed. Returns the object 'flags'."""
    if pavement is None or pavement.type != 'MESH':
        raise ValueError('lay_flags needs a mesh object (the pavement)')
    bpy.context.view_layer.update()
    frame, x0, x1, y0, y1, top = _frame(pavement)
    a0, a1, b0, b1, swapped = _axes(along, x0, x1, y0, y1)
    finder = _TopFinder(pavement, frame, top)
    rng = random.Random(seed)
    target = _output_collection(collection)
    slabs = _material(flag_material)
    shapes = _flag_shapes(slabs, target)
    shape_count = len(shapes.objects)
    width = a1 - a0
    strips = max(1, int(round(width / strip_width)))
    strip = width / strips
    turn = Matrix.Rotation(math.pi / 2, 3, 'Z') if swapped else Matrix.Identity(3)
    frame_turn = frame.to_3x3()
    points, scales, rotations, shapes_index = [], [], [], []
    for column in range(strips):
        middle = a0 + (column + 0.5) * strip
        y = b0
        while y < b1:
            depth = rng.uniform(0.53, 0.85)
            wander = rng.uniform(-0.02, 0.02)
            lift = rng.uniform(-0.012, 0.012)
            spread = rng.uniform(-0.03, 0.03)
            spin = rng.uniform(-0.013, 0.013)
            if not keep_inside and y + depth / 2 > b1:
                break
            if keep_inside and b1 - (y + depth) < 0.2:
                depth = b1 - y                              # the last flag of a strip cut to the pavement's end
                if depth < 0.2:
                    break
            pa, pb = middle + wander, y + depth / 2
            px, py = (pb, pa) if swapped else (pa, pb)
            y += depth
            surface = finder.height(px, py)
            if surface is None:
                continue
            flag_width = strip - 0.02 + spread
            if keep_inside:
                flag_width = min(flag_width, strip - 0.012)
            points.append(tuple(frame @ Vector((px, py, surface + 0.005 + lift))))
            scales.append((flag_width, depth - 0.025, 1.0))
            rotations.append(tuple((frame_turn @ turn @ Euler((0.0, 0.0, spin)).to_matrix()).to_euler()))
            shapes_index.append(rng.randrange(shape_count))
    flags = _laid_stones('flags', points, scales, rotations, shapes_index, shapes, target)
    store.mark(flags, ground=frame.translation.z + top)
    flags['stones'] = len(points)
    return flags


# ----------------------------------------------------------------------------------------------- command line

def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the road (or, with --flags, the pavement) object')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--flags', action='store_true', help='lay flagstones on a pavement instead of setts on a road')
    parser.add_argument('--seed', type=int, default=0, help='which stones go where; default 0')
    parser.add_argument('--sett-material', default=SETT_MATERIAL, help='setts\' material')
    parser.add_argument('--bed-material', default=BED_MATERIAL, help="the road's new material, the bed; 'none' leaves it")
    parser.add_argument('--lower-road', type=float, default=0.07, help='metres the road is lowered under the setts; default 0.07')
    parser.add_argument('--crown', type=float, default=0.025, help='metres the road edges sit lower than its middle; default 0.025')
    parser.add_argument('--missing', type=float, default=0.007, help='share of setts left out; default 0.007')
    parser.add_argument('--flag-material', default=FLAG_MATERIAL, help='flags\' material')
    parser.add_argument('--strip-width', type=float, default=0.7, help='about how wide each strip of flags is; default 0.7')
    parser.add_argument('--along', default='auto', choices=['auto', 'x', 'y'], help='which way the road runs in its own axes')
    parser.add_argument('--ragged-edge', action='store_true', help='let edge stones hang over the edge (the bundle\'s way)')
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to lay stones')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    obj = bpy.data.objects.get(args.object)
    if obj is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    if args.flags:
        made = lay_flags(obj, seed=args.seed, flag_material=args.flag_material, strip_width=args.strip_width,
                         along=args.along, keep_inside=not args.ragged_edge)
    else:
        bed = None if args.bed_material.lower() == 'none' else args.bed_material
        made = lay_setts(obj, seed=args.seed, sett_material=args.sett_material, bed_material=bed, lower_road=args.lower_road,
                         crown=args.crown, missing=args.missing, along=args.along, keep_inside=not args.ragged_edge)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s: %d stones, saved %s' % (made.name, len(made.data.vertices), args.out))


if __name__ == '__main__':
    main()
