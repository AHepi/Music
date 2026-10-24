# What this does: draws one small check picture of a built set from a chosen spot (EEVEE, 540 x 960),
# to look at a set's shape. Run: blender -b SET.blend --python overview_picture.py -- OUT.png X Y Z PITCH_DEGREES [YAW_DEGREES] [FOV_DEGREES]
import math
import sys

import bpy
from mathutils import Euler

arguments = sys.argv[sys.argv.index('--') + 1:]
out, x, y, z, pitch = arguments[0], *map(float, arguments[1:5])
yaw = float(arguments[5]) if len(arguments) > 5 else 0.0
fov = float(arguments[6]) if len(arguments) > 6 else 60.0
data = bpy.data.cameras.new('overview')
data.sensor_fit = 'VERTICAL'
data.angle_y = math.radians(fov)
data.clip_end = 2000
camera = bpy.data.objects.new('overview', data)
bpy.context.scene.collection.objects.link(camera)
camera.location = (x, y, z)
camera.rotation_euler = Euler((math.radians(90 + pitch), 0, math.radians(yaw)), 'XYZ')
scene = bpy.context.scene
scene.camera = camera
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.eevee.taa_render_samples = 8
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
