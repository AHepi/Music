# What this does (plain words): STUDY ONLY, saves nothing in the scene. Tests the kit's planned "geometry reader" idea on the courtyard: for every spot of the ground (a 0.2 m grid
# seen from above) and for the faces of the plaster walls and the roof, it asks the real 3D shapes two questions with rays:
#   (a) OPENNESS: what share of the sky can this spot see? (32 fixed directions over the half-sphere)
#   (b) YEAR SUN: how much direct sun does this spot get over a whole year, if the garden is at latitude 35 degrees north (Kyoto) with north along +y?
#       (4 days = both solstices and the equinox twice, every hour of daylight; a hall, wall, rock or tree that is in the way blocks it; leaves block 60 %)
# It also counts where the add-on grew its own moss (the real moss pieces) and checks how well a "shade" rule would predict it.
# Run: blender -b --disable-autoexec FILE --python c8_shade_maps.py -- OUT_PREFIX
import json, math, re, sys, time
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PREFIX = sys.argv[sys.argv.index('--') + 1]
T0 = time.time()
def say(t): print(f'[{time.time() - T0:6.1f}s] {t}', flush=True)
deps = bpy.context.evaluated_depsgraph_get()

SOLID_SKIP = r'^(Hills,|Dark plain|Pond water|Basin water|Lily pads|Lotus|Fallen leaves|Courtyard ground source|CT / |Maple leaves|Maple inner mass|Pine pads|Bamboo leaves|Astra / moss|Astra / pebbles)'
FOLIAGE = r'^(Maple leaves|Maple inner mass|Pine pads|Bamboo leaves)$'
def world_mesh(names_rx, skip_rx=None):
    verts, polys, off = [], [], 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.hide_render and not ob.name.startswith('x'): 
            if not (ob.type == 'MESH' and re.match(names_rx, ob.name) and not ob.hide_render): continue
        if not re.match(names_rx, ob.name): continue
        if skip_rx and re.match(skip_rx, ob.name): continue
        ev = ob.evaluated_get(deps); me = ev.to_mesh()
        if len(me.polygons) == 0: ev.to_mesh_clear(); continue
        me.calc_loop_triangles()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        mw = np.array(ob.matrix_world); co = co @ mw[:3, :3].T + mw[:3, 3]
        tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', tri)
        verts.append(co); polys.append(tri.reshape(-1, 3) + off); off += len(co); ev.to_mesh_clear()
    V = np.concatenate(verts); P = np.concatenate(polys)
    return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(p) for p in P]), len(P)
solid, ns = world_mesh(r'.*', SOLID_SKIP)
foliage, nf = world_mesh(FOLIAGE)
ground_bvh, ng = world_mesh(r'^(Astra / Courtyard receiving ground|Raked gravel court)$')
say(f'trees built: solid {ns} triangles, foliage {nf}, ground {ng}')

# ---------- sun positions: latitude 35 N, north = +y, east = +x
LAT = math.radians(35.0)
def sun_dirs():
    out = []
    for decl in (-23.44, 0.0, 23.44, 0.0):
        d = math.radians(decl)
        for hour in range(5, 20):
            H = math.radians(15.0 * (hour - 12 + 0.5))
            sin_el = math.sin(LAT) * math.sin(d) + math.cos(LAT) * math.cos(d) * math.cos(H)
            if sin_el < math.sin(math.radians(2.0)): continue
            el = math.asin(sin_el)
            cos_az = (math.sin(d) - sin_el * math.sin(LAT)) / (math.cos(el) * math.cos(LAT))
            az = math.acos(max(-1, min(1, cos_az)))
            if H > 0: az = 2 * math.pi - az              # afternoon: west
            out.append(Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), sin_el)))
    return out
SUN = sun_dirs()
say(f'{len(SUN)} sun positions')
def hemisphere(n):
    """n fixed, evenly spread directions over the upper half-sphere, cosine-weighted (Fibonacci spiral)."""
    ds = []
    for i in range(n):
        u = (i + 0.5) / n; phi = i * 2.399963229728653
        r = math.sqrt(u); ds.append((r * math.cos(phi), r * math.sin(phi), math.sqrt(1 - u)))
    return ds
