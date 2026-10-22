import sys, math, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof')
import bpy
import r_stones, r_moss
import json
cap = bpy.data.objects['Lantern cap']
bvh = r_stones.make_bvh(cap)
cx, cy = 0.95, 1.1
def pol(r, az):
    a = math.radians(az); return (cx + r*math.cos(a), cy + r*math.sin(a))
out = []
for k, (r_, az, R, asp, turn, th) in enumerate([(0.34, 197.5, 0.078, 0.92, 0.0, 0.034), (0.39, 317.5, 0.056, 0.92, 0.0, 0.028), (0.37, 197.5, 0.10, 0.72, 0.0, 0.034)]):
    rng = np.random.default_rng(5 + k)
    me = r_moss.cushion_mesh(lambda x, y: r_stones.surface_hit(bvh, x, y), pol(r_, az), R, th, rng, 'dbg', aspect=asp, angle=math.radians(az + turn), S=36, lumps=2, max_dz=0.10, min_nz=0.45, uv_tile=0.3, wobble=0.25)
    co = np.array([v.co[:] for v in me.vertices])
    S = 36
    rim = co[-S:]            # last ring = outline
    print(k, 'verts', len(co), 'rim x-range', rim[:,0].min(), rim[:,0].max(), 'y-range', rim[:,1].min(), rim[:,1].max(), 'rim z range', rim[:,2].min(), rim[:,2].max())
    ctr = np.array(pol(r_, az))
    out.append({'rim': [[float(p[0]-ctr[0]), float(p[1]-ctr[1]), float(p[2])] for p in rim], 'all': [[float(p[0]-ctr[0]), float(p[1]-ctr[1]), float(p[2])] for p in co]})
json.dump(out, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof/out/padshape.json','w'))
