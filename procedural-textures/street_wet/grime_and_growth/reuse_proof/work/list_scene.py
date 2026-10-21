import bpy, json
out = []
for o in bpy.data.objects:
    mats = [s.material.name if s.material else None for s in o.material_slots]
    mods = [m.type for m in o.modifiers]
    out.append((o.name, o.type, o.hide_render, o.hide_viewport, mats[:3], len(mats), mods, [round(v,2) for v in o.location], [round(v,2) for v in o.dimensions], len(o.data.polygons) if o.type=='MESH' else 0, dict(o.items()) if o.keys() else {}))
for r in sorted(out):
    print(r[:7], r[7], r[8], r[9], {k:str(v)[:30] for k,v in r[10].items() if not k.startswith('_')})
print('MATERIALS')
for m in bpy.data.materials:
    print(m.name, m.users, [k for k in m.keys() if not k.startswith('_')])
print('CAM', bpy.context.scene.camera.name, [round(x,3) for x in bpy.context.scene.camera.location], bpy.context.scene.camera.rotation_euler[:], bpy.context.scene.camera.data.angle_y, bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y, bpy.context.scene.render.engine)
print('SUNS', [(l.name, l.data.type, l.data.energy, tuple(l.rotation_euler)) for l in bpy.data.objects if l.type=='LIGHT'])
