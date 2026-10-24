import bpy, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get()
out = {}
def obinfo(o):
    bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
    mn = [min(v[i] for v in bb) for i in range(3)]; mx = [max(v[i] for v in bb) for i in range(3)]
    return dict(n=o.name, t=o.type, d=(o.data.name if o.data else (o.instance_collection.name if o.instance_collection else None)), loc=[round(v,2) for v in o.location], mn=[round(v,2) for v in mn], mx=[round(v,2) for v in mx], hide_r=o.hide_render)
for cn in ('Trees','Undergrowth','Grass','RoadDebris','Atmosphere','Lights','Terrain'):
    c = bpy.data.collections.get(cn)
    out[cn] = [obinfo(o) for o in c.all_objects]
# terrain height grid via BVH
ter = bpy.data.objects['Terrain'].evaluated_get(dg)
me = ter.to_mesh()
mw = ter.matrix_world
verts = [mw @ v.co for v in me.vertices]
polys = [tuple(p.vertices) for p in me.polygons]
bvh = BVHTree.FromPolygons(verts, polys)
xs = np.arange(-100, 101, 1.0); ys = np.arange(-60, 71, 1.0)
H = np.full((len(ys), len(xs)), np.nan)
for j, y in enumerate(ys):
    for i, x in enumerate(xs):
        hit = bvh.ray_cast(Vector((x, y, 200)), Vector((0, 0, -1)))
        if hit[0] is not None:
            H[j, i] = hit[0].z
np.save(bpy.path.abspath('//') + 'x', H) if False else None
np.savez('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-4k/sonnet_work/height.npz', H=H, xs=xs, ys=ys)
print('NV', len(verts), len(polys))
json.dump(out, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-4k/sonnet_work/objs.json','w'))
# puddles mesh: islands centres
pud = bpy.data.objects['Puddles']
pm = pud.data
pv = np.array([ (pud.matrix_world @ v.co)[:] for v in pm.vertices])
print('PUDV', len(pv))
np.save('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-4k/sonnet_work/pudv.npy', pv)
# world / sun info
w = bpy.context.scene.world
info = []
if w and w.node_tree:
    for n in w.node_tree.nodes:
        d = {'n': n.name, 't': n.bl_idname}
        for k in ('sun_elevation','sun_rotation','sun_size','sun_intensity','altitude','air_density','dust_density','ozone_density','sky_type'):
            if hasattr(n, k):
                v = getattr(n, k); d[k] = v if isinstance(v,(str,int,float)) else str(v)
        info.append(d)
print('WORLD', json.dumps(info))
