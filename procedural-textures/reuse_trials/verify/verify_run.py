# What this does (plain words): the independent checker's own Blender run for ONE surface of the reuse trials. It does two things and
# writes everything into verify/work/SURFACE/:
#   1. NODE COUNT: builds the surface's recipe exactly as the trial ships it, then counts the nodes inside every box ("box" = one
#      node group) by walking the finished recipe, and records from which file each shared module was really imported (so the
#      "unchanged from the frozen snapshot" claim can be checked) and what the new boxes are. Written to node_count.json.
#   2. HALF-TILE TEST (512 dots): bakes the finished colour with the recipe as it is and again slid by half a picture in both directions
#      (the recipe's 'shift' parameter), for one tile across and for two tiles across; also the finished height for one tile across.
#      If the tile repeats exactly, the slid picture equals the plain picture moved by half its size (checked later by half_tile_analyse.py).
# Use: blender -b --disable-autoexec -t 2 --python verify_run.py -- SURFACE [parts, e.g. 1,2]   (part 1 = node count, part 2 = half tile)
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
surface = arguments[0]
parts = [int(p) for p in (arguments[1] if len(arguments) > 1 else '1,2').split(',')]
RECIPE_FILES = {'brick': 'brick_recipe.py', 'wood': 'wood_recipe.py', 'metal': 'metal_recipe.py', 'mud': 'mud_recipe.py', 'gravel': 'gravel_recipe.py'}
trial_folder = os.path.join(PROC, 'reuse_trials', surface)
out_folder = os.path.join(HERE, 'work', surface)
os.makedirs(out_folder, exist_ok=True)
started = time.time()
recipe = bh.load_recipe(os.path.join(trial_folder, RECIPE_FILES[surface]))

if 1 in parts:
    tree = recipe.build_node_group({})
    boxes = {}

    def walk(group, label):
        boxes[label] = {
            'nodes_directly_inside': len(group.nodes),
            'box_nodes_inside_it': dict(collections.Counter(n.node_tree.name.split('.')[0] for n in group.nodes
                                                            if n.bl_idname == 'ShaderNodeGroup' and n.node_tree is not None)),
        }
        for node in group.nodes:
            if node.bl_idname == 'ShaderNodeGroup' and node.node_tree is not None:
                name = node.node_tree.name.split('.')[0]
                if name not in boxes:
                    walk(node.node_tree, name)

    walk(tree, 'TOP (recipe wiring)')
    modules = {}
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and ('reuse_trials' in path or os.sep + 'lib' + os.sep in path):
            modules[name] = path
    with open(os.path.join(out_folder, 'node_count.json'), 'w') as handle:
        json.dump({'surface': surface, 'boxes': boxes, 'imported_files': modules}, handle, indent=1)
    for name, row in boxes.items():
        print('[nodes]', name, row['nodes_directly_inside'], flush=True)
    print('[count done]', round(time.time() - started), 's', flush=True)

if 2 in parts:
    scene, tile = bh.new_bake_scene(512)
    for tiles in (1, 2):
        for shift_name, shift in (('plain', None), ('shifted', [0.5, 0.5])):
            parameters = {'recipe.tiles_across': tiles}
            if shift:
                parameters['shift'] = shift
            group = recipe.build_node_group(parameters)
            for channel in (['Colour', 'Height'] if tiles == 1 else ['Colour']):
                material = bh.show_channel_material(group, channel)
                tile.data.materials.clear()
                tile.data.materials.append(material)
                bh.render_to(scene, os.path.join(out_folder, f't{tiles}_{shift_name}_{channel.lower()}.png'), channel != 'Colour', channel == 'Height')
            print('[half tile]', tiles, shift_name, round(time.time() - started), 's', flush=True)
    print('[half done]', round(time.time() - started), 's', flush=True)
