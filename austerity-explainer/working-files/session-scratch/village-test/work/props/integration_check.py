import bpy, sys, json, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out_path = sys.argv[sys.argv.index('--') + 1]
dg = bpy.context.evaluated_depsgraph_get()

def tree(obj):
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    try:
        verts = [obj.matrix_world @ v.co for v in me.vertices]
        me.calc_loop_triangles()
        tris = [tuple(t.vertices) for t in me.loop_triangles]
        return BVHTree.FromPolygons([tuple(v) for v in verts], tris, epsilon=0.0), np.array([tuple(v) for v in verts])
    finally:
        ev.to_mesh_clear()

mine = [o for o in bpy.data.objects if o.type == 'MESH' and o.get('place_owner') == 'props']
others = [o for o in bpy.data.objects if o.type == 'MESH' and o.get('place_owner') in ('cottages_north', 'cottages_south', 'stable')]
print('mine', len(mine), 'others', len(others))
mt = {o.name: tree(o) for o in mine}
ot = {o.name: tree(o) for o in others}
overlaps = []
close = []
for mn, (mtree, mv) in mt.items():
    lo, hi = mv.min(axis=0), mv.max(axis=0)
    for on, (otree, ov) in ot.items():
        olo, ohi = ov.min(axis=0), ov.max(axis=0)
        if np.any(hi + 0.02 < olo) or np.any(lo - 0.02 > ohi):
            continue
        pairs = mtree.overlap(otree)
        if pairs:
            overlaps.append((mn, on, len(pairs)))
# nearest approach of each of my objects to the other owners' meshes (sampled vertices)
nearest = {}
for mn, (mtree, mv) in mt.items():
    best = None
    sample = mv[:: max(1, len(mv) // 400)]
    for on, (otree, ov) in ot.items():
        olo, ohi = ov.min(axis=0), ov.max(axis=0)
        lo, hi = mv.min(axis=0), mv.max(axis=0)
        gap = np.maximum(np.maximum(olo - hi, lo - ohi), 0.0)
        if np.linalg.norm(gap) > 2.0:
            continue
        for p in sample:
            h = otree.find_nearest(Vector(p), 2.0)
            if h[0] is not None and (best is None or h[3] < best[0]):
                best = (float(h[3]), on)
    if best:
        nearest[mn] = best
inside_stable = []
for mn, (mtree, mv) in mt.items():
    c = mv.mean(axis=0)
    if 19.0 <= c[0] <= 29.0 and 35.9 <= c[1] <= 42.1:
        inside_stable.append(mn)
doorway = []
for mn, (mtree, mv) in mt.items():
    if np.any((mv[:, 0] >= 21.4) & (mv[:, 0] <= 26.6) & (mv[:, 1] >= 34.6) & (mv[:, 1] <= 36.8)):
        doorway.append(mn)
json.dump({'overlaps_with_other_owners': overlaps, 'nearest_to_other_owners_m': nearest, 'props_inside_stable_footprint': inside_stable, 'props_with_points_in_doorway': doorway}, open(out_path, 'w'), indent=1)
print('overlaps', overlaps)
print('inside stable', inside_stable, 'doorway', doorway)
print({k: (round(v[0], 3), v[1]) for k, v in nearest.items()})
