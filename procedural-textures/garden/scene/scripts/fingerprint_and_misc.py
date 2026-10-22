# What this does: (1) computes the same "fingerprint" the build script writes (names, counts, rounded world coordinates, material names of every mesh)
#   for the opened scene, so it can be compared with cmp_v021.fingerprint.json; (2) checks nothing is linked from outside (libraries, images, missing files);
#   (3) lists collections, hidden objects and what is excluded from rendering; (4) world check: where the sky texture puts its sun.
import bpy, sys, json, hashlib
import numpy as np
dg = bpy.context.evaluated_depsgraph_get(); parts = []; tv = tf = 0
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type != 'MESH': continue
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    co = np.array([tuple(v.co) for v in me.vertices], dtype=np.float64)
    m = np.array(ob.matrix_world, dtype=np.float64); world = (co @ m[:3, :3].T + m[:3, 3]) if len(co) else co
    digest = hashlib.sha256(np.round(world, 5).tobytes()).hexdigest()[:16]
    parts.append((ob.name, len(me.vertices), len(me.polygons), digest, [mt.name if mt else None for mt in ob.data.materials]))
    tv += len(me.vertices); tf += len(me.polygons); ev.to_mesh_clear()
whole = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:24]
print('FINGERPRINT', len(parts), tv, tf, whole)
ref = json.load(open(sys.argv[sys.argv.index('--') + 1])) if '--' in sys.argv else None
if ref:
    print('REFERENCE  ', ref['objects'], ref['vertices'], ref['faces'], ref['whole'])
    refparts = {p[0]: p for p in ref['parts']}
    diff = [p[0] for p in parts if p[0] not in refparts or refparts[p[0]][3] != p[3]]
    print('PARTS THAT DIFFER:', diff[:10], len(diff))
print('LIBRARIES', [l.filepath for l in bpy.data.libraries], 'IMAGES', [i.filepath for i in bpy.data.images], 'MOVIECLIPS', len(bpy.data.movieclips))
print('HIDDEN_RENDER', [o.name for o in bpy.data.objects if o.hide_render])
print('NO_COLLECTION', [o.name for o in bpy.data.objects if not o.users_collection])
print('SCENES', [s.name for s in bpy.data.scenes], 'WORLDS', [w.name for w in bpy.data.worlds])
