"""Plain note: our own test. For each kind of procedural layer Ucupaint offers, makes a one-layer stack on a plane, bakes the colour
at 512 px headless and saves it (so another script can measure whether the tile wraps without a seam), and reports the time."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np
from ucu_common import *
OUT = sys.argv[sys.argv.index('--')+1]; os.makedirs(OUT, exist_ok=True)
TYPES = ['BRICK','CHECKER','GRADIENT','MAGIC','MUSGRAVE','NOISE','VORONOI','WAVE','GABOR','COLOR','HEMI','EDGE_DETECT','AO','BACKGROUND']
for typ in TYPES:
    for scale in ((1,1,1),(2.5,2.5,2.5)) if typ in ('NOISE','VORONOI','BRICK','MUSGRAVE','WAVE','GABOR') else ((1,1,1),):
        obj, mat = fresh_scene()
        bpy.context.scene.render.engine='CYCLES'
        bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
        BakeMod = importlib.import_module(MOD + '.Bake'); BakeMod.YBakeChannels.no_layer_using = False
        try:
            bpy.ops.wm.y_new_layer(name=typ, type=typ, uv_map='UVMap')
        except Exception as e:
            print(f'{typ}: FAILED to add layer: {repr(e)[:200]}'); continue
        yp, grp = get_yp(mat); l = yp.layers[0]
        try: l.scale = scale
        except Exception as e: print('  scale not settable', repr(e)[:100])
        ov = ui_override(); t = time.time()
        try:
            with bpy.context.temp_override(**ov):
                bpy.ops.wm.y_bake_channels(width=512, height=512, samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')
        except Exception as e:
            print(f'{typ}: BAKE FAILED {repr(e)[:200]}'); continue
        im = bpy.data.images.get('Ucupaint Material Color')
        if not im: print(typ, 'no colour image'); continue
        im.filepath_raw = os.path.join(OUT, f'{typ}_scale{scale[0]}.png'); im.file_format='PNG'; im.save()
        a = np.empty(512*512*4, dtype=np.float32); im.pixels.foreach_get(a)
        print(f'{typ} scale {scale[0]}: baked in {time.time()-t:.2f}s, mean {a.reshape(-1,4)[:,:3].mean():.3f}, source node: {l.source}')
