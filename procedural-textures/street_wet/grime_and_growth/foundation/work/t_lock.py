import bpy
for o in bpy.data.objects:
    n=o.name.lower()
    if any(k in n for k in ('brazier','drum','barrel','stove','fire','coal')) and o.type in ('MESH','EMPTY'):
        print('OBJ', o.name, o.type, [c.name for c in o.users_collection], [s.material.name for s in o.material_slots if s.material])
print('MATS', [m.name for m in bpy.data.materials if any(k in m.name.lower() for k in ('barrel','stove','brazier','drum','fire','coal','ember'))])
print('COLLS', [c.name for c in bpy.data.collections])
