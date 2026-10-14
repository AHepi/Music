"""What this does: checks where the props land during a straight camera push toward the notice (log 30).
A helper wrote it during the log 30 critique; it is a calculation on paper, not a render."""
import math, sys, json
import numpy as np
sys.path.insert(0, '.')
from solve import camera, project, street_vp, ground_z, pave_z
from layout import box_corners, screen_box
cfg = json.load(open(sys.argv[1]))
c = cfg['camera']
paper = [p for p in cfg['props'] if p['name'].startswith('paper')][0]
eye_z = pave_z(22.2) + 1.85
d = np.array([paper['x'] - c['x'], paper['y'] - c['y']]); d = d / np.linalg.norm(d)
for t in [float(a) for a in sys.argv[2:]]:
    x, y = c['x'] + d[0] * t, c['y'] + d[1] * t
    cam = camera(x, y, eye_z - pave_z(y), c['yaw_left_deg'], c['vfov_deg'])
    out = [f'move {t:+.1f} m -> cam ({x:.2f},{y:.2f})  lines meet {tuple(round(float(a),3) for a in street_vp(cam))}']
    for p in cfg['props']:
        if p['name'] in ('drum', 'chair', 'pail', 'lantern', 'paper', 'board'):
            z0 = ground_z(p['x'], p['y']) + p.get('lift', 0.0)
            u0, u1, v0, v1, z = screen_box(cam, box_corners(p['x'], p['y'], p['w'], p['d'], p['h'], p.get('turn', 0), z0, p.get('scale', 1.0)))
            out.append(f"   {p['name']:8s} x {u0:.3f}-{u1:.3f} y {v0:.3f}-{v1:.3f} box {(u1-u0)*(v1-v0)*100:.2f}%")
    print('\n'.join(out))
