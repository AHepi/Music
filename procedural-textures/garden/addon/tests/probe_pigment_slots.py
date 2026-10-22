# What this does: checks that the pigment tool covers only one material slot per object (the add-on's planks have seven)
import sys, importlib.util
sys.dont_write_bytecode = True
import bpy
FOLDER = sys.argv[sys.argv.index('--') + 1]
name = 'astra_painted_workbench'
spec = importlib.util.spec_from_file_location(name, FOLDER + '/__init__.py', submodule_search_locations=[FOLDER])
mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
import astra_painted_workbench.runtime.api as api
bpy.ops.wm.read_factory_settings(use_empty=True)
run = api.create_planks(length=4, width=1.3, count=14, seed=5)
plank = run.children[0]
for m in list(plank.modifiers): plank.modifiers.remove(m)
used = sorted({p.material_index for p in plank.data.polygons})
print('slots used by faces:', used)
api.apply_pigment(plank, 0, 'timber', 'Y', 41, .7)
try:
    api.apply_pigment(plank, 1, 'timber', 'Y', 41, .7); print('slot 1 second pigment: OK')
except Exception as e:
    print('slot 1 second pigment: FAIL', str(e)[:160])
print('slots now:', [s.material.name for s in plank.material_slots])
