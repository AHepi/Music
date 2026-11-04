"""
What this file does: builds the store's soil and pebble materials, the ones the ground, stones and tracks tools write
numbers for (build_materials.py calls build_all()). They read these numbers on each point of the ground:

    wetness      0 dry, about 0.2 damp, about 0.5 wet, 0.86 and over standing water (the ground tool writes it)
    wear         0 untrodden, 1 trodden hard and polished (paths, the floor of a rut); in dry dust it brushes the dust away
    crust        0 none, 1 dried mud cracked into curling plates (old puddle beds, old ruts)
    tread        how strongly a tyre's tread or a boot's hobnails show (0 none), with tread_u (across, metres),
                 tread_v (along, metres) and tread_kind (0 a plain band, 1 a tyre's bars, 2 hobnails)
    smear        0 none, 1 wet mud a wheel has dragged: fine streaks along the track (along tread_v), replacing the
                 photograph's grain, so a wet rut's shine breaks into streaks instead of one smooth line

All are optional: a mesh without them reads as dry, untrodden soil. Wet is the same soil darker and glossier, by a
curve, with a film of water (a clear coat) whose shine comes in after the darkening and goes first on drying; dust is a
pale layer that settles in the low parts of the photograph on dry ground and is brushed away by feet and wheels.

Dials, as nodes in each soil material: 'Dust' (0.6), 'Crust' (1.0), 'Wet gain' (1.0, multiplies the wetness),
'Bump' (0.5), 'Picture scale' (1.0: the photographs' real size; 2 = twice as big).
"""

import json
import os

import bpy

from node_helpers import fresh_material, math, mix, noise, ramp

FLOODED = 0.86


def _linear_mean(path):
    from PIL import Image
    import numpy
    picture = numpy.asarray(Image.open(path).convert('RGB').resize((128, 128)), dtype=numpy.float32) / 255.0
    linear = numpy.where(picture <= 0.04045, picture / 12.92, ((picture + 0.055) / 1.055) ** 2.4)
    return float((linear @ numpy.array([0.2126, 0.7152, 0.0722])).mean()), [float(v) for v in linear.reshape(-1, 3).mean(0)]


def _range(nodes, links, value, low, high, to_low=0.0, to_high=1.0, smooth=False):
    node = nodes.new('ShaderNodeMapRange')
    node.clamp = True
    if smooth:
        node.interpolation_type = 'SMOOTHSTEP'
    node.inputs['From Min'].default_value = low
    node.inputs['From Max'].default_value = high
    node.inputs['To Min'].default_value = to_low
    node.inputs['To Max'].default_value = to_high
    if isinstance(value, bpy.types.NodeSocket):
        links.new(value, node.inputs['Value'])
    else:
        node.inputs['Value'].default_value = value
    return node.outputs['Result']


def _lerp(nodes, links, factor, a, b):
    """a + (b - a) x factor, for plain numbers (sockets or values)."""
    return math(nodes, links, 'ADD', a, math(nodes, links, 'MULTIPLY', factor, math(nodes, links, 'SUBTRACT', b, a)))


def _attribute(nodes, name, kind='GEOMETRY'):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_type = kind
    node.attribute_name = name
    return node.outputs['Fac']


def _value(nodes, name, value):
    node = nodes.new('ShaderNodeValue')
    node.name = node.label = name
    node.outputs[0].default_value = value
    return node.outputs[0]


def _scale(nodes, links, colour, factor):
    node = nodes.new('ShaderNodeVectorMath')
    node.operation = 'SCALE'
    if isinstance(colour, bpy.types.NodeSocket):
        links.new(colour, node.inputs[0])
    else:
        node.inputs[0].default_value = colour
    if isinstance(factor, bpy.types.NodeSocket):
        links.new(factor, node.inputs['Scale'])
    else:
        node.inputs['Scale'].default_value = factor
    return node.outputs[0]


def _vadd(nodes, links, a, b):
    node = nodes.new('ShaderNodeVectorMath')
    node.operation = 'ADD'
    for socket, value in zip(node.inputs, (a, b)):
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value
    return node.outputs[0]


def _picture(nodes, links, path, colour_space, vector):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colour_space
    node = nodes.new('ShaderNodeTexImage')
    node.image = image
    node.projection = 'BOX'
    node.projection_blend = 0.2
    links.new(vector, node.inputs['Vector'])
    return node


CHURNED = 'brown_mud_03'          # the photographed churned mud laid where a track left bare earth
CHURNED_TURN, CHURNED_SHIFT = 0.31, (1.3, 7.1, 0.0)
SECOND_TURN, SECOND_SHIFT = 0.63, (3.7, 1.9, 0.0)
DEPTHS = {'brown_mud': 0.012, 'gravel_road': 0.012, 'mud_forest': 0.01, 'brown_mud_03': 0.045}   # metres from the lowest to the highest of each height photo


