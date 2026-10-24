import bpy, sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_seamless_tiles_and_baking')
__file__='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_seamless_tiles_and_baking/exp2d_geometry_routes.py'
sys.argv=['x','--','64']
src=open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_seamless_tiles_and_baking/exp2d_geometry_routes.py').read()
# run only until the GN part
i=src.index('# ---------------------------------------------------------------------------------- Route 1')
j=src.index('# ---------------------------------------------------------------------------------- Route 3')
head=src[:i]; tail=src[j:]
exec(compile(head,'head','exec'))
exec(compile(tail.split('started = time.time()')[0],'tail','exec'))
dg=bpy.context.evaluated_depsgraph_get()
ev=obj.evaluated_get(dg)
m=ev.to_mesh()
print('EVAL verts',len(m.vertices),'polys',len(m.polygons),'materials',[x.name if x else None for x in m.materials])
import numpy as np
co=np.empty(len(m.vertices)*3,np.float32); m.vertices.foreach_get('co',co); co=co.reshape(-1,3)
print('bbox',co.min(0),co.max(0))
print('slots',[s.material.name if s.material else None for s in obj.material_slots])
print('modifier node group errors?', [ (n.name, getattr(n,'bl_idname',''))for n in gn.nodes])
