# What this does: draws a lettered prop as the film would see it: the film's lens (60.4 degrees top to
# bottom on a 1080 x 1920 frame), level, from a given distance straight in front, at dusk-ish light.
# Only a crop round the prop is drawn (Blender's render border), at the film's full pixel size, so the
# letters come out at their real on-screen size without drawing the whole frame.
# Run: blender -b --python film_distance_check.py -- PROP.glb OUT.png DISTANCE_METRES LIFT_METRES
#      (LIFT: how high the prop's bottom is hung above the ground, e.g. a gate board over a gate)
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village/props')
import prop_library as library  # noqa: E402
import render_contact_sheet as sheet  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
path, out, distance, lift = arguments[0], arguments[1], float(arguments[2]), float(arguments[3])
library.empty_scene()
camera = sheet.stage((1080, 1920))
bpy.context.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
bpy.ops.import_scene.gltf(filepath=path)
for o in bpy.context.scene.objects:
    if o.parent is None and o.type == 'EMPTY':
        o.location.z += lift
bpy.context.view_layer.update()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name != 'ground']
low, high = library.bounds(meshes)
centre = (low + high) / 2
camera.data.sensor_fit = 'VERTICAL'
camera.data.angle_y = math.radians(60.4)
camera.location = (centre.x, centre.y - distance, 1.7)
camera.rotation_euler = (math.radians(90), 0, 0)
camera.data.clip_end = distance * 10
bpy.context.view_layer.update()   # so the camera's new place is used below
# the render border: the prop's corners as the camera sees them, with a margin
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
scene = bpy.context.scene
corners = [world_to_camera_view(scene, camera, Vector((x, y, z))) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
scene.render.use_border = True
scene.render.use_crop_to_border = True
scene.render.border_min_x = max(0.0, min(c.x for c in corners) - 0.03)
scene.render.border_max_x = min(1.0, max(c.x for c in corners) + 0.03)
scene.render.border_min_y = max(0.0, min(c.y for c in corners) - 0.02)
scene.render.border_max_y = min(1.0, max(c.y for c in corners) + 0.02)
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print('drew', path, 'from', distance, 'm')
