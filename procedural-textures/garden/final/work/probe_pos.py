import bpy
for n in ['Maple trunk','Lantern base','Lantern window glow','Hall posts','Water basin','Stone plinth','Raked gravel court','Pond water','Rock 0','Rock 1','Stepping stone 0','Pine trunk','Bamboo stalks','Back wall, left','Right wall behind hall']:
    o=bpy.data.objects.get(n)
    if o: 
        bb=[o.matrix_world@__import__('mathutils').Vector(c) for c in o.bound_box]
        print('POS',n,[round(x,2) for x in o.location],'bbox',[round(min(v[i] for v in bb),2) for i in range(3)],[round(max(v[i] for v in bb),2) for i in range(3)])
for c in ('photo','veranda'):
    o=bpy.data.objects[c]; print('CAM',c,[round(x,3) for x in o.location],[round(x,4) for x in o.rotation_euler], o.data.lens, o.data.sensor_width, o.data.sensor_fit, o.data.dof.use_dof)
sc=bpy.context.scene; print('RES',sc.render.resolution_x,sc.render.resolution_y,sc.cycles.samples,sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure, sc.render.use_compositing)
