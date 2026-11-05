"""
What this file does: (re)builds the store's materials file, materials/Materials.blend. It keeps the street bundle's 45
materials as they are (their sandstone pictures packed inside), and rebuilds every other material in it:

  - SURFACE • <set>: one per photographed surface on the shelf (brief/surfaces/), laid from three sides in the
    object's own space at the picture's real size, darkened into the look's range, with dials (see below); each
    piece a tool marks with the number 'pp_piece' shows its own part of the picture (pieces_group);
  - BRICK • <set> and ASHLAR • <set>: the wall photographs whose whole bricks and blocks find_atlas.py found
    (materials/atlas/<set>.json), read through the wall tool's UV map 'pp_atlas' (atlas_material);
  - MADE • dirt, MADE • dirt, dark, MADE • pebbles, wet: the ground tools' soil and stones (ground_materials.py);
  - MADE • ...: the materials made in code (made.py: old brass, copper, china, weathered boards, wet bark, puddle water,
    a wet-ground film, rusty nail heads, a rust stain), and two made here from shelf photographs: wet mud (the forest
    mud soaked), army canvas (the linen weave without its blue dye) and the walkway's boards (rough sawn wood laid along each
    board by its 'metres' UV map).

    python3 build_materials.py            (run from anywhere; needs the bpy module and Pillow)

Every SURFACE material has two dial nodes a builder may change from a script:
    mat.node_tree.nodes['Picture size'].inputs['Scale']   1 = the photograph's real size; 2 = twice as big
    mat.node_tree.nodes['Weather'].inputs[...]:
        'Darken'      how much of the photograph's brightness is kept (set per surface so it sits in the look)
        'Wet'         0 dry, 1 soaked: darker and glossier
        'Grime'       dirt settled in hollows and corners (0 none, 1 heavy)
        'Mud height'  metres of mud splashed up from the ground (0 none)
        'Mud color'   the mud's colour
        'Edge wear'   corners and edges rubbed paler (0 none, 1 strong; costs render time when above 0)
        'Bump'        how strongly the photograph's relief shows
    mat.node_tree.nodes['Pieces'].inputs['Turn' | 'Shade']   each piece's own turn (1 any angle, 0 none) and shade
The pictures are kept as paths to the shelf (`//../../surfaces/...`), not packed, so the file stays small; the
store's loader finds them again wherever the brief folder is.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import ground_materials  # noqa: E402
import made  # noqa: E402
from node_helpers import fresh_material, map_range, math, mix, noise  # noqa: E402

MATERIALS = os.path.dirname(HERE)
STORE = os.path.dirname(MATERIALS)
BRIEF = os.path.dirname(STORE)
SHELF = os.path.join(BRIEF, 'surfaces')
TARGET = os.path.join(MATERIALS, 'Materials.blend')

STREET = {
    'Chimney smoke • organic soft wisps': 'chimney smoke: a volume for a box above a chimney (soft wisps, not balloons)',
    'COBBLES • wet basalt / broken amber-blue reflections': 'the street\'s wet cobbles (setts): basalt, broken reflections; the cobbles tool lays them',
    'Damp • fine dark soot': 'fine dark soot and damp, for staining walls',
    'Fallen leaf • ochre': 'a fallen leaf, ochre',
    'Fallen leaf • peat brown': 'a fallen leaf, peat brown',
    'Fine cool rain haze': 'a thin cool haze volume',
    'GLASS • dim amber rooms': 'window glass with a dim amber room behind (a faint glow)',
    'GLASS • sleeping navy interiors': 'dark window glass, navy room behind',
    'GLASS • warm occupied interiors': 'lit window glass, a warm occupied room behind (glows; give it a light of its own outside the glass)',
    'GRIME • dark damp organic residue': 'dark damp grime, for wall feet and corners',
    'IRON • soot-black lamp posts': 'soot-black painted iron (lamp posts, railings, brackets)',
    'LAMP • honey flame glow': 'a gas mantle or flame glow (emits light colour; add a real light beside it)',
    'Lantern • glowing imperfect amber glass': 'glowing amber lantern glass',
    'MORTAR • dark eroded joints': 'dark eroded mortar, for joints behind stones and bricks',
    'Moss • organic irregular green-gold': 'moss, green-gold, irregular',
    'MOSS • subdued olive crevices': 'moss, subdued olive, for crevices',
    'PAPER • aged torn fragments': 'aged torn paper (posters, notices without words)',
    'PAVEMENT • damp sandstone slabs': 'damp sandstone flags; the cobbles tool lays them on a pavement',
    'PLASTER • mineral flakes and scars': 'old plaster with flakes and scars',
    'PUDDLE • shallow transparent reflective film': 'the street\'s puddle film (a thin reflective sheet)',
    'Rain glints • cool subtle streaks': 'rain glints, for falling rain streaks',
    'Rain • faint blue glint': 'faint blue rain glint',
    'RECESSES • near-black blue': 'near-black blue for deep recesses (inside doorways, behind sashes)',
    'ROAD BED • damp grit': 'damp grit, the bed under setts (reads as a mirror on wide open ground: use a SURFACE mud there)',
    'RUST • rain-aged iron': 'rain-aged rusted iron',
    'SLATE • soot-dark irregular roofs': 'soot-dark slate roofs',
    'STONE • unique sandstone / damp soot': 'natural sandstone with damp and soot (rocks, rubble)',
    'STONE • worn honey-grey architectural dressings': 'worn honey-grey dressed stone (sills, lintels, kerbs, quoins)',
    'WATER • puddle film / IOR 1.333': 'clear water film',
    'Weed • dark ivy': 'dark ivy leaves',
    'Weed • rain olive': 'rain-olive weeds',
    'Weed • yellowed seed blades': 'yellowed seed grass blades',
    'WOOD • peeling dark painted doors': 'dark painted wood, peeling (doors, shutters, sashes, frames)',
}
for shade in range(12):
    STREET['Hand-painted sandstone • shade %02d' % shade] = 'sandstone wall, shade %d of 12 (project one big picture: call store.fit_stone_pictures)' % shade


def _socket(group, name, kind, in_out, default=None, low=None, high=None):
    socket = group.interface.new_socket(name, in_out=in_out, socket_type=kind)
    if default is not None and hasattr(socket, 'default_value'):
        socket.default_value = default
    if low is not None and hasattr(socket, 'min_value'):
        socket.min_value = low
    if high is not None and hasattr(socket, 'max_value'):
        socket.max_value = high
    return socket


def box_coordinates_group():
    """The object's own coordinates, its unapplied scale undone (the object number 'pp_scale'), divided by the
    picture's real size times the Scale dial: one unit is one copy of the picture."""
    group = bpy.data.node_groups.new('STORE • box coordinates', 'ShaderNodeTree')
    _socket(group, 'Size', 'NodeSocketVector', 'INPUT', (1.0, 1.0, 1.0))
    _socket(group, 'Scale', 'NodeSocketFloat', 'INPUT', 1.0, 0.01, 100.0)
    _socket(group, 'Vector', 'NodeSocketVector', 'OUTPUT')
    nodes, links = group.nodes, group.links
    inputs, outputs = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    coordinates = nodes.new('ShaderNodeTexCoord')
    scale_attribute = nodes.new('ShaderNodeAttribute')
    scale_attribute.attribute_type = 'OBJECT'
    scale_attribute.attribute_name = 'pp_scale'

    def vmath(operation, a, b=None):
        node = nodes.new('ShaderNodeVectorMath')
        node.operation = operation
        for socket, value in zip(node.inputs, (a, b)):
            if value is None:
                continue
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, socket)
            else:
                socket.default_value = value
        return node.outputs[0]

    absolute = vmath('ABSOLUTE', scale_attribute.outputs['Vector'])
    missing = vmath('SUBTRACT', (1.0, 1.0, 1.0), vmath('SIGN', absolute))       # 1 where no scale was recorded
    real_scale = vmath('ADD', absolute, missing)
    world_sized = vmath('MULTIPLY', coordinates.outputs['Object'], real_scale)
    size = nodes.new('ShaderNodeVectorMath')
    size.operation = 'SCALE'
    links.new(inputs.outputs['Size'], size.inputs[0])
    links.new(inputs.outputs['Scale'], size.inputs['Scale'])
    links.new(vmath('DIVIDE', world_sized, size.outputs[0]), outputs.inputs['Vector'])
    return group


