import bpy, json, sys, math, time
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import *
from mathutils import Vector
t0 = time.time()
R = {}
PL = ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007']
planks = Parts(PL)
stringers = Parts(['Bridge stringers'])
bearers = Parts(['G6 wood / bridge bearers'])
posts = Parts(['G6 wood / bridge posts'])
footings = Parts(['G6 wood / bridge footings', 'Bridge pier 1', 'Bridge pier 2'])
sills = Parts(['Bridge pier 0', 'Bridge pier 3'])
pegs = Parts(['G6 wood / bridge pegs'])
cramps = Parts(['G6 wood / bridge cramps'])
R['counts'] = {'planks': len(planks.items), 'stringers': len(stringers.items), 'bearers': len(bearers.items), 'posts': len(posts.items), 'footings_incl_piers12': len(footings.items), 'sills': len(sills.items), 'pegs': len(pegs.items), 'cramps': len(cramps.items)}

def under_z(P, k, x, y):
    b = P.bvh(k)
    hit = b.ray_cast(Vector((x, y, P.items[k]['bmin'][2] - 0.05)), Vector((0, 0, 1)), 1.0)
    return None if hit[0] is None else hit[0].z

def rest_on(upper, lower, spacing=0.015, tol=0.008, up_label=''):
    out = {}
    lb, lab = lower.all_bvh()
    # lower items ids -> readable
    for it in upper.items:
        k = it['id']
        xs = np.arange(it['bmin'][0] + spacing / 2, it['bmax'][0], spacing)
        ys = np.arange(it['bmin'][1] + spacing / 2, it['bmax'][1], spacing)
        cnt = {}
        mgap = {}
        nsamp = 0
        for x in xs:
            for y in ys:
                zu = under_z(upper, k, x, y)
                if zu is None:
                    continue
                nsamp += 1
                h = lb.ray_cast(Vector((x, y, zu + 0.03)), Vector((0, 0, -1)), 2.0)
                if h[0] is None:
                    continue
                lid = int(lab[h[2]])
                gap = zu - h[0].z
                if gap < -0.03:
                    continue
                if lid not in mgap or gap < mgap[lid]:
                    mgap[lid] = gap
                if gap <= tol:
                    cnt[lid] = cnt.get(lid, 0) + 1
        out[k] = {'n_under': nsamp, 'contacts': {str(l): {'n': c, 'area_cm2': round(c * spacing * spacing * 1e4, 1), 'min_gap_mm': round(mgap[l] * 1000, 1)} for l, c in cnt.items()},
                  'near': {str(l): round(g * 1000, 1) for l, g in mgap.items() if l not in cnt}}
    return out

def summarize(res, upper, lower, min_area=4.0, need=2, name=''):
    # contact counts with area >= min_area cm2
    bad = []
    nlow = []
    gaps = []
    pen = []
    for k, d in res.items():
        good = [l for l, c in d['contacts'].items() if c['area_cm2'] >= min_area]
        nlow.append(len(good))
        for l in good:
            gaps.append(d['contacts'][l]['min_gap_mm'])
        if len(good) < need:
            bad.append({'upper': k, 'upper_obj': upper.items[k]['obj'], 'upper_idx': upper.items[k]['idx'], 'contacts': d['contacts'], 'near': d['near']})
    return {'name': name, 'n_upper': len(res), 'min_supports': int(min(nlow)) if nlow else None, 'max_supports': int(max(nlow)) if nlow else None, 'n_bad': len(bad), 'bad': bad[:12],
            'contact_min_gap_mm_range': [min(gaps), max(gaps)] if gaps else None}

