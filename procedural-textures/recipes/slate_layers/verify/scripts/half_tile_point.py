# What this does (plain words): the verifier's STRICT half-tile test. It bakes the recipe twice at SIZE dots, once as it is and once slid by half a
# picture (the recipe's 'shift' parameter), with POINT SAMPLING (1 sample per dot, a tiny pixel filter, so every dot is the recipe's value at the
# dot's centre and there is no anti-aliasing jitter that differs from dot to dot). If the recipe wraps exactly, the shifted picture equals the first
# one rolled by half, dot for dot, up to floating-point rounding. Pictures: colour (8-bit), height (16-bit), and the four layer masks + piece_id.
# Use: blender -b --disable-autoexec -t 2 --python half_tile_point.py -- OUT_FOLDER SIZE TILES_ACROSS
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

RECIPE = os.path.join(PROC, 'recipes', 'slate_layers', 'recipe', 'slate_recipe.py')
VIEWS = ['colour_and_fade.mask', 'damage.mask', 'moss.mask', 'outline_and_shadow.mask', 'bundle.piece_id']
arguments = sys.argv[sys.argv.index('--') + 1:]
out_folder, size, tiles = arguments[0], int(arguments[1]), int(arguments[2])
os.makedirs(out_folder, exist_ok=True)
recipe = bh.load_recipe(RECIPE)
scene, tile = bh.new_bake_scene(size)
scene.cycles.samples = 1
scene.cycles.filter_width = 0.01          # point sampling: every sample lands (almost) on the dot centre
try:
    scene.cycles.seed = 0
except Exception:
    pass


def shoot(group, channel, path, linear, sixteen):
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    bh.render_to(scene, path, linear, sixteen)


for name, shift in (('plain', None), ('shifted', [0.5, 0.5])):
    base = {'recipe.tiles_across': tiles}
    if shift:
        base['shift'] = shift
    group = recipe.build_node_group(dict(base))
    shoot(group, 'Colour', os.path.join(out_folder, f'{name}_colour.png'), False, False)
    shoot(group, 'Height', os.path.join(out_folder, f'{name}_height.png'), True, True)
    for view in VIEWS:
        params = dict(base)
        params['debug_view'] = view
        params['debug_scale'] = 1.0
        group = recipe.build_node_group(params)
        shoot(group, 'Height', os.path.join(out_folder, f'{name}_mask_{view.replace(".", "_")}.png'), True, True)
    print('[verify] half tile baked', name, flush=True)
