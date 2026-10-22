import sys
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/wood'
sys.path.insert(0, HERE); sys.dont_write_bytecode = True
import bpy, numpy as np
import stage_wood
stage_wood.apply({})
o = bpy.data.objects['Astra / varied planks.004']
me = o.data
uv = np.array([l.uv[:] for l in me.uv_layers['UVMap'].data], dtype=np.float64)
for p in me.polygons:
    idx = list(range(p.loop_start, p.loop_start + p.loop_total))
    a = 0.0
    for i in range(len(idx)):
        x0, y0 = uv[idx[i]]; x1, y1 = uv[idx[(i + 1) % len(idx)]]
        a += x0 * y1 - x1 * y0
    if a < 1e-7:
        print('FACE', p.index, 'area', a, 'verts', len(idx), 'geom area', round(p.area, 9), 'mat', p.material_index, [tuple(round(c, 5) for c in uv[i]) for i in idx])
