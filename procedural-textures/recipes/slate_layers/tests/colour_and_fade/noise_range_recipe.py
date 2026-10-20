# What this file does (plain words): a tiny recipe that outputs one Noise Texture value as the Height (exact, 16 bit), so the spread of
# Blender's noise (2D, 3D, 4D, 1D and the project's seamless one) can be measured with python (noise_ranges.py). Only a measuring tool.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'layers'))
import layer_interface as li


def build_node_group(parameters):
    tree, b = li.make_plain_group('noise range', [('Vector', 'vector', (0, 0, 0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    dims = parameters.get('dims', '2D')
    detail = float(parameters.get('detail', 0.0))
    u, v, _ = b.xyz(b.input('Vector'))
    place = b.vec(b.mul(u, 1000.0), b.mul(v, 1000.0), 3.7)
    if dims == '1D':
        node = b.noise(None, 1.0, detail, 0.5, 0.0, b.mul(u, 1000.0), '1D')
    elif dims == 'seamless':
        value = b.tileable_noise(b.input('Vector'), 40.0, detail, 0.5, 3.0)
        node = None
    else:
        node = b.noise(place, 1.0, detail, 0.5, 0.0, b.mul(v, 17.0) if dims == '4D' else None, dims)
    value = node.outputs['Factor'] if node is not None else value
    b.output('Height', value)
    b.output('Colour', b.grey_to_colour(value))
    b.output('Roughness', 0.5)
    b.output('Metallic', 0.0)
    return tree
