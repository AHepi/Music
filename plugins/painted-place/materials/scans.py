"""
What this file does:
Gives the plugin's code-made surfaces real photographed texture: weathered timber, deck planks, bark, damp sand and
driftwood, from free Poly Haven scans (CC0, public domain) kept in materials/textures/. Each scan brings three
pictures: its colour, how shiny it is (roughness), and its relief (height, used as bumps).

Builders' shapes have no texture layout (no UVs), so every picture is laid on from three sides and blended by which
way the surface faces ("box" projection, in the object's own space so the grain turns with a turned house). Wood
grain runs along the object's longest side (along a board, up a post, across a deck), each board samples its own
patch of the scan so no two neighbours repeat, and big ground is sampled at two sizes mixed by a slow noise so the
tile never shows. Every colour is darkened and dulled into the look's range before the plugin's own weathering
(paint peeling, rain streaks, a shade per board) goes on top.

    import scans
    scans.available()                       # are the pictures here?
    scans.boards()                          # weathered boards with the paint layers (lay_timber uses it)
    scans.planks() scans.bark(palm=True) scans.sand() scans.driftwood()
    scans.mark_object(obj)                  # writes the per-object numbers these materials read (scale, grain)

If the textures folder is missing, available() is False and the plugin falls back to its code-made materials.
"""

import json
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
TEXTURES = os.path.join(HERE, 'textures')
PREFIX = 'SCAN • '


def manifest():
    path = os.path.join(TEXTURES, 'manifest.json')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


ENABLED = os.environ.get('PAINTED_PLACE_NO_SCANS', '') == ''      # switched off by --no-scans or that variable


def available(name=None):
    if not ENABLED:
        return False
    sets = manifest()
    names = [name] if name else list(sets)
    if not names:
        return False
    for set_name in names:
        entry = sets.get(set_name)
        if entry is None:
            return False
        for file_name in entry['maps'].values():
            if not os.path.exists(os.path.join(TEXTURES, set_name, file_name)):
                return False
    return True


def _image(set_name, role):
    entry = manifest()[set_name]
    path = os.path.join(TEXTURES, set_name, entry['maps'][role])
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB' if role == 'diff' else 'Non-Color'
    return image


def tile_size(set_name):
    return manifest()[set_name]['size_m'][0]


def mark_object(obj, grain_axis=None):
    """The numbers the scanned materials read from each object: its scale (so a scaled object gets the scan at its
    real size) and the axis its grain runs along (0 x, 1 y, 2 z of its own: by default its longest side)."""
    if obj.type != 'MESH':
        return
    obj['pp_scale'] = tuple(abs(v) if abs(v) > 1e-6 else 1.0 for v in obj.scale)
    if grain_axis is None:
        corners = obj.bound_box
        extent = [(max(c[k] for c in corners) - min(c[k] for c in corners)) * obj['pp_scale'][k] for k in range(3)]
        grain_axis = max(range(3), key=lambda k: extent[k])
    obj['pp_grain'] = float(grain_axis)


# ----------------------------------------------------------------------------------------------- node helpers

def _math(nodes, links, operation, a, b=None, c=None):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for socket, value in zip(node.inputs, (a, b, c)):
        if value is None:
            continue
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value
    return node.outputs[0]


def _vmath(nodes, links, operation, a, b=None, scale=None):
    node = nodes.new('ShaderNodeVectorMath')
    node.operation = operation
    for socket, value in ((node.inputs[0], a), (node.inputs[1], b)):
        if value is None:
            continue
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value
    if scale is not None:
        if isinstance(scale, bpy.types.NodeSocket):
            links.new(scale, node.inputs['Scale'])
        else:
            node.inputs['Scale'].default_value = scale
    return node.outputs['Value'] if operation in ('DOT_PRODUCT', 'DISTANCE', 'LENGTH') else node.outputs['Vector']


def _combine(nodes, links, x, y):
    node = nodes.new('ShaderNodeCombineXYZ')
    links.new(x, node.inputs['X'])
    links.new(y, node.inputs['Y'])
    return node.outputs['Vector']


def _mix_vector(nodes, links, factor, a, b):
    node = nodes.new('ShaderNodeMix')
    node.data_type = 'VECTOR'
    links.new(factor, node.inputs[0])
    links.new(a, node.inputs[4])
    links.new(b, node.inputs[5])
    return node.outputs[1]


def _object_number(nodes, name):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_type = 'OBJECT'
    node.attribute_name = name
    return node


