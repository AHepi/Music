import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sc=bpy.context.scene
o=bpy.data.objects["Hall roof"]
m=o.modifiers[0]
pr=m.properties
print("props type",type(pr), [a for a in dir(pr) if not a.startswith('_')][:30])
for it in m.node_group.interface.items_tree:
    if it.item_type=='SOCKET' and it.in_out=='INPUT':
        try: print("  ",it.name,it.identifier, pr[it.identifier])
        except Exception as e: print("  ",it.name,it.identifier,"ERR",e)
dg=bpy.context.evaluated_depsgraph_get()
cams={n:bpy.data.objects[n] for n in ("photo","veranda")}
res=[]
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.name=="Hall roof":
        mw=inst.matrix_world
        res.append((np.array(mw.translation), np.array(mw.to_euler()), mw.to_scale()[:], inst.instance_object.name if inst.instance_object else None))
print("n inst",len(res), res[0][3])
P=np.array([r[0] for r in res])
print("bbox",P.min(0),P.max(0))
print("y quantiles",np.percentile(P[:,1],[0,25,50,75,100]))
for i in (0,1,2,37,38,39,343,344,345,687):
    print(i,np.round(res[i][0],3),np.round(np.degrees(res[i][1]),1),np.round(res[i][2],3))
for cn,c in cams.items():
    vis=0
    for r in res:
        co=world_to_camera_view(sc,c,Vector(r[0]))
        if 0<co.x<1 and 0<co.y<1 and co.z>0: vis+=1
    print(cn,"inst in frame",vis, "cam loc",tuple(c.location), "rot",tuple(round(x,3) for x in c.rotation_euler))
print("render res",sc.render.resolution_x,sc.render.resolution_y,"engine",sc.render.engine,"samples",sc.cycles.samples)
print("color mgmt",sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure)
