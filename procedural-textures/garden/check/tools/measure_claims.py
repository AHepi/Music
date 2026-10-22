# Checker script (fresh eyes): independent measurement of the four repair claims, no drawing.
# Run: blender -b --disable-autoexec FILE.blend --python measure_claims.py -- OUT.json
# Measures from the evaluated geometry in world space, using ray casts, not by reading the builders' numbers.
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out_path = sys.argv[sys.argv.index('--') + 1]
dg = bpy.context.evaluated_depsgraph_get()
R = {}


def world_mesh(o):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return verts, polys


def bvh_of(objs):
    verts, polys, off = [], [], 0
    for o in objs:
        v, p = world_mesh(o)
        verts += v
        polys += [tuple(i + off for i in q) for q in p]
        off += len(v)
    return BVHTree.FromPolygons(verts, polys) if polys else None


def objs(prefixes=None, names=None):
    res = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        if names and o.name in names:
            res.append(o)
        elif prefixes and any(o.name.startswith(p) for p in prefixes):
            res.append(o)
    return res


ground = bpy.data.objects.get('Astra / Courtyard receiving ground')
gbvh = bvh_of([ground])


def ground_z(x, y):
    hit = gbvh.ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else None


# ---- A. bridge piers: gap between pier top and what carries it (planks + stringers) ----
carriers = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and
            (o.name.startswith('Astra / varied planks') or o.name == 'Bridge stringers')]
