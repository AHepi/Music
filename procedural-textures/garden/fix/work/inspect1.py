import bpy, sys
sc = bpy.context.scene
print('ENGINE', sc.render.engine, 'cam', sc.camera.name if sc.camera else None, 'file', bpy.data.filepath)
print('N objects', len(bpy.data.objects), 'N materials', len(bpy.data.materials))
for ob in sorted(bpy.data.objects, key=lambda o:o.name):
    if ob.type in ('MESH','CURVE','LIGHT','EMPTY','CAMERA') :
        mods=[m.type+':'+(m.node_group.name if getattr(m,'node_group',None) else '') for m in ob.modifiers]
        sl=[s.material.name if s.material else None for s in ob.material_slots]
        nv = len(ob.data.vertices) if ob.type=='MESH' else 0
        print('OB', ob.name, ob.type, 'own=',ob.get('garden_owner'), 'role=',ob.get('garden_role'), 'v=',nv, 'vis=(cam,gl,diff)=', ob.visible_camera, ob.visible_glossy, ob.visible_diffuse, 'hide_render', ob.hide_render, 'mods', mods, 'slots', sl[:3])
