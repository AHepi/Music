"""Plain note: our own test. Builds a 3-layer Ucupaint stack (solid colour, brick with bump, noise with bump on top at reduced
opacity), turns on the Colour, Roughness and Normal channels per layer, bakes all channels headless and saves the pictures."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; SIZE = int(sys.argv[sys.argv.index('--')+2])
os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene()
bpy.context.scene.render.engine = 'CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
bpy.ops.wm.y_new_layer(name='Base', type='COLOR', solid_color=(0.55,0.25,0.12), uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Cloud', type='NOISE', uv_map='UVMap')
yp, grp = get_yp(mat)
print('channels', [(i,c.name,c.type) for i,c in enumerate(yp.channels)])
for l in yp.layers:
    print(l.name, 'ch props:', [p for p in l.channels[0].bl_rna.properties.keys()][:60]) if l.name=='Cloud' else None
for l in yp.layers:
    for i in (0,2,3):
        l.channels[i].enable = True
    l.channels[3].normal_map_type = 'BUMP_MAP'
yp.layers['Cloud'].channels[0].intensity_value = 0.4
yp.layers['Cloud'].channels[0].blend_type = 'MULTIPLY'
print('layer order top->bottom:', [l.name for l in yp.layers])
ov = ui_override()
t = time.time()
with bpy.context.temp_override(**ov):
    r = bpy.ops.wm.y_bake_channels(width=SIZE, height=SIZE, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
print('BAKE', r, '%.2fs' % (time.time()-t))
for im in bpy.data.images:
    a = np.empty(im.size[0]*im.size[1]*4, dtype=np.float32); im.pixels.foreach_get(a)
    print('  ', repr(im.name), tuple(im.size), im.colorspace_settings.name, 'float' if im.is_float else '8bit', 'mean=%.4f' % a.mean(), 'min=%.3f max=%.3f' % (a.min(), a.max()))
    if im.name != 'Render Result':
        im.filepath_raw = os.path.join(OUT, im.name.replace(' ','_') + '.png'); im.file_format='PNG'; im.save()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'stack.blend'), copy=True)
