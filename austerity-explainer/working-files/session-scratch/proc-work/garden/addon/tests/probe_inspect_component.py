# What this does: on Blender 5.2.2, checks whether the add-on's inspect_component reports the real roof/stone settings
import sys, importlib.util
sys.dont_write_bytecode = True
import bpy
FOLDER = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-upload-021'
name = 'astra_painted_workbench'
spec = importlib.util.spec_from_file_location(name, FOLDER + '/__init__.py', submodule_search_locations=[FOLDER])
mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
import astra_painted_workbench.runtime.api as api
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work')
from astra_loader import apply_blender_52_shim; apply_blender_52_shim(api)
bpy.ops.wm.read_factory_settings(use_empty=True)
st = api.create_stone('S', api.StoneSpec(length=2.0, width=1.2, height=0.9, seed=77))
from astra_painted_workbench.runtime.vendor.courtyard_tools import api as ct
info = ct.inspect_component(st)
print('SPEC says length 2.0 width 1.2 height 0.9 seed 77')
print('inspect_component controls ->', info['controls'])
m = next(x for x in st.modifiers if x.type == 'NODES')
print('real value via properties:', {s.name: getattr(m.properties.inputs, s.identifier).value for s in m.node_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name != 'Geometry'})
