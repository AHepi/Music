"""
What this file does: lays hand-cut stone setts (cobbles) on a flat road object you name, or along a line or curve you
give (a road that bends and climbs with it), and worn flagstones on a flat pavement object or along a line. The stones are the street bundle's ("Rain on the Old Curve"): eighteen chipped eight-sided
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

Along a line or curve (the road's middle; its height is the setts' tops there, so the road climbs and falls with it):

    line = [(0, 0, 0), (0, 8, 0), (3.5, 18, 0.4), (10.5, 26, 0.8)]     # a few points make a smooth curve; or a curve object
    setts = lay_cobbles.lay_setts_along(line, 5.0, seed=3)              # a road 5 m wide; the same wear options as lay_setts
    left, right = lay_cobbles.road_edges(line, 5.0)                     # the road's two edges, at the setts' tops there
    import lay_kerb
    lay_kerb.lay(left, road='right'); lay_kerb.lay(right, road='left')  # kerbs exactly along the road's edges
    middle, _ = lay_cobbles.road_edges(line, 5.0, beyond=0.30 + 0.9, rise=0.13)   # behind a 0.30 m kerb, 0.13 m up
    flags = lay_cobbles.lay_flags_along(middle, 1.8, seed=3)            # a 1.8 m pavement along it
    lay_cobbles.top_at(setts, x, y)                                     # the setts' tops at any place on the road

The setts go in courses straight across the road, square to the line, each course's joints at least 6 cm from the
last's; on a bend the courses fan: each is a wedge, the setts on the inside shorter than those on the outside, and a
sett is never wider than lets the wedge open its joints past `joint`. The flags go in rows across the pavement, each
flag on a bend cut to its wedge, so their joints stay even. Each makes its own bed under the stones: the road's
'road bed' 12.5 cm under the line (setts['bed']), the pavement's 'flag bed' 3.5 cm under (flags['bed']). A road's
line may bend no tighter than a radius of 1.33 times half its width (a 5 m road: 3.4 m), a pavement's no tighter than
its width (a 1.8 m pavement: 1.8 m); a tighter line is refused, with the radius it needs.

From the command line:

    python3 lay_cobbles.py --help
    python3 lay_cobbles.py --blend IN.blend --object Road --out OUT.blend [--seed 3]
    python3 lay_cobbles.py --blend IN.blend --object Pavement --flags --out OUT.blend
    python3 lay_cobbles.py --points "0,0,0 0,8,0 3.5,18,0" --width 5 --out OUT.blend      (or --blend IN.blend --line "Road line")

Options (lay_setts):
    seed            which stones go where (same seed, same road); default 0
    collection      the collection the stones go in; default a new collection 'lay_cobbles'
    sett_material   the stones' material; default 'SURFACE • dark_rock_02' (photographed; the street's own
                    'COBBLES • wet basalt / broken amber-blue reflections' still works by name)
    bed_material    the road becomes this, the bed seen in the joints; default 'SURFACE • gravel_road' (None: leave it;
                    the street's own 'ROAD BED • damp grit' still works by name)
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
    flag_material   default 'SURFACE • worn_rock_natural_01' (photographed; 'PAVEMENT • damp sandstone slabs' by name)
    strip_width     about how wide each strip of flags is, metres; default 0.7
    shades          each flag its own shade, 0 to 0.9; default 0 (0.15 is about what the street builder used)

Options (lay_setts_along): line, width (the road's, metres), and seed, collection, sett_material, bed_material,
lower_road, crown, missing and all the wear as lay_setts (rocked_area, holes, patch, moss are places in the world), and
    joint           the widest a joint may open, metres; default 0.025 (as laid the joints are 8 mm where narrowest)
What `top_height` means: on a level road, the setts' tops along its middle (as on lay_setts); on a road that climbs,
their tops on the line at its first point only (setts['top_lowest'] and setts['top_highest'] are the line's lowest and
highest): for anything placed on a climbing road ask lay_cobbles.top_at(setts, x, y), e.g. a puddle there:
puddle.make((x, y, 0), level=lay_cobbles.top_at(setts, x, y) + 0.002).

Options (lay_flags_along): line (the pavement's middle; its height is the flags' tops), width (the pavement's), seed,
collection, flag_material, shades as lay_flags, and
    bed_material    the bed under the flags' joints; default 'SURFACE • gravel_road' (None: no bed)
    joint           the widest a joint may open, metres; default 0.05 (as laid 2 cm)

road_edges(line, width, beyond=0.0, rise=0.0, crown=0.025): the road's left and right edge lines (lists of points every
5 cm, running the same way as the line), `beyond` metres outside the edge, at the setts' tops there plus `rise`.

Every sett, flag and relaid sett carries its own number 'pp_piece' (0 to 1, on the points that carry the copies): a
photographed material shows each stone its own part of its pictures by it. With a photographed material the stones
are given a copy of it, '<material> • stone sized', that undoes each copy's own size, so the pictures are at their real
size on every stone.

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

SETT_MATERIAL = 'SURFACE • dark_rock_02'              # photographed sets (decision 80; brief/store/materials/Photographed.md)
BED_MATERIAL = 'SURFACE • gravel_road'
FLAG_MATERIAL = 'SURFACE • worn_rock_natural_01'
OLD_SETT_MATERIAL = 'COBBLES • wet basalt / broken amber-blue reflections'     # the street's own: still there by name
OLD_BED_MATERIAL = 'ROAD BED • damp grit'
OLD_FLAG_MATERIAL = 'PAVEMENT • damp sandstone slabs'

TOOL = {
    'name': 'lay_cobbles',
    'what': 'lays hand-cut setts on a flat road object you name or along a line or curve you give (the road bends, '
            'climbs and fans its courses with it), and worn flagstones on a flat pavement object or along a line; '
            'road_edges gives the road\'s edge lines for lay_kerb and the pavement',
    'call': "lay_cobbles.lay_setts(road, seed=3)  /  lay_cobbles.lay_setts(road, seed=3, shades=0.3, quarries=True, rocked=0.15, holes=[(2.9, 1.0)], hole_water=True, patch=(1.3, 1.1, 2.8, 2.7), grit=True, moss=(2.9, -9, 3.4, 30))  /  lay_cobbles.lay_flags(pavement, seed=3, shades=0.15)  /  "
            "lay_cobbles.lay_setts_along([(0, 0, 0), (0, 8, 0), (3.5, 18, 0.4)], 5.0, seed=3, grit=True)  /  left, right = lay_cobbles.road_edges(line, 5.0)  /  "
            "lay_cobbles.lay_flags_along(lay_cobbles.road_edges(line, 5.0, beyond=1.2, rise=0.13)[0], 1.8, seed=3)",
    'options': {
        'line, width': "lay_setts_along and lay_flags_along: the road's (or pavement's) middle line, its height the stones' tops (a list of points, a curve or line-mesh object, or a JSON file), and its width in metres",
        'joint': 'along a line: the widest a joint may open, metres; default 0.025 for setts, 0.05 for flags',
        'seed': 'which stones go where; default 0',
        'collection': "the collection the stones go in; default a new collection 'lay_cobbles'",
        'sett_material': "setts' material; default '%s' (photographed; the street's own '%s' still works by name)" % (SETT_MATERIAL, OLD_SETT_MATERIAL),
        'bed_material': "the road becomes this bed, seen in the joints (along a line: its own bed); default '%s' (None leaves the road's own)" % BED_MATERIAL,
        'lower_road': 'metres the road (the bed) is lowered below the stones\' tops; default 0.125, at least 0.08',
        'crown': 'metres the road edges sit lower than its middle; default 0.025',
        'missing': 'share of setts left out; default 0.007',
        'flag_material': "flags' material; default '%s' (the street's own '%s' still works by name)" % (FLAG_MATERIAL, OLD_FLAG_MATERIAL),
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
    'materials': [SETT_MATERIAL, BED_MATERIAL, FLAG_MATERIAL, OLD_SETT_MATERIAL, OLD_BED_MATERIAL, OLD_FLAG_MATERIAL, 'MADE • puddle water',
                  'MADE • pebbles, wet', 'MOSS • subdued olive crevices'],
    'source': "along a line: made here for decision 80 (the owner's 'the road to a curve', 5 November 2026), following _lines.py as lay_kerb and dry_wall do; "
              "plugins/painted-place/materials/lay_setts.py: lay_setts_on, lay_flags_on, _sett_prototypes, _flag_prototypes, "
              "_scatter; the street's wear from the town street builders' '55 street - render_final.py': each stone its own "
              "shade (vary_per_stone, line 1944), setts of two quarries (line 1320), rocked and missing setts with water "
              "(lines 1235-1285), the relaid patch with pitch (line 792), grit and moss in the joints (lines 838, 1254); "
              "made into options that work on a copy of the material instead of changing the store's own",
    'trap': 'call store.prepare_for_render(scene) once before drawing; a puddle on setts: puddle.make(..., level=setts[\'top_height\'] + 0.002), but on a road laid along a climbing line top_height is only the tops at the line\'s first point: give level=lay_cobbles.top_at(setts, x, y) + 0.002; keep other ground at least 13 cm below the road; the stones wear copies of their material (\'<material> • stone sized\', and with shades, quarries or a patch \'• sett by sett\'): change those copies, not the store\'s, to change their look; a road\'s line bending tighter than 1.33 times its half width, or a pavement\'s tighter than its width, is refused, with the radius it needs (a pavement round the inside of a road\'s bend sits on a tighter line than the road: give the road room)',
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


def _sized(material):
    """A photographed material for the laid stones: they are copies of shapes 1 m across, each sized to its stone, and
    a photographed material lays its pictures in the shape's own measure, so each stone would show a whole metre of
    picture squeezed into it. The copy, '<material> • stone sized', undoes each copy's own size (the number
    'stone_scale' it carries), so every stone shows its pictures at their real size. A material without the
    photographed sets' 'Picture size' (the street's own) is given back as it is; the store's own is left as it was."""
    if material is None or not material.use_nodes or material.node_tree is None:
        return material
    node = material.node_tree.nodes.get('Picture size')
    if node is None or node.type != 'GROUP' or node.node_tree is None:
        return material
    if any(n.type == 'ATTRIBUTE' and n.attribute_name == 'stone_scale' for n in node.node_tree.nodes):
        return material                                 # it already undoes the stones' own sizes
    name = '%s • stone sized' % material.name
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_sized_of') == material.name:
        return existing
    group_name = '%s • stone sized' % node.node_tree.name
    group = bpy.data.node_groups.get(group_name)
    if group is None:
        group = node.node_tree.copy()
        group.name = group_name
        nodes, links = group.nodes, group.links
        coordinates = next(n for n in nodes if n.type == 'TEX_COORD')
        targets = [link.to_socket for link in links if link.from_node == coordinates and link.from_socket.name == 'Object']
        size = nodes.new('ShaderNodeAttribute')
        size.attribute_type = 'INSTANCER'
        size.attribute_name = 'stone_scale'

        def vmath(operation, a, b=None):
            made = nodes.new('ShaderNodeVectorMath')
            made.operation = operation
            for socket, value in zip(made.inputs, (a, b)):
                if isinstance(value, bpy.types.NodeSocket):
                    links.new(value, socket)
                elif value is not None:
                    socket.default_value = value
            return made.outputs[0]
        absolute = vmath('ABSOLUTE', size.outputs['Vector'])
        factor = vmath('ADD', absolute, vmath('SUBTRACT', (1.0, 1.0, 1.0), vmath('SIGN', absolute)))   # 1 where none
        sized = vmath('MULTIPLY', coordinates.outputs['Object'], factor)
        for target in targets:
            links.new(sized, target)
    copy = material.copy()
    copy.name = name
    copy['pp_sized_of'] = material.name
    copy.node_tree.nodes['Picture size'].node_tree = group
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
    stones = _sized(stones)
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
        numbers = {'stone_tint': tints} if tints is not None else {}
        numbers['pp_piece'] = _pieces(seed, len(points), 606 if name == 'setts' else 616)
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
    slabs = _sized(slabs)
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
    numbers = dict(numbers or {}, pp_piece=_pieces(seed, len(points)))
    flags = _laid_stones('flags', points, scales, rotations, shapes_index, shapes, target, numbers=numbers)
    store.mark(flags, ground=frame.translation.z + top)
    flags['stones'] = len(points)
    return flags


