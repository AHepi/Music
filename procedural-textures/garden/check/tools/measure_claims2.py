# Checker script: second, denser version of the pier and cap measurements.
# Run: blender -b --disable-autoexec FILE.blend --python measure_claims2.py -- OUT.json
import bpy, sys, json, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out_path = sys.argv[sys.argv.index('--') + 1]
dg = bpy.context.evaluated_depsgraph_get()
R = {}


def world_mesh(o):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return verts, polys


def bvh_of(objs):
    verts, polys, off = [], [], 0
    for o in objs:
        v, p = world_mesh(o)
        verts += v
        polys += [tuple(i + off for i in q) for q in p]
        off += len(v)
    return BVHTree.FromPolygons(verts, polys)


# ---------- A. piers, dense grid on the top surface ----------
carriers = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and
            (o.name.startswith('Astra / varied planks') or o.name == 'Bridge stringers')]
cbvh = bvh_of(carriers)
A = {}
for i in range(4):
    p = bpy.data.objects[f'Bridge pier {i}']
    pv, pp = world_mesh(p)
    pb = BVHTree.FromPolygons(pv, pp)
    top = max(c.z for c in pv)
    xs = [c.x for c in pv]; ys = [c.y for c in pv]
    N = 40
    gaps = []
    ntop = 0
    for a in range(N):
        for b in range(N):
            x = min(xs) + (a + 0.5) / N * (max(xs) - min(xs))
            y = min(ys) + (b + 0.5) / N * (max(ys) - min(ys))
            h = pb.ray_cast(Vector((x, y, top + 1.0)), Vector((0, 0, -1)))
            if h[0] is None:
                continue
            if h[0].z < top - 0.02:   # not the top surface (side slope)
                continue
            ntop += 1
            # ray up from well inside the pier so overlap shows as a negative gap
            hc = cbvh.ray_cast(Vector((x, y, h[0].z - 0.25)), Vector((0, 0, 1)), 2.0)
            if hc[0] is not None:
                gaps.append(hc[0].z - h[0].z)
    g = sorted(gaps)
    A[p.name] = {'pier_top_z': round(top, 4), 'top_surface_points': ntop, 'points_with_carrier_above': len(g),
                 'gap_cm_min': round(g[0] * 100, 2) if g else None,
                 'gap_cm_p10': round(g[len(g) // 10] * 100, 2) if g else None,
                 'gap_cm_median': round(g[len(g) // 2] * 100, 2) if g else None,
                 'share_touching_within_5mm': round(sum(1 for q in g if q < 0.005) / max(1, ntop), 3)}
R['A_piers_dense'] = A

# ---------- C. caps: separate pieces and whether each touches the wall or another piece ----------
def components(o):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    bm = bmesh.new(); bm.from_mesh(me)
    ev.to_mesh_clear()
    bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; seen.add(v.index); cc = []
        while stack:
            u = stack.pop(); cc.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index); stack.append(w)
        comps.append([mw @ x.co for x in cc])
    bm.free()
    return comps


C = {}
for wall in ('Back wall, left', 'Back wall, right', 'Right wall behind hall'):
    w = bpy.data.objects[wall]; c = bpy.data.objects[wall + ' cap']
    wv, wp = world_mesh(w)
    wbvh = BVHTree.FromPolygons(wv, wp)
    wtop = max(p.z for p in wv)
    comps = components(c)
    rows = []
    # per component: min z, max z, nearest distance to the wall surface and to the union of other pieces' vertices
    for k, cv in enumerate(comps):
        zmin = min(p.z for p in cv); zmax = max(p.z for p in cv)
        # nearest distance of this piece to the wall
        dwall = min((wbvh.find_nearest(p)[3] for p in cv[:: max(1, len(cv) // 40)]), default=9)
        # nearest distance to other pieces (vertex to vertex, sampled)
        others = [q for j, oc in enumerate(comps) if j != k for q in oc]
        if others:
            ob = BVHTree.FromPolygons(others, [])  if False else None
        rows.append({'piece': k, 'verts': len(cv), 'z_min': round(zmin, 4), 'z_max': round(zmax, 4), 'dist_to_wall_m': round(dwall, 4)})
    # gap of the lowest piece's top to the next piece's bottom (the builder's definition: second lowest piece min z minus wall top)
    zm = sorted(r['z_min'] for r in rows)
    C[wall] = {'n_pieces': len(comps), 'wall_top_z': round(wtop, 4),
               'second_lowest_piece_zmin_minus_wall_top_cm': round((zm[1] - wtop) * 100, 2) if len(zm) > 1 else None,
               'lowest_piece_zmin_minus_wall_top_cm': round((zm[0] - wtop) * 100, 2),
               'pieces_not_touching_wall_(>2mm)': sum(1 for r in rows if r['dist_to_wall_m'] > 0.002),
               'max_dist_piece_to_wall_cm': round(max(r['dist_to_wall_m'] for r in rows) * 100, 2),
               'pieces': rows[:12]}
R['C_caps_pieces'] = C
json.dump(R, open(out_path, 'w'), indent=1)
print('MEASURE2_DONE')
