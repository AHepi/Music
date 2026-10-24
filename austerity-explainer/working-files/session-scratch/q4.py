import bpy, sys, os
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_geometry_nodes_curves_modifiers_physics')
import gn_tools as gt
tree, g = gt.make_geometry_group('q', [('Geometry','NodeSocketGeometry',None), ('Iterations','NodeSocketInt',40), ('Size','NodeSocketFloat',2.0)])
g.link('in','Geometry','out','Geometry')
obj, mod = gt.add_geometry_object('q', tree)
print([a for a in dir(mod) if not a.startswith('_')])
P=mod.properties; print('properties type', type(P)); print([a for a in dir(P) if not a.startswith('_')]); print('inputs', type(P.inputs), [ (a, type(getattr(P.inputs,a))) for a in dir(P.inputs) if not a.startswith('_')][:30]); print(len(P.inputs)); 
for i in P.inputs: print(' input', i, [a for a in dir(i) if not a.startswith('_') and a not in ('bl_rna','rna_type')])
for item in tree.interface.items_tree: print(item.name, item.identifier, item.in_out)
try:
    pass
except Exception as e: print('ERR', e)