class BoxLayout:
    """Where each picture lands: three projections in the object's own (scaled) space, their weights from the way
    the surface faces, the grain along the object's chosen axis, and a patch offset per board."""

    def __init__(self, nodes, links, along, across, sharpness=6.0, by_location=False):
        self.nodes, self.links = nodes, links
        coordinates = nodes.new('ShaderNodeTexCoord')
        scale = _object_number(nodes, 'pp_scale').outputs['Vector']
        # an object without the number (made by hand) reads (0, 0, 0): use 1 instead
        missing = _vmath(nodes, links, 'SUBTRACT', (1.0, 1.0, 1.0),
                         _vmath(nodes, links, 'MINIMUM', (1.0, 1.0, 1.0), _vmath(nodes, links, 'CEIL', _vmath(nodes, links, 'ABSOLUTE', scale))))
        scale = _vmath(nodes, links, 'ADD', scale, missing)
        position = _vmath(nodes, links, 'MULTIPLY', coordinates.outputs['Object'], scale)
        separate = nodes.new('ShaderNodeSeparateXYZ')
        links.new(position, separate.inputs['Vector'])
        x, y, z = separate.outputs['X'], separate.outputs['Y'], separate.outputs['Z']
        grain = _object_number(nodes, 'pp_grain').outputs['Fac']
        grain_is_x = _math(nodes, links, 'COMPARE', grain, 0.0, 0.5)
        grain_is_y = _math(nodes, links, 'COMPARE', grain, 1.0, 0.5)
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'GEOMETRY'
        tone.attribute_name = 'board_tone'
        offset = _vmath(nodes, links, 'MULTIPLY', _combine(nodes, links, tone.outputs['Fac'], tone.outputs['Fac']), (7.31, 3.17, 0.0))
        if by_location:     # laid stones are copies of a few pieces: each copy samples the scan where it lies
            where = nodes.new('ShaderNodeObjectInfo')
            offset = _vmath(nodes, links, 'ADD', offset, _vmath(nodes, links, 'MULTIPLY', where.outputs['Location'], (0.61, 0.43, 0.0)))
        size = (1.0 / across, 1.0 / along, 1.0)
        # the picture's grain runs up it (its second coordinate), so that coordinate follows the object's grain axis
        self.planes = []
        for plain, turned, turn in (((y, z), (z, y), grain_is_y),     # seen along x
                                    ((x, z), (z, x), grain_is_x),     # seen along y
                                    ((x, y), (y, x), grain_is_x)):    # seen from above or below
            vector = _mix_vector(nodes, links, turn, _combine(nodes, links, *plain), _combine(nodes, links, *turned))
            vector = _vmath(nodes, links, 'MULTIPLY', vector, size)
            self.planes.append(_vmath(nodes, links, 'ADD', vector, offset))
        normal = _vmath(nodes, links, 'ABSOLUTE', coordinates.outputs['Normal'])
        separate_n = nodes.new('ShaderNodeSeparateXYZ')
        links.new(normal, separate_n.inputs['Vector'])
        powered = [_math(nodes, links, 'POWER', separate_n.outputs[k], sharpness) for k in ('X', 'Y', 'Z')]
        total = _math(nodes, links, 'ADD', _math(nodes, links, 'ADD', powered[0], powered[1]), powered[2])
        self.weights = [_math(nodes, links, 'DIVIDE', p, _math(nodes, links, 'MAXIMUM', total, 1e-5)) for p in powered]

    def sample(self, image, colour=True):
        """The picture laid on from three sides and blended: a colour (vector) socket, or a value socket."""
        nodes, links = self.nodes, self.links
        result = None
        for plane, weight in zip(self.planes, self.weights):
            texture = nodes.new('ShaderNodeTexImage')
            texture.image = image
            texture.interpolation = 'Linear' if colour else 'Cubic'
            links.new(plane, texture.inputs['Vector'])
            if colour:
                part = _vmath(nodes, links, 'SCALE', texture.outputs['Color'], scale=weight)
                result = part if result is None else _vmath(nodes, links, 'ADD', result, part)
            else:
                part = _math(nodes, links, 'MULTIPLY', texture.outputs['Color'], weight)
                result = part if result is None else _math(nodes, links, 'ADD', result, part)
        return result


def _look(nodes, links, colour, value, saturation):
    """Darken and dull a scanned colour into the look's range."""
    node = nodes.new('ShaderNodeHueSaturation')
    node.inputs['Saturation'].default_value = saturation
    node.inputs['Value'].default_value = value
    links.new(colour, node.inputs['Color'])
    return node.outputs['Color']


