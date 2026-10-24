import bpy
seen=set()
for o in bpy.data.objects:
    ow=o.get('place_owner'); 
    if ow!='forest' and not o.name.startswith(('Scatter','PK','Plants','Litter','Forest')): 
        if o.get('pk_scatter') is None: continue
    key=(ow, o.get('place_role'), o.name.split(' ')[0])
    if key in seen: continue
    seen.add(key)
    print(o.name, '| owner', ow, '| role', o.get('place_role'), '| scatter', o.get('pk_scatter'), '| keys', [k for k in o.keys()][:40], '| mats', [s.material.name if s.material else None for s in o.material_slots][:5], '| shadow', o.visible_shadow, len(o.data.polygons) if o.type=='MESH' else '')
