import bpy, json, sys, math, time
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import *
from mathutils import Vector
R = {}
PL = ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007']
stringers = Parts(['Bridge stringers'])
bearers = Parts(['G6 wood / bridge bearers'])
sills = Parts(['Bridge pier 0', 'Bridge pier 3'])
footings = Parts(['G6 wood / bridge footings', 'Bridge pier 1', 'Bridge pier 2'])
pegs = Parts(['G6 wood / bridge pegs'])
cramps = Parts(['G6 wood / bridge cramps'])
allw = Parts(PL + ['Bridge stringers', 'G6 wood / bridge bearers', 'G6 wood / bridge posts'])
bvh, lab = allw.all_bvh()
def signed_min(it):
    best = 1e9
    for v in it['V']:
        h = bvh.find_nearest(Vector(v))
        if h[0] is None: continue
        d = (Vector(v) - h[0]).dot(h[1])
        sd = h[3] if d >= 0 else -h[3]
        best = min(best, sd)
    return best
sd = np.array([signed_min(it) for it in pegs.items]) * 1000
R['pegs'] = {'n': len(sd), 'any_vertex_inside_or_within_1mm': int((sd <= 1.0).sum()), 'floating_over_1mm': int((sd > 1.0).sum()), 'floating_values_mm': np.round(sd[sd > 1.0], 2).tolist()}
sd = np.array([signed_min(it) for it in cramps.items]) * 1000
R['cramps'] = {'n_parts': len(sd), 'touch_or_inside': int((sd <= 1.0).sum()), 'floating_over_1mm': int((sd > 1.0).sum()), 'floating_values_mm': np.round(sd[sd > 1.0], 2).tolist()}
# stringer spans from real contact positions
lb, llab = bearers.all_bvh()
spans = []
for st in stringers.items:
    V = st['V']; c = V[:, :2].mean(axis=0)
    u, s, vt = np.linalg.svd(V[:, :2] - c, full_matrices=False)
    ax = vt[0]
    al = (V[:, :2] - c) @ ax; lo, hi = al.min(), al.max()
    # support extents along axis from bearers' contact samples under the stringer bottom (z=stringer bmin z)
    zb = st['bmin'][2]
    pos = {}
    for t in np.arange(lo + 0.005, hi, 0.01):
        for a in np.linspace(-0.03, 0.03, 3):
            p = c + ax * t + np.array([-ax[1], ax[0]]) * a
            h = lb.ray_cast(Vector((p[0], p[1], zb + 0.02)), Vector((0, 0, -1)), 0.2)
            if h[0] is not None and zb - h[0].z < 0.006:
                pos.setdefault(int(llab[h[2]]), []).append(float(t - lo))
    sup = sorted([(min(v), max(v)) for v in pos.values()])
    # sill support
    on_sill = False
    for sl in sills.items:
        if abs(sl['bmax'][2] - zb) < 0.01 and np.all(st['bmin'][:2] < sl['bmax'][:2] + 0.01) and np.all(st['bmax'][:2] > sl['bmin'][:2] - 0.01): on_sill = True
    L = hi - lo
    free = []
    if sup:
        free.append(sup[0][0]); free.append(L - sup[-1][1])
        for i in range(len(sup) - 1): free.append(sup[i + 1][0] - sup[i][1])
    spans.append({'k': st['id'], 'length': round(float(L), 3), 'on_sill': on_sill, 'supports(from,to)': [(round(a, 2), round(b, 2)) for a, b in sup], 'free_lengths': [round(x, 3) for x in free]})
R['stringer_spans'] = spans
R['max_free_span_m'] = max([max(s['free_lengths']) for s in spans if s['free_lengths'] and not s['on_sill']] or [0])
# footings floating fraction vs terrain
gv, gt, _ = world_mesh(bpy.data.objects['Astra / Courtyard receiving ground'], evaluated=True)
ground = BVHTree.FromPolygons([tuple(x) for x in gv], [tuple(x) for x in gt], epsilon=0.0)
bed_obj = bpy.data.objects['Life / pond bed']
bv, bt, _ = world_mesh(bed_obj, evaluated=True)
bed = BVHTree.FromPolygons([tuple(x) for x in bv], [tuple(x) for x in bt], epsilon=0.0)
res = []
for it in footings.items:
    zb = it['bmin'][2]
    gaps = []
    for x in np.linspace(it['bmin'][0] + 0.02, it['bmax'][0] - 0.02, 12):
        for y in np.linspace(it['bmin'][1] + 0.02, it['bmax'][1] - 0.02, 12):
            # only points actually under the footing body: ray up inside footing
            b = footings.bvh(it['id'])
            hh = b.ray_cast(Vector((x, y, zb - 0.05)), Vector((0, 0, 1)), 1.0)
            if hh[0] is None: continue
            zu = hh[0].z
            best = None
            for T in (ground, bed):
                h = T.ray_cast(Vector((x, y, zu + 0.3)), Vector((0, 0, -1)), 2.0)
                if h[0] is not None and (best is None or h[0].z > best): best = h[0].z
            if best is not None: gaps.append(zu - best)
    g = np.array(gaps) * 1000
    res.append({'obj': it['obj'].replace('G6 wood / bridge ', ''), 'idx': it['idx'], 'n': len(g), 'floating_over_10mm_pct': round(float((g > 10).mean() * 100), 1), 'max_float_mm': round(float(g.max()), 1), 'buried_mm_max': round(float(-g.min()), 1), 'bottom_z': round(float(zb), 3)})
R['footings_vs_terrain_top_surface'] = res
json.dump(R, open(sys.argv[-1], 'w'), indent=1)
print('CHECK3 DONE')
