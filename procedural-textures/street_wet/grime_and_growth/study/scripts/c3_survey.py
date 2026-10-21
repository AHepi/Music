# What this does (plain words): STUDY ONLY, saves nothing. Opens the saved Japanese courtyard scene and, for each FAMILY of things (all the stepping
# stones, all the plaster walls ...), lists: how many objects, faces, size, how much surface looks up / sideways / down, which materials (including the
# materials a geometry-nodes object hands out, like the roof), whether they carry a vertex colour, and what the main camera sees of each (one ray per dot of a 120 x 80 grid).
# Run: blender -b --disable-autoexec FILE --python c3_survey.py -- OUT.json
import json, math, re, sys
from collections import Counter, defaultdict
import bpy
import numpy as np
from mathutils import Vector

out_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()

RULES = [  # (family, regex on object name)
    ('ground: add-on earth and moss ground', r'^Astra / Courtyard receiving ground$'),
    ('add-on moss clumps (real geometry)', r'^Astra / moss grouped bodies$'),
    ('add-on pebbles (real geometry)', r'^Astra / pebbles grouped bodies$'),
    ('raked gravel court', r'^Raked gravel court$'),
    ('water: pond and basin', r'^(Pond water|Basin water)$'),
    ('wood: veranda deck planks (add-on)', r'^Astra / varied planks(\.00[0-2])?$'),
    ('wood: bridge planks (add-on)', r'^Astra / varied planks\.00[3-7]$'),
    ('wood: posts, beams, soffit, shoji lattice', r'^(Hall posts|Hall beams|Eave soffit|Shoji bars)$'),
    ('paper: shoji screens and open room (glow)', r'^(Shoji paper|Open room back)$'),
    ('plaster: hall walls and garden walls', r'^(Hall plaster|Back wall, (left|right)|Right wall behind hall)$'),
    ('wall cap tiles', r'^(Back wall, (left|right)|Right wall behind hall) cap$'),
    ('roof: ceramic tiles (geometry nodes)', r'^Hall roof$'),
    ('stone: hall plinth and lantern finial (simple material)', r'^(Stone plinth|Lantern finial)$'),
    ('stone: stepping stones (add-on)', r'^Stepping stone \d+$'),
    ('stone: veranda steps (add-on)', r'^Veranda step'),
    ('stone: pond edge stones (add-on)', r'^Pond edge stone \d+$'),
    ('stone: rock group and gravel rocks (add-on)', r'^(Rock \d+|Gravel rock \d+)$'),
    ('stone: lantern body (add-on)', r'^Lantern (base|post|gallery|firebox|cap)$'),
    ('stone: water basin (add-on)', r'^Water basin$'),
    ('stone: bridge piers (add-on)', r'^Bridge pier \d+$'),
    ('glow: lantern window', r'^Lantern window glow$'),
    ('bamboo: fence, stalks, leaves', r'^Bamboo'),
    ('trees: bark (trunks and limbs)', r'^(Maple|Pine) (trunk|branch|limb)'),
    ('trees: leaf masses', r'^(Maple leaves|Maple inner mass|Pine pads)$'),
    ('pond plants: lily pads and lotus', r'^(Lily pads|Lotus blossoms)$'),
    ('fallen leaves', r'^Fallen leaves$'),
    ('backdrop: hills and plain', r'^(Hills,|Dark plain)'),
    ('hidden: ground source and prototypes', r'^(Courtyard ground source|CT / )'),
]
def family(name):
    for f, rx in RULES:
        if re.match(rx, name):
            return f
    return 'UNSORTED ' + name

def poly_arrays(me, mw):
    n = len(me.polygons)
    nor = np.empty(n * 3); me.polygons.foreach_get('normal', nor); nor = nor.reshape(-1, 3) @ mw[:3, :3].T
    nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-9)
    ar = np.empty(n); me.polygons.foreach_get('area', ar); ar = ar * abs(np.linalg.det(mw[:3, :3])) ** (2 / 3)
    mi = np.empty(n, np.int32); me.polygons.foreach_get('material_index', mi)
    return nor, ar, mi

fam = defaultdict(lambda: dict(objects=[], faces=0, verts=0, area=0.0, up=0.0, side=0.0, down=0.0, mats=Counter(), lo=np.full(3, 1e9), hi=np.full(3, -1e9),
                               vcol=False, uv=False, ctrest=False, mods=Counter(), dims=[], hidden=0, base_faces=0))
