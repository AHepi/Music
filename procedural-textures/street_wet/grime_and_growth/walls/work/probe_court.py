import bpy
for o in bpy.data.objects:
    if o.name.startswith(('Hall plaster','Back wall','Right wall','Hall posts','Veranda step','Water basin','Pond edge stone 0','Lantern base')) :
        bb=[o.matrix_world@__import__('mathutils').Vector(c) for c in o.bound_box]
        xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
        print('OBJ',o.name,'x',round(min(xs),2),round(max(xs),2),'y',round(min(ys),2),round(max(ys),2),'z',round(min(zs),2),round(max(zs),2), [s.material.name for s in o.material_slots][:2])
cam=bpy.data.objects.get('Camera') or bpy.context.scene.camera
print('CAM', cam.name if cam else None, [round(v,2) for v in cam.location] if cam else '')
