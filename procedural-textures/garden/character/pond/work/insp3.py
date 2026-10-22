import bpy, numpy as np, math, json
from mathutils import Vector
def vs(o):
    me=o.data; a=np.empty(len(me.vertices)*3,np.float32); me.vertices.foreach_get('co',a); return a.reshape(-1,3)
pw=bpy.data.objects['Pond water']; P=vs(pw)
print("POND WATER bbox", P.min(0).round(2), P.max(0).round(2), "z set", np.unique(P[:,2].round(3))[:5])
d=np.array([a.value for a in pw.data.attributes['depth'].data]); print("depth attr", d.min().round(3), d.max().round(3), d.mean().round(3), np.percentile(d,[10,50,90]).round(3), pw.data.attributes['depth'].domain)
# boundary vertices
me=pw.data
from collections import Counter
ec=Counter()
for p in me.polygons:
    vv=p.vertices
    for i in range(len(vv)):
        a,b=vv[i],vv[(i+1)%len(vv)]; ec[(min(a,b),max(a,b))]+=1
bnd=sorted({v for e,c in ec.items() if c==1 for v in e})
B=P[bnd]; print("boundary verts", len(bnd), "depth at boundary mean", d[bnd].mean().round(3))
print("grid hint: sample verts", P[:5].round(3).tolist())
bed=bpy.data.objects['Life / pond bed']; Bv=vs(bed); print("BED bbox", Bv.min(0).round(2), Bv.max(0).round(2), "z uniq", np.unique(Bv[:,2].round(2))[:10])
pb=bpy.data.objects['Life / pond pebbles']; Pv=vs(pb); print("PEBBLES", len(Pv), Pv.min(0).round(2), Pv.max(0).round(2), "z hist", np.histogram(Pv[:,2],bins=8)[0].tolist(), np.histogram(Pv[:,2],bins=8)[1].round(2).tolist())
# ground
g=bpy.data.objects['Astra / Courtyard receiving ground']
dg=bpy.context.evaluated_depsgraph_get()
sc=bpy.context.scene
def gz(x,y):
    ok,loc,n,i,o,m=sc.ray_cast(dg, Vector((x,y,3.0)), Vector((0,0,-1)))
    return loc.z if ok and o.name==g.name else (loc.z if ok else None), (o.name if ok else None)
print("ground sample grid (x down from -7 to 1, y from -2.5 to 4.5):")
xs=np.arange(-7.0,1.01,0.5); ys=np.arange(-2.0,4.51,0.5)
print("      "+" ".join("%5.1f"%y for y in ys))
for x in xs:
    row=[]
    for y in ys:
        z,n=gz(x,y); row.append("%5.2f"%z if z is not None else "  -  ")
    print("%5.1f "%x+" ".join(row))
