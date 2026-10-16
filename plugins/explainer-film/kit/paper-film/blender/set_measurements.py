# What this does: measures three things in a built Blender set that the planners need and that a place facts file's
# boxes are too rough for (it changes nothing in the scene and never saves):
#   footprints  each named group's base: the width and depth (x, y) of the part within a few centimetres of its lowest
#               point, its middle and its bottom height. The effects planner sizes contact shadows from it
#               (calculators/plan_effects.py contact-shadows --footprints FILE): a chair's legs, not its back.
#   objects     where named things are (each object matching a pattern: a mesh's box, a light's place and watts), for
#               example the street builder's lamps (--match "gas_lamp_*"), which the light planner projects onto the frame
#   beam        every surface a light's cone meets, out to a distance: for rays spread over the cone, all the hits along
#               each ray (distance, object, group), in order. The light planner reads it (calculators/plan_lights.py
#               --beam-hits FILE) to set the light's reach short of the first surface it should not light; a light with
#               no shadow lights everything along a ray, not only the first thing it meets (log 31: the notice glow went
#               through the board onto the wall until its reach was cut to 1.4 m).
# Groups are named as in a shot check file ("groups": {"drum": ["brazier-drum*", ...]}): an object belongs to the
# group whose pattern matches its own name or the name of what it hangs from (the same rule as shot_facts.py).
# Use (Blender in the background; the .blend is only read):
#   blender -b SET.blend --python set_measurements.py -- footprints --check shot-check.json --groups drum,chair,pail
#         [--slice 0.05] --out footprints.json
#   blender -b SET.blend --python set_measurements.py -- beam --check shot-check.json --at x,y,z --aim x,y,z
#         --cone 50 [--rings 6 --per-ring 24] [--far 6] --out beam.json [--name "notice glow"]
#   blender -b SET.blend --python set_measurements.py -- objects --match "gas_lamp_*" --out lamps.json
#   (or --light NAME instead of --at/--aim/--cone, to read a spot light of the scene; --scene-script FILE runs a
#   script that builds the set first, for sets that are assembled each time.)
# Coordinates are Blender metres. The output JSON says what it measured and from which file.

import fnmatch
import json
import math
import os
import sys

import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not arguments or arguments[0] in ('-h', '--help'):
    try:
        print(open(os.path.abspath(__file__)).read().split('\nimport')[0])
    except (NameError, OSError):
        print('set_measurements.py: footprints, objects or beam; see the note at the top of the file')
    sys.exit(0)
command = arguments[0]


def option(name, default=None):
    return arguments[arguments.index(name) + 1] if name in arguments else default


def vector(text):
    return Vector([float(v) for v in text.split(',')])


check = json.load(open(option('--check'))) if option('--check') else {'groups': {}}
groups = check.get('groups', {})
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()


def ancestors(o):
    while o.parent:
        o = o.parent
        yield o


def group_of(o):
    for name in [o.name] + [a.name for a in ancestors(o)]:
        for group, patterns in groups.items():
            if any(fnmatch.fnmatch(name, p) for p in patterns):
                return group
    return None


meshes = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render]


def footprints():
    wanted = [g.strip() for g in option('--groups', ','.join(groups)).split(',') if g.strip()]
    slice_height = float(option('--slice', '0.05'))
    found = {}
    for group in wanted:
        points = []
        for o in meshes:
            if group_of(o) != group:
                continue
            evaluated = o.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            matrix = o.matrix_world
            points += [matrix @ v.co for v in mesh.vertices]
            evaluated.to_mesh_clear()
        if not points:
            found[group] = {'missing': True}
            continue
        bottom = min(p.z for p in points)
        base = [p for p in points if p.z <= bottom + slice_height]
        xs, ys = [p.x for p in base], [p.y for p in base]
        found[group] = {'width': round(max(xs) - min(xs), 4), 'depth': round(max(ys) - min(ys), 4),
                        'centre': [round((max(xs) + min(xs)) / 2, 4), round((max(ys) + min(ys)) / 2, 4)], 'bottom': round(bottom, 4),
                        'vertices_in_base': len(base), 'how': f'vertices within {slice_height} m of the lowest point (set_measurements.py)'}
    return {'about': 'Base footprints of groups, measured in Blender (set_measurements.py footprints).', 'blend': bpy.data.filepath,
            'slice_metres': slice_height, 'footprints': found}


