# What this does: opens the starting courtyard scene, runs stage_shapes.apply(look), and draws small EEVEE previews (960 x 640) from the hero camera and two close views.
# Run (on RunPod): /workspace/blender/blender -b --disable-autoexec --factory-startup START.blend -P render_preview.py -- LOOK OUT_PREFIX [engine] [views comma list]
import sys, time, os
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
look, prefix = a[0], a[1]
engine = a[2] if len(a) > 2 else 'BLENDER_EEVEE'
wanted = a[3].split(',') if len(a) > 3 else None
import stage_shapes
t0 = time.time()
rep = stage_shapes.apply({'look': look})
print('STAGE_SECONDS', round(time.time() - t0, 1), flush=True)
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = engine
if engine == 'BLENDER_EEVEE':
    sc.eevee.taa_render_samples = 48
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 640, 100
sc.render.image_settings.file_format = 'PNG'
cam = sc.camera
cd = cam.data
cd.dof.use_dof = False
views = [('hero', None, None, cd.lens), ('lantern', (-0.55, -0.25, 1.35), (0.95, 1.1, 1.25), 50.0), ('rocks', (-1.0, -1.8, 1.4), (-4.2, 3.4, 0.8), 36.0),
         ('basin', (3.0, 2.2, 1.3), (4.4, 4.2, 0.3), 45.0), ('wall', (9.0, 3.0, 1.6), (7.5, 10.5, 2.2), 40.0), ('gravel', (3.0, -6.2, 1.6), (5.8, -1.0, 0.0), 40.0),
         ('bridge', (-1.5, -3.6, 1.0), (-3.4, 0.6, 0.2), 40.0), ('veranda', (3.6, 5.3, 1.55), (-2.5, 0.8, 0.55), 24.0)]
if wanted:
    views = [v for v in views if v[0] in wanted]
for name, loc, tgt, lens in views:
    if loc is not None:
        cam.location = loc
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens
    sc.render.filepath = f'{prefix}_{look}_{name}.png'
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('RENDER', name, look, round(time.time() - t, 1), 's', flush=True)
print('DONE', look, round(time.time() - t0, 1), flush=True)
