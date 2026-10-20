# What this does (plain words): the verifier's check. Builds the slate recipe in a FRESH Blender and lists what is inside the top box "SLATE":
# every sub-group (its label, its node-group name, how many nodes it holds), every input socket of each layer group with its value, and every
# link that goes INTO a layer group from anywhere other than the LAYOUT group or the top box's Vector input (those are the cross-layer links).
# Also checks that no Image Texture node exists anywhere. Writes verify/node_tree_listing.json.
# Use: blender -b --disable-autoexec -t 2 --python list_node_tree.py
import importlib.util
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
VERIFY = os.path.dirname(HERE)
RECIPE = os.path.join(VERIFY, '..', 'recipe', 'slate_recipe.py')

spec = importlib.util.spec_from_file_location('slate_recipe_verify', RECIPE)
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)
tree = recipe.build_node_group({})

report = {'top_group': tree.name, 'sub_groups': [], 'cross_layer_links': [], 'image_nodes_anywhere': []}
for group in bpy.data.node_groups:
    for node in group.nodes:
        if node.bl_idname in ('ShaderNodeTexImage', 'ShaderNodeTexEnvironment', 'ShaderNodeTexIES', 'ShaderNodeScript'):
            report['image_nodes_anywhere'].append([group.name, node.name, node.bl_idname])

for node in tree.nodes:
    if node.bl_idname != 'ShaderNodeGroup':
        continue
    inner = node.node_tree
    entry = {'label': node.label, 'group_name': inner.name, 'nodes_inside': len(inner.nodes),
             'nested_groups': sorted({n.node_tree.name.split('.')[0] for n in inner.nodes if n.bl_idname == 'ShaderNodeGroup'}),
             'inputs': {}, 'outputs': [s.name for s in node.outputs]}
    for socket in node.inputs:
        if socket.is_linked:
            source = socket.links[0].from_node
            entry['inputs'][socket.name] = 'LINKED from ' + (source.label or source.name) + '.' + socket.links[0].from_socket.name
            if source.label not in ('LAYOUT',) and source.bl_idname != 'NodeGroupInput' and node.label not in ('COMBINE',):
                report['cross_layer_links'].append([source.label, socket.links[0].from_socket.name, '->', node.label, socket.name])
        else:
            value = socket.default_value
            try:
                value = [round(x, 5) for x in value]
            except TypeError:
                value = round(value, 6) if isinstance(value, float) else value
            entry['inputs'][socket.name] = value
    report['sub_groups'].append(entry)

with open(os.path.join(VERIFY, 'node_tree_listing.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('TOP', tree.name)
for entry in report['sub_groups']:
    seed = entry['inputs'].get('Seed', '-')
    amount = entry['inputs'].get('Amount', '-')
    own = [k for k, v in entry['inputs'].items() if not str(v).startswith('LINKED')]
    print(f"SUB {entry['label']:20s} group={entry['group_name']:20s} nodes={entry['nodes_inside']:5d} seed={seed} amount={amount} own_controls={len(own)} nested={entry['nested_groups']}")
print('CROSS LAYER LINKS', report['cross_layer_links'])
print('IMAGE NODES', report['image_nodes_anywhere'])
