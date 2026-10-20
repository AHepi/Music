# What this does: the smallest possible recipe (seamless noise as colour and height), used to test the bake harness end to end.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import recipe_tools as rt

DEFAULT_PARAMETERS = {'scale': 6.0, 'detail': 6.0, 'seed': 0.0}

def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    tree, w = rt.make_group_tree('Smoke recipe', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
    noise_group = rt.tileable_noise_group()
    w.add('ShaderNodeGroup', 'noise', x=0)
    w.nodes['noise'].node_tree = noise_group
    w.link('in', 'Vector', 'noise', 'Vector')
    w.nodes['noise'].inputs['Scale'].default_value = p['scale']
    w.nodes['noise'].inputs['Detail'].default_value = p['detail']
    w.nodes['noise'].inputs['Seed'].default_value = p['seed']
    w.add('ShaderNodeValToRGB', 'ramp', x=1)
    w.nodes['ramp'].color_ramp.elements[0].color = (0.1, 0.05, 0.02, 1)
    w.nodes['ramp'].color_ramp.elements[1].color = (0.8, 0.6, 0.3, 1)
    w.link('noise', 'Fac', 'ramp', 'Fac')
    w.link('ramp', 'Color', 'out', 'Colour')
    w.link('noise', 'Fac', 'out', 'Height')
    w.math('rough', 'ADD', 0.7, 0.0, x=1, y=-2)
    w.link('rough', 0, 'out', 'Roughness')
    w.math('metal', 'ADD', 0.0, 0.0, x=1, y=-3)
    w.link('metal', 0, 'out', 'Metallic')
    return tree