def _pieces(seed, count, salt=606):
    """Each stone its own number from 0 to 1 ('pp_piece'): a photographed material shows each stone its own part of
    its pictures by it. Its own dice: asking for it moves no stone."""
    pick = random.Random(seed * 7919 + salt)
    return [pick.random() for _ in range(count)]


# ----------------------------------------------------------------------------------------------- along a line or curve

SETT_JOINT = 0.008        # metres between two setts as laid along a line, where the joint is narrowest
FLAG_JOINT = 0.02         # metres between two flags as laid along a line, where the joint is narrowest
JITTER = 0.0015           # metres a stone laid along a line may sit off its place, each way
TURN_OFF = 0.006          # radians a stone laid along a line may be turned off square, each way


class _RoadLine:
    """The road's middle line seen from above, smoothed into the curve a wheel would take, measured along its flat
    length: where it is, which way it heads, how sharply it bends and how high it is, at any distance along it."""

    def __init__(self, line):
        import _lines
        points = []
        for point in _lines.line_points(line):
            p = Vector((point[0], point[1], point[2] if len(point) > 2 else 0.0))
            if points and (p.xy - points[-1].xy).length < 1e-5:
                continue
            points.append(p)
        if len(points) < 2:
            raise ValueError('the line needs at least two different points (seen from above)')
        smooth = numpy.array([tuple(p) for p in _lines.Path(points).smooth(0.05).points], dtype=numpy.float64)
        step = numpy.linalg.norm(numpy.diff(smooth[:, :2], axis=0), axis=1)
        smooth = smooth[numpy.concatenate([[True], step > 1e-6])]
        self.xy, self.z = smooth[:, :2], smooth[:, 2]
        self.s = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(self.xy, axis=0), axis=1))])
        self.total = float(self.s[-1])
        if self.total < 0.5:
            raise ValueError('the line is only %.2f m long: too short to lay stones along' % self.total)
        ahead = numpy.gradient(self.xy, self.s, axis=0)
        self.heading = numpy.unwrap(numpy.arctan2(ahead[:, 1], ahead[:, 0]))
        bend = numpy.gradient(self.heading, self.s)
        self.bend = numpy.convolve(numpy.pad(bend, 2, mode='edge'), numpy.ones(5) / 5.0, mode='valid')
        self.slope = numpy.gradient(self.z, self.s)

    def at(self, s):
        """(x, y, height, heading) of the line s metres along it (s may be an array)."""
        s = numpy.clip(numpy.asarray(s, dtype=numpy.float64), 0.0, self.total)
        return (numpy.interp(s, self.s, self.xy[:, 0]), numpy.interp(s, self.s, self.xy[:, 1]),
                numpy.interp(s, self.s, self.z), numpy.interp(s, self.s, self.heading))

    def place(self, s, t):
        """The point t metres to the left of the line (to its right when negative), s metres along it, seen from above."""
        x, y, _z, h = self.at(s)
        return x - t * numpy.sin(h), y + t * numpy.cos(h)

    def slope_at(self, s):
        return numpy.interp(numpy.clip(s, 0.0, self.total), self.s, self.slope)

    def tightest(self, s0, s1):
        inside = (self.s >= s0) & (self.s <= s1)
        values = numpy.concatenate([numpy.abs(self.bend[inside]), numpy.abs(numpy.interp([s0, s1], self.s, self.bend))])
        return float(values.max())

    def check_reach(self, reach, what, most=0.85):
        """Refuse a line that bends so tightly that a side `reach` metres from it would fold over itself (or, with
        `most` below 0.85, come so near to it that the stones on the inside could not be laid)."""
        worst = int(numpy.argmax(numpy.abs(self.bend)))
        if abs(self.bend[worst]) * reach > most:
            raise ValueError('the line bends too tightly for %s: %.1f m along it its radius is %.2f m, and the inside '
                             'edge, %.2f m from the line, would fold over itself or leave no room for the stones there; '
                             'give the bend a radius of at least %.1f m there' % (what, self.s[worst], 1.0 / abs(self.bend[worst]),
                                                                                 reach, reach / most))

    def edge(self, offset, spacing=0.05):
        """Points (x, y, line height) every `spacing` metres along the line, `offset` metres to its left (right when
        negative)."""
        count = max(2, int(math.ceil(self.total / spacing)) + 1)
        s = numpy.linspace(0.0, self.total, count)
        x, y = self.place(s, offset)
        return s, x, y, self.at(s)[2]


