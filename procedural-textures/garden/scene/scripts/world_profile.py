# What this does: tiny equirectangular render (256x128, 2 samples, Cycles) of the scene's own world exactly as saved (objects hidden), to see the real sky colour
#   at each height above the horizon. In-memory copy; saves one small PNG; no .blend.
import bpy, math, sys
sc = bpy.context.scene
for o in bpy.data.objects: o.hide_render = True
cd = bpy.data.cameras.new('pano'); cd.type = 'PANO'
try: cd.panorama_type = 'EQUIRECTANGULAR'
except Exception: cd.cycles.panorama_type = 'EQUIRECTANGULAR'
cam = bpy.data.objects.new('pano', cd); sc.collection.objects.link(cam); cam.rotation_euler = (math.radians(90), 0, 0); sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.samples = 2; sc.cycles.use_denoising = False; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 256, 128, 100
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
sc.render.filepath = sys.argv[sys.argv.index('--') + 1]
bpy.ops.render.render(write_still=True); print('WORLD_DONE')
