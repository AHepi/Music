import sys
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, ROOT + '/lib'); sys.path.insert(0, ROOT + '/modules')
import numpy as np
import ground_and_yard as g
plan = g.GroundPlan()
for p in plan.puddles:
    if p['kind'] == 'blob':
        cx, cy = p['spec']['centre']; r = max(p['spec']['size']) * 1.6 + 1.0
        x0, x1, y0, y1 = cx - r, cx + r, cy - r, cy + r
    else:
        xs, ys = p['samples'][:, 0], p['samples'][:, 1]; x0, x1, y0, y1 = xs.min() - 1.5, xs.max() + 1.5, ys.min() - 1.5, ys.max() + 1.5
    gx, gy = np.meshgrid(np.arange(x0, x1, 0.1), np.arange(y0, y1, 0.1)); gx, gy = gx.ravel(), gy.ravel()
    inside = plan.puddle_inside_depth(p, gx, gy)
    nat, _, _, slow = plan.ground_without_puddles(gx, gy)
    nat = plan._levelled(p, inside, nat, slow)
    sel = inside > 0
    ring = (inside < -0.3) & (inside > -1.0)
    print('%-26s level %.3f  inside natural min %.3f mean %.3f max %.3f | dig mean %.3f max %.3f | ring natural mean %.3f' % (
        p['name'], p['water_level'], nat[sel].min(), nat[sel].mean(), nat[sel].max(), nat[sel].mean() - p['water_level'] + 0.04, nat[sel].max() - p['water_level'] + 0.04, nat[ring].mean()))
