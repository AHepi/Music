# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# A small recipe for the bake harness (and for tests/bake_tools.py) used to look at the MOSS layer by itself. It holds LAYOUT (the slates),
# a base paint under the moss, the MOSS box, optionally the DAMAGE box (so the declared link 'Damage Mask' is wired and damage is painted on
# top), and the dark joints. The other layers (outline) are replaced by a plain dark joint colour.
# Parameters (not settings; settings 'moss.*', 'layout.*', 'damage.*' work as in the real recipe; recipe/settings.json is NOT read here):
#   base     'flat' (default): every slate one flat blue-grey so the moss is easy to see; 'paint': the real COLOUR AND FADE layer.
#   order    'moss_on_top': paint the moss OVER the damage (default: damage over the moss, the real stack order); only with damage = true.
#   damage   true: also build DAMAGE, wire the declared link and paint damage over the moss (the real stack order). Default false.
#   view     'colour' (default) the picture; 'mask' moss strength as grey; 'height' moss height (0.5 = no change, 5 x); 'roughness' (0.5 = no change, 2 x);
#            'joints' LAYOUT's piece_mask; 'moss_only' the moss colour where the mask is 1 and black elsewhere; 'bundle_<name>' one bundle number.
#   shift    [u, v] slides the whole pattern (the half-tile test).
#   flat_colour  '#hex' of the flat slate (default '#444c53').
# Outputs: Colour, Roughness, Metallic, Height (Height = LAYOUT base_height + MOSS height, so the harness's normal map shows the moss relief).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.abspath(os.path.join(HERE, '..', 'layers'))
if LAYERS not in sys.path:
    sys.path.insert(0, LAYERS)
import layer_interface as li  # noqa: E402
import layout  # noqa: E402
import moss  # noqa: E402
import damage  # noqa: E402
import colour_and_fade  # noqa: E402


def build_node_group(parameters):
    parameters = dict(parameters or {})
    tiles = int(parameters.get('recipe.tiles_across', 1))
    parameters['recipe.tiles_across'] = tiles
    view = parameters.get('view', 'colour')
    shift = parameters.get('shift') or (0.0, 0.0)
    tree, b = li.make_plain_group('MOSS test', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    vector = b.input('Vector')
    if shift[0] or shift[1]:
        vector = b.vmath('ADD', vector, (float(shift[0]), float(shift[1]), 0.0))
    layout_node = b.node('ShaderNodeGroup')
    layout_node.node_tree = layout.build_group(parameters)
    layout_node.label = 'LAYOUT'
    b.tree.links.new(vector, layout_node.inputs['Vector'])

    def make_layer(module):
        node = b.node('ShaderNodeGroup')
        node.node_tree = module.build_group(parameters)
        node.label = module.GROUP_NAME
        b.tree.links.new(vector, node.inputs['Vector'])
        node.inputs['Tile Count'].default_value = float(tiles)
        for name in li.BUNDLE_NAMES:
            b.tree.links.new(layout_node.outputs[name], node.inputs[name])
        return node

    moss_node = make_layer(moss)
    use_damage = bool(parameters.get('damage'))
    if use_damage:
        damage_node = make_layer(damage)
        b.tree.links.new(damage_node.outputs['Mask'], moss_node.inputs['Damage Mask'])
    if parameters.get('base', 'flat') == 'paint':
        base_node = make_layer(colour_and_fade)
        base_colour = base_node.outputs['Colour']
    else:
        base_colour = li.rt.srgb_hex_to_linear(parameters.get('flat_colour', '#444c53'))
    joint = parameters.get('joint_colour', '#0c0e11')
    height = b.add(layout_node.outputs['base_height'], moss_node.outputs['Height'])
    roughness = b.add(0.8, moss_node.outputs['Roughness'])
    if use_damage and parameters.get('order') == 'moss_on_top':          # moss painted OVER the damage (the other stack order)
        colour = b.mix(base_colour, damage_node.outputs['Colour'], damage_node.outputs['Mask'])
        colour = b.mix(colour, moss_node.outputs['Colour'], moss_node.outputs['Mask'])
    else:                                                                # the real stack order: moss, then damage over it
        colour = b.mix(base_colour, moss_node.outputs['Colour'], moss_node.outputs['Mask'])
        if use_damage:
            colour = b.mix(colour, damage_node.outputs['Colour'], damage_node.outputs['Mask'])
    if use_damage:
        height = b.add(height, damage_node.outputs['Height'])
        roughness = b.add(roughness, damage_node.outputs['Roughness'])
    colour = b.mix(joint, colour, layout_node.outputs['piece_mask'])
    if view == 'joints':
        colour = b.grey_to_colour(layout_node.outputs['piece_mask'])
    elif view == 'mask':
        colour = b.grey_to_colour(moss_node.outputs['Mask'])
    elif view == 'height':
        colour = b.grey_to_colour(b.add(0.5, b.mul(moss_node.outputs['Height'], 5.0)))
    elif view == 'roughness':
        colour = b.grey_to_colour(b.add(0.5, b.mul(moss_node.outputs['Roughness'], 2.0)))
    elif view == 'moss_only':
        colour = b.mix((0.0, 0.0, 0.0, 1.0), moss_node.outputs['Colour'], moss_node.outputs['Mask'])
    elif view == 'damage_mask' and use_damage:
        colour = b.grey_to_colour(damage_node.outputs['Mask'])
    elif view.startswith('bundle_'):
        colour = b.grey_to_colour(layout_node.outputs[view[len('bundle_'):]])
    b.output('Colour', colour)
    b.output('Height', height)
    b.output('Roughness', roughness)
    b.output('Metallic', 0.0)
    return tree
