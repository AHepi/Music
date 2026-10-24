import sys
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from place_kit.checks import construction as C
from place_kit import settings_file
rt=settings_file.roles_table()
allp=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.get('place_owner') is None: continue
    role=o.get('place_role') or ''
    if role.startswith('ground.'): continue
    allp.extend(C._loose_parts(o,{'role':role},rt))
V=[];T=[];off=0
for p in allp:
    V.append(p.V);T.append(p.T+off);off+=len(p.V)
bvh=BVHTree.FromPolygons([tuple(v) for v in np.vstack(V)],[tuple(t) for t in np.vstack(T)],epsilon=0.0)
for p in allp:
    if p.obj_name not in ('Stable girts south wall','Stable girts west gable','Stable girts north wall'): continue
    best=None
    for s in p.face_samples(0.04,up_only=True)[:300]:
        if s[2]<p.bmax[2]-0.01: continue
        hit=bvh.ray_cast(Vector((s[0],s[1],s[2]+0.0005)),Vector((0,0,1)),0.15)
        if hit[0] is not None and hit[3] is not None:
            gap=hit[0].z-s[2]
            if gap>0.005:
                # which part?
                who=None
                for q in allp:
                    if q is p: continue
                    if np.all(hit[0]>=q.bmin-1e-3) and np.all(hit[0]<=q.bmax+1e-3): who=q.name; break
                if best is None or gap<best[0]: best=(gap,tuple(round(c,3) for c in s),who)
    if best: print(p.name, best)
