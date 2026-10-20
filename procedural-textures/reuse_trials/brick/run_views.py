# What this does (plain words): bakes several quick "views" of the brick trial recipe in ONE Blender run (one Blender start, many pictures),
# for looking and hand-tuning. Each view is the recipe built with settings.json plus that view's own changes (for example a debug view of one
# layer, or one setting changed). It writes <view>_colour.png (and <view>_height.png, 16 bit, when asked) into the out folder, and the seconds
# each view took into timing.json. Nothing outside the out folder is written (the cache-folder switch is set before anything is imported).
# Use: blender -b --disable-autoexec -t 2 --python run_views.py -- OUT_FOLDER SIZE 'JSON {view name: {setting: value}}' [Colour,Height]
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
out_folder, size, views = arguments[0], int(arguments[1]), json.loads(arguments[2])
channels = arguments[3].split(',') if len(arguments) > 3 else ['Colour']
os.makedirs(out_folder, exist_ok=True)
recipe = bh.load_recipe(os.path.join(HERE, 'brick_recipe.py'))
scene, tile = bh.new_bake_scene(size)
scene.cycles.samples = 4
timing = {}
for name, parameters in views.items():
    started = time.time()
    group = recipe.build_node_group(parameters)
    for channel in channels:
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        suffix = {'Colour': '_colour', 'Height': '_height', 'Roughness': '_roughness'}[channel]
        bh.render_to(scene, os.path.join(out_folder, name + suffix + '.png'), channel != 'Colour', channel == 'Height')
    timing[name] = round(time.time() - started, 1)
    print('[view]', name, timing[name], 'seconds', flush=True)
with open(os.path.join(out_folder, 'timing.json'), 'w') as handle:
    json.dump({'size': size, 'samples': 4, 'seconds_per_view': timing}, handle, indent=1)
print('[views done]', flush=True)