def cone_directions(axis, cone_degrees, rings, per_ring):
    """The axis plus rings of directions out to the cone's edge."""
    axis = axis.normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    side = axis.cross(helper).normalized()
    up = side.cross(axis).normalized()
    half = math.radians(cone_degrees / 2)
    directions = [(0.0, axis)]
    for ring in range(1, rings + 1):
        angle = half * ring / rings
        for k in range(per_ring):
            turn = 2 * math.pi * k / per_ring
            d = axis * math.cos(angle) + (side * math.cos(turn) + up * math.sin(turn)) * math.sin(angle)
            directions.append((math.degrees(angle), d.normalized()))
    return directions


def all_hits(origin, direction, far):
    """Every surface along a ray out to `far`, nearest first (stepping just past each hit)."""
    hits, start, travelled = [], origin.copy(), 0.0
    for _ in range(64):
        hit, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, start, direction, distance=far - travelled)
        if not hit:
            break
        distance = (location - origin).length
        hits.append({'distance': round(distance, 4), 'object': obj.name, 'group': group_of(obj),
                     'facing_light': normal.dot(direction) < 0})
        travelled = distance + 0.001
        start = origin + direction * travelled
        if travelled >= far:
            break
    return hits


def beam():
    if option('--light'):
        light = scene.objects[option('--light')]
        at = light.matrix_world.translation.copy()
        axis = light.matrix_world.to_3x3() @ Vector((0, 0, -1))
        cone = math.degrees(light.data.spot_size) if light.data.type == 'SPOT' else 179.0
        reach = light.data.cutoff_distance if getattr(light.data, 'use_custom_distance', False) else None
        name = light.name
    else:
        at, axis, cone, reach, name = vector(option('--at')), vector(option('--aim')) - vector(option('--at')), float(option('--cone')), None, option('--name', 'light')
    rings, per_ring, far = int(option('--rings', '6')), int(option('--per-ring', '24')), float(option('--far', '6'))
    rays = []
    for angle, direction in cone_directions(axis, cone, rings, per_ring):
        rays.append({'off_axis_degrees': round(angle, 3), 'direction': [round(v, 5) for v in direction], 'hits': all_hits(at, direction, far)})
    return {'about': 'Every surface a light\'s cone meets, ray by ray (set_measurements.py beam).', 'blend': bpy.data.filepath, 'light': name,
            'at': [round(v, 4) for v in at], 'axis': [round(v, 5) for v in axis.normalized()], 'cone_degrees': cone,
            'custom_distance': reach, 'far_metres': far, 'rays': rays}


def objects():
    pattern = option('--match', '*')
    found = {}
    for o in scene.objects:
        if not fnmatch.fnmatch(o.name, pattern):
            continue
        if o.type == 'MESH':
            corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
            found[o.name] = {'type': 'MESH', 'group': group_of(o), 'box_low': [round(min(p[i] for p in corners), 4) for i in range(3)],
                             'box_high': [round(max(p[i] for p in corners), 4) for i in range(3)]}
        elif o.type == 'LIGHT':
            found[o.name] = {'type': 'LIGHT', 'light_type': o.data.type, 'at': [round(v, 4) for v in o.matrix_world.translation],
                             'watts': o.data.energy}
        else:
            found[o.name] = {'type': o.type, 'at': [round(v, 4) for v in o.matrix_world.translation]}
    return {'about': f'Objects matching "{pattern}" (set_measurements.py objects).', 'blend': bpy.data.filepath, 'objects': found}


if option('--scene-script'):
    exec(compile(open(option('--scene-script')).read(), option('--scene-script'), 'exec'), {'__name__': '__main__'})
    depsgraph = bpy.context.evaluated_depsgraph_get()
    meshes = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render]
result = {'footprints': footprints, 'beam': beam, 'objects': objects}[command]()
out = option('--out')
with open(out, 'w') as handle:
    json.dump(result, handle, indent=1)
print(f'set_measurements {command}: wrote {out}')
