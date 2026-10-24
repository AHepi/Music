import sys, math, json
import bpy
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
views = json.loads(args[0]) if args else []
outdir = args[1] if len(args) > 1 else '/tmp/prev'
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 10
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 3
sc.render.threads_mode = 'FIXED'
sc.render.threads = 2
sc.render.resolution_x, sc.render.resolution_y = 640, 420
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 80
try:
    sc.view_settings.view_transform = 'Standard'
except Exception:
    pass
for ob in bpy.data.objects:
    if ob.get('place_owner') == 'ground_and_roads' and ob.name.startswith('Backdrop'):
        ob.hide_render = True
cam_data = bpy.data.cameras.new('tmpcam'); cam_data.clip_end = 500; cam_data.lens = 28
cam = bpy.data.objects.new('Place cottages_south cam tmp', cam_data); sc.collection.objects.link(cam)
sc.camera = cam
for name, loc, target, lens in views:
    if isinstance(loc, str):
        sc.camera = bpy.data.objects[loc]
        sc.render.filepath = f'{outdir}/{name}.jpg'
        bpy.ops.render.render(write_still=True)
        print('rendered', name)
        sc.camera = cam
        continue
    cam.location = Vector(loc); cam_data.lens = lens
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{outdir}/{name}.jpg'
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
