"""What this does: places our real props at chosen spots and reports where they land in a 1536 x 2752 frame (log 30 rebuild plan).
A helper wrote it during the log 30 critique; it is a calculation on paper, not a render."""
# Place our real props (true sizes from props/index.json) and check where they land in a 1536x2752 frame.
import math, sys, json
import numpy as np
sys.path.insert(0, '.')
from solve import camera, project, ray_to_ground, street_vp, pave_z, road_z, ground_z, W, H

def box_corners(cx, cy, w, d, h, turn_deg, z0, s=1.0):
    t = math.radians(turn_deg); w, d, h = w * s, d * s, h * s
    pts = []
    for sx in (-0.5, 0.5):
        for sy in (-0.5, 0.5):
            x = cx + (sx * w) * math.cos(t) - (sy * d) * math.sin(t)
            y = cy + (sx * w) * math.sin(t) + (sy * d) * math.cos(t)
            for z in (z0, z0 + h):
                pts.append((x, y, z))
    return pts

def screen_box(cam, pts):
    uv = [project(cam, p) for p in pts]
    us = [a[0] for a in uv]; vs = [a[1] for a in uv]; zs = [a[2] for a in uv]
    return min(us), max(us), min(vs), max(vs), sum(zs) / len(zs)

def report(cam, name, pts, target=None):
    u0, u1, v0, v1, z = screen_box(cam, pts)
    area = (u1 - u0) * (v1 - v0) * 100
    line = f'{name:16s} x {u0:.3f}-{u1:.3f}  y {v0:.3f}-{v1:.3f}  centre ({(u0+u1)/2:.3f},{(v0+v1)/2:.3f})  box {area:.2f}%  depth {z:.1f} m'
    if target:
        line += f'   | AI: x {target[0]:.3f}-{target[1]:.3f} y {target[2]:.3f}-{target[3]:.3f} box {(target[1]-target[0])*(target[3]-target[2])*100:.2f}%'
    print(line)

if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1]))
    c = cfg['camera']
    cam = camera(c['x'], c['y'], c['eye_above_own_pavement'], c['yaw_left_deg'], c['vfov_deg'])
    print('camera eye z', round(cam['c'][2], 3), 'street lines meet at', [round(a, 3) for a in street_vp(cam)])
    for p in cfg['props']:
        z0 = ground_z(p['x'], p['y']) + p.get('lift', 0.0)
        pts = box_corners(p['x'], p['y'], p['w'], p['d'], p['h'], p.get('turn', 0), z0, p.get('scale', 1.0))
        report(cam, p['name'], pts, p.get('ai'))
    for k, pt in cfg.get('points', {}).items():
        u, v, z = project(cam, pt)
        print(f'{k:16s} at ({u:.3f}, {v:.3f}) depth {z:.1f}')
