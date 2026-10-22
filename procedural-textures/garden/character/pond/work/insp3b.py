import bpy, numpy as np, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
g=bpy.data.objects['Astra / Courtyard receiving ground']
me=g.data
bv=BVHTree.FromObject(g, bpy.context.evaluated_depsgraph_get())
def gz(x,y):
    r=bv.ray_cast(Vector((x,y,5.0)),Vector((0,0,-1)))
    return r[0].z if r[0] is not None else None
xs=np.arange(-6.5,0.76,0.5); ys=np.arange(-2.0,3.51,0.5)
print("ground z (rows x, cols y)")
print("       "+" ".join("%5.1f"%y for y in ys))
for x in xs:
    print("%5.1f  "%x+" ".join(("%5.2f"%gz(x,y)) if gz(x,y) is not None else "  -  " for y in ys))
pw=bpy.data.objects['Pond water']
P=np.array([v.co[:] for v in pw.data.vertices]); d=np.array([a.value for a in pw.data.attributes['depth'].data])
zz=np.array([gz(x,y) for x,y,_ in P])
print("depth vs -0.12-gz: corr", np.corrcoef(d, np.clip(-0.12-zz,0,0.46))[0,1].round(3), "max diff", np.abs(d-np.clip(-0.12-zz,0,0.46)).max().round(3))
# pond outline function
cx,cy,A,B,rot=-3.0,1.0,3.3,2.5,math.radians(10)
def pr(x,y):
    dx,dy=x-cx,y-cy; u=dx*math.cos(-rot)-dy*math.sin(-rot); v=dx*math.sin(-rot)+dy*math.cos(-rot)
    th=math.atan2(v/B,u/A); wob=1+0.10*math.sin(3*th+0.8)+0.06*math.sin(5*th+2.1)+0.04*math.sin(2*th)
    return math.hypot(u/A,v/B)/wob
rr=np.array([pr(x,y) for x,y,_ in P])
print("pond_radius over water verts: min/max", rr.min().round(2), rr.max().round(2))
# distance from bank (boundary) for water verts
# where d==0
print("verts with depth<0.02:", (d<0.02).sum(), "of", len(d))
# pond-edge stones, rocks
for nm in [f'Pond edge stone {i}' for i in range(15)]+[f'Rock {i}' for i in range(5)]+['Shore stones']:
    o=bpy.data.objects.get(nm)
    if o:
        c=np.array([v.co[:] for v in o.data.vertices]); 
        print(nm, "bbox", c.min(0).round(2), c.max(0).round(2), "loc", np.round(o.location,2), "collections", [x.name for x in o.users_collection], "verts", len(c))
