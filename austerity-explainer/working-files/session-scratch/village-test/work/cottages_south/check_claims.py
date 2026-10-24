"""My own measurements of the finished part (mesh as built, with the object matrices), written to evidence.json. Plain numbers; the report claims point here."""
import sys, json, math, colorsys
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
import place_kit as pk
from place_kit import scene_read
W = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/'
settings = json.load(open(W + 'plan/place-settings.json'))
mine = [o for o in bpy.data.objects if o.get('place_owner') == 'cottages_south' and o.type == 'MESH']
ev = {}

def world_verts(o):
    n = len(o.data.vertices)
    a = np.empty(n * 3); o.data.vertices.foreach_get('co', a)
    a = a.reshape(-1, 3)
    M = np.array(o.matrix_world)
    return a @ M[:3, :3].T + M[:3, 3]

def parts_of(o):
    V = world_verts(o)
    labels, n = scene_read.loose_part_labels(o.data)
    return V, labels, n

ev['objects_total'] = len(mine)
ev['objects_C'] = sum(1 for o in mine if o.name.startswith('Cottage C'))
ev['objects_D'] = sum(1 for o in mine if o.name.startswith('Cottage D'))
ev['every_object_has_owner_and_role'] = all(o.get('place_owner') == 'cottages_south' and o.get('place_role') for o in mine)
ev['roles_used'] = sorted({o.get('place_role') for o in mine})
ev['names_ok'] = all(o.name.startswith('Cottage C') or o.name.startswith('Cottage D') for o in mine)
ev['collection_ok'] = all(any(c.name == 'Place: cottages_south' for c in o.users_collection) for o in mine)
ev['no_props_named'] = not any(w in o.name.lower() for o in mine for w in ('barrel', 'bucket', 'bench', 'ladder', 'sack', 'jug', 'haystack', 'basket', 'woodpile', 'hurdle'))
# triangles (as built)
def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)
ev['triangles_C_as_built'] = sum(tris(o) for o in mine if o.name.startswith('Cottage C'))
ev['triangles_D_as_built'] = sum(tris(o) for o in mine if o.name.startswith('Cottage D'))
dg = bpy.context.evaluated_depsgraph_get()
def tris_eval(o):
    e = o.evaluated_get(dg)
    m = e.to_mesh()
    t = sum(len(p.vertices) - 2 for p in m.polygons)
    e.to_mesh_clear()
    return t
ev['triangles_C_evaluated'] = sum(tris_eval(o) for o in mine if o.name.startswith('Cottage C'))
ev['triangles_D_evaluated'] = sum(tris_eval(o) for o in mine if o.name.startswith('Cottage D'))

def ground(x, y):
    return pk.ground_height_at(x, y)

