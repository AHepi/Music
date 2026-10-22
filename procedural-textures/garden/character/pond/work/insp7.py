import bpy, numpy as np, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
g=bpy.data.objects['Astra / Courtyard receiving ground']; bv=BVHTree.FromObject(g, bpy.context.evaluated_depsgraph_get())
def gz(x,y):
    r=bv.ray_cast(Vector((x,y,5.0)),Vector((0,0,-1))); return r[0].z if r[0] is not None else None
bed=bpy.data.objects['Life / pond bed']
V=np.array([v.co[:] for v in bed.data.vertices]); G=np.array([gz(x,y) for x,y,_ in V])
dz=V[:,2]-G
print("plate z - ground z: min %.3f max %.3f mean %.3f"%(dz.min(),dz.max(),dz.mean()), "z range", V[:,2].min().round(3), V[:,2].max().round(3))
for lo,hi in ((-1,-0.45),(-0.45,-0.4),(-0.4,-0.35),(-0.35,0)):
    m=(V[:,2]>=lo)&(V[:,2]<hi); print("plate z in",lo,hi,"n",m.sum(),"dz mean %.3f"%dz[m].mean() if m.sum() else "")
print("plate verts where ground z > plate z:", (dz<0).sum(), "ground z at those: min", G[dz<0].min() if (dz<0).any() else None)
# corridor polyline distance
nodes=np.array([(-5.95,1.55),(-3.90,0.15),(-2.00,1.00),(-0.55,-0.60)])
def dseg(p,a,b):
    ab=b-a; t=np.clip(np.dot(p-a,ab)/np.dot(ab,ab),0,1); return np.hypot(*(p-(a+t*ab)))
def dc(p): return min(dseg(np.array(p),nodes[i],nodes[i+1]) for i in range(3))
D=np.array([dc(v[:2]) for v in V]); print("plate verts inside 1.2 m of corridor", (D<1.2).sum(), "of", len(V))
# faces
print("plate faces", len(bed.data.polygons), "area xy approx")
pb=bpy.data.objects['Life / pond pebbles']; P=np.array([v.co[:] for v in pb.data.vertices])
Gp=np.array([gz(x,y) for x,y,_ in P]); dp=P[:,2]-Gp
print("pebble verts z - ground z: min %.3f mean %.3f max %.3f"%(dp.min(),dp.mean(),dp.max()))
# bed grid structure
xs=np.unique(V[:,0].round(3)); ys=np.unique(V[:,1].round(3)); print("plate grid unique x",len(xs),"unique y",len(ys), xs[:5], ys[:5])
# footing check: bridge piers in water z ranges
for n in ['Bridge pier','Bridge pier.001','Bridge pier.002','Bridge pier.003']:
    o=bpy.data.objects.get(n)
    if o:
        Vp=np.array([v.co[:] for v in o.data.vertices]); W=np.array([o.matrix_world@Vector(v) for v in Vp]); print(n,"world bbox",W.min(0).round(2),W.max(0).round(2))
