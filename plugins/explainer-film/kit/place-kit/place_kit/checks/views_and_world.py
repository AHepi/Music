"""What this does: gathers four more kinds of FACTS for the place audit (scene_audit.py); calculators/place_audit_check.py judges them.
  views      the scene's render size, whether the place settings say "for_film": true, and every view camera (every camera except the kit's own
             "Place ... cam" previews): its lens, clip end, how deep the farthest object in front of it lies, and what a grid of rays through its
             frame hits (rays that go below the horizon and hit nothing see past the edge of the ground into empty sky).
  world      objects with the role backdrop that cast shadows, large far objects that cast shadows, a haze volume in the world, and how
             wide the place is (place_span_m: the widest horizontal extent of the visible objects that are not backdrop; a crate on a 3 m
             square of ground spans 3 m, a whole place usually 30 m or more), so the judge can tell a prop built alone from a place.
  sun        the scene's sun lamp (the strongest one when there are several), its direction, and per view the share of the ground points the
             view sees that are shadowed from the sun, with the objects that shadow them.
  lettering  every sign, notice, placard, poster, name board or book (found by its role first, then by those whole words in its name; "board"
             alone is not enough, so floorboards and skirting boards stay out) and whether it carries lettering: a picture texture, a shape made
             from text, or a text-made or lettering object on it.
A concrete example: a 4 m hall with the sun low behind it (9 degrees up) throws a shadow about 25 m long (4 / tan 9 degrees), and hazy hills
that cast shadows block the sun as well; that view's sun facts say most of its ground points are shadowed, by the hall first. Needs Blender (bpy).
"""
import math
import re

import bpy
from mathutils import Vector

from .. import names, roles as roles_module, scene_read

LETTERED_WORDS = re.compile(r'\b(signs?|signboards?|signposts?|notices?|noticeboards?|placards?|posters?|name ?boards?|nameboards?|books?)\b', re.I)
LETTERING_NEIGHBOUR_WORDS = re.compile(r'\b(letters?|lettering|text|label|labels|decal|decals|masthead|title|words?)\b', re.I)
RAY_GRID_LONG_SIDE = 32
BELOW_HORIZON_Z = -math.sin(math.radians(0.5))     # a ray counts as below the horizon from half a degree down (a ray along the horizon may miss everything)
TOUCH_METRES = 0.03


def plain_words(text):
    """'ShopSign_02.001' -> 'shop sign': camel case split, underscores, dots, dashes and digits turned into spaces."""
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text or '')
    return re.sub(r'[\s_\-.\d]+', ' ', text).strip().lower()


def is_preview_camera(obj):
    return obj.name.startswith(names.CAMERA_PREFIX) and ' cam' in obj.name


def view_cameras(scene=None):
    scene = scene or bpy.context.scene
    return [o for o in scene.objects if o.type == 'CAMERA' and not is_preview_camera(o)]


def _bounds_corners(obj):
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def _ray_directions(camera, scene):
    """Unit directions through a grid of the camera's frame (the render's shape), top row first."""
    frame = [Vector(c) for c in camera.data.view_frame(scene=scene)]      # top right, bottom right, bottom left, top left (camera space)
    top_right, bottom_right, bottom_left, top_left = frame
    width, height = (top_right - top_left).length, (top_left - bottom_left).length
    if width >= height:
        columns, rows = RAY_GRID_LONG_SIDE, max(2, int(round(RAY_GRID_LONG_SIDE * height / max(width, 1e-9))))
    else:
        rows, columns = RAY_GRID_LONG_SIDE, max(2, int(round(RAY_GRID_LONG_SIDE * width / max(height, 1e-9))))
    turn = camera.matrix_world.to_3x3()
    directions = []
    for row in range(rows):
        v = (row + 0.5) / rows
        for column in range(columns):
            u = (column + 0.5) / columns
            point = top_left + (top_right - top_left) * u + (bottom_left - top_left) * v
            directions.append((turn @ point).normalized())
    return directions, columns, rows


