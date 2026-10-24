import sys, math, json, time
import bpy
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
views = json.loads(args[0]); outdir = args[1]
w = int(args[2]) if len(args) > 2 else 640
h = int(args[3]) if len(args) > 3 else 420
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 10; sc.cycles.use_denoising = False; sc.cycles.max_bounces = 3
sc.render.threads_mode = 'FIXED'; sc.render.threads = 2
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 80
try: sc.view_settings.view_transform = 'Standard'
except Exception: pass
for ob in bpy.data.objects:
    if ob.name.startswith('Backdrop'): ob.hide_render = True
cd = bpy.data.cameras.new('tmpcam'); cd.clip_end = 500
cam = bpy.data.objects.new('Place props cam tmp', cd); sc.collection.objects.link(cam)
for name, loc, tgt, lens in views:
    t = time.time()
    if isinstance(loc, str):
        sc.camera = bpy.data.objects[loc]
    else:
        cam.location = Vector(loc); cd.lens = lens
        cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = cam
    sc.render.filepath = f'{outdir}/{name}.jpg'
    bpy.ops.render.render(write_still=True)
    print('rendered', name, round(time.time() - t, 1))