t = time.time()
r = rest_on(planks, stringers)
R['planks_on_stringers'] = summarize(r, planks, stringers, min_area=8.0, need=2, name='planks on stringers (>=2, area>=8cm2)')
# also allow bearers/sills as extra support for planks
r_b = rest_on(planks, bearers)
R['planks_on_bearers_extra'] = {str(k): {l: c['area_cm2'] for l, c in d['contacts'].items()} for k, d in r_b.items() if d['contacts']}
# plank spans: for each plank, positions of stringers touching it (centre line coordinates) not needed
print('planks done', time.time() - t)
t = time.time()
# stringers rest on bearers or sills
bs = Parts(['G6 wood / bridge bearers', 'Bridge pier 0', 'Bridge pier 3'])
r = rest_on(stringers, bs, spacing=0.02, tol=0.008)
R['stringers_on_bearers_or_sills'] = summarize(r, stringers, bs, min_area=8.0, need=2, name='stringers on bearers or bank sills (>=2)')
R['stringers_on_bearers_or_sills']['detail'] = {str(k): {'obj': bs.items[int(l)]['obj'] + ':' + str(bs.items[int(l)]['idx']) for l in d['contacts']} for k, d in r.items()}
R['stringers_on_bearers_or_sills']['detail'] = {str(k): [bs.items[int(l)]['obj'].replace('G6 wood / bridge ', '') + ':' + str(bs.items[int(l)]['idx']) + ' a=' + str(c['area_cm2']) + ' g=' + str(c['min_gap_mm']) for l, c in d['contacts'].items()] for k, d in r.items()}
print('stringers done', time.time() - t)
# bearers rest on posts (2 posts)
r = rest_on(bearers, posts, spacing=0.01, tol=0.008)
# posts hold bearers from the side (ends overlap post): the bearer bottom may be above the post top? record, and test also side contact by bbox overlap
R['bearers_on_posts_vertical'] = summarize(r, bearers, posts, min_area=1.0, need=2, name='bearers vertically resting on posts (>=2)')
# bearer-to-post by overlap of 3D boxes (bearer end embedded in/against post)
def box_overlap(a, b, m=0.005):
    return bool(np.all(a['bmin'] <= b['bmax'] + m) and np.all(b['bmin'] <= a['bmax'] + m))
bo = {}
for b in bearers.items:
    # bearer body is a long box; find posts whose xy hull is within 3cm of any bearer end: use verts distance
    Vb = b['V']
    lst = []
    for p in posts.items:
        # min distance between bearer verts' xy-lines: use point-in-expanded-bbox test with z overlap
        zov = min(b['bmax'][2], p['bmax'][2]) - max(b['bmin'][2], p['bmin'][2])
        if zov < 0.02:
            continue
        # distance from post centre to bearer centre line segment in xy
        pc = (p['bmin'][:2] + p['bmax'][:2]) / 2
        # bearer long axis from PCA
        c = Vb[:, :2].mean(axis=0)
        u, s, vt = np.linalg.svd(Vb[:, :2] - c, full_matrices=False)
        ax = vt[0]; nrm = np.array([-ax[1], ax[0]])
        along = (Vb[:, :2] - c) @ ax
        lo, hi = along.min(), along.max()
        across_half = ((Vb[:, :2] - c) @ nrm)
        ah = max(abs(across_half.min()), abs(across_half.max()))
        pa = (pc - c) @ ax; pn = (pc - c) @ nrm
        # post half size 0.07
        d_along = max(0, abs(pa - (lo + hi) / 2) - (hi - lo) / 2)
        d_across = max(0, abs(pn) - ah)
        if d_along - 0.07 <= 0.02 and d_across - 0.07 <= 0.02:
            lst.append((p['id'], round(float(d_along), 3), round(float(d_across), 3)))
    bo[b['id']] = lst
R['bearers_touch_posts_box'] = {str(k): v for k, v in bo.items()}
# posts on footings (vertical)
r = rest_on(posts, footings, spacing=0.01, tol=0.01)
rs = summarize(r, posts, footings, min_area=4.0, need=1, name='posts standing on a footing stone (>=1, tol 10mm)')
sill_r = rest_on(posts, sills, spacing=0.01, tol=0.01)
miss = []
for k, d in r.items():
    good = [l for l, c in d['contacts'].items() if c['area_cm2'] >= 4.0]
    sg = [l for l, c in sill_r[k]['contacts'].items() if c['area_cm2'] >= 4.0]
    if not good and not sg:
        miss.append({'post': k, 'near_footing': d['near'], 'near_sill': sill_r[k]['near']})
rs['posts_without_footing_or_sill'] = miss
rs['post_to_support'] = {str(k): [footings.items[int(l)]['obj'].replace('G6 wood / bridge ', '') + ':' + str(footings.items[int(l)]['idx']) + ' g=' + str(c['min_gap_mm']) for l, c in d['contacts'].items()] + ['SILL:' + sills.items[int(l)]['obj'] + ' g=' + str(c['min_gap_mm']) for l, c in sill_r[k]['contacts'].items()] for k, d in r.items()}
R['posts_on_footings'] = rs
print('posts done')
# footings stand on the bed/ground
dg = bpy.context.evaluated_depsgraph_get()
def terrain_bvh(names):
    Vs, Ts, off = [], [], 0
    for n in names:
        V, T, P = world_mesh(bpy.data.objects[n], evaluated=True)
        Vs.append(V); Ts.append(T + off); off += len(V)
    return BVHTree.FromPolygons([tuple(v) for v in np.vstack(Vs)], [tuple(t) for t in np.vstack(Ts)], epsilon=0.0)
