"""Plain note: our own test. Builds a small Ucupaint layer stack on a plane (brick layer over a solid colour, a noise mask),
asks Ucupaint to bake its channels to pictures (CPU, no screen), then lists and saves the pictures it made."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]
SIZE = int(sys.argv[sys.argv.index('--')+2])
os.makedirs(OUT, exist_ok=True)
obj, mat = fresh_scene()
bpy.context.scene.render.engine = 'CYCLES'
bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
bpy.ops.wm.y_new_layer(name='Base', type='COLOR', solid_color=(0.55,0.25,0.12), uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap')
yp, grp = get_yp(mat)
print('layers', [l.name for l in yp.layers])
import importlib
BakeMod = importlib.import_module(MOD + '.Bake')
BakeMod.YBakeChannels.no_layer_using = False   # workaround: 'invoke' normally sets this, but background Blender calls 'execute' directly
t=time.time()
try:
    ov = ui_override(); print('ui override:', {k:(v.type if hasattr(v,'type') else str(v)) for k,v in (ov or {}).items()})
    with bpy.context.temp_override(**ov):
      r = bpy.ops.wm.y_bake_channels(width=SIZE, height=SIZE, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
    print('BAKE returned', r, '%.1fs' % (time.time()-t))
except Exception as e:
    import traceback; traceback.print_exc(); print('BAKE FAILED', repr(e)[:400])
print('images now:')
for im in bpy.data.images:
    a = np.empty(im.size[0]*im.size[1]*4, dtype=np.float32); im.pixels.foreach_get(a)
    print('  ', im.name, tuple(im.size), im.colorspace_settings.name, 'float' if im.is_float else '8bit', 'mean=%.4f' % a.mean(), 'min=%.3f max=%.3f' % (a.min(), a.max()), 'users', im.users, 'filepath', repr(im.filepath))
    if im.name != 'Render Result' and im.size[0] >= 8:
        im.filepath_raw = os.path.join(OUT, im.name.replace(' ','_').replace('/','_') + '.png')
        im.file_format = 'PNG'
        try: im.save()
        except Exception as e: print('save fail', e)
