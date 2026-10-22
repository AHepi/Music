import bpy, sys, os, json, time
sys.path.insert(0, 'proc-work/garden/surfaces')
look, out = sys.argv[sys.argv.index('--') + 1:][:2]
import stage_surfaces as ss
t = time.time()
rep = ss.apply({'look': look, 'weathering': look == 'real', 'verbose': True})
res = {'look': look, 'seconds': round(time.time() - t, 1)}
new = [o for o in bpy.data.objects if o.get('garden_owner') in ('shapes', 'life') and o.type in ('MESH', 'CURVE')]
res['new_objects_total'] = len(new)
res['placeholders_left'] = [m.name for m in bpy.data.materials if m.name.startswith('GARDEN placeholder')]
byrole = {}
for o in new:
    mats = [m.name if m else None for m in o.data.materials]
    byrole.setdefault(o.get('garden_role'), []).append((o.name, mats, [m.get('garden_family') for m in o.data.materials if m]))
res['new_by_role'] = {k: {'count': len(v), 'sample': v[:3]} for k, v in byrole.items()}
res['objects_without_surface_material'] = [o.name for o in bpy.data.objects if family_ok if False] if False else []
unowned = []
for o in bpy.data.objects:
    if o.type in ('MESH', 'CURVE') and ss.family_of(o):
        for m in o.data.materials:
            if m is not None and m.get('garden_owner') != 'surfaces':
                unowned.append((o.name, m.name))
res['family_objects_with_untouched_material'] = unowned[:40]
if look == 'real':
    w = rep['weathering']
    res['kit_roles'] = w['roles']; res['kit_unassigned'] = w['unassigned_objects']; res['mask_pack'] = w['mask_pack']; res['problems'] = w['problems']
json.dump(res, open(out, 'w'), indent=1, default=str)
print('CROSS', json.dumps({k: res[k] for k in res if k not in ('new_by_role',)})[:1500])
print('CROSSROLES', json.dumps(res['new_by_role'])[:2000])
