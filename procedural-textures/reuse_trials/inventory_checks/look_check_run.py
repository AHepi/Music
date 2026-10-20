# What this does (plain words): runs the LOOK CHECK (look_check_recipe.py next to this file) in ONE Blender run and saves only the colour picture of
# each view (512 dots, 4 samples) into the folder look_check/ next to this file, then writes look_check/timing.json. Nothing outside this folder is written
# (the cache-folder switch is set before anything is imported).
# Use: blender -b --disable-autoexec -t 2 --python reuse_trials/inventory_checks/look_check_run.py
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

VIEWS = {
    'wood_plain_colour_and_fade_only': {'layout': 'wood_plain', 'only': 'colour_and_fade'},
    'wood_turned_colour_and_fade_only': {'layout': 'wood_turned', 'only': 'colour_and_fade'},
    'wood_turned_all_layers': {'layout': 'wood_turned'},
    'brick_b1_colour_and_fade_only': {'layout': 'brick', 'style': 'b1', 'only': 'colour_and_fade'},
    'brick_flat_colour_and_fade_only': {'layout': 'brick', 'style': 'flat', 'only': 'colour_and_fade'},
    'brick_flat_all_layers': {'layout': 'brick', 'style': 'flat'},
}
OUT = os.path.join(HERE, 'look_check')
os.makedirs(OUT, exist_ok=True)
recipe = bh.load_recipe(os.path.join(HERE, 'look_check_recipe.py'))
scene, tile = bh.new_bake_scene(512)
scene.cycles.samples = 4
timing = {}
for name, parameters in VIEWS.items():
    started = time.time()
    group = recipe.build_node_group(parameters)
    material = bh.show_channel_material(group, 'Colour')
    tile.data.materials.clear()
    tile.data.materials.append(material)
    bh.render_to(scene, os.path.join(OUT, name + '_colour.png'), False, False)
    timing[name] = round(time.time() - started, 1)
    print('[look check]', name, timing[name], 's')
with open(os.path.join(OUT, 'timing.json'), 'w') as handle:
    json.dump({'size': 512, 'samples': 4, 'seconds_per_view': timing}, handle, indent=1)
