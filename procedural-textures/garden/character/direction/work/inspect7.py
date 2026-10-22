import bpy, sys, re
names=sorted(o.name for o in bpy.data.objects)
sel=[n for n in names if re.match(r'^(Rock|Stepping stone|Pond edge stone|Gravel rock|Bridge pier|Maple branch|Pine limb|Maple leaf source|Life / (moss|tuft|pebble) sources|Astra / (varied|Planked)|CT /)',n)]
print("RESULT", sel)
print("RESULT colls", [c.name for c in bpy.data.collections if 'moss sources' in c.name or 'tuft' in c.name or 'pebble' in c.name or 'Planked' in c.name])
for c in bpy.data.collections:
    if c.name.startswith('Life /'):
        print("RESULT coll",c.name,[o.name for o in c.objects])
mats=sorted(m.name for m in bpy.data.materials if m.name.startswith('Astra / planks'))
print("RESULT planks mats",mats[:10],len(mats))
for n in ('Gravel kerb','Basin drain pebbles','Shore stones'): print("RESULT",n,[s.material.name for s in bpy.data.objects[n].material_slots])
print("RESULT ground.earth users",[o.name for o in bpy.data.objects if any(s.material and s.material.name=='GARDEN ground.earth' for s in o.material_slots)])
print("RESULT stone.lantern users",[o.name for o in bpy.data.objects if any(s.material and s.material.name=='GARDEN stone.lantern' for s in o.material_slots)])
print("RESULT CT timber users",[o.name for o in bpy.data.objects if any(s.material and s.material.name=='CT / Timber painterly surface' for s in o.material_slots)])
print("RESULT Dark timber users",[o.name for o in bpy.data.objects if any(s.material and s.material.name in('Dark timber','Beam timber','GARDEN timber.post') for s in o.material_slots)])
print("RESULT Bark users",[o.name for o in bpy.data.objects if any(s.material and s.material.name=='Bark' for s in o.material_slots)][:3])
