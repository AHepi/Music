import bpy, json, sys, math, time
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import *
from mathutils import Vector
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
# (a) stringer spans: bearer centres projected on stringer axis; sills count as continuous support
def axis_of(V):
    c = V[:, :2].mean(axis=0)
    u, s, vt = np.linalg.svd(V[:, :2] - c, full_matrices=False)
    return c, vt[0]
spans = []
for k, st in enumerate(stringers.items):
    c, ax = axis_of(st['V'])
    al = (st['V'][:, :2] - c) @ ax
    lo, hi = al.min(), al.max()
    sup = []
    for b in bearers.items:
        # bearer contact if z ranges touch (bearer top ~ stringer bottom) and xy overlap in hull sense: approximate by min distance of bearer verts to stringer axis line
        if abs(b['bmax'][2] - st['bmin'][2]) > 0.01: continue
        bc, bax = axis_of(b['V'])
        # bearer must cross the stringer: distance of its centre from stringer line in across coordinate small enough
        nrm = np.array([-ax[1], ax[0]])
        # take bearer verts, across-coords range
        Vb = b['V'][:, :2] - c
        ac = Vb @ nrm
        if ac.min() <= 0.06 and ac.max() >= -0.06:
            sup.append(float(((bc - c) @ ax)))
    on_sill = any(abs(sl['bmax'][2] - st['bmin'][2]) < 0.01 and np.all(st['bmin'][:2] < sl['bmax'][:2] + 0.01) and np.all(st['bmax'][:2] > sl['bmin'][:2] - 0.01) for sl in sills.items)
    sup = sorted(sup)
    pts = [lo] + sup + [hi]
    free = [pts[i + 1] - pts[i] for i in range(len(pts) - 1)]
    spans.append({'stringer': k, 'length': round(float(hi - lo), 3), 'support_positions_from_start': [round(s - lo, 3) for s in sup], 'on_sill': bool(on_sill),
                  'overhang_start': round(sup[0] - lo, 3) if sup else None, 'overhang_end': round(hi - sup[-1], 3) if sup else None,
                  'max_gap_between_supports': round(max([sup[i + 1] - sup[i] for i in range(len(sup) - 1)] or [0]), 3)})
R['stringer_spans'] = spans
R['max_bearer_spacing_m'] = max([s['max_gap_between_supports'] for s in spans])
R['max_overhang_m'] = max([max(s['overhang_start'] or 0, s['overhang_end'] or 0) for s in spans if not s['on_sill']])
# (b) posts vs planks: do posts penetrate planks?
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
def sep(h1, h2):
    best = -1e9
    for h in (h1, h2):
        for i in range(len(h)):
            e = h[(i + 1) % len(h)] - h[i]
            n = np.array([e[1], -e[0]]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            n /= ln
            p1 = h1 @ n; p2 = h2 @ n
            best = max(best, max(p2.min() - p1.max(), p1.min() - p2.max()))
    return best
PH = [hull2(p['V'][:, :2]) for p in planks.items]
pen = []
for k, p in enumerate(posts.items):
    hp = hull2(p['V'][:, :2])
    for j, pl in enumerate(planks.items):
        zov = min(p['bmax'][2], pl['bmax'][2]) - max(p['bmin'][2], pl['bmin'][2])
        if zov <= 0.002: continue
        g = sep(hp, PH[j])
        if g < 0.0:
            pen.append({'post': k, 'plank': j, 'plank_obj': pl['obj'][-3:], 'penetration_xy_mm': round(-g * 1000, 1), 'z_overlap_mm': round(zov * 1000, 1)})
R['posts_penetrating_planks'] = pen
# stringers vs posts
pen2 = []
for k, p in enumerate(posts.items):
    hp = hull2(p['V'][:, :2])
    for j, st in enumerate(stringers.items):
        zov = min(p['bmax'][2], st['bmax'][2]) - max(p['bmin'][2], st['bmin'][2])
        if zov <= 0.002: continue
        g = sep(hp, hull2(st['V'][:, :2]))
        if g < 0.0:
            pen2.append({'post': k, 'stringer': j, 'penetration_mm': round(-g * 1000, 1)})
R['posts_penetrating_stringers'] = pen2
# plank-to-plank overlaps between different objects, and planks vs stringer tops (intersections)
# (c) pegs: nearest distance to any support surface
allparts = Parts(['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007', 'Bridge stringers', 'G6 wood / bridge bearers', 'G6 wood / bridge posts'])
bvh, lab = allparts.all_bvh()
mind = []
who = []
for it in pegs.items:
    d = []
    for v in it['V']:
        h = bvh.find_nearest(Vector(v))
        if h[0] is not None:
            d.append(h[3])
    mind.append(min(d))
R['pegs_min_vertex_distance_to_wood_mm'] = {'n': len(mind), 'hist': np.histogram(np.array(mind) * 1000, bins=[0, 0.5, 1, 2, 3, 5, 10, 1000])[0].tolist(), 'max_mm': round(max(mind) * 1000, 2)}
mind = []
for it in cramps.items:
    d = [bvh.find_nearest(Vector(v))[3] for v in it['V']]
    mind.append(min(d))
R['cramps_min_vertex_distance_to_wood_mm'] = {'n': len(mind), 'hist': np.histogram(np.array(mind) * 1000, bins=[0, 0.5, 1, 2, 3, 5, 10, 1000])[0].tolist(), 'max_mm': round(max(mind) * 1000, 2)}
# (d) pond pebbles / footings
if 'Life / pond pebbles' in bpy.data.objects:
    pp = Parts(['Life / pond pebbles'])
    R['n_pebbles'] = len(pp.items)
    inter = []
    for f in footings.items + sills.items:
        for p in pp.items:
            if np.all(p['bmin'] < f['bmax'] - 0.005) and np.all(p['bmax'] > f['bmin'] + 0.005):
                inter.append((f['obj'], f['idx'], p['id']))
    R['pebbles_overlapping_footing_boxes'] = inter[:20]
    R['n_pebbles_overlapping_footing_boxes'] = len(inter)
    # pebbles within 1.2 m of the centre line and above bed
    nodes = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]
    def dseg(p, a, b):
        a = np.array(a); b = np.array(b); p = np.array(p)
        t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        return np.linalg.norm(p - (a + t * (b - a)))
    cnt = 0
    for p in pp.items:
        c = (p['bmin'] + p['bmax'])[:2] / 2
        if min(dseg(c, a, b) for a, b in zip(nodes[:-1], nodes[1:])) < 1.2: cnt += 1
    R['pebbles_within_1p2m_of_bridge_line'] = cnt
# (e) bearers: bearer bottoms, longest bearer
R['bearers'] = [{'k': i, 'z': [round(float(b['bmin'][2]), 3), round(float(b['bmax'][2]), 3)], 'length_m': round(float(np.ptp((b['V'][:, :2] - axis_of(b['V'])[0]) @ axis_of(b['V'])[1])), 3)} for i, b in enumerate(bearers.items)]
# water level object
if 'Pond water' in bpy.data.objects:
    w = bpy.data.objects['Pond water']; R['pond_water_z'] = round(float(w.matrix_world.translation.z), 3)
json.dump(R, open(sys.argv[-1], 'w'), indent=1)
print('CHECK2 DONE')
