import bpy, json, sys
out = {}
sc = bpy.context.scene
rows = []
for ob in bpy.data.objects:
    d = {'name': ob.name, 'type': ob.type, 'owner': ob.get('garden_owner'), 'role': ob.get('garden_role'),
         'colls': [c.name for c in ob.users_collection], 'nv': len(ob.data.vertices) if ob.type == 'MESH' else None,
         'uv': [u.name for u in ob.data.uv_layers] if ob.type == 'MESH' else None,
         'mods': [m.type for m in ob.modifiers], 'hide': ob.hide_render,
         'mats': [s.material.name if s.material else None for s in ob.material_slots]}
    rows.append(d)
out['objects'] = rows
out['n_materials'] = len(bpy.data.materials)
out['n_images'] = len(bpy.data.images)
out['images'] = [(i.name, i.size[0], i.size[1], i.colorspace_settings.name, i.packed_file is not None) for i in bpy.data.images]
json.dump(out, open(sys.argv[-1], 'w'))
print('DONE', len(rows))
