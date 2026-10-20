# What this does (plain words): the verifier's own bake for the independence check. For each named variant (a dict of settings laid over
# settings.json), it builds the slate recipe in Blender and photographs, with the lib bake harness building blocks only:
#   final colour (8-bit sRGB), final height (16-bit), final roughness (16-bit),
#   and the masks of four layers plus piece_id, each through the recipe's debug_view, read from the 16-bit Height output.
# Use: blender -b --disable-autoexec -t 2 --python bake_variants.py -- OUT_FOLDER SIZE 'JSON {variant: {settings}}'
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

RECIPE = os.path.join(PROC, 'recipes', 'slate_layers', 'recipe', 'slate_recipe.py')
MASK_VIEWS = ['colour_and_fade.mask', 'damage.mask', 'moss.mask', 'outline_and_shadow.mask', 'bundle.piece_id']

arguments = sys.argv[sys.argv.index('--') + 1:]
out_folder, size, variants = arguments[0], int(arguments[1]), json.loads(arguments[2])
os.makedirs(out_folder, exist_ok=True)
recipe = bh.load_recipe(RECIPE)
scene, tile = bh.new_bake_scene(size)


def shoot(group, channel, path, linear, sixteen):
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    bh.render_to(scene, path, linear, sixteen)


for name, settings in variants.items():
    folder = os.path.join(out_folder, name)
    os.makedirs(folder, exist_ok=True)
    group = recipe.build_node_group(dict(settings))
    shoot(group, 'Colour', os.path.join(folder, 'colour.png'), False, False)
    shoot(group, 'Height', os.path.join(folder, 'height.png'), True, True)
    shoot(group, 'Roughness', os.path.join(folder, 'roughness.png'), True, True)
    for view in MASK_VIEWS:
        params = dict(settings)
        params['debug_view'] = view
        params['debug_scale'] = 1.0
        group = recipe.build_node_group(params)
        shoot(group, 'Height', os.path.join(folder, 'mask_' + view.replace('.', '_') + '.png'), True, True)
    print('[verify] baked', name, flush=True)
