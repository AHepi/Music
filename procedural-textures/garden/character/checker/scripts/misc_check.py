import bpy, json, sys, math
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from common import world_mesh
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/'
nodes = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]
def dseg(p, a, b):
    a = np.array(a); b = np.array(b)
    t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
    return np.linalg.norm(p - (a + t * (b - a)))
def snap():
    S = {}
    ob = bpy.data.objects['Life / pond bed']
    V, T, P = world_mesh(ob)
    S['bed'] = V
    for nm in [o.name for o in bpy.data.objects if o.name.startswith(('Rock ', 'Pond edge stone', 'Pine pads', 'Pine trunk', 'Shore stones', 'Stone plinth', 'Hall plaster', 'Lantern', 'Maple trunk'))]:
        o = bpy.data.objects[nm]
        if o.type == 'MESH':
            V, T, P = world_mesh(o)
            S[nm] = (V.min(axis=0), V.max(axis=0), len(V))
        else:
            S[nm] = (np.array(o.matrix_world.translation), np.array(o.matrix_world.translation), 0)
    return S
bpy.ops.wm.open_mainfile(filepath=G + 'direction/start/garden_real_fixed.blend'); A = snap()
bpy.ops.wm.open_mainfile(filepath=G + 'final/garden_character.blend'); B = snap()
R = {}
a, b = A['bed'], B['bed']
R['bed'] = {'nv_before': len(a), 'nv_after': len(b)}
if len(a) == len(b):
    d = np.linalg.norm(a - b, axis=1)
    dist = np.array([min(dseg(p[:2], x, y) for x, y in zip(nodes[:-1], nodes[1:])) for p in a])
    inside = dist < 1.2
    R['bed'].update({'n_inside_corridor': int(inside.sum()), 'max_move_inside_corridor_m': round(float(d[inside].max()), 4), 'n_moved_outside': int((d[~inside] > 1e-4).sum()), 'max_move_outside_m': round(float(d[~inside].max()), 4),
                     'z_before_min_max': [round(float(a[:, 2].min()), 3), round(float(a[:, 2].max()), 3)], 'z_after_min_max': [round(float(b[:, 2].min()), 3), round(float(b[:, 2].max()), 3)],
                     'bed_after_above_-0.44_count': int((b[:, 2] > -0.44).sum()), 'bed_before_above_-0.44_count': int((a[:, 2] > -0.44).sum())})
mv = {}
for nm in A:
    if nm == 'bed' or nm not in B: continue
    c0 = (A[nm][0] + A[nm][1]) / 2; c1 = (B[nm][0] + B[nm][1]) / 2
    mv[nm] = {'centre_move_m': round(float(np.linalg.norm(c1 - c0)), 3), 'size_before': [round(float(x), 2) for x in A[nm][1] - A[nm][0]], 'size_after': [round(float(x), 2) for x in B[nm][1] - B[nm][0]]}
R['moves'] = mv
json.dump(R, open(sys.argv[-1], 'w'), indent=1)
print('MISC', R['bed'])
