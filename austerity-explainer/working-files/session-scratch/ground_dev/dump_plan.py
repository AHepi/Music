# dev helper: writes the plan (ruts, puddles, heaps, props, track) to plan.json so a picture of the layout can be drawn
import sys, os, json, math
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, ROOT + '/lib'); sys.path.insert(0, ROOT + '/modules')
import numpy as np
import ground_and_yard as g
import mine_common as mc
plan = g.GroundPlan()
out = {'ruts': [l['xy'][::5].tolist() for l in plan.rut_lines],
       'rut_names': [l['road'] + str(l['side']) for l in plan.rut_lines],
       'track': plan.track_samples[::10].tolist(),
       'heaps': [list(h[:4]) for h in g.COAL_HEAPS], 'mounds': [list(m) for m in g.EARTH_MOUNDS],
       'buildings': [list(b) for b in g.BUILDING_FOOTPRINTS],
       'barrels': g.BARREL_SPOTS, 'lamp': g.LAMP_POSITION, 'rack': g.TIMBER_RACK, 'cart': g.HANDCART, 'sleepers': g.SLEEPER_PILE,
       'fence': g.FENCE_LINE, 'puddles': []}
for p in plan.puddles:
    xs = np.linspace(-20, 22, 840); ys = np.linspace(-32, 14, 920)
    gx, gy = np.meshgrid(xs[::2], ys[::2])
    ins = plan.puddle_inside_depth(p, gx.ravel(), gy.ravel()).reshape(gx.shape) > -0.05
    pts = np.stack([gx[ins], gy[ins]], 1)
    out['puddles'].append({'name': p['name'], 'pts': pts.tolist(), 'level': p['water_level']})
json.dump(out, open('plan.json', 'w'))
print('ok')
