# What this does: tests, for "06 Guide - the painted look.md", an outline idea that was only READ about before (the Ucupaint research,
# "transition ramp": a dark band where a soft mask goes from 0 to 1). Nothing like it had been run in this project.
# The recipe, all shader nodes, all seamless:
#   seamless noise (lib recipe_tools.tileable_noise_group, Scale 3, Detail 2, Seed 7)
#   -> Map Range from (0.5 - softness) .. (0.5 + softness) to 0 .. 1 = the soft mask m (0 on one side, 1 on the other, a soft edge between)
#   -> patch colour: brick red where m > 0.5, mortar brown where not (two flat patches)
#   -> band = 1 - |2 m - 1|  (1 exactly on the edge, falling to 0 where the mask is fully 0 or 1)
#   -> line = band greater than (1 - share)   ("share" = how much of the soft edge is painted dark; 0 = no line)
#   -> Mix the dark outline colour in where line = 1.
# Outputs: Colour, and Height = the mask m itself (used only to MEASURE where the patch edge is).
# Writes: work/outline_band_share/ (256-dot squares for the strip, sweep.json), work/outline_band_measure/ (512-dot colour + 16-bit mask per
# setting, for finish_strips.py to measure the line width), and work/outline_band_softness/ (a second, smaller sweep of the softness).
# Run: blender -b --disable-autoexec -t 2 --python make_painted_strips.py
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))

import bpy  # noqa: E402

import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402
import sweep_tools as st  # noqa: E402

WORK = os.path.join(HERE, 'work')
BRICK = rt.srgb_hex_to_linear('#a34d2d')     # colours from the measured brick palette (hand-painted research, section 2.1)
MORTAR = rt.srgb_hex_to_linear('#775e49')
DARK = rt.srgb_hex_to_linear('#2b201b')
SHARES = [0.0, 0.1, 0.25, 0.5, 1.0]
SOFTNESS = 0.05


def build(share, softness=SOFTNESS):
    tree, w = rt.make_group_tree(f'outline band {share} {softness}', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeGroup', 'noise', x=0)
    w.nodes['noise'].node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', 'noise', 'Vector')
    for socket, value in (('Scale', 3.0), ('Detail', 2.0), ('Seed', 7.0)):
        w.nodes['noise'].inputs[socket].default_value = value
    w.add('ShaderNodeMapRange', 'mask', x=1, clamp=True, From__Min=0.5 - softness, From__Max=0.5 + softness, To__Min=0.0, To__Max=1.0)
    w.link('noise', 'Fac', 'mask', 'Value')
    w.math('side', 'GREATER_THAN', None, 0.5, x=2, y=1)
    w.link('mask', 'Result', 'side', 0)
    w.add('ShaderNodeMix', 'patch', x=3, y=1, data_type='RGBA')
    w.link('side', 0, 'patch', 'Factor')
    w.nodes['patch'].inputs['A'].default_value = MORTAR
    w.nodes['patch'].inputs['B'].default_value = BRICK
    w.math('twice minus one', 'MULTIPLY_ADD', None, 2.0, -1.0, x=2, y=-1)
    w.link('mask', 'Result', 'twice minus one', 0)
    w.math('distance from edge', 'ABSOLUTE', x=3, y=-1)
    w.link('twice minus one', 0, 'distance from edge', 0)
    w.math('band', 'SUBTRACT', 1.0, None, x=4, y=-1)
    w.link('distance from edge', 0, 'band', 1)
    w.math('line', 'GREATER_THAN', None, 1.0 - share, x=5, y=-1)
    w.link('band', 0, 'line', 0)
    w.add('ShaderNodeMix', 'outlined', x=6, data_type='RGBA')
    w.link('line', 0, 'outlined', 'Factor')
    w.link('patch', 'Result', 'outlined', 'A')
    w.nodes['outlined'].inputs['B'].default_value = DARK
    w.link('outlined', 'Result', 'out', 'Colour')
    w.link('mask', 'Result', 'out', 'Height')
    return tree


def measure_renders():
    folder = os.path.join(WORK, 'outline_band_measure')
    os.makedirs(folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(512)
    scene.cycles.samples = 1          # one sample: every dot is either line or not, so the counting is exact
    done = []
    for share in SHARES:
        group = build(share)
        for channel, linear, sixteen in (('Colour', False, False), ('Height', True, True)):
            tile.data.materials.clear()
            tile.data.materials.append(bh.show_channel_material(group, channel))
            path = os.path.join(folder, f'share_{share}_{channel.lower()}.png')
            bh.render_to(scene, path, linear, sixteen)
            done.append(os.path.basename(path))
    with open(os.path.join(folder, 'renders.json'), 'w') as handle:
        json.dump({'size': 512, 'samples': 1, 'softness': SOFTNESS, 'shares': SHARES, 'files': done}, handle, indent=1)


if __name__ == '__main__':
    st.render_sweep(lambda share: build(share), SHARES, os.path.join(WORK, 'outline_band_share'), channel='Colour', size=256,
                    labels=[('share 0 (no line)' if s == 0 else f'share {s}') for s in SHARES])
    softness_values = [0.02, 0.05, 0.12]
    st.render_sweep(lambda soft: build(0.25, soft), softness_values, os.path.join(WORK, 'outline_band_softness'), channel='Colour', size=256,
                    labels=[f'softness {s}, share 0.25' for s in softness_values])
    measure_renders()
    print('done')
