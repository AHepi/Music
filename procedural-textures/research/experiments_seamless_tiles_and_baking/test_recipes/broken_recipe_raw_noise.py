# What this does: a deliberately BROKEN recipe used to prove that recipe_tiling_test.py catches a seam: it uses Blender's plain 3D Noise (not seamless).
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'lib'))
import recipe_tools as rt

def build_node_group(parameters):
    tree, w = rt.make_group_tree('Broken recipe', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeTexNoise', 'noise', noise_dimensions='3D', noise_type='FBM', normalize=True, Scale=5.0, Detail=4.0)
    w.link('in', 'Vector', 'noise', 'Vector')
    w.link('noise', 'Color', 'out', 'Colour')
    w.link('noise', 'Fac', 'out', 'Height')
    w.math('rough', 'ADD', 0.7, 0.0)
    w.link('rough', 0, 'out', 'Roughness')
    w.math('metal', 'ADD', 0.0, 0.0)
    w.link('metal', 0, 'out', 'Metallic')
    return tree
