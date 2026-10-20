# What this does (plain words): the like-for-like bake of the wood trial (a copy of the brick trial's final_bake.py with the recipe name changed).
# In ONE Blender run it bakes several "sets" of the recipe (the same settings with different seeds), each at full size: colour.png (what you see),
# height.png (16 bit, exact), roughness.png and metallic.png, into OUT_ROOT/<set name>/, plus bake.json with the settings changes and the seconds
# taken. It uses the bake harness's own scene and "photograph one output" materials (lib/bake_harness.py), but skips the harness's two normal maps:
# the normal map is made afterwards from the height with recipes/slate_layers/integration/make_normal.py at the wood reference strength (8).
# Use: blender -b --disable-autoexec -t 2 --python final_bake.py -- OUT_ROOT SIZE 'JSON {set name: {setting: value}}' [maps, e.g. height]
# (the optional last word bakes only those maps; bake.json is then written as bake_<maps>.json so the first record is kept)
# Two special keys may sit in a set's settings: "_height_filter": [type, width, samples] (for example ["GAUSSIAN", 2.0, 8]) renders the HEIGHT map
# (only) with that pixel filter and sample count instead of the harness's box filter of width 1 and 4 samples; a wider filter blurs the height a
# little, as the wood reference's height is blurred a little; the colour, roughness and metallic maps always use the harness's own filter.
# "_maps": "height" bakes only the maps named there for that set (the set's folder then gets bake_<maps>.json).
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
wanted = arguments[3].split(',') if len(arguments) > 3 else ['colour', 'height', 'roughness', 'metallic']
recipe = bh.load_recipe(os.path.join(HERE, 'wood_recipe.py'))
scene, tile = bh.new_bake_scene(size)
for name, parameters in sets.items():
    folder = os.path.join(out_root, name)
    os.makedirs(folder, exist_ok=True)
    started = time.time()
    parameters = dict(parameters)
    height_filter = parameters.pop('_height_filter', None)
    set_wanted = parameters.pop('_maps').split(',') if '_maps' in parameters else wanted
    group = recipe.build_node_group(parameters)
    seconds = {}
    for channel, file_name, linear, sixteen in (('Colour', 'colour', False, False), ('Height', 'height', True, True),
                                                ('Roughness', 'roughness', True, False), ('Metallic', 'metallic', True, False)):
        if file_name not in set_wanted:
            continue
        channel_started = time.time()
        if channel == 'Height' and height_filter:
            scene.cycles.pixel_filter_type, scene.cycles.filter_width, scene.cycles.samples = height_filter[0], float(height_filter[1]), int(height_filter[2])
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        bh.render_to(scene, os.path.join(folder, file_name + '.png'), linear, sixteen)
        scene.cycles.pixel_filter_type, scene.cycles.filter_width, scene.cycles.samples = 'BOX', 1.0, 4
        seconds[file_name] = round(time.time() - channel_started, 1)
        print('[set]', name, file_name, seconds[file_name], 'seconds', flush=True)
    with open(os.path.join(folder, 'bake.json' if len(set_wanted) == 4 else 'bake_' + '_'.join(set_wanted) + '.json'), 'w') as handle:
        json.dump({'size': size, 'samples': 4, 'height_filter': height_filter, 'changes_to_settings_json': parameters, 'seconds': seconds,
                   'total_seconds': round(time.time() - started, 1), 'normal': 'made afterwards by make_normal.py, strength 8'}, handle, indent=1)
print('[final bake done]', flush=True)
