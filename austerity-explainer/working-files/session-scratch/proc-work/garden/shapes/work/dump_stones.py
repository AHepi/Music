import sys, json, re
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/shapes')
import bpy, numpy as np
import stage_shapes as S
g = S.Ground()
out = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    if re.match(r'^(Rock|Gravel rock|Pond edge stone|Stepping stone|Veranda step|Bridge pier|Water basin|Lantern)', ob.name):
        p = S.world_points(ob)
        gz = g.z(p[:,0].mean(), p[:,1].mean())
        # ground under footprint (hull-ish: sample the vertices low on the stone)
        low = p[p[:,2] < p[:,2].min() + 0.25*(p[:,2].max()-p[:,2].min())]
        gzs = [g.z(x, y) for x, y in low[:, :2]]
        out[ob.name] = dict(zmin=float(p[:,2].min()), zmax=float(p[:,2].max()), cx=float(p[:,0].mean()), cy=float(p[:,1].mean()), ground_c=gz,
                            ground_min=min(gzs), ground_max=max(gzs), H=float(p[:,2].max()-p[:,2].min()),
                            buried_c=(gz-float(p[:,2].min()))/float(p[:,2].max()-p[:,2].min()),
                            xy=[[float(a), float(b)] for a, b in p[:, :2][::max(1, len(p)//60)]], ext=[float(p[:,0].max()-p[:,0].min()), float(p[:,1].max()-p[:,1].min())])
json.dump(out, open(sys.argv[sys.argv.index('--')+1], 'w'))
for k, v in sorted(out.items()):
    print(f"{k:24} z {v['zmin']:.2f}..{v['zmax']:.2f}  H {v['H']:.2f} ground c {v['ground_c']:.2f} min {v['ground_min']:.2f} max {v['ground_max']:.2f}  buried {v['buried_c']*100:.0f}%  at ({v['cx']:.2f},{v['cy']:.2f}) ext {v['ext'][0]:.2f}x{v['ext'][1]:.2f}")
