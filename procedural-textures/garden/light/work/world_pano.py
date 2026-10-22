# Minimal scene: world only + a sun lamp like the garden's; equirect panorama to check the sky layout, the glow direction and the camera/light split.
import bpy, sys, math, json
sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/garden/light')
import stage_light
from mathutils import Vector
a = sys.argv[sys.argv.index('--')+1:]
look, out = a[0], a[1]
mode = a[2] if len(a) > 2 else 'golden'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
ld = bpy.data.lights.new('Golden hour sun', 'SUN'); ld.energy = 8
so = bpy.data.objects.new('Golden hour sun', ld); sc.collection.objects.link(so)
so.rotation_euler = Vector((0.93, 0.24, -0.22)).normalized().to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
stage_light.build_world(look, mode)
cd = bpy.data.cameras.new('pano'); cd.type = 'PANO'
try: cd.panorama_type = 'EQUIRECTANGULAR'
except Exception: cd.cycles.panorama_type = 'EQUIRECTANGULAR'
cam = bpy.data.objects.new('pano', cd); sc.collection.objects.link(cam); cam.rotation_euler = (math.radians(90), 0, 0); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = False; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 512, 256, 100
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
sc.render.filepath = out
bpy.ops.render.render(write_still=True); print('PANO_DONE')
