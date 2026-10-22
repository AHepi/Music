import bpy, sys, json, numpy as np
OUT = sys.argv[-1]
res = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or not ob.data.uv_layers: continue
    me = ob.data
    for ul in me.uv_layers:
        n = len(me.loops)
        uv = np.empty(n * 2); ul.data.foreach_get('uv', uv); uv = uv.reshape(n, 2)
        ls = np.array([p.loop_start for p in me.polygons]); lt = np.array([p.loop_total for p in me.polygons])
        pos = neg = 0; zero = 0
        # signed area via loops (fan not needed: use shoelace per polygon)
        areas = np.zeros(len(me.polygons))
        for i, (s, t) in enumerate(zip(ls, lt)):
            P = uv[s:s + t]; x, y = P[:, 0], P[:, 1]
            areas[i] = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
        # normal-based orientation: a mirrored face has UV winding opposite to its 3D winding; the winding of uv vs 3D normal sign: compare with polygon's 3D orientation in the plane
        # use tangent-handedness: sign of (dP/du x dP/dv) . N via first triangle of each polygon
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        mir = 0; tot = 0
        for i, p in enumerate(me.polygons):
            s = p.loop_start
            if p.loop_total < 3: continue
            v = [me.loops[s + k].vertex_index for k in range(3)]
            a, b, c = co[v[0]], co[v[1]], co[v[2]]
            u0, u1, u2 = uv[s], uv[s + 1], uv[s + 2]
            e1, e2 = b - a, c - a; d1, d2 = u1 - u0, u2 - u0
            det = d1[0] * d2[1] - d2[0] * d1[1]
            if abs(det) < 1e-12: continue
            Tn = (e1 * d2[1] - e2 * d1[1]) / det; Bn = (e2 * d1[0] - e1 * d2[0]) / det
            n = np.cross(e1, e2)
            tot += 1
            if np.dot(np.cross(Tn, Bn), n) < 0: mir += 1
        res.append({'obj': ob.name, 'uv': ul.name, 'faces': tot, 'mirrored_share': round(mir / max(tot, 1), 3), 'uv_min': np.round(uv.min(axis=0), 2).tolist(), 'uv_max': np.round(uv.max(axis=0), 2).tolist(),
                    'mats': [s.material.name for s in ob.material_slots if s.material][:2]})
        break
bad = [r for r in res if r['mirrored_share'] > 0.02]
json.dump({'n_objects': len(res), 'with_mirrored_over_2pct': bad, 'all': res}, open(OUT, 'w'))
print('UV DONE', len(res), 'bad', len(bad))
