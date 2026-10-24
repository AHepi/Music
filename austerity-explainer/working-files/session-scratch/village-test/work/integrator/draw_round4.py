# What this does (runs inside Blender on a rented card): opens the finished village, adds two close-up cameras of the ground IN MEMORY ONLY
# (the file is never saved, so the audited file stays exactly as it was), then runs the plugin's own `render` verb on the job file.
# One close-up looks along the wheel ruts of the high road from knee height; the other looks at the nearest standing water (a puddle) from low down.
# Use: blender -b FINISHED.blend --python draw_round4.py -- PLUGIN_KIT_PLACE_KIT_FOLDER JOB.json
import math
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


def add_camera(name, position, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = 0.05
    data.clip_end = 3000.0
    camera = bpy.data.objects.new(name, data)
    scene.collection.objects.link(camera)
    camera.location = position
    camera.rotation_euler = (target - position).to_track_quat('-Z', 'Y').to_euler()
    return camera


road_eye = bpy.data.objects['View road_eye']
origin = road_eye.matrix_world.translation
forward = (road_eye.matrix_world.to_quaternion() @ mathutils.Vector((0, 0, -1)))
forward.z = 0
forward.normalize()

# Close-up 1: knee height, looking along the road ahead of the road_eye camera.
start_x, start_y = origin.x + forward.x * 4.0, origin.y + forward.y * 4.0
start_z, _ = ground_height(start_x, start_y)
aim_x, aim_y = start_x + forward.x * 3.5, start_y + forward.y * 3.5
aim_z, _ = ground_height(aim_x, aim_y)
add_camera('Closeup ground ruts', mathutils.Vector((start_x, start_y, start_z + 0.55)), mathutils.Vector((aim_x, aim_y, aim_z)), 35.0)

# Close-up 2: the puddle nearest to the road_eye camera, seen from low down and a little way off.
puddles = bpy.data.objects.get('PK puddles')
if puddles is not None and len(puddles.data.vertices) > 0:
    best = min((puddles.matrix_world @ v.co for v in puddles.data.vertices), key=lambda p: (p.x - origin.x) ** 2 + (p.y - origin.y) ** 2)
    towards = mathutils.Vector((origin.x - best.x, origin.y - best.y, 0))
    towards.normalize()
    camera_x, camera_y = best.x + towards.x * 2.2, best.y + towards.y * 2.2
    camera_z, _ = ground_height(camera_x, camera_y)
    add_camera('Closeup ground puddle', mathutils.Vector((camera_x, camera_y, camera_z + 0.5)), mathutils.Vector((best.x, best.y, best.z)), 35.0)
    print('closeup puddle at', tuple(round(c, 2) for c in best))
else:
    print('there is no PK puddles object; only the ruts close-up exists')
print('closeup ruts camera at', round(start_x, 2), round(start_y, 2), round(start_z + 0.55, 2))

sys.argv = [sys.argv[0], '--', 'render', '--where', 'on-card', '--job', job_file]
runpy.run_path(os.path.join(kit_place_kit, 'blender_run.py'), run_name='__main__')
