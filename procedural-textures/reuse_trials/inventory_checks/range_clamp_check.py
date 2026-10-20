# What this does (plain words): a one-minute check for the inventory. Every layer control becomes a socket with a lowest and highest value (its range).
# Question: if a trial's settings give a value OUTSIDE that range (for example a brick mortar joint wider than the slate layout's 'joint_width' range),
# does Blender keep it or silently cut it to the range? It builds the frozen LAYOUT box with joint_width 0.016 (above its highest value 0.01) and prints
# what the socket really holds, both on the box itself and on a copy of the box placed in a recipe (a group node). Writes range_clamp_check.json next to this file. Nothing else is written.
# Use: blender -b --disable-autoexec -t 2 --python reuse_trials/inventory_checks/range_clamp_check.py
import json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'reuse_trials', 'shared_layers_snapshot', 'layers'))
import layout  # noqa: E402
tree = layout.build_group({'layout.joint_width': 0.016, 'layout.row_gap': 0.0148, 'layout.rows_per_tile': 12, 'layout.slates_per_row': 4})
found = {}
for item in tree.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name in ('Joint Width', 'Row Gap'):
        found[item.name] = {'asked': 0.016 if item.name == 'Joint Width' else 0.0148, 'socket_holds': round(item.default_value, 6),
                            'range': [item.min_value, item.max_value]}
import bpy  # noqa: E402
parent = bpy.data.node_groups.new('parent', 'ShaderNodeTree')
node = parent.nodes.new('ShaderNodeGroup')
node.node_tree = tree
for name in ('Joint Width', 'Row Gap'):
    found[name]['group_node_in_a_recipe_holds'] = round(node.inputs[name].default_value, 6)
    node.inputs[name].default_value = 0.02
    found[name]['after_setting_0.02_on_the_group_node'] = round(node.inputs[name].default_value, 6)
json.dump(found, open(os.path.join(HERE, 'range_clamp_check.json'), 'w'), indent=1)
print('[range check]', found)
