# Save world XY(Z) of puddle mesh vertices (and yard water) for puddle matching between passes. Read-only.
import bpy, sys, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
res = {}
for ob in bpy.data.objects:
    if ob.type == 'MESH' and (ob.name.startswith('puddles_') or ob.name.endswith('_water')):
        me = ob.data
        co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
        res[ob.name] = co.astype(np.float32)
        print('PUD', ob.name, len(co), [m.type for m in ob.modifiers])
np.savez_compressed(out, **res)
