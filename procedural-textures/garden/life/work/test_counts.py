# Face counts of the whole scene, with instances counted as the render sees them. Run: blender -b START.blend -P test_counts.py -- LOOK|none OUT.json
import bpy, sys, json, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
look, out = argv[0], argv[1]
HERE = 'proc-work/garden/life'
sys.path.insert(0, HERE)
if look != 'none':
    import stage_life
    stage_life.apply({'look': look})
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
rows = {}
def ref_faces(ref):
    try:
        if isinstance(ref, bpy.types.Object):
            return len(ref.data.polygons) if ref.type == 'MESH' else 0
        if isinstance(ref, bpy.types.Collection):
            return sum(len(o.data.polygons) for o in ref.all_objects if o.type == 'MESH')
        return len(ref.mesh.polygons) if ref.mesh is not None else 0
    except Exception:
        return 0
for ob in bpy.context.scene.objects:
    if ob.type not in ('MESH', 'CURVE') or ob.hide_render:
        continue
    ev = ob.evaluated_get(dg)
    gs = ev.evaluated_geometry()
    unique = 0; inst = 0
    if gs.mesh is not None:
        unique += len(gs.mesh.polygons)
    if gs.curves is not None:
        unique += 0
    ipc = gs.instances_pointcloud()
    if ipc is not None and len(ipc.points):
        refs = gs.instance_references()
        rf = [ref_faces(r) for r in refs]
        idx = np.zeros(len(ipc.points), dtype=np.int32)
        if '.reference_index' in ipc.attributes:
            ipc.attributes['.reference_index'].data.foreach_get('value', idx)
        inst = int(sum(rf[i] for i in idx if i < len(rf)))
    if ob.type == 'CURVE':
        try:
            m = ev.to_mesh(); unique = len(m.polygons); ev.to_mesh_clear()
        except Exception:
            pass
    rows[ob.name] = (unique, inst)
tot_u = sum(v[0] for v in rows.values()); tot_i = sum(v[1] for v in rows.values())
top = sorted(rows.items(), key=lambda kv: -(kv[1][0] + kv[1][1]))[:14]
res = {'look': look, 'objects': len(rows), 'faces_in_meshes': tot_u, 'faces_from_instances': tot_i, 'total_as_rendered': tot_u + tot_i, 'top': top}
json.dump(res, open(out, 'w'), indent=1)
print('COUNTS', json.dumps({k: v for k, v in res.items() if k != 'top'}))
for n, (u, i) in top: print('   ', n, u, i)
