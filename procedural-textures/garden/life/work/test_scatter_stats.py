# Where do the live-scatter instances really stand? (keep-clear path, gravel court, stones, water). Run: blender -b START.blend -P test_scatter_stats.py -- LOOK OUT.json
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
look, out = argv[0], argv[1]
HERE = 'proc-work/garden/life'
sys.path.insert(0, HERE)
import stage_life as SL
st = SL.Stage({'look': look}); SL._STAGE_REF['st'] = st
SL.apply({'look': look})
bpy.context.view_layer.update()
sc = SL.scene_context(st)
path = sc['path']
gx0, gy0, gx1, gy1 = sc['gravel']
dg = bpy.context.evaluated_depsgraph_get()
res = {'look': look, 'path_points': len(path), 'gravel_rect': [round(v, 2) for v in sc['gravel']]}
for ob in bpy.data.objects:
    if ob.get('astra_kind') != 'native_scatter' or ob.get('garden_owner') != 'life':
        continue
    gs = ob.evaluated_get(dg).evaluated_geometry()
    ipc = gs.instances_pointcloud()
    n = len(ipc.points)
    T = np.zeros((n, 16), dtype=np.float32)
    ipc.attributes['instance_transform'].data.foreach_get('value', T.ravel() if False else T.reshape(-1))
    M = T.reshape(n, 4, 4)
    P = M[:, 3, :3] if abs(M[0, 3, 3] - 1) < 1e-3 else M[:, :3, 3]      # translation (column-major or row-major)
    dpath = np.array([SL.dist_to_polyline(p[:2], path) for p in P]) if len(path) > 1 else np.zeros(n)
    in_gravel = [(gx0 - 0.0 < p[0] < gx1 and gy0 < p[1] < gy1) for p in P]
    below_water = [p[2] < SL.WATER_Z - 0.015 for p in P]
    res[ob.name] = {'instances': n, 'min_distance_to_stepping_path_m': round(float(dpath.min()), 3) if n else None,
                    'inside_gravel_court': int(sum(in_gravel)), 'below_waterline': int(sum(below_water)),
                    'z_range_m': [round(float(P[:, 2].min()), 3), round(float(P[:, 2].max()), 3)] if n else None}
json.dump(res, open(out, 'w'), indent=1)
for k, v in res.items():
    if isinstance(v, dict): print('SCATTER', k, v)
