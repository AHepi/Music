# What this does (plain words): times the recipe. Inside Blender it (1) builds the node groups and counts their nodes, (2) photographs the
# Colour picture and the Height picture at 1254 dots (4 samples, the harness setting), for the whole recipe and for the LAYOUT alone
# (debug view bundle.gap_mask), and (3) the same for a 2 x 2 area of new content (recipe.tiles_across = 2, 2508 dots).
# Times are wall-clock seconds on 2 threads, shared with other jobs, so treat them as rough.
# Use: blender -b --disable-autoexec -t 2 --python time_it.py -- OUT_JSON
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bake_tools as bt  # noqa: E402

bh = bt.bh
os.makedirs(os.path.join(HERE, 'run_logs'), exist_ok=True)
out = sys.argv[sys.argv.index('--') + 1]
recipe = bh.load_recipe(os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'))
rows = []
for label, size, params in (('whole recipe, one tile', 1254, {}), ('layout alone (bundle.gap_mask), one tile', 1254, {'debug_view': 'bundle.gap_mask'}),
                            ('whole recipe, 2 x 2 area of new content (tiles_across 2)', 2508, {'recipe.tiles_across': 2})):
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = 4
    start = time.time()
    group = recipe.build_node_group(params)
    build_seconds = time.time() - start
    counts = {}
    for node in group.nodes:
        if node.bl_idname == 'ShaderNodeGroup':
            counts[node.label or node.node_tree.name] = len(node.node_tree.nodes)
    row = {'what': label, 'size': size, 'build seconds': round(build_seconds, 2), 'nodes per box': counts}
    for channel in ('Colour', 'Height'):
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        start = time.time()
        bh.render_to(scene, os.path.join(HERE, 'run_logs', 'time_it_picture.png'), channel != 'Colour', channel == 'Height')
        row[f'{channel} render seconds'] = round(time.time() - start, 1)
    rows.append(row)
    print('TIMING', json.dumps(row), flush=True)
with open(out, 'w') as handle:
    json.dump(rows, handle, indent=1)
