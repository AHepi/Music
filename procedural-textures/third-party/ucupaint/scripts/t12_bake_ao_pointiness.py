"""Plain note: our own test. On a bevelled, unwrapped cube, asks Ucupaint to bake an AO (corner shadow) layer and a POINTINESS (edge wear)
layer headless. These commands expect a screen and a pop-up first, so we first set the values the pop-up would normally set."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene('Cube')
bpy.data.objects.remove(obj); bpy.ops.mesh.primitive_cube_add(size=1.0); obj = bpy.context.active_object; obj.data.materials.append(mat)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.bevel(offset=0.06, segments=2); bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02); bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.scene.render.engine='CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
yp, grp = get_yp(mat)
BTL = importlib.import_module(MOD + '.BakeToLayer').YBakeToLayer
BTL.entity = None; BTL.obj = obj; BTL.scene = bpy.context.scene
BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
ov = ui_override()
for typ in ('AO', 'POINTINESS'):
    t = time.time()
    try:
        with bpy.context.temp_override(**ov):
            r = bpy.ops.wm.y_bake_to_layer(type=typ, name=typ, width=256, height=256, samples=8 if typ=='AO' else 1, margin=4, uv_map=obj.data.uv_layers.active.name, bake_device='CPU', target_type='LAYER', blend_type='MULTIPLY' if typ=='AO' else 'ADD', fxaa=False, denoise=False, channel_idx='0', normal_map_type='BUMP_MAP')
        print(typ, 'returned', r, '%.1fs' % (time.time()-t))
    except Exception as e:
        print(typ, 'FAILED', repr(e)[:400])
yp, grp = get_yp(mat)
print('layers:', [(l.name, l.type) for l in yp.layers])
for im in bpy.data.images:
    if im.size[0] > 8:
        a = np.empty(im.size[0]*im.size[1]*4, dtype=np.float32); im.pixels.foreach_get(a)
        print('image', im.name, tuple(im.size), 'rgb mean %.3f min %.3f max %.3f' % (a.reshape(-1,4)[:,:3].mean(), a.min(), a.max()))
        im.filepath_raw = os.path.join(OUT, im.name.replace(' ','_')+'.png'); im.file_format='PNG'; im.save()
