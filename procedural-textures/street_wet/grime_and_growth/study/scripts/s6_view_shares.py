# What this does (plain words): STUDY ONLY, saves nothing. Shoots one ray through every dot of a coarse grid (90 x 160) of each plate camera and counts what each ray hits: which MATERIAL and which
# FAMILY of object. This gives "share of the picture" for each thing weathering could go on, for the cameras the street tests use. In the lockout shot file it also counts the props.
# Run: blender -b --disable-autoexec FILE --python s6_view_shares.py -- OUT.json [lockout]
import json, math, re, sys
from collections import Counter
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view  # noqa: F401
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
args = sys.argv[sys.argv.index('--') + 1:]
out_path = args[0]
is_lockout = len(args) > 1


def make_camera(name, location, quaternion, fov, aspect=(1536, 2730)):
    data = bpy.data.cameras.new(name)
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(fov)
    cam = bpy.data.objects.new(name, data)
    scene.collection.objects.link(cam)
    cam.location = Vector(location)
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = quaternion
    return cam


cams = {'main': scene.camera}
if not is_lockout:
    cams['lockout_camera'] = make_camera('lockout_plate', (-1.0, 1.2, 1.69709), (0.65516, 0.753675, -0.039498, -0.034335), 44.0)
    cams['notice_camera'] = make_camera('notice_plate', (2.99313, 16.35381, 3.18819), (0.705836, 0.705836, 0.042367, 0.042367), 64.4)
    cams['close_road'] = make_camera('close_road', (0.5, 6.0, 1.0), (1, 0, 0, 0), 38.0)
    cams['close_road'].rotation_mode = 'XYZ'
    cams['close_road'].rotation_euler = (Vector((0.0, 11.0, 0.45)) - cams['close_road'].location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
FAMILY = [(re.compile(r'^(left|right)_row_[ab]_cottage_\d+_(\w+?)(_\d+)?$'), lambda m: f'{m.group(1)}_row {m.group(2)}'), (re.compile(r'^gas_lamp_\d+_(\w+)$'), lambda m: 'gas_lamp ' + m.group(1))]


def family(name, obj):
    for rx, f in FAMILY:
        m = rx.match(name)
        if m:
            return f(m)
    if obj.users_collection and obj.users_collection[0].name in ('props', 'signs'):
        return f'[{obj.users_collection[0].name}] ' + re.sub(r'(_\d+|\.\d+)$', '', name)
    return re.sub(r'(_\d+|\.\d+)$', '', name)


W, H = 90, 160
res = {}
for cname, cam in cams.items():
    # rays through the dots of the camera frame (vertical field of view, aspect 1536:2730)
    data = cam.data
    tan_v = math.tan(data.angle_y / 2)
    tan_h = tan_v * (1536 / 2730)
    mats, fams, sky = Counter(), Counter(), 0
    origin = cam.matrix_world.translation
    rot = cam.matrix_world.to_quaternion()
    total = W * H
    for j in range(H):
        for i in range(W):
            sx = ((i + 0.5) / W * 2 - 1) * tan_h
            sy = (1 - (j + 0.5) / H * 2) * tan_v
            d = rot @ Vector((sx, sy, -1.0)).normalized()
            hit, loc, nor, idx, obj, mtx = scene.ray_cast(deps, origin, d)
            if not hit:
                sky += 1
                continue
            mat = None
            if obj.type == 'MESH' and idx < len(obj.data.polygons):
                mi = obj.data.polygons[idx].material_index
                if mi < len(obj.material_slots) and obj.material_slots[mi].material:
                    mat = obj.material_slots[mi].material.name
            mats[mat] += 1
            fams[family(obj.name, obj)] += 1
    res[cname] = dict(rays=total, sky_no_hit=round(sky / total, 4), materials={k: round(v / total, 4) for k, v in mats.most_common(40)}, families={k: round(v / total, 4) for k, v in fams.most_common(40)})
json.dump(res, open(out_path, 'w'), indent=1)
print('SHARES DONE')