def weather_group(with_normal=False):
    """Darken, mud from the ground up, grime in hollows, worn edges, wetness and relief, for any photographed surface.
    with_normal: the group takes a Normal (the set's normal picture, already turned into world space) and lays the
    height picture's relief over it."""
    group = bpy.data.node_groups.new('STORE • weather with normal picture' if with_normal else 'STORE • weather', 'ShaderNodeTree')
    _socket(group, 'Color', 'NodeSocketColor', 'INPUT', (0.5, 0.5, 0.5, 1.0))
    _socket(group, 'Roughness', 'NodeSocketFloat', 'INPUT', 0.7, 0.0, 1.0)
    _socket(group, 'Height', 'NodeSocketFloat', 'INPUT', 0.5, 0.0, 1.0)
    _socket(group, 'Darken', 'NodeSocketFloat', 'INPUT', 1.0, 0.0, 2.0)
    _socket(group, 'Wet', 'NodeSocketFloat', 'INPUT', 0.0, 0.0, 1.0)
    _socket(group, 'Grime', 'NodeSocketFloat', 'INPUT', 0.3, 0.0, 1.0)
    _socket(group, 'Mud height', 'NodeSocketFloat', 'INPUT', 0.0, 0.0, 5.0)
    _socket(group, 'Mud color', 'NodeSocketColor', 'INPUT', (0.034, 0.028, 0.020, 1.0))
    _socket(group, 'Edge wear', 'NodeSocketFloat', 'INPUT', 0.0, 0.0, 1.0)
    _socket(group, 'Bump', 'NodeSocketFloat', 'INPUT', 0.3, 0.0, 2.0)
    if with_normal:
        _socket(group, 'Normal', 'NodeSocketVector', 'INPUT', (0.0, 0.0, 1.0))
    _socket(group, 'Base Color', 'NodeSocketColor', 'OUTPUT')
    _socket(group, 'Roughness', 'NodeSocketFloat', 'OUTPUT')
    _socket(group, 'Normal', 'NodeSocketVector', 'OUTPUT')
    nodes, links = group.nodes, group.links
    g_in, g_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    geometry = nodes.new('ShaderNodeNewGeometry')

    def scale_colour(colour, factor):
        node = nodes.new('ShaderNodeVectorMath')
        node.operation = 'SCALE'
        links.new(colour, node.inputs[0])
        if isinstance(factor, bpy.types.NodeSocket):
            links.new(factor, node.inputs['Scale'])
        else:
            node.inputs['Scale'].default_value = factor
        return node.outputs[0]

    def mix_colour(factor, a, b):
        node = nodes.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        for socket, value in ((node.inputs[0], factor), (node.inputs[6], a), (node.inputs[7], b)):
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, socket)
            else:
                socket.default_value = value
        return node.outputs[2]

    colour = scale_colour(g_in.outputs['Color'], g_in.outputs['Darken'])
    # mud splashed up from the ground: height above the ground under the object (object number 'pp_ground')
    ground = nodes.new('ShaderNodeAttribute')
    ground.attribute_type = 'OBJECT'
    ground.attribute_name = 'pp_ground'
    position = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geometry.outputs['Position'], position.inputs['Vector'])
    height = math(nodes, links, 'SUBTRACT', position.outputs['Z'], ground.outputs['Fac'])
    splash = nodes.new('ShaderNodeTexNoise')
    splash.inputs['Scale'].default_value = 3.5
    splash.inputs['Detail'].default_value = 6.0
    links.new(geometry.outputs['Position'], splash.inputs['Vector'])
    reach = math(nodes, links, 'MULTIPLY', g_in.outputs['Mud height'], math(nodes, links, 'MULTIPLY_ADD', splash.outputs['Fac'], 0.9, 0.35))
    mud = map_range(nodes, links, math(nodes, links, 'SUBTRACT', height, reach), -0.08, 0.03, 0.92, 0.0)
    mud = math(nodes, links, 'MULTIPLY', mud, math(nodes, links, 'GREATER_THAN', g_in.outputs['Mud height'], 0.001))
    colour = mix_colour(mud, colour, g_in.outputs['Mud color'])
    # grime settled where surfaces close in on each other
    occlusion = nodes.new('ShaderNodeAmbientOcclusion')
    occlusion.samples = 8
    occlusion.inputs['Distance'].default_value = 0.3
    crevice = map_range(nodes, links, occlusion.outputs['AO'], 0.95, 0.4)
    grime = math(nodes, links, 'MULTIPLY', crevice, g_in.outputs['Grime'])
    colour = mix_colour(grime, colour, scale_colour(colour, 0.28))
    # edges and corners rubbed paler
    bevel = nodes.new('ShaderNodeBevel')
    bevel.samples = 4
    bevel.inputs['Radius'].default_value = 0.015
    facing = nodes.new('ShaderNodeVectorMath')
    facing.operation = 'DOT_PRODUCT'
    links.new(bevel.outputs['Normal'], facing.inputs[0])
    links.new(geometry.outputs['Normal'], facing.inputs[1])
    edge = map_range(nodes, links, math(nodes, links, 'SUBTRACT', 1.0, facing.outputs['Value']), 0.0, 0.06)
    worn = math(nodes, links, 'MULTIPLY', edge, g_in.outputs['Edge wear'])
    colour = mix_colour(worn, colour, scale_colour(colour, 1.8))
    # wet: darker and glossier
    colour = scale_colour(colour, math(nodes, links, 'MULTIPLY_ADD', g_in.outputs['Wet'], -0.5, 1.0))
    links.new(colour, g_out.inputs['Base Color'])
    wet_gloss = math(nodes, links, 'MULTIPLY', g_in.outputs['Wet'], 0.85)
    rough = math(nodes, links, 'MULTIPLY_ADD', wet_gloss, math(nodes, links, 'SUBTRACT', 0.1, g_in.outputs['Roughness']), g_in.outputs['Roughness'])
    links.new(rough, g_out.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.02
    links.new(g_in.outputs['Bump'], bump.inputs['Strength'])
    links.new(g_in.outputs['Height'], bump.inputs['Height'])
    if with_normal:
        links.new(g_in.outputs['Normal'], bump.inputs['Normal'])
    links.new(bump.outputs['Normal'], g_out.inputs['Normal'])
    return group


# Blender's BOX projection lays a picture on each side of the box like this (measured in log 54: for each side, the
# object axis along which the picture's u grows, and the one along which its v grows):
#   +X: u along +Y, v along +Z    -X: u along -Y, v along +Z
#   +Y: u along -X, v along +Z    -Y: u along +X, v along +Z
#   +Z: u along -Y, v along +X    -Z: u along +Y, v along +X
def box_normal_group():
    """A photographed set's normal picture (OpenGL, green up), read through the same BOX projection as its colour, turned
    into a world-space normal: on each side of the box its x runs along the way the picture's u grows there, its y along
    the way v grows, its z out of that side (the table above); between sides the three are blended by how squarely the
    surface faces each. Strength 0 gives the plain surface, 1 the picture's full relief."""
    group = bpy.data.node_groups.new('STORE • box normal picture', 'ShaderNodeTree')
    _socket(group, 'Color', 'NodeSocketColor', 'INPUT', (0.5, 0.5, 1.0, 1.0))
    _socket(group, 'Strength', 'NodeSocketFloat', 'INPUT', 1.0, 0.0, 2.0)
    _socket(group, 'Axis', 'NodeSocketVector', 'INPUT', (0.0, 0.0, 1.0))
    _socket(group, 'Angle', 'NodeSocketFloat', 'INPUT', 0.0)
    _socket(group, 'Normal', 'NodeSocketVector', 'OUTPUT')
    nodes, links = group.nodes, group.links
    g_in, g_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    coordinates = nodes.new('ShaderNodeTexCoord')

    def plug(socket, value):
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value

    def vmath(operation, a, b=None, c=None, scale=None):
        node = nodes.new('ShaderNodeVectorMath')
        node.operation = operation
        if operation == 'SCALE':
            plug(node.inputs[0], a)
            plug(node.inputs['Scale'], scale)
        else:
            for socket, value in zip(node.inputs, (a, b, c)):
                if value is not None:
                    plug(socket, value)
        return node.outputs['Vector']

    def separate(vector):
        node = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vector, node.inputs['Vector'])
        return node.outputs['X'], node.outputs['Y'], node.outputs['Z']

    def combine(x, y, z):
        node = nodes.new('ShaderNodeCombineXYZ')
        for socket, value in zip(node.inputs, (x, y, z)):
            plug(socket, value)
        return node.outputs['Vector']

    def times(a, b):
        return math(nodes, links, 'MULTIPLY', a, b)

    x, y, z = separate(vmath('MULTIPLY_ADD', g_in.outputs['Color'], (2.0, 2.0, 2.0), (-1.0, -1.0, -1.0)))   # 0..1 to -1..1
    facing = vmath('NORMALIZE', coordinates.outputs['Normal'])                                                  # object space
    fx, fy, fz = separate(facing)
    sx, sy, sz = (math(nodes, links, 'SIGN', f) for f in (fx, fy, fz))
    # the picture as each side reads it, in object space (u direction * x + v direction * y + the side's outward * z)
    on_x = combine(times(z, sx), times(x, sx), y)
    on_y = combine(times(times(x, sy), -1.0), times(z, sy), y)
    on_z = combine(y, times(times(x, sz), -1.0), times(z, sz))
    # how squarely the surface faces each side, sharp as the BOX projection's own blend
    wx, wy, wz = separate(vmath('POWER', vmath('ABSOLUTE', facing), (8.0, 8.0, 8.0)))
    total = math(nodes, links, 'ADD', math(nodes, links, 'ADD', wx, wy), wz)
    blended = vmath('ADD', vmath('ADD', vmath('SCALE', on_x, scale=wx), vmath('SCALE', on_y, scale=wy)), vmath('SCALE', on_z, scale=wz))
    blended = vmath('SCALE', blended, scale=math(nodes, links, 'DIVIDE', 1.0, math(nodes, links, 'MAXIMUM', total, 1e-6)))
    # a piece whose picture was turned (the Pieces node's Angle about its Axis) has its relief turned back the same way,
    # so it stays lit from the right side; with no turn (Angle 0) this changes nothing
    turned_back = nodes.new('ShaderNodeVectorRotate')
    turned_back.rotation_type = 'AXIS_ANGLE'
    turned_back.invert = True
    links.new(blended, turned_back.inputs['Vector'])
    links.new(g_in.outputs['Axis'], turned_back.inputs['Axis'])
    links.new(g_in.outputs['Angle'], turned_back.inputs['Angle'])
    blended = turned_back.outputs['Vector']
    # strength: from the plain surface (0) to the picture's relief (1)
    mixed = vmath('ADD', facing, vmath('SCALE', vmath('SUBTRACT', blended, facing), scale=g_in.outputs['Strength']))
    to_world = nodes.new('ShaderNodeVectorTransform')
    to_world.vector_type = 'NORMAL'
    to_world.convert_from = 'OBJECT'
    to_world.convert_to = 'WORLD'
    links.new(vmath('NORMALIZE', mixed), to_world.inputs['Vector'])
    links.new(vmath('NORMALIZE', to_world.outputs['Vector']), g_out.inputs['Normal'])
    return group


