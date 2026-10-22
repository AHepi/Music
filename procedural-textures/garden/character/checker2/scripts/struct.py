# Fresh-eyes check of the bridge construction (written by the checker, not by the builders).
# Run: blender -b FILE --python struct.py -- OUT.json
import bpy, sys, json, math, time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = sys.argv[-1]
t0 = time.time()
R = {}

def mesh_world(ob, evaluated=False):
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        eo = ob.evaluated_get(dg)
        me = eo.to_mesh()
    else:
        me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    M = np.array(ob.matrix_world)
    V = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    T = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', T); T = T.reshape(nt, 3)
    # polygon vertex lists for loose-part detection
    polys = [tuple(p.vertices) for p in me.polygons]
    return V, T, polys

def loose_parts(V, T, polys):
    parent = list(range(len(V)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for p in polys:
        r = find(p[0])
        for v in p[1:]:
            rv = find(v)
            if rv != r:
                parent[rv] = r
    roots = np.array([find(i) for i in range(len(V))])
    _, comp = np.unique(roots, return_inverse=True)
    return comp

class Part:
    def __init__(self, obj, idx, V, T):
        self.obj = obj; self.idx = idx; self.V = V; self.T = T
        self.bmin = V.min(axis=0); self.bmax = V.max(axis=0)
        self._bvh = None; self._samp = None
    @property
    def name(self):
        return f'{self.obj}:{self.idx}'
    @property
    def bvh(self):
        if self._bvh is None:
            self._bvh = BVHTree.FromPolygons([tuple(v) for v in self.V], [tuple(t) for t in self.T], epsilon=0.0)
        return self._bvh
    def samples(self, spacing=0.015):
        if self._samp is None:
            pts = []
            P0 = self.V[self.T[:, 0]]; P1 = self.V[self.T[:, 1]]; P2 = self.V[self.T[:, 2]]
            L = np.maximum.reduce([np.linalg.norm(P1 - P0, axis=1), np.linalg.norm(P2 - P1, axis=1), np.linalg.norm(P0 - P2, axis=1)])
            k = np.maximum(1, np.ceil(L / spacing)).astype(int)
            for i in range(len(self.T)):
                kk = int(min(k[i], 40))
                a, b = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1))
                m = (a + b) <= kk
                u = (a[m] / kk); v = (b[m] / kk)
                pts.append(P0[i] + np.outer(u, P1[i] - P0[i]) + np.outer(v, P2[i] - P0[i]))
            self._samp = np.vstack(pts)
        return self._samp

def parts_of(names):
    out = []
    for nm in names:
        if nm not in bpy.data.objects:
            print('MISSING', nm); continue
        ob = bpy.data.objects[nm]
        V, T, polys = mesh_world(ob)
        comp = loose_parts(V, T, polys)
        tcomp = comp[T[:, 0]]
        for c in range(comp.max() + 1):
            vm = comp == c
            idxmap = -np.ones(len(V), dtype=np.int64); idxmap[vm] = np.arange(vm.sum())
            out.append(Part(nm, c, V[vm], idxmap[T[tcomp == c]]))
    return out

def boxes_touch(a, b, m):
    return bool(np.all(a.bmin <= b.bmax + m) and np.all(b.bmin <= a.bmax + m))

def rest_patch(A, B, tol=0.006, spacing=0.015):
    """A's surface points that lie within tol of an UP-facing face of B and are not below it: A rests on B.
    returns n_points, area_cm2, extent (xy bbox sizes of the patch), min gap mm"""
    if not boxes_touch(A, B, tol):
        return None
    S = A.samples(spacing)
    # quick box filter
    m = np.all((S >= B.bmin - tol) & (S <= B.bmax + tol), axis=1)
    S = S[m]
    if len(S) == 0:
        return None
    hits = []
    gaps = []
    for p in S:
        r = B.bvh.find_nearest(Vector(p), tol)
        if r[0] is None:
            continue
        loc, nrm = r[0], r[1]
        if nrm.z > 0.6 and p[2] >= loc.z - 0.003:
            hits.append(p); gaps.append(p[2] - loc.z)
    if not hits:
        return None
    H = np.array(hits)
    ext = H.max(axis=0) - H.min(axis=0)
    return {'n': len(H), 'area_cm2': round(len(H) * spacing * spacing * 1e4, 1), 'extent_cm': [round(float(ext[0]) * 100, 1), round(float(ext[1]) * 100, 1)], 'min_gap_mm': round(min(gaps) * 1000, 2), 'z': round(float(H[:, 2].mean()), 3), 'xy': [round(float(H[:, 0].mean()), 3), round(float(H[:, 1].mean()), 3)]}