def _normal_picture(nodes, links, path, vector, turn):
    """A normal photo laid flat from above on the same coordinates as its colour photo: returns its sideways lean
    (x, y, 0) in the object's own directions (the photo's turn undone)."""
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'Non-Color'
    node = nodes.new('ShaderNodeTexImage')
    node.image = image
    node.projection = 'FLAT'
    links.new(vector, node.inputs['Vector'])
    decoded = nodes.new('ShaderNodeVectorMath')
    decoded.operation = 'MULTIPLY_ADD'
    links.new(node.outputs['Color'], decoded.inputs[0])
    decoded.inputs[1].default_value = (2.0, 2.0, 0.0)
    decoded.inputs[2].default_value = (-1.0, -1.0, 0.0)
    if not turn:
        return decoded.outputs[0]
    rotate = nodes.new('ShaderNodeVectorRotate')
    rotate.rotation_type = 'Z_AXIS'
    rotate.inputs['Angle'].default_value = -turn
    links.new(decoded.outputs[0], rotate.inputs['Vector'])
    return rotate.outputs['Vector']


def _photo_set(nodes, links, shelf, entry, set_id, box_group, scale_socket, turn=0.0, shift=(0.0, 0.0, 0.0), with_normal=False):
    coordinates = nodes.new('ShaderNodeGroup')
    coordinates.node_tree = box_group
    size_x, size_y = entry['size_m']
    coordinates.inputs['Size'].default_value = (size_x, size_x, size_y)
    links.new(scale_socket, coordinates.inputs['Scale'])
    vector = coordinates.outputs['Vector']
    if turn or any(shift):
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Rotation'].default_value = (0.0, 0.0, turn)
        mapping.inputs['Location'].default_value = shift
        links.new(vector, mapping.inputs['Vector'])
        vector = mapping.outputs['Vector']
    folder = os.path.join(shelf, set_id)
    colour = _picture(nodes, links, os.path.join(folder, entry['maps']['diff']), 'sRGB', vector)
    rough = _picture(nodes, links, os.path.join(folder, entry['maps']['rough']), 'Non-Color', vector)
    height = _picture(nodes, links, os.path.join(folder, entry['maps']['disp']), 'Non-Color', vector)
    mean, average = _linear_mean(os.path.join(folder, entry['maps']['diff']))
    darken = max(0.3, min(1.0, (0.08 / max(mean, 1e-4)) ** 0.7))
    if with_normal:
        lean = (_normal_picture(nodes, links, os.path.join(folder, entry['maps']['normal']), vector, turn)
                if 'normal' in entry['maps'] else _vadd(nodes, links, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        return colour.outputs['Color'], rough.outputs['Color'], height.outputs['Color'], darken, average, lean
    return colour.outputs['Color'], rough.outputs['Color'], height.outputs['Color'], darken, average


def soil_material(name, shelf, manifest, first, second, second_weight, box_group, what, tint=(1.0, 1.0, 1.0)):
    """A soil from two shelf photographs mixed in big patches, reading the ground's numbers (see the note above)."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    scale = _value(nodes, 'Picture scale', 1.0)
    dust_dial = _value(nodes, 'Dust', 0.6)
    crust_dial = _value(nodes, 'Crust', 1.0)
    wet_gain = _value(nodes, 'Wet gain', 1.0)
    bump_dial = _value(nodes, 'Bump', 0.5)
    a_colour, a_rough, a_height, a_darken, a_average, a_lean = _photo_set(nodes, links, shelf, manifest[first], first, box_group, scale,
                                                                          with_normal=True)
    b_colour, b_rough, b_height, b_darken, _, b_lean = _photo_set(nodes, links, shelf, manifest[second], second, box_group, scale,
                                                                  turn=SECOND_TURN, shift=SECOND_SHIFT, with_normal=True)
    c_colour, c_rough, c_height, c_darken, _, c_lean = _photo_set(nodes, links, shelf, manifest[CHURNED], CHURNED, box_group, scale,
                                                                  turn=CHURNED_TURN, shift=CHURNED_SHIFT, with_normal=True)
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    # the two photographs in big soft patches, each darkened into the look, the whole broken by slow tone changes; on a
    # ground made by the ground tool the patches come from its 'soil_patch' number (the same the ground's lumps follow)
    noise_patches = _range(nodes, links, noise(nodes, links, position, 0.14, detail=3.0), 0.38, 0.66, 0.0, second_weight, smooth=True)
    patches = _lerp(nodes, links, _attribute(nodes, 'soil_patch_on'), noise_patches,
                    math(nodes, links, 'MULTIPLY', _attribute(nodes, 'soil_patch'), second_weight))
    # where a track left bare earth, the photographed churned mud (lumps, clods and boot marks) takes over
    churn = _range(nodes, links, _attribute(nodes, 'bare'), 0.15, 0.6, smooth=True)
    colour = mix(nodes, links, patches, _scale(nodes, links, a_colour, a_darken), _scale(nodes, links, b_colour, b_darken))
    colour = mix(nodes, links, churn, colour, _scale(nodes, links, c_colour, c_darken))
    colour = mix(nodes, links, 1.0, colour, tint, 'MULTIPLY')
    tone = _range(nodes, links, noise(nodes, links, position, 0.35, detail=2.0), 0.3, 0.7, 0.82, 1.12)
    colour = _scale(nodes, links, colour, tone)
    height = mix(nodes, links, churn, mix(nodes, links, patches, a_height, b_height), c_height)
    rough = mix(nodes, links, churn, mix(nodes, links, patches, a_rough, b_rough), c_rough)
    lean = mix(nodes, links, churn, mix(nodes, links, patches, a_lean, b_lean), c_lean)
    height_value = nodes.new('ShaderNodeRGBToBW')
    links.new(height, height_value.inputs['Color'])
    height = height_value.outputs['Val']
    rough_value = nodes.new('ShaderNodeRGBToBW')
    links.new(rough, rough_value.inputs['Color'])
    rough = math(nodes, links, 'MULTIPLY_ADD', rough_value.outputs['Val'], 0.35, 0.6)

    wet = math(nodes, links, 'MULTIPLY', _attribute(nodes, 'wetness'), wet_gain, clamp=True)
    wear = _attribute(nodes, 'wear')
    crust_amount = math(nodes, links, 'MULTIPLY', _attribute(nodes, 'crust'), crust_dial, clamp=True)
    tread = _attribute(nodes, 'tread')
    tread_u = _attribute(nodes, 'tread_u')
    tread_v = _attribute(nodes, 'tread_v')
    tread_kind = _attribute(nodes, 'tread_kind')

    # dust: a pale fine layer on dry ground, settling first in the low parts of the photograph; feet brush it away
    dry = math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, wet, 0.06, 0.32, smooth=True))
    dust_amount = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', dust_dial, dry),
                       math(nodes, links, 'MULTIPLY_ADD', wear, -0.9, 1.0), clamp=True)
    grain = noise(nodes, links, position, 38.0, detail=4.0)
    settle = math(nodes, links, 'ADD', math(nodes, links, 'SUBTRACT', 1.0, height), math(nodes, links, 'MULTIPLY_ADD', grain, 0.5, -0.25))
    dust_mask = _range(nodes, links, math(nodes, links, 'SUBTRACT', settle, math(nodes, links, 'MULTIPLY_ADD', dust_amount, -1.1, 1.2)),
                       -0.08, 0.12, smooth=True)
    dust_mask = math(nodes, links, 'MULTIPLY', dust_mask, math(nodes, links, 'MINIMUM', math(nodes, links, 'MULTIPLY', dust_amount, 3.0), 1.0))
    grey = nodes.new('ShaderNodeRGBToBW')
    links.new(colour, grey.inputs['Color'])
    dust_colour = mix(nodes, links, 0.55, _vadd(nodes, links, _scale(nodes, links, colour, 1.45), (0.03, 0.027, 0.022)),
                      _vadd(nodes, links, _scale(nodes, links, (1.0, 0.94, 0.84), math(nodes, links, 'MULTIPLY', grey.outputs['Val'], 1.6)),
                            (0.03, 0.027, 0.022)))
    colour = mix(nodes, links, dust_mask, colour, dust_colour)
    rough = math(nodes, links, 'MAXIMUM', rough, math(nodes, links, 'MULTIPLY', dust_mask, 0.95))

    # crust: dried mud cracked into plates 5 to 30 cm across, their edges curling up, the cracks dark
    cells = nodes.new('ShaderNodeTexVoronoi')
    cells.feature = 'DISTANCE_TO_EDGE'
    cells.inputs['Scale'].default_value = 7.0
    big_cells = nodes.new('ShaderNodeTexVoronoi')
    big_cells.feature = 'DISTANCE_TO_EDGE'
    big_cells.inputs['Scale'].default_value = 3.2
    warp = nodes.new('ShaderNodeTexNoise')
    warp.inputs['Scale'].default_value = 6.0
    warp.inputs['Detail'].default_value = 3.0
    links.new(position, warp.inputs['Vector'])
    warped = _vadd(nodes, links, position, _scale(nodes, links, warp.outputs['Color'], 0.035))
    links.new(warped, cells.inputs['Vector'])
    links.new(warped, big_cells.inputs['Vector'])
    which = _range(nodes, links, noise(nodes, links, position, 0.8, detail=1.0), 0.4, 0.6, smooth=True)
    edge = math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY', cells.outputs['Distance'], math(nodes, links, 'SUBTRACT', 1.0, which)),
                math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', big_cells.outputs['Distance'], 0.5), which))
    crack = math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, edge, 0.0, 0.035, smooth=True))
    curl = math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, edge, 0.03, 0.2, smooth=True))
    crust_height = math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', math(nodes, links, 'MULTIPLY', curl, 0.5), crack),
                        crust_amount)
    crust_colour = mix(nodes, links, crack, _vadd(nodes, links, _scale(nodes, links, colour, 1.18), (0.012, 0.011, 0.01)),
                       _scale(nodes, links, colour, 0.3))
    colour = mix(nodes, links, crust_amount, colour, crust_colour)
    rough = math(nodes, links, 'MAXIMUM', rough, math(nodes, links, 'MULTIPLY', crust_amount, 0.9))

    # wear: trodden hard, a little paler and smoother where dry, the fine relief pressed flat
    colour = _scale(nodes, links, colour, math(nodes, links, 'ADD', 1.0, math(nodes, links, 'MULTIPLY', wear,
                                                                       math(nodes, links, 'MULTIPLY', dry, 0.14))))
    rough = math(nodes, links, 'MULTIPLY', rough, math(nodes, links, 'MULTIPLY_ADD', wear, -0.3, 1.0))

    # tread: a tyre's bars or a boot's hobnails pressed into the floor of a track
    bars_phase = math(nodes, links, 'FRACT', math(nodes, links, 'DIVIDE', math(nodes, links, 'ADD', tread_v,
                                                                       math(nodes, links, 'MULTIPLY', math(nodes, links, 'ABSOLUTE', tread_u), 0.35)), 0.03))
    bars = math(nodes, links, 'SUBTRACT', _range(nodes, links, bars_phase, 0.15, 0.3, smooth=True),
                _range(nodes, links, bars_phase, 0.55, 0.7, smooth=True))
    dot_x = math(nodes, links, 'SUBTRACT', math(nodes, links, 'FRACT', math(nodes, links, 'DIVIDE', tread_u, 0.018)), 0.5)
    dot_y = math(nodes, links, 'SUBTRACT', math(nodes, links, 'FRACT', math(nodes, links, 'DIVIDE', tread_v, 0.018)), 0.5)
    dot_r = math(nodes, links, 'SQRT', math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY', dot_x, dot_x),
                                            math(nodes, links, 'MULTIPLY', dot_y, dot_y)))
    dots = math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, dot_r, 0.14, 0.26, smooth=True))
    is_bars = math(nodes, links, 'SUBTRACT', 1.0, math(nodes, links, 'MINIMUM',
                                                       math(nodes, links, 'MULTIPLY', math(nodes, links, 'ABSOLUTE', math(nodes, links, 'SUBTRACT', tread_kind, 1.0)), 3.0), 1.0))
    is_dots = math(nodes, links, 'SUBTRACT', 1.0, math(nodes, links, 'MINIMUM',
                                                       math(nodes, links, 'MULTIPLY', math(nodes, links, 'ABSOLUTE', math(nodes, links, 'SUBTRACT', tread_kind, 2.0)), 3.0), 1.0))
    tread_height = math(nodes, links, 'MULTIPLY', tread, math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY', bars, is_bars),
                                                              math(nodes, links, 'MULTIPLY', dots, is_dots)))

    # smear: wet mud a wheel has dragged, in fine streaks along the track (tread_u runs across it, tread_v along it)
    smear = _attribute(nodes, 'smear')
    track = nodes.new('ShaderNodeCombineXYZ')
    links.new(math(nodes, links, 'MULTIPLY', tread_v, 2.5), track.inputs['X'])
    links.new(math(nodes, links, 'MULTIPLY', tread_u, 30.0), track.inputs['Y'])
    streaks = noise(nodes, links, track.outputs['Vector'], 1.0, detail=6.0, roughness=0.62)
    smear_height = math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', streaks, 0.5), math(nodes, links, 'MULTIPLY', smear, 1.6))
    colour = _scale(nodes, links, colour, math(nodes, links, 'MULTIPLY_ADD', smear, -0.18, 1.0))

    # bare earth a track has churned ('bare'): crumbs a few centimetres across, their creases dark
    bare = _attribute(nodes, 'bare')
    crumbs = nodes.new('ShaderNodeTexVoronoi')
    crumbs.inputs['Scale'].default_value = 26.0
    crumbs.inputs['Randomness'].default_value = 1.0
    crumb_warp = noise(nodes, links, position, 9.0, detail=2.0)
    links.new(_vadd(nodes, links, position, _scale(nodes, links, (1.0, 1.0, 1.0), math(nodes, links, 'MULTIPLY_ADD', crumb_warp, 0.05, -0.025))),
              crumbs.inputs['Vector'])                                   # the crumbs' edges wander, so they do not tile like scales
    crumb = _range(nodes, links, crumbs.outputs['Distance'], 0.0, 0.75, 1.0, 0.0, smooth=True)
    crumb = mix(nodes, links, 0.45, crumb, noise(nodes, links, position, 40.0, detail=3.0))
    patchy = _range(nodes, links, noise(nodes, links, position, 3.0, detail=2.0), 0.35, 0.65, 0.35, 1.0)
    crumb_amount = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', bare, patchy),
                        math(nodes, links, 'SUBTRACT', 1.0, math(nodes, links, 'MULTIPLY', smear, 0.6)))
    crumb_height = math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', crumb, 0.5), crumb_amount)
    colour = _scale(nodes, links, colour, math(nodes, links, 'SUBTRACT', 1.0,
                                               math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', 1.0, crumb),
                                                    math(nodes, links, 'MULTIPLY', crumb_amount, 0.3))))

    # contact shadow: soil darkens where it meets stones, walls and the walls of a track
    occlusion = nodes.new('ShaderNodeAmbientOcclusion')
    occlusion.samples = 8
    occlusion.inputs['Distance'].default_value = 0.12
    colour = _scale(nodes, links, colour, math(nodes, links, 'MULTIPLY_ADD', occlusion.outputs['AO'], 0.45, 0.55))

    # wet: darker by a curve, a little richer, and under a film of water whose shine comes in after the darkening
    gloss = _range(nodes, links, wet, 0.32, 0.8, smooth=True)
    flooded = _range(nodes, links, wet, FLOODED - 0.02, FLOODED + 0.02, smooth=True)
    darker = math(nodes, links, 'MULTIPLY_ADD', wet, -0.72, 1.0)
    darker = math(nodes, links, 'MULTIPLY', darker, math(nodes, links, 'MULTIPLY_ADD', flooded, -0.45, 1.0))
    wet_colour = _scale(nodes, links, colour, darker)
    wet_colour = mix(nodes, links, math(nodes, links, 'MULTIPLY', wet, 0.8), wet_colour,
                     mix(nodes, links, 1.0, wet_colour, (1.03, 0.97, 0.9), 'MULTIPLY'))       # soaked earth turns a deeper, warmer brown
    richer = nodes.new('ShaderNodeHueSaturation')
    links.new(wet_colour, richer.inputs['Color'])
    links.new(math(nodes, links, 'MULTIPLY_ADD', wet, 0.45, 1.0), richer.inputs['Saturation'])
    links.new(richer.outputs['Color'], principled.inputs['Base Color'])
    links.new(_lerp(nodes, links, gloss, rough, 0.62), principled.inputs['Roughness'])       # the soil stays rough; the film shines
    # the film on wet mud is patchy and follows the soil's grain, so its shine breaks into pieces; only standing water
    # is a smooth mirror (a smooth film the whole length of a rut reads as a rail)
    film = _range(nodes, links, noise(nodes, links, position, 2.6, detail=3.0), 0.32, 0.68, smooth=True)
    upright = nodes.new('ShaderNodeSeparateXYZ')                # water runs off steep faces: the walls of a rut drain
    links.new(nodes.new('ShaderNodeNewGeometry').outputs['Normal'], upright.inputs[0])
    drain = _range(nodes, links, upright.outputs['Z'], 0.96, 0.78, smooth=True)
    film = math(nodes, links, 'MULTIPLY', film, math(nodes, links, 'MULTIPLY_ADD', drain, -0.85, 1.0))
    film_weight = _lerp(nodes, links, flooded, math(nodes, links, 'MULTIPLY_ADD', film, 0.55, 0.15), 0.9)
    links.new(math(nodes, links, 'MULTIPLY', gloss, film_weight), principled.inputs['Coat Weight'])
    film_rough = math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY_ADD', wet, -0.12, 0.3),
                      math(nodes, links, 'MULTIPLY_ADD', film, -0.1, 0.1))
    film_rough = math(nodes, links, 'MULTIPLY_ADD', drain, 0.2, film_rough)
    links.new(_lerp(nodes, links, flooded, film_rough, 0.015), principled.inputs['Coat Roughness'])
    principled.inputs['Coat IOR'].default_value = 1.33

    # the photos' own relief: their normal photos carry most of it (below); their height adds a little, and smears over it
    photo_relief = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', height, math(nodes, links, 'MULTIPLY_ADD', wet, -0.2, 0.45)),
                        math(nodes, links, 'MULTIPLY_ADD', smear, -0.5, 1.0))
    relief = math(nodes, links, 'ADD', math(nodes, links, 'ADD', photo_relief, math(nodes, links, 'ADD', smear_height, crumb_height)),
                  math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY', crust_height, 0.8), math(nodes, links, 'MULTIPLY', tread_height, -0.7)))
    relief = math(nodes, links, 'MULTIPLY', relief, math(nodes, links, 'MULTIPLY_ADD', wear, -0.5, 1.0))
    # the normal photos lean the light the way each tiny bit of the photographed ground faced, on faces that look up
    # (the photos are laid from above); water fills the pores, so less when wet, none under standing water
    normal_dial = _value(nodes, 'Normal', 1.0)
    facing = nodes.new('ShaderNodeNewGeometry').outputs['Normal']
    upward = nodes.new('ShaderNodeSeparateXYZ')
    links.new(facing, upward.inputs[0])
    lean_strength = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', normal_dial, _range(nodes, links, upward.outputs['Z'], 0.55, 0.85, smooth=True)),
                         math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY_ADD', wet, -0.4, 1.0), math(nodes, links, 'SUBTRACT', 1.0, flooded)))
    to_world = nodes.new('ShaderNodeVectorTransform')
    to_world.vector_type = 'VECTOR'
    to_world.convert_from = 'OBJECT'
    to_world.convert_to = 'WORLD'
    links.new(lean, to_world.inputs['Vector'])
    leaned = nodes.new('ShaderNodeVectorMath')
    leaned.operation = 'NORMALIZE'
    links.new(_vadd(nodes, links, facing, _scale(nodes, links, to_world.outputs['Vector'], lean_strength)), leaned.inputs[0])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.012
    links.new(math(nodes, links, 'MULTIPLY', bump_dial, math(nodes, links, 'MULTIPLY_ADD', flooded, -0.85, 1.0)), bump.inputs['Strength'])
    links.new(relief, bump.inputs['Height'])
    links.new(leaned.outputs[0], bump.inputs['Normal'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    coat_bump = nodes.new('ShaderNodeBump')
    coat_bump.inputs['Distance'].default_value = 0.012
    links.new(math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', bump_dial, 0.85), math(nodes, links, 'SUBTRACT', 1.0, flooded)),
              coat_bump.inputs['Strength'])
    links.new(relief, coat_bump.inputs['Height'])
    links.new(leaned.outputs[0], coat_bump.inputs['Normal'])
    links.new(coat_bump.outputs['Normal'], principled.inputs['Coat Normal'])
    material.diffuse_color = (*[c * a_darken for c in a_average], 1.0)
    # what the ground tool needs to push a ground's surface up and down by these same photos (ground.detail)
    material['store_photos'] = json.dumps({
        'first': first, 'second': second, 'second_weight': second_weight, 'second_turn': SECOND_TURN, 'second_shift': list(SECOND_SHIFT),
        'churned': CHURNED, 'churned_turn': CHURNED_TURN, 'churned_shift': list(CHURNED_SHIFT),
        'sizes': {key: manifest[key]['size_m'] for key in (first, second, CHURNED)},
        'heights': {key: os.path.join(key, manifest[key]['maps']['disp']) for key in (first, second, CHURNED)},
        'depths': {key: DEPTHS.get(key, 0.012) for key in (first, second, CHURNED)}})
    material['store_what'] = what
    material['store_size_m'] = manifest[first]['size_m']
    material['store_source'] = manifest[first].get('source', '')
    return material


def pebble_material(name):
    """Pebbles and broken stones: greys and browns, each stone its own shade, soil stained up their foot, dark and glossy
    when wet: reads 'wetness' from the stone's own mesh, or from the points that place copies of it (the stones tool)."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    info = nodes.new('ShaderNodeObjectInfo')
    coordinates = nodes.new('ShaderNodeTexCoord')
    shades = ramp(nodes, [(0.0, (0.05, 0.048, 0.045)), (0.3, (0.085, 0.075, 0.062)), (0.55, (0.11, 0.105, 0.098)),
                          (0.8, (0.075, 0.062, 0.05)), (1.0, (0.13, 0.12, 0.105))])
    links.new(info.outputs['Random'], shades.inputs[0])
    shifted = _vadd(nodes, links, coordinates.outputs['Object'], _scale(nodes, links, info.outputs['Location'], 1.0))
    mottle = _range(nodes, links, noise(nodes, links, shifted, 28.0, detail=5.0), 0.3, 0.7, 0.7, 1.25)
    colour = _scale(nodes, links, shades.outputs['Color'], mottle)
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(coordinates.outputs['Generated'], separate.inputs[0])
    # soil stains each stone from its own soil line up (the stones tool writes 'stone_burial', the share of its height
    # sunk into the ground); a stone without it is stained from its foot
    above_soil = math(nodes, links, 'SUBTRACT', separate.outputs['Z'], _attribute(nodes, 'stone_burial', 'INSTANCER'))
    stained = math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, above_soil, -0.02, 0.32, smooth=True))
    colour = mix(nodes, links, math(nodes, links, 'MULTIPLY', stained, 0.7), colour, (0.045, 0.034, 0.024))
    wet = math(nodes, links, 'MAXIMUM', _attribute(nodes, 'wetness'), _attribute(nodes, 'wetness', 'INSTANCER'))
    # dry stones carry a little of the ground's pale dust on their tops, so they sit in dusty soil instead of speckling it
    dusty = math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, wet, 0.06, 0.32, smooth=True)),
                 _range(nodes, links, separate.outputs['Z'], 0.5, 0.95, smooth=True))
    dusty = math(nodes, links, 'MULTIPLY', dusty, _range(nodes, links, noise(nodes, links, shifted, 16.0, detail=3.0), 0.35, 0.65, 0.15, 0.6))
    colour = mix(nodes, links, dusty, colour, (0.15, 0.135, 0.11))
    gloss = _range(nodes, links, wet, 0.3, 0.75, smooth=True)
    links.new(_scale(nodes, links, colour, math(nodes, links, 'MULTIPLY_ADD', wet, -0.5, 1.0)), principled.inputs['Base Color'])
    links.new(_range(nodes, links, noise(nodes, links, shifted, 9.0, detail=2.0), 0.3, 0.7, 0.5, 0.8), principled.inputs['Roughness'])
    links.new(math(nodes, links, 'MULTIPLY', gloss, 0.85), principled.inputs['Coat Weight'])
    principled.inputs['Coat Roughness'].default_value = 0.06
    principled.inputs['Coat IOR'].default_value = 1.33
    pits = noise(nodes, links, shifted, 60.0, detail=3.0)
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.002
    links.new(pits, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.085, 0.078, 0.07, 1.0)
    material['store_what'] = ("pebbles and broken stones, each its own grey or brown, soil up their foot, dark and glossy when wet "
                              "(reads 'wetness' from the stone or from the stones tool's points)")
    return material