def _bump(nodes, links, height, distance, normal=None):
    node = nodes.new('ShaderNodeBump')
    node.inputs['Distance'].default_value = distance
    node.inputs['Strength'].default_value = 1.0
    links.new(height, node.inputs['Height'])
    if normal is not None:
        links.new(normal, node.inputs['Normal'])
    return node.outputs['Normal']


def _new_material(name):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material, False
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    return material, True


# ----------------------------------------------------------------------------------------------- the materials

def boards():
    """Weathered boards from the rough-wood scan: each board its own patch and shade, grain along the board, rain
    streaks running down, and one faded paint per building left in cracked, peeling patches."""
    if not available('rough_wood'):
        return None
    material, new = _new_material(PREFIX + 'weathered boards, peeling paint')
    if not new:
        return material
    import lay_timber
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    layout = BoxLayout(nodes, links, along=tile_size('rough_wood') * 2.2, across=tile_size('rough_wood') * 1.1)
    wood = _look(nodes, links, layout.sample(_image('rough_wood', 'diff')), 0.62, 0.7)
    tone = nodes.new('ShaderNodeAttribute')
    tone.attribute_type = 'GEOMETRY'
    tone.attribute_name = 'board_tone'
    shade = nodes.new('ShaderNodeMapRange')         # a shade per board: from near black (rotten) to pale (a newer board put in)
    shade.inputs['To Min'].default_value, shade.inputs['To Max'].default_value = 0.45, 1.55
    links.new(tone.outputs['Fac'], shade.inputs['Value'])
    bare = lay_timber._mix(nodes, links, 1.0, wood, _combine_gray(nodes, links, shade.outputs['Result']), 'MULTIPLY')
    material, nodes, links = _paint_and_streaks(material, nodes, links, principled, bare, layout)
    rough = layout.sample(_image('rough_wood', 'rough'), colour=False)
    links.new(_math(nodes, links, 'MULTIPLY', rough, 0.92), principled.inputs['Roughness'])
    height = layout.sample(_image('rough_wood', 'disp'), colour=False)
    links.new(_bump(nodes, links, height, 0.004), principled.inputs['Normal'])
    material.diffuse_color = (0.12, 0.11, 0.10, 1)
    return material


def _combine_gray(nodes, links, value):
    node = nodes.new('ShaderNodeCombineXYZ')
    for axis in ('X', 'Y', 'Z'):
        links.new(value, node.inputs[axis])
    return node.outputs['Vector']


def _paint_and_streaks(material, nodes, links, principled, bare, layout):
    """The plugin's own weathering on top of a scanned wood: the old paint held in cracked patches (one faded paint
    per building), more of it gone low down, and rain streaks running down."""
    import lay_timber
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    info = nodes.new('ShaderNodeObjectInfo')
    paint = lay_timber._ramp(nodes, [(0.0, (0.36, 0.36, 0.33)), (0.2, (0.18, 0.25, 0.25)), (0.4, (0.11, 0.155, 0.23)),
                                     (0.6, (0.12, 0.18, 0.12)), (0.8, (0.30, 0.27, 0.18)), (0.9, (0.07, 0.18, 0.18))], interpolation='CONSTANT')
    where = nodes.new('ShaderNodeTexNoise')
    where.inputs['Scale'].default_value = 0.045
    where.inputs['Detail'].default_value = 0.0
    links.new(info.outputs['Location'], where.inputs['Vector'])
    spread = nodes.new('ShaderNodeMapRange')
    spread.inputs['From Min'].default_value, spread.inputs['From Max'].default_value = 0.32, 0.68
    links.new(where.outputs['Fac'], spread.inputs['Value'])
    links.new(spread.outputs['Result'], paint.inputs[0])
    peel = lay_timber._noise(nodes, links, position, 2.7, detail=9.0, roughness=0.62, distortion=0.35)
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position, separate.inputs['Vector'])
    low = nodes.new('ShaderNodeMapRange')
    low.inputs['From Min'].default_value, low.inputs['From Max'].default_value = 0.0, 1.2
    low.inputs['To Min'].default_value, low.inputs['To Max'].default_value = 0.12, 0.0
    links.new(separate.outputs['Z'], low.inputs['Value'])
    # less paint than on code-made wood: the scanned grain is what should show, with paint left in patches
    threshold = _math(nodes, links, 'ADD', _math(nodes, links, 'MULTIPLY_ADD', info.outputs['Random'], 0.12, 0.50), low.outputs['Result'])
    held = nodes.new('ShaderNodeMapRange')
    links.new(peel, held.inputs['Value'])
    links.new(_math(nodes, links, 'SUBTRACT', threshold, 0.015), held.inputs['From Min'])
    links.new(_math(nodes, links, 'ADD', threshold, 0.015), held.inputs['From Max'])
    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = 34.0
    links.new(position, voronoi.inputs['Vector'])
    crack = nodes.new('ShaderNodeMapRange')
    crack.inputs['From Min'].default_value, crack.inputs['From Max'].default_value = 0.0, 0.05
    crack.inputs['To Min'].default_value, crack.inputs['To Max'].default_value = 0.35, 1.0
    links.new(voronoi.outputs['Distance'], crack.inputs['Value'])
    cracked = lay_timber._mix(nodes, links, 1.0, paint.outputs['Color'], crack.outputs['Result'], 'MULTIPLY')
    colour = lay_timber._mix(nodes, links, held.outputs['Result'], bare, cracked)
    streak = lay_timber._noise(nodes, links, lay_timber._stretched(nodes, links, position, (1.7, 1.7, 0.085)), 1.0, detail=5.0, roughness=0.6)
    streak_ramp = lay_timber._ramp(nodes, [(0.32, (0.55, 0.55, 0.55)), (0.62, (1.0, 1.0, 1.0))])
    links.new(streak, streak_ramp.inputs[0])
    colour = lay_timber._mix(nodes, links, 1.0, colour, streak_ramp.outputs['Color'], 'MULTIPLY')
    links.new(colour, principled.inputs['Base Color'])
    return material, nodes, links


