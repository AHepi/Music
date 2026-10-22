import bpy, numpy as np, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
g=bpy.data.objects['Astra / Courtyard receiving ground']; bv=BVHTree.FromObject(g, dg)
def gz(x,y):
    r=bv.ray_cast(Vector((x,y,5.0)),Vector((0,0,-1))); return r[0].z if r[0] is not None else 0.0
out={}
# water points on a 0.1 grid inside the pond water mesh: use mesh vertex (0.15 spacing) grid: take all verts and midpoints
pw=bpy.data.objects['Pond water']; P=np.array([v.co[:] for v in pw.data.vertices]); d=np.array([a.value for a in pw.data.attributes['depth'].data])
# densify: 0.1 grid, depth from ground z
xs=np.arange(-5.7,0.25,0.1); ys=np.arange(-1.3,3.15,0.1)
pts=[]
for x in xs:
    for y in ys:
        z=gz(x,y); dep=-0.12-z
        # inside pond only if the water mesh covers it: nearest vertex within 0.15
        dd=np.hypot(P[:,0]-x,P[:,1]-y); 
        if dd.min()>0.11 or dep<0: continue
        pts.append((x,y,min(dep,0.46)))
print("water pts", len(pts))
for camname in ('photo','veranda'):
    cam=bpy.data.objects[camname]; cl=cam.location; res=[]
    for (x,y,dep) in pts:
        p=Vector((x,y,-0.10)); co=world_to_camera_view(sc,cam,p)
        if not (0.01<=co.x<=0.99 and 0.01<=co.y<=0.99) or co.z<=0: continue
        dv=p-cl; L=dv.length; dv.normalize()
        ok,loc,n,i,ob,m=sc.ray_cast(dg, cl, dv, distance=L-0.02)
        if ok: continue
        res.append((round(x,2),round(y,2),round(dep,3),round(co.x*2400),round((1-co.y)*1600)))
    out[camname]=res; print(camname, len(res))
json.dump(out, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond/work/water_samples.json','w'))
