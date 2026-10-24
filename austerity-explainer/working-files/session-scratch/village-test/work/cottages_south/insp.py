import bpy, json
rows = {}
for ob in bpy.data.objects:
    if ob.get('place_owner') == 'cottages_south':
        rows.setdefault(ob.get('place_role'), []).append((ob.name, [s.material.name if s.material else None for s in ob.material_slots], len(ob.modifiers), ob.get('pk_original_materials') or ob.get('pk_orig_materials')))
for r, v in rows.items():
    print('INSP', r, v[0][1], len(v), v[0][3])
print('INSP keys', [k for k in list(bpy.data.objects['Cottage C door leaf'].keys())])
