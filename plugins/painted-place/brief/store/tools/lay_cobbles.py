"""
What this file does: lays hand-cut stone setts (cobbles) on a flat road object you name, and worn flagstones on a flat
pavement object you name. The stones are the street bundle's ("Rain on the Old Curve"): eighteen chipped eight-sided
sett shapes (eight worn flag shapes), each stone its own small turn, size and height, so nothing repeats. Setts are
laid in courses across the road, a slight crown in the middle, a few true missing setts; the stones' tops sit at the
road's own height along its middle (a little lower towards its edges), so a thing you stand on the road at its height
stands on the stones; the road itself becomes the dark damp bed 12.5 cm below the tops, seen in the joints. Flags are laid in strips along the pavement. Nothing here decides
where the road or pavement is: the stones go only on the object you pass, inside its outline.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import bpy
    import lay_cobbles
    setts = lay_cobbles.lay_setts(my_road, seed=3)              # returns the object 'setts' (one point per stone)
    print(setts['top_height'])                                  # the stones' tops: the road's height before it was lowered
    flags = lay_cobbles.lay_flags(my_pavement, seed=3)          # returns the object 'flags'
    print(len(setts.data.vertices), 'setts')
    import store
    store.prepare_for_render(bpy.context.scene)                 # once, before drawing (it fits the stone pictures)

From the command line:

    python3 lay_cobbles.py --help
    python3 lay_cobbles.py --blend IN.blend --object Road --out OUT.blend [--seed 3]
    python3 lay_cobbles.py --blend IN.blend --object Pavement --flags --out OUT.blend

Options (lay_setts):
    seed            which stones go where (same seed, same road); default 0
    collection      the collection the stones go in; default a new collection 'lay_cobbles'
    sett_material   the stones' material; default 'COBBLES • wet basalt / broken amber-blue reflections'
    bed_material    the road becomes this, the bed seen in the joints; default 'ROAD BED • damp grit' (None: leave it)
    lower_road      how far the road (the bed) is lowered below the stones' tops, metres; default 0.125, at least 0.08
                    (any less and the road's surface would cover the stones)
    crown           how much lower the edges of the road are than its middle, metres; default 0.025
    missing         the share of setts left out (true missing setts); default 0.007
    along           which way the road runs in its own axes: 'x', 'y' or 'auto' (its longer side); default 'auto'
    keep_inside     stones at the road's edge are cut to fit inside it; default True (False: the bundle's ragged edge)


The street's wear, each an option that changes nothing unless asked for (lay_setts):
    shades          each sett its own shade: how much one is lighter or darker than the next, 0 to 0.9; default 0
                    (0.3 is about what the street builder used)
    quarries        setts from two quarries: (warm share, dark share), e.g. (0.32, 0.12): that share stained warm
                    brown (iron in the stone, rust off the tyres) and that share blue-black whinstone; True gives
                    (0.32, 0.12); default None
    rocked          the share of setts rocked loose by the wheels, 0 to 1: each sunk up to 1.6 cm and tipped, so it
                    catches the light its own way; default 0
    rocked_area     where setts are rocked: a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or None (all over)
    holes           places [(x, y), ...] where a sett is gone: the sett whose middle is nearest each place; default none
    hole_water      True: water stands in every hole (these and the `missing` ones) 2 cm under the tops, over wet grit;
                    default False
    patch           a relaid patch: a rectangle (x0, y0, x1, y1) or a polygon [(x, y), ...]: the old setts there are
                    lifted and new ones laid, paler, sharper edged, a little proud, shiny black pitch in the joints;
                    default None
    grit            True: grit and small stones packed into every joint, 3 cm under the tops, so the joints never read
                    as bottomless black lines; default False
    moss            where moss grows in the joints instead of some of the grit: a rectangle, a polygon or 'all'
                    (needs grit=True); default None
What the wear makes, in the same collection, each named on the setts object: setts['relaid setts'], setts['pitch'],
setts['hole water'], setts['grit bed'], setts['joint stones'], setts['joint moss'] (only those asked for); and the counts
setts['rocked'], setts['holes'], setts['relaid'], setts['lifted'].

Options (lay_flags): seed, collection, along, keep_inside as above, and
    flag_material   default 'PAVEMENT • damp sandstone slabs'
    strip_width     about how wide each strip of flags is, metres; default 0.7
    shades          each flag its own shade, 0 to 0.9; default 0 (0.15 is about what the street builder used)

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
import numpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import store  # noqa: E402

SETT_MATERIAL = 'COBBLES • wet basalt / broken amber-blue reflections'
BED_MATERIAL = 'ROAD BED • damp grit'
FLAG_MATERIAL = 'PAVEMENT • damp sandstone slabs'

TOOL = {
    'name': 'lay_cobbles',
    'what': 'lays hand-cut setts on a flat road object you name, or worn flagstones on a flat pavement object you name',
    'call': "lay_cobbles.lay_setts(road, seed=3)  /  lay_cobbles.lay_setts(road, seed=3, shades=0.3, quarries=True, rocked=0.15, holes=[(2.9, 1.0)], hole_water=True, patch=(1.3, 1.1, 2.8, 2.7), grit=True, moss=(2.9, -9, 3.4, 30))  /  lay_cobbles.lay_flags(pavement, seed=3, shades=0.15)",
    'options': {
        'seed': 'which stones go where; default 0',
        'collection': "the collection the stones go in; default a new collection 'lay_cobbles'",
        'sett_material': "setts' material; default '%s'" % SETT_MATERIAL,
        'bed_material': "the road becomes this bed, seen in the joints; default '%s' (None leaves the road's own)" % BED_MATERIAL,
        'lower_road': 'metres the road (the bed) is lowered below the stones\' tops; default 0.125, at least 0.08',
        'crown': 'metres the road edges sit lower than its middle; default 0.025',
        'missing': 'share of setts left out; default 0.007',
        'flag_material': "flags' material; default '%s'" % FLAG_MATERIAL,
        'strip_width': 'about how wide each strip of flags is, metres; default 0.7',
        'along': "which way the road or pavement runs in its own axes: 'x', 'y' or 'auto' (its longer side); default 'auto'",
        'keep_inside': 'stones at the edge are cut to fit inside the object; default True',
        'shades': 'each sett (or flag) its own shade: how much one is lighter or darker than the next, 0 to 0.9; default 0',
        'quarries': 'setts from two quarries: (warm share, dark share): warm brown and blue-black whinstone; True is (0.32, 0.12); default None',
        'rocked, rocked_area': 'the share of setts rocked loose (sunk, tipped), 0 to 1, and where (a rectangle or polygon; None all over); default 0',
        'holes, hole_water': 'places [(x, y), ...] where a sett is gone; True: water standing in every hole over wet grit; default none, False',
        'patch': 'a relaid patch, a rectangle or polygon: new paler, sharper setts, a little proud, shiny black pitch in the joints; default None',
        'grit, moss': "True: grit and small stones packed in every joint 3 cm under the tops; moss in the joints instead of some grit within a rectangle, polygon or 'all'; default False, None",
    },
    'materials': [SETT_MATERIAL, BED_MATERIAL, FLAG_MATERIAL, 'MADE • puddle water', 'MADE • pebbles, wet', 'MOSS • subdued olive crevices'],
    'source': "plugins/painted-place/materials/lay_setts.py: lay_setts_on, lay_flags_on, _sett_prototypes, _flag_prototypes, "
              "_scatter; the street's wear from the town street builders' '55 street - render_final.py': each stone its own "
              "shade (vary_per_stone, line 1944), setts of two quarries (line 1320), rocked and missing setts with water "
              "(lines 1235-1285), the relaid patch with pitch (line 792), grit and moss in the joints (lines 838, 1254); "
              "made into options that work on a copy of the material instead of changing the store's own",
    'trap': 'the stone materials project one big picture over the place: call store.prepare_for_render(scene) once before drawing (it fits them); a puddle on setts: puddle.make(..., level=setts[\'top_height\'] + 0.002); keep other ground at least 13 cm below the road; shades, quarries and a patch put a copy of the sett material on the setts (\'<material> • sett by sett\'): change that copy, not the store\'s, to change their look',
}

SHAPES_COLLECTION = 'lay_cobbles shapes'
QUARRIES = (0.32, 0.12)            # the street builder's: about a third warm brown, one in eight blue-black
WARM = (1.32, 0.98, 0.72)          # a warm brown sett's colour, times the sett material's own
DARK = (0.72, 0.78, 0.86)          # a blue-black whinstone sett's
PALE = 2.0                         # how much paler the relaid patch's new setts are than the old
WATER_MATERIAL = 'MADE • puddle water'
GRIT_MATERIAL = 'MADE • pebbles, wet'
MOSS_MATERIAL = 'MOSS • subdued olive crevices'
PITCH = 'lay_cobbles • pitch'
GRIT_DEPTH = 0.03                  # metres under the setts' tops the grit is packed in the joints
WATER_DEPTH = 0.02                 # metres under the setts' tops water stands in a hole


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


def _sett_shapes(material, collection, count=18, bevel=0.014, key='setts'):
    """Eighteen worn octagonal stones (1 x 1 m before each copy is sized) with rounded wet shoulders (`bevel`; the
    relaid patch's new setts are sharper)."""
    shapes = _shapes_collection(key + ' • ' + material.name, collection)
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
        rounding = obj.modifiers.new('rounded wet shoulders', 'BEVEL')
        rounding.width = bevel
        rounding.segments = 3
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


def _laid_stones(name, points, scales, rotations, shapes_index, shapes, collection, numbers=None):
    """One point per stone carrying its size, turn and shape; Geometry Nodes put a live copy of a shape on each.
    `numbers` adds more per-stone numbers {name: values} (a list of 3-number tuples is written as a vector): the copies
    carry them, for a material to read (an Attribute node of the Instancer kind)."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], [])
    mesh.update()
    for attribute, values in (('stone_scale', scales), ('stone_rotation', rotations)):
        data = mesh.attributes.new(attribute, 'FLOAT_VECTOR', 'POINT')
        data.data.foreach_set('vector', [v for value in values for v in value])
    shape = mesh.attributes.new('stone_shape', 'INT', 'POINT')
    shape.data.foreach_set('value', shapes_index)
    for attribute, values in (numbers or {}).items():
        vector = bool(values) and isinstance(values[0], (tuple, list))
        data = mesh.attributes.new(attribute, 'FLOAT_VECTOR' if vector else 'FLOAT', 'POINT')
        if values:
            data.data.foreach_set('vector' if vector else 'value', [v for value in values for v in value] if vector else list(values))
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


def _tinted(material):
    """A copy of a stone material in which each stone's colour is times its own 'stone_tint' (a colour each laid
    stone carries: its shade, its quarry, the relaid patch's paleness). Named '<material> • sett by sett'; made once
    for a material, then shared; the store's own material is left as it was."""
    name = '%s • sett by sett' % material.name
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_tinted_of') == material.name:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_tinted_of'] = material.name
    if not copy.use_nodes or copy.node_tree is None:
        return copy
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    for principled in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        base = principled.inputs['Base Color']
        source = base.links[0].from_socket if base.links else None
        tint = nodes.new('ShaderNodeAttribute')
        tint.attribute_type = 'INSTANCER'
        tint.attribute_name = 'stone_tint'
        multiply = nodes.new('ShaderNodeMix')
        multiply.data_type = 'RGBA'
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1.0
        if source is not None:
            links.new(source, multiply.inputs[6])
        else:
            multiply.inputs[6].default_value = base.default_value
        links.new(tint.outputs['Color'], multiply.inputs[7])
        links.new(multiply.outputs[2], base)
    return copy


