# What this does: tests what an Astra add-on button leaves behind when it fails late (version 0.2.0 versus 0.2.1).
# It registers the add-on, builds a plank run and a roof through the real buttons while forcing the "select the new
# object" step to fail, and counts the Blender data blocks before and after. Then it repeats each build normally.
# Use: blender -b --disable-autoexec --python rollback_test.py -- ADDON_FOLDER
import sys, json, bpy
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from astra_loader import load_astra, apply_blender_52_shim
folder = sys.argv[sys.argv.index('--') + 1]
api = load_astra(folder)
apply_blender_52_shim(api)
import astra_painted_workbench as addon
import astra_painted_workbench.runtime.ui as ui
bpy.ops.wm.read_factory_settings(use_empty=True)
addon.register()
VERSION = ui.contract.VERSION if hasattr(ui, 'contract') else '?'

def counts():
    d = bpy.data
    return {'objects': len(d.objects), 'meshes': len(d.meshes), 'materials': len(d.materials), 'collections': len(d.collections),
            'node_groups': len(d.node_groups), 'texts': len(d.texts)}
def delta(a, b): return {k: b[k] - a[k] for k in a if b[k] != a[k]}

real_select = ui.select
def failing_select(context, obj): raise RuntimeError('injected late failure after the object was built')

results = {}
for name, op in (('planks', bpy.ops.astra_scene.planks), ('roof', bpy.ops.astra_scene.roof)):
    for mode in ('late failure', 'normal run'):
        ui.select = failing_select if mode == 'late failure' else real_select
        before = counts(); outcome = None
        try:
            outcome = sorted(op())
        except RuntimeError as e:
            outcome = 'raised: ' + str(e).strip().splitlines()[-1][:90]
        after = counts()
        results[f'{name} / {mode}'] = {'result': outcome, 'left behind': delta(before, after) or 'nothing'}
ui.select = real_select
print('ROLLBACKTEST', json.dumps({'add-on version': addon.bl_info['version'], 'results': results}))
