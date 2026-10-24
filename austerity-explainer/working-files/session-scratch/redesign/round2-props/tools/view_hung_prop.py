# What this does: draws a prop as the film would see it, hung on a wall: the film's lens (60.4 degrees top
# to bottom on a 1080 x 1920 frame), level, from a given distance straight in front (or turned by an
# azimuth), the prop lifted so its base is LIFT metres up, a dull brick-coloured wall behind it in the
# plane given (the prop's +y side), dusk-ish light. Only a crop round the prop is drawn, at the film's
# full pixel size (Blender's render border), so the prop comes out at its real on-screen size.
# Run: DISPLAY=:96 blender -b --python view_hung_prop.py -- PROP.glb OUT.png DISTANCE LIFT WALL_Y [AZIMUTH] [EYE_HEIGHT] [MARGIN]
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village/props')
import prop_library as library  # noqa: E402
import render_contact_sheet as sheet  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
path, out, distance, lift, wall_y = arguments[0], arguments[1], float(arguments[2]), float(arguments[3]), float(arguments[4])
azimuth = float(arguments[5]) if len(arguments) > 5 else 0.0
eye = float(arguments[6]) if len(arguments) > 6 else 1.6
margin = float(arguments[7]) if len(arguments) > 7 else 0.05
library.empty_scene()
camera = sheet.stage((1080, 1920))
bpy.context.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
bpy.ops.import_scene.gltf(filepath=path)
for o in bpy.context.scene.objects:
    if o.parent is None and o.type == 'EMPTY':
        o.location.z += lift
bpy.context.view_layer.update()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name not in ('ground', 'wall')]
low, high = library.bounds(meshes)
# the wall: a dull brick-red plane at y = wall_y (prop space)
wall = bpy.data.meshes.new('wall')
wall.from_pydata([(-20, wall_y + 0.001, 0), (20, wall_y + 0.001, 0), (20, wall_y + 0.001, 6), (-20, wall_y + 0.001, 6)], [], [(0, 1, 2, 3)])
wall_object = bpy.data.objects.new('wall', wall); bpy.context.scene.collection.objects.link(wall_object)
brick = bpy.data.materials.new('wall'); brick.use_nodes = True
brick.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.16, 0.08, 0.06, 1)
brick.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
wall.materials.append(brick)
centre = (low + high) / 2
camera.data.sensor_fit = 'VERTICAL'
camera.data.angle_y = math.radians(60.4)
camera.location = (centre.x + distance * math.sin(math.radians(azimuth)), centre.y - distance * math.cos(math.radians(azimuth)), eye)
camera.rotation_euler = (math.radians(90), 0, math.radians(azimuth))
camera.data.clip_end = distance * 10
bpy.context.view_layer.update()
scene = bpy.context.scene
corners = [world_to_camera_view(scene, camera, Vector((x, y, z))) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
scene.render.use_border = True
scene.render.use_crop_to_border = True
scene.render.border_min_x = max(0.0, min(c.x for c in corners) - margin)
scene.render.border_max_x = min(1.0, max(c.x for c in corners) + margin)
scene.render.border_min_y = max(0.0, min(c.y for c in corners) - margin * 0.56)
scene.render.border_max_y = min(1.0, max(c.y for c in corners) + margin * 0.56)
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print('drew', path, 'from', distance, 'm')
