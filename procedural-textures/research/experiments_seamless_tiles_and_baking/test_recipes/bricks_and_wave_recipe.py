# What this does: a small recipe that uses the two tested seamless groups in tileable_pattern_groups.py (bricks with wrapped numbers, wavy bands), used to prove with
# recipe_tiling_test.py that every output repeats exactly: Colour from the per-brick random value, Height = brick mask x brick height, Roughness from the wave, Metallic 0.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
import recipe_tools as rt
import tileable_pattern_groups as tpg

def build_node_group(parameters):
    tree, w = rt.make_group_tree('Bricks and wave recipe', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
    bricks = w.add('ShaderNodeGroup', 'bricks')
    bricks.node_tree = tpg.tileable_bricks_group()
    w.link('in', 'Vector', 'bricks', 'Vector')
    wave = w.add('ShaderNodeGroup', 'wave')
    wave.node_tree = tpg.tileable_wave_group()
    w.link('in', 'Vector', 'wave', 'Vector')
    w.add('ShaderNodeValToRGB', 'ramp')
    ramp = w.nodes['ramp'].color_ramp
    ramp.elements[0].color, ramp.elements[1].color = (0.25, 0.05, 0.03, 1), (0.75, 0.30, 0.15, 1)
    w.link('bricks', 'Random', 'ramp', 'Fac')
    w.add('ShaderNodeMix', 'mortar colour', data_type='RGBA')
    w.nodes['mortar colour'].inputs['A'].default_value = (0.5, 0.48, 0.42, 1)      # Factor 0 = mortar
    w.link('bricks', 'Brick mask', 'mortar colour', 'Factor')
    w.link('ramp', 'Color', 'mortar colour', 'B')                                  # Factor 1 = brick
    w.link('mortar colour', 'Result', 'out', 'Colour')
    w.math('height', 'MULTIPLY_ADD', None, 0.4)
    w.nodes['height'].inputs[2].default_value = 0.0
    w.link('bricks', 'Random', 'height', 0)
    w.math('masked height', 'MULTIPLY')
    w.link('height', 0, 'masked height', 0)
    w.link('bricks', 'Brick mask', 'masked height', 1)
    w.math('plus', 'ADD', None, 0.2)
    w.link('masked height', 0, 'plus', 0)
    w.link('plus', 0, 'out', 'Height')
    w.math('rough', 'MULTIPLY_ADD', None, 0.3)
    w.nodes['rough'].inputs[2].default_value = 0.5
    w.link('wave', 'Fac', 'rough', 0)
    w.link('rough', 0, 'out', 'Roughness')
    w.math('metal', 'ADD', 0.0, 0.0)
    w.link('metal', 0, 'out', 'Metallic')
    return tree
