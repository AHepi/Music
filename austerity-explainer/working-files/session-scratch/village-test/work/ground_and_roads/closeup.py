import sys, bpy, math
from mathutils import Vector
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
args = sys.argv[sys.argv.index('--') + 1:]
tag = args[0]; px, py, pz, ax, ay, az = [float(v) for v in args[1:7]]; width = int(args[7]); lens = float(args[8]) if len(args) > 8 else 35
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 24; scene.cycles.use_denoising = True
scene.render.resolution_x = width; scene.render.resolution_y = int(width * 2 / 3)
cam = bpy.data.objects.new('dbgcam', bpy.data.cameras.new('dbgcam')); scene.collection.objects.link(cam)
cam.data.lens = lens; cam.data.clip_end = 3000
cam.location = (px, py, pz); cam.rotation_euler = (Vector((ax, ay, az)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = f'{base}/work/ground_and_roads/cu_{tag}.png'
bpy.ops.render.render(write_still=True)
print('done', flush=True)
