# What this does: measures a shot in Blender exactly, for the shot checker (paper-film/tools/check_shot.py).
# Run it after a script has dressed the scene (or on a saved .blend). It reads a check file (JSON) that
# names the shot's props as groups of objects, and writes into an output folder:
#   ids.png          every named group drawn in its own flat colour, as the camera sees it (what hides what)
#   solo/NAME.png    each group drawn alone, so the parts hidden behind other things count too
#   facts.json       the camera (place, height above the surface under it, turn, tilt, roll, view angle
#                    top to bottom), where the street's lines meet on screen (worked out from the camera,
#                    so it is exact), the lights, and for each group: its distance, size, top and bottom,
#                    what it stands on (another group, or the set) and how far above it, and how many
#                    metres one pixel covers at its distance (to turn pixel faults into metre fixes)
# The flat pictures are drawn with Blender's quick Workbench engine (seconds, not minutes).
# Run (needs the same virtual screen the EEVEE pictures use):
#   DISPLAY=:96 blender -b street.blend --python assemble_notice_corner.py --python shot_facts.py -- \
#       --check examples/notice-corner/shot-check.json --facts OUT_FOLDER [--view end]
#       [--camera-at x,y,z --yaw DEGREES [--pitch DEGREES] --fov DEGREES]
# --view is read by the scene script, which leaves its camera there. --camera-at, --yaw (the turn, + is left
# of straight up +y), --pitch (the tilt, + is up; only with --yaw) and --fov (the view angle, top to bottom)
# try another camera without changing the scene script.
# Each object belongs to the group whose name pattern matches its own name, or failing that the name of
# the nearest thing it hangs from; * stands for any letters (e.g. "kitchen-chair*"). Objects matching the
# check file's "sky" pattern (default "sky_dome*") are left out of the flat pictures.

import fnmatch
import json
import math
import os
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default=None):
    return arguments[arguments.index(name) + 1] if name in arguments else default

check = json.load(open(option('--check')))
out_folder = option('--facts')
os.makedirs(os.path.join(out_folder, 'solo'), exist_ok=True)
WIDTH, HEIGHT = (int(v) for v in check.get('size', [1080, 1920]))

scene = bpy.context.scene
camera = scene.camera
# an optional trial camera, to ask "what if the camera stood here?" without changing the scene script
if option('--camera-at'):
    camera.location = Vector(float(v) for v in option('--camera-at').split(','))
if option('--yaw'):
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = Euler((math.radians(90 + float(option('--pitch', '0'))), 0, math.radians(float(option('--yaw')))), 'XYZ')
if option('--fov'):
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.angle_y = math.radians(float(option('--fov')))
bpy.context.view_layer.update()

# ------------------------------------------------------------------ which mesh belongs to which group
groups = check['groups']
def group_of(o):
    # nearest first: the object's own name, then what it hangs from, then that one's holder, ...
    for name in [o.name] + [a.name for a in iter_ancestors(o)]:
        for group, patterns in groups.items():
            if any(fnmatch.fnmatch(name, p) for p in patterns):
                return group
    return None

def iter_ancestors(o):
    while o.parent:
        o = o.parent
        yield o