HEMI = hemisphere(32)
def basis(n):
    n = Vector(n).normalized(); a = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    t = n.cross(a).normalized(); b = n.cross(t); return t, b, n
def blocked(origin, d, dist=60.0):
    """1.0 if a solid thing is in the way, 0.6 if leaves are, else 0."""
    if solid.ray_cast(origin, d, dist)[0] is not None: return 1.0
    if foliage.ray_cast(origin, d, dist)[0] is not None: return 0.6
    return 0.0
def measure(points, normals):
    sun = np.zeros(len(points)); opn = np.zeros(len(points))
    sun_max = sum(max(0.0, Vector((0, 0, 1)).dot(s)) for s in SUN)
    for i, (p, n) in enumerate(zip(points, normals)):
        o = Vector(p) + Vector(n) * 0.03
        s_sum = 0.0
        for s in SUN:
            c = Vector(n).dot(s)
            if c <= 0: continue
            s_sum += c * (1.0 - blocked(o, s))
        sun[i] = s_sum / sun_max
        t, b, nn = basis(n); o_sum = 0.0
        for (x, y, z) in HEMI:
            d = (t * x + b * y + nn * z)
            o_sum += 1.0 - blocked(o, d, 40.0)
        opn[i] = o_sum / len(HEMI)
    return sun, opn

# ---------- the ground grid
X0, X1, Y0, Y1, STEP = -11.0, 11.0, -8.5, 12.5, 0.2
xs = np.arange(X0 + STEP / 2, X1, STEP); ys = np.arange(Y0 + STEP / 2, Y1, STEP)
pts, nors, idx = [], [], []
for j, y in enumerate(ys):
    for i, x in enumerate(xs):
        hit = ground_bvh.ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)), 60.0)
        if hit[0] is None: continue
        pts.append(tuple(hit[0])); nors.append(tuple(hit[1])); idx.append((j, i))
say(f'ground grid {len(xs)} x {len(ys)}, {len(pts)} spots')
g_sun, g_opn = measure(pts, nors)
say('ground measured')
S = np.full((len(ys), len(xs)), np.nan, np.float32); O = S.copy(); Z = S.copy()
for (j, i), s, o, p in zip(idx, g_sun, g_opn, pts): S[j, i] = s; O[j, i] = o; Z[j, i] = p[2]
np.savez_compressed(PREFIX + '_ground.npz', sun=S.astype(np.float16), openness=O.astype(np.float16), z=Z.astype(np.float16), x0=X0, y0=Y0, step=STEP)