def pieces_group():
    """Each piece its own part of the photograph: reads the number 'pp_piece' (0..1, one random number per brick, block,
    sett, flag or kerbstone) from the mesh's faces or from the points that instanced the copy, and gives back how far
    to turn the picture (Angle, about the Axis the face looks along), how far to shift it (Offset, in copies of the
    picture) and how much lighter or darker to make it (Brightness). Where 'pp_piece' is absent (0) they are 0, 0 and
    1 exactly, so the material draws as it did before. Dials: Turn (1 any angle, 0 never turned), Shade (0.12: up to
    12 per cent lighter or darker)."""
    group = bpy.data.node_groups.new('STORE • pieces', 'ShaderNodeTree')
    _socket(group, 'Turn', 'NodeSocketFloat', 'INPUT', 1.0, 0.0, 1.0)
    _socket(group, 'Shade', 'NodeSocketFloat', 'INPUT', 0.12, 0.0, 1.0)
    _socket(group, 'Angle', 'NodeSocketFloat', 'OUTPUT')
    _socket(group, 'Axis', 'NodeSocketVector', 'OUTPUT')
    _socket(group, 'Offset', 'NodeSocketVector', 'OUTPUT')
    _socket(group, 'Brightness', 'NodeSocketFloat', 'OUTPUT')
    _socket(group, 'Piece', 'NodeSocketFloat', 'OUTPUT')
    nodes, links = group.nodes, group.links
    g_in, g_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')

    def number(kind):
        node = nodes.new('ShaderNodeAttribute')
        node.attribute_type = kind
        node.attribute_name = 'pp_piece'
        return node.outputs['Fac']

    piece = math(nodes, links, 'MAXIMUM', number('GEOMETRY'), number('INSTANCER'))
    present = math(nodes, links, 'GREATER_THAN', piece, 0.0)

    def random(offset):
        node = nodes.new('ShaderNodeTexWhiteNoise')
        node.noise_dimensions = '1D'
        links.new(math(nodes, links, 'ADD', piece, offset), node.inputs['W'])
        return node

    first, second = random(0.0), random(7.31)
    angle = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', first.outputs['Value'], 6.283185307), g_in.outputs['Turn'])
    links.new(math(nodes, links, 'MULTIPLY', angle, present), g_out.inputs['Angle'])
    offset = nodes.new('ShaderNodeVectorMath')
    offset.operation = 'SCALE'
    links.new(first.outputs['Color'], offset.inputs[0])
    links.new(present, offset.inputs['Scale'])
    links.new(offset.outputs[0], g_out.inputs['Offset'])
    swing = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY_ADD', second.outputs['Value'], 2.0, -1.0), g_in.outputs['Shade'])
    links.new(math(nodes, links, 'MULTIPLY_ADD', swing, present, 1.0), g_out.inputs['Brightness'])
    links.new(piece, g_out.inputs['Piece'])
    # the axis the face looks along most (object space): the picture turns about it, so it turns within the face
    facing = nodes.new('ShaderNodeTexCoord')
    absolute = nodes.new('ShaderNodeVectorMath')
    absolute.operation = 'ABSOLUTE'
    links.new(facing.outputs['Normal'], absolute.inputs[0])
    parts = nodes.new('ShaderNodeSeparateXYZ')
    links.new(absolute.outputs[0], parts.inputs['Vector'])
    ax, ay, az = parts.outputs['X'], parts.outputs['Y'], parts.outputs['Z']
    on_x = math(nodes, links, 'MULTIPLY', math(nodes, links, 'GREATER_THAN', ax, ay), math(nodes, links, 'GREATER_THAN', ax, az))
    on_y = math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', 1.0, on_x), math(nodes, links, 'GREATER_THAN', ay, az))
    on_z = math(nodes, links, 'SUBTRACT', math(nodes, links, 'SUBTRACT', 1.0, on_x), on_y)
    axis = nodes.new('ShaderNodeCombineXYZ')
    for socket, value in zip(axis.inputs, (on_x, on_y, on_z)):
        links.new(value, socket)
    links.new(axis.outputs['Vector'], g_out.inputs['Axis'])
    return group


