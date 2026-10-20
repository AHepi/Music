# What this does (plain words): scores the real-geometry route (outputs/S_v4_geometry) against the gravel reference, to compare it honestly with the flat painter
# route (outputs/S_v4) made from the SAME description. Four sets: (1) "geometry alone" = flat block colours + true height of the blocks + normal from that height;
# (2) "painter alone" = the flat painter's colour, with height and normal derived from its colour (the way the reference was made); (3) "painter colour + geometry height":
# the painter's colour with the true block height and the normal from it; (4) "hybrid": the painter's colour with half true-geometry height, half colour-derived height.
# Plain Python (python3 -I). Writes outputs/geometry_compare_* and scores/geometry_route_summary.json.
import json, os, shutil, subprocess, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.abspath(os.path.join(HERE, '..'))
geo, painter = os.path.join(G, 'outputs', 'S_v4_geometry'), os.path.join(G, 'outputs', 'S_v4')
def load_h(path):
    h = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64); return (h[..., 0] if h.ndim == 3 else h) / 65535.0
def normal_from(height, strength=10):
    h8 = np.round(height * 255)
    hx = (np.roll(h8, -1, 1) - np.roll(h8, 1, 1)) / 2; hy = (np.roll(h8, -1, 0) - np.roll(h8, 1, 0)) / 2
    nx, ny, nz = -strength * hx / 255, strength * hy / 255, np.ones_like(h8); L = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return (np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5)[..., ::-1]
def make(name, colour_from, height, normal=None):
    f = os.path.join(G, 'outputs', name); os.makedirs(f, exist_ok=True)
    shutil.copy(os.path.join(colour_from, 'colour.png'), os.path.join(f, 'colour.png'))
    cv2.imwrite(os.path.join(f, 'height.png'), (np.clip(height, 0, 1) * 65535).astype(np.uint16))
    if normal is None:
        normal = normal_from(height)
    cv2.imwrite(os.path.join(f, 'normal.png'), (np.clip(normal, 0, 1) * 255).round().astype(np.uint8))
    return f
h_geo = load_h(os.path.join(geo, 'height.png'))
h_painter = load_h(os.path.join(painter, 'height.png'))
h_geo_matched = (h_geo - h_geo.mean()) / (h_geo.std() + 1e-9) * h_painter.std() + h_painter.mean()
sets = {'geometry_compare_geometry_alone': make('geometry_compare_geometry_alone', geo, h_geo),
        'geometry_compare_painter_alone': painter,
        'geometry_compare_painter_colour_geometry_height': make('geometry_compare_painter_colour_geometry_height', painter, h_geo_matched),
        'geometry_compare_hybrid': make('geometry_compare_hybrid', painter, 0.5 * h_painter + 0.5 * h_geo_matched)}
out = {}
for name, folder in sets.items():
    r = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'score_folder.py'), folder, name], capture_output=True, text=True)
    s = json.loads(r.stdout.strip().splitlines()[-1]); out[name] = s
    p = s['pixel']
    print(name, p['tier_reached'], 'ssim', round(p['colour_ssim'], 3), 'height_mae_fit', round(p['height_mae_best_fit_levels'], 1), 'normal_deg', round(p['normal_mean_angle_degrees'], 1), 'texture', s['texture_as_baked']['overall'], s['texture_view']['overall'], flush=True)
out['photo'] = json.load(open(os.path.join(geo, 'geometry_route.json')))
json.dump(out, open(os.path.join(G, 'scores', 'geometry_route_summary.json'), 'w'), indent=1)
