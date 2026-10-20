# What this does (plain words): all the PROOF pictures of the gravel trial in ONE Blender run (the machine is shared, so one start instead of
# twenty). It only bakes pictures; checks_analyse.py (plain Python) then measures them. Four parts:
#   1. HALF-TILE TEST (512 dots): the recipe as it is and slid by half a picture (parameter shift = [0.5, 0.5]), for one base tile across and
#      for two (recipe.tiles_across 2): the finished colour, a random colour per stone, and the exact (16 bit) edge distance and the SOIL and FACETS masks.
#      If the tile repeats exactly, the slid picture equals the plain picture rolled by half its size. (The same idea as
#      recipes/slate_layers/tests/half_tile_test.py, with all bakes in one run.)
#   2. LAYER MASKS (627 dots): each layer's Mask on the gravel layout, for the picture sheet.
#   3. INDEPENDENCE TEST (320 dots): the finished colour, exact height and roughness as they are, then with each layer's Amount set to 0 and
#      with each layer's Seed + 1, plus each layer's own Mask (exact, 16 bit). (The same idea as tests/independence_test.py.)
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
recipe = bh.load_recipe(os.path.join(HERE, 'gravel_recipe.py'))
SEEDS = {'gravel_layout': 1.0, 'colour_and_fade': 11.0, 'damage': 21.0, 'outline_and_shadow': 41.0, 'soil': 51.0, 'facets': 61.0}
LAYERS = ['colour_and_fade', 'facets', 'damage', 'outline_and_shadow', 'soil']


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
            photograph(scene, tile, dict(base, debug_view='bundle.piece_colour'), stem + 'pieces', ['Colour'])
            photograph(scene, tile, dict(base, debug_view='bundle.edge_distance'), stem + 'edge_distance', ['Height'])
            photograph(scene, tile, dict(base, debug_view='soil.mask'), stem + 'soil_mask', ['Height'])
            photograph(scene, tile, dict(base, debug_view='facets.mask'), stem + 'facets_mask', ['Height'])
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
    folder = os.path.join(out_root, 'independence')
    os.makedirs(folder, exist_ok=True)
    scene, tile = bh.new_bake_scene(320)
    channels = ['Colour', 'Height', 'Roughness']
    photograph(scene, tile, {}, os.path.join(folder, 'base'), channels)
    for layer in LAYERS:
        photograph(scene, tile, {'debug_view': f'{layer}.mask'}, os.path.join(folder, f'mask_{layer}'), ['Height'])
        photograph(scene, tile, {f'{layer}.amount': 0.0}, os.path.join(folder, f'{layer}_amount_0'), channels)
        photograph(scene, tile, {f'{layer}.seed': SEEDS[layer] + 1.0}, os.path.join(folder, f'{layer}_seed_plus_1'), channels)
    photograph(scene, tile, {'gravel_layout.seed': 2.0}, os.path.join(folder, 'gravel_layout_seed_plus_1'), channels)
    print('[independence]', round(time.time() - started), flush=True)
if 4 in parts:
    tree = recipe.build_node_group({})
    counts = {}

    def walk(group, label, depth=0):
        kinds = collections.Counter(node.bl_idname.replace('ShaderNode', '') for node in group.nodes)
        inner = {}
        for node in group.nodes:
            if node.bl_idname == 'ShaderNodeGroup' and node.node_tree is not None:
                inner.setdefault(node.node_tree.name.split('.')[0], node.node_tree)
        counts[label] = {'nodes': len(group.nodes), 'kinds': dict(kinds.most_common(10)),
                         'boxes_inside': collections.Counter(node.node_tree.name.split('.')[0] for node in group.nodes
                                                             if node.bl_idname == 'ShaderNodeGroup' and node.node_tree is not None)}
        for name, sub in inner.items():
            if name not in counts:
                walk(sub, name, depth + 1)
    walk(tree, 'GRAVEL (top: the recipe wiring)')
    with open(os.path.join(out_root, 'node_counts.json'), 'w') as handle:
        json.dump(counts, handle, indent=1)
    for name, row in counts.items():
        print('[nodes]', name, row['nodes'], dict(row['boxes_inside']), flush=True)
print('[checks done]', round(time.time() - started), 'seconds', flush=True)
