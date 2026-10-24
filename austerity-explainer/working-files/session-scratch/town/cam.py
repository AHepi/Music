import bpy, math
from mathutils import Vector
s = bpy.context.scene; cam = s.camera
def tj(x, y, z): return Vector((x, -z, y))   # three.js -> Blender
P, L, F = __VIEW__
cam.location = tj(*P); cam.data.angle = math.radians(F)
cam.rotation_euler = (tj(*L) - cam.location).to_track_quat('-Z', 'Y').to_euler()
result = {'cam': tuple(cam.location)}
