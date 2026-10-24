# What this does: for a fresh checker, names the roof and the four walls round a few pieces the "inside a building" test caught, to prove the test (read only).
import base64, collections, sys
import bpy, mathutils, numpy as np
scene = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
OWN = {'cottages_north', 'cottages_south', 'stable'}
role = lambda o: str(o.get('place_role') or '')
roof_names = {o.name for o in scene.objects if role(o).startswith('roof.')}
wall_names = {o.name for o in scene.objects if o.get('place_owner') in OWN and role(o).startswith(('wall.', 'timber.', 'stone.'))}
UP = mathutils.Vector((0, 0, 1)); SIDES = [mathutils.Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]
found = collections.Counter(); shown = 0
for obj in [o for o in scene.objects if o.get('pk_scatter') and o.get('pk_scatter_group') == 'plant']:
    roots = np.frombuffer(base64.b64decode(bpy.data.texts['pk_roots_' + obj.name].as_string().encode()), dtype=np.float32).reshape(-1, 3)
    for x, y, z in roots:
        p = mathutils.Vector((float(x), float(y), float(z) + 0.05))
        hit = scene.ray_cast(dg, p, UP, distance=15.0)
        if not hit[0] or hit[4].name not in roof_names:
            # look past scatter or other things: only roofs count
            continue
        sides = []
        for s in SIDES:
            h = scene.ray_cast(dg, p + mathutils.Vector((0, 0, 0.3)), s, distance=12.0)
            sides.append(h[4].name if h[0] else None)
        if all(n is not None and n in wall_names for n in sides):
            owners = {scene.objects[n].get('place_owner') for n in sides}
            found[(hit[4].name, tuple(sorted(owners)))] += 1
            if shown < 6:
                print('INSIDE', obj.name, tuple(round(v, 2) for v in (x, y, z)), 'roof', hit[4].name, 'walls', sides); shown += 1
print('INSIDE COUNTS', dict(found))
