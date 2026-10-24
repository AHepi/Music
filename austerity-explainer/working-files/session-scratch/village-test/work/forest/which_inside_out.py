import bpy, numpy as np, sys
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import scene_read
for o in bpy.data.objects:
    if o.get('place_owner')!='forest': continue
    me=o.data; n=len(me.vertices); co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(n,3)
    labels,k=scene_read.loose_part_labels(me); me.calc_loop_triangles(); t=len(me.loop_triangles)
    f=np.empty(t*3,dtype=np.int64); me.loop_triangles.foreach_get('vertices',f); f=f.reshape(-1,3)
    for i in range(k):
        mask=labels==i; idx=-np.ones(n,dtype=np.int64); idx[mask]=np.arange(mask.sum()); tt=f[labels[f[:,0]]==i]
        v=co[mask]; tri=v[idx[tt]]; vol=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6
        if vol<0: print(o.name,i,round(vol,3), len(tt))
