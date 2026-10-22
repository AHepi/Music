import bpy, mathutils, numpy as np
def bbox(nm):
    ob=bpy.data.objects[nm]
    dg=bpy.context.evaluated_depsgraph_get()
    e=ob.evaluated_get(dg)
    me=e.to_mesh()
    co=np.array([ (ob.matrix_world@v.co)[:] for v in me.vertices])
    e.to_mesh_clear()
    return co.min(0).round(2), co.max(0).round(2), len(co)
for nm in ['Astra / Courtyard receiving ground','Dark plain','Hills, foot','Raked gravel court','Pond water','Life / shrubs','Pine pads','Maple leaves','Hall plaster','Shoji paper']:
    try: print(nm, bbox(nm))
    except Exception as e: print(nm,'ERR',e)
for c in ['photo','veranda']:
    ob=bpy.data.objects[c]; print(c, ob.location[:], ob.data.lens, ob.rotation_euler[:])
sc=bpy.context.scene
print(sc.render.resolution_x, sc.render.resolution_y, sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
ob = bpy.data.objects['Life / shrubs']
print([ (k, ob[k]) for k in ob.keys()])
# ground z profile at far edge
