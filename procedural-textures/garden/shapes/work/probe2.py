# test bmesh bisect + fill on a stone's evaluated mesh
import bpy, bmesh, math, random
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
ob = bpy.data.objects['Rock 0']
ev = ob.evaluated_get(dg); me = ev.to_mesh(); bm = bmesh.new(); bm.from_mesh(me); ev.to_mesh_clear()
print('layers', [l.name for l in bm.verts.layers.float_vector], [l.name for l in bm.faces.layers.int], bm.edges.layers.float.keys() if hasattr(bm.edges.layers.float,'keys') else '')
print('start', len(bm.verts), len(bm.faces), 'manifold', all(e.is_manifold for e in bm.edges))
rng = random.Random(1)
import time; t=time.time()
for i in range(60):
    v = rng.choice(bm.verts[:])
    n = (v.normal + Vector((rng.uniform(-.5,.5),rng.uniform(-.5,.5),rng.uniform(-.5,.5)))).normalized()
    p = v.co - n*rng.uniform(0.01,0.05)
    geom = bm.verts[:]+bm.edges[:]+bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=p, plane_no=n, clear_outer=True, clear_inner=False)
    b = [e for e in bm.edges if e.is_boundary]
    if b:
        r = bmesh.ops.contextual_create(bm, geom=b)
        # print(i, len(b), len(r['faces']), [len(f.verts) for f in r['faces']])
print('after', len(bm.verts), len(bm.faces), 'manifold', all(e.is_manifold for e in bm.edges), 'boundary', sum(e.is_boundary for e in bm.edges), time.time()-t)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
print('vol', bm.calc_volume())
print(sorted(set(len(f.verts) for f in bm.faces)))
