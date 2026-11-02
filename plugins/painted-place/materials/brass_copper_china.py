"""
What this file does:
Makes the three surfaces a tea room, a pub or a kitchen needs that the street bundle's Materials.blend does not have,
for the roles `brass`, `copper` and `china` (apply_by_role.py calls these when an object has one of those roles):

  - old brass and old copper: bright where hands and cloths keep them polished, darker and duller in every hollow
    and in patches of tarnish, each object its own patches; old copper also turns blue-green deep in its hollows.
    In this look they read dark-golden and catch the lamps as warm glints, never as a bright yellow toy;
  - glazed china: a glossy glaze over cream, pale blue-white or the dark brown of an everyday teapot, chosen per
    object, so a table's cups do not all match.

Everything is worked out from each object's own coordinates (not the world's), so a cup reads the same wherever it
stands and however small it is.
"""

import bpy

import lay_timber

BRASS = {'polished': (0.78, 0.56, 0.24), 'tarnish': (0.11, 0.075, 0.035)}
COPPER = {'polished': (0.78, 0.40, 0.24), 'tarnish': (0.12, 0.05, 0.03), 'verdigris': (0.06, 0.19, 0.16)}
CHINA_GLAZES = [(0.0, (0.60, 0.56, 0.48)),     # cream, most pieces
                (0.60, (0.46, 0.52, 0.56)),    # pale blue-white
                (0.82, (0.085, 0.040, 0.018))]  # dark brown glaze, the everyday teapot


def _own_coordinates(nodes, links, spread=(17.0, 29.0, 11.0)):
    """The object's own coordinates, moved by a different amount for each object, so no two pieces share a pattern."""
    coordinates = nodes.new('ShaderNodeTexCoord')
    info = nodes.new('ShaderNodeObjectInfo')
    offset = nodes.new('ShaderNodeVectorMath')
    offset.operation = 'SCALE'
    offset.inputs[0].default_value = spread
    links.new(info.outputs['Random'], offset.inputs['Scale'])
    shifted = nodes.new('ShaderNodeVectorMath')
    shifted.operation = 'ADD'
    links.new(coordinates.outputs['Object'], shifted.inputs[0])
    links.new(offset.outputs['Vector'], shifted.inputs[1])
    return shifted.outputs['Vector'], info


def _map(nodes, links, value, low, high, to_low=0.0, to_high=1.0):
    node = nodes.new('ShaderNodeMapRange')
    node.clamp = True
    node.inputs['From Min'].default_value = low
    node.inputs['From Max'].default_value = high
    node.inputs['To Min'].default_value = to_low
    node.inputs['To Max'].default_value = to_high
    links.new(value, node.inputs['Value'])
    return node.outputs['Result']


def old_metal(name, copper=False):
    """Old brass (or, with copper=True, old copper). Returns the material, made once."""
    material, fresh = lay_timber._fresh_material(name)
    if not fresh:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    colours = COPPER if copper else BRASS
    vector, _ = _own_coordinates(nodes, links)
    # tarnish in patches (about a third of the surface, never quite black) and in every hollow
    patches = lay_timber._noise(nodes, links, vector, 7.0, detail=5.0, roughness=0.62)
    patchy = _map(nodes, links, patches, 0.50, 0.66, 0.0, 0.75)
    hollows = nodes.new('ShaderNodeAmbientOcclusion')
    hollows.samples = 8
    hollows.inputs['Distance'].default_value = 0.05
    hollow = _map(nodes, links, hollows.outputs['AO'], 0.95, 0.55)        # 1 deep in a hollow, 0 in the open
    tarnish = lay_timber._math(nodes, links, 'MAXIMUM', hollow, patchy)
    colour = lay_timber._mix(nodes, links, tarnish, colours['polished'], colours['tarnish'])
    metallic = lay_timber._math(nodes, links, 'MULTIPLY_ADD', tarnish, -0.5, 1.0)     # the tarnish film is half metal
    # polished parts are smooth but smudged; tarnished parts dull
    smudges = lay_timber._noise(nodes, links, vector, 23.0, detail=3.0)
    smooth = _map(nodes, links, smudges, 0.3, 0.7, 0.20, 0.34)
    roughness = lay_timber._math(nodes, links, 'MAXIMUM', smooth, lay_timber._math(nodes, links, 'MULTIPLY', tarnish, 0.58))
    if copper:
        # blue-green verdigris only deep in the hollows and where a second pattern says so: dull, not metal at all
        spots = lay_timber._noise(nodes, links, vector, 13.0, detail=4.0)
        spotty = _map(nodes, links, spots, 0.52, 0.62)
        green = lay_timber._math(nodes, links, 'MULTIPLY', hollow, spotty)
        colour = lay_timber._mix(nodes, links, green, colour, colours['verdigris'])
        metallic = lay_timber._math(nodes, links, 'MULTIPLY_ADD', green, -1.0, metallic)
        metallic.node.use_clamp = True
        roughness = lay_timber._math(nodes, links, 'MAXIMUM', roughness, lay_timber._math(nodes, links, 'MULTIPLY', green, 0.85))
    links.new(colour, principled.inputs['Base Color'])
    links.new(metallic, principled.inputs['Metallic'])
    links.new(roughness, principled.inputs['Roughness'])
    # small dents from years of use
    dents = lay_timber._noise(nodes, links, vector, 40.0, detail=2.0)
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.06
    bump.inputs['Distance'].default_value = 0.002
    links.new(dents, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material['pp_made_for'] = 'copper' if copper else 'brass'
    return material


def glazed_china(name):
    """Glazed china: one of three glazes per object, glossy under a clear coat, the glaze a little uneven."""
    material, fresh = lay_timber._fresh_material(name)
    if not fresh:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    vector, info = _own_coordinates(nodes, links)
    glaze = lay_timber._ramp(nodes, CHINA_GLAZES, 'CONSTANT')
    links.new(info.outputs['Random'], glaze.inputs[0])
    uneven = lay_timber._noise(nodes, links, vector, 35.0, detail=3.0)
    shade = _map(nodes, links, uneven, 0.3, 0.7, 0.0, 0.14)
    colour = lay_timber._mix(nodes, links, shade, glaze.outputs['Color'], (0.20, 0.18, 0.15))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.16
    principled.inputs['Coat Weight'].default_value = 0.5
    principled.inputs['Coat Roughness'].default_value = 0.06
    material['pp_made_for'] = 'china'
    return material
