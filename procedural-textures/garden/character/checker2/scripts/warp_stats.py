import bpy, sys, json, math, numpy as np
OUT = sys.argv[-1]
def mesh_world(ob):
    me = ob.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    M = np.array(ob.matrix_world); V = co @ M[:3, :3].T + M[:3, 3]
    return V, [tuple(p.vertices) for p in me.polygons]
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
def warp(objs):
    out = []
    for obj in objs:
        V, polys = mesh_world(bpy.data.objects[obj]); c = comps(V, polys)
        for k in range(c.max() + 1):
            P = V[c == k]; ctr = P[:, :2].mean(axis=0)
            u, s, vt = np.linalg.svd(P[:, :2] - ctr, full_matrices=False); ax = vt[0]; nr = np.array([-ax[1], ax[0]])
            al = (P[:, :2] - ctr) @ ax; ac = (P[:, :2] - ctr) @ nr
            top = P[:, 2] > P[:, 2].max() - 0.012
            A = al[top]; Cc = ac[top]; Z = P[top, 2]
            if len(Z) < 8: continue
            L = A.max() - A.min(); W = Cc.max() - Cc.min()
            # bow: z at middle third minus mean z at the two end thirds (centre line only: |ac| < 0.3W)
            cl = np.abs(Cc) < 0.3 * W / 2 + 1e-9
            def zat(sel): return Z[sel].mean() if sel.sum() else np.nan
            mid = zat(cl & (np.abs(A) < L / 6)); e1 = zat(cl & (A < -L / 3)); e2 = zat(cl & (A > L / 3))
            bow = mid - np.nanmean([e1, e2])
            # cup at middle: centre minus edges
            m3 = np.abs(A) < L / 6
            cen = zat(m3 & (np.abs(Cc) < W / 6)); edg = np.nanmean([zat(m3 & (Cc < -W / 3)), zat(m3 & (Cc > W / 3))])
            cup = cen - edg
            # twist: cross slope at the two end thirds
            def xs(sel):
                if sel.sum() < 4: return np.nan
                a = np.polyfit(Cc[sel], Z[sel], 1)[0]; return math.degrees(math.atan(a))
            t1 = xs(A < -L / 6); t2 = xs(A > L / 6)
            twist = abs(t1 - t2) if not (np.isnan(t1) or np.isnan(t2)) else np.nan
            out.append({'obj': obj[-3:], 'bow_mm': float(bow * 1000), 'cup_mm': float(cup * 1000), 'twist_deg': float(twist)})
    return out
res = {}
for nm, objs in (('bridge', ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005']), ('deck', ['Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002'])):
    w = warp(objs)
    B = np.array([abs(x['bow_mm']) for x in w]); C = np.array([abs(x['cup_mm']) for x in w]); T = np.array([x['twist_deg'] for x in w])
    T = np.nan_to_num(T)
    any_ = (B > 2) | (C > 2) | (T > 0.5)
    res[nm] = {'n': len(w), 'share_with_bow_or_cup_over_2mm_or_twist_over_0.5deg': round(float(any_.mean()), 2), 'bow_mm_p50_max': [round(float(np.median(B)), 2), round(float(B.max()), 1)], 'cup_mm_p50_max': [round(float(np.median(C)), 2), round(float(C.max()), 1)], 'twist_deg_p50_max': [round(float(np.median(T)), 2), round(float(T.max()), 2)],
                'any_over_15mm_or_3deg': int(((B > 15) | (C > 15) | (T > 3)).sum())}
json.dump(res, open(OUT, 'w'), indent=1); print('WARP DONE', json.dumps(res))