def planks():
    """A flat timber deck or floor laid as one slab: grey weathered planks along its longer side."""
    if not available('wood_planks_grey'):
        return None
    material, new = _new_material(PREFIX + 'weathered deck planks')
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    size = tile_size('wood_planks_grey')
    layout = BoxLayout(nodes, links, along=size, across=size)
    links.new(_look(nodes, links, layout.sample(_image('wood_planks_grey', 'diff')), 0.9, 0.75), principled.inputs['Base Color'])
    links.new(_math(nodes, links, 'MULTIPLY', layout.sample(_image('wood_planks_grey', 'rough'), colour=False), 0.85), principled.inputs['Roughness'])
    links.new(_bump(nodes, links, layout.sample(_image('wood_planks_grey', 'disp'), colour=False), 0.006), principled.inputs['Normal'])
    material.diffuse_color = (0.06, 0.06, 0.055, 1)
    return material


def bark(palm=False):
    """Wet bark from a scan: a palm's ringed trunk, or furrowed bark for any other tree; rings and furrows run with
    the trunk."""
    set_name = 'palm_tree_bark' if palm else 'bark_willow_02'
    if not available(set_name):
        return None
    material, new = _new_material(PREFIX + ('wet palm bark' if palm else 'wet furrowed bark'))
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    size = tile_size(set_name)
    layout = BoxLayout(nodes, links, along=size, across=size * (0.6 if palm else 1.0), sharpness=3.0)
    links.new(_look(nodes, links, layout.sample(_image(set_name, 'diff')), 0.42 if palm else 0.6, 0.65), principled.inputs['Base Color'])
    links.new(_math(nodes, links, 'MULTIPLY', layout.sample(_image(set_name, 'rough'), colour=False), 0.8), principled.inputs['Roughness'])
    links.new(_bump(nodes, links, layout.sample(_image(set_name, 'disp'), colour=False), 0.015), principled.inputs['Normal'])
    material.diffuse_color = (0.07, 0.06, 0.05, 1)
    return material


def driftwood():
    """Bleached, salt-grey driftwood: the rough-wood scan, paler and greyer, grain along the log."""
    if not available('rough_wood'):
        return None
    material, new = _new_material(PREFIX + 'bleached driftwood')
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    size = tile_size('rough_wood')
    layout = BoxLayout(nodes, links, along=size * 2.0, across=size)
    links.new(_look(nodes, links, layout.sample(_image('rough_wood', 'diff')), 1.15, 0.25), principled.inputs['Base Color'])
    links.new(layout.sample(_image('rough_wood', 'rough'), colour=False), principled.inputs['Roughness'])
    links.new(_bump(nodes, links, layout.sample(_image('rough_wood', 'disp'), colour=False), 0.006), principled.inputs['Normal'])
    material.diffuse_color = (0.3, 0.29, 0.27, 1)
    return material