def any_touch(A, B, tol=0.003):
    """true volume contact: triangle overlap or any sample within tol"""
    if not boxes_touch(A, B, tol):
        return None
    ov = A.bvh.overlap(B.bvh)
    S = A.samples(0.02)
    m = np.all((S >= B.bmin - tol) & (S <= B.bmax + tol), axis=1)
    nclose = 0; dmin = 9
    for p in S[m]:
        r = B.bvh.find_nearest(Vector(p), tol)
        if r[0] is not None:
            nclose += 1
            dmin = min(dmin, r[3])
    return {'overlap_tris': len(ov), 'n_close_pts': nclose}

# ------------------------------------------------------------------ parts
PLANK_OBJS = ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007']
planks = parts_of(PLANK_OBJS)
stringers = parts_of(['Bridge stringers'])
bearers = parts_of(['G6 wood / bridge bearers'])
posts = parts_of(['G6 wood / bridge posts'])
footings = parts_of(['G6 wood / bridge footings'])
piers = parts_of(['Bridge pier 0', 'Bridge pier 1', 'Bridge pier 2', 'Bridge pier 3'])
pegs = parts_of(['G6 wood / bridge pegs'])
cramps = parts_of(['G6 wood / bridge cramps'])
R['counts'] = {'planks': len(planks), 'stringers': len(stringers), 'bearers': len(bearers), 'posts': len(posts), 'footings': len(footings), 'piers': len(piers), 'pegs': len(pegs), 'cramp_parts': len(cramps),
               'planks_by_object': {o: sum(1 for p in planks if p.obj == o) for o in PLANK_OBJS}}
R['piers'] = [{'name': p.name, 'bmin': np.round(p.bmin, 3).tolist(), 'bmax': np.round(p.bmax, 3).tolist()} for p in piers]
R['footing_boxes'] = [{'name': p.name, 'bmin': np.round(p.bmin, 3).tolist(), 'bmax': np.round(p.bmax, 3).tolist()} for p in footings]
R['post_boxes'] = [{'name': p.name, 'bmin': np.round(p.bmin, 3).tolist(), 'bmax': np.round(p.bmax, 3).tolist()} for p in posts]
R['bearer_boxes'] = [{'name': p.name, 'bmin': np.round(p.bmin, 3).tolist(), 'bmax': np.round(p.bmax, 3).tolist()} for p in bearers]
R['stringer_boxes'] = [{'name': p.name, 'bmin': np.round(p.bmin, 3).tolist(), 'bmax': np.round(p.bmax, 3).tolist()} for p in stringers]

# ------------------------------------------------------------------ 1. planks on stringers
def axis_xy(V):
    c = V[:, :2].mean(axis=0)
    u, s, vt = np.linalg.svd(V[:, :2] - c, full_matrices=False)
    ax = vt[0]
    return c, ax / np.linalg.norm(ax)

rows = []
bad_planks = []
for i, pl in enumerate(planks):
    c, ax = axis_xy(pl.V)
    al = (pl.V[:, :2] - c) @ ax
    lo, hi = float(al.min()), float(al.max())
    sup = []
    for k, st in enumerate(stringers):
        r = rest_patch(pl, st, tol=0.008)
        # plank rests on stringer means the plank's bottom is on the stringer's top face. rest_patch(A=plank, B=stringer)
        if r and r['area_cm2'] >= 16.0:
            sup.append((k, r))
    pos = sorted(float((np.array(r['xy']) - c) @ ax) for k, r in sup)
    # spans: from plank end to first support, between supports, last to end
    pts = [lo] + pos + [hi]
    free = [pts[j + 1] - pts[j] for j in range(len(pts) - 1)]
    rows.append({'i': i, 'obj': pl.obj[-3:], 'len_m': round(hi - lo, 3), 'n_support': len(sup), 'supports': [k for k, r in sup], 'overhangs_cm': [round(pos[0] - lo, 3) * 100, round(hi - pos[-1], 3) * 100] if pos else None,
                 'max_span_between_m': round(max([pos[j + 1] - pos[j] for j in range(len(pos) - 1)] or [0]), 3)})
    if len(sup) < 2:
        bad_planks.append(i)
