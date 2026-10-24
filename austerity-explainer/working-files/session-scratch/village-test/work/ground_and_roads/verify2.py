import sys, json, math
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from place_kit import parts, scene_read
base = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
out = {}
ground = [o for o in bpy.data.objects if o.type == 'MESH' and (o.get('place_role') or '').startswith('ground.')]
back = [o for o in bpy.data.objects if o.type == 'MESH' and o.get('place_role') == 'backdrop']
def boundary_vertices(o):
    m = o.data
    loops = np.empty(len(m.loops), dtype=np.int64); m.loops.foreach_get('edge_index', loops)
    uses = np.bincount(loops, minlength=len(m.edges))
    ev = np.empty(len(m.edges) * 2, dtype=np.int64); m.edges.foreach_get('vertices', ev); ev = ev.reshape(-1, 2)
    bv = np.unique(ev[uses == 1].ravel())
    co = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world)
    return (co[bv].astype(np.float64) @ mw[:3, :3].T + mw[:3, 3])
def key(p): return set(map(tuple, np.round(p, 5)))
bnd = {o.name: boundary_vertices(o) for o in ground}
allkeys = {n: key(p) for n, p in bnd.items()}
out['boundary'] = {}
for n, p in bnd.items():
    others = set().union(*[k for m, k in allkeys.items() if m != n])
    # the floor's round edge is shared with the backdrop skirt
    back_keys = set().union(*[key(boundary_vertices(b)) for b in back])
    unmatched = [t for t in map(tuple, np.round(p, 5)) if t not in others and t not in back_keys]
    out['boundary'][n] = {'boundary_vertices': len(p), 'not_shared_with_any_other_object': len(unmatched), 'examples': [list(u) for u in unmatched[:3]]}
trees = {}
for o in ground:
    v, t = parts.world_triangles(o)
    trees[o.name] = BVHTree.FromPolygons([tuple(x) for x in v], [tuple(x) for x in t], epsilon=0.0)
rng = np.random.default_rng(9)
r = np.sqrt(rng.uniform(0, 189.0 ** 2, 8000)); a = rng.uniform(0, 2 * math.pi, 8000)
pts = np.column_stack([r * np.cos(a), r * np.sin(a)])
village = rng.uniform(-70, 70, (4000, 2))
gaps = multi = 0
for x, y in np.concatenate([pts, village]):
    hits = [n for n, tr in trees.items() if tr.ray_cast(Vector((float(x), float(y), 100.0)), Vector((0, 0, -1)))[0] is not None]
    gaps += len(hits) == 0; multi += len(hits) > 1
out['random_points_in_disc'] = 12000; out['gaps'] = int(gaps); out['multi_hits'] = int(multi)
# the floor meets the skirt: heights on the edge ring
fl = bpy.data.objects['Ground forest floor']; v, t = parts.world_triangles(fl)
out['floor_bbox'] = [round(float(x), 2) for x in list(v.min(0)) + list(v.max(0))]
out['ground_area_m2'] = round(sum(0.5 * np.abs(np.cross(*(lambda vt: (vt[0][vt[1][:, 1]] - vt[0][vt[1][:, 0]], vt[0][vt[1][:, 2]] - vt[0][vt[1][:, 0]]))(parts.world_triangles(o)))[:, 2]).sum() for o in ground))
out['triangles'] = {o.name: scene_read.triangle_count(o, True) for o in ground + back}
out['triangles_total'] = sum(out['triangles'].values())
out['objects_total'] = len(bpy.data.objects); out['meshes'] = len([o for o in bpy.data.objects if o.type == 'MESH'])
json.dump(out, open(base + '/work/ground_and_roads/verify2.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
