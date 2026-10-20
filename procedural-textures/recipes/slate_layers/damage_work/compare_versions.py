# What this does (plain words): compares the first (slower) version of the DAMAGE layer (damage_v1_slower.py, a saved copy) with the current
# layers/damage.py: (1) the same zoomed window drawn with each, to see whether making the layer cheaper changed the look, and (2) the time of a
# colour picture with no damage layer / the first version / the current version, alternating twice (the first picture of a run includes
# compiling the shader, so look at round 1). The computer is shared with other helpers, so only the differences between the three matter.
# Use (inside Blender):  blender -b --disable-autoexec -t 2 --python compare_versions.py -- OUT_FOLDER TIMING_PIXELS
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'layers'))
import bake_harness as bh  # noqa: E402

out, pixels = sys.argv[sys.argv.index('--') + 1], int(sys.argv[sys.argv.index('--') + 2])
os.makedirs(out, exist_ok=True)
recipe = bh.load_recipe(os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'))
current = recipe.LAYER_MODULES['damage']
spec = importlib.util.spec_from_file_location('damage_v1_slower', os.path.join(HERE, 'damage_v1_slower.py'))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

# (1) the look, same window
scene, tile = bh.new_bake_scene(500)
scene.camera.location = (0.2, 0.354, 5.0)
scene.camera.data.ortho_scale = 0.4
for name, module in (('v1_slower', old), ('current', current)):
    recipe.LAYER_MODULES['damage'] = module
    group = recipe.build_node_group({})
    tile.data.materials.clear()
    tile.data.materials.append(bh.show_channel_material(group, 'Colour'))
    bh.render_to(scene, os.path.join(out, f'look_{name}.png'), False, False)

# (2) the time
scene, tile = bh.new_bake_scene(pixels)
results = []
for round_index in range(2):
    for name, module, params in (('no damage layer', current, {'recipe.stack_order': 'colour_and_fade,moss,outline_and_shadow'}), ('v1_slower', old, {}), ('current', current, {})):
        recipe.LAYER_MODULES['damage'] = module
        group = recipe.build_node_group(dict(params))
        tile.data.materials.clear()
        tile.data.materials.append(bh.show_channel_material(group, 'Colour'))
        started = time.time()
        bh.render_to(scene, os.path.join(out, 'tmp.png'), False, False)
        results.append({'round': round_index, 'variant': name, 'seconds': round(time.time() - started, 1)})
        print(results[-1], flush=True)
json.dump({'pixels': pixels, 'colour_picture_seconds': results}, open(os.path.join(out, 'timing_versions.json'), 'w'), indent=1)
os.remove(os.path.join(out, 'tmp.png'))
