# What this does: measures the real heights of the parts the delivery check said float (lantern, bridge, veranda step, wall caps, roof). Reads only.
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get()
def bb(name):
    ob = bpy.data.objects[name]; ev = ob.evaluated_get(dg); me = ev.to_mesh()
    co = [ob.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    lo = [min(c[k] for c in co) for k in range(3)]; hi = [max(c[k] for c in co) for k in range(3)]
    return lo, hi
def f(v): return '(' + ', '.join(f'{x:.3f}' for x in v) + ')'
ground = bpy.data.objects['Astra / Courtyard receiving ground']
bvh = BVHTree.FromObject(ground, dg)
def gz(x, y):
    h = bvh.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1))); return h[0].z if h[0] else None
print('--- LANTERN (ground under it: %.3f)' % gz(0.95, 1.1))
for n in ('Lantern base', 'Lantern post', 'Lantern gallery', 'Lantern firebox', 'Lantern cap', 'Lantern finial', 'Lantern window glow'):
    lo, hi = bb(n); print(f'{n:22} z {lo[2]:.3f} .. {hi[2]:.3f}   xy size {hi[0]-lo[0]:.2f} x {hi[1]-lo[1]:.2f}')
print('--- BRIDGE piers / planks')
for i in range(4):
    lo, hi = bb(f'Bridge pier {i}'); ob = bpy.data.objects[f'Bridge pier {i}']
    print(f'pier {i} at ({ob.location.x:.2f},{ob.location.y:.2f}) z {lo[2]:.3f} .. {hi[2]:.3f}  xy {f(lo[:2])}..{f(hi[:2])}  ground there {gz(ob.location.x, ob.location.y)}')
for n in ('Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007'):
    lo, hi = bb(n); print(f'{n:28} z {lo[2]:.3f} .. {hi[2]:.3f}  xy {f(lo[:2])}..{f(hi[:2])}')
lo, hi = bb('Pond water'); print('Pond water z', lo[2], hi[2])
print('--- VERANDA')
for n in ('Veranda step', 'Veranda step, lower', 'Stone plinth', 'Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002'):
    lo, hi = bb(n); print(f'{n:28} z {lo[2]:.3f} .. {hi[2]:.3f}  xy {f(lo[:2])}..{f(hi[:2])}')
print('ground under step (2.2,4.25):', gz(2.2, 4.25), ' under lower (2.2,3.7):', gz(2.2, 3.7))
print('--- WALLS and CAPS')
for n in ('Back wall, left', 'Back wall, left cap', 'Back wall, right', 'Back wall, right cap', 'Right wall behind hall', 'Right wall behind hall cap'):
    lo, hi = bb(n); print(f'{n:28} z {lo[2]:.3f} .. {hi[2]:.3f}  xy {f(lo[:2])}..{f(hi[:2])}')
# cap pieces: islands z ranges
import bmesh
ob = bpy.data.objects['Back wall, left cap']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
seen = set(); k = 0
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; comp = []
    while stack:
        a = stack.pop()
        if a.index in seen: continue
        seen.add(a.index); comp.append(a)
        for e in a.link_edges: stack.append(e.other_vert(a))
    z = [c.co.z for c in comp]; k += 1
    print(f'   cap piece {k}: z {min(z):.3f} .. {max(z):.3f}')
print('--- ROOF and HALL')
roof = bpy.data.objects['Hall roof']
for n in ('Hall beams', 'Hall posts', 'Hall plaster', 'Eave soffit'):
    lo, hi = bb(n); print(f'{n:14} z {lo[2]:.3f} .. {hi[2]:.3f}  xy {f(lo[:2])}..{f(hi[:2])}')
# roof instance bounds
zs = []; ys = []
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.original == roof:
        m = inst.matrix_world
        for c in inst.object.bound_box:
            w = m @ Vector(c); zs.append(w.z); ys.append(w.y)
print('roof tiles z', f'{min(zs):.3f} .. {max(zs):.3f}', ' y', f'{min(ys):.3f} .. {max(ys):.3f}', ' (roof object origin', f(roof.location), ')')
