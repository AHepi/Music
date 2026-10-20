# What this does: counts the nodes in each of the six recipe node groups (so the guide's size statements are measured, not guessed).
# Run: blender -b --disable-autoexec --python count_nodes.py
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'recipes')); sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'lib')))
for name in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']:
    module = importlib.import_module('recipe_' + name)
    group = module.build_node_group({})
    kinds = {}
    for node in group.nodes:
        kinds[node.bl_idname] = kinds.get(node.bl_idname, 0) + 1
    top = sorted(kinds.items(), key=lambda kv: -kv[1])[:4]
    print('NODES', name, len(group.nodes), 'links', len(group.links), top)
