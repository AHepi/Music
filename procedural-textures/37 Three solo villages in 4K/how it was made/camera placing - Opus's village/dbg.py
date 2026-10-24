import bpy, sys
print("DBG start", flush=True)
sc = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
print("DBG deps ok", flush=True)
from mathutils import Vector
hit = sc.ray_cast(deps, Vector((0,0,50)), Vector((0,0,-1)), distance=100)
print("DBG raycast ok", hit[0], hit[4].name if hit[0] else None, flush=True)