terr_names = [n for n in ['Astra / Courtyard receiving ground', 'Life / pond bed'] if n in bpy.data.objects]
R['terrain_objects'] = terr_names
tb = terrain_bvh(terr_names)
ground_only = terrain_bvh(['Astra / Courtyard receiving ground'])
bedonly = terrain_bvh(['Life / pond bed'])
def footing_gap(P):
    res = []
    for it in P.items:
        xs = np.linspace(it['bmin'][0] + 0.03, it['bmax'][0] - 0.03, 7)
        ys = np.linspace(it['bmin'][1] + 0.03, it['bmax'][1] - 0.03, 7)
        zb = it['bmin'][2]
        gs = []; gb = []; gg = []
        for x in xs:
            for y in ys:
                # footing bottom at this xy ~ zb (flat bottom) ; ground height from above
                h = tb.ray_cast(Vector((x, y, zb + 0.3)), Vector((0, 0, -1)), 2.0)
                hg = ground_only.ray_cast(Vector((x, y, zb + 0.3)), Vector((0, 0, -1)), 2.0)
                hb = bedonly.ray_cast(Vector((x, y, zb + 0.3)), Vector((0, 0, -1)), 2.0)
                if h[0] is not None: gs.append(zb - h[0].z)
                if hg[0] is not None: gg.append(zb - hg[0].z)
                if hb[0] is not None: gb.append(zb - hb[0].z)
        res.append({'obj': it['obj'], 'idx': it['idx'], 'bottom_z': round(float(zb), 4), 'top_z': round(float(it['bmax'][2]), 4),
                    'gap_to_top_surface_mm_min_max': [round(min(gs) * 1000, 1), round(max(gs) * 1000, 1)] if gs else None,
                    'gap_to_ground_mm': [round(min(gg) * 1000, 1), round(max(gg) * 1000, 1)] if gg else None,
                    'gap_to_bedplate_mm': [round(min(gb) * 1000, 1), round(max(gb) * 1000, 1)] if gb else None})
    return res
R['footings_on_bed'] = footing_gap(footings)
R['sills_on_ground'] = footing_gap(sills)
# pegs touching planks
pb, plab = planks.all_bvh()
pgaps = []
unseated = 0
for it in pegs.items:
    c = (it['bmin'] + it['bmax']) / 2
    h = pb.ray_cast(Vector((c[0], c[1], it['bmax'][2] + 0.05)), Vector((0, 0, -1)), 1.0)
    if h[0] is None:
        # peg not above any plank
        pgaps.append(None); unseated += 1; continue
    pgaps.append(float(it['bmin'][2] - h[0].z))
v = [g for g in pgaps if g is not None]
R['pegs'] = {'n': len(pegs.items), 'not_over_a_plank': unseated, 'gap_mm_min': round(min(v) * 1000, 2), 'gap_mm_max': round(max(v) * 1000, 2), 'n_floating_over_1mm': int(sum(1 for g in v if g > 0.001)), 'n_over_5mm': int(sum(1 for g in v if g > 0.005)), 'gap_hist_mm': np.histogram(np.array(v) * 1000, bins=[-100, -5, -1, 0.0, 1, 2, 5, 100])[0].tolist()}
# walkability: centre line
nodes = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]
pts = []
for a, b in zip(nodes[:-1], nodes[1:]):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / 0.05)
    for i in range(n):
        s = i / n
        pts.append((a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s))
pts.append(nodes[-1])
# extend 0.4 m past the ends
def ext(p, q, d):
    L = math.hypot(q[0] - p[0], q[1] - p[1]); return (q[0] + (q[0] - p[0]) / L * d, q[1] + (q[1] - p[1]) / L * d)
zs = []
for p in pts:
    h = pb.ray_cast(Vector((p[0], p[1], 1.0)), Vector((0, 0, -1)), 2.0)
    zs.append(None if h[0] is None else float(h[0].z))
seg = [i for i, z in enumerate(zs) if z is not None]
miss_runs = []; cur = 0
for z in zs[seg[0]:seg[-1] + 1]:
    if z is None: cur += 1
    else:
        if cur: miss_runs.append(cur)
        cur = 0
vz = np.array([z for z in zs if z is not None])
steps = [abs(zs[i + 1] - zs[i]) for i in range(len(zs) - 1) if zs[i] is not None and zs[i + 1] is not None]
R['walk'] = {'n_points': len(pts), 'n_hit': int(len(vz)), 'first_hit_index': seg[0], 'last_hit_index': seg[-1], 'route_length_m': round(len(pts) * 0.05, 2),
             'top_z_min_max': [round(float(vz.min()), 4), round(float(vz.max()), 4)], 'max_step_between_5cm_samples_mm': round(max(steps) * 1000, 1), 'miss_run_lengths_samples': miss_runs,
             'first_hit_xy': pts[seg[0]], 'last_hit_xy': pts[seg[-1]]}
