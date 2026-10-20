# What this does (plain words): builds the brick recipe once with the SHARED slate LAYOUT (recipe.layout 'slate') instead of the new brick layout,
# counts the nodes in every box and writes checks/node_counts_with_shared_slate_layout.json. It bakes no picture.
# Use: blender -b --disable-autoexec -t 2 --python count_nodes_with_shared_layout.py
import sys, os, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import bake_harness as bh
recipe = bh.load_recipe(os.path.join(HERE, 'brick_recipe.py'))
tree = recipe.build_node_group({'recipe.layout': 'slate'})
out = {}
for node in tree.nodes:
    if node.bl_idname == 'ShaderNodeGroup':
        out[node.node_tree.name.split('.')[0]] = len(node.node_tree.nodes)
out['top'] = len(tree.nodes)
print('[slate layout nodes]', json.dumps(out))
json.dump(out, open(os.path.join(HERE, 'checks', 'node_counts_with_shared_slate_layout.json'), 'w'), indent=1)
