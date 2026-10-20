# What this does (plain words): the independent checker re-bakes the FINISHED COLOUR of one trial's seed set 1 at full size (1254 dots) from the
# trial's recipe and settings (the settings changes are read from the trial's own final/seeds_1/bake.json), into verify/rebake/SURFACE/colour.png,
# so that rebake_compare.py can check that the stored colour.png really is what the recipe makes (nothing painted over or edited by hand).
# Use: blender -b --disable-autoexec -t 2 --python rebake_colour.py -- SURFACE [height|heightonly] [--extra JSON --tag NAME]
#   (height = bake the height too; heightonly = only the height; --extra changes more settings and --tag puts the pictures in rebake/SURFACE_NAME)
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
surface = arguments[0]
with_height = 'height' in arguments[1:]
only_height = 'heightonly' in arguments[1:]
extra = json.loads(arguments[arguments.index('--extra') + 1]) if '--extra' in arguments else {}     # settings changed on top of the trial's seed set 1
tag = arguments[arguments.index('--tag') + 1] if '--tag' in arguments else ''                        # output goes to rebake/SURFACE_TAG
RECIPE_FILES = {'brick': 'brick_recipe.py', 'wood': 'wood_recipe.py', 'metal': 'metal_recipe.py', 'mud': 'mud_recipe.py', 'gravel': 'gravel_recipe.py'}
trial = os.path.join(PROC, 'reuse_trials', surface)
changes = json.load(open(os.path.join(trial, 'final', 'seeds_1', 'bake.json')))['changes_to_settings_json']
out_folder = os.path.join(HERE, 'rebake', surface + ('_' + tag if tag else ''))
os.makedirs(out_folder, exist_ok=True)
recipe = bh.load_recipe(os.path.join(trial, RECIPE_FILES[surface]))
scene, tile = bh.new_bake_scene(1254)
changes = dict(changes, **extra)
group = recipe.build_node_group(dict(changes))
started = time.time()
for channel, name, linear, sixteen in (('Colour', 'colour', False, False), ('Height', 'height', True, True)):
    if name == 'height' and not (with_height or only_height):
        continue
    if name == 'colour' and only_height:
        continue
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    bh.render_to(scene, os.path.join(out_folder, name + '.png'), linear, sixteen)
    print('[rebake]', surface, name, round(time.time() - started), 's', flush=True)
print('[rebake done]', flush=True)
