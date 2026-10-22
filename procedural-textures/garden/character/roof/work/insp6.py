import bpy, numpy as np, json, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sc=bpy.context.scene
o=bpy.data.objects["Hall roof"]
m=o.modifiers[0]
for it in m.node_group.interface.items_tree:
    if it.item_type=='SOCKET' and it.in_out=='INPUT' and it.identifier!='Socket_0':
        print("  ",it.name,it.identifier, m.properties.inputs[it.identifier]['value'])
print("obj matrix", [list(r) for r in o.matrix_world])
dg=bpy.context.evaluated_depsgraph_get()
res=[]
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.name=="Hall roof":
        res.append((np.array(inst.matrix_world), inst.instance_object.name, inst.persistent_id[:] if hasattr(inst,'persistent_id') else None))
print("n inst",len(res), set(r[1] for r in res))
P=np.array([r[0][:3,3] for r in res])
print("bbox",P.min(0),P.max(0))
for i in list(range(0,6))+[28,29,30,31,32,33,343,344,345,346,687]:
    M=res[i][0]
    print(i, np.round(M[:3,3],3), "Ydir",np.round(M[:3,1],3),"Zdir",np.round(M[:3,2],3),"sc",np.round(np.linalg.norm(M[:3,:3],axis=0),3), res[i][2])
np.save("/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof/work/inst_world.npy", np.array([r[0] for r in res]))
# evaluated roof mesh
ev=o.evaluated_get(dg)
me=ev.to_mesh()
print("evaluated realized mesh verts",len(me.vertices),"mats",[mm.name if mm else None for mm in me.materials])
mi=np.zeros(len(me.polygons),dtype=int); me.polygons.foreach_get("material_index",mi)
co=np.zeros(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
W=np.array(o.matrix_world)
for k in range(len(me.materials)):
    sel=set()
    for p in me.polygons:
        if p.material_index==k: sel.update(p.vertices)
    if sel:
        v=co[list(sel)]; vw=(W[:3,:3]@v.T).T+W[:3,3]
        print("mat idx",k,me.materials[k].name if me.materials[k] else None,"nverts",len(sel),"world bbox",np.round(vw.min(0),3),np.round(vw.max(0),3))
ev.to_mesh_clear()
for cn in ("photo","veranda"):
    c=bpy.data.objects[cn]
    vis=0
    for r in res:
        co_=world_to_camera_view(sc,c,Vector(r[0][:3,3]))
        if 0<co_.x<1 and 0<co_.y<1 and co_.z>0: vis+=1
    print(cn,"inst in frame",vis,"rot",tuple(round(x,4) for x in c.rotation_euler),"lens",c.data.lens,"sensor",c.data.sensor_width,c.data.sensor_fit, "clip",c.data.clip_start,c.data.clip_end)
print("render",sc.render.resolution_x,sc.render.resolution_y,sc.render.engine,sc.cycles.samples, sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
