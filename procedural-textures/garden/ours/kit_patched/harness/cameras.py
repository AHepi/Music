# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# CAMERAS from the set file's `cameras` table: by numbers (location and a rotation quaternion), by "look at" (location, a point to aim at, vertical field of view), or the
# scene's own camera ("from_file"). A camera entry may name a `scene` (it exists only there), a picture `size`, and an `aim_at_feature`: a feature another part reports
# (for example the ground-cracks layer's strongest flag crack) that the camera is re-aimed at, so a close view always has its subject in it; the report is a small JSON file
# (feature_report.json) the builder writes; if it is missing the entry's own look_at is used and the camera says so.
# dot_angle(camera, plate_height) is the tangent of the angle one PLATE dot covers (what WK SCALE needs): a 540 x 960 test picture uses the plate's value.
import json
import math
import os

import bpy
from mathutils import Vector


def _make(name, location, look_at=None, quaternion_wxyz=None, fov_vertical=40.0):
    data = bpy.data.cameras.new(name)
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(fov_vertical)
    data.clip_start, data.clip_end = 0.05, 2000.0
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = Vector(location)
    if quaternion_wxyz is not None:
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = quaternion_wxyz
    else:
        obj.rotation_euler = (Vector(look_at) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


def load_feature(spec, search_dirs):
    """The reported position of the feature the entry wants to aim at, or None."""
    want = spec.get('aim_at_feature')
    if not want:
        return None
    for folder in search_dirs:
        path = os.path.join(folder, 'feature_report.json')
        if os.path.exists(path):
            try:
                report = json.load(open(path))
            except ValueError:
                continue
            item = report.get(want['feature'])
            if item and 'position' in item:
                y = item['position'][1]
                lo, hi = want.get('within_y', [-1e9, 1e9])
                if lo <= y <= hi:
                    return item['position']
    return None


def make_all(settings, scene_id, search_dirs=()):
    """{name: camera object, ...} for the cameras that belong to this scene (and the scene's own camera as the entry with from_file)."""
    scene = bpy.context.scene
    result, notes = {}, {}
    for spec in settings.get('cameras', []):
        if spec.get('scene') not in (None, scene_id):
            continue
        name = spec['name']
        if spec.get('from_file'):
            result[name] = scene.camera
            continue
        look_at = spec.get('look_at')
        feature = load_feature(spec, search_dirs)
        if feature is not None:
            look_at = feature
            notes[name] = 'aimed at the reported feature'
        elif spec.get('aim_at_feature'):
            notes[name] = 'feature report missing: aimed at the entry\'s own look_at'
        result[name] = _make('wk_' + name, spec['location'], look_at=look_at, quaternion_wxyz=spec.get('quaternion_wxyz'), fov_vertical=spec.get('fov_v', 40.0))
    return result, notes


def fov_vertical(camera):
    return math.degrees(camera.data.angle_y)


def dot_angle(camera, plate_height_dots):
    return 2.0 * math.tan(camera.data.angle_y / 2.0) / float(plate_height_dots)


def spec_of(settings, name):
    for spec in settings.get('cameras', []):
        if spec['name'] == name:
            return spec
    raise KeyError(name)
