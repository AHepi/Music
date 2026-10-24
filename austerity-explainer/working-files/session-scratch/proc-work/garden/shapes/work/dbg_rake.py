import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/shapes')
import bpy, numpy as np, stage_shapes as S
ctx = S.Ctx({'look': 'painted'}); S.step_gravel(ctx)
me = bpy.data.objects['Raked gravel court'].data
co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
nx, ny = 342, 325
Z = co[:,2].reshape(ny+1, nx+1); X = co[:,0].reshape(ny+1, nx+1); Y = co[:,1].reshape(ny+1, nx+1)
for j in (20, 60, 100, 140, 300):
    row = Z[j]; x = X[j]
    # local maxima
    pk = [i for i in range(1, nx) if row[i] > row[i-1] and row[i] >= row[i+1] and row[i] > 0.02 + 0.006]
    print('y=%.2f peaks at x:' % Y[j][0], [round(float(x[i]), 3) for i in pk[:10]], 'heights', [round(float(row[i]-0.02), 4) for i in pk[:10]])
