import bpy
from mathutils import Vector
c = bpy.data.objects['cam']; c.data.lens = 60
c.location = (0.6, -1.0, 1.3)
c.rotation_euler = (Vector((0.0, 0.75, 1.1)) - c.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
result = 'ok'