# sets whose picture has a direction (grain, courses, corrugations, a weave): their pieces are shifted, never turned
DIRECTED = {'bark_willow_02', 'brick_wall_02', 'brick_wall_10', 'cobblestone_floor_01', 'damaged_plaster', 'dark_brick_wall',
            'distressed_painted_planks', 'hessian_380', 'old_planks_02', 'old_stone_wall_02', 'palm_tree_bark', 'rough_linen',
            'rough_wood', 'rusty_corrugated_iron', 'sandstone_blocks_05', 'wood_planks_grey', 'worn_corrugated_iron'}


def walkway_boards(entry, box_group, weather):
    """MADE • walkway boards: the shelf's rough sawn wood (rough_wood) laid along each board by the mesh's UV map
    'metres' (one unit is one metre; the grain runs along V), with the numbers the walkway tool writes on each board:
    'board_tone' (0..1, its shade), 'across' (-1..1 from one end of the board to the other, so the middle is where boots
    tread), 'wear' (0..1, how polished and pale that middle is), 'wet' (0..1, standing water films on the wood) and 'mud'
    (0..1, mud trodden onto it). A mesh without them reads as plain rough boards."""
    set_id = 'rough_wood'
    material = fresh_material('MADE • walkway boards')
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'metres'
    size_x, size_y = entry['size_m']
    sized = nodes.new('ShaderNodeVectorMath')
    sized.operation = 'DIVIDE'
    links.new(uv.outputs['UV'], sized.inputs[0])
    sized.inputs[1].default_value = (size_x, size_y, 1.0)
    pictures = {}
    for role, colour_space in (('diff', 'sRGB'), ('rough', 'Non-Color'), ('disp', 'Non-Color')):
        image = bpy.data.images.load(os.path.join(SHELF, set_id, entry['maps'][role]), check_existing=True)
        image.colorspace_settings.name = colour_space
        node = nodes.new('ShaderNodeTexImage')
        node.image = image
        links.new(sized.outputs[0], node.inputs['Vector'])
        pictures[role] = node

    def number(name):
        node = nodes.new('ShaderNodeAttribute')
        node.attribute_type = 'GEOMETRY'
        node.attribute_name = name
        return node.outputs['Fac']

    dials = nodes.new('ShaderNodeGroup')
    dials.node_tree = weather
    dials.name = dials.label = 'Weather'
    mean, colour = linear_mean(os.path.join(SHELF, set_id, entry['maps']['diff']))
    darken = max(0.3, min(1.0, (0.08 / max(mean, 1e-4)) ** 0.7))
    dials.inputs['Darken'].default_value = round(darken, 3)
    dials.inputs['Grime'].default_value = 0.55
    dials.inputs['Bump'].default_value = 0.45
    links.new(pictures['rough'].outputs['Color'], dials.inputs['Roughness'])
    links.new(pictures['disp'].outputs['Color'], dials.inputs['Height'])
    # each board its own shade
    tone = math(nodes, links, 'MULTIPLY_ADD', number('board_tone'), 0.55, 0.72)
    shaded = nodes.new('ShaderNodeVectorMath')
    shaded.operation = 'SCALE'
    links.new(pictures['diff'].outputs['Color'], shaded.inputs[0])
    links.new(tone, shaded.inputs['Scale'])
    links.new(shaded.outputs[0], dials.inputs['Color'])
    colour_out, rough_out = dials.outputs['Base Color'], dials.outputs['Roughness']
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    # boots polish the middle of each board: paler and smoother, broken up
    middle = map_range(nodes, links, math(nodes, links, 'ABSOLUTE', number('across')), 0.1, 0.8, 1.0, 0.0)
    middle = math(nodes, links, 'POWER', middle, 1.2)
    scuffs = map_range(nodes, links, noise(nodes, links, position, 7.0, detail=5.0, roughness=0.6), 0.28, 0.62)
    polish = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', middle, scuffs), number('wear'), clamp=True)
    colour_out = mix(nodes, links, polish, colour_out, (0.21, 0.178, 0.145))
    rough_out = math(nodes, links, 'MULTIPLY_ADD', polish, -0.35, rough_out)
    # standing water films: darker, glossy patches
    films = map_range(nodes, links, noise(nodes, links, position, 2.4, detail=3.0), 0.44, 0.58)
    wet = math(nodes, links, 'MULTIPLY', films, number('wet'), clamp=True)
    colour_out = mix(nodes, links, math(nodes, links, 'MULTIPLY', wet, 0.45), colour_out, (0.0, 0.0, 0.0))
    rough_out = math(nodes, links, 'MULTIPLY', rough_out, math(nodes, links, 'MULTIPLY_ADD', wet, -0.85, 1.0))
    # mud trodden on: patchy, dark, wet-glossy
    smears = map_range(nodes, links, noise(nodes, links, position, 5.0, detail=6.0, roughness=0.65), 0.35, 0.6)
    mud = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', smears, 1.6), number('mud'), clamp=True)
    colour_out = mix(nodes, links, mud, colour_out, (0.030, 0.023, 0.016))
    rough_out = math(nodes, links, 'MULTIPLY_ADD', mud, math(nodes, links, 'SUBTRACT', 0.42, rough_out), rough_out)
    links.new(colour_out, principled.inputs['Base Color'])
    links.new(rough_out, principled.inputs['Roughness'])
    links.new(dials.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (*[c * darken for c in colour], 1.0)
    material['store_what'] = ("the walkway tool's boards: rough sawn wood along each board's UV map 'metres', each board its own "
                              "shade, the middle polished pale by boots, wet films, trodden mud (numbers the walkway tool writes)")
    material['store_size_m'] = entry['size_m']
    material['store_source'] = entry.get('source', '')
    return material


def army_canvas():
    """MADE • army canvas: the shelf's rough linen weave (it was photographed dyed blue) as undyed buff canvas: its weave,
    relief and dials kept, its colour taken out and a buff laid in, the brightness unchanged."""
    material = bpy.data.materials['SURFACE • rough_linen'].copy()
    material.name = 'MADE • army canvas'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    weather = nodes['Weather']
    picture = weather.inputs['Color'].links[0].from_socket
    grey = nodes.new('ShaderNodeRGBToBW')
    links.new(picture, grey.inputs['Color'])
    buff = nodes.new('ShaderNodeMix')
    buff.data_type = 'RGBA'
    buff.blend_type = 'MULTIPLY'
    buff.inputs[0].default_value = 1.0
    links.new(grey.outputs['Val'], buff.inputs[6])
    buff.inputs[7].default_value = (1.17, 0.99, 0.61, 1.0)      # a buff whose own brightness is 1: the weave's brightness kept
    links.new(buff.outputs[2], weather.inputs['Color'])
    material['store_what'] = 'undyed army canvas, buff (bell tents, tarpaulins, covers): the shelf\'s linen weave without its blue dye'
    material.diffuse_color = (0.30, 0.26, 0.17, 1.0)
    return material


def wet_mud(box_group, weather):
    """MADE • wet mud: the shelf's dark forest mud, soaked: darker and glossy in its hollows, stronger relief."""
    source = bpy.data.materials['SURFACE • mud_forest']
    material = source.copy()
    material.name = 'MADE • wet mud'
    dials = material.node_tree.nodes['Weather']
    dials.inputs['Wet'].default_value = 0.8
    dials.inputs['Bump'].default_value = 0.55
    dials.inputs['Grime'].default_value = 0.5
    material['store_what'] = 'wet mud: the forest mud soaked, dark and glossy (ground, ruts, mud lumps)'
    return material


def linear_mean(path):
    from PIL import Image
    import numpy
    picture = numpy.asarray(Image.open(path).convert('RGB').resize((128, 128)), dtype=numpy.float32) / 255.0
    linear = numpy.where(picture <= 0.04045, picture / 12.92, ((picture + 0.055) / 1.055) ** 2.4)
    return float((linear @ numpy.array([0.2126, 0.7152, 0.0722])).mean()), [float(v) for v in linear.reshape(-1, 3).mean(0)]


def surface_material(set_id, entry, box_group, weather, weather_normal=None, normal_group=None, pieces=None):
    """SURFACE • <set>: the shelf set's colour, roughness and height pictures laid from three sides (BOX) at the
    photograph's real size, with the weather dials; a set with a normal picture also has it, read the same way and turned
    into world space (normal_group), with the height picture's relief laid lightly over it."""
    material = fresh_material('SURFACE • ' + set_id)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    size_x, size_y = entry['size_m']
    coordinates = nodes.new('ShaderNodeGroup')
    coordinates.node_tree = box_group
    coordinates.name = coordinates.label = 'Picture size'
    coordinates.inputs['Size'].default_value = (size_x, size_x, size_y)
    coordinates.location = (-900, 0)
    projected = coordinates.outputs['Vector']
    variety = None
    if pieces is not None:
        # each piece (pp_piece) its own part of the picture: turned within its face and shifted, a little lighter or darker
        variety = nodes.new('ShaderNodeGroup')
        variety.node_tree = pieces
        variety.name = variety.label = 'Pieces'
        variety.location = (-1150, -300)
        variety.inputs['Turn'].default_value = 0.0 if set_id in DIRECTED else 1.0
        turned = nodes.new('ShaderNodeVectorRotate')
        turned.rotation_type = 'AXIS_ANGLE'
        turned.location = (-760, -200)
        links.new(projected, turned.inputs['Vector'])
        links.new(variety.outputs['Axis'], turned.inputs['Axis'])
        links.new(variety.outputs['Angle'], turned.inputs['Angle'])
        shifted = nodes.new('ShaderNodeVectorMath')
        shifted.operation = 'ADD'
        shifted.location = (-700, -350)
        links.new(turned.outputs['Vector'], shifted.inputs[0])
        links.new(variety.outputs['Offset'], shifted.inputs[1])
        projected = shifted.outputs['Vector']
    pictures = {}
    roles = [('diff', 'sRGB'), ('rough', 'Non-Color'), ('disp', 'Non-Color')]
    if normal_group is not None and 'normal' in entry['maps']:
        roles.append(('normal', 'Non-Color'))
    for index, (role, colour_space) in enumerate(roles):
        if role not in entry['maps']:
            continue
        path = os.path.join(SHELF, set_id, entry['maps'][role])
        image = bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = colour_space
        node = nodes.new('ShaderNodeTexImage')
        node.image = image
        node.projection = 'BOX'
        node.projection_blend = 0.2
        node.location = (-600, 300 - 280 * index)
        links.new(projected, node.inputs['Vector'])
        pictures[role] = node
    dials = nodes.new('ShaderNodeGroup')
    dials.node_tree = weather_normal if 'normal' in pictures else weather
    dials.name = dials.label = 'Weather'
    dials.location = (-200, 0)
    if variety is not None:
        shade = nodes.new('ShaderNodeVectorMath')
        shade.operation = 'SCALE'
        shade.location = (-350, 250)
        links.new(pictures['diff'].outputs['Color'], shade.inputs[0])
        links.new(variety.outputs['Brightness'], shade.inputs['Scale'])
        links.new(shade.outputs[0], dials.inputs['Color'])
    else:
        links.new(pictures['diff'].outputs['Color'], dials.inputs['Color'])
    if 'normal' in pictures:
        turned = nodes.new('ShaderNodeGroup')
        turned.node_tree = normal_group
        turned.name = turned.label = 'Normal picture'
        turned.location = (-400, -600)
        links.new(pictures['normal'].outputs['Color'], turned.inputs['Color'])
        if variety is not None:
            links.new(variety.outputs['Axis'], turned.inputs['Axis'])
            links.new(variety.outputs['Angle'], turned.inputs['Angle'])
        links.new(turned.outputs['Normal'], dials.inputs['Normal'])
        dials.inputs['Bump'].default_value = 0.15      # the normal picture carries the fine relief; the height adds a little
    if 'rough' in pictures:
        links.new(pictures['rough'].outputs['Color'], dials.inputs['Roughness'])
    if 'disp' in pictures:
        links.new(pictures['disp'].outputs['Color'], dials.inputs['Height'])
    mean, colour = linear_mean(os.path.join(SHELF, set_id, entry['maps']['diff']))
    darken = max(0.3, min(1.0, (0.08 / max(mean, 1e-4)) ** 0.7))
    dials.inputs['Darken'].default_value = round(darken, 3)
    links.new(dials.outputs['Base Color'], principled.inputs['Base Color'])
    links.new(dials.outputs['Roughness'], principled.inputs['Roughness'])
    links.new(dials.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (*[c * darken for c in colour], 1.0)
    material['store_what'] = entry.get('what', entry.get('name', set_id))
    material['store_size_m'] = entry['size_m']
    material['store_source'] = entry.get('source', '')
    return material


ATLAS = os.path.join(MATERIALS, 'atlas')


def atlas_material(atlas_path, manifest, weather_normal, pieces):
    """BRICK • <set> or ASHLAR • <set>: a wall photograph whose whole bricks or blocks were found (atlas/<set>.json,
    made by find_atlas.py). The wall tool gives each unit's front face one of those rectangles through the UV map
    'pp_atlas' (and its sides thin strips at the rectangle's edges); this material reads all four pictures through
    that UV map (the normal picture through the UV map's own directions), makes each piece a little lighter or
    darker by its 'pp_piece', and has the same Weather dials as a SURFACE."""
    atlas = json.load(open(atlas_path))
    set_id = atlas['set']
    entry = manifest[set_id]
    material = fresh_material(atlas['material'])
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'pp_atlas'
    uv.location = (-900, 0)
    pictures = {}
    for index, (role, colour_space) in enumerate((('diff', 'sRGB'), ('rough', 'Non-Color'), ('disp', 'Non-Color'), ('normal', 'Non-Color'))):
        image = bpy.data.images.load(os.path.join(SHELF, set_id, entry['maps'][role]), check_existing=True)
        image.colorspace_settings.name = colour_space
        node = nodes.new('ShaderNodeTexImage')
        node.image = image
        node.extension = 'EXTEND'
        node.location = (-600, 300 - 280 * index)
        links.new(uv.outputs['UV'], node.inputs['Vector'])
        pictures[role] = node
    variety = nodes.new('ShaderNodeGroup')
    variety.node_tree = pieces
    variety.name = variety.label = 'Pieces'
    variety.location = (-900, 400)
    variety.inputs['Turn'].default_value = 0.0
    variety.inputs['Shade'].default_value = 0.15
    shade = nodes.new('ShaderNodeVectorMath')
    shade.operation = 'SCALE'
    links.new(pictures['diff'].outputs['Color'], shade.inputs[0])
    links.new(variety.outputs['Brightness'], shade.inputs['Scale'])
    relief = nodes.new('ShaderNodeNormalMap')
    relief.space = 'TANGENT'
    relief.uv_map = 'pp_atlas'
    relief.name = relief.label = 'Normal picture'
    links.new(pictures['normal'].outputs['Color'], relief.inputs['Color'])
    dials = nodes.new('ShaderNodeGroup')
    dials.node_tree = weather_normal
    dials.name = dials.label = 'Weather'
    dials.location = (-200, 0)
    links.new(shade.outputs[0], dials.inputs['Color'])
    links.new(pictures['rough'].outputs['Color'], dials.inputs['Roughness'])
    links.new(pictures['disp'].outputs['Color'], dials.inputs['Height'])
    links.new(relief.outputs['Normal'], dials.inputs['Normal'])
    dials.inputs['Bump'].default_value = 0.15
    mean, colour = linear_mean(os.path.join(SHELF, set_id, entry['maps']['diff']))
    darken = max(0.3, min(1.0, (0.08 / max(mean, 1e-4)) ** 0.7))
    dials.inputs['Darken'].default_value = round(darken, 3)
    links.new(dials.outputs['Base Color'], principled.inputs['Base Color'])
    links.new(dials.outputs['Roughness'], principled.inputs['Roughness'])
    links.new(dials.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (*[c * darken for c in colour], 1.0)
    kind = 'bricks' if atlas['material'].startswith('BRICK') else 'stone blocks'
    material['store_what'] = ('%s for the wall tool, each its own whole %s from the photograph %s (%d found, atlas/%s.json); '
                              'needs the UV map pp_atlas the wall tool writes' % (kind, kind[:-1], set_id, len(atlas['units']), set_id))
    material['store_size_m'] = entry['size_m']
    material['store_source'] = entry.get('source', '')
    material['store_atlas'] = 'atlas/%s.json' % set_id
    return material


def main():
    bpy.ops.wm.open_mainfile(filepath=TARGET)
    for material in list(bpy.data.materials):
        if material.name.startswith(('SURFACE •', 'MADE •', 'BRICK •', 'ASHLAR •')):
            bpy.data.materials.remove(material)
    for group in list(bpy.data.node_groups):
        if group.name.startswith('STORE •'):
            bpy.data.node_groups.remove(group)
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    for name, what in STREET.items():
        material = bpy.data.materials.get(name)
        if material is not None:
            material['store_what'] = what
            material.use_fake_user = True
    box_group, weather = box_coordinates_group(), weather_group()
    weather_normal, normal_group = weather_group(with_normal=True), box_normal_group()
    pieces = pieces_group()
    manifest = json.load(open(os.path.join(SHELF, 'manifest.json')))
    for set_id, entry in sorted(manifest.items()):
        surface_material(set_id, entry, box_group, weather, weather_normal, normal_group, pieces).use_fake_user = True
    if os.path.isdir(ATLAS):
        for name in sorted(os.listdir(ATLAS)):
            if name.endswith('.json'):
                atlas_material(os.path.join(ATLAS, name), manifest, weather_normal, pieces).use_fake_user = True
    for material in made.build_all().values():
        material.use_fake_user = True
    walkway_boards(manifest['rough_wood'], box_group, weather).use_fake_user = True
    wet_mud(box_group, weather).use_fake_user = True
    army_canvas().use_fake_user = True
    ground_materials.build_all(SHELF, manifest, box_group)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile(filepath=TARGET)
    counts = {'street': sum(1 for m in bpy.data.materials if not m.name.startswith(('SURFACE •', 'MADE •', 'BRICK •', 'ASHLAR •'))),
              'atlas': sum(1 for m in bpy.data.materials if m.name.startswith(('BRICK •', 'ASHLAR •'))),
              'surface': sum(1 for m in bpy.data.materials if m.name.startswith('SURFACE •')),
              'made': sum(1 for m in bpy.data.materials if m.name.startswith('MADE •'))}
    print('saved', TARGET, counts)


if __name__ == '__main__':
    main()
