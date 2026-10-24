# Leans the scene camera 5 degrees (Blender Euler Y = +5) without changing its turn or tilt, for the code check of check_shot.py's lean sign.
import math
import bpy
camera = bpy.context.scene.camera
camera.rotation_mode = 'XYZ'
camera.rotation_euler.y = math.radians(5.0)
bpy.context.view_layer.update()
print('roll_camera: camera leaned to', tuple(round(math.degrees(v), 3) for v in camera.rotation_euler))
