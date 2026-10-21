# What this file does (plain words): builds the three layers in the street copy inside Blender and prints what it made (node counts, pieces, errors) WITHOUT drawing anything. A quick check
# that the node recipes can be built at all. Run: blender -b --disable-autoexec street.blend --python smoke_build.py -- [street|lockout]
import os, sys, time
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'setts', 'tools'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw
import apply_joints_to_set as aj
import apply_rubbish_to_set as ar
import rubbish_layer as rl
import rubbish_pieces as rp
kind = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else 'street'
aw.cameras()
aw.apply(0.85, 0.5)
aj.apply()
t = time.time()
ar.apply(places=kind, amount=1.0)
print('BUILT in', round(time.time() - t, 2), 's')
for name in ('RUBBISH', rl.SCATTER_TREE_NAME):
    tree = bpy.data.node_groups.get(name)
    print(name, 'nodes', len(tree.nodes) if tree else None, 'links', len(tree.links) if tree else None)
print('collections', {k: len(v.objects) for k, v in rp.COLLECTIONS.items()})
dg = bpy.context.evaluated_depsgraph_get()
print('pieces', ar.piece_count())
for name in rl.SHADER_MATERIALS:
    tree = bpy.data.materials[name].node_tree
    bad = [l for l in tree.links if not l.is_valid]
    print(name, 'invalid links', len(bad))
tree = bpy.data.node_groups[rl.SCATTER_TREE_NAME]
print('scatter invalid links', len([l for l in tree.links if not l.is_valid]))
tree = bpy.data.node_groups['RUBBISH']
print('group invalid links', len([l for l in tree.links if not l.is_valid]))