for ob in scene.objects:
    if ob.type not in ('MESH', 'CURVE'):
        continue
    f = fam[family(ob.name)]
    f['objects'].append(ob.name)
    f['hidden'] += 1 if ob.hide_render else 0
    for m in ob.modifiers:
        f['mods'][m.type + ':' + m.name] += 1
    ev = ob.evaluated_get(deps)
    me = ev.to_mesh()
    mw = np.array(ob.matrix_world)
    nv, nf = len(me.vertices), len(me.polygons)
    if ob.type == 'MESH': f['base_faces'] += len(ob.data.polygons)
    f['verts'] += nv; f['faces'] += nf
    if nf:
        nor, ar, mi = poly_arrays(me, mw)
        f['area'] += ar.sum(); f['up'] += ar[nor[:, 2] > 0.7].sum(); f['down'] += ar[nor[:, 2] < -0.7].sum(); f['side'] += ar[np.abs(nor[:, 2]) <= 0.7].sum()
        mats = list(me.materials)
        for k in np.unique(mi):
            mm = mats[k] if k < len(mats) and mats[k] else None
            f['mats'][mm.name if mm else None] += int((mi == k).sum())
        co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        f['lo'] = np.minimum(f['lo'], co.min(0)); f['hi'] = np.maximum(f['hi'], co.max(0))
        f['dims'].append((co.max(0) - co.min(0)).tolist())
        f['vcol'] |= len(me.color_attributes) > 0
        f['uv'] |= len(me.uv_layers) > 0
        f['ctrest'] |= 'CT_rest' in me.attributes
    ev.to_mesh_clear()

# ---- what the main camera sees, one ray per dot
cam = scene.camera
W, H = 120, 80
tan_h = math.tan(cam.data.angle_x / 2); tan_v = tan_h * (H / W)
origin = cam.matrix_world.translation; rot = cam.matrix_world.to_quaternion()
seen_f, seen_m, sky = Counter(), Counter(), 0
seen_fm = defaultdict(Counter)
for j in range(H):
    for i in range(W):
        sx = ((i + 0.5) / W * 2 - 1) * tan_h; sy = (1 - (j + 0.5) / H * 2) * tan_v
        d = rot @ Vector((sx, sy, -1.0)).normalized()
        hit, loc, nor, idx, ob, mtx = scene.ray_cast(deps, origin, d)
        if not hit:
            sky += 1; continue
        ev = ob.evaluated_get(deps)
        mname = None
        try:
            me = ev.data
            mi = me.polygons[idx].material_index if ob.type == 'MESH' and idx < len(me.polygons) else 0
            mats = list(me.materials)
            mname = mats[mi].name if mi < len(mats) and mats[mi] else None
        except Exception:
            pass
        fm = family(ob.name)
        seen_f[fm] += 1; seen_m[mname] += 1; seen_fm[fm][mname] += 1
tot = W * H

res = {'file': bpy.data.filepath, 'camera': {'name': cam.name, 'loc': [round(v, 3) for v in cam.matrix_world.translation], 'fov_h_deg': round(math.degrees(cam.data.angle_x), 1)},
       'families': {}, 'view_share': {k: round(v / tot, 4) for k, v in seen_f.most_common()}, 'view_sky': round(sky / tot, 4), 'view_grid': [W, H]}
for k, f in sorted(fam.items()):
    dims = np.array(f['dims']) if f['dims'] else np.zeros((1, 3))
    res['families'][k] = dict(count=len(f['objects']), first=f['objects'][0], last=f['objects'][-1], base_faces=f['base_faces'], faces=f['faces'], verts=f['verts'],
                              area_m2=round(f['area'], 2), up_m2=round(f['up'], 2), side_m2=round(f['side'], 2), down_m2=round(f['down'], 2),
                              materials=dict(f['mats'].most_common(12)), n_materials=len(f['mats']), vertex_colour=bool(f['vcol']), uv=bool(f['uv']), has_CT_rest=bool(f['ctrest']),
                              modifiers=dict(f['mods']), hidden_in_render=f['hidden'],
                              bbox_lo=[round(float(v), 2) for v in f['lo']], bbox_hi=[round(float(v), 2) for v in f['hi']],
                              dims_min=[round(float(v), 2) for v in dims.min(0)], dims_median=[round(float(v), 2) for v in np.median(dims, 0)], dims_max=[round(float(v), 2) for v in dims.max(0)],
                              seen_materials={str(a): round(b / tot, 4) for a, b in seen_fm[k].most_common(6)} if k in seen_fm else {})
json.dump(res, open(out_path, 'w'), indent=1, default=str)
print('SURVEY DONE', len(res['families']), 'families')
