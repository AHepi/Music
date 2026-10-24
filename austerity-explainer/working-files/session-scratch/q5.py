import bpy, sys
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_geometry_nodes_curves_modifiers_physics')
import gn_tools as gt
tree, g = gt.make_geometry_group('q', [('Geometry','NodeSocketGeometry',None), ('Iterations','NodeSocketInt',40), ('Size','NodeSocketFloat',2.0)])
g.link('in','Geometry','out','Geometry')
obj, mod = gt.add_geometry_object('q', tree)
I = mod.properties.inputs
s = I.Socket_1
print([a for a in dir(s) if not a.startswith('_')])
print(s.value if hasattr(s,'value') else None)
s.value = 7
print('now', s.value)
s2 = I.Socket_2; s2.value = 3.5; print(s2.value)
