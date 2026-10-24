# What this does: draws a close view of one part of a prop .glb on the contact sheet's grey stage (EEVEE,
# small): the camera aimed at a chosen point from a chosen side and distance.
# Run: DISPLAY=:96 blender -b --python view_close.py -- PROP.glb OUT.png X Y Z DISTANCE AZIMUTH ELEVATION [SIZE]
#      (Blender coordinates of the point, metres; azimuth 0 = from the prop's -y side, positive = from its right)
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village/props')
import prop_library as library  # noqa: E402
import render_contact_sheet as sheet  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
path, out = arguments[0], arguments[1]
target = Vector(tuple(float(value) for value in arguments[2:5]))
distance, azimuth, elevation = float(arguments[5]), math.radians(float(arguments[6])), math.radians(float(arguments[7]))
size = int(arguments[8]) if len(arguments) > 8 else 640
library.empty_scene()
camera = sheet.stage((size, size))
bpy.ops.import_scene.gltf(filepath=path)
direction = Vector((math.sin(azimuth) * math.cos(elevation), -math.cos(azimuth) * math.cos(elevation), math.sin(elevation)))
camera.location = target + direction * distance
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.clip_start = distance / 100
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print('drew', out)
