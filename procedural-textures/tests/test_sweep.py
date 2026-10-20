# What this does: tests the sweep tools by showing seamless noise at several Detail values.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import bpy
import recipe_tools as rt
import sweep_tools as st
def build(detail):
    tree, w = rt.make_group_tree(f'sweep {detail}', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeGroup', 'n', x=0); w.nodes['n'].node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', 'n', 'Vector')
    w.nodes['n'].inputs['Scale'].default_value = 5.0; w.nodes['n'].inputs['Detail'].default_value = detail
    w.link('n', 'Color', 'out', 'Colour')
    return tree
st.render_sweep(build, [0, 1, 3, 6, 12], 'out/test_sweep', 'Colour', 256, [f'Detail {d}' for d in (0, 1, 3, 6, 12)])
