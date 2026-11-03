"""
What this file does: lays real stone grain over a stone material you name: the pits, cracks and mottling of the shelf's
sandstone photographs (brief/surfaces/sandstone_cracks/, a 2 m piece of real stone) multiply the material's colour and
add to its bumps, without changing its average colour: the photograph's brightness is divided by its own average, so
it only makes parts lighter and darker than the stone already was. Every stone samples its own patch of the
photograph (by the number 'stone_patch' on each face, which the lay_stone tool writes, by each object or laid copy's
own random number, and by where each copy lies), so neighbouring blocks never show the same pits. The material's own
colours, weathering and bumps stay; nothing is placed anywhere.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import stone_grain
    stone_grain.add('Hand-painted sandstone • shade 03')            # by store name (brought in if needed)
    stone_grain.add(my_material, strength=0.5, relief=0.01)          # or a material you hold

From the command line:

    python3 stone_grain.py --help
    python3 stone_grain.py --blend IN.blend --material "Hand-painted sandstone • shade 03" --out OUT.blend [--strength 0.65]

Options:
    strength    how strongly the grain lightens and darkens the colour (0 none, 1 the photograph's full range); default 0.65
    relief      how deep the grain's bumps are, metres; default 0.005 (flags under raking light look right at 0.014)

A material gets the grain once (it is marked 'pp_stone_grain'); adding it again does nothing and returns False.
The grain changes every object that uses the material: copy the material first (mat.copy()) to change one thing only.
The photograph is laid from three sides in each object's own space at its real size (2 m), so it turns with a turned
object; an object scaled after it was marked (store.mark / store.use_material) needs store.prepare_for_render.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy  # noqa: E402

import store  # noqa: E402

SHELF = os.path.normpath(os.path.join(HERE, '..', '..', 'surfaces'))
GRAIN_SET = 'sandstone_cracks'
LUMINANCE = numpy.array([0.2126, 0.7152, 0.0722], dtype=numpy.float64)   # what the shader's RGB to BW node weighs

TOOL = {
    'name': 'stone_grain',
    'what': "lays real sandstone grain (pits, cracks, relief) over a stone material's colour and bumps, its average colour kept",
    'call': "stone_grain.add('Hand-painted sandstone • shade 03', strength=0.65, relief=0.005)",
    'options': {
        'material': 'the stone material: a store name or a material you hold',
        'strength': "how strongly the grain lightens and darkens the colour (0 none, 1 the photograph's full range); default 0.65",
        'relief': 'how deep the grain bumps are, metres; default 0.005',
    },
    'materials': ["any stone material (e.g. the 'Hand-painted sandstone • shade NN' set, 'STONE • worn honey-grey architectural dressings', 'PAVEMENT • damp sandstone slabs')"],
    'source': 'plugins/painted-place/materials/scans.py: add_stone_grain, BoxLayout',
    'trap': 'it changes every object using that material: copy the material first to grain one thing only',
}


# ----------------------------------------------------------------------------------------------- the photographs

def _entry():
    with open(os.path.join(SHELF, 'manifest.json'), encoding='utf-8') as handle:
        return json.load(handle)[GRAIN_SET]


def _picture(role):
    """One of the grain photographs, kept as a path to the shelf (not packed, so the file stays small)."""
    entry = _entry()
    path = os.path.join(SHELF, GRAIN_SET, entry['maps'][role])
    if not os.path.exists(path):
        raise FileNotFoundError('the stone grain photograph is not on the shelf: %s' % path)
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB' if role == 'diff' else 'Non-Color'
    return image


def mean_luminance(image):
    """The colour photograph's average brightness as the shader sees it (in linear light), kept on the image."""
    if 'mean_luminance' in image:
        return float(image['mean_luminance'])
    pixels = numpy.empty(image.size[0] * image.size[1] * image.channels, dtype=numpy.float32)
    image.pixels.foreach_get(pixels)
    rgb = pixels.reshape(-1, image.channels)[:, :3].astype(numpy.float64)
    if image.colorspace_settings.name == 'sRGB' and not image.is_float:
        rgb = numpy.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    value = float((rgb @ LUMINANCE).mean())
    image['mean_luminance'] = value
    return value


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


def _vector_math(nodes, links, operation, a, b=None, scale=None):
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


def _combine(nodes, links, x, y, z=None):
    node = nodes.new('ShaderNodeCombineXYZ')
    links.new(x, node.inputs['X'])
    links.new(y, node.inputs['Y'])
    if z is not None:
        links.new(z, node.inputs['Z'])
    return node.outputs['Vector']


def _attribute(nodes, kind, name):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_type = kind
    node.attribute_name = name
    return node


