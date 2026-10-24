"""What this does (scratch, round 5 W4 helper): run after assemble_works.py in the same Blender run. For each named
object group, counts how many of its points (vertices and face middles) the cameras of W1, W2 and W3 can see, at
the plate spot (plate lens) and at five spots along each slide to the composed spot (film lens), in every state those
views are drawn in. A point counts as seen when it is inside the frame and a ray from the camera reaches it first.
So 0 everywhere means the group cannot change those views' plates or films.
It runs assemble_works.py itself (in its own namespace, so it can dress each state with the script's own set_state).
Use: blender -b works-lane.blend --python seen_from_views.py -- --assemble PATH/assemble_works.py --groups PAT,PAT ... --out FILE.json"""
import fnmatch
import json
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
patterns = option('--groups', 'jacket-and-cap,w4-upturned-crate,tin-mug-and-wages').split(',')
out = option('--out')
ASSEMBLE = option('--assemble')
names = {'__name__': '__main__', '__file__': ASSEMBLE}
exec(compile(open(ASSEMBLE).read(), ASSEMBLE, 'exec'), names)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920


def objects_of(pattern):
    found = []
    for o in bpy.data.objects:
        if fnmatch.fnmatch(o.name, pattern):
            found.append(o)
            found.extend(o.children_recursive)
    return [o for o in found if o.type == 'MESH']


def points_of(o, depsgraph):
    evaluated = o.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    world = o.matrix_world
    points = [world @ v.co for v in mesh.vertices] + [world @ p.center for p in mesh.polygons]
    evaluated.to_mesh_clear()
    return points


def seen(camera, objects, depsgraph):
    own = set(o.name for o in objects)
    count, total = 0, 0
    origin = camera.matrix_world.translation
    for o in objects:
        if o.hide_render:
            continue
        for p in points_of(o, depsgraph):
            on = world_to_camera_view(scene, camera, p)
            if not (0 <= on.x <= 1 and 0 <= on.y <= 1 and on.z > 0):
                continue
            total += 1
            direction = (p - origin)
            distance = direction.length
            hit, where, normal, index, what, matrix = scene.ray_cast(depsgraph, origin, direction.normalized(), distance=distance + 0.01)
            if hit and (what.name in own or (where - p).length < 0.004):
                count += 1
    return count, total


g = names
views = {'w1': ['quiet', 'working', 'men gone', 'quiet, no men'], 'w2': ['quiet', 'slowed'], 'w3': ['quiet']}
result = {}
for view, states in views.items():
    for state in states:
        g['set_state'](state, plate=True, men_2_in_plate=(state == 'slowed'))
        for o in bpy.data.objects:          # ray casts see what the render sees
            o.hide_viewport = o.hide_render
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        spots = [('plate', g['PLATE_FOV'], None)]
        if g['views']()[view]['composed']:
            plate_xy = Vector(g['views']()[view]['plate']); composed_xy = Vector(g['views']()[view]['composed'])
            for k in range(5):
                spots.append((f'slide {k / 4:.2f}', g['FILM_FOV'], k / 4))
        for spot_name, fov, share in spots:
            camera = g['put_camera'](view, 'plate', fov)
            if share is not None:
                a = g['camera_spot'](view, 'plate'); b = g['camera_spot'](view, 'composed')
                camera.location = a.lerp(b, share)
                bpy.context.view_layer.update()
            for pattern in patterns:
                objects = objects_of(pattern)
                count, total = seen(camera, objects, depsgraph)
                result.setdefault(pattern, {})[f'{view} {state} {spot_name}'] = [count, total]
for o in bpy.data.objects:
    o.hide_viewport = False
summary = {pattern: {key: value for key, value in spots.items() if value[0] > 0} for pattern, spots in result.items()}
print('seen_from_views:', json.dumps(summary, indent=1))
if out:
    with open(out, 'w') as handle:
        json.dump({'seen (points seen, points in frame)': result, 'any seen': summary}, handle, indent=1)