# ---------- walls and roof: face-centre grids
def face_samples(name_rx, nz_max, min_area, step=0.4):
    P, N, tag = [], [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not re.match(name_rx, ob.name): continue
        ev = ob.evaluated_get(deps); me = ev.to_mesh(); mw = np.array(ob.matrix_world)
        for poly in me.polygons:
            if poly.area < min_area: continue
            n = np.array(poly.normal) @ mw[:3, :3].T; n /= np.linalg.norm(n)
            if abs(n[2]) > nz_max: continue
            vs = [np.array(me.vertices[v].co) @ mw[:3, :3].T + mw[:3, 3] for v in poly.vertices]
            if len(vs) != 4: continue
            a, b, c, d = vs; e1 = b - a; e2 = d - a
            n1 = max(1, int(np.linalg.norm(e1) / step)); n2 = max(1, int(np.linalg.norm(e2) / step))
            for u in range(n1):
                for v in range(n2):
                    P.append(tuple(a + e1 * (u + .5) / n1 + e2 * (v + .5) / n2)); N.append(tuple(n)); tag.append(ob.name)
        ev.to_mesh_clear()
    return P, N, tag
res = {'ground': {}, 'walls': {}, 'roof': {}}
wp, wn, wt = face_samples(r'^(Hall plaster|Back wall, (left|right)|Right wall behind hall)$', 0.3, 0.8)
w_sun, w_opn = measure(wp, wn); say(f'walls measured: {len(wp)} spots')
def facing(n):
    az = math.degrees(math.atan2(n[0], n[1])) % 360      # clockwise from north (+y)
    return ['north', 'east', 'south', 'west'][int(((az + 45) % 360) // 90)]
for f in ('north', 'east', 'south', 'west'):
    sel = [k for k, n in enumerate(wn) if facing(n) == f]
    if sel: res['walls'][f] = {'spots': len(sel), 'year_sun_mean': float(np.mean(w_sun[sel])), 'openness_mean': float(np.mean(w_opn[sel]))}
rp, rn, rt = face_samples(r'^Hall roof$', 0.99, 0.5, 0.5)
r_sun, r_opn = measure(rp, rn); say(f'roof measured: {len(rp)} spots')
for f in ('north', 'east', 'south', 'west'):
    sel = [k for k, n in enumerate(rn) if facing(n) == f and abs(n[2]) < 0.99 and n[2] > 0.1]
    if sel: res['roof'][f + '-facing slope'] = {'spots': len(sel), 'year_sun_mean': float(np.mean(r_sun[sel])), 'openness_mean': float(np.mean(r_opn[sel]))}
json.dump({'walls_points': [[float(v) for v in p] + [float(v) for v in n] + [float(s), float(o)] for p, n, s, o in zip(wp, wn, w_sun, w_opn)][::3]}, open(PREFIX + '_walls_points.json', 'w'))

# ---------- the add-on's own moss: where did it put its clumps?
mo = bpy.data.objects['Astra / moss grouped bodies']; ev = mo.evaluated_get(deps); me = ev.to_mesh()
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); ev.to_mesh_clear()
CELL = 0.5
nxc, nyc = int((X1 - X0) / CELL), int((Y1 - Y0) / CELL)
H, _, _ = np.histogram2d(co[:, 0], co[:, 1], bins=[nxc, nyc], range=[[X0, X1], [Y0, Y1]])
# mean ground sun/openness per 0.5 m cell
cs = np.zeros((nxc, nyc)); co_ = np.zeros((nxc, nyc)); cn = np.zeros((nxc, nyc))
for (j, i), s, o, p in zip(idx, g_sun, g_opn, pts):
    a = min(nxc - 1, int((p[0] - X0) / CELL)); b = min(nyc - 1, int((p[1] - Y0) / CELL)); cs[a, b] += s; co_[a, b] += o; cn[a, b] += 1
ok = cn > 0; cs[ok] /= cn[ok]; co_[ok] /= cn[ok]
land = ok & (np.array([[True] * nyc] * nxc))
def rank(a): return np.argsort(np.argsort(a)).astype(float)
def spearman(a, b): ra, rb = rank(a), rank(b); return float(np.corrcoef(ra, rb)[0, 1])
dens = H[ok]
res['moss_vs_shade'] = {'cells_0p5m': int(ok.sum()), 'cells_with_moss': int((dens > 0).sum()),
                        'spearman_moss_density_vs_year_sun': spearman(dens, cs[ok]), 'spearman_moss_density_vs_openness': spearman(dens, co_[ok]),
                        'mean_year_sun_where_moss': float(np.average(cs[ok], weights=np.maximum(dens, 1e-9))), 'mean_year_sun_everywhere': float(cs[ok].mean()),
                        'mean_openness_where_moss': float(np.average(co_[ok], weights=np.maximum(dens, 1e-9))), 'mean_openness_everywhere': float(co_[ok].mean())}
np.savez_compressed(PREFIX + '_moss_density.npz', density=H.astype(np.float32), cell=CELL, x0=X0, y0=Y0)
fin = ~np.isnan(S)
res['ground'] = {'spots': int(fin.sum()), 'year_sun_mean': float(np.nanmean(S)), 'year_sun_p10_p50_p90': [float(np.nanpercentile(S, q)) for q in (10, 50, 90)],
                 'openness_mean': float(np.nanmean(O)), 'openness_p10_p50_p90': [float(np.nanpercentile(O, q)) for q in (10, 50, 90)],
                 'share_of_ground_below_20pct_year_sun': float((S[fin] < 0.2).mean()), 'share_below_35pct': float((S[fin] < 0.35).mean())}
res['sun_positions'] = len(SUN); res['latitude_deg'] = 35.0; res['north_axis'] = '+y'
json.dump(res, open(PREFIX + '_stats.json', 'w'), indent=1)
say('DONE ' + json.dumps({k: res[k] for k in ('ground', 'walls', 'roof', 'moss_vs_shade')}))
