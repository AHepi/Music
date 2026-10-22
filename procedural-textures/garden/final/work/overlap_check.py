# What this does: "a quick look for objects that now overlap" (plan section 12.2). Builds a world-space BVH of every real mesh object (modifiers applied, scatters,
# sky, hills and the big ground/gravel/water sheets left out) and lists pairs whose triangles actually cross. Read-only.
# Run: blender -b --disable-autoexec --factory-startup FILE.blend -P overlap_check.py -- OUT.json
import bpy, sys, json, itertools, time
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index('--') + 1]
SKIP = ('Hills,', 'Dark plain', 'Courtyard ground source', 'CT / Ceramic pan prototype', 'Maple leaf source', 'Life / moss sources', 'Life / pebble sources', 'Life / tuft sources', 'ROOF_')
SCATTER = {'Life / moss at feet and damp edges', 'Life / pebble fringe', 'Life / tufts', 'Maple leaves', 'Maple inner mass', 'Pine pads', 'Bamboo leaves', 'Fallen leaves', 'Lily pads',
           'Lotus blossoms', 'Astra / moss grouped bodies', 'Astra / pebbles grouped bodies', 'Bamboo stalks'}
BIG = {'Astra / Courtyard receiving ground', 'Raked gravel court', 'Pond water', 'Basin water', 'Life / pond bed'}
dg = bpy.context.evaluated_depsgraph_get()
items = []
t = time.time()
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH' or ob.hide_render or ob.name in SCATTER or ob.name in BIG or any(ob.name.startswith(p) for p in SKIP):
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    if len(me.polygons) == 0:
        ev.to_mesh_clear(); continue
    me.transform(ob.matrix_world)
    me.calc_loop_triangles()
    verts = [v.co.copy() for v in me.vertices]
    tris = [tuple(tr.vertices) for tr in me.loop_triangles]
    ev.to_mesh_clear()
    xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
    items.append((ob.name, BVHTree.FromPolygons(verts, tris, epsilon=0.0), (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)), ob.get('garden_owner'), len(tris)))
print('built', len(items), 'bvh in', round(time.time() - t, 1), 's', flush=True)
def box_hit(a, b):
    return not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2] or a[5] < b[4] or b[5] < a[4])
pairs = []
for (na, ba, xa, oa, ta), (nb, bb, xb, ob_, tb) in itertools.combinations(items, 2):
    if not box_hit(xa, xb):
        continue
    n = len(ba.overlap(bb))
    if n:
        pairs.append((n, na, nb, oa, ob_))
pairs.sort(reverse=True)
res = [{'tri_pairs': n, 'a': a, 'b': b, 'owner_a': oa, 'owner_b': ob_} for n, a, b, oa, ob_ in pairs]
json.dump(res, open(out, 'w'), indent=1)
print('OVERLAP_PAIRS', len(res))
for r in res[:40]:
    print('  ', r['tri_pairs'], r['a'], '<->', r['b'], r['owner_a'], r['owner_b'])
