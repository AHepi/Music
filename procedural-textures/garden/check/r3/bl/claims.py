# Checker round 3: independent measurements of the repair claims and of the fix stage. Reads only, saves nothing.
import bpy, bmesh, json, sys, statistics
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
out = {}

def ev_mesh(o):
    e = o.evaluated_get(dg)
    me = e.to_mesh()
    mw = e.matrix_world
    me.calc_loop_triangles()
    vs = [mw @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    return vs, tris, me, e

def bvh(objs):
    allv, allt = [], []
    for o in objs:
        vs, tris, me, e = ev_mesh(o)
        base = len(allv); allv += vs; allt += [tuple(i + base for i in t) for t in tris]
        e.to_mesh_clear()
    return BVHTree.FromPolygons(allv, allt)

def O(name):
    return bpy.data.objects.get(name)

ground = bvh([O('Astra / Courtyard receiving ground')])
def ground_z(x, y):
    h = ground.ray_cast(Vector((x, y, 6.0)), Vector((0, 0, -1)))
    return h[0].z if h[0] is not None else None

# A. veranda steps
A = {}
for nm in ('Veranda step', 'Veranda step, lower'):
    o = O(nm)
    vs, tris, me, e = ev_mesh(o)
    low = sorted(vs, key=lambda v: v.z)[:8]
    gaps = [round(v.z - ground_z(v.x, v.y), 3) for v in low]
    top = max(v.z for v in vs)
    A[nm] = {'lowest8_gap_to_ground_m': gaps, 'top_z': round(top, 3)}
    e.to_mesh_clear()
out['A_steps'] = A

# B. piers against what carries them
planks = [o for o in bpy.data.objects if o.name.startswith('Astra / varied planks') and o.type == 'MESH']
stringers = [o for o in bpy.data.objects if o.name == 'Bridge stringers']
carry = bvh(planks + stringers)
B = {}
for i in range(4):
    o = O(f'Bridge pier {i}')
    vs, tris, me, e = ev_mesh(o)
    top = max(v.z for v in vs); bot = min(v.z for v in vs)
    xs = [v.x for v in vs]; ys = [v.y for v in vs]
    gaps = []
    N = 30
    for a in range(N):
        for b in range(N):
            x = min(xs) + (max(xs) - min(xs)) * (a + .5) / N
            y = min(ys) + (max(ys) - min(ys)) * (b + .5) / N
            h = carry.ray_cast(Vector((x, y, top - 0.03)), Vector((0, 0, 1)), 0.6)
            if h[0] is not None:
                gaps.append(h[0].z - top)
    B[f'pier{i}'] = {'top_z': round(top, 3), 'bottom_z': round(bot, 3), 'grid_hits': len(gaps), 'of': N * N,
                     'min_gap_cm': round(min(gaps) * 100, 1) if gaps else None,
                     'median_gap_cm': round(statistics.median(gaps) * 100, 1) if gaps else None,
                     'touching_within_1cm_share': round(sum(1 for g in gaps if g <= 0.01) / (N * N), 2),
                     'ground_z_under_pier_centre': ground_z((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)}
    e.to_mesh_clear()
out['B_piers'] = B

# C. wall caps: loose pieces and whether each one rests on the wall or on another cap piece
C = {}
for wname, cname in (('Back wall, left', 'Back wall, left cap'), ('Back wall, right', 'Back wall, right cap'), ('Right wall behind hall', 'Right wall behind hall cap')):
    wall = O(wname); cap = O(cname)
    wv, wt, wme, we = ev_mesh(wall)
    walltop = max(v.z for v in wv)
    cv, ct, cme, ce = ev_mesh(cap)
    # connected components by shared vertex index (loop triangles share vertex ids inside one piece)
    parent = list(range(len(cv)))
    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for t in ct:
        a, b, c = t
        parent[f(b)] = f(a); parent[f(c)] = f(a)
    comps = {}
    for i in set(i for t in ct for i in t):
        comps.setdefault(f(i), []).append(i)
    wallb = BVHTree.FromPolygons(wv, wt)
    res = []
    for cid, idx in comps.items():
        pts = [cv[i] for i in idx]
        zmin = min(p.z for p in pts)
        low = [p for p in pts if p.z <= zmin + 0.005]
        # other cap pieces BVH
        other_t = [t for t in ct if f(t[0]) != cid]
        ob = BVHTree.FromPolygons(cv, other_t) if other_t else None
        gaps = []
        for p in low[:40]:
            g = []
            h = wallb.ray_cast(p + Vector((0, 0, 0.0)), Vector((0, 0, -1)), 2.0)
            if h[0] is not None: g.append(p.z - h[0].z)
            if ob is not None:
                h2 = ob.ray_cast(p, Vector((0, 0, -1)), 2.0)
                if h2[0] is not None: g.append(p.z - h2[0].z)
            # also if the point is inside the wall (ray from below)
            h3 = wallb.ray_cast(p - Vector((0, 0, 0.03)), Vector((0, 0, 1)), 0.03)
            if h3[0] is not None: g.append(-0.0)
            gaps.append(min(g) if g else None)
        ok = [g for g in gaps if g is not None]
        res.append({'verts': len(pts), 'zmin': round(zmin, 3), 'min_gap_to_support_mm': round(min(ok) * 1000, 1) if ok else None})
    floating = [r for r in res if r['min_gap_to_support_mm'] is None or r['min_gap_to_support_mm'] > 3]
    C[cname] = {'wall_top_z': round(walltop, 3), 'pieces': len(res), 'floating_pieces_over_3mm': len(floating),
                'worst_gap_mm': max([r['min_gap_to_support_mm'] for r in res if r['min_gap_to_support_mm'] is not None] + [0]),
                'lowest_cap_z': round(min(r['zmin'] for r in res), 3), 'unsupported_no_hit': sum(1 for r in res if r['min_gap_to_support_mm'] is None)}
    we.to_mesh_clear(); ce.to_mesh_clear()
out['C_caps'] = C

# D. lantern opening seen from the cameras
D = {}
glow = O('Lantern window glow')
gv, gt, gme, ge = ev_mesh(glow)
cen = sum(gv, Vector()) / len(gv)
D['glow_centre'] = [round(c, 3) for c in cen]
for cam in [o for o in bpy.data.objects if o.type == 'CAMERA']:
    org = cam.matrix_world.translation
    pts = [cen] + [cen + (v - cen) * 0.6 for v in gv[:4]]
    hits = []
    for p in pts:
        d = (p - org); L = d.length
        r = sc.ray_cast(dg, org, d.normalized(), distance=L + 0.5)
        hits.append((r[4].name if r[4] else None, round((r[1] - org).length - L, 3) if r[0] else None))
    D[cam.name] = hits
ge.to_mesh_clear()
out['D_lantern'] = D

# E. mirror-ray flags of the screens and glow lamps
E = {}
for o in bpy.data.objects:
    if o.name.startswith('Hall glow') or o.name in ('Shoji paper', 'Shoji bars', 'Lantern window glow', 'Lantern light'):
        E[o.name] = {k: getattr(o, k, None) for k in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_shadow')}
out['E_visibility'] = E

# F. compositor shadow lift
F = {}
g = bpy.data.node_groups.get('GARDEN finish')
if g:
    F['nodes'] = [(n.name, n.bl_idname.split('Node')[-1]) for n in g.nodes]
nt = getattr(sc, 'compositing_node_group', None)
F['scene_comp_nodes'] = [(n.name, n.bl_idname) for n in nt.nodes] if nt else None
out['F_comp'] = F

# G. hedge and pine
Gd = {}
h = O('Fix / far hedge')
if h:
    hv, ht, hme, he = ev_mesh(h)
    cam = O('photo') or O('Camera')
    insidev = 0
    for v in hv:
        c = world_to_camera_view(sc, cam, v)
        if 0 <= c.x <= 1 and 0 <= c.y <= 1 and c.z > 0: insidev += 1
    zs = [v.z for v in hv]
    Gd['hedge'] = {'tris': len(ht), 'bbox': [[round(min(v[i] for v in hv), 2), round(max(v[i] for v in hv), 2)] for i in range(3)],
                   'verts_visible_in_hero_frame': insidev, 'of': len(hv), 'lowest_z': round(min(zs), 3),
                   'ground_under_lowest': ground_z(*[ (lambda v: (v.x, v.y))(min(hv, key=lambda v: v.z)) ][0])}
    he.to_mesh_clear()
p = O('Pine pads')
Gd['pine_pads_polys'] = len(p.data.polygons) if p else None
ml = O('Maple leaves')
if ml:
    e = ml.evaluated_get(dg)
    Gd['maple_leaves_object_points'] = len(ml.data.vertices)
out['G_misc'] = Gd
json.dump(out, open(sys.argv[sys.argv.index('--') + 1], 'w'), indent=1)
print('CLAIMS_DONE')
