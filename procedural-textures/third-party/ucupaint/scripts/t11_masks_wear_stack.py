"""Plain note: our own test. Builds a 'wear' stack the way our recipes layer things (base colour, brick pattern, soot patches,
moss patches) with Ucupaint layers and procedural masks, all by Python, then bakes the colour headless and saves it."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene()
bpy.context.scene.render.engine='CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
def step(label, fn):
    try: r = fn(); print('OK  ', label); return r
    except Exception as e: print('FAIL', label, repr(e)[:250]); return None
step('Base colour', lambda: bpy.ops.wm.y_new_layer(name='Base', type='COLOR', solid_color=(0.6,0.2,0.1), uv_map='UVMap'))
step('Bricks', lambda: bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap', blend_type='MULTIPLY'))
step('Soot layer', lambda: bpy.ops.wm.y_new_layer(name='Soot', type='COLOR', solid_color=(0.04,0.03,0.025), uv_map='UVMap'))
step('Soot mask NOISE', lambda: bpy.ops.wm.y_new_layer_mask(name='SootMask', type='NOISE', texcoord_type='UV', uv_name='UVMap', blend_type='MULTIPLY'))
yp, grp = get_yp(mat)
soot = yp.layers[0]
print('soot masks:', [(m.name, m.type) for m in soot.masks], 'mask props:', [p for p in soot.masks[0].bl_rna.properties.keys() if p not in ('rna_type',)][:50] if soot.masks else None)
step('Soot mask modifier RAMP', lambda: bpy.ops.wm.y_new_mask_modifier(type='RAMP') if hasattr(bpy.ops.wm,'y_new_mask_modifier') else None)
step('Moss layer', lambda: bpy.ops.wm.y_new_layer(name='Moss', type='COLOR', solid_color=(0.15,0.4,0.08), uv_map='UVMap'))
step('Moss mask VORONOI', lambda: bpy.ops.wm.y_new_layer_mask(name='MossMask', type='VORONOI', texcoord_type='UV', uv_name='UVMap', blend_type='MULTIPLY'))
yp, grp = get_yp(mat)
print('layers top->bottom:', [(l.name, l.type, [m.type for m in l.masks]) for l in yp.layers])
# tweak: mask scale, soot opacity
try:
    for l in yp.layers:
        for m in l.masks: m.scale = (3,3,3) if l.name=='Soot' else (2,2,2)
except Exception as e: print('mask scale fail', repr(e)[:150])
yp.layers['Soot'].channels[0].intensity_value = 0.9
ov = ui_override(); t=time.time()
with bpy.context.temp_override(**ov):
    bpy.ops.wm.y_bake_channels(width=512, height=512, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
print('bake %.2fs' % (time.time()-t))
im = bpy.data.images['Ucupaint Material Color']; im.filepath_raw=os.path.join(OUT,'wear_stack_colour.png'); im.file_format='PNG'; im.save()
print('GROUP layer test'); step('layer GROUP', lambda: bpy.ops.wm.y_new_layer(name='Folder', type='GROUP', uv_map='UVMap'))
print('layers now:', [(l.name, l.type, l.parent_idx) for l in get_yp(mat)[0].layers])