# footing and plinth: width (smaller horizontal side) and height above the ground, for every stone
for name in ('Cottage C footing', 'Cottage D plinth'):
    o = bpy.data.objects[name]
    V, lab, n = parts_of(o)
    widths, heights = [], []
    for k in range(n):
        P = V[lab == k]
        lo, hi = P.min(axis=0), P.max(axis=0)
        widths.append(float(min(hi[0] - lo[0], hi[1] - lo[1])))
        heights.append(float(hi[2] - ground((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)))
    ev[name] = dict(stones=n, width_min=round(min(widths), 3), width_max=round(max(widths), 3), height_above_ground_min=round(min(heights), 3), height_above_ground_max=round(max(heights), 3))

# stud spacing along the walls of C (centres of every upright, sorted)
def centres(o):
    V, lab, n = parts_of(o)
    out = []
    for k in range(n):
        P = V[lab == k]
        lo, hi = P.min(axis=0), P.max(axis=0)
        out.append(((lo + hi) / 2, hi - lo))
    return out
ups = []
for name in ('Cottage C studs', 'Cottage C post NW', 'Cottage C post NE', 'Cottage C post SW', 'Cottage C post SE', 'Cottage C door posts', 'Cottage C window posts 1', 'Cottage C window posts 2'):
    for c, d in centres(bpy.data.objects[name]):
        if c[2] < 1.4:
            ups.append(c)
xw0, xw1, yw0, yw1 = -29.63, -22.37, -12.73, -8.27
walls = {'north': ([c[0] for c in ups if abs(c[1] - yw1) < 0.12], 7.26), 'south': ([c[0] for c in ups if abs(c[1] - yw0) < 0.12], 7.26),
         'west': ([c[1] for c in ups if abs(c[0] - xw0) < 0.12], 4.46), 'east': ([c[1] for c in ups if abs(c[0] - xw1) < 0.12], 4.46)}
sp = {}
for k, (pos, L) in walls.items():
    pos = sorted(pos)
    gaps = [round(pos[i + 1] - pos[i], 3) for i in range(len(pos) - 1)]
    sp[k] = dict(uprights=len(pos), gap_min=min(gaps), gap_max=max(gaps), gaps_over_0_9=[g for g in gaps if g > 0.9])
ev['stud_spacing_C'] = sp

# ridge sag (highest point of the ridge piece along its length: truss ends against the middle of the bay)
def sag(name, axis, trusses):
    o = bpy.data.objects[name]
    V = world_verts(o)
    zs = {}
    for v in V:
        key = round(float(v[axis]), 1)
        zs[key] = max(zs.get(key, -9), float(v[2]))
    keys = sorted(zs)
    return keys, zs
keys, zs = sag('Cottage C ridge piece', 0, None)
xt = [-29.63, -26.0, -22.37]
res = []
for a, b in ((xt[0], xt[1]), (xt[1], xt[2])):
    mid = (a + b) / 2
    zmid = np.interp(mid, keys, [zs[k] for k in keys])
    zends = 0.5 * (np.interp(a, keys, [zs[k] for k in keys]) + np.interp(b, keys, [zs[k] for k in keys]))
    res.append(round(float(zends - zmid), 4))
ev['ridge_sag_C_each_bay_m'] = res
keys, zs = sag('Cottage D ridge piece', 1, None)
mid = -8.0
zmid = np.interp(mid, keys, [zs[k] for k in keys]); zends = 0.5 * (np.interp(-9.7, keys, [zs[k] for k in keys]) + np.interp(-6.3, keys, [zs[k] for k in keys]))
ev['ridge_sag_D_m'] = round(float(zends - zmid), 4)
ev['ridge_length_D_m'] = round(float(max(v[1] for v in world_verts(bpy.data.objects['Cottage D ridge piece'])) - min(v[1] for v in world_verts(bpy.data.objects['Cottage D ridge piece']))), 3)

# truss line spacing: principal rafters
cs = sorted({round(c[0][0], 2) for c in centres(bpy.data.objects['Cottage C principal rafters'])})
ev['truss_lines_x_C'] = cs
ev['truss_spacing_C_m'] = [round(cs[i + 1] - cs[i], 3) for i in range(len(cs) - 1)]

# roof pitch from the audit file; overhang from the meshes
audit = json.load(open(W + 'work/cottages_south/place-audit.json'))
pitch = {}
for ob in audit['objects']:
    if ob['name'].startswith('Cottage') and ob.get('scale'):
        for e in ob['scale']:
            if e['dimension'] == 'pitch' and e['fact'] in ('thatch_pitch', 'shingle_pitch'):
                pitch[ob['name']] = e['value']
ev['pitch_degrees_from_audit'] = pitch
tn = world_verts(bpy.data.objects['Cottage C thatch north'])
ts = world_verts(bpy.data.objects['Cottage C thatch south'])
ev['overhang_C_north_m'] = round(float(tn[:, 1].max() - (-8.2)), 3)
ev['overhang_C_south_m'] = round(float(-12.8 - ts[:, 1].min()), 3)
se = world_verts(bpy.data.objects['Cottage D shingles east'])
sw = world_verts(bpy.data.objects['Cottage D shingles west'])
ev['overhang_D_east_m'] = round(float(se[:, 0].max() - 5.85), 3)
ev['overhang_D_west_m'] = round(float(2.15 - sw[:, 0].min()), 3)
# thatch thickness (perpendicular): from the slab's top vertices to the underside plane through the lowest edge
def thatch_thickness(o, side):
    V = world_verts(o)
    labels, n = scene_read.loose_part_labels(o.data)
    top = V[V[:, 2] > np.percentile(V[:, 2], 20)]
    return None
# floor top above the ground
for name, (x0, x1, y0, y1) in (('Cottage C earth floor', (-29.4, -22.6, -12.52, -8.48)), ('Cottage D earth floor', (2.66, 5.34, -9.69, -6.42))):
    V = world_verts(bpy.data.objects[name])
    top = V[V[:, 2] > V[:, 2].min() + 0.05]
    g = np.array([ground(v[0], v[1]) for v in top[::7]])
    ev[name] = dict(top_above_ground_min=round(float((top[::7][:, 2] - g).min()), 3), top_above_ground_max=round(float((top[::7][:, 2] - g).max()), 3))
# doors and steps
for name in ('Cottage C door leaf', 'Cottage D door leaf'):
    V = world_verts(bpy.data.objects[name]); d = V.max(axis=0) - V.min(axis=0)
    ev[name] = dict(height=round(float(d[2]), 3), width=round(float(max(d[0], d[1])), 3), thickness=round(float(min(d[0], d[1])), 3))
cons = json.load(open(W + 'work/cottages_south/construction.json'))['objects']
ev['doorstep_rise_m'] = {n: cons[n]['rise_m'] for n in ('Cottage C doorstep', 'Cottage D doorstep')}
ev['doorway_floor_gap_m'] = {n: cons[n]['opening_floor_gap_m'] for n in ('Cottage C door leaf', 'Cottage D door leaf')}
# colour: daub colour and the saturation of every other object
def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)
sat = {}
for o in mine:
    attr = o.data.color_attributes.get('Col')
    if attr is None:
        continue
    n = len(attr.data)
    a = np.empty(n * 4); attr.data.foreach_get('color', a)
    a = a.reshape(-1, 4)[:, :3]
    s = srgb(a)
    mx, mn = s.max(axis=1), s.min(axis=1)
    sat_ = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    sat[o.name] = (float(sat_.mean()), float(np.percentile(sat_, 95)), '#%02X%02X%02X' % tuple(int(round(v * 255)) for v in s.mean(axis=0)))
