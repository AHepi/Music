# What this does: a tiny recipe (for the harness) that contains ONLY the LAYOUT group, so the layout can be looked at before any other
# layer exists. parameters['view'] picks what to show in the Colour output: 'piece_colour' (a random colour per slate), 'joints'
# (black joints on a grey slate) or any bundle name (shown as grey, scaled by parameters['scale']). The same number also goes to 'Height'
# (exact data, 16 bit).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'layers'))
import layer_interface as li
import layout


def build_node_group(parameters):
    tree, b = li.make_plain_group('layout test', [('Vector', 'vector', (0, 0, 0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    node = b.node('ShaderNodeGroup')
    node.node_tree = layout.build_group(parameters)
    b.tree.links.new(b.input('Vector'), node.inputs['Vector'])
    view = parameters.get('view', 'piece_colour')
    scale = float(parameters.get('scale', 1.0))
    if view == 'piece_colour':
        colour = b.hash4(b.vec(node.outputs['piece_id'], 0.5, 0.5), 2.5).outputs['Color']
        value = node.outputs['piece_id']
    elif view == 'joints':
        colour = b.mix((0.02, 0.02, 0.025), (0.25, 0.28, 0.3), node.outputs['piece_mask'])
        value = node.outputs['piece_mask']
    else:
        value = b.mul(node.outputs[view], scale)
        colour = b.grey_to_colour(value)
    b.output('Colour', colour)
    b.output('Height', value)
    b.output('Roughness', 0.5)
    b.output('Metallic', 0.0)
    return tree
