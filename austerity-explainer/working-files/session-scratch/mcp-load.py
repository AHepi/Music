import bpy, math
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
bpy.ops.import_scene.gltf(filepath='/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/factory-a.glb')
scene = bpy.context.scene
cam_data = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam)
cam.location = (3.6, -7.5, 2.4); cam.rotation_euler = (math.radians(80), 0, math.radians(26)); scene.camera = cam
sun = bpy.data.lights.new('key', 'SUN'); sun.energy = 3; sun_o = bpy.data.objects.new('key', sun); scene.collection.objects.link(sun_o); sun_o.rotation_euler = (math.radians(50), 0, math.radians(-40))
scene.world = bpy.data.worlds.new('w'); scene.world.color = (0.05, 0.06, 0.07)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.render.resolution_x = 1080; scene.render.resolution_y = 1920
result = {'objects': len(bpy.data.objects), 'meshes': len([o for o in bpy.data.objects if o.type == 'MESH'])}
