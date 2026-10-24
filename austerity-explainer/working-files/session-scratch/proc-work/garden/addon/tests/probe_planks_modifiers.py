# What this does: checks whether the add-on's detail and pigment tools accept the add-on's own planks, stones and roof
# (they all carry modifiers), and what happens when the plank bevel is removed first. Tiny scene, no rendering.
import sys, importlib.util, traceback
sys.dont_write_bytecode = True
import bpy
ARGS = sys.argv[sys.argv.index('--') + 1:]; FOLDER = ARGS[0]
name = 'astra_painted_workbench'
spec = importlib.util.spec_from_file_location(name, FOLDER + '/__init__.py', submodule_search_locations=[FOLDER])
mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
import astra_painted_workbench.runtime.api as api
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work')
from astra_loader import apply_blender_52_shim; apply_blender_52_shim(api)
bpy.ops.wm.read_factory_settings(use_empty=True)
def attempt(label, fn):
    try:
        out = fn(); print('OK   ', label, '->', str(out)[:140]); return out
    except Exception as e:
        print('FAIL ', label, '->', type(e).__name__, str(e)[:170]); return None
run = api.create_planks(length=4, width=1.3, count=14, seed=5)
plank = run.children[0] if run.children else None
print('plank object:', plank.name, 'modifiers:', [m.name for m in plank.modifiers], 'materials:', len(plank.data.materials), [m.name for m in plank.data.materials])
attempt('apply_detail timber on add-on planks (bevel modifier present)', lambda: api.apply_detail(plank, 'timber', 5))
attempt('apply_pigment timber on add-on planks (bevel present)', lambda: api.apply_pigment(plank, 0, 'timber', 'Y', 41, .7))
stone = api.create_stone('S', api.StoneSpec(length=1, width=.8, height=.5))
attempt('apply_detail stone on add-on stone (GN modifier)', lambda: api.apply_detail(stone, 'stone', 5))
roof = api.create_roof('R', api.RoofSpec(width=4, half_depth=1.5, rise=.6))
attempt('apply_pigment on add-on roof (GN modifier)', lambda: api.apply_pigment(roof, 0, 'timber'))
# remove bevel then retry
for m in list(plank.modifiers): plank.modifiers.remove(m)
slot = 0
attempt('apply_pigment timber after removing bevel', lambda: api.apply_pigment(plank, slot, 'timber', 'Y', 41, .7))
print('plank materials now:', [s.material.name if s.material else None for s in plank.material_slots][:4], 'slots:', len(plank.material_slots))
if plank.get('astra_surface_transaction'):
    api.restore_surface(plank)
attempt('apply_detail timber after removing bevel', lambda: api.apply_detail(plank, 'timber', 5))
print('slot0 material tree nodes:', len(plank.material_slots[0].material.node_tree.nodes) if plank.material_slots[0].material else None)