def strongest_sun(scene=None):
    scene = scene or bpy.context.scene
    suns = [o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN' and not o.hide_render and getattr(o.data, 'energy', 0) > 0]
    return max(suns, key=lambda o: o.data.energy) if suns else None


def toward_sun(sun):
    """The unit direction from the ground toward the sun (a sun lamp shines along its own -Z)."""
    return (sun.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def sun_angles(direction):
    """(compass angle, height angle) in degrees, in the kit's own way of writing a sun: (cos a cos h, sin a cos h, sin h)."""
    height = math.degrees(math.asin(max(-1.0, min(1.0, direction.z))))
    compass = math.degrees(math.atan2(direction.y, direction.x)) % 360.0
    return compass, height


def shadow_caster(scene, depsgraph, start, direction, steps=8):
    """The first object toward the sun that casts a shadow, or None. Blender's ray cast also hits objects whose shadow is turned off
    (Object > Visibility > Shadow), so the ray goes on through them."""
    for _ in range(steps):
        hit, location, _normal, _index, blocker, _matrix = scene.ray_cast(depsgraph, start, direction, distance=100000.0)
        if not hit or blocker is None:
            return None
        if getattr(blocker, 'visible_shadow', True):
            return blocker
        start = location + direction * 0.01
    return None


def gather(settings, objects, by_object):
    """{'views': ..., 'world': ..., 'sun': ...} for the audit (see the note at the top)."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    role_of = {name: (info.get('role') or '') for name, info in by_object.items()}
    sun = strongest_sun(scene)
    sun_direction = toward_sun(sun) if sun else None
    cameras = []
    for camera in view_cameras(scene):
        origin = camera.matrix_world.translation.copy()
        forward = (camera.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
        farthest, farthest_name = 0.0, None
        for obj in objects:
            depth = max((corner - origin).dot(forward) for corner in _bounds_corners(obj))
            if depth > farthest:
                farthest, farthest_name = depth, obj.name
        row = {'name': camera.name, 'scene_camera': scene.camera == camera, 'kind': camera.data.type, 'lens_mm': round(float(camera.data.lens), 2),
               'clip_start_m': round(float(camera.data.clip_start), 3), 'clip_end_m': round(float(camera.data.clip_end), 2),
               'farthest_depth_m': round(farthest, 2), 'farthest_object': farthest_name, 'view_size': None}
        if 'view_size' in camera.keys():
            try:
                row['view_size'] = [int(v) for v in camera['view_size']][:2]
            except (TypeError, ValueError):
                row['view_size'] = None
        if camera.data.type == 'PERSP':
            directions, columns, rows = _ray_directions(camera, scene)
            below, empty_below, ground_points = 0, 0, []
            for direction in directions:
                hit, location, normal, _index, hit_object, _matrix = scene.ray_cast(depsgraph, origin, direction, distance=camera.data.clip_end)
                if direction.z < BELOW_HORIZON_Z:
                    below += 1
                    if not hit:
                        empty_below += 1
                if hit and hit_object is not None and role_of.get(hit_object.name, '').startswith('ground.'):
                    ground_points.append((location.copy(), normal.copy()))
            row.update({'rays': len(directions), 'ray_grid': [columns, rows], 'rays_below_horizon': below, 'empty_below_horizon': empty_below,
                        'empty_below_horizon_share': (empty_below / below) if below else 0.0, 'ground_points': len(ground_points)})
            if sun_direction is not None and ground_points:
                shadowed, by_name = 0, {}
                for location, normal in ground_points:
                    blocker = shadow_caster(scene, depsgraph, location + normal * 0.02 + sun_direction * 0.02, sun_direction)
                    if blocker is not None:
                        shadowed += 1
                        by_name[blocker.name] = by_name.get(blocker.name, 0) + 1
                ranked = sorted(by_name.items(), key=lambda item: -item[1])
                row['sun'] = {'ground_points': len(ground_points), 'shadowed': shadowed, 'shadowed_share': shadowed / len(ground_points),
                              'shadowed_by': [{'object': n, 'points': c} for n, c in ranked[:5]]}
        cameras.append(row)
    views = {'for_film': settings.get('for_film') is True, 'render_size': [int(scene.render.resolution_x), int(scene.render.resolution_y),
             int(scene.render.resolution_percentage)], 'cameras': cameras}

    # the world: backdrops and large far things that cast shadows, a haze volume
    backdrop_shadows, far_shadows = [], []
    from .. import house_numbers
    world_numbers = house_numbers.value('place_audit.world')
    centres = [c.matrix_world.translation for c in view_cameras(scene)] or [Vector((0.0, 0.0, 0.0))]
    for obj in objects:
        role = role_of.get(obj.name, '')
        casts = bool(getattr(obj, 'visible_shadow', True))
        corners = _bounds_corners(obj)
        low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        size = max(high - low)
        middle = (low + high) / 2
        distance = min((middle - centre).length for centre in centres)
        if roles_module.role_class(role) == 'backdrop':
            if casts:
                backdrop_shadows.append({'name': obj.name, 'distance_m': round(distance, 1), 'size_m': round(size, 1)})
        elif casts and distance > world_numbers['far_object_metres'] and size > world_numbers['large_object_metres']:
            far_shadows.append({'name': obj.name, 'role': role or None, 'distance_m': round(distance, 1), 'size_m': round(size, 1)})
    haze = False
    if scene.world is not None and scene.world.use_nodes and scene.world.node_tree is not None:
        for node in scene.world.node_tree.nodes:
            if node.type == 'OUTPUT_WORLD' and node.inputs.get('Volume') is not None and node.inputs['Volume'].is_linked:
                haze = True
    backdrops = [o.name for o in objects if roles_module.role_class(role_of.get(o.name, '')) == 'backdrop']
    span = 0.0
    lows, highs = [], []
    for obj in objects:
        if roles_module.role_class(role_of.get(obj.name, '')) == 'backdrop':
            continue
        corners = _bounds_corners(obj)
        lows.append((min(c.x for c in corners), min(c.y for c in corners)))
        highs.append((max(c.x for c in corners), max(c.y for c in corners)))
    if lows:
        span = max(max(h[0] for h in highs) - min(l[0] for l in lows), max(h[1] for h in highs) - min(l[1] for l in lows))
    world = {'backdrops': backdrops, 'backdrops_casting_shadows': backdrop_shadows, 'far_large_casting_shadows': far_shadows, 'haze_volume': haze,
             'place_span_m': round(span, 2)}
    sun_info = None
    if sun is not None:
        compass, height = sun_angles(sun_direction)
        sun_info = {'name': sun.name, 'compass_degrees': round(compass, 1), 'height_degrees': round(height, 1), 'energy': round(float(sun.data.energy), 3)}
    return {'views': views, 'world': world, 'sun': sun_info}


def _has_picture_texture(obj):
    for slot in obj.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            continue
        trees = [material.node_tree] + [n.node_tree for n in material.node_tree.nodes if n.type == 'GROUP' and n.node_tree is not None]
        if any(node.type == 'TEX_IMAGE' and node.image is not None for tree in trees for node in tree.nodes):
            return True
    return False


def _text_made(obj):
    if obj.type == 'FONT':
        return True
    source = obj.get('pk_converted_from')
    original = bpy.data.objects.get(source) if source else None
    return bool(original is not None and original.type == 'FONT')


def _boxes_touch(first, second, margin):
    a, b = _bounds_corners(first), _bounds_corners(second)
    for axis in range(3):
        if max(c[axis] for c in a) + margin < min(c[axis] for c in b) or max(c[axis] for c in b) + margin < min(c[axis] for c in a):
            return False
    return True


def lettering_facts(objects, by_object):
    """{'checked': n, 'objects': [{'name', 'word', 'found_by', 'picture_texture', 'text_made', 'lettering_on_it'}]} for every lettered kind of thing."""
    scene = bpy.context.scene
    candidates = [o for o in scene.objects if o.type in ('MESH', 'FONT') and scene_read.is_visible(o)]
    lettering_things = [o for o in candidates if _text_made(o) or LETTERING_NEIGHBOUR_WORDS.search(plain_words(o.name))]
    rows = []
    for obj in objects:
        role = (by_object.get(obj.name) or {}).get('role') or ''
        if roles_module.is_never(role) or scene_read.is_scatter(obj):
            continue
        found = LETTERED_WORDS.search(plain_words(role.split('.', 1)[-1]))
        found_by = 'role'
        if not found:
            found = LETTERED_WORDS.search(plain_words(obj.name))
            found_by = 'name'
        if not found:
            continue
        near = [o.name for o in lettering_things if o is not obj and (o.parent == obj or obj.parent == o or _boxes_touch(obj, o, TOUCH_METRES))]
        rows.append({'name': obj.name, 'word': found.group(1).lower(), 'found_by': found_by, 'picture_texture': _has_picture_texture(obj),
                     'text_made': _text_made(obj), 'lettering_on_it': near[:6]})
    return {'checked': len(rows), 'objects': rows}