def _pitch_material():
    """Road pitch run into the relaid setts' joints: near black, glossy, a little uneven (made here, once)."""
    existing = bpy.data.materials.get(PITCH)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(PITCH)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    principled.inputs['Base Color'].default_value = (0.008, 0.007, 0.006, 1.0)
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 12.0
    rough = nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = 0.03
    rough.inputs['To Max'].default_value = 0.14
    links.new(noise.outputs['Fac'], rough.inputs['Value'])
    links.new(rough.outputs['Result'], principled.inputs['Roughness'])
    return material


def _lump_shapes(material, collection, key, flat, count=6):
    """Small rough lumps 1 m across before each copy is sized (grit stones, moss cushions), squashed to `flat`."""
    import bmesh
    shapes = _shapes_collection(key + ' • ' + material.name, collection)
    for i in range(len(shapes.objects), count):
        pick = random.Random(905 + 17 * i + len(key))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5)
        for vertex in bm.verts:
            vertex.co = Vector((vertex.co.x * pick.uniform(0.85, 1.15), vertex.co.y * pick.uniform(0.85, 1.15),
                                vertex.co.z * flat * pick.uniform(0.8, 1.2)))
        mesh = bpy.data.meshes.new('%s %d' % (key, i))
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(material)
        shapes.objects.link(bpy.data.objects.new('%s %d' % (key, i), mesh))
    return shapes


