import sys, time, os, bpy
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
args = sys.argv[sys.argv.index('--') + 1:]
tag = args[0]; width = int(args[1]); samples = int(args[2]); which = args[3:] or ['View wide', 'View road_eye', 'View stable_close', 'View cottage_close']
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = samples
scene.cycles.use_denoising = False
scene.render.resolution_x = width; scene.render.resolution_y = int(width * 2 / 3); scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'JPEG'; scene.render.image_settings.quality = 82
scene.cycles.max_bounces = 3; scene.cycles.diffuse_bounces = 2
for name in which:
    cam = bpy.data.objects[name]
    scene.camera = cam
    t = time.time()
    scene.render.filepath = f'{base}/pictures/{tag}_{name.replace("View ", "")}.jpg'
    bpy.ops.render.render(write_still=True)
    print('rendered', name, round(time.time() - t, 1), flush=True)
