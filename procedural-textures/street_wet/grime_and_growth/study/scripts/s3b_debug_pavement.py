# debug only: which object is under x = 3.8 and what is the pavement top there
import bpy
from mathutils import Vector
deps = bpy.context.evaluated_depsgraph_get()
for x in (2.9, 3.3, 3.6, 3.8, 3.95, 4.1, 4.3):
    hit, loc, nor, idx, obj, mat = bpy.context.scene.ray_cast(deps, Vector((x, 10.0, 40.0)), Vector((0, 0, -1)))
    print('X', x, obj.name if obj else None, round(loc.z, 2) if hit else None, [round(v, 2) for v in nor])