def _crown_drop(crown, half):
    return lambda t: crown * (numpy.minimum(numpy.abs(t), half) / max(half, 0.5)) ** 1.8


def _cell(road, s0, s1, t0, t1, joint):
    """A stone's place in its course: the biggest rectangle square to the line between the two straight cuts across
    the road at s0 and s1 (they meet towards the inside of a bend) and between t0 and t1 from the line, with half a
    joint left all round. Returns (middle x, middle y, heading, width, depth) or None when too little is left."""
    x0, y0, _z0, h0 = (float(v) for v in road.at(s0))
    x1, y1, _z1, h1 = (float(v) for v in road.at(s1))
    corners = numpy.array([(x0 - t * math.sin(h0), y0 + t * math.cos(h0)) for t in (t0, t1)]
                          + [(x1 - t * math.sin(h1), y1 + t * math.cos(h1)) for t in (t0, t1)])
    h = (h0 + h1) / 2.0
    right = numpy.array([math.sin(h), -math.cos(h)])
    ahead = numpy.array([math.cos(h), math.sin(h)])
    u, v = corners @ right, corners @ ahead          # 0: near cut at t0, 1: near cut at t1, 2: far cut at t0, 3: far at t1
    u_low, u_high = max(u[1], u[3]) + joint / 2, min(u[0], u[2]) - joint / 2

    def on(a, b, at):
        return max(v[a], v[b]) if abs(u[b] - u[a]) < 1e-9 else v[a] + (v[b] - v[a]) * (at - u[a]) / (u[b] - u[a])
    v_low = max(on(0, 1, u_low), on(0, 1, u_high)) + joint / 2
    v_high = min(on(2, 3, u_low), on(2, 3, u_high)) - joint / 2
    if u_high - u_low < 0.03 or v_high - v_low < 0.03:
        return None
    middle = right * (u_low + u_high) / 2 + ahead * (v_low + v_high) / 2
    return float(middle[0]), float(middle[1]), h, u_high - u_low, v_high - v_low


