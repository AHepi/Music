"""Plain note: our own test. Shows which input choices a layer channel offers, and what the Roughness picture looks like
when a colour noise layer feeds a single-number (value) channel in different ways."""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
obj, mat = fresh_scene()
bpy.context.scene.render.engine='CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
bpy.ops.wm.y_new_layer(name='Cloud', type='NOISE', uv_map='UVMap')
yp, grp = get_yp(mat)
l = yp.layers[0]; ch = l.channels[2]; ch.enable = True
print('Roughness channel layer_input items:', [i.identifier for i in ch.bl_rna.properties['layer_input'].enum_items], 'current', ch.layer_input)
try: print('socket_input_name items:', [i.identifier for i in ch.bl_rna.properties['socket_input_name'].enum_items], 'current', ch.socket_input_name)
except Exception as e: print('socket_input_name', repr(e))
print('other props: gamma_space', ch.gamma_space, 'use_clamp', ch.use_clamp, 'swizzle', ch.swizzle_input_mode if hasattr(ch,'swizzle_input_mode') else None)
def bake_and_stats(tag):
    ov = ui_override()
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.y_bake_channels(width=128, height=128, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
    im = bpy.data.images['Ucupaint Material Roughness']
    a = np.empty(128*128*4, dtype=np.float32); im.pixels.foreach_get(a); a=a.reshape(-1,4)
    print(f'{tag}: R mean {a[:,0].mean():.3f} G mean {a[:,1].mean():.3f} B mean {a[:,2].mean():.3f}; R==G==B max diff {np.abs(a[:,0]-a[:,1]).max():.3f}')
    # remove baked pictures so next try is clean
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.y_delete_baked_channel_images()
    for i in list(bpy.data.images): 
        if i.users==0 or i.name.startswith('Ucupaint Material'): bpy.data.images.remove(i)
bake_and_stats('default (Color socket, swizzle RGB)')
print('source output sockets:', [o.name for o in __import__('importlib').import_module(MOD+'.common').get_layer_source(l).outputs])
for sock, sw in (('Fac','RGB'), ('Color','R'), ('Color','G'), ('Fac','R')):
    try:
        ch.socket_input_name = sock; ch.swizzle_input_mode = sw
        bake_and_stats(f'socket_input_name={sock} swizzle={sw}')
    except Exception as e: print('FAIL', sock, sw, repr(e)[:200])
