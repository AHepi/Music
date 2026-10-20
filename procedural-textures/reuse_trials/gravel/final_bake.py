# What this does (plain words): the like-for-like bake of the gravel trial. In ONE Blender run it bakes several "sets" of the recipe (the same
# settings with different seeds, or one setting changed), each at full size: colour.png (what you see), height.png (16 bit, exact), roughness.png
# and metallic.png, into OUT_ROOT/<set name>/, plus bake.json with the settings changes and the seconds taken. It uses the bake harness's own
# scene and "photograph one output" materials (lib/bake_harness.py), but skips the harness's two normal maps: the normal map is made
# afterwards from the height with recipes/slate_layers/integration/make_normal.py at the gravel reference strength (10), as the task asks.
# Use: blender -b --disable-autoexec -t 2 --python final_bake.py -- OUT_ROOT SIZE 'JSON {set name: {setting: value}}' [maps, e.g. height]
# (the optional last word bakes only those maps for every set; a single set can also carry '_maps': 'height' to bake only that map for that set;
#  bake.json is then written as bake_<maps>.json so the first record is kept)
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
out_root, size, sets = arguments[0], int(arguments[1]), json.loads(arguments[2])
wanted_default = arguments[3].split(',') if len(arguments) > 3 else ['colour', 'height', 'roughness', 'metallic']
recipe = bh.load_recipe(os.path.join(HERE, 'gravel_recipe.py'))
scene, tile = bh.new_bake_scene(size)
for name, parameters in sets.items():
    if name.startswith('_'):
        continue                                                      # a name starting with an underscore is a note
    folder = os.path.join(out_root, name)
    os.makedirs(folder, exist_ok=True)
    started = time.time()
    parameters = dict(parameters)
    wanted = parameters.pop('_maps').split(',') if '_maps' in parameters else wanted_default     # a set may ask for its own maps: '_maps': 'height'
    group = recipe.build_node_group(parameters)
    seconds = {}
    for channel, file_name, linear, sixteen in (('Colour', 'colour', False, False), ('Height', 'height', True, True),
                                                ('Roughness', 'roughness', True, False), ('Metallic', 'metallic', True, False)):
        if file_name not in wanted:
            continue
        channel_started = time.time()
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        bh.render_to(scene, os.path.join(folder, file_name + '.png'), linear, sixteen)
        seconds[file_name] = round(time.time() - channel_started, 1)
        print('[set]', name, file_name, seconds[file_name], 'seconds', flush=True)
    with open(os.path.join(folder, 'bake.json' if len(wanted) == 4 else 'bake_' + '_'.join(wanted) + '.json'), 'w') as handle:
        json.dump({'_what_this_is': 'How the final pictures of this set were baked: size, samples, the settings changed from settings.json, and the seconds each map took (made by final_bake.py).', 'size': size, 'samples': scene.cycles.samples, 'changes_to_settings_json': parameters, 'seconds': seconds,
                   'total_seconds': round(time.time() - started, 1), 'normal': 'made afterwards by make_normal.py, strength 10'}, handle, indent=1)
print('[final bake done]', flush=True)
