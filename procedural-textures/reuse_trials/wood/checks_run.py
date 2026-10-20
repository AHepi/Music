# What this does (plain words): all the PROOF pictures of the wood trial in ONE Blender run (the machine is shared, so one start instead of many).
# It only bakes pictures and counts nodes; checks_analyse.py (plain Python) then measures the pictures. Four parts (a copy of the brick trial's
# checks_run.py with the wood layers):
#   1. HALF-TILE TEST (512 dots): the recipe as it is and slid by half a picture (parameter shift = [0.5, 0.5]), for one base tile across and
#      (finished colour only) for two: the finished colour, a random colour per board, and the exact (16 bit) edge distance and the CRACKS,
#      KNOTS and GRAIN masks. If the tile repeats exactly, the slid picture equals the plain picture rolled by half its size.
#   2. LAYER MASKS (627 dots): each layer's Mask on the wood layout, for the picture sheet.
#   3. SWITCH-OFF TEST (320 dots): the finished colour and exact height as they are, then with each layer's Amount set to 0, plus each layer's own
#      Mask (exact, 16 bit). A layer switched off must change nothing outside its own mask.
#   4. NODE COUNT: builds the recipe once and counts the nodes in every box (shared boxes and new boxes).
# Use: blender -b --disable-autoexec -t 2 --python checks_run.py -- OUT_ROOT [parts, e.g. 1,2,3,4]
import collections
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402
import bpy  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
out_root = arguments[0]
parts = [int(p) for p in (arguments[1] if len(arguments) > 1 else '1,2,3,4').split(',')]
recipe = bh.load_recipe(os.path.join(HERE, 'wood_recipe.py'))
LAYERS = ['colour_and_fade', 'grain', 'moss', 'damage', 'cracks', 'knots', 'outline_and_shadow']


def photograph(scene, tile, parameters, path_stem, channels):
    group = recipe.build_node_group(parameters)
    for channel in channels:
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        suffix = {'Colour': '_colour.png', 'Height': '_height.png', 'Roughness': '_roughness.png'}[channel]
        bh.render_to(scene, path_stem + suffix, channel != 'Colour', channel == 'Height')


started = time.time()
if 1 in parts:
    folder = os.path.join(out_root, 'half_tile')
    os.makedirs(folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(512)
    for tiles in (1, 2):
        for shift_name, shift in (('plain', None), ('shifted', [0.5, 0.5])):
            base = {'recipe.tiles_across': tiles}
            if shift:
                base['shift'] = shift
            stem = os.path.join(folder, f't{tiles}_{shift_name}_')
            photograph(scene, tile, base, stem + 'finished', ['Colour'])
            if tiles == 1:
                photograph(scene, tile, dict(base, debug_view='bundle.piece_colour'), stem + 'pieces', ['Colour'])
                photograph(scene, tile, dict(base, debug_view='bundle.edge_distance'), stem + 'edge_distance', ['Height'])
                for layer in ('cracks', 'knots', 'grain'):
                    photograph(scene, tile, dict(base, debug_view=f'{layer}.mask'), stem + f'{layer}_mask', ['Height'])
            print('[half tile]', tiles, shift_name, round(time.time() - started), flush=True)
if 2 in parts:
    folder = os.path.join(out_root, 'masks')
    os.makedirs(folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(627)
    views = {'bundle_pieces': 'bundle.piece_colour', 'colour_and_fade_colour': 'colour_and_fade.colour'}
    views.update({f'{layer}_mask': f'{layer}.mask' for layer in LAYERS})
    for name, view in views.items():
        photograph(scene, tile, {'debug_view': view}, os.path.join(folder, name), ['Colour'])
    print('[masks]', round(time.time() - started), flush=True)
if 3 in parts:
    folder = os.path.join(out_root, 'switch_off')
    os.makedirs(folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(320)
    channels = ['Colour', 'Height']
    photograph(scene, tile, {}, os.path.join(folder, 'base'), channels)
    for layer in LAYERS:
        photograph(scene, tile, {'debug_view': f'{layer}.mask'}, os.path.join(folder, f'mask_{layer}'), ['Height'])
        photograph(scene, tile, {f'{layer}.amount': 0.0}, os.path.join(folder, f'{layer}_amount_0'), channels)
    print('[switch off]', round(time.time() - started), flush=True)
if 4 in parts:
    tree = recipe.build_node_group({})
    counts = {}

    def walk(group, label):
        kinds = collections.Counter(node.bl_idname.replace('ShaderNode', '') for node in group.nodes)
        inner = {}
        for node in group.nodes:
            if node.bl_idname == 'ShaderNodeGroup' and node.node_tree is not None:
                inner.setdefault(node.node_tree.name.split('.')[0], node.node_tree)
        counts[label] = {'nodes': len(group.nodes), 'kinds': dict(kinds.most_common(10)),
                         'boxes_inside': dict(collections.Counter(node.node_tree.name.split('.')[0] for node in group.nodes
                                                                   if node.bl_idname == 'ShaderNodeGroup' and node.node_tree is not None))}
        for name, sub in inner.items():
            if name not in counts:
                walk(sub, name)
    walk(tree, 'WOOD (top: the recipe wiring)')
    with open(os.path.join(out_root, 'node_counts.json'), 'w') as handle:
        json.dump(counts, handle, indent=1)
    for name, row in counts.items():
        print('[nodes]', name, row['nodes'], row['boxes_inside'], flush=True)
print('[checks done]', round(time.time() - started), 'seconds', flush=True)
