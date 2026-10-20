"""Plain note: our own small test. Turns on the transition ramp of a masked layer and reports where Ucupaint keeps the colour-ramp node (inside a sub-group called ~yPL Ramp_Copy)."""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from ucu_common import *
obj, mat = fresh_scene()
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
bpy.ops.wm.y_new_layer(name='Patches', type='COLOR', solid_color=(0.85,0.45,0.15), uv_map='UVMap')
bpy.ops.wm.y_new_layer_mask(name='PatchMask', type='VORONOI', texcoord_type='UV', uv_name='UVMap', blend_type='MULTIPLY')
yp, grp = get_yp(mat); L = yp.layers[0]; ch = L.channels[0]; ch.enable = True
ch.show_transition_ramp = True; ch.enable_transition_ramp = True
print('ch.tr_ramp =', repr(getattr(ch,'tr_ramp',None)), ' tr_ramp_blend =', repr(getattr(ch,'tr_ramp_blend',None)), 'enable now', ch.enable_transition_ramp)
for t in bpy.data.node_groups:
    for n in t.nodes:
        if n.type == 'VALTORGB': print('ramp node', n.name, 'in', t.name)
print([p for p in ch.bl_rna.properties.keys() if 'tr_' in p or 'ramp' in p])