def _wedge(road, s0, s1, t0, t1, joint):
    """A flag's place in its row: the wedge between the two straight cuts across the road at s0 and s1 and between t0
    and t1 from the line, half a joint in from every side (so the joints stay even on a bend). Returns (middle x,
    middle y, heading, width, depth in the middle, taper) or None: the depth is depth * (1 - taper * x) at x from -0.5
    (the wedge's left, seen along the line) to 0.5 (its right) of its width."""
    x0, y0, _z0, h0 = (float(v) for v in road.at(s0))
    x1, y1, _z1, h1 = (float(v) for v in road.at(s1))
    corners = numpy.array([(x0 - t * math.sin(h0), y0 + t * math.cos(h0)) for t in (t0, t1)]
                          + [(x1 - t * math.sin(h1), y1 + t * math.cos(h1)) for t in (t0, t1)])
    h = (h0 + h1) / 2.0
    right = numpy.array([math.sin(h), -math.cos(h)])
    ahead = numpy.array([math.cos(h), math.sin(h)])
    u, v = corners @ right, corners @ ahead
    u_low, u_high = max(u[1], u[3]) + joint / 2, min(u[0], u[2]) - joint / 2

    def on(a, b, at):
        return max(v[a], v[b]) if abs(u[b] - u[a]) < 1e-9 else v[a] + (v[b] - v[a]) * (at - u[a]) / (u[b] - u[a])
    tilt = (h1 - h0) / 2.0                              # each cut is turned this much off square to the wedge's middle
    inset = joint / 2 / max(math.cos(tilt), 0.5)
    left_depth = on(2, 3, u_low) - on(0, 1, u_low) - 2 * inset
    right_depth = on(2, 3, u_high) - on(0, 1, u_high) - 2 * inset
    if u_high - u_low < 0.05 or min(left_depth, right_depth) < 0.05:
        return None
    middle_u = (u_low + u_high) / 2
    middle_v = (on(0, 1, middle_u) + on(2, 3, middle_u)) / 2
    middle = right * middle_u + ahead * middle_v
    depth = (left_depth + right_depth) / 2
    return float(middle[0]), float(middle[1]), h, u_high - u_low, depth, (left_depth - right_depth) / depth


TAPER_STEP = 0.01         # the flags' wedge shapes are made for tapers this far apart