def _sheet(name, frame, swapped, cells, height, material, collection):
    """A sheet over the cells [(a0, a1, b0, b1)] of the road's frame (across a, along b), each corner at height(a)
    in the frame (so it follows the road's crown); one face per cell."""
    verts, faces, index = [], [], {}

    def corner(a, b):
        key = (round(a, 5), round(b, 5))
        if key not in index:
            px, py = (b, a) if swapped else (a, b)
            index[key] = len(verts)
            verts.append(tuple(frame @ Vector((px, py, height(a)))))
        return index[key]
    for a0, a1, b0, b1 in cells:
        faces.append((corner(a0, b0), corner(a1, b0), corner(a1, b1), corner(a0, b1)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    store.use_material(obj, material, ground=frame.translation.z)
    return obj


def _grid(low_a, high_a, low_b, high_b, step):
    cells = []
    count_a = max(1, int(math.ceil((high_a - low_a) / step)))
    count_b = max(1, int(math.ceil((high_b - low_b) / step)))
    for i in range(count_a):
        for j in range(count_b):
            a0, a1 = low_a + (high_a - low_a) * i / count_a, low_a + (high_a - low_a) * (i + 1) / count_a
            b0, b1 = low_b + (high_b - low_b) * j / count_b, low_b + (high_b - low_b) * (j + 1) / count_b
            cells.append((a0, a1, b0, b1))
    return cells


def _quarries(quarries):
    if quarries is None or quarries is False:
        return None
    if quarries is True:
        return QUARRIES
    try:
        warm, dark = (float(v) for v in quarries)
    except (TypeError, ValueError):
        raise ValueError('quarries is (warm share, dark share), e.g. (0.32, 0.12), or True; not %r' % (quarries,))
    if warm < 0 or dark < 0 or warm + dark > 1:
        raise ValueError('quarries: the two shares are each 0 to 1 and together at most 1; not %r' % (quarries,))
    return warm, dark


def _where(area, what):
    """A function telling, for (n, 2) points, which lie in the area (a rectangle, a polygon or 'all')."""
    import stones
    if isinstance(area, str):
        if area != 'all':
            raise ValueError("%s is a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or 'all'; not %r" % (what, area))
        return lambda xy: numpy.ones(len(numpy.asarray(xy).reshape(-1, 2)), dtype=bool)
    try:
        weigh, _box = stones._area(area)
    except ValueError:
        raise ValueError('%s is a rectangle (x0, y0, x1, y1) or a polygon [(x, y), ...]; not %r' % (what, area))
    return lambda xy: weigh(numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)) > 0.5


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

def lay_setts(road, seed=0, collection=None, sett_material=SETT_MATERIAL, bed_material=BED_MATERIAL, lower_road=0.125,
              crown=0.025, missing=0.007, along='auto', keep_inside=True, shades=0.0, quarries=None, rocked=0.0,
              rocked_area=None, holes=(), hole_water=False, patch=None, grit=False, moss=None):
    """Lay setts over a flat road object. Returns the object 'setts' (one point per stone, live copies on them). The
    street's wear (shades ... moss) changes nothing unless asked for: see the note at the top."""
    if road is None or road.type != 'MESH':
        raise ValueError('lay_setts needs a mesh object (the road)')
    shades, rocked = float(shades), float(rocked)
    if not 0.0 <= shades <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    quarries = _quarries(quarries)
    if not 0.0 <= rocked <= 1.0:
        raise ValueError('rocked is a share of the setts, 0 to 1, not %r' % (rocked,))
    rocked_in = _where(rocked_area, 'rocked_area') if rocked_area is not None else None
    try:
        holes = [(float(h[0]), float(h[1])) for h in (holes or ())]
    except (TypeError, IndexError, ValueError):
        raise ValueError('holes is a list of places [(x, y), ...], not %r' % (holes,))
    if isinstance(patch, str):
        raise ValueError('patch is a rectangle (x0, y0, x1, y1) or a polygon [(x, y), ...]; not %r' % (patch,))
    patch_in = _where(patch, 'patch') if patch is not None else None
    if moss is not None and not grit:
        raise ValueError('moss grows in the grit packed in the joints: ask for grit=True as well')
    moss_in = _where(moss, 'moss') if moss is not None else None
    bpy.context.view_layer.update()
    frame, x0, x1, y0, y1, top = _frame(road)
    a0, a1, b0, b1, swapped = _axes(along, x0, x1, y0, y1)
    finder = _TopFinder(road, frame, top)
    rng = random.Random(seed)
    tint_rng = random.Random(seed * 7919 + 101)      # the wear's own dice: asking for it moves no stone of the road
    rock_rng = random.Random(seed * 7919 + 202)
    target = _output_collection(collection)
    stones = _material(sett_material)
    tinting = shades > 0 or quarries is not None or patch is not None
    if tinting:
        stones = _tinted(stones)
    shapes = _sett_shapes(stones, target)
    shape_count = len(shapes.objects)
    half_width = (a1 - a0) / 2
    centre = (a0 + a1) / 2
    turn = Matrix.Rotation(math.pi / 2, 3, 'Z') if swapped else Matrix.Identity(3)
    frame_turn = frame.to_3x3()

    def crown_drop(a):
        return crown * (abs(a - centre) / max(half_width, 0.5)) ** 1.8

    def place(pa, pb, z):
        px, py = (pb, pa) if swapped else (pa, pb)
        return frame @ Vector((px, py, z))

    laid = []       # each kept sett: [pa, pb, pz, width, depth, tilt, shape]
    gone = []       # each missing sett's hole: (pa, pb, pz, width, depth)
    y = b0
    shift = None
    course = -1
    while True:
        course += 1
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
            if span is None or rows_span is None:
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
            # the stones' tops at the road's own height in the middle (so anything stood on the road at its height stands on
            # them), the bed lowered under them: the same joints and depths as the street bundle, only the whole laid 5.5 cm lower
            pz = surface + height_wobble - crown_drop(pa)
            if not keep:
                gone.append((pa, pb, pz, stone_width, stone_depth, course, rows_span))
                continue
            laid.append([pa, pb, pz, stone_width, stone_depth, tilt, rng.randrange(shape_count), course, rows_span])
        y += depth

    def footprint(pa, pb, width, depth, inset=0.0):
        """The sett's middle and four corners, seen from above, in the world."""
        corners = [(pa, pb)] + [(pa + sa * (width / 2 - inset), pb + sb * (depth / 2 - inset))
                                for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        return [tuple(place(a, b, top))[:2] for a, b in corners]

    # the relaid patch: the old setts whose middles lie in it lifted, and the hole relaid course by course with new setts
    lifted = 0
    new_setts = []
    lifted_prints = []
    if patch_in is not None:
        kept, hole_runs = [], {}
        for stone in laid + [list(hole[:5]) + [None, None] + list(hole[5:]) for hole in gone]:
            if patch_in([footprint(stone[0], stone[1], stone[3], stone[4])[0]])[0]:
                hole_runs.setdefault(stone[7], []).append((stone[0] - stone[3] / 2, stone[0] + stone[3] / 2, stone[8], stone[2]))
                lifted_prints.append(stone)
                lifted += stone[5] is not None
            elif stone[5] is not None:
                kept.append(stone)
        laid = kept
        gone = [hole for hole in gone if not patch_in([footprint(hole[0], hole[1], hole[3], hole[4])[0]])[0]]
        patch_rng = random.Random(seed * 7919 + 303)
        for course_number in sorted(hole_runs):
            spans = sorted(hole_runs[course_number])
            rows = spans[0][2]
            runs = [[spans[0][0], spans[0][1]]]
            for low, high, _rows, _z in spans[1:]:          # neighbouring lifted setts make one run across the road
                if low - runs[-1][1] < 0.05:
                    runs[-1][1] = max(runs[-1][1], high)
                else:
                    runs.append([low, high])
            for low, high in runs:
                a = low
                while a < high - 0.05:
                    width = patch_rng.uniform(0.24, 0.31)
                    if high - (a + width) < 0.1:
                        width = high - a                    # the last one cut to fit, as the road men do
                    proud = patch_rng.uniform(0.0, 0.012)   # a week old: not yet sunk to the old setts' level
                    tilt = (patch_rng.uniform(-0.005, 0.005), patch_rng.uniform(-0.005, 0.005), patch_rng.uniform(-0.012, 0.012))
                    shape = patch_rng.randrange(shape_count)
                    pa, pb = a + width / 2, (rows[0] + rows[1]) / 2
                    a += width
                    px, py = (pb, pa) if swapped else (pa, pb)
                    surface = finder.height(px, py)
                    if surface is None:
                        continue
                    new_setts.append([pa, pb, surface + proud - crown_drop(pa), width - 0.006, rows[1] - rows[0] - 0.006, tilt, shape])

    # setts taken out where you say
    for hx, hy in holes:
        if not laid:
            break
        middles = numpy.array([footprint(s[0], s[1], s[3], s[4])[0] for s in laid])
        nearest = int(numpy.argmin(((middles - numpy.array([hx, hy])) ** 2).sum(axis=1)))
        stone = laid.pop(nearest)
        gone.append(tuple(stone[:5]))

    # setts rocked loose by the wheels: sunk a little and tipped
    rocked_count = 0
    for stone in laid:
        chance, sink = rock_rng.random(), rock_rng.uniform(0.004, 0.016)
        tip = (rock_rng.uniform(-0.07, 0.07), rock_rng.uniform(-0.07, 0.07), rock_rng.uniform(-0.03, 0.03))
        if chance >= rocked:
            continue
        if rocked_in is not None and not rocked_in([footprint(stone[0], stone[1], stone[3], stone[4])[0]])[0]:
            continue
        stone[2] -= sink
        stone[5] = tuple(t + d for t, d in zip(stone[5], tip))
        rocked_count += 1

    def lay_out(name, stones_laid, shapes_used, tints):
        points, scales, rotations, shapes_index = [], [], [], []
        for pa, pb, pz, width, depth, tilt, shape in (stone[:7] for stone in stones_laid):
            points.append(tuple(place(pa, pb, pz)))
            scales.append((width - 0.008, depth - 0.008, 1.0))
            rotations.append(tuple((frame_turn @ turn @ Euler(tilt).to_matrix()).to_euler()))
            shapes_index.append(shape)
        numbers = {'stone_tint': tints} if tints is not None else None
        return _laid_stones(name, points, scales, rotations, shapes_index, shapes_used, target, numbers=numbers)

    tints = None
    if tinting:
        tints = []
        for _stone in laid:
            tone = 1.0 + shades * (2.0 * tint_rng.random() - 1.0)
            pick = tint_rng.random()
            colour = (1.0, 1.0, 1.0)
            if quarries is not None and pick < quarries[0]:
                colour = WARM
            elif quarries is not None and pick > 1.0 - quarries[1]:
                colour = DARK
            tints.append(tuple(tone * c for c in colour))
    setts = lay_out('setts', laid, shapes, tints)
    store.mark(setts, ground=frame.translation.z + top)
    setts['stones'] = len(laid)
    if rocked > 0:
        setts['rocked'] = rocked_count
    ground_z = frame.translation.z + top
    bed = _material(bed_material if bed_material is not None else BED_MATERIAL)

    if patch_in is not None:
        new_rng = random.Random(seed * 7919 + 404)
        pale = [tuple([PALE * (1.0 + max(0.1, shades * 0.6) * (2.0 * new_rng.random() - 1.0))] * 3) for _ in new_setts]
        relaid = lay_out('relaid setts', new_setts, _sett_shapes(stones, target, bevel=0.006, key='relaid setts'), pale)
        store.mark(relaid, ground=ground_z)
        cells = [(s[0] - s[3] / 2 - 0.015, s[0] + s[3] / 2 + 0.015, s[1] - s[4] / 2 - 0.015, s[1] + s[4] / 2 + 0.015)
                 for s in lifted_prints]
        pitch = _sheet('pitch', frame, swapped, cells, lambda a: top - 0.010 - crown_drop(a), _pitch_material(), target)
        setts['relaid setts'], setts['pitch'] = relaid, pitch
        setts['relaid'], setts['lifted'] = len(new_setts), lifted

    if grit:
        cells = [cell for cell in _grid(a0, a1, b0, b1, 0.2)
                 if finder.height(*(((cell[2] + cell[3]) / 2, (cell[0] + cell[1]) / 2) if swapped else
                                    ((cell[0] + cell[1]) / 2, (cell[2] + cell[3]) / 2))) is not None]
        setts['grit bed'] = _sheet('grit bed', frame, swapped, cells, lambda a: top - GRIT_DEPTH - crown_drop(a), bed, target)
        joint_rng = random.Random(seed * 7919 + 505)
        candidates = []
        for pa, pb, pz, width, depth, tilt, _shape in (stone[:7] for stone in laid):
            for edge, length in (('a', depth), ('b', width)):      # the joint beyond its far side, and beyond its far end
                for _ in range(int(length * 28 + joint_rng.random())):
                    along_edge = joint_rng.uniform(-0.5, 0.5)
                    if edge == 'a':
                        ja, jb = pa + width / 2 + 0.002, pb + along_edge * depth
                    else:
                        ja, jb = pa + along_edge * width, pb + depth / 2 + 0.002
                    candidates.append((ja, jb, pz - joint_rng.uniform(0.024, 0.031), joint_rng.uniform(0.014, 0.032),
                                       joint_rng.uniform(0.0, math.tau), joint_rng.randrange(6), joint_rng.random() < 0.55))
        # the setts are laid a little off true, so a neighbour may close a joint: nothing goes where a sett stands
        if candidates and laid:
            from scipy.spatial import cKDTree
            middles = numpy.array([(stone[0], stone[1]) for stone in laid])
            halves = numpy.array([(stone[3] / 2 - 0.004, stone[4] / 2 - 0.004) for stone in laid])
            places = numpy.array([(c[0], c[1]) for c in candidates])
            covered = numpy.zeros(len(places), dtype=bool)
            for index, near in enumerate(cKDTree(middles).query_ball_point(places, r=0.3)):
                if near:
                    offset = numpy.abs(middles[near] - places[index])
                    covered[index] = bool(((offset[:, 0] < halves[near, 0] - 0.002) & (offset[:, 1] < halves[near, 1] - 0.002)).any())
            candidates = [c for c, hidden in zip(candidates, covered) if not hidden]
        found = {'grit': ([], [], [], []), 'moss': ([], [], [], [])}
        for ja, jb, z, size, turn_z, shape, mossy in candidates:
            where = place(ja, jb, z)
            kind = 'moss' if (moss_in is not None and mossy and moss_in([tuple(where)[:2]])[0]) else 'grit'
            if kind == 'moss':
                size *= 1.35
            points, scales, rotations, shapes_index = found[kind]
            points.append(tuple(where))
            scales.append((size, size, size))
            rotations.append((0.0, 0.0, turn_z))
            shapes_index.append(shape)
        for kind, material_name, flat, name in (('grit', GRIT_MATERIAL, 0.6, 'joint stones'), ('moss', MOSS_MATERIAL, 0.4, 'joint moss')):
            points, scales, rotations, shapes_index = found[kind]
            if not points:
                continue
            numbers = {'wetness': [0.9] * len(points), 'stone_burial': [0.45] * len(points)} if kind == 'grit' else None
            made = _laid_stones(name, points, scales, rotations, shapes_index,
                                _lump_shapes(_material(material_name), target, name, flat), target, numbers=numbers)
            store.mark(made, ground=ground_z)
            setts[name] = made

    if holes or hole_water:
        setts['holes'] = len(gone)
    if hole_water and gone:
        verts, faces, shallow = [], [], []
        floors = []
        for pa, pb, pz, width, depth in (hole[:5] for hole in gone):
            middle = len(verts)
            verts.append(tuple(place(pa, pb, pz - WATER_DEPTH)))
            shallow.append(0.35)
            for k in range(8):                                  # reaching just under the setts round the hole
                angle = math.tau * k / 8
                verts.append(tuple(place(pa + math.cos(angle) * (width / 2 + 0.03) * 1.08,
                                         pb + math.sin(angle) * (depth / 2 + 0.03) * 1.08, pz - WATER_DEPTH)))
                shallow.append(1.0)
            faces += [(middle, middle + 1 + k, middle + 1 + (k + 1) % 8) for k in range(8)]
            floors.append((pa - width / 2 - 0.03, pa + width / 2 + 0.03, pb - depth / 2 - 0.03, pb + depth / 2 + 0.03, pz))
        mesh = bpy.data.meshes.new('hole water')
        mesh.from_pydata(verts, [], faces)
        layer = mesh.attributes.new('shallow', 'FLOAT', 'POINT')
        layer.data.foreach_set('value', shallow)
        mesh.update()
        water = bpy.data.objects.new('hole water', mesh)
        target.objects.link(water)
        store.use_material(water, WATER_MATERIAL, ground=ground_z)
        setts['hole water'] = water
        if not grit:                                            # wet grit at the bottom of each hole
            floor_verts, floor_faces = [], []
            for a_low, a_high, b_low, b_high, pz in floors:
                base = len(floor_verts)
                floor_verts += [tuple(place(a, b, pz - GRIT_DEPTH - 0.01)) for a, b in
                                ((a_low, b_low), (a_high, b_low), (a_high, b_high), (a_low, b_high))]
                floor_faces.append((base, base + 1, base + 2, base + 3))
            mesh = bpy.data.meshes.new('grit bed')
            mesh.from_pydata(floor_verts, [], floor_faces)
            mesh.update()
            floor = bpy.data.objects.new('grit bed', mesh)
            target.objects.link(floor)
            store.use_material(floor, bed, ground=ground_z)
            setts['grit bed'] = floor

    if bed_material is not None:
        store.use_material(road, _material(bed_material), ground=frame.translation.z + top)
    setts['top_height'] = float(frame.translation.z + top)        # the road's height before it was lowered: the stones' tops
    if lower_road < 0.08:
        print('lay_setts: lower_road %.3f is too shallow (the road would cover the stones); using 0.08' % lower_road)
        lower_road = 0.08
    if lower_road and not road.get('lay_cobbles_lowered'):
        road.matrix_world = Matrix.Translation((0.0, 0.0, -lower_road)) @ road.matrix_world
        road['lay_cobbles_lowered'] = float(lower_road)
    return setts


# ----------------------------------------------------------------------------------------------- flags

def lay_flags(pavement, seed=0, collection=None, flag_material=FLAG_MATERIAL, strip_width=0.7, along='auto', keep_inside=True,
              shades=0.0):
    """Lay worn flagstones over a flat pavement object, in strips along its length. The pavement stays underneath
    as the bed. Returns the object 'flags'. shades > 0: each flag its own shade (a copy of the material reads it)."""
    if pavement is None or pavement.type != 'MESH':
        raise ValueError('lay_flags needs a mesh object (the pavement)')
    shades = float(shades)
    if not 0.0 <= shades <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    bpy.context.view_layer.update()
    frame, x0, x1, y0, y1, top = _frame(pavement)
    a0, a1, b0, b1, swapped = _axes(along, x0, x1, y0, y1)
    finder = _TopFinder(pavement, frame, top)
    rng = random.Random(seed)
    target = _output_collection(collection)
    slabs = _material(flag_material)
    if shades > 0:
        slabs = _tinted(slabs)
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
    numbers = None
    if shades > 0:
        tint_rng = random.Random(seed * 7919 + 101)            # its own dice: the flags lie where they would without it
        numbers = {'stone_tint': [tuple([1.0 + shades * (2.0 * tint_rng.random() - 1.0)] * 3) for _ in points]}
    flags = _laid_stones('flags', points, scales, rotations, shapes_index, shapes, target, numbers=numbers)
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
    parser.add_argument('--lower-road', type=float, default=0.125, help='metres the road (the bed) is lowered below the setts\' tops; default 0.125, at least 0.08')
    parser.add_argument('--crown', type=float, default=0.025, help='metres the road edges sit lower than its middle; default 0.025')
    parser.add_argument('--missing', type=float, default=0.007, help='share of setts left out; default 0.007')
    parser.add_argument('--flag-material', default=FLAG_MATERIAL, help='flags\' material')
    parser.add_argument('--strip-width', type=float, default=0.7, help='about how wide each strip of flags is; default 0.7')
    parser.add_argument('--along', default='auto', choices=['auto', 'x', 'y'], help='which way the road runs in its own axes')
    parser.add_argument('--ragged-edge', action='store_true', help='let edge stones hang over the edge (the bundle\'s way)')
    parser.add_argument('--shades', type=float, default=0.0, help='each stone its own shade, 0 to 0.9; default 0')
    parser.add_argument('--quarries', type=float, nargs=2, metavar=('WARM', 'DARK'), help='setts from two quarries: the warm brown share and the blue-black share')
    parser.add_argument('--rocked', type=float, default=0.0, help='the share of setts rocked loose, 0 to 1; default 0')
    parser.add_argument('--patch', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='a relaid patch: new paler setts, pitch in the joints')
    parser.add_argument('--hole-water', action='store_true', help='water standing in the holes of missing setts')
    parser.add_argument('--grit', action='store_true', help='grit and small stones packed in the joints')
    parser.add_argument('--moss-everywhere', action='store_true', help='moss in the joints among the grit (with --grit)')
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to lay stones')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    obj = bpy.data.objects.get(args.object)
    if obj is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    if args.flags:
        made = lay_flags(obj, seed=args.seed, flag_material=args.flag_material, strip_width=args.strip_width,
                         along=args.along, keep_inside=not args.ragged_edge, shades=args.shades)
    else:
        bed = None if args.bed_material.lower() == 'none' else args.bed_material
        made = lay_setts(obj, seed=args.seed, sett_material=args.sett_material, bed_material=bed, lower_road=args.lower_road,
                         crown=args.crown, missing=args.missing, along=args.along, keep_inside=not args.ragged_edge,
                         shades=args.shades, quarries=tuple(args.quarries) if args.quarries else None, rocked=args.rocked,
                         patch=tuple(args.patch) if args.patch else None, hole_water=args.hole_water, grit=args.grit,
                         moss='all' if args.moss_everywhere else None)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s: %d stones, saved %s' % (made.name, len(made.data.vertices), args.out))


if __name__ == '__main__':
    main()
