"""Plain note: our own test. A soft noise mask on an orange layer over dark ground, with Ucupaint's transition ramp turned on and set to a
dark band: we want to see whether a dark rim appears where the mask fades (like the painted outlines in our references)."""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene(); bpy.context.scene.render.engine='CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
bpy.ops.wm.y_new_layer(name='Ground', type='COLOR', solid_color=(0.25,0.12,0.06), uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Patches', type='COLOR', solid_color=(0.85,0.45,0.15), uv_map='UVMap')
bpy.ops.wm.y_new_layer_mask(name='PatchMask', type='NOISE', texcoord_type='UV', uv_name='UVMap', blend_type='MULTIPLY')
yp, grp = get_yp(mat); L = yp.layers[0]; ch = L.channels[0]; ch.enable = True
L.masks[0].scale = (4,4,4)
ch.show_transition_ramp = True; ch.enable_transition_ramp = True
def bake(tag):
    ov = ui_override()
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.y_bake_channels(width=512, height=512, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
    im = bpy.data.images['Ucupaint Material Color']; im.filepath_raw=os.path.join(OUT, tag+'.png'); im.file_format='PNG'; im.save()
    with bpy.context.temp_override(**ov): bpy.ops.wm.y_delete_baked_channel_images()
    for i in list(bpy.data.images):
        if i.name.startswith('Ucupaint Material'): bpy.data.images.remove(i)
bake('ramp_default')
for t in bpy.data.node_groups:
    for n in t.nodes:
        if n.type == 'VALTORGB' and n.name == '_RAMP':
            cr = n.color_ramp; print('ramp default elements', [(round(e.position,2), tuple(round(c,2) for c in e.color)) for e in cr.elements])
            cr.elements[0].color = (0.02,0.01,0.0,1.0); cr.elements[1].color = (0.02,0.01,0.0,1.0)
            cr.elements[0].position = 0.0; cr.elements[1].position = 1.0
ch.transition_ramp_intensity_value = 1.0
bake('ramp_dark')
