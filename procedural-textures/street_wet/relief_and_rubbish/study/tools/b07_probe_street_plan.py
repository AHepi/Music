# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Reads the street's PLAN (where things stand, seen from above) out of a street file, so that the rubbish mask can be drawn from it: where the house walls stand,
# where every front door is, where the rain pipes and lamp posts stand, where the ground meets the kerb, and in the lockout shot file where the props stand (the drum
# with the fire, the handcart, the sacks, the coal heap, the pail, the dustbin, the ladder, the notice board). It changes and saves nothing; it writes a JSON file.
# Run: blender -b --disable-autoexec -t 2 BLEND --python b07_probe_street_plan.py -- OUT_JSON
import json
import sys

import bpy
from mathutils import Vector

out = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
plan = {'file': bpy.data.filepath}
# 1. the wall line: shoot rays from the pavement toward each side and see where they first hit a wall object
walls = {}
for side, direction in (('right', Vector((1, 0, 0))), ('left', Vector((-1, 0, 0)))):
    hits = []
    for y in (3.5, 8.0, 13.0, 18.0, 24.0, 30.0, 40.0):
        origin = Vector((direction.x * 3.0, y, direction.x * 0 + 0.3 + y * 0.0708 + 0.35))
        ok, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, origin, direction, distance=3.0)
        hits.append(dict(y=y, hit=ok, x=round(location.x, 3) if ok else None, obj=obj.name if ok else None))
    walls[side] = hits
plan['wall_rays'] = walls
# 2. doors, lamp posts, rain pipes
doors, lamps, pipes = [], [], []
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    p = obj.matrix_world.translation
    if obj.name.endswith('_door') and (obj.name.startswith('right_row') or obj.name.startswith('left_row')):
        doors.append(dict(name=obj.name, x=round(p.x, 3), y=round(p.y, 3), z=round(p.z, 3)))
    elif obj.name.startswith('gas_lamp') and obj.name.endswith('_iron'):
        lamps.append(dict(name=obj.name, x=round(p.x, 3), y=round(p.y, 3), z=round(p.z, 3)))
    elif obj.name.endswith('_rainwater') and (obj.name.startswith('right_row') or obj.name.startswith('left_row')):
        low = []
        eval_obj = obj.evaluated_get(depsgraph)
        for v in eval_obj.data.vertices:
            w = obj.matrix_world @ v.co
            if w.z - p.z < 0.9 and abs(w.x) > 3.2:
                low.append((w.x, w.y))
        if low:
            xs = sorted(set(round(a, 2) for a, b in low))
            pipes.append(dict(name=obj.name, origin_y=round(p.y, 3), x_min=round(min(a for a, b in low), 3), x_max=round(max(a for a, b in low), 3),
                              y_values=sorted(set(round(b, 2) for a, b in low))[:12]))
plan['doors'], plan['lamps'], plan['rainwater_low_vertices'] = doors, lamps, pipes[:6]
plan['rainwater_count'] = len(pipes)
# 3. ground pieces: extents
extents = {}
for name in ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements', 'ground'):
    obj = bpy.data.objects.get(name)
    if obj:
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        extents[name] = dict(x=[round(min(xs), 2), round(max(xs), 2)], y=[round(min(ys), 2), round(max(ys), 2)])
plan['extents'] = extents
# 4. the road surface height along the middle, the gutter and the pavement (to know the slope and crown): z at a few x for y = 10
heights = {}
for x in (0.0, 1.0, 2.0, 2.3, 2.6, 3.0, 4.0, 4.3):
    ok, loc, n, i, o, m = scene.ray_cast(depsgraph, Vector((x, 10.0, 6.0)), Vector((0, 0, -1)), distance=20.0)
    heights[str(x)] = dict(z=round(loc.z, 3) if ok else None, obj=o.name if ok else None)
plan['heights_at_y10'] = heights
# 5. props (lockout file only)
props = {}
for obj in scene.objects:
    if obj.type == 'MESH' and obj.name in ('cart-body', 'wheel_left', 'sack0', 'sack1', 'slack-heap', 'coal-heap', 'tub-body', 'barrel_stove', 'metal_trash_can', 'metal_trash_can_rust', 'wooden_bucket_01',
                                           'wooden_bucket_02', 'wooden_ladder_steps', 'notice-board', 'notice', 'Lantern_01', 'wine_barrel_01', 'large_iron_gate', 'rusted_spade_01', 'track', 'name-board'):
        eval_obj = obj.evaluated_get(depsgraph)
        corners = [obj.matrix_world @ Vector(c) for c in eval_obj.bound_box]
        props[obj.name] = dict(x=[round(min(c.x for c in corners), 2), round(max(c.x for c in corners), 2)], y=[round(min(c.y for c in corners), 2), round(max(c.y for c in corners), 2)],
                               z=[round(min(c.z for c in corners), 2), round(max(c.z for c in corners), 2)])
    if obj.type == 'LIGHT' and obj.name == 'brazier_light':
        props['brazier_light'] = dict(x=round(obj.matrix_world.translation.x, 2), y=round(obj.matrix_world.translation.y, 2), z=round(obj.matrix_world.translation.z, 2))
plan['props'] = props
json.dump(plan, open(out, 'w'), indent=1)
print('WROTE', out, 'doors', len(doors), 'lamps', len(lamps), 'props', list(props))
