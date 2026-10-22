# What this does: proves the stage covers objects made by OTHER builders (tagged garden_role, wearing 'GARDEN placeholder <role>'), without knowing their names.
#   blender -b START.blend --python prove_new_objects.py -- LOOK OUT.json
import bpy, sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
look, out = sys.argv[sys.argv.index('--') + 1:][:2]
ROLES = ['stone.natural', 'stone.dressed', 'timber.deck', 'timber.frame', 'wall.plaster', 'wall.cap', 'roof.tile', 'ground.earth', 'ground.gravel']
made = []
col = bpy.data.collections.new('G1 shapes'); bpy.context.scene.collection.children.link(col)
for i, role in enumerate(ROLES):
    me = bpy.data.meshes.new('t' + str(i)); 
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=0.6); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(f'Odd name {i} for {role}', me)
    col.objects.link(ob); ob.location = (12.0 + i, 12.0, 0.3)
    ob['garden_owner'] = 'shapes'; ob['garden_role'] = role
    pm = bpy.data.materials.get('GARDEN placeholder ' + role) or bpy.data.materials.new('GARDEN placeholder ' + role)
    me.materials.append(pm)
    made.append(ob.name)
# a curve tagged bark
cu = bpy.data.curves.new('c', 'CURVE'); sp = cu.splines.new('POLY'); sp.points.add(2)
for j, p in enumerate(sp.points): p.co = (0, 0, j, 1)
cu.bevel_depth = 0.05
cb = bpy.data.objects.new('Odd bark limb', cu); col.objects.link(cb); cb.location = (12, 14, 0); cb['garden_owner'] = 'life'; cb['garden_role'] = 'bark'
cb.data.materials.append(bpy.data.materials.new('GARDEN placeholder bark'))
made.append(cb.name)
import stage_surfaces as ss
t = time.time()
rep = ss.apply({'look': look, 'weathering': look == 'real', 'verbose': True})
res = {'look': look, 'seconds': round(time.time() - t, 1), 'objects': {}}
for n in made:
    ob = bpy.data.objects[n]
    res['objects'][n] = {'role': ob.get('garden_role'), 'material': [m.name if m else None for m in ob.data.materials], 'family': (ob.data.materials[0].get('garden_family') if ob.data.materials[0] else None)}
res['placeholders_left'] = [m.name for m in bpy.data.materials if m.name.startswith('GARDEN placeholder')]
if look == 'real':
    w = rep['weathering']
    res['kit_roles'] = w['roles']; res['kit_unassigned'] = w['unassigned_objects']; res['mask_pack'] = w['mask_pack']
    from apply import roles as roles_module
    import weathering_stage
    h = weathering_stage._HANDLE['w']
    rm = h.kit.role_map
    res['kit_role_of_new_objects'] = {n: rm.role_of(n) for n in made}
json.dump(res, open(out, 'w'), indent=1, default=str)
print('NEWOBJ', json.dumps(res['objects'])[:1500])
print('KIT', res.get('kit_role_of_new_objects'), 'placeholders left', res['placeholders_left'])
