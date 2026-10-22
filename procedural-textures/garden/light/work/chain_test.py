# Extra check (not asked for by the brief): run shapes -> life -> light on the open starting scene, in memory, and look for clashes.
# Copies of the other stage files sit in work/chain/. Nothing is saved.
import bpy, sys, os, json, time
sys.dont_write_bytecode = True
CH = os.path.dirname(os.path.abspath(__file__)) + '/chain'
sys.path.insert(0, CH); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
look = sys.argv[sys.argv.index('--') + 1]
t = time.time()
import stage_shapes, stage_life, stage_light
r1 = stage_shapes.apply({'look': look}); print('CHAIN shapes done', round(time.time() - t, 1), 's')
r2 = stage_life.apply({'look': look, 'quick': True, 'scatter': False}); print('CHAIN life done', round(time.time() - t, 1), 's')
objs_before_light = set(o.name for o in bpy.data.objects)
r3 = stage_light.apply({'look': look}); print('CHAIN light done', round(time.time() - t, 1), 's')
print('CHAIN light created', r3['created'], 'deleted', r3['deleted'])
print('CHAIN lightgroups', [g.name for g in bpy.context.scene.view_layers[0].lightgroups])
# who got which light group
from collections import Counter
c = Counter(o.lightgroup for o in bpy.data.objects if getattr(o, 'lightgroup', ''))
print('CHAIN objects per light group', dict(c))
rest = [o.name for o in bpy.data.objects if getattr(o, 'lightgroup', '') == 'rest']
print('CHAIN rest group members', rest[:40])
rim = bpy.data.objects.get('Rim light (maple, hall edge)')
print('CHAIN rim receivers', [o.name for o in rim.light_linking.receiver_collection.objects])
print('CHAIN roof receivers', [o.name for o in bpy.data.objects.get('Roof lift (hall roof only)').light_linking.receiver_collection.objects])
print('CHAIN scene camera', bpy.context.scene.camera.name, 'objects', len(bpy.data.objects))
# any object that has a material slot without a material after everything?
print('CHAIN meshes without material', [o.name for o in bpy.data.objects if o.type == 'MESH' and any(s.material is None for s in o.material_slots)][:20])
if '--save' in sys.argv:
    out = sys.argv[sys.argv.index('--save') + 1]
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
    print('CHAIN saved', out, os.path.getsize(out))
