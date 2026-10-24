# What this does: draws one prop .glb from a chosen side (EEVEE, small), on the contact sheet's grey
# stage, to look at it closely. Run: blender -b --python view_prop.py -- PROP.glb OUT.png AZIMUTH_DEGREES ELEVATION_DEGREES [SIZE]
# (azimuth 0 = straight in front, looking at the prop's -y face; positive = from its right)
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village/props')
import prop_library as library  # noqa: E402
import render_contact_sheet as sheet  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
path, out, azimuth, elevation = arguments[0], arguments[1], float(arguments[2]), float(arguments[3])
size = int(arguments[4]) if len(arguments) > 4 else 640
library.empty_scene()
camera = sheet.stage((size, size))
bpy.ops.import_scene.gltf(filepath=path)
bpy.context.view_layer.update()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name != 'ground']
low, high = library.bounds(meshes)
centre = (low + high) / 2
radius = (high - low).length / 2
direction = Vector((math.sin(math.radians(azimuth)) * math.cos(math.radians(elevation)), -math.cos(math.radians(azimuth)) * math.cos(math.radians(elevation)), math.sin(math.radians(elevation))))
distance = radius / math.sin(camera.data.angle / 2) * 1.02
camera.location = centre + direction * distance
camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.clip_end = distance * 4; camera.data.clip_start = distance / 200
bpy.context.scene.render.filepath = out
bpy.ops.render.render(write_still=True)
