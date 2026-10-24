import sys, time, os, bpy
args = sys.argv[sys.argv.index('--') + 1:]
tag, width, samples = args[0], int(args[1]), int(args[2]); which = args[3:] or ['View wide','View road_eye','View stable_close','View cottage_close']
base='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest/pics'
scene = bpy.context.scene
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = samples; scene.cycles.use_denoising = False
scene.render.resolution_x = width; scene.render.resolution_y = int(width*2/3); scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'JPEG'; scene.render.image_settings.quality = 80
scene.cycles.max_bounces = 3; scene.cycles.diffuse_bounces = 2
# give materialless objects a plain colour for the look (preview only, never saved)
cols = {'tree.bark': (0.16,0.11,0.07,1), 'plant.foliage': (0.09,0.16,0.06,1), 'stone.rock': (0.3,0.3,0.28,1)}
for o in bpy.data.objects:
    r = o.get('place_role')
    if o.type=='MESH' and r in cols and not o.material_slots:
        m = bpy.data.materials.new('prev_'+r); m.use_nodes=True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = cols[r]; m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.9
        o.data.materials.append(m)
for name in which:
    scene.camera = bpy.data.objects[name]; t=time.time()
    scene.render.filepath = f'{base}/{tag}_{name.replace("View ","")}.jpg'
    bpy.ops.render.render(write_still=True); print('rendered', name, round(time.time()-t,1), flush=True)
