# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# A small recipe for the bake harness that contains ONLY two boxes: LAYOUT (the slates) and COLOUR AND FADE (the paint), plus the dark
# joints. The other layers (damage, moss, outline) are not in it. It is used to look at and measure the colour-and-fade layer by itself,
# quickly, and to be sure nothing else is hiding its faults. Same settings as the real recipe: 'colour_and_fade.*' and 'layout.*'
# (parameters override the defaults in the layer files; the file recipe/settings.json is NOT read here, so a test is never changed by it).
# Extra parameters (not settings):
#   view   'colour' (default): the slates painted by this layer, joints dark; 'mask': the fade strength as grey; 'height' and 'roughness':
#          this layer's relief / roughness change as grey (0.5 = no change); 'joints': LAYOUT's piece_mask as grey (1 on a slate, 0 in a joint); 'layout_only': the Height output is LAYOUT's base_height
#          alone (the layer's tone relief left out) so the layer's own height can be found by subtraction.
#   shift  [u, v]: slides the whole pattern (the half-tile test).
#   joint_colour  '#hex' of the dark joints (default a near-black blue).
# Outputs are the usual four: Colour, Roughness, Metallic, Height. Height = LAYOUT's base_height + this layer's height, so the normal map
# of the harness shows what the tone relief does.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.abspath(os.path.join(HERE, '..', '..', 'layers'))
if LAYERS not in sys.path:
    sys.path.insert(0, LAYERS)
import layer_interface as li  # noqa: E402
import layout  # noqa: E402
import colour_and_fade  # noqa: E402


def build_node_group(parameters):
    parameters = dict(parameters or {})
    tiles = int(parameters.get('recipe.tiles_across', 1))
    parameters['recipe.tiles_across'] = tiles
    view = parameters.get('view', 'colour')
    shift = parameters.get('shift') or (0.0, 0.0)
    tree, b = li.make_plain_group('COLOUR AND FADE test', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    vector = b.input('Vector')
    if shift[0] or shift[1]:
        vector = b.vmath('ADD', vector, (float(shift[0]), float(shift[1]), 0.0))
    layout_node = b.node('ShaderNodeGroup')
    layout_node.node_tree = layout.build_group(parameters)
    layout_node.label = 'LAYOUT'
    b.tree.links.new(vector, layout_node.inputs['Vector'])
    layer = b.node('ShaderNodeGroup')
    layer.node_tree = colour_and_fade.build_group(parameters)
    layer.label = 'COLOUR AND FADE'
    b.tree.links.new(vector, layer.inputs['Vector'])
    layer.inputs['Tile Count'].default_value = float(tiles)
    for name in li.BUNDLE_NAMES:
        b.tree.links.new(layout_node.outputs[name], layer.inputs[name])

    joint = parameters.get('joint_colour', '#0c0e11')
    paint = layer.outputs['Colour']
    colour = b.mix(joint, paint, layout_node.outputs['piece_mask'])
    height = b.math('ADD', layout_node.outputs['base_height'], layer.outputs['Height'], clamp=True)
    roughness = b.add(0.8, layer.outputs['Roughness'])
    if view == 'layout_only':
        height = layout_node.outputs['base_height']
        roughness = 0.8
    if view == 'joints':
        colour = b.grey_to_colour(layout_node.outputs['piece_mask'])
    elif view == 'mask':
        colour = b.grey_to_colour(layer.outputs['Mask'])
    elif view == 'height':
        colour = b.grey_to_colour(b.add(0.5, b.mul(layer.outputs['Height'], 5.0)))
    elif view == 'roughness':
        colour = b.grey_to_colour(b.add(0.5, b.mul(layer.outputs['Roughness'], 2.0)))
    b.output('Colour', colour)
    b.output('Height', height)
    b.output('Roughness', roughness)
    b.output('Metallic', 0.0)
    return tree
