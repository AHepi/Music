"""A variation hook for the ground part's light: the sun's strength, how much light the sky gives (not how it looks: a camera ray still sees the full sky colour) and how light the hills are.
Runs inside Blender on a freshly opened copy of the finished scene; the scene is never saved. args: sun_strength (W per square metre), sky_strength (0..1), hill_gain (1 = as made)."""
import bpy


def apply(variation):
    a = dict(variation.get('args') or {})
    sun = bpy.data.objects.get('Sun')
    if sun is not None and 'sun_strength' in a:
        sun.data.energy = float(a['sun_strength'])
    world = bpy.data.worlds.get('Sky')
    if world is not None and 'sky_strength' in a:
        s = float(a['sky_strength'])
        for node in world.node_tree.nodes:
            if node.type == 'MATH' and node.operation == 'MULTIPLY_ADD':
                node.inputs[1].default_value = 1.0 - s                 # camera ray: 1.0 in all; others: s
                node.inputs[2].default_value = s
    gain = float(a.get('hill_gain', 1.0))
    if abs(gain - 1.0) > 1e-6:
        for material in bpy.data.materials:
            if not material.name.startswith('Backdrop') or material.node_tree is None:
                continue
            tree = material.node_tree
            diffuse = next((n for n in tree.nodes if n.type == 'BSDF_DIFFUSE'), None)
            if diffuse is None or not diffuse.inputs['Color'].links:
                continue
            source = diffuse.inputs['Color'].links[0].from_socket
            mix = tree.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            mix.inputs[7].default_value = (gain, gain, gain, 1.0)
            tree.links.new(source, mix.inputs[6])
            tree.links.new(mix.outputs[2], diffuse.inputs['Color'])
