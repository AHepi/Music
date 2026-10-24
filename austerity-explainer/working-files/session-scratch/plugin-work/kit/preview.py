"""Scratch: open a scene, add a camera, draw a small picture with Cycles CPU. Usage: blender -b FILE --python preview.py -- OUT.jpg [W H samples cam_x cam_y cam_z tx ty tz]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]
W, H, S = (int(a[1]), int(a[2]), int(a[3])) if len(a) > 3 else (480, 320, 24)
cam = tuple(float(v) for v in a[4:7]) if len(a) > 6 else (7.0, -8.0, 4.5)
target = tuple(float(v) for v in a[7:10]) if len(a) > 9 else (0.0, 0.0, 1.2)
sc = bpy.context.scene
cam_obj = bpy.data.objects.get('preview_cam')
if cam_obj is None:
    cd = bpy.data.cameras.new('preview_cam'); cd.lens = 35
    cam_obj = bpy.data.objects.new('preview_cam', cd); sc.collection.objects.link(cam_obj)
cam_obj.location = cam
cam_obj.rotation_euler = (Vector(target) - Vector(cam)).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam_obj
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = S; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
sc.render.filepath = out
if sc.world is None:
    sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
bpy.ops.render.render(write_still=True)
print('DRAWN', out)
