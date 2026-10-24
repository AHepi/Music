import bpy
from mathutils import Vector
cam = bpy.data.objects['cam']
cam.location = (-2.4, -4.3, 2.5)
cam.rotation_euler = (Vector((-0.3, 0, 1.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
result = 'ok'