# step from bank to deck at the two ends
for nm, p, q in (('west_end', nodes[0], nodes[1]), ('east_end', nodes[-1], nodes[-2])):
    L = math.hypot(q[0] - p[0], q[1] - p[1]); ux, uy = (p[0] - q[0]) / L, (p[1] - q[1]) / L
    row = []
    for d in (-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        x, y = p[0] + ux * d, p[1] + uy * d
        hg = ground_only.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)), 5.0)
        hp = pb.ray_cast(Vector((x, y, 2.0)), Vector((0, 0, -1)), 5.0)
        row.append({'beyond_node_m': d, 'ground_z': None if hg[0] is None else round(hg[0].z, 3), 'plank_top_z': None if hp[0] is None else round(hp[0].z, 3)})
    R['bank_' + nm] = row
# plank character from mesh
cs = []
for it in planks.items:
    V = it['V']; c = V[:, :2].mean(axis=0)
    u, s, vt = np.linalg.svd(V[:, :2] - c, full_matrices=False)
    ax = vt[0]; nrm = np.array([-ax[1], ax[0]])
    al = (V[:, :2] - c) @ ax; ac = (V[:, :2] - c) @ nrm
    cs.append({'id': it['id'], 'obj': it['obj'], 'len': float(al.max() - al.min()), 'width': float(ac.max() - ac.min()), 'thick': float(V[:, 2].max() - V[:, 2].min()), 'c': c.tolist(), 'ax': ax.tolist(), 'nv': len(V), 'vol_hash': round(float(V.sum()), 4)})
W = np.array([x['width'] for x in cs]); Tk = np.array([x['thick'] for x in cs]); Ln = np.array([x['len'] for x in cs])
R['plank_character'] = {'n': len(cs), 'width_cm_min_max_std': [round(W.min() * 100, 2), round(W.max() * 100, 2), round(W.std() * 100, 2)], 'z_extent_mm_min_max_std(includes bow)': [round(Tk.min() * 1000, 1), round(Tk.max() * 1000, 1), round(Tk.std() * 1000, 1)],
                        'length_m_min_max': [round(Ln.min(), 3), round(Ln.max(), 3)], 'max_vertices': max(x['nv'] for x in cs), 'distinct_vertex_sums': len(set(x['vol_hash'] for x in cs))}
# gaps between neighbouring planks of the same run
gaps = []
for i, a in enumerate(cs):
    ai = np.array(a['ax'])
    for j in range(i + 1, len(cs)):
        b = cs[j]
        if a['obj'] != b['obj']: continue
        bj = np.array(b['ax'])
        if abs(ai @ bj) < 0.97: continue
        d = np.array(b['c']) - np.array(a['c'])
        along = abs(d @ ai)
        across = abs(d @ np.array([-ai[1], ai[0]]))
        if along < 0.35 and across < 0.30:
            gaps.append(across - (a['width'] + b['width']) / 2)
G = np.array(gaps)
R['plank_gaps_mm'] = {'n': len(G), 'min': round(G.min() * 1000, 1), 'max': round(G.max() * 1000, 1), 'std': round(G.std() * 1000, 2), 'n_under_5mm': int((G < 0.005).sum()), 'n_over_14mm': int((G > 0.014).sum()), 'n_negative': int((G < 0).sum())}
# overlaps between planks, hull SAT in xy with margin 1 cm (all bridge planks, regardless of run)
def hull2(P):
    pts = sorted(set(map(tuple, np.round(P, 5))))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])
H = [hull2(it['V'][:, :2]) for it in planks.items]
def sep(h1, h2):
    best = -1e9
    for h in (h1, h2):
        for i in range(len(h)):
            e = h[(i + 1) % len(h)] - h[i]
            n = np.array([e[1], -e[0]]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            n /= ln
            p1 = h1 @ n; p2 = h2 @ n
            g = max(p2.min() - p1.max(), p1.min() - p2.max())
            best = max(best, g)
    return best
close = []
for i in range(len(H)):
    for j in range(i + 1, len(H)):
        a, b = planks.items[i], planks.items[j]
        if np.any(a['bmin'][:2] > b['bmax'][:2] + 0.02) or np.any(b['bmin'][:2] > a['bmax'][:2] + 0.02): continue
        g = sep(H[i], H[j])
        if g < 0.01:
            close.append((i, j, round(g * 1000, 1), a['obj'][-3:], b['obj'][-3:]))
R['plank_pairs_closer_than_1cm'] = {'n': len(close), 'pairs': close[:40]}
R['seconds'] = round(time.time() - t0, 1)
json.dump(R, open(sys.argv[-1], 'w'), indent=1)
print('BRIDGE CHECK DONE', R['seconds'])
