# What this file does (plain words): checks in Blender whether a Voronoi set to "Smooth F1" with Smoothness 0 gives the same cells as plain
# "F1" (so Patch Hardness can use one node for both hard and soft cell edges). Height = how much the two cell colours differ at each dot.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'layers'))
import layer_interface as li


def build_node_group(parameters):
    tree, b = li.make_plain_group('voronoi smooth check', [('Vector', 'vector', (0, 0, 0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    u, v, _ = b.xyz(b.input('Vector'))
    place = b.vec(b.mul(u, 12.0), b.mul(v, 12.0), 0.0)
    outs = []
    for feature, smooth in (('F1', 0.0), ('SMOOTH_F1', float(parameters.get('smooth', 0.0)))):
        node = b.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature=feature, distance='EUCLIDEAN', normalize=False)
        b._put(node, 'Vector', place)
        b._put(node, 'Scale', 1.0)
        b._put(node, 'Randomness', 1.0)
        if feature == 'SMOOTH_F1':
            b._put(node, 'Smoothness', smooth)
        outs.append(b.channels(node.outputs['Color'])[0])
    difference = b.absolute(b.sub(outs[0], outs[1]))
    b.output('Height', difference)
    b.output('Colour', b.grey_to_colour(outs[1]))
    b.output('Roughness', 0.5)
    b.output('Metallic', 0.0)
    return tree