meshes = [o for o in scene.objects if o.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT') and not o.hide_render]
members = {g: [] for g in groups}
for o in meshes:
    g = group_of(o)
    if g:
        members[g].append(o)
missing = [g for g, objects in members.items() if not objects]

# ------------------------------------------------------------------ flat colour pictures (Workbench)
def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

# colours far apart in 8-bit sRGB, so they decode reliably; black is the sky, dark grey everything else
PALETTE = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
           (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (220, 190, 255), (170, 110, 40), (255, 250, 200),
           (128, 0, 0), (170, 255, 195), (128, 128, 0), (255, 215, 180), (0, 0, 128), (255, 255, 255)]
SET_COLOUR = (64, 64, 64)
names = [g for g in groups if members[g]]
if len(names) > len(PALETTE):
    raise SystemExit(f'shot_facts: at most {len(PALETTE)} groups')
colour_of = {g: PALETTE[i] for i, g in enumerate(names)}

def setup_flat():
    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light = 'FLAT'
    shading.color_type = 'OBJECT'
    shading.show_shadows = False
    shading.show_cavity = False
    shading.show_object_outline = False
    shading.show_specular_highlight = False
    shading.show_xray = False
    scene.display.render_aa = 'OFF'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('facts world')
    scene.world.color = (0, 0, 0)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.film_transparent = False
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = WIDTH, HEIGHT, 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'

def paint(o, colour):
    o.color = (*(srgb_to_linear(c) for c in colour), 1.0)

def draw(path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

setup_flat()
sky = [o for o in meshes if fnmatch.fnmatch(o.name, check.get('sky', 'sky_dome*'))]
for o in meshes:
    g = group_of(o)
    paint(o, colour_of[g] if g in colour_of else SET_COLOUR)
was_hidden = {o.name: o.hide_render for o in meshes}
for o in sky:
    o.hide_render = True
draw(os.path.join(out_folder, 'ids.png'))
for g in names:
    for o in meshes:
        o.hide_render = group_of(o) != g
    draw(os.path.join(out_folder, 'solo', f'{g}.png'))
for o in meshes:
    o.hide_render = was_hidden[o.name]

# ------------------------------------------------------------------ the camera and the lines
def on_screen(point):
    p = world_to_camera_view(scene, camera, point)
    return [round(p.x, 5), round(1 - p.y, 5)], p.z   # across (0 left), down (0 top), depth

def lowest_surface_below(point, ignore=()):
    """The surfaces straight below `point`: the first one met (what something stands on) and the object
    it belongs to, and the lowest upward-facing one (the ground; the undersides of slabs don't count)."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    origin, first, first_object, lowest = point.copy(), None, None, None
    for _ in range(16):
        hit, location, normal, index, hit_object, matrix = scene.ray_cast(depsgraph, origin, Vector((0, 0, -1)))
        if not hit:
            break
        origin = location - Vector((0, 0, 0.001))
        if hit_object.name in ignore or hit_object.hide_render:
            continue
        if first is None:   # whatever way its surface faces (some models face inward)
            first, first_object = location.copy(), hit_object
        if normal.z > 0.5:
            lowest = location.copy()
    return first, first_object, lowest or first

eye = camera.matrix_world.translation.copy()
rotation = camera.matrix_world.to_euler('XYZ')
looking = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
ground_under_camera, _, _ = lowest_surface_below(eye)
# the view angle top to bottom: with sensor fit AUTO, Blender's angle spans the frame's longer side
fit = camera.data.sensor_fit
if fit == 'VERTICAL' or (fit == 'AUTO' and HEIGHT > WIDTH):
    vertical_fov = camera.data.angle_y if fit == 'VERTICAL' else camera.data.angle
else:
    across = camera.data.angle_x if fit == 'HORIZONTAL' else camera.data.angle   # the angle side to side
    vertical_fov = 2 * math.atan(math.tan(across / 2) * HEIGHT / WIDTH)
facts = {
    'about': 'Written by shot_facts.py. Screen positions are fractions: across 0 = left edge, down 0 = top edge. Blender metres.',
    'size': [WIDTH, HEIGHT],
    'camera': {
        'at': [round(v, 4) for v in eye],
        'eye_height': round(eye.z - ground_under_camera.z, 3) if ground_under_camera else None,
        'turn_degrees': round(math.degrees(math.atan2(-looking.x, looking.y)), 3),   # + is left of straight up +y
        'tilt_degrees': round(math.degrees(math.asin(max(-1, min(1, looking.z)))), 3),   # + is looking up
        'roll_degrees': round(math.degrees(rotation.y), 3),
        'vertical_fov_degrees': round(math.degrees(vertical_fov), 3),
    },
    'lines_meet': {},
    'lights': [],
    'groups': {},
    'missing_groups': missing,
}
for light in scene.objects:
    if light.type != 'LIGHT' or light.hide_render:
        continue
    where, depth = on_screen(light.matrix_world.translation)
    facts['lights'].append({'name': light.name, 'kind': light.data.type, 'at': [round(v, 3) for v in light.matrix_world.translation],
                            'on_screen': where if depth > 0 else None, 'energy': round(light.data.energy, 1),
                            'colour': [round(c, 3) for c in light.data.color]})
for name, direction in check.get('lines', {}).items():
    far = eye + Vector(direction).normalized() * 1e5
    where, depth = on_screen(far)
    facts['lines_meet'][name] = where if depth > 0 else None

metres_per_pixel = lambda distance: 2 * distance * math.tan(vertical_fov / 2) / HEIGHT
depsgraph_now = bpy.context.evaluated_depsgraph_get()
for g in names:
    points = [o.matrix_world @ Vector(c) for o in members[g] for c in o.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    centre = (low + high) / 2
    distance = (centre - eye).dot(looking)
    # from just above the group's foot, passing through its own parts, so the first surface met is what it stands on.
    # Five spots across its base, keeping the highest surface met: one line can slip between the planks of a seat
    own = {o.name for o in members[g]}
    first, first_object, lowest = None, None, None
    for fx, fy in ((0, 0), (-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25)):
        spot = Vector((centre.x + fx * (high.x - low.x), centre.y + fy * (high.y - low.y), low.z + 0.05))
        hit, hit_object, deepest = lowest_surface_below(spot, ignore=own)
        if hit is not None and (first is None or hit.z > first.z):
            first, first_object = hit, hit_object
        if deepest is not None and (lowest is None or deepest.z < lowest.z):
            lowest = deepest
    # sunk into the ground? Looking up from its bottom, an upward-facing surface of the set (not of any prop) within
    # half its height means it stands below that surface: record that as negative air
    sunk = None
    origin = Vector((centre.x, centre.y, low.z + 0.001))
    for _ in range(16):
        hit, location, normal, index, hit_object, matrix = scene.ray_cast(depsgraph_now, origin, Vector((0, 0, 1)), distance=0.5 * (high.z - low.z))
        if not hit:
            break
        if hit_object.name not in own and not hit_object.hide_render and group_of(hit_object) is None and normal.z > 0.5:
            sunk = location.copy()   # keep looking: the highest such surface is the street's own (a buried layer lies lower)
        origin = location + Vector((0, 0, 0.001))
    corners = [on_screen(p) for p in points]
    in_front = [c for c, depth in corners if depth > 0]
    facts['groups'][g] = {
        'objects': len(members[g]),
        'centre': [round(v, 3) for v in centre], 'bottom': round(low.z, 3), 'top': round(high.z, 3),
        'width': round(high.x - low.x, 3), 'depth': round(high.y - low.y, 3), 'height': round(high.z - low.z, 3),
        'distance': round(distance, 3),
        'metres_per_pixel': round(metres_per_pixel(max(distance, 0.1)), 6),
        # sunk: negative; otherwise the air under it (never below 0: looking up found nothing it is sunk into)
        'stands_above_surface_below': round(low.z - sunk.z, 3) if sunk else (max(0.0, round(low.z - first.z, 3)) if first else None),
        'stands_above_ground': round(low.z - lowest.z, 3) if lowest else None,
        'stands_on': (group_of(first_object) or 'the set') if first_object else None,
        # where the whole group would land on screen if nothing hid it and the frame went on for ever
        'screen_box_unclipped': [round(min(c[0] for c in in_front), 4), round(min(c[1] for c in in_front), 4),
                                 round(max(c[0] for c in in_front), 4), round(max(c[1] for c in in_front), 4)] if in_front else None,
        'colour': colour_of[g],
    }
# for each prop that should rest on another (a lantern on a chair), the top of that support where the prop would
# stand: the first surface of the support's own parts met coming down over the support's middle (the seat, not the back)
facts['support_tops'] = {}
depsgraph = bpy.context.evaluated_depsgraph_get()
for g, support in check.get('stands_on', {}).items():
    if support not in facts['groups'] or g not in facts['groups']:
        continue
    info = facts['groups'][support]
    x, y = info['centre'][0], info['centre'][1]
    tops = []
    for fx, fy in ((0, 0), (-0.15, -0.15), (0.15, -0.15), (-0.15, 0.15), (0.15, 0.15)):
        origin = Vector((x + fx * info['width'], y + fy * info['depth'], info['bottom'] + 0.75 * info['height']))
        for _ in range(16):
            hit, location, normal, index, hit_object, matrix = scene.ray_cast(depsgraph, origin, Vector((0, 0, -1)))
            if not hit:
                break
            if group_of(hit_object) == support and normal.z > 0.5:
                tops.append(location.z)
                break
            origin = location - Vector((0, 0, 0.001))
    if tops:
        facts['support_tops'][g] = {'support': support, 'top': round(sorted(tops)[len(tops) // 2], 3)}
with open(os.path.join(out_folder, 'facts.json'), 'w') as handle:
    json.dump(facts, handle, indent=1)
print('shot_facts: done', out_folder)