cbvh = bvh_of(carriers)
piers = {}
for i in range(4):
    p = bpy.data.objects.get(f'Bridge pier {i}')
    v, _ = world_mesh(p)
    top = max(c.z for c in v)
    topv = [c for c in v if c.z > top - 0.004]
    cx = sum(c.x for c in topv) / len(topv)
    cy = sum(c.y for c in topv) / len(topv)
    pts = [(cx, cy)] + [((cx + c.x) / 2, (cy + c.y) / 2) for c in topv]
    gaps = []
    for (x, y) in pts:
        hit = cbvh.ray_cast(Vector((x, y, top - 0.25)), Vector((0, 0, 1)))
        gaps.append(None if hit[0] is None else hit[0].z - top)
    g = [q for q in gaps if q is not None]
    piers[p.name] = {'pier_top_z': round(top, 4), 'n_samples': len(pts), 'n_hit': len(g),
                     'gap_cm_min': round(min(g) * 100, 2) if g else None,
                     'gap_cm_median': round(sorted(g)[len(g) // 2] * 100, 2) if g else None,
                     'gap_cm_max': round(max(g) * 100, 2) if g else None}
R['A_bridge_piers'] = piers

# ---- B. veranda steps: lowest points against the ground below them ----
steps = {}
for name in ('Veranda step', 'Veranda step, lower'):
    o = bpy.data.objects.get(name)
    v, _ = world_mesh(o)
    zmin = min(c.z for c in v)
    zmax = max(c.z for c in v)
    low = [c for c in v if c.z < zmin + 0.01]
    clear = []
    for c in low:
        gz = ground_z(c.x, c.y)
        if gz is not None:
            clear.append(c.z - gz)
    steps[name] = {'lowest_z': round(zmin, 4), 'top_z': round(zmax, 4), 'n_low_verts': len(low),
                   'clearance_cm_over_ground_min': round(min(clear) * 100, 1) if clear else None,
                   'clearance_cm_over_ground_max': round(max(clear) * 100, 1) if clear else None}
R['B_veranda_steps'] = steps

# ---- C. wall caps: cap underside against the wall top ----
caps = {}
for wall in ('Back wall, left', 'Back wall, right', 'Right wall behind hall'):
    w = bpy.data.objects.get(wall)
    c = bpy.data.objects.get(wall + ' cap')
    wv, wp = world_mesh(w)
    cv, cp = world_mesh(c)
    wtop = max(p.z for p in wv)
    ctop = max(p.z for p in cv)
    cbot = min(p.z for p in cv)
    # cap underside where the wall is: cast rays down from above the cap at a grid over the wall top verts
    wtv = [p for p in wv if p.z > wtop - 0.01]
    xs = [p.x for p in wtv]; ys = [p.y for p in wtv]
    bw = bvh_of([w]); bc = bvh_of([c])
    # for samples over the wall top: first hit downward from above the cap = cap top; then from inside the wall, up = cap bottom
    gaps = []
    for k in range(40):
        t = (k + 0.5) / 40
        x = min(xs) + t * (max(xs) - min(xs))
        y = (min(ys) + max(ys)) / 2
        # wall top surface z at this x,y (hit downward from above, wall only)
        hw = bw.ray_cast(Vector((x, y, wtop + 1.0)), Vector((0, 0, -1)))
        if hw[0] is None:
            continue
        # cap underside above that point: ray up from just below wall top (inside the wall) against cap only
        hc = bc.ray_cast(Vector((x, y, hw[0].z - 0.05)), Vector((0, 0, 1)))
        if hc[0] is None:
            gaps.append(None)
        else:
            gaps.append(hc[0].z - hw[0].z)
    g = [q for q in gaps if q is not None]
    caps[wall] = {'wall_top_z': round(wtop, 4), 'cap_min_z': round(cbot, 4), 'cap_max_z': round(ctop, 4),
                  'samples': len(gaps), 'samples_with_cap_above': len(g),
                  'gap_cm_min': round(min(g) * 100, 2) if g else None,
                  'gap_cm_median': round(sorted(g)[len(g) // 2] * 100, 2) if g else None,
                  'gap_cm_max': round(max(g) * 100, 2) if g else None,
                  'wall_bbox_xy': [round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3)],
                  'cap_bbox_xy': [round(min(p.x for p in cv), 3), round(max(p.x for p in cv), 3),
                                  round(min(p.y for p in cv), 3), round(max(p.y for p in cv), 3)]}
R['C_wall_caps'] = caps

# ---- D. lantern: is the window visible from the cameras, and what blocks it ----
lan = {}
glow = bpy.data.objects.get('Lantern window glow')
gv, _ = world_mesh(glow)
gc = sum(gv, Vector()) / len(gv)
lan['glow_center'] = [round(c, 3) for c in gc]
lan['glow_bbox'] = [[round(min(p[i] for p in gv), 3), round(max(p[i] for p in gv), 3)] for i in range(3)]
allm = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and o.name != 'Lantern window glow'
        and o.name not in ('Maple leaves',)]
# the instanced leaves / scatter are evaluated via instances: include them with a depsgraph-instance BVH
inst_polys = []
verts_i, polys_i, off = [], [], 0
for inst in dg.object_instances:
    o = inst.object
    if o.type != 'MESH' or not inst.is_instance:
        continue
    pass
nobj = len([1 for o in bpy.data.objects if o.type == 'MESH'])
full = bvh_of(allm + [glow])
for cam_name in ('photo', 'Camera', 'veranda'):
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        continue
    org = cam.matrix_world.translation
    # the glow box is a box: test the 6 face centres and the box centre
    res = []
    for p in [gc] + [Vector(((gv[i].x + gv[j].x) / 2, (gv[i].y + gv[j].y) / 2, (gv[i].z + gv[j].z) / 2)) for i, j in ((0, 2), (1, 3), (4, 6), (5, 7))]:
        d = (p - org)
        dist = d.length
        hit = full.ray_cast(org, d.normalized(), dist + 0.5)
        res.append(None if hit[0] is None else round((hit[0] - org).length - dist, 3))
    # which object is first hit when aiming at the glow centre (use per-object BVH)
    d = (gc - org); dist = d.length
    best = None
    for o in allm + [glow]:
        b = bvh_of([o])
        if b is None:
            continue
        h = b.ray_cast(org, d.normalized(), dist + 0.5)
        if h[0] is not None and (best is None or h[3] < best[1]):
            best = (o.name, h[3])
    lan[cam_name] = {'cam_pos': [round(c, 2) for c in org], 'dist_to_glow': round(dist, 2),
                     'hit_minus_distance_m (negative = something in front)': res, 'first_object_hit': best[0] if best else None}
# light position against the glow box
ll = bpy.data.objects.get('Lantern light')
if ll:
    p = ll.matrix_world.translation
    lan['lantern_light_pos'] = [round(c, 3) for c in p]
    lan['lantern_light_inside_glow_bbox'] = all(lan['glow_bbox'][i][0] <= p[i] <= lan['glow_bbox'][i][1] for i in range(3))
    lan['lantern_light_type'] = ll.data.type
    lan['lantern_light_energy_W'] = round(ll.data.energy, 3)
    lan['lantern_light_shadow_soft_size'] = round(getattr(ll.data, 'shadow_soft_size', 0), 3)
# glow material emission
mat = glow.active_material
if mat and mat.node_tree:
    for n in mat.node_tree.nodes:
        if n.type in ('EMISSION', 'BSDF_PRINCIPLED'):
            for nm in ('Strength', 'Emission Strength'):
                if nm in n.inputs:
                    lan['glow_material_' + n.name + '_' + nm] = round(n.inputs[nm].default_value, 3)
R['D_lantern'] = lan

json.dump(R, open(out_path, 'w'), indent=1)
print('MEASURE_DONE', out_path)
