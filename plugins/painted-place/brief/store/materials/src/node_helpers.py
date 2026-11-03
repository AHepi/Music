"""
What this file does: small helpers for building Blender materials in code (a colour ramp, a colour mix, a maths node,
a noise, a stretched coordinate, a fresh material, a clamped range). Used by build_materials.py and made.py.
"""

import bpy


def fresh_material(name):
    """A new material with nodes; if one of that name exists it is emptied and reused, so a rebuild replaces it."""
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (300, 0)
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return material


def ramp(nodes, stops, interpolation='LINEAR'):
    node = nodes.new('ShaderNodeValToRGB')
    node.color_ramp.interpolation = interpolation
    elements = node.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, (position, colour) in zip(elements, stops):
        element.position = position
        element.color = (*colour, 1) if len(colour) == 3 else colour
    return node


def _set(links, socket, value):
    if isinstance(value, bpy.types.NodeSocket):
        links.new(value, socket)
    elif value is not None:
        socket.default_value = value if not isinstance(value, tuple) or len(value) != 3 or socket.type != 'RGBA' else (*value, 1)


def mix(nodes, links, factor, a, b, blend='MIX'):
    """Colour mix; factor, a and b are sockets or plain values. Returns the result socket."""
    node = nodes.new('ShaderNodeMix')
    node.data_type = 'RGBA'
    node.blend_type = blend
    _set(links, node.inputs[0], factor)
    _set(links, node.inputs[6], a)
    _set(links, node.inputs[7], b)
    return node.outputs[2]


def math(nodes, links, operation, a, b=None, c=None, clamp=False):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    node.use_clamp = clamp
    for socket, value in zip(node.inputs, (a, b, c)):
        _set(links, socket, value)
    return node.outputs[0]


def noise(nodes, links, vector, scale, detail=4.0, roughness=0.5, distortion=0.0):
    node = nodes.new('ShaderNodeTexNoise')
    node.inputs['Scale'].default_value = scale
    node.inputs['Detail'].default_value = detail
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Distortion'].default_value = distortion
    if vector is not None:
        links.new(vector, node.inputs['Vector'])
    return node.outputs['Fac']


def stretched(nodes, links, vector, scale):
    node = nodes.new('ShaderNodeMapping')
    node.inputs['Scale'].default_value = scale
    links.new(vector, node.inputs['Vector'])
    return node.outputs['Vector']


def map_range(nodes, links, value, low, high, to_low=0.0, to_high=1.0, clamp=True):
    node = nodes.new('ShaderNodeMapRange')
    node.clamp = clamp
    node.inputs['From Min'].default_value = low
    node.inputs['From Max'].default_value = high
    node.inputs['To Min'].default_value = to_low
    node.inputs['To Max'].default_value = to_high
    _set(links, node.inputs['Value'], value)
    return node.outputs['Result']
