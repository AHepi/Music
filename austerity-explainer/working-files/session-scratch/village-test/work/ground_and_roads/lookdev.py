import sys, time, os, bpy
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
args = sys.argv[sys.argv.index('--') + 1:]
tag, kind, samples, width = args[0], args[1], int(args[2]), int(args[3])
which = args[4:] or ['View wide', 'View road_eye', 'View stable_close', 'View cottage_close']
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4; scene.cycles.diffuse_bounces = 2
scene.render.resolution_x = width; scene.render.resolution_y = int(width * 2 / 3); scene.render.resolution_percentage = 100
if kind == 'backdrop':
    scene.render.film_transparent = True
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.startswith('Backdrop'): o.hide_render = True
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
    ext = 'png'
else:
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
    ext = 'png'
for name in which:
    scene.camera = bpy.data.objects[name]
    t = time.time()
    scene.render.filepath = f'{base}/work/ground_and_roads/lk_{tag}_{kind}_{name.replace("View ", "")}.{ext}'
    bpy.ops.render.render(write_still=True)
    print('rendered', kind, name, round(time.time() - t, 1), flush=True)