def _wedge_flag_shapes(material, collection, most, count=8):
    """Flag shapes narrowing to one side, for flags fanned round a bend: for each taper (0, TAPER_STEP, ... up to
    `most`), the eight flag shapes, 'wedge flag NNNN' = taper step * 8 + shape, so the copies pick them by number."""
    shapes = _shapes_collection('wedge flags • ' + material.name, collection)
    steps = int(math.ceil(most / TAPER_STEP - 1e-9)) + 1
    for index in range(len(shapes.objects), steps * count):
        taper = (index // count) * TAPER_STEP
        y0, y1 = 0.5 * (1.0 + taper * 0.5), 0.5 * (1.0 - taper * 0.5)     # half depth at the left and at the right
        z = 0.07
        verts = [(-0.5, -y0, -z), (0.5, -y1, -z), (0.5, y1, -z), (-0.5, y0, -z),
                 (-0.5, -y0, z), (0.5, -y1, z), (0.5, y1, z), (-0.5, y0, z)]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        obj = _mesh_object('wedge flag %04d' % index, verts, faces, material, shapes)
        bevel = obj.modifiers.new('worn softened edges', 'BEVEL')
        bevel.width = 0.03
        bevel.segments = 2
    return shapes


def _courses(road, half, rng, depths, widths, joint, widest_joint, shortest_inside, first_shift, stagger, wedges=False,
             smallest=0.07):
    """Courses straight across the road, square to the line, one after another along it: [(s0, s1, [(t0, t1), ...])].
    On a bend a course is a wedge, shallower on the inside; a course is made deeper where its inside would be shorter
    than `shortest_inside`, and its stones narrower where the wedge would open a joint wider than `widest_joint`.
    Each course's joints are kept `stagger` metres from the last course's."""
    courses, previous, s = [], [], 0.0
    while s < road.total - 0.05:
        depth = rng.uniform(*depths)
        if wedges:                                          # a row turning no more than about 9 degrees
            turning = road.tightest(s, s + depth)
            if turning > 1e-9:
                depth = max(min(depth, 0.15 / turning), depths[0] * 0.4)
        bend = 0.0 if wedges else road.tightest(s, s + depth)
        if bend > 1e-9:                                     # a wedge so deep it would open the joints too wide
            depth = max(min(depth, (widest_joint - joint - 4 * JITTER - 0.002) / (1.3 * bend * widths[0])), depths[0] * 0.5)
        inside = max(0.15, 1.0 - road.tightest(s, s + depth) * half)
        if depth * inside < shortest_inside:                # the inside stones not too short, the outside not too long
            depth = max(depth, min(shortest_inside / inside, depths[1]))
        if road.total - (s + depth) < depths[0] * 0.6:
            depth = road.total - s                          # the last course fitted to the road's end
        s0, s1 = s, min(s + depth, road.total)
        s = s1
        wedge = 0.0 if wedges else abs(float(road.at(s1)[3]) - float(road.at(s0)[3]))
        widest = max(widths[0] * 0.5, (widest_joint - joint - 4 * JITTER - 0.002) / max(1.3 * wedge, 1e-9))
        joints, last, x = [], -half, -half - rng.random() * first_shift
        while True:
            width = min(rng.uniform(*widths), widest)
            x += width
            if x >= half - smallest:
                break                                       # the last stone reaches the edge, cut to fit
            if x <= -half + smallest:
                continue                                    # no sliver at the near edge: the first stone is cut longer
            for p in previous:
                if abs(x - p) < stagger:
                    for moved in (p + stagger + 0.004, p - stagger - 0.004):
                        if min(widths[0] * 0.6, widest) <= moved - last <= widest and moved < half - smallest:
                            x = moved
                            break
                    break
            joints.append(x)
            last = x
        broadest = max(min(widths[1], widest) + 0.01, 2 * smallest)
        if joints and half - joints[-1] > broadest:
            joints.append(joints[-1] + (half - joints[-1]) / 2)     # no stone at the edge wider than the rest: two
        if joints and joints[0] + half > broadest:
            joints.insert(0, (joints[0] - half) / 2)
        if not joints and width > broadest:
            joints = [float(t) for t in numpy.linspace(-half, half, int(math.ceil(width / broadest)) + 1)[1:-1]]
        edges = [-half] + joints + [half]
        courses.append((s0, s1, list(zip(edges[:-1], edges[1:]))))
        previous = joints
    return courses


def _strip(name, road, t_low, t_high, height, material, collection, ground, step=0.2):
    """A sheet along the line between t_low and t_high from it, each corner at height(s, t)."""
    count_s = max(2, int(math.ceil(road.total / step)) + 1)
    count_t = max(2, int(math.ceil((t_high - t_low) / step)) + 1)
    s = numpy.linspace(0.0, road.total, count_s)
    verts = []
    for t in numpy.linspace(t_low, t_high, count_t):
        x, y = road.place(s, t)
        z = height(s, t)
        verts += list(zip(x.tolist(), y.tolist(), numpy.broadcast_to(z, s.shape).tolist()))
    faces = [(j * count_s + i, j * count_s + i + 1, (j + 1) * count_s + i + 1, (j + 1) * count_s + i)
             for j in range(count_t - 1) for i in range(count_s - 1)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material is not None:
        store.use_material(obj, material, ground=ground)
    return obj


def _quads(name, quads, material, collection, ground):
    """A sheet of separate four-cornered faces, each given as four (x, y, z) corners."""
    verts, faces = [], []
    for quad in quads:
        faces.append(tuple(range(len(verts), len(verts) + 4)))
        verts += [tuple(c) for c in quad]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    store.use_material(obj, material, ground=ground)
    return obj


def _frame_of(stone):
    """A laid stone's own ways (right across the road, ahead along it), seen from above."""
    h = stone['heading']
    return numpy.array([math.sin(h), -math.cos(h)]), numpy.array([math.cos(h), math.sin(h)])


def _local_to_world(stone, u, v):
    right, ahead = _frame_of(stone)
    return stone['x'] + right[0] * u + ahead[0] * v, stone['y'] + right[1] * u + ahead[1] * v


def _turn_of(stone, tilt=(0.0, 0.0, 0.0)):
    """The stone's turn: square to the line (its heading), pitched up or down the road's climb, and its own tilt."""
    return tuple((Matrix.Rotation(stone['heading'] - math.pi / 2, 3, 'Z') @ Matrix.Rotation(stone['pitch'], 3, 'X')
                  @ Euler(tilt).to_matrix()).to_euler())


def _covered(places, stones, inset):
    """For each place (n, 2): does a laid stone stand there, more than `inset` inside its footprint?"""
    result = numpy.zeros(len(places), dtype=bool)
    if not len(places) or not stones:
        return result
    from scipy.spatial import cKDTree
    middles = numpy.array([(s['x'], s['y']) for s in stones])
    for index, near in enumerate(cKDTree(middles).query_ball_point(places, r=0.6)):
        for j in near:
            right, ahead = _frame_of(stones[j])
            d = places[index] - middles[j]
            if abs(d @ right) < stones[j]['width'] / 2 - inset and abs(d @ ahead) < stones[j]['depth'] / 2 - inset:
                result[index] = True
                break
    return result


def road_edges(line, width, beyond=0.0, rise=0.0, crown=0.025):
    """The two edge lines of the road lay_setts_along lays on this line and width: (left, right), each a list of
    (x, y, z) points every 5 cm, running the same way as the line. Each lies `beyond` metres outside the road's edge
    (0: on the edge, where a kerb's road face goes), at the setts' tops there (the line's height less the crown) plus
    `rise`. Give one to lay_kerb.lay (left with road='right', right with road='left'), or, with beyond = the kerb's
    width and half a pavement and rise = the kerb's height, to lay_flags_along as the pavement's middle line."""
    width, beyond, rise, crown = float(width), float(beyond), float(rise), float(crown)
    if not 0.5 <= width <= 40.0:
        raise ValueError('width is the road\'s width, 0.5 to 40 m; not %r' % (width,))
    road = _RoadLine(line)
    reach = width / 2 + beyond
    road.check_reach(reach, 'edges %.2f m from it' % reach)
    sides = []
    for sign in (1.0, -1.0):
        _s, x, y, z = road.edge(sign * reach)
        sides.append([(float(a), float(b), float(c) - crown + rise) for a, b, c in zip(x, y, z)])
    return sides[0], sides[1]


def top_at(setts, x, y):
    """The stones' tops at a place: on a road laid by lay_setts_along (the line's height there less the crown) or a
    pavement laid by lay_flags_along (the line's height there): for a puddle where they climb,
    puddle.make(..., level=lay_cobbles.top_at(setts, x, y) + 0.002). Setts or flags laid flat give their top_height."""
    line = setts.get('road_line')
    if line is None:
        return float(setts['top_height'])
    import _lines
    points = numpy.array(line, dtype=numpy.float64).reshape(-1, 3)
    path = _lines.Path([Vector(p) for p in points])
    along, across, _ahead = path.project(numpy.array([[x, y]]))
    flat = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(points[:, :2], axis=0), axis=1))])
    lengths = numpy.array(path.lengths)
    s = numpy.interp(along[0], lengths, flat)
    half = float(setts['road_width']) / 2
    return float(numpy.interp(s, flat, points[:, 2]) - _crown_drop(float(setts['road_crown']), half)(across[0]))


