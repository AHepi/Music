# What this does: looks closer at what the skill's delivery gate flags in the street copy. It repeats the gate's own z-fighting test (using the gate's own helper functions)
# but records HOW FAR APART the two flagged faces really are, which two materials they wear, and where they are. It also lists the closed parts the gate calls inside-out
# and whether any material in the file hides back faces. Changes and saves nothing in the .blend.
# Run: blender -b --disable-autoexec --factory-startup STREET.blend --python probe_flags.py -- OUT.json
import sys, json, collections
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy, bx_audit
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene
excl = ('sky_dome', 'moorland_hills')
meshes = [o for o in sc.objects if o.type == 'MESH' and not o.name.startswith(excl)]
every = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
diag = (Vector([max(c[k] for c in every) for k in range(3)]) - Vector([min(c[k] for c in every) for k in range(3)])).length
weld = diag * 1e-6
EPS = 0.05   # look out to 5 cm, so we can see the whole spread of separations
parts, owner, mats_of = [], [], []
inward = []
for o in meshes:
    bm, double, b2b, zero = bx_audit._welded(o, True, weld)
    isl = bx_audit._islands(bm, 1.0)
    for i, p in enumerate(isl):
        if p['closed'] and p['volume'] < -(diag ** 3) * 1e-9:
            inward.append((o.name, [round(v, 2) for v in p['lo']], [round(v, 2) for v in p['hi']], p['faces'], round(p['volume'], 4)))
    parts += isl; owner += [o.name] * len(isl)
    bm.free()
coords, polys, face_part = [], [], []
for i, p in enumerate(parts):
    polys += [[k + len(coords) for k in poly] for poly in p['polys']]
    coords += p['coords']; face_part += [i] * p['faces']
tree = BVHTree.FromPolygons(coords, polys)
hits = collections.defaultdict(list)
for i, p in enumerate(parts):
    for c, nrm in zip(p['centers'], p['normals']):
        for loc, hn, idx, _ in tree.find_nearest_range(c, EPS):
            j = face_part[idx]; d = nrm.dot(hn); off = c - loc
            if j != i and abs(d) > 0.999 and (off - off.dot(hn) * hn).length < 1e-5:   # the gate's own rule: the face centre must land inside the other face (0.01 x the 1 mm run's eps)
                
                hits[(owner[i], owner[j], d > 0)].append((round(abs(off.dot(hn)), 6), tuple(round(v, 2) for v in c)))
# material of a face near a point, per object
trees = {}
def mat_at(name, wpt):
    o = bpy.data.objects[name]
    if name not in trees:
        trees[name] = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    loc, nrm, idx, dist = trees[name].find_nearest(o.matrix_world.inverted() @ Vector(wpt))
    if idx is None or not o.data.materials: return None
    mi = o.data.polygons[idx].material_index
    m = o.data.materials[mi] if mi < len(o.data.materials) else None
    return m.name if m else None
rows = []
for (a, b, same), lst in hits.items():
    ds = sorted(x[0] for x in lst)
    sample = lst[0]
    rows.append({'a': a, 'b': b, 'same_facing': same, 'faces': len(lst), 'sep_min_mm': round(ds[0] * 1000, 3), 'sep_median_mm': round(ds[len(ds) // 2] * 1000, 3), 'sep_max_mm': round(ds[-1] * 1000, 3),
                 'under_0.1mm': sum(1 for x in ds if x < 0.0001), 'under_1mm': sum(1 for x in ds if x < 0.001), 'under_5mm': sum(1 for x in ds if x < 0.005), 'under_5cm': len(ds),
                 'at': sample[1], 'mat_a': mat_at(a, sample[1]), 'mat_b': mat_at(b, sample[1])})
rows.sort(key=lambda r: -r['faces'])
culling = [m.name for m in bpy.data.materials if getattr(m, 'use_backface_culling', False)]
culling_shadow = [m.name for m in bpy.data.materials if getattr(m, 'use_backface_culling_shadow', False)]
res = {'diag_without_backdrop': round(diag, 1), 'pairs': rows, 'inward_parts': inward, 'materials_with_backface_culling': culling, 'materials_with_shadow_culling': culling_shadow, 'material_count': len(bpy.data.materials)}
json.dump(res, open(out, 'w'), indent=1)
print('PROBE pairs', len(rows), 'inward parts', len(inward), 'culling materials', culling, culling_shadow)