class BoxLayout:
    """Where the photograph lands: three projections in the object's own space at its real size (the object number
    'pp_scale' undoes an unapplied scale), weighted by which way the surface faces, each stone its own patch."""

    def __init__(self, nodes, links, across, up, sharpness=4.0):
        self.nodes, self.links = nodes, links
        coordinates = nodes.new('ShaderNodeTexCoord')
        scale = _attribute(nodes, 'OBJECT', 'pp_scale').outputs['Vector']
        # an object without the number reads (0, 0, 0): use 1 there instead
        missing = _vector_math(nodes, links, 'SUBTRACT', (1.0, 1.0, 1.0),
                               _vector_math(nodes, links, 'MINIMUM', (1.0, 1.0, 1.0),
                                            _vector_math(nodes, links, 'CEIL', _vector_math(nodes, links, 'ABSOLUTE', scale))))
        scale = _vector_math(nodes, links, 'ADD', scale, missing)
        position = _vector_math(nodes, links, 'MULTIPLY', coordinates.outputs['Object'], scale)
        separate = nodes.new('ShaderNodeSeparateXYZ')
        links.new(position, separate.inputs['Vector'])
        x, y, z = separate.outputs['X'], separate.outputs['Y'], separate.outputs['Z']
        patch = _attribute(nodes, 'GEOMETRY', 'stone_patch').outputs['Fac']
        offset = _vector_math(nodes, links, 'MULTIPLY', _combine(nodes, links, patch, patch), (7.31, 3.17, 0.0))
        # every object, every copy of one and every laid stone samples its own patch
        where = nodes.new('ShaderNodeObjectInfo')
        offset = _vector_math(nodes, links, 'ADD', offset,
                              _vector_math(nodes, links, 'MULTIPLY', _combine(nodes, links, where.outputs['Random'], where.outputs['Random']),
                                           (5.27, 2.91, 0.0)))
        offset = _vector_math(nodes, links, 'ADD', offset, _vector_math(nodes, links, 'MULTIPLY', where.outputs['Location'], (0.61, 0.43, 0.0)))
        size = (1.0 / across, 1.0 / up, 1.0)
        self.planes = []
        for first, second in ((y, z), (x, z), (x, y)):          # seen along x, along y, from above or below
            vector = _vector_math(nodes, links, 'MULTIPLY', _combine(nodes, links, first, second), size)
            self.planes.append(_vector_math(nodes, links, 'ADD', vector, offset))
        normal = _vector_math(nodes, links, 'ABSOLUTE', coordinates.outputs['Normal'])
        separate_normal = nodes.new('ShaderNodeSeparateXYZ')
        links.new(normal, separate_normal.inputs['Vector'])
        powered = [_math(nodes, links, 'POWER', separate_normal.outputs[k], sharpness) for k in ('X', 'Y', 'Z')]
        total = _math(nodes, links, 'ADD', _math(nodes, links, 'ADD', powered[0], powered[1]), powered[2])
        self.weights = [_math(nodes, links, 'DIVIDE', p, _math(nodes, links, 'MAXIMUM', total, 1e-5)) for p in powered]

    def sample(self, image, colour=True):
        """The photograph laid on from three sides and blended: a colour socket, or a value socket."""
        nodes, links = self.nodes, self.links
        result = None
        for plane, weight in zip(self.planes, self.weights):
            texture = nodes.new('ShaderNodeTexImage')
            texture.image = image
            texture.interpolation = 'Linear' if colour else 'Cubic'
            links.new(plane, texture.inputs['Vector'])
            if colour:
                part = _vector_math(nodes, links, 'SCALE', texture.outputs['Color'], scale=weight)
                result = part if result is None else _vector_math(nodes, links, 'ADD', result, part)
            else:
                part = _math(nodes, links, 'MULTIPLY', texture.outputs['Color'], weight)
                result = part if result is None else _math(nodes, links, 'ADD', result, part)
        return result


# ----------------------------------------------------------------------------------------------- the tool

def add(material, strength=0.65, relief=0.005):
    """Lay the stone grain over a material (a store name or a material). Returns True when added, False when the
    material had it already or has no Principled BSDF to add it to."""
    material = store.material(material) if isinstance(material, str) else material
    if material is None or not material.use_nodes or material.node_tree is None or material.get('pp_stone_grain'):
        return False
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled_nodes = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
    if not principled_nodes:
        return False
    across, up = (_entry()['size_m'] + [None])[:2]
    up = up or across
    colour_picture = _picture('diff')
    layout = BoxLayout(nodes, links, across, up)
    gray = nodes.new('ShaderNodeRGBToBW')
    links.new(layout.sample(colour_picture), gray.inputs['Color'])
    mean = mean_luminance(colour_picture)
    # 1 + strength x (grain / its average - 1): lighter and darker than the stone by the photograph's own variation
    factor = _math(nodes, links, 'MULTIPLY_ADD', _math(nodes, links, 'SUBTRACT', _math(nodes, links, 'DIVIDE', gray.outputs['Val'], mean), 1.0),
                   float(strength), 1.0)
    factor = _math(nodes, links, 'MAXIMUM', factor, 0.2)
    height = layout.sample(_picture('disp'), colour=False)
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
        links.new(_combine(nodes, links, factor, factor, factor), multiply.inputs[7])
        links.new(multiply.outputs[2], base)
        normal = principled.inputs['Normal']
        previous = normal.links[0].from_socket if normal.links else None
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Distance'].default_value = float(relief)
        bump.inputs['Strength'].default_value = 1.0
        links.new(height, bump.inputs['Height'])
        if previous is not None:
            links.new(previous, bump.inputs['Normal'])
        links.new(bump.outputs['Normal'], normal)
    material['pp_stone_grain'] = True
    material['pp_stone_grain_strength'] = float(strength)
    material['pp_stone_grain_relief'] = float(relief)
    return True


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--material', action='append', default=[], help='a material in the file or the store (repeat for more)')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--strength', type=float, default=0.65, help='how strongly the grain lightens and darkens; default 0.65')
    parser.add_argument('--relief', type=float, default=0.005, help='how deep the grain bumps are, metres; default 0.005')
    args = parser.parse_args(argv)
    if not (args.blend and args.material and args.out):
        parser.error('--blend, --material and --out are needed to add grain')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    for name in args.material:
        print('%s: %s' % (name, 'grain added' if add(name, args.strength, args.relief) else 'had it already (or no Principled BSDF)'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))


if __name__ == '__main__':
    main()
