import sys, time, json, os, math
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import place_kit as pk
from place_kit import parts, names, scene_read
from place_kit.surfaces import roads as R
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
out = {}
settings = pk.read_settings(base + '/plan/place-settings.json')
ground = [o for o in bpy.data.objects if o.type == 'MESH' and (o.get('place_role') or '').startswith('ground.')]
trees = {}
for o in ground:
    v, t = parts.world_triangles(o)
    trees[o.name] = BVHTree.FromPolygons([tuple(x) for x in v], [tuple(x) for x in t], epsilon=0.0)
    lo, hi = scene_read.world_bounds(o)
    out.setdefault('objects', {})[o.name] = {'tris': len(t), 'verts': len(v), 'bbox': [round(float(a), 2) for a in list(lo) + list(hi)],
                                              'relief': round(scene_read.relief_metres(o), 3), 'fine_edge': round(scene_read.fine_edge_length(o), 3)}
def hits(x, y):
    res = []
    for n, tr in trees.items():
        h = tr.ray_cast(Vector((x, y, 100.0)), Vector((0, 0, -1)))
        if h[0] is not None:
            res.append((n, h[0].z))
    return res
rng = np.random.default_rng(5)
# random points everywhere + points concentrated in the village
pts = np.concatenate([rng.uniform(-70, 70, (3000, 2)), rng.uniform(-900, 900, (1500, 2)), rng.uniform(-160, 160, (1500, 2))])
gaps, multi, zdiff = [], [], 0.0
for x, y in pts:
    h = hits(float(x), float(y))
    if len(h) == 0: gaps.append((float(x), float(y)))
    elif len(h) > 1:
        zs = [a[1] for a in h]
        if max(zs) - min(zs) > 1e-3: multi.append((float(x), float(y), [a[0] for a in h]))
        zdiff = max(zdiff, max(zs) - min(zs))
out['random_points'] = len(pts); out['gaps'] = len(gaps); out['gap_examples'] = gaps[:5]
out['multi_hit_differing'] = len(multi); out['multi_examples'] = multi[:5]; out['max_z_diff_on_multi_hits'] = zdiff
parts.refresh_ground()
gh = parts.ground_height_at
# pads
def grid(x0, y0, x1, y1, n=40):
    xs = np.linspace(x0, x1, n); ys = np.linspace(y0, y1, n)
    return np.array([[gh(float(x), float(y)) for x in xs] for y in ys])
PADS = {'A': (-40.05, 7.6, -26.45, 12.4), 'B': (-9.2, 7.2, -2.8, 11.8), 'C': (-29.7, -12.8, -22.3, -8.2), 'D': (2.15, -10.2, 5.85, -5.8), 'stable': (19.1, 36.0, 28.9, 42.0)}
out['pads'] = {}
for k, (x0, y0, x1, y1) in PADS.items():
    z = grid(x0 - 1.5, y0 - 1.5, x1 + 1.5, y1 + 1.5)
    out['pads'][k] = {'range': round(float(z.max() - z.min()), 4), 'mean': round(float(z.mean()), 3)}
z = grid(21.4, 34.6, 26.6, 36.8, 60)
out['doorway_range'] = round(float(z.max() - z.min()), 4)
# slopes within 40 m of buildings: gradient from finite differences on 0.5 m steps
worst = 0.0
for k, (x0, y0, x1, y1) in PADS.items():
    for x in np.arange(x0 - 40, x1 + 40, 2.0):
        for y in np.arange(y0 - 40, y1 + 40, 2.0):
            # skip the road and yard where the ruts and dimples live
            dz1 = abs(gh(x + 1.0, y) - gh(x - 1.0, y)) / 2.0; dz2 = abs(gh(x, y + 1.0) - gh(x, y - 1.0)) / 2.0
            worst = max(worst, math.hypot(dz1, dz2))
out['max_slope_within_40m_of_buildings(2m baseline)'] = round(worst, 4)
# land outside the clearing: lumps
zs = np.array([gh(float(x), float(y)) for x, y in rng.uniform(-900, 900, (3000, 2))])
out['outside_land_range'] = [round(float(zs.min()), 3), round(float(zs.max()), 3)]
# clearing fall NE to SW
out['z_NE_corner'] = round(gh(55, 45), 3); out['z_SW_corner'] = round(gh(-45, -28), 3)
# rut measure by the kit
out['roads'] = R.audit_roads(settings, ground)
# finer rut measure: sample every 2 cm across the road at 60 stations, take the lowest point each side of the centre line, report median gauge and depth
def fine_measure(road, stations=60):
    poly = np.array(road['polyline']); seg = np.diff(poly, axis=0); ln = np.hypot(*seg.T); cum = np.concatenate([[0], np.cumsum(ln)])
    depths, gauges = [], []
    for s in np.linspace(5, cum[-1] - 5, stations):
        i = np.searchsorted(cum, s, side='right') - 1; i = min(i, len(ln) - 1)
        d = seg[i] / ln[i]; p = poly[i] + d * (s - cum[i]); n = np.array([-d[1], d[0]])
        offs = np.arange(-2.5, 2.501, 0.02)
        h = np.array([gh(*(p + n * o)) for o in offs])
        L = offs < -0.1; Rr = offs > 0.1
        li = np.argmin(np.where(L, h, 9)); ri = np.argmin(np.where(Rr, h, 9))
        shoulder = float(np.median(h)); depths.append(shoulder - min(h[li], h[ri])); gauges.append(offs[ri] - offs[li])
    return {'median_depth': round(float(np.median(depths)), 4), 'p10_depth': round(float(np.percentile(depths, 10)), 4), 'p90_depth': round(float(np.percentile(depths, 90)), 4),
            'median_gauge': round(float(np.median(gauges)), 3), 'gauge_p10': round(float(np.percentile(gauges, 10)), 3), 'gauge_p90': round(float(np.percentile(gauges, 90)), 3)}
out['fine'] = {r['name']: fine_measure(r) for r in settings.roads}
# triangle quality of the road
o = bpy.data.objects['Ground road high_road']
v, t = parts.world_triangles(o)
a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
def lens(p, q): return np.linalg.norm((p - q)[:, :2], axis=1)
e1, e2, e3 = lens(a, b), lens(b, c), lens(c, a)
area = np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])) / 2
q = 4 * math.sqrt(3) * area / (e1 ** 2 + e2 ** 2 + e3 ** 2 + 1e-12)
out['road_triangle_quality'] = {'min': round(float(q.min()), 4), 'p1': round(float(np.percentile(q, 1)), 3), 'p10': round(float(np.percentile(q, 10)), 3), 'median': round(float(np.median(q)), 3), 'below_0.1': int((q < 0.1).sum())}
json.dump(out, open(base + '/work/ground_and_roads/verify_ground.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
