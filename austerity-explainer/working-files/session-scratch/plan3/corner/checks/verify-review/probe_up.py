# What this does: lists every surface met going straight up and straight down through a few spots (read-only probe)
import bpy
from mathutils import Vector
scene = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
def walk(start, direction, limit):
    origin, out = Vector(start), []
    for _ in range(20):
        hit, loc, normal, idx, obj, m = scene.ray_cast(dg, origin, Vector(direction), distance=limit)
        if not hit:
            break
        out.append((round(loc.z, 3), obj.name, round(normal.z, 2)))
        origin = loc + Vector(direction) * 0.001
    return out
for name, x, y, z in (('drum centre', 2.76, 22.0, 1.369), ('pail centre', 3.281, 21.15, 1.519), ('dustbins centre', -3.6, 27.2, 1.9)):
    print('PROBE', name, 'up:', walk((x, y, z), (0, 0, 1), 0.6))
    print('PROBE', name, 'down from +1 m:', walk((x, y, z + 1.0), (0, 0, -1), 2.0))
