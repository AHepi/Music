# What this does (plain words): scores the real-geometry route (outputs/geometry_route) three ways against the slate reference, to compare it honestly with the
# flat painter route: (1) as photographed (height = true geometry, normal = slope of that height), (2) with the geometry's own true normal, (3) a hybrid:
# half true height, half "brightness of the colour" height (the way the reference was made), normal from the hybrid. Plain Python.
import json, os, shutil, subprocess, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SLATE = os.path.abspath(os.path.join(HERE, '..'))
src = os.path.join(SLATE, 'outputs', 'geometry_route')
variants = {}
def prep(name):
    folder = os.path.join(SLATE, 'outputs', name); os.makedirs(folder, exist_ok=True)
    shutil.copy(os.path.join(src, 'colour.png'), os.path.join(folder, 'colour.png'))
    return folder
h = cv2.imread(os.path.join(src, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64); h = (h[..., 0] if h.ndim == 3 else h) / 65535.0
colour = cv2.imread(os.path.join(src, 'colour.png'))
grey = cv2.cvtColor(colour, cv2.COLOR_BGR2GRAY).astype(np.float64)
h_colour = np.clip((grey - 9.5) / 102.0, 0, 1)
def normal_from(height, strength=7):
    h8 = np.round(height * 255)
    hx = (np.roll(h8, -1, 1) - np.roll(h8, 1, 1)) / 2; hy = (np.roll(h8, -1, 0) - np.roll(h8, 1, 0)) / 2
    nx, ny, nz = -strength * hx / 255, strength * hy / 255, np.ones_like(h8); L = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return (np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5)[..., ::-1]
# 1 as photographed
f = prep('geometry_route_plain'); shutil.copy(os.path.join(src, 'height.png'), os.path.join(f, 'height.png')); shutil.copy(os.path.join(src, 'normal.png'), os.path.join(f, 'normal.png'))
# 2 true normal
f = prep('geometry_route_true_normal'); shutil.copy(os.path.join(src, 'height.png'), os.path.join(f, 'height.png')); shutil.copy(os.path.join(src, 'normal_geometry.png'), os.path.join(f, 'normal.png'))
# 3 hybrid
f = prep('geometry_route_hybrid')
hb = 0.5 * (h - h.min()) / (h.max() - h.min()) + 0.5 * h_colour
cv2.imwrite(os.path.join(f, 'height.png'), (np.clip(hb, 0, 1) * 65535).astype(np.uint16))
cv2.imwrite(os.path.join(f, 'normal.png'), (np.clip(normal_from(hb), 0, 1) * 255).round().astype(np.uint8))
# 4 colour-derived height from the geometry colour (the derivation the reference used) - shows what the geometry COLOUR alone would give
f = prep('geometry_route_colour_derived')
cv2.imwrite(os.path.join(f, 'height.png'), (h_colour * 65535).astype(np.uint16)); cv2.imwrite(os.path.join(f, 'normal.png'), (np.clip(normal_from(h_colour), 0, 1) * 255).round().astype(np.uint8))
out = {}
for name in ('geometry_route_plain', 'geometry_route_true_normal', 'geometry_route_hybrid', 'geometry_route_colour_derived'):
    r = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'score_folder.py'), os.path.join(SLATE, 'outputs', name), name], capture_output=True, text=True)
    s = json.loads(r.stdout.strip().splitlines()[-1]); out[name] = s
    print(name, s['pixel']['tier_reached'], s['pixel']['colour_ssim'], s['pixel']['colour_mean_delta_e'], s['pixel']['edge_skill_2px'], s['pixel']['height_mae_best_fit_levels'], s['pixel']['normal_mean_angle_degrees'], s['texture_as_baked']['overall'], s['texture_view']['overall'], flush=True)
info = json.load(open(os.path.join(src, 'photo.json')))
out['photo'] = info
json.dump(out, open(os.path.join(SLATE, 'scores', 'geometry_route_summary.json'), 'w'), indent=1)
