# What this does: the EXACT "does my recipe tile?" test, for a recipe written for lib/bake_harness.py (a Python file with build_node_group(parameters) that returns a node group
# with input 'Vector' and outputs 'Colour', 'Roughness', 'Metallic', 'Height'). It photographs every output of the recipe five times: normally, and with the tile coordinate moved by
# one whole tile to the right, up, both, and by (-3, +2) tiles. A recipe that really repeats every 1.0 gives the same picture every time. It prints, for each output, the average and the
# biggest difference (picture values 0..1) and a verdict. It also prints the usual seam ratio of the normal picture.
#   PASS  the picture does not change when moved by whole tiles: the pattern repeats exactly.
#   FAIL  it changes: the pattern does not repeat. The seam you see in the 2 x 2 tile preview comes from this.
# Limits (found by testing): (1) a recipe that is only defined inside 0..1 (cross-fade repairs clamp the coordinate) cannot pass this test but may still be seamless - judge it by the
# seam picture; (2) whole bricks that never touch the tile edge may get a new random colour when moved by a tile; that is a FAIL here although the picture can look fine, so also look at it.
# Run:  blender -b --disable-autoexec -t 2 --python recipe_tiling_test.py -- RECIPE.py [--size 256] [--params '{"seed": 3}']
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
recipe_path = arguments[0]
option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
size = int(option('--size', 256))
parameters = json.loads(option('--params', '{}'))
OFFSETS = {'unmoved': (0, 0, 0), 'one tile right': (1, 0, 0), 'one tile up': (0, 1, 0), 'one tile right and up': (1, 1, 0), 'three left, two up': (-3, 2, 0)}
CHANNELS = ('Colour', 'Roughness', 'Metallic', 'Height')

scene, tile = bh.new_bake_scene(size)
recipe = bh.load_recipe(recipe_path)
group = recipe.build_node_group(dict(parameters))
present = [c for c in CHANNELS if c in [s.name for s in group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT']]


def shifted(inner, offset, name):
    types = {'Colour': 'NodeSocketColor', 'Roughness': 'NodeSocketFloat', 'Metallic': 'NodeSocketFloat', 'Height': 'NodeSocketFloat'}
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [(c, types[c]) for c in present])
    w.vector_math('shift', 'ADD', x=1)
    w.nodes['shift'].inputs[1].default_value = offset
    w.link('in', 'Vector', 'shift', 0)
    node = w.add('ShaderNodeGroup', 'inner', x=2)
    node.node_tree = inner
    w.link('shift', 0, 'inner', 'Vector')
    for c in present:
        w.link('inner', c, 'out', c)
    return tree


pictures = {c: {} for c in present}
folder = os.path.join(HERE, 'out', 'recipe_tiling_test')
os.makedirs(folder, exist_ok=True)
for label, offset in OFFSETS.items():
    wrapper = shifted(group, offset, 'shifted ' + label)
    for channel in present:
        tile.data.materials.clear()
        tile.data.materials.append(bh.show_channel_material(wrapper, channel))
        path = os.path.join(folder, f'{channel}_{label.replace(" ", "_")}.png')
        bh.render_to(scene, path, channel != 'Colour', sixteen_bit=(channel != 'Colour'))
        pictures[channel][label] = bh.load_png_as_array(path)

print('\nTILING TEST for', recipe_path, 'at', size, 'px')
for channel in present:
    base = pictures[channel]['unmoved']
    worst_mean = worst_max = 0.0
    for label in list(OFFSETS)[1:]:
        difference = np.abs(base - pictures[channel][label])
        worst_mean, worst_max = max(worst_mean, float(difference.mean())), max(worst_max, float(difference.max()))
    grey = base.mean(axis=-1)
    inner = (np.abs(np.diff(grey, axis=1)).mean() + np.abs(np.diff(grey, axis=0)).mean()) / 2.0
    wrap = (np.abs(grey[:, 0] - grey[:, -1]).mean() + np.abs(grey[0, :] - grey[-1, :]).mean()) / 2.0
    verdict = 'PASS: repeats exactly' if worst_mean < 0.002 else 'FAIL: does not repeat (moved by whole tiles it looks different)'
    print(f'  {channel:10s} {verdict:70s} average difference {worst_mean:.5f}, biggest {worst_max:.3f}, seam ratio of the picture {wrap / max(inner, 1e-9):.2f}')