def lay_setts_along(line, width, seed=0, collection=None, sett_material=SETT_MATERIAL, bed_material=BED_MATERIAL,
                    lower_road=0.125, crown=0.025, missing=0.007, joint=0.025, shades=0.0, quarries=None, rocked=0.0,
                    rocked_area=None, holes=(), hole_water=False, patch=None, grit=False, moss=None):
    """Lay a road of setts `width` metres wide along a line or curve (its middle), climbing and falling with the line's
    heights, with its own bed under the setts. Returns the object 'setts' (one point per stone), as lay_setts does.
    The street's wear (shades ... moss) changes nothing unless asked for, as on lay_setts."""
    width, lower_road, crown, missing, joint = float(width), float(lower_road), float(crown), float(missing), float(joint)
    if not 0.5 <= width <= 40.0:
        raise ValueError('width is the road\'s width, 0.5 to 40 m; not %r' % (width,))
    if not 0.0 <= crown <= 0.2:
        raise ValueError('crown is 0 to 0.2 m, not %r' % (crown,))
    if not 0.0 <= missing <= 0.5:
        raise ValueError('missing is a share of the setts, 0 to 0.5, not %r' % (missing,))
    if not 0.015 <= joint <= 0.08:
        raise ValueError('joint is the widest a joint may open, 0.015 to 0.08 m, not %r' % (joint,))
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
    road = _RoadLine(line)
    half = width / 2
    road.check_reach(half, 'a road %.1f m wide' % width, most=0.75)
    rng = random.Random(seed)
    tint_rng = random.Random(seed * 7919 + 101)
    rock_rng = random.Random(seed * 7919 + 202)
    target = _output_collection(collection)
    stones_material = _material(sett_material)
    tinting = shades > 0 or quarries is not None or patch is not None
    if tinting:
        stones_material = _tinted(stones_material)
    stones_material = _sized(stones_material)
    shapes = _sett_shapes(stones_material, target)
    shape_count = len(shapes.objects)
    crown_drop = _crown_drop(crown, half)
    lowest = float(road.z.min())

    def stone_at(s0, s1, t0, t1, joint_here):
        cell = _cell(road, s0, s1, t0, t1, joint_here)
        if cell is None:
            return None
        x, y, heading, w, d = cell
        s_mid, t_mid = (s0 + s1) / 2, (t0 + t1) / 2
        return {'x': x, 'y': y, 'heading': heading, 'width': w, 'depth': d, 's': s_mid, 't': t_mid, 's0': s0, 's1': s1,
                'line_z': float(road.at(s_mid)[2]), 'pitch': math.atan(float(road.slope_at(s_mid)))}

    laid, gone = [], []
    for course, (s0, s1, cells) in enumerate(_courses(road, half, rng, (0.125, 0.19), (0.23, 0.36), SETT_JOINT, joint,
                                                       0.085, 0.22, 0.06)):
        for t0, t1 in cells:
            shift = (rng.uniform(-JITTER, JITTER), rng.uniform(-JITTER, JITTER))
            wobble = rng.uniform(-0.006, 0.006)
            keep = rng.random() > missing
            tilt = (rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008), rng.uniform(-TURN_OFF, TURN_OFF))
            shape = rng.randrange(shape_count)
            stone = stone_at(s0, s1, t0, t1, SETT_JOINT)
            if stone is None:
                continue
            stone['x'], stone['y'] = _local_to_world(stone, *shift)
            stone.update(z=stone['line_z'] + wobble - float(crown_drop(stone['t'])), tilt=tilt, shape=shape, course=course,
                         t0=t0, t1=t1)
            (laid if keep else gone).append(stone)

    def middle(stone):
        return (stone['x'], stone['y'])

    # the relaid patch: the old setts whose middles lie in it lifted, and the hole relaid course by course
    lifted, new_setts, lifted_prints = 0, [], []
    if patch_in is not None:
        for stone in laid:
            stone['missing'] = False
        for stone in gone:
            stone['missing'] = True
        kept_laid, kept_gone, runs = [], [], {}
        for stone in laid + gone:
            if patch_in([middle(stone)])[0]:
                runs.setdefault(stone['course'], []).append(stone)
                lifted_prints.append(stone)
                lifted += not stone['missing']
            else:
                (kept_gone if stone['missing'] else kept_laid).append(stone)
        laid, gone = kept_laid, kept_gone
        patch_rng = random.Random(seed * 7919 + 303)
        for course_number in sorted(runs):
            spans = sorted((stone['t0'], stone['t1']) for stone in runs[course_number])
            s0, s1 = runs[course_number][0]['s0'], runs[course_number][0]['s1']
            merged = [list(spans[0])]
            for low, high in spans[1:]:
                if low - merged[-1][1] < 0.05:
                    merged[-1][1] = max(merged[-1][1], high)
                else:
                    merged.append([low, high])
            for low, high in merged:
                a = low
                while a < high - 0.05:
                    w = patch_rng.uniform(0.24, 0.31)
                    if high - (a + w) < 0.1:
                        w = high - a
                    proud = patch_rng.uniform(0.0, 0.012)
                    tilt = (patch_rng.uniform(-0.005, 0.005), patch_rng.uniform(-0.005, 0.005), patch_rng.uniform(-0.004, 0.004))
                    shape = patch_rng.randrange(shape_count)
                    stone = stone_at(s0, s1, a, a + w, SETT_JOINT)
                    a += w
                    if stone is None:
                        continue
                    stone.update(z=stone['line_z'] + proud - float(crown_drop(stone['t'])), tilt=tilt, shape=shape)
                    new_setts.append(stone)

    for hx, hy in holes:
        if not laid:
            break
        middles = numpy.array([middle(stone) for stone in laid])
        gone.append(laid.pop(int(numpy.argmin(((middles - numpy.array([hx, hy])) ** 2).sum(axis=1)))))

    rocked_count = 0
    for stone in laid:
        chance, sink = rock_rng.random(), rock_rng.uniform(0.004, 0.016)
        tip = (rock_rng.uniform(-0.07, 0.07), rock_rng.uniform(-0.07, 0.07), rock_rng.uniform(-0.03, 0.03))
        if chance >= rocked or (rocked_in is not None and not rocked_in([middle(stone)])[0]):
            continue
        stone['z'] -= sink
        stone['tilt'] = tuple(t + d for t, d in zip(stone['tilt'], tip))
        rocked_count += 1

    def lay_out(name, stones_laid, shapes_used, tints, salt):
        points = [(s['x'], s['y'], s['z']) for s in stones_laid]
        scales = [(s['width'], s['depth'], 1.0) for s in stones_laid]
        rotations = [_turn_of(s, s['tilt']) for s in stones_laid]
        numbers = {'pp_piece': _pieces(seed, len(stones_laid), salt)}
        if tints is not None:
            numbers['stone_tint'] = tints
        return _laid_stones(name, points, scales, rotations, [s['shape'] for s in stones_laid], shapes_used, target,
                            numbers=numbers)

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
    setts = lay_out('setts', laid, shapes, tints, 606)
    store.mark(setts, ground=lowest)
    setts['stones'] = len(laid)
    if rocked > 0:
        setts['rocked'] = rocked_count
    bed = _material(bed_material if bed_material is not None else BED_MATERIAL)

    if patch_in is not None:
        new_rng = random.Random(seed * 7919 + 404)
        pale = [tuple([PALE * (1.0 + max(0.1, shades * 0.6) * (2.0 * new_rng.random() - 1.0))] * 3) for _ in new_setts]
        relaid = lay_out('relaid setts', new_setts, _sett_shapes(stones_material, target, bevel=0.006, key='relaid setts'),
                         pale, 616)
        store.mark(relaid, ground=lowest)
        quads = []
        for stone in lifted_prints:
            corners = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                u, v = su * (stone['width'] / 2 + 0.019), sv * (stone['depth'] / 2 + 0.019)
                x, y = _local_to_world(stone, u, v)
                corners.append((x, y, stone['line_z'] + math.tan(stone['pitch']) * v - 0.010
                                - float(crown_drop(stone['t'] - u))))
            quads.append(corners)
        setts['relaid setts'], setts['pitch'] = relaid, _quads('pitch', quads, _pitch_material(), target, lowest)
        setts['relaid'], setts['lifted'] = len(new_setts), lifted

    if grit:
        setts['grit bed'] = _strip('grit bed', road, -half, half,
                                   lambda s, t: road.at(s)[2] - GRIT_DEPTH - crown_drop(t), bed, target, lowest)
        joint_rng = random.Random(seed * 7919 + 505)
        candidates = []
        for stone in laid:
            for edge, length in (('a', stone['depth']), ('b', stone['width'])):
                for _ in range(int(length * 28 + joint_rng.random())):
                    along_edge = joint_rng.uniform(-0.5, 0.5)
                    if edge == 'a':
                        u, v = stone['width'] / 2 + 0.003, along_edge * stone['depth']
                    else:
                        u, v = along_edge * stone['width'], stone['depth'] / 2 + 0.003
                    x, y = _local_to_world(stone, u, v)
                    candidates.append((x, y, stone['z'] - joint_rng.uniform(0.024, 0.031), joint_rng.uniform(0.014, 0.032),
                                       joint_rng.uniform(0.0, math.tau), joint_rng.randrange(6), joint_rng.random() < 0.55))
        if candidates:
            places = numpy.array([(c[0], c[1]) for c in candidates])
            hidden = _covered(places, laid, 0.002)
            inside = numpy.abs(_across(road, places)) < half - 0.004
            candidates = [c for c, h, i in zip(candidates, hidden, inside) if not h and i]
        found = {'grit': ([], [], [], []), 'moss': ([], [], [], [])}
        for x, y, z, size, turn_z, shape, mossy in candidates:
            kind = 'moss' if (moss_in is not None and mossy and moss_in([(x, y)])[0]) else 'grit'
            if kind == 'moss':
                size *= 1.35
            points, scales, rotations, shapes_index = found[kind]
            points.append((x, y, z))
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
            store.mark(made, ground=lowest)
            setts[name] = made

    if holes or hole_water:
        setts['holes'] = len(gone)
    if hole_water and gone:
        verts, faces, shallow, floors = [], [], [], []
        for stone in gone:
            first = len(verts)
            verts.append((stone['x'], stone['y'], stone['z'] - WATER_DEPTH))
            shallow.append(0.35)
            for k in range(8):
                angle = math.tau * k / 8
                x, y = _local_to_world(stone, math.cos(angle) * (stone['width'] / 2 + 0.03) * 1.08,
                                       math.sin(angle) * (stone['depth'] / 2 + 0.03) * 1.08)
                verts.append((x, y, stone['z'] - WATER_DEPTH))
                shallow.append(1.0)
            faces += [(first, first + 1 + k, first + 1 + (k + 1) % 8) for k in range(8)]
            corners = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                x, y = _local_to_world(stone, su * (stone['width'] / 2 + 0.03), sv * (stone['depth'] / 2 + 0.03))
                corners.append((x, y, stone['z'] - GRIT_DEPTH - 0.01))
            floors.append(corners)
        mesh = bpy.data.meshes.new('hole water')
        mesh.from_pydata(verts, [], faces)
        layer = mesh.attributes.new('shallow', 'FLOAT', 'POINT')
        layer.data.foreach_set('value', shallow)
        mesh.update()
        water = bpy.data.objects.new('hole water', mesh)
        target.objects.link(water)
        store.use_material(water, WATER_MATERIAL, ground=lowest)
        setts['hole water'] = water
        if not grit:
            setts['grit bed'] = _quads('grit bed', floors, bed, target, lowest)

    # the road's own bed, `lower_road` under the line, seen in the joints
    if lower_road < 0.08:
        print('lay_setts_along: lower_road %.3f is too shallow (the bed would cover the stones); using 0.08' % lower_road)
        lower_road = 0.08
    road_bed = _strip('road bed', road, -half, half, lambda s, t: road.at(s)[2] - lower_road + 0.0 * t,
                      bed if bed_material is not None else None, target, lowest - lower_road, step=0.25)
    road_bed['lay_cobbles_lowered'] = float(lower_road)
    setts['bed'] = road_bed
    setts['top_height'] = float(road.z[0])          # the stones' tops on the line at its first point
    setts['top_lowest'], setts['top_highest'] = lowest, float(road.z.max())
    setts['road_width'], setts['road_crown'] = width, crown
    setts['road_line'] = [float(v) for i in range(0, len(road.s), 2) for v in (road.xy[i, 0], road.xy[i, 1], road.z[i])] \
        + [float(road.xy[-1, 0]), float(road.xy[-1, 1]), float(road.z[-1])]
    return setts