def grass_material(name):
    """Grass blades for the grass tool: dark olive to yellow-green, drying to straw from the tips, dark at the root, lit
    through a little from behind; darker with a sheen when wet. Reads 'blade_height', 'blade_random' and 'blade_head' from
    the blade itself and 'grass_tone', 'grass_dry' and 'wetness' from the point that places the tuft."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    output = nodes.get('Material Output')
    height = _attribute(nodes, 'blade_height')
    blade = _attribute(nodes, 'blade_random')
    head = _attribute(nodes, 'blade_head')
    tone = _attribute(nodes, 'grass_tone', 'INSTANCER')
    dry = _attribute(nodes, 'grass_dry', 'INSTANCER')
    wet = _attribute(nodes, 'wetness', 'INSTANCER')
    greens = ramp(nodes, [(0.0, (0.016, 0.026, 0.009)), (0.45, (0.036, 0.052, 0.015)), (0.8, (0.06, 0.074, 0.02)),
                          (1.0, (0.08, 0.082, 0.028))])
    links.new(math(nodes, links, 'MULTIPLY_ADD', tone, 0.7, math(nodes, links, 'MULTIPLY', blade, 0.3)), greens.inputs[0])
    straw = ramp(nodes, [(0.0, (0.075, 0.058, 0.03)), (0.6, (0.13, 0.105, 0.058)), (1.0, (0.17, 0.145, 0.085))])
    links.new(blade, straw.inputs[0])
    drying = math(nodes, links, 'ADD', math(nodes, links, 'ADD', dry, math(nodes, links, 'MULTIPLY_ADD', blade, 0.5, -0.25)),
                  math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', height, dry), 0.45))     # the tips go first
    colour = mix(nodes, links, _range(nodes, links, drying, 0.35, 0.75, smooth=True), greens.outputs['Color'], straw.outputs['Color'])
    colour = _scale(nodes, links, colour, _range(nodes, links, height, 0.0, 0.35, 0.3, 1.0, smooth=True))       # dark at the root
    colour = mix(nodes, links, head, colour, (0.055, 0.04, 0.026))                                          # dry seed heads
    colour = _scale(nodes, links, colour, math(nodes, links, 'MULTIPLY_ADD', wet, -0.3, 1.0))
    links.new(colour, principled.inputs['Base Color'])
    links.new(math(nodes, links, 'MULTIPLY_ADD', wet, -0.25, 0.55), principled.inputs['Roughness'])
    links.new(math(nodes, links, 'MULTIPLY', _range(nodes, links, wet, 0.3, 0.8, smooth=True), 0.6), principled.inputs['Coat Weight'])
    principled.inputs['Coat Roughness'].default_value = 0.12
    through = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(_scale(nodes, links, colour, 1.6), through.inputs['Color'])
    both = nodes.new('ShaderNodeMixShader')
    both.inputs['Fac'].default_value = 0.28
    links.new(principled.outputs['BSDF'], both.inputs[1])
    links.new(through.outputs['BSDF'], both.inputs[2])
    links.new(both.outputs['Shader'], output.inputs['Surface'])
    material.diffuse_color = (0.05, 0.06, 0.02, 1.0)
    material['store_what'] = ("grass blades for the grass tool: olive to yellow-green, drying to straw from the tips, dark at the root, "
                              "seed heads brown; darker and shining when wet (reads the grass tool's numbers)")
    return material


def leaf_material(name):
    """Fallen leaves for the litter tool: ochre, rust, peat brown and a few still green, with a darker midrib, veins and
    edge; trodden into mud darker and muddier; dark and shining when wet. Reads 'leaf_u' and 'leaf_v' from the leaf
    and 'litter_tone', 'litter_mud' and 'wetness' from the point that lays it."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    output = nodes.get('Material Output')
    along = _attribute(nodes, 'leaf_u')
    across = math(nodes, links, 'ABSOLUTE', _attribute(nodes, 'leaf_v'))
    tone = _attribute(nodes, 'litter_tone', 'INSTANCER')
    mud = _attribute(nodes, 'litter_mud', 'INSTANCER')
    wet = _attribute(nodes, 'wetness', 'INSTANCER')
    shades = ramp(nodes, [(0.0, (0.032, 0.017, 0.008)), (0.25, (0.085, 0.03, 0.01)), (0.5, (0.15, 0.075, 0.017)),
                          (0.75, (0.19, 0.125, 0.03)), (0.9, (0.095, 0.08, 0.02)), (1.0, (0.045, 0.055, 0.014))])
    links.new(tone, shades.inputs[0])
    midrib = math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, across, 0.0, 0.07, smooth=True))
    slant = math(nodes, links, 'FRACT', math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', along,
                                                                          math(nodes, links, 'MULTIPLY', across, 0.5)), 7.0))
    veins = math(nodes, links, 'MULTIPLY', math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, slant, 0.0, 0.09, smooth=True)),
                 math(nodes, links, 'SUBTRACT', 1.0, _range(nodes, links, across, 0.8, 0.95)))
    lines = math(nodes, links, 'MAXIMUM', midrib, math(nodes, links, 'MULTIPLY', veins, 0.6))
    colour = _scale(nodes, links, shades.outputs['Color'], math(nodes, links, 'MULTIPLY_ADD', lines, -0.28, 1.0))
    colour = _scale(nodes, links, colour, _range(nodes, links, across, 0.7, 1.0, 1.0, 0.7, smooth=True))     # a darker edge
    place = nodes.new('ShaderNodeTexCoord').outputs['Object']
    colour = _scale(nodes, links, colour, _range(nodes, links, noise(nodes, links, place, 9.0, detail=3.0), 0.3, 0.7, 0.8, 1.15))
    colour = mix(nodes, links, math(nodes, links, 'MULTIPLY', mud, 0.8), colour, (0.03, 0.022, 0.014))         # trodden into mud
    colour = _scale(nodes, links, colour, math(nodes, links, 'MULTIPLY_ADD', wet, -0.35, 1.0))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.72
    principled.inputs['Specular IOR Level'].default_value = 0.3
    links.new(math(nodes, links, 'MULTIPLY', _range(nodes, links, wet, 0.3, 0.8, smooth=True), 0.2), principled.inputs['Coat Weight'])
    principled.inputs['Coat Roughness'].default_value = 0.25
    through = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(_scale(nodes, links, colour, 1.4), through.inputs['Color'])
    both = nodes.new('ShaderNodeMixShader')
    both.inputs['Fac'].default_value = 0.15
    links.new(principled.outputs['BSDF'], both.inputs[1])
    links.new(through.outputs['BSDF'], both.inputs[2])
    links.new(both.outputs['Shader'], output.inputs['Surface'])
    material.diffuse_color = (0.12, 0.06, 0.015, 1.0)
    material['store_what'] = ("fallen leaves for the litter tool: ochre, rust, peat brown and a few green, veined, darker at the edge; "
                              "muddy where trodden, dark and shining when wet (reads the litter tool's numbers)")
    return material


def build_all(shelf, manifest, box_group):
    made = [
        soil_material('MADE • dirt', shelf, manifest, 'brown_mud', 'gravel_road', 0.45, box_group,
                      "dirt ground for the ground tool: brown earth with gravel in patches; reads the ground's 'wetness', 'wear', "
                      "'crust' and 'tread' numbers (dry and dusty to wet and glossy to standing water)"),
        soil_material('MADE • dirt, dark', shelf, manifest, 'mud_forest', 'brown_mud', 0.3, box_group,
                      "dark earth ground for the ground tool (forest mud with brown earth in patches); reads the same numbers as MADE • dirt",
                      tint=(0.92, 0.9, 0.88)),
        pebble_material('MADE • pebbles, wet'),
        grass_material('MADE • grass'),
        leaf_material('MADE • fallen leaves'),
    ]
    for material in made:
        material.use_fake_user = True
    return made
