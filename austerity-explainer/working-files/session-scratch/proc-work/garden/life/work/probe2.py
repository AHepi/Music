import bpy, bmesh, sys, math, numpy as np
sys.path.insert(0,'/home/user/Music/japanese-courtyard')
from astra_loader import load_astra, apply_blender_52_shim
api=load_astra('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life/addon_copy')
print('api ok', hasattr(api,'create_native_scatter'), 'shim', apply_blender_52_shim(api))
# bamboo components signed volume
for name in ['Bamboo stalks','Bamboo fence']:
    ob=bpy.data.objects[name]; me=ob.data
    bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    # islands
    seen=set(); islands=[]
    for f in bm.faces:
        if f.index in seen: continue
        stack=[f]; isl=[]
        seen.add(f.index)
        while stack:
            c=stack.pop(); isl.append(c)
            for e in c.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        islands.append(isl)
    neg=[]
    for isl in islands:
        vol=0
        for f in isl:
            vs=[v.co for v in f.verts]
            for i in range(1,len(vs)-1):
                vol+=vs[0].dot(vs[i].cross(vs[i+1]))/6
        if vol<0: neg.append((len(isl), round(vol,8), tuple(round(c,2) for c in isl[0].calc_center_median())))
    print(name,'islands',len(islands),'negative-volume islands',len(neg),neg[:6])
    bm.free()
# ground z range and pond
g=bpy.data.objects['Astra / Courtyard receiving ground']
print('ground matrix identity', [list(r) for r in g.matrix_world][:3], g.parent.matrix_world[0][:])
co=np.array([tuple(v.co) for v in g.data.vertices])
print('ground z min/max',co[:,2].min(),co[:,2].max())
dep=bpy.context.evaluated_depsgraph_get()
cam=bpy.context.scene.camera
print('cam', cam.location, cam.matrix_world.to_euler())
