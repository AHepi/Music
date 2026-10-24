# Pinhole model of the pit-village street (Blender coords: x across, +right; y up the street; z up).
# For a candidate camera, cast rays through the AI picture's prop foot points onto the ground to find
# where each prop must stand, and project known set features to compare with the AI picture.
import math, sys
import numpy as np
W, H = 1536, 2752
T4 = math.tan(math.radians(4))
def pave_z(y): return min(y, 76) * T4 + 0.13
def road_z(y): return min(y, 76) * T4
def ground_z(x, y): return pave_z(y) if abs(x) >= 2.68 else road_z(y)

def camera(xc, yc, eye, yaw_deg, vfov_deg, pitch_deg=0.0):
    f = (H / 2) / math.tan(math.radians(vfov_deg) / 2)
    c = np.array([xc, yc, pave_z(yc) + eye])
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    fwd = np.array([-math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    right = np.array([math.cos(yaw), math.sin(yaw), 0.0])
    up = np.cross(right, fwd)
    return dict(f=f, c=c, fwd=fwd, right=right, up=up)

def project(cam, p):
    v = np.array(p, float) - cam['c']
    zc = v @ cam['fwd']
    return (W / 2 + cam['f'] * (v @ cam['right']) / zc) / W, (H / 2 - cam['f'] * (v @ cam['up']) / zc) / H, zc

def ray_to_ground(cam, u, v, on='auto'):
    px, py = u * W - W / 2, -(v * H - H / 2)
    d = cam['fwd'] * cam['f'] + cam['right'] * px + cam['up'] * py
    d = d / np.linalg.norm(d)
    # march to find ground hit
    t = 0.05
    while t < 200:
        p = cam['c'] + d * t
        if p[2] <= ground_z(p[0], p[1]):
            return p, (p - cam['c']) @ cam['fwd']
        t += 0.005
    return None, None

def street_vp(cam):
    d = np.array([0, 1, T4])
    return project(cam, cam['c'] + d * 1e6)[:2]

if __name__ == '__main__':
    xc, yc, eye, yaw, vfov = [float(a) for a in sys.argv[1:6]]
    cam = camera(xc, yc, eye, yaw, vfov)
    print('camera', cam['c'].round(3), 'f px', round(cam['f']), 'street VP', [round(a, 3) for a in street_vp(cam)])
    # kerb top inner edge (x=2.68) and outer (2.50) where they cross the bottom edge
    for kx in (2.50, 2.68, -2.5, 4.15):
        for yy in np.arange(yc + 0.5, yc + 60, 0.01):
            u, v, z = project(cam, (kx, yy, pave_z(yy)))
            if v <= 1.0:
                print(f'line x={kx} enters frame bottom at u={u:.3f} (y={yy:.2f})') if 0 <= u <= 1 else print(f'line x={kx} at bottom edge u={u:.3f} (off frame)')
                break
    feats = {
        'winding wheels centre (x0, y86, z~23.4)': (0.0, 86.0, 76 * T4 + 16 + 2.1),
        'gate centre (0, 71.5, 1.5 above)': (0.0, 71.5, road_z(71.5) + 1.5),
        'right lamp 1 head (3.03, 39)': (3.03, 39.0, pave_z(39) + 3.1),
        'left lamp 1 head (-3.03, 25)': (-3.03, 25.0, pave_z(25) + 3.1),
        'right lamp 0 head (3.03, 11)': (3.03, 11.0, pave_z(11) + 3.1),
        'chimney top (-9.5,108,~?)': (-9.5, 108.0, 76 * T4 + 30),
    }
    for k, p in feats.items():
        u, v, z = project(cam, p)
        print(f'{k}: u={u:.3f} v={v:.3f} dist={z:.1f}')
    # AI-picture foot points (fractions) -> ground positions
    feet = {
        'drum foot centre (0.594, 0.812)': (0.594, 0.812),
        'board left post foot (0.70, 0.79)': (0.700, 0.790),
        'board right post foot (0.965, 0.79)': (0.965, 0.790),
        'chair front-left foot (0.535+? ) (0.71, 0.853)': (0.712, 0.853),
        'chair front-right foot (0.79, 0.86)': (0.79, 0.858),
        'chair back-right foot (0.93, 0.80)': (0.93, 0.80),
        'pail foot centre (0.891, 0.875)': (0.891, 0.875),
        'barrel foot (0.661, 0.565)': (0.661, 0.565),
        'coal tub foot (0.542, 0.57)': (0.542, 0.57),
        'cart wheel foot (0.27, 0.565)': (0.27, 0.565),
        'sacks foot (0.07, 0.545)': (0.07, 0.545),
        'dustbins foot (0.414, 0.488)': (0.414, 0.488),
    }
    for k, (u, v) in feet.items():
        p, z = ray_to_ground(cam, u, v)
        if p is None: print(k, 'no hit'); continue
        s = cam['f'] / z
        print(f'{k}: x={p[0]:.2f} y={p[1]:.2f} z={p[2]:.2f} depth={z:.2f} m, scale {s:.0f} px/m = {s/W:.3f} frame-widths/m')
