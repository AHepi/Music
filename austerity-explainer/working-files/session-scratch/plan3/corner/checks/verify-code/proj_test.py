# compares check_shot.project() with Blender's own on-screen positions (lights, lines meeting) in each facts folder
import json, sys, math
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
import numpy as np
S = sys.argv[1]
for n in ['composed-end','a-camera-too-high','e-camera-tilted']:
    f = json.load(open(f'{S}/{n}/facts.json'))
    c = f['camera']; W, H = f['size']
    worst = 0
    for l in f['lights']:
        if l['on_screen'] is None: continue
        p, d = cs.project((*c['at'], c['turn_degrees'], c['vertical_fov_degrees']), l['at'], (W, H), c['tilt_degrees'], c['roll_degrees'])
        b = np.array(l['on_screen']) * [W, H]
        worst = max(worst, float(np.hypot(*(p - b))))
    # lines meet
    eye = np.array(c['at'])
    for name, dirn in {'street': [0,1,0.069927], 'level':[0,1,0]}.items():
        dvec = np.array(dirn)/np.linalg.norm(dirn)
        p, d = cs.project((*c['at'], c['turn_degrees'], c['vertical_fov_degrees']), eye + dvec*1e5, (W, H), c['tilt_degrees'], c['roll_degrees'])
        b = np.array(f['lines_meet'][name]) * [W, H]
        print(n, name, 'ours', p.round(1), 'blender', b.round(1))
    print(n, 'tilt', c['tilt_degrees'], 'roll', c['roll_degrees'], 'worst light mismatch px', round(worst, 2))
