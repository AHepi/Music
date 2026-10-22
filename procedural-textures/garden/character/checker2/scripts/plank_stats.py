import bpy, sys, json, math, numpy as np, hashlib
OUT = sys.argv[-1]
def mesh_world(ob):
    me = ob.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    M = np.array(ob.matrix_world); V = co @ M[:3, :3].T + M[:3, 3]
    polys = [tuple(p.vertices) for p in me.polygons]
    return V, polys
def comps(V, polys):
    parent = list(range(len(V)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for p in polys:
        r = find(p[0])
        for v in p[1:]:
            rv = find(v)
            if rv != r: parent[rv] = r
    roots = np.array([find(i) for i in range(len(V))]); _, c = np.unique(roots, return_inverse=True); return c
def plank_rows(objname):
    V, polys = mesh_world(bpy.data.objects[objname]); c = comps(V, polys)
    rows = []
    for k in range(c.max() + 1):
        P = V[c == k]
        ctr = P[:, :2].mean(axis=0)
        u, s, vt = np.linalg.svd(P[:, :2] - ctr, full_matrices=False)
        ax = vt[0]; nr = np.array([-ax[1], ax[0]])
        al = (P[:, :2] - ctr) @ ax; ac = (P[:, :2] - ctr) @ nr
        # thickness: z extent of the vertices within the central 50% of the length
        mid = np.abs(al) < 0.25 * (al.max() - al.min())
        Pm = P[mid]
        th = float(Pm[:, 2].max() - Pm[:, 2].min())
        # bow: z of the top surface along the length: top z of vertices binned along length
        bins = np.linspace(al.min(), al.max(), 9); topz = []
        for i in range(8):
            m = (al >= bins[i]) & (al <= bins[i + 1])
            if m.sum() > 2: topz.append(P[m, 2].max())
        bow = float(max(topz) - min(topz)) if topz else 0.0
        sig = hashlib.md5(np.round((P - P.mean(axis=0)) @ np.array([[ax[0], ax[1], 0], [nr[0], nr[1], 0], [0, 0, 1]]).T, 3).tobytes()).hexdigest()[:10]
        rows.append({'obj': objname, 'k': k, 'nv': int((c == k).sum()), 'len': float(al.max() - al.min()), 'width': float(ac.max() - ac.min()), 'thick_mm': th * 1000, 'bow_mm': bow * 1000,
                     'c': ctr.tolist(), 'ax': ax.tolist(), 'zmax': float(P[:, 2].max()), 'sig': sig})
    return rows
R = {}
bridge = []
for n in ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005']:
    bridge += plank_rows(n)
breakers = plank_rows('Astra / varied planks.006') + plank_rows('Astra / varied planks.007')
deck = []
for n in ['Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002']:
    deck += plank_rows(n)
def stats(rows, nm):
    W = np.array([r['width'] for r in rows]) * 100; T = np.array([r['thick_mm'] for r in rows]); B = np.array([r['bow_mm'] for r in rows]); L = np.array([r['len'] for r in rows])
    return {'n': len(rows), 'width_cm_min_max_std': [round(W.min(), 2), round(W.max(), 2), round(W.std(), 2)], 'thick_mm_min_max_std': [round(T.min(), 1), round(T.max(), 1), round(T.std(), 1)],
            'len_m_min_max': [round(L.min(), 2), round(L.max(), 2)], 'max_vertices': max(r['nv'] for r in rows), 'distinct_shapes': len(set(r['sig'] for r in rows)), 'share_top_variation_over_2mm': round(float((B > 2).mean()), 2), 'top_variation_mm_max': round(float(B.max()), 1)}
R['bridge_planks_49'] = stats(bridge, 'bridge'); R['breaker_boards'] = stats(breakers, 'breakers'); R['deck_boards'] = stats(deck, 'deck')
# gaps in each bridge run: sort by position along the run direction
gaps = []
for obj in ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005']:
    rows = [r for r in bridge if r['obj'] == obj]
    # run direction = mean of the plank axes perpendicular
    ax = np.array(rows[0]['ax']); nrm = np.array([-ax[1], ax[0]])
    pos = sorted(rows, key=lambda r: np.array(r['c']) @ nrm)
    for a, b in zip(pos[:-1], pos[1:]):
        d = (np.array(b['c']) - np.array(a['c'])) @ nrm
        gaps.append(abs(d) - (a['width'] + b['width']) / 2)
G = np.array(gaps) * 1000
R['bridge_gaps_mm'] = {'n': len(G), 'min': round(float(G.min()), 1), 'max': round(float(G.max()), 1), 'std': round(float(G.std()), 2), 'share_in_5_14mm': round(float(((G >= 5) & (G <= 14)).mean()), 2), 'n_outside_5_14': [round(float(x), 1) for x in G if not (5 <= x <= 14)][:30]}
# deck rows
yr = {}
for r in deck:
    yr.setdefault(round(r['c'][1], 1), []).append(r)
R['deck_rows'] = {'n_rows_by_y': len(yr)}
# deck gaps between adjacent rows (along y)
ys = sorted(set(round(r['c'][1], 3) for r in deck))
R['deck_unique_y_centres'] = len(ys)
# staggering: for each pair of neighbouring rows, minimal distance between butt joints
rows_by_y = {}
for r in deck:
    rows_by_y.setdefault(round(r['c'][1] / 0.0001), []).append(r)
# group by y with tolerance 3 cm
deck_sorted = sorted(deck, key=lambda r: r['c'][1])
groups = []
for r in deck_sorted:
    if groups and abs(r['c'][1] - groups[-1][-1]['c'][1]) < 0.03: groups[-1].append(r)
    else: groups.append([r])
R['deck_rows_grouped'] = len(groups)
joints = []
for g in groups:
    js = sorted(r['c'][0] + r['len'] / 2 for r in g)[:-1] if all(abs(r['ax'][0]) > 0.9 for r in g) else None
    joints.append(js)
mins = []
for a, b in zip(groups[:-1], groups[1:]):
    ja = []; jb = []
    for r in sorted(a, key=lambda r: r['c'][0])[:-1]: ja.append(r['c'][0] + r['len'] / 2)
    for r in sorted(b, key=lambda r: r['c'][0])[:-1]: jb.append(r['c'][0] + r['len'] / 2)
    if ja and jb: mins.append(min(abs(x - y) for x in ja for y in jb))
R['deck_min_stagger_between_neighbour_rows_m'] = round(min(mins), 2) if mins else None
R['deck_lengths_distinct_m'] = sorted(set(round(r['len'], 1) for r in deck))[:12]
json.dump(R, open(OUT, 'w'), indent=1)
print('PLANK STATS DONE')
