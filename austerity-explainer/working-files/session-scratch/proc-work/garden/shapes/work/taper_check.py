import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/shapes')
import bpy, numpy as np, stage_shapes as S
look = sys.argv[sys.argv.index('--')+1]
ctx = S.Ctx({'look': look})
orig = {}
import re
def widths(ob, g):
    p = S.world_points(ob)
    gz = g.z(float(p[:,0].mean()), float(p[:,1].mean()))
    zt = p[:,2].max(); vis = zt - gz
    def w(lo, hi):
        q = p[(p[:,2] >= lo) & (p[:,2] <= hi)]
        if len(q) < 3: return 0.0
        return float(np.hypot(np.ptp(q[:,0]), np.ptp(q[:,1])))
    base = w(gz, gz + 0.25*vis); top = w(zt - 0.25*vis, zt)
    return base, top, vis
names = [f'Rock {i}' for i in range(5)] + [f'Gravel rock {i}' for i in range(3)] + [f'Pond edge stone {i}' for i in range(15)]
def report(tag):
    bad = []
    for n in names:
        b, t, v = widths(bpy.data.objects[n], ctx.ground)
        bad.append((n, round(b,2), round(t,2), round(t/b if b else 0,2), round(v,2)))
    print(tag, 'rows (name, base width, top width, top/base, visible height):')
    for r in bad: print('   ', r)
report('BEFORE')
S.step_rocks(ctx)
report('AFTER')
