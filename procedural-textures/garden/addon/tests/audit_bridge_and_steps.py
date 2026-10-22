# What this does: read-only check of the zigzag bridge bearings and the veranda steps in the saved courtyard.
import sys, math
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath='scratchpad/astra-work/out/courtyard_final.blend')
dg = bpy.context.evaluated_depsgraph_get()
def world_tris(obs):
    vs = []; fs = []
    for ob in obs:
        ev = ob.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles(); off = len(vs)
        vs += [ob.matrix_world @ v.co for v in me.vertices]; fs += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]; ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)
planks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Astra / varied planks')]
piers = [o for o in bpy.data.objects if o.name.startswith('Bridge pier')]
deck_bvh = world_tris(planks)
print('plank objects:', len(planks))
for ob in sorted(piers, key=lambda o: o.name):
    ev = ob.evaluated_get(dg); me = ev.to_mesh(); pts = [ob.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    top = max(p.z for p in pts); topv = [p for p in pts if p.z > top - 0.01]
    cx = sum(p.x for p in topv) / len(topv); cy = sum(p.y for p in topv) / len(topv)
    hit = deck_bvh.ray_cast(Vector((cx, cy, top - 0.02)), Vector((0, 0, 1)), 2.0)
    print(f'  {ob.name}: top z {top:.3f} at ({cx:.2f},{cy:.2f}); gap up to deck underside: {None if hit[0] is None else round(hit[0].z - top, 3)} m')
# veranda steps: what is under the lowest points
step = bpy.data.objects['Veranda step']; low_step = bpy.data.objects['Veranda step, lower']
others = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in ('Veranda step',) and not o.name.startswith(('Hills', 'Dark plain', 'Pond water', 'Raked gravel', 'Astra / Courtyard receiving ground', 'Courtyard ground source'))]
bvh_o = world_tris(others)
ev = step.evaluated_get(dg); me = ev.to_mesh(); pts = [step.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
zmin = min(p.z for p in pts); low = [p for p in pts if p.z < zmin + 0.01]
res = []
for p in low:
    h = bvh_o.ray_cast(p - Vector((0, 0, 0.001)), Vector((0, 0, -1)), 3.0)
    res.append(None if h[0] is None else round(p.z - h[0].z, 3))
print('upper step lowest z', round(zmin, 3), 'gaps to nearest other solid below (lowest points):', sorted(set(res), key=lambda x: (x is None, x))[:8])
