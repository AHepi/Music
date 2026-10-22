import bpy, numpy as np, mathutils
OWN = ["Astra / varied planks"] + ["Astra / varied planks.%03d" % i for i in range(1,8)] + ["Bridge pier %d"%i for i in range(4)] + ["Bridge stringers","Veranda step","Veranda step, lower","Hall posts","Hall beams","Eave soffit","Roof carrying frame","Gravel timber edge","Shoji bars","Stone plinth"]
print("SCENE", bpy.context.scene.name, "frame", bpy.context.scene.frame_current, "units", bpy.context.scene.unit_settings.system)
for n in OWN:
    o = bpy.data.objects.get(n)
    if not o: print("MISSING", n); continue
    me = o.data
    P = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices])
    print("OBJ", n, "verts", len(me.vertices), "faces", len(me.polygons), "loc", tuple(round(x,3) for x in o.location), "rot", tuple(round(x,3) for x in o.rotation_euler), "scale", tuple(round(x,3) for x in o.scale))
    print("   bbox", np.round(P.min(0),3).tolist(), np.round(P.max(0),3).tolist())
    print("   mats", [m.name if m else None for m in me.materials], "mods", [(m.type, m.name) for m in o.modifiers], "colls", [c.name for c in o.users_collection], "uv", list(me.uv_layers.keys()), "attrs", [a.name for a in me.attributes][:12])
    print("   props", {k: (str(o[k])[:40]) for k in o.keys()})
    print("   parent", o.parent.name if o.parent else None, "hide", o.hide_viewport, o.hide_render, "visible_camera", o.visible_camera)
for n in ["photo","veranda","Focus"]:
    o = bpy.data.objects.get(n)
    print("CAM", n, o.type, tuple(round(x,3) for x in o.location), tuple(round(x,3) for x in o.rotation_euler), (o.data.lens, o.data.sensor_width, o.data.sensor_fit, o.data.dof.use_dof) if o.type=='CAMERA' else '')
print("COLLS", [(c.name, len(c.objects), [ch.name for ch in c.children]) for c in bpy.data.collections])
sc = bpy.context.scene
print("RENDER", sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
print("OBJECT COUNT", len(bpy.data.objects), "MATS", len(bpy.data.materials), "images", len(bpy.data.images))