R['planks_on_stringers'] = {'n_planks': len(planks), 'n_with_less_than_2': len(bad_planks), 'bad': bad_planks, 'support_count_hist': np.bincount([r['n_support'] for r in rows]).tolist(),
                            'overhang_cm_min_max': [min(min(r['overhangs_cm']) for r in rows if r['overhangs_cm']), max(max(r['overhangs_cm']) for r in rows if r['overhangs_cm'])],
                            'max_clear_span_between_stringers_m': max(r['max_span_between_m'] for r in rows), 'rows': rows}
print('planks done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 2. stringers on bearers / piers
supports_below = bearers + piers + posts  # anything a stringer could rest on
srows = []
for k, st in enumerate(stringers):
    c, ax = axis_xy(st.V)
    al = (st.V[:, :2] - c) @ ax
    lo, hi = float(al.min()), float(al.max())
    sup = []
    for b in supports_below:
        r = rest_patch(st, b, tol=0.008, spacing=0.02)
        if r and r['area_cm2'] >= 16.0:
            sup.append((b.name, r))
    pos = sorted((float((np.array(r['xy']) - c) @ ax), nm, r['area_cm2']) for nm, r in sup)
    # support intervals in axis coordinates (from sample extents): use extent of the patch along the axis via 1-d projection of contact points: approximated by pos +- half of extent
    srows.append({'k': k, 'len_m': round(hi - lo, 3), 'start_xy': np.round(c + ax * lo, 3).tolist(), 'end_xy': np.round(c + ax * hi, 3).tolist(), 'supports': [(round(p - lo, 3), nm, a) for p, nm, a in pos],
                  'free_start_m': round(pos[0][0] - lo, 3) if pos else None, 'free_end_m': round(hi - pos[-1][0], 3) if pos else None,
                  'max_between_m': round(max([pos[j + 1][0] - pos[j][0] for j in range(len(pos) - 1)] or [0]), 3), 'z': [round(float(st.bmin[2]), 3), round(float(st.bmax[2]), 3)]})
R['stringers'] = srows
print('stringers done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 3. bearers vs posts (vertical rest and side joint)
brows = []
for b in bearers:
    entry = {'name': b.name, 'bmin': np.round(b.bmin, 3).tolist(), 'bmax': np.round(b.bmax, 3).tolist(), 'rest_on_post_top': [], 'joined_to_post': []}
    for p in posts:
        r = rest_patch(b, p, tol=0.006, spacing=0.01)
        if r:
            entry['rest_on_post_top'].append((p.name, r['area_cm2']))
        t = any_touch(b, p, 0.004)
        if t and (t['overlap_tris'] > 0 or t['n_close_pts'] > 0):
            entry['joined_to_post'].append((p.name, t['overlap_tris'], t['n_close_pts'], [round(float(p.bmin[2]), 3), round(float(p.bmax[2]), 3)]))
    # does the bearer rest on footings / piers / terrain? (no)
    brows.append(entry)
R['bearers'] = brows
print('bearers done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 4. posts on footing stones / sills
prow = []
bases = footings + piers
for p in posts:
    best = []
    for f in bases:
        r = rest_patch(p, f, tol=0.01, spacing=0.01)
        if r and r['area_cm2'] >= 16.0:
            best.append((f.name, r['area_cm2'], r['min_gap_mm']))
    prow.append({'post': p.name, 'bottom_z': round(float(p.bmin[2]), 3), 'top_z': round(float(p.bmax[2]), 3), 'xy': np.round((p.bmin[:2] + p.bmax[:2]) / 2, 3).tolist(), 'on': best})
R['posts'] = prow
print('posts done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 5. footings and sills on the terrain (bed plate and ground)
def terrain(names):
    Vs, Ts, off = [], [], 0
    for n in names:
        if n not in bpy.data.objects: continue
        V, T, _ = mesh_world(bpy.data.objects[n], evaluated=True)
        Vs.append(V); Ts.append(T + off); off += len(V)
    return BVHTree.FromPolygons([tuple(v) for v in np.vstack(Vs)], [tuple(t) for t in np.vstack(Ts)], epsilon=0.0)
tb_all = terrain(['Astra / Courtyard receiving ground', 'Life / pond bed'])
tb_bed = terrain(['Life / pond bed'])
tb_ground = terrain(['Astra / Courtyard receiving ground'])
def footprint_gap(part, grid=9):
    xs = np.linspace(part.bmin[0] + 0.01, part.bmax[0] - 0.01, grid)
    ys = np.linspace(part.bmin[1] + 0.01, part.bmax[1] - 0.01, grid)
    gaps = []; gb = []
    for x in xs:
        for y in ys:
            top = part.bvh.ray_cast(Vector((x, y, part.bmax[2] + 1.0)), Vector((0, 0, -1)), 5.0)
            if top[0] is None: continue
            bot = part.bvh.ray_cast(Vector((x, y, part.bmin[2] - 1.0)), Vector((0, 0, 1)), 5.0)
            if bot[0] is None: continue
            zb = bot[0].z
            h = tb_all.ray_cast(Vector((x, y, zb + 1.0)), Vector((0, 0, -1)), 5.0)
            if h[0] is None: continue
            gaps.append(zb - h[0].z)
            hb = tb_bed.ray_cast(Vector((x, y, zb + 1.0)), Vector((0, 0, -1)), 5.0)
            if hb[0] is not None: gb.append(zb - hb[0].z)
    g = np.array(gaps) * 1000
    return {'name': part.name, 'bottom_z': round(float(part.bmin[2]), 3), 'top_z': round(float(part.bmax[2]), 3), 'size_m': np.round(part.bmax - part.bmin, 2).tolist(), 'n': len(g),
            'gap_under_mm_min_median_max': [round(float(g.min()), 1), round(float(np.median(g)), 1), round(float(g.max()), 1)] if len(g) else None,
            'share_air_gap_over_10mm': round(float((g > 10).mean()), 2) if len(g) else None, 'share_air_gap_over_30mm': round(float((g > 30).mean()), 2) if len(g) else None,
            'share_buried_over_30mm': round(float((g < -30).mean()), 2) if len(g) else None,
            'gap_to_bedplate_only_mm_min_max': [round(min(gb) * 1000, 1), round(max(gb) * 1000, 1)] if gb else None}
R['footings'] = [footprint_gap(f) for f in footings]
R['piers_on_terrain'] = [footprint_gap(f) for f in piers]
print('footings done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 6. connectivity graph: planks -> ... -> terrain
nodes = {('plank', i): pl for i, pl in enumerate(planks)}
adj = {}
def link(a, b):
    adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
for i, pl in enumerate(planks):
    for k, st in enumerate(stringers):
        r = rest_patch(pl, st, 0.008)
        if r and r['area_cm2'] >= 16: link(('plank', i), ('stringer', k))
for k, st in enumerate(stringers):
    for j, b in enumerate(bearers):
        r = rest_patch(st, b, 0.008, 0.02)
        if r and r['area_cm2'] >= 16: link(('stringer', k), ('bearer', j))
    for j, pr in enumerate(piers):
        r = rest_patch(st, pr, 0.008, 0.02)
        if r and r['area_cm2'] >= 16: link(('stringer', k), ('pier', j))
for j, b in enumerate(bearers):
    for q, p in enumerate(posts):
        t = any_touch(b, p, 0.004)
        if t and (t['overlap_tris'] > 0 or t['n_close_pts'] > 0): link(('bearer', j), ('post', q))
for q, p in enumerate(posts):
    for f_i, f in enumerate(footings):
        r = rest_patch(p, f, 0.01, 0.01)
        if r and r['area_cm2'] >= 16: link(('post', q), ('footing', f_i))
    for j, pr in enumerate(piers):
        r = rest_patch(p, pr, 0.01, 0.01)
        if r and r['area_cm2'] >= 16: link(('post', q), ('pier', j))
# terrain: a footing/pier is grounded when its lowest points are within 20 mm of the terrain (min air gap)
grounded = set()
for f_i, f in enumerate(footings):
    fg = R['footings'][f_i]['gap_under_mm_min_median_max']
    if fg and fg[0] < 20: grounded.add(('footing', f_i))
for j, pr in enumerate(piers):
    fg = R['piers_on_terrain'][j]['gap_under_mm_min_median_max']
    if fg and fg[0] < 20: grounded.add(('pier', j))
seen = set(); stack = list(grounded)
seen |= grounded
while stack:
    n = stack.pop()
    for m in adj.get(n, ()):
        if m not in seen:
            seen.add(m); stack.append(m)
unreached = {}
for kind, items in (('plank', planks), ('stringer', stringers), ('bearer', bearers), ('post', posts), ('footing', footings), ('pier', piers)):
    miss = [i for i in range(len(items)) if (kind, i) not in seen]
    unreached[kind] = miss
R['connectivity'] = {'grounded': sorted(map(str, grounded)), 'unreached_from_ground': unreached}
print('graph done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 7. pegs and cramps: are they in/on wood?
wood = planks + stringers + bearers + posts
def nearest_wood(p, maxd=0.05):
    best = (9, None)
    for w in wood:
        if np.any(p < w.bmin - maxd) or np.any(p > w.bmax + maxd): continue
        r = w.bvh.find_nearest(Vector(p), maxd)
        if r[0] is not None and r[3] < best[0]:
            best = (r[3], w.name)
    return best
def inside(part_bvh, p):
    # even-odd ray cast along +z
    n = 0; o = Vector(p); d = Vector((0.0001, 0.0002, 1.0)).normalized()
    pos = o
    for _ in range(20):
        h = part_bvh.ray_cast(pos, d, 3.0)
        if h[0] is None: break
        n += 1; pos = h[0] + d * 1e-5
    return n % 2 == 1
peg_rows = []
for pg in pegs:
    dmin = 9; who = None; ninside = 0
    S = pg.V
    for v in S:
        d, w = nearest_wood(v, 0.02)
        if d < dmin: dmin, who = d, w
    # inside test at the lowest vertex ring centre
    low = S[S[:, 2] < S[:, 2].min() + 0.002].mean(axis=0)
    peg_rows.append({'name': pg.name, 'min_vertex_to_wood_mm': round(dmin * 1000, 2), 'wood': who, 'z': round(float(S[:, 2].min()), 3), 'height_mm': round(float((S[:, 2].max() - S[:, 2].min()) * 1000), 1)})
d = np.array([r['min_vertex_to_wood_mm'] for r in peg_rows])
R['pegs'] = {'n': len(peg_rows), 'within_1mm': int((d <= 1.0).sum()), 'between_1_and_5mm': int(((d > 1) & (d <= 5)).sum()), 'over_5mm': int((d > 5).sum()), 'over_5mm_list': [r for r in peg_rows if r['min_vertex_to_wood_mm'] > 5][:15],
             'on_what': {k: sum(1 for r in peg_rows if r['wood'] and r['wood'].startswith(k)) for k in ('Astra', 'G6 wood / bridge bearers', 'G6 wood / bridge posts', 'Bridge stringers')}}
crow = []
for cp in cramps:
    dmin = 9; who = None
    for v in cp.V:
        dd, w = nearest_wood(v, 0.06)
        if dd < dmin: dmin, who = dd, w
    # fraction of vertices more than 5mm from any wood surface (an inside vertex is distance>0 but within the wood: count only if not inside)
    far = 0
    for v in cp.V:
        dd, w = nearest_wood(v, 0.06)
        if dd > 0.005:
            # check inside the plank volume
            ins = False
            for pl in planks:
                if np.all(v >= pl.bmin) and np.all(v <= pl.bmax) and inside(pl.bvh, v):
                    ins = True; break
            if not ins: far += 1
    crow.append({'name': cp.name, 'nv': len(cp.V), 'min_to_wood_mm': round(dmin * 1000, 2), 'verts_far_from_wood_and_outside': far, 'z': [round(float(cp.bmin[2]), 3), round(float(cp.bmax[2]), 3)], 'size_cm': np.round((cp.bmax - cp.bmin) * 100, 1).tolist()})
R['cramps'] = crow
print('pegs/cramps done', round(time.time() - t0, 1))

# ------------------------------------------------------------------ 8. walkability and runs overlapping
allp = Part('planks_all', 0, np.vstack([p.V for p in planks]), np.vstack([p.T + sum(len(q.V) for q in planks[:i]) for i, p in enumerate(planks)]))
nodes_xy = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]
pts = []
for a, b in zip(nodes_xy[:-1], nodes_xy[1:]):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / 0.05)
    for i in range(n):
        s = i / n; pts.append((a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s))
pts.append(nodes_xy[-1])
zs = []
for p in pts:
    h = allp.bvh.ray_cast(Vector((p[0], p[1], 1.5)), Vector((0, 0, -1)), 3.0)
    zs.append(None if h[0] is None else float(h[0].z))
hit = [i for i, z in enumerate(zs) if z is not None]
runs = []; cur = 0
for z in zs[hit[0]:hit[-1] + 1]:
    if z is None: cur += 1
    else:
        if cur: runs.append(cur)
        cur = 0
vz = np.array([z for z in zs if z is not None])
# ray hit gaps are real inter-plank gaps; also check lateral: hit points at +-0.4 m across the centre line
across = []
for a, b in zip(nodes_xy[:-1], nodes_xy[1:]):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = -uy, ux
    for s in np.linspace(0.3, L - 0.3, 14):
        cx, cy = a[0] + ux * s, a[1] + uy * s
        row = []
        for off in np.arange(-0.8, 0.801, 0.02):
            h = allp.bvh.ray_cast(Vector((cx + nx * off, cy + ny * off, 1.5)), Vector((0, 0, -1)), 3.0)
            row.append(h[0] is not None)
        row = np.array(row)
        if row.any():
            idx = np.where(row)[0]
            across.append(round(float((idx.max() - idx.min()) * 0.02), 2))
R['walk'] = {'n_points': len(pts), 'n_hit': len(vz), 'first_hit_idx': hit[0], 'last_hit_idx': hit[-1], 'miss_runs_in_samples_of_5cm': runs, 'longest_miss_run_cm': 5 * max(runs or [0]),
             'plank_top_z_min_max': [round(float(vz.min()), 4), round(float(vz.max()), 4)], 'max_step_between_samples_mm': round(max(abs(zs[i + 1] - zs[i]) for i in range(len(zs) - 1) if zs[i] is not None and zs[i + 1] is not None) * 1000, 1),
             'deck_width_m_min_mean_max': [min(across), round(float(np.mean(across)), 3), max(across)]}
# different-run plank interpenetration
ov = []
for i in range(len(planks)):
    for j in range(i + 1, len(planks)):
        if planks[i].obj == planks[j].obj: continue
        if not boxes_touch(planks[i], planks[j], 0.01): continue
        n = len(planks[i].bvh.overlap(planks[j].bvh))
        ov.append((i, j, planks[i].obj[-3:], planks[j].obj[-3:], n))
R['planks_of_different_runs_that_touch_or_overlap_boxes'] = {'n_pairs_with_box_touch': len(ov), 'n_with_triangle_overlap': sum(1 for o in ov if o[4] > 0), 'pairs_with_overlap': [o for o in ov if o[4] > 0][:20]}
# planks vs posts crossing
pp = []
for q, p in enumerate(posts):
    for i, pl in enumerate(planks):
        if boxes_touch(p, pl, 0.0):
            n = len(p.bvh.overlap(pl.bvh))
            if n: pp.append((q, i, pl.obj[-3:], n))
R['posts_cutting_through_planks'] = pp
R['seconds'] = round(time.time() - t0, 1)
json.dump(R, open(OUT, 'w'), indent=1, default=float)
print('STRUCT DONE', R['seconds'])