def _across(road, places):
    """How far to the left of the road's line each place lies (an (n, 2) array), metres."""
    import _lines
    path = _lines.Path([Vector((x, y, 0.0)) for x, y in road.xy])
    _along, across, _ahead = path.project(places)
    return across


def lay_flags_along(line, width, seed=0, collection=None, flag_material=FLAG_MATERIAL, bed_material=BED_MATERIAL,
                    joint=0.05, shades=0.0):
    """Lay worn flagstones on a pavement `width` metres wide along a line or curve (its middle; the line's height is
    the flags' tops), in rows across the pavement, fanning on a bend as the setts do, with a bed under the joints.
    Returns the object 'flags', as lay_flags does."""
    width, joint, shades = float(width), float(joint), float(shades)
    if not 0.4 <= width <= 12.0:
        raise ValueError('width is the pavement\'s width, 0.4 to 12 m; not %r' % (width,))
    if not 0.03 <= joint <= 0.12:
        raise ValueError('joint is the widest a joint between flags may open, 0.03 to 0.12 m, not %r' % (joint,))
    if not 0.0 <= shades <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    road = _RoadLine(line)
    half = width / 2
    road.check_reach(half, 'a pavement %.1f m wide' % width, most=0.5)
    rng = random.Random(seed)
    target = _output_collection(collection)
    slabs = _material(flag_material)
    if shades > 0:
        slabs = _tinted(slabs)
    slabs = _sized(slabs)
    across = min(0.9, max(0.45, width / max(1, round(width / 0.7))))
    laid = []
    for s0, s1, cells in _courses(road, half, rng, (0.53, 0.85), (across * 0.8, across * 1.25), FLAG_JOINT, joint,
                                  0.3, across, 0.12, wedges=True, smallest=0.2):
        for t0, t1 in cells:
            shift = (rng.uniform(-JITTER, JITTER), rng.uniform(-JITTER, JITTER))
            lift = rng.uniform(-0.006, 0.006)
            spin = rng.uniform(-TURN_OFF, TURN_OFF)
            shape = rng.randrange(8)
            cell = _wedge(road, s0, s1, t0, t1, FLAG_JOINT)
            if cell is None:
                continue
            x, y, heading, w, d, taper = cell
            s_mid = (s0 + s1) / 2
            if taper < 0:                                   # narrowing to its left: the shape turned half round
                heading, taper = heading + math.pi, -taper
            stone = {'x': x, 'y': y, 'heading': heading, 'width': w, 'depth': d, 'taper': taper,
                     'pitch': math.atan(float(road.slope_at(s_mid))) * (1.0 if math.cos(heading - float(road.at(s_mid)[3])) > 0 else -1.0)}
            stone['x'], stone['y'] = _local_to_world(stone, *shift)
            stone.update(z=float(road.at(s_mid)[2]) - 0.07 + lift, tilt=(0.0, 0.0, spin),
                         shape=int(round(taper / TAPER_STEP)) * 8 + shape)
            laid.append(stone)
    shapes = _wedge_flag_shapes(slabs, target, max([s['taper'] for s in laid] + [0.0]))
    numbers = {'pp_piece': _pieces(seed, len(laid)), 'stone_taper': [s['taper'] for s in laid]}
    if shades > 0:
        tint_rng = random.Random(seed * 7919 + 101)
        numbers['stone_tint'] = [tuple([1.0 + shades * (2.0 * tint_rng.random() - 1.0)] * 3) for _ in laid]
    lowest = float(road.z.min())
    flags = _laid_stones('flags', [(s['x'], s['y'], s['z']) for s in laid], [(s['width'], s['depth'], 1.0) for s in laid],
                         [_turn_of(s, s['tilt']) for s in laid], [s['shape'] for s in laid], shapes, target, numbers=numbers)
    store.mark(flags, ground=lowest)
    flags['stones'] = len(laid)
    if bed_material is not None:
        flags['bed'] = _strip('flag bed', road, -half, half, lambda s, t: road.at(s)[2] - 0.035 + 0.0 * t,
                              _material(bed_material), target, lowest - 0.035, step=0.25)
    flags['top_height'] = float(road.z[0])          # the flags' tops on the line at its first point: top_at for anywhere
    flags['road_width'], flags['road_crown'] = width, 0.0
    flags['road_line'] = [float(v) for i in range(0, len(road.s), 2) for v in (road.xy[i, 0], road.xy[i, 1], road.z[i])] \
        + [float(road.xy[-1, 0]), float(road.xy[-1, 1]), float(road.z[-1])]
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
    parser.add_argument('--line', help='lay along this curve or line-mesh object (the road\'s or pavement\'s middle) instead of on --object; needs --width')
    parser.add_argument('--points', help='lay along this line instead, "x,y,z x,y,z ..." (a new file unless --blend is given); needs --width')
    parser.add_argument('--width', type=float, help='the road\'s (or with --flags the pavement\'s) width along --line or --points, metres')
    parser.add_argument('--joint', type=float, help='along a line: the widest a joint may open, metres; default 0.025 (flags 0.05)')
    args = parser.parse_args(argv)
    if args.line or args.points:
        if not (args.width and args.out):
            parser.error('--width and --out are needed to lay stones along a line')
        if args.blend:
            bpy.ops.wm.open_mainfile(filepath=args.blend)
        else:
            bpy.ops.wm.read_factory_settings(use_empty=True)
        line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()] if args.points else bpy.data.objects.get(args.line)
        if line is None:
            parser.error('no object %r in %s' % (args.line, args.blend))
        if args.flags:
            made = lay_flags_along(line, args.width, seed=args.seed, flag_material=args.flag_material, shades=args.shades,
                                   **({'joint': args.joint} if args.joint else {}))
        else:
            bed = None if args.bed_material.lower() == 'none' else args.bed_material
            made = lay_setts_along(line, args.width, seed=args.seed, sett_material=args.sett_material, bed_material=bed,
                                   lower_road=args.lower_road, crown=args.crown, missing=args.missing, shades=args.shades,
                                   quarries=tuple(args.quarries) if args.quarries else None, rocked=args.rocked,
                                   patch=tuple(args.patch) if args.patch else None, hole_water=args.hole_water, grit=args.grit,
                                   moss='all' if args.moss_everywhere else None, **({'joint': args.joint} if args.joint else {}))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('%s: %d stones, saved %s' % (made.name, len(made.data.vertices), args.out))
        return
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to lay stones (or --line / --points with --width)')
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
