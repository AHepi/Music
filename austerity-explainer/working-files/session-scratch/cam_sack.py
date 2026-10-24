import bpy
from mathutils import Vector
c = bpy.data.objects['cam']; c.data.lens = 70
c.location = (-0.15, -0.35, 0.45)
c.rotation_euler = (Vector((-0.35, 0.33, 0.05)) - c.location).to_track_quat('-Z', 'Y').to_euler()
result = 'ok'
