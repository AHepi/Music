# What this does (runs inside Blender on a rented card, for the fresh checker): opens the FIRST village, adds the same ground close-up camera the rebuild used
# (knee height, 4 m ahead of the road_eye camera, looking 3.5 m along the road; made the same way as in work/integrator/draw_round4.py) IN MEMORY ONLY, and
# draws it with the plugin's own render verb, so the before and after close-ups match. The scene file is never saved.
# Use: blender -b FIRST.blend --python draw_before_closeup.py -- PLUGIN_KIT_PLACE_KIT_FOLDER JOB.json
import os
import runpy
import sys

import bpy
import mathutils

kit_place_kit = sys.argv[sys.argv.index('--') + 1]
job_file = sys.argv[sys.argv.index('--') + 2]
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()


def ground_height(x, y):
    hit, location, _normal, _index, hit_object, _matrix = scene.ray_cast(depsgraph, mathutils.Vector((x, y, 60.0)), mathutils.Vector((0, 0, -1)))
    return (location.z, hit_object.name) if hit else (0.0, None)


road_eye = bpy.data.objects['View road_eye']
origin = road_eye.matrix_world.translation
forward = road_eye.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1))
forward.z = 0
forward.normalize()
start_x, start_y = origin.x + forward.x * 4.0, origin.y + forward.y * 4.0
start_z, start_hit = ground_height(start_x, start_y)
aim_x, aim_y = start_x + forward.x * 3.5, start_y + forward.y * 3.5
aim_z, aim_hit = ground_height(aim_x, aim_y)
data = bpy.data.cameras.new('Closeup ground ruts')
data.lens = 35.0
data.clip_start = 0.05
data.clip_end = 3000.0
camera = bpy.data.objects.new('Closeup ground ruts', data)
scene.collection.objects.link(camera)
position = mathutils.Vector((start_x, start_y, start_z + 0.55))
camera.location = position
camera.rotation_euler = (mathutils.Vector((aim_x, aim_y, aim_z)) - position).to_track_quat('-Z', 'Y').to_euler()
print('closeup ruts camera at', round(start_x, 2), round(start_y, 2), round(start_z + 0.55, 2), 'start hit', start_hit, 'aim', round(aim_z, 3), aim_hit)
sys.argv = [sys.argv[0], '--', 'render', '--where', 'on-card', '--job', job_file]
runpy.run_path(os.path.join(kit_place_kit, 'blender_run.py'), run_name='__main__')
