# What this does (plain words): STUDY ONLY, saves nothing. For the street's plate cameras it measures, with Blender's own camera maths, how big one plate dot is on the ground (across the street
# and along it) and on the right-hand cottage wall, at several distances. The painter sees the plate at about 0.45 of its size, so one painter dot is 1 / 0.45 = 2.2 plate dots.
import json, math, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
W, H = 1536, 2730
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100


def make_camera(name, location, quaternion, fov):
    data = bpy.data.cameras.new(name)
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(fov)
    cam = bpy.data.objects.new(name, data)
    scene.collection.objects.link(cam)
    cam.location = Vector(location)
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = quaternion
    return cam


cams = {'main': scene.camera,
        'lockout': make_camera('lockout_plate', (-1.0, 1.2, 1.69709), (0.65516, 0.753675, -0.039498, -0.034335), 44.0),
        'notice': make_camera('notice_plate', (2.99313, 16.35381, 3.18819), (0.705836, 0.705836, 0.042367, 0.042367), 64.4)}
bpy.context.view_layer.update()


def ground_z(x, y):
    hit, loc, n, i, obj, m = scene.ray_cast(deps, Vector((x, y, 40.0)), Vector((0, 0, -1)))
    return loc.z if hit else None


def px(cam, p):
    c = world_to_camera_view(scene, cam, Vector(p))
    return c.x * W, (1 - c.y) * H, c.z


out = {}
for cname, cam in cams.items():
    rows = []
    for y in (4, 6, 8, 12, 16, 24, 32, 48):
        # the ground point straight ahead of the camera's x
        x = cam.location.x if cname != 'notice' else 0.0
        z = ground_z(x, y)
        if z is None:
            continue
        a = px(cam, (x, y, z)); b = px(cam, (x, y + 0.1, ground_z(x, y + 0.1))); c = px(cam, (x + 0.1, y, ground_z(x + 0.1, y)))
        if a[2] <= 0:
            continue
        along = abs(b[1] - a[1]) / 0.1          # plate dots (rows) per metre along the street
        across = abs(c[0] - a[0]) / 0.1         # plate dots (columns) per metre across the street
        dist = (cam.matrix_world.translation - Vector((x, y, z))).length
        rows.append(dict(y=y, distance_m=round(dist, 1), plate_dots_per_m_across=round(across, 1), plate_dots_per_m_along=round(along, 1),
                         painter_dot_mm_across=round(1000 / (across * 0.45), 1) if across else None, painter_dot_mm_along=round(1000 / (along * 0.45), 1) if along else None))
    # the right-hand wall face (x = 4.15), 1.5 m above the floor
    wall = []
    for y in (4, 6, 8, 12, 16, 24, 32):
        z = ground_z(3.3, y) + 1.5
        a = px(cam, (4.15, y, z)); b = px(cam, (4.15, y + 0.1, z)); c = px(cam, (4.15, y, z + 0.1))
        if a[2] <= 0 or not (0 <= a[0] <= W and 0 <= a[1] <= H):
            continue
        along = abs(b[0] - a[0]) / 0.1
        up = abs(c[1] - a[1]) / 0.1
        wall.append(dict(y=y, plate_dots_per_m_along_wall=round(along, 1), plate_dots_per_m_up=round(up, 1), painter_dot_mm_along=round(1000 / (along * 0.45), 1) if along else None, painter_dot_mm_up=round(1000 / (up * 0.45), 1)))
    out[cname] = dict(ground=rows, right_wall=wall, camera=[round(v, 2) for v in cam.location])
json.dump(out, open(sys.argv[sys.argv.index('--') + 1], 'w'), indent=1)