ev['colour_saturation_by_object'] = {k: [round(v[0], 3), round(v[1], 3), v[2]] for k, v in sat.items()}
panel_sat = sat['Cottage C daub panels'][0]
others = {k: v[0] for k, v in sat.items() if k != 'Cottage C daub panels'}
ev['daub_mean_saturation'] = round(panel_sat, 3)
ev['most_saturated_other_object'] = max(others.items(), key=lambda kv: kv[1])
ev['daub_is_the_most_saturated'] = panel_sat > max(others.values())
# keep out of the high road
road = [r for r in settings['roads'] if r['name'] == 'high_road'][0]
pts = np.array(road['polyline'])
def dist_to_poly(p):
    best = 1e9
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        t = np.clip(np.dot(p - a, b - a) / np.dot(b - a, b - a), 0, 1)
        best = min(best, float(np.linalg.norm(p - (a + t * (b - a)))))
    return best
dmin = 1e9
for o in mine:
    V = world_verts(o)
    for v in V[::5]:
        dmin = min(dmin, dist_to_poly(v[:2]))
ev['nearest_distance_to_high_road_centre_m'] = round(dmin, 2)
# shutters: which leaves are ajar (their depth across the wall is far larger than a leaf's thickness)
for name in ('Cottage C shutters', 'Cottage D shutter'):
    V, lab, n = parts_of(bpy.data.objects[name])
    deep = 0
    for k in range(n):
        P = V[lab == k]; d = P.max(axis=0) - P.min(axis=0)
        if d[1] > 0.1 and d[2] > 0.3: deep += 1
    ev[name] = dict(leaves=n, ajar=deep)
# the daub chips and the wattle
ev['wattle_pieces'] = parts_of(bpy.data.objects['Cottage C wattle'])[2]
# the ground under the pads
for nm, (x0, x1, y0, y1) in (('C', (-31.2, -20.8, -14.3, -6.7)), ('D', (0.65, 7.35, -11.7, -4.3))):
    hs = [ground(x, y) for x in np.linspace(x0, x1, 9) for y in np.linspace(y0, y1, 7)]
    ev['pad_flatness_%s_m' % nm] = round(max(hs) - min(hs), 3)
json.dump(ev, open(W + 'work/cottages_south/evidence.json', 'w'), indent=1, default=str)
print('EVIDENCE written', len(ev))
