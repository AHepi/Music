import bpy
for o in sorted(bpy.data.objects,key=lambda o:(o.get('garden_owner',''),o.name)):
    if o.get('garden_owner') in ('life','light','surfaces'):
        print(f"{o.get('garden_owner'):8} {o.type:7} {o.name}  verts={len(o.data.vertices) if o.type=='MESH' else '-'} hide_render={o.hide_render} collections={[c.name for c in o.users_collection]}")
