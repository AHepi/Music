import bpy, sys, numpy as np
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
import place_kit as pk
from place_kit import parts
from mathutils import Vector
from mathutils.bvhtree import BVHTree
obs=[o for o in bpy.data.objects if o.get('place_owner')=='cottages_north']
allv=[];allt=[];off=0;owner=[]
for o in obs:
    vs,ts=parts.world_triangles(o)
    allv.append(vs); allt.append(ts+off); off+=len(vs); owner += [o.name]*len(ts)
V=np.vstack(allv);T=np.vstack(allt)
bvh=BVHTree.FromPolygons([tuple(v) for v in V],[tuple(t) for t in T],epsilon=0.0)
for name in sys.argv[sys.argv.index('--')+1:]:
    o=bpy.data.objects[name]
    vs,ts=parts.world_triangles(o)
    zmax=vs[:,2].max()
    top=[v for v in vs if v[2]>zmax-0.2]
    print(name,'zmax',round(zmax,4))
    # sample top faces (up facing triangles)
    for t in ts:
        a,b,c=vs[t[0]],vs[t[1]],vs[t[2]]
        n=np.cross(b-a,c-a); ln=np.linalg.norm(n)
        if ln<1e-12: continue
        n/=ln
        if n[2]<0.5: continue
        cen=(a+b+c)/3
        if cen[2]<zmax-0.3: continue
        hit=bvh.ray_cast(Vector((cen[0],cen[1],cen[2]+0.0005)),Vector((0,0,1)),0.15)
        if hit[0] is not None:
            print('  tri centre',np.round(cen,3),'hit dist',round(hit[0].z-cen[2],4),'on',owner[hit[2]])