def sand(name=PREFIX + 'damp sand'):
    """Damp sand from a scan, laid flat in world space at two sizes mixed by a slow noise (so its tile never shows),
    dark enough that a fire beside it does not turn it to snow."""
    if not available('damp_beach_sand'):
        return None
    material, new = _new_material(name)
    if not new:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    size = tile_size('damp_beach_sand')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position, separate.inputs['Vector'])
    flat = _combine(nodes, links, separate.outputs['X'], separate.outputs['Y'])
    near = _vmath(nodes, links, 'MULTIPLY', flat, (1.0 / size, 1.0 / size, 1.0))
    turned = nodes.new('ShaderNodeVectorRotate')
    turned.rotation_type = 'Z_AXIS'
    turned.inputs['Angle'].default_value = 0.64
    links.new(flat, turned.inputs['Vector'])
    far = _vmath(nodes, links, 'MULTIPLY', turned.outputs['Vector'], (1.0 / (size * 1.7), 1.0 / (size * 1.7), 1.0))
    blend = nodes.new('ShaderNodeTexNoise')
    blend.inputs['Scale'].default_value = 0.12
    blend.inputs['Detail'].default_value = 1.0
    links.new(position, blend.inputs['Vector'])
    mask = nodes.new('ShaderNodeMapRange')
    mask.inputs['From Min'].default_value, mask.inputs['From Max'].default_value = 0.4, 0.6
    links.new(blend.outputs['Fac'], mask.inputs['Value'])

    def two_sizes(role, colour):
        outputs = []
        for vector in (near, far):
            texture = nodes.new('ShaderNodeTexImage')
            texture.image = _image('damp_beach_sand', role)
            links.new(vector, texture.inputs['Vector'])
            outputs.append(texture.outputs['Color'])
        node = nodes.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        links.new(mask.outputs['Result'], node.inputs[0])
        links.new(outputs[0], node.inputs[6])
        links.new(outputs[1], node.inputs[7])
        return node.outputs[2]

    links.new(_look(nodes, links, two_sizes('diff', True), 0.42, 0.6), principled.inputs['Base Color'])
    links.new(_math(nodes, links, 'MULTIPLY', two_sizes('rough', False), 0.95), principled.inputs['Roughness'])
    links.new(_bump(nodes, links, two_sizes('disp', False), 0.02), principled.inputs['Normal'])
    material.diffuse_color = (0.07, 0.065, 0.05, 1)
    return material


# ----------------------------------------------------------------------------------------------- stone grain

STONE_FAMILY = ('Hand-painted sandstone', 'STONE •', 'PAVEMENT •')


def add_stone_grain(material, strength=0.65, relief=0.005):
    """Real stone grain from the sandstone scan, laid over one of the street's stone materials without changing its
    colours or its weathering: the scan's pits, cracks and mottling multiply the colour (its average brightness is
    kept), its relief adds to the bumps, and every block, flag or laid stone samples its own patch. Done once per
    material (marked `pp_stone_grain`)."""
    if material is None or not available('sandstone_cracks') or not material.node_tree or material.get('pp_stone_grain'):
        return False
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled_nodes = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
    if not principled_nodes:
        return False
    size = tile_size('sandstone_cracks')
    layout = BoxLayout(nodes, links, along=size, across=size, sharpness=4.0, by_location=True)
    gray = nodes.new('ShaderNodeRGBToBW')
    links.new(layout.sample(_image('sandstone_cracks', 'diff')), gray.inputs['Color'])
    mean = manifest()['sandstone_cracks'].get('mean_luminance', 0.4)
    # 1 + strength x (grain / its average - 1): brighter and darker than the stone by the scan's own variation
    factor = _math(nodes, links, 'MULTIPLY_ADD', _math(nodes, links, 'SUBTRACT', _math(nodes, links, 'DIVIDE', gray.outputs['Val'], mean), 1.0),
                   strength, 1.0)
    factor = _math(nodes, links, 'MAXIMUM', factor, 0.2)
    height = layout.sample(_image('sandstone_cracks', 'disp'), colour=False)
    for principled in principled_nodes:
        base = principled.inputs['Base Color']
        source = base.links[0].from_socket if base.links else None
        multiply = nodes.new('ShaderNodeMix')
        multiply.data_type = 'RGBA'
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1.0
        if source is not None:
            links.new(source, multiply.inputs[6])
        else:
            multiply.inputs[6].default_value = base.default_value
        links.new(_combine_gray(nodes, links, factor), multiply.inputs[7])
        links.new(multiply.outputs[2], base)
        normal = principled.inputs['Normal']
        previous = normal.links[0].from_socket if normal.links else None
        links.new(_bump(nodes, links, height, relief, previous), normal)
    material['pp_stone_grain'] = True
    return True
