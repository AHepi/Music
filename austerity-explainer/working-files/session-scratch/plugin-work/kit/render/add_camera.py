import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
cd = bpy.data.cameras.new('Camera A'); cd.lens = 35
cam = bpy.data.objects.new('Camera A', cd); sc.collection.objects.link(cam)
cam.location = (7.0, -8.0, 4.5)
cam.rotation_euler = (Vector((0, 0, 1.2)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
bpy.ops.wm.save_as_mainfile(filepath=out)
