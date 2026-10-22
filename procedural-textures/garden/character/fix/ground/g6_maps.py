"""GROUND builder (22 October character round): makes the maps the ground materials need. Plain numpy + PIL (system python3 -I is fine).
Writes into maps/ next to this file:
  path_mask.png        2048x2048 RGB, top-down over the 22 x 21 m ground (x -11..11, y -8.5..12.5): R bare worn earth (0..1), G footfall dish (0..1), B pebble specks
  ground_normal.png    2048x2048 tangent normal (OpenGL), soft clods and dishes, tile = 3 m
  moss_normal.png      1024x1024 tangent normal, soft pillow cells, tile = 0.5 m (2 x 2 cells)
  pebble_normal.png    1024x1024 from a blurred clean_pebbles_disp_1k.jpg, soft
  stone_normal.png     1024x1024 from a blurred rock_08_disp_1k.jpg, soft, tile = 1 m
  *_height.png         the height pictures the normals were made from (small, for the test light)
Every map is deterministic (fixed seeds).  Run:  python3 -I g6_maps.py [--only name,name] [--size 2048]
"""
import os, sys, json
import numpy as np
try:
    from PIL import Image
except ImportError:          # inside Blender (no PIL): only the numpy parts are used
    Image = None

HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = os.path.join(HERE, 'maps')
SCANS = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/maps'
sys.path.insert(0, HERE)
from normal_tools import height_to_normal, to_rgb  # noqa: E402

GROUND_STRENGTH = 0.05
MOSS_STRENGTH = 0.14
PEBBLE_STRENGTH = 0.07
STONE_STRENGTH = 0.07
GX0, GX1, GY0, GY1 = -11.0, 11.0, -8.5, 12.5      # ground bounding box (measured)

# worn paths, world metres: (polyline, half width m)
PATHS = {
    # (a) from the last stepping stone to the veranda steps
    'steps': ([(2.00, 2.05), (2.12, 2.75), (2.22, 3.35), (2.25, 3.62)], 0.21),
    # (b) desire line from the east bridge end, round the kerb corner, to the first stepping stone
    'desire': ([(-0.45, -0.75), (-0.05, -1.45), (0.22, -2.35), (0.38, -3.45), (0.42, -4.55), (0.28, -5.55), (0.55, -6.45),
                (1.55, -6.85), (2.85, -6.75), (3.70, -6.45), (4.20, -5.95)], 0.27),
}
# patches (ellipses): centre x, y, radius a, radius b, angle degrees
PATCHES = [
    (-6.45, 2.45, 0.62, 0.48, 20.0),     # west bridge end
    (2.22, 3.42, 0.46, 0.32, 0.0),       # foot of the veranda steps
    (0.36, -3.30, 0.48, 0.38, 25.0),     # a wider worn spot on the desire line (the hero lower right)
]


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def fbm_periodic(n, wl_min, wl_max, beta=2.0, seed=0):
    """Tileable band-limited noise 0..1 (wavelengths in pixels)."""
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    k = np.sqrt(fx ** 2 + fy ** 2) + 1e-9
    amp = k ** (-beta / 2.0)
    amp *= np.exp(-(k * wl_min) ** 4)                 # remove wavelengths shorter than wl_min
    amp *= 1.0 - np.exp(-(k * wl_max) ** 2)           # remove wavelengths longer than wl_max
    amp[0, 0] = 0.0
    spec = amp * np.exp(2j * np.pi * rng.random((n, n)))
    a = np.fft.ifft2(spec).real
    lo, hi = np.percentile(a, 1.0), np.percentile(a, 99.0)
    return np.clip((a - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def blur_periodic(h, sigma_px):
    n0, n1 = h.shape
    fy = np.fft.fftfreq(n0)[:, None]
    fx = np.fft.fftfreq(n1)[None, :]
    g = np.exp(-2.0 * (np.pi * sigma_px) ** 2 * (fx ** 2 + fy ** 2))
    return np.fft.ifft2(np.fft.fft2(h) * g).real.astype(np.float32)


def save_rgb(path, rgb01):
    Image.fromarray((np.clip(rgb01, 0, 1) * 255.0 + 0.5).astype(np.uint8), 'RGB').save(path, optimize=True)


def save_gray(path, g01):
    Image.fromarray((np.clip(g01, 0, 1) * 255.0 + 0.5).astype(np.uint8), 'L').save(path, optimize=True)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
    cx, cy = ax + t * dx, ay + t * dy
    return np.sqrt((px - cx) ** 2 + (py - cy) ** 2), t


def make_path_mask(n=2048):
    """FIX ROUND: soft bare earth, no grass islands. R = how bare (0 grass .. 1 earth) with a gently wavy, soft edge; G = footfall dish; B = 0 (the
    pebbles are real little stones now, placed by the stage). The edge noise is a slow 15 to 70 cm wave, so the path reads as ONE soft shape, not as
    camouflage patches."""
    cols = (np.arange(n, dtype=np.float32) + 0.5) / n
    X = (GX0 + cols * (GX1 - GX0))[None, :].repeat(n, 0)
    Y = (GY0 + (1.0 - cols) * (GY1 - GY0))[:, None].repeat(n, 1)         # row 0 = top = +y
    inner = np.zeros((n, n), np.float32)                                  # 0..1 how deep inside a path
    e1 = fbm_periodic(n, 14, 70, 1.6, seed=11)     # 14-70 cm gentle edge wave
    e2 = fbm_periodic(n, 30, 160, 1.8, seed=12)    # 0.3 - 1.7 m wobble of the width
    for name, (pts, hw) in PATHS.items():
        d = np.full((n, n), 1e9, np.float32)
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dd, _ = seg_dist(X, Y, ax, ay, bx, by)
            d = np.minimum(d, dd)
        wob = hw * (0.92 + 0.30 * e2)
        edge = (e1 - 0.5) * 0.22
        v = wob + edge - d
        inner = np.maximum(inner, smoothstep(0.0, 0.30, v))
    for (cx, cy, ra, rb, ang) in PATCHES:
        c, s = np.cos(np.radians(ang)), np.sin(np.radians(ang))
        u = (X - cx) * c + (Y - cy) * s
        w = -(X - cx) * s + (Y - cy) * c
        r = np.sqrt((u / ra) ** 2 + (w / rb) ** 2)
        v = (1.0 - r) * min(ra, rb) * 0.9 + (e1 - 0.5) * 0.20 + (e2 - 0.5) * 0.20
        inner = np.maximum(inner, smoothstep(0.0, 0.30, v))
    bare = smoothstep(0.0, 0.60, inner)                                   # 0 on grass .. 1 deep in the path, one soft ramp (no grass islands)
    bare = np.clip(blur_periodic(bare, 1.5), 0, 1)
    dish = smoothstep(0.35, 1.0, inner) * (0.6 + 0.4 * fbm_periodic(n, 20, 120, 1.5, seed=14))
    specks = np.zeros_like(bare)
    rgb = np.stack([bare, dish, specks], axis=2)
    return rgb.astype(np.float32)


def make_ground_height(n=2048, tile_m=3.0):
    """soft clods (10-60 cm), footfall dishes and little dry crumbs (>= 1 cm at 1.5 mm/px). Nothing under 5 mm."""
    px = n / tile_m                                   # pixels per metre
    clods = fbm_periodic(n, 0.10 * px, 0.9 * px, 1.8, seed=21)          # 10 cm .. 90 cm
    crumbs = fbm_periodic(n, 0.025 * px, 0.10 * px, 1.0, seed=22)       # 2.5 .. 10 cm
    h = 0.70 * clods + 0.10 * crumbs
    h = blur_periodic(h, 0.004 * px)                                    # soften: nothing under about 5 mm
    return (h - h.min()) / (h.max() - h.min())


def voronoi_height(n, cells, seed, rounded=1.0):
    """periodic Voronoi 'pillow' height: each cell a soft dome, thin dark groove between cells (white = high)."""
    rng = np.random.default_rng(seed)
    P = rng.random((cells, cells, 2))
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32) / n * cells
    best = np.full((n, n), 9.0, np.float32)
    second = np.full((n, n), 9.0, np.float32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            for j in range(cells):
                for i in range(cells):
                    px_ = i + P[j, i, 0] + ox * cells
                    py_ = j + P[j, i, 1] + oy * cells
                    d = np.sqrt((xs - px_) ** 2 + (ys - py_) ** 2)
                    m = d < best
                    second = np.where(m, best, np.minimum(second, d))
                    best = np.where(m, d, best)
    edge = np.clip((second - best) * 2.0, 0.0, 1.0)            # 0 on the border between two cells, 1 well inside
    dome = np.sqrt(np.clip(1.0 - (best / 0.62) ** 2, 0.0, 1.0)) # round top
    h = (smoothstep(0.0, 0.55, edge) ** 0.8) * (0.55 + 0.45 * dome)
    return h.astype(np.float32)


def make_moss_height(n=1024):
    h = voronoi_height(n, 3, seed=31)
    h = blur_periodic(h, 0.028 * n)                      # pillows, not scales: soft rounded lumps
    lump = fbm_periodic(n, 0.12 * n, 0.5 * n, 1.4, seed=32)
    lump2 = fbm_periodic(n, 0.05 * n, 0.2 * n, 1.2, seed=33)
    h = (h - h.min()) / (h.max() - h.min())
    h = 0.20 * h + 0.55 * lump + 0.25 * lump2
    return (h - h.min()) / (h.max() - h.min())


def scan_height(name, blur_frac, n=1024):
    a = np.asarray(Image.open(os.path.join(SCANS, name)).convert('L').resize((n, n), Image.BICUBIC), dtype=np.float32) / 255.0
    a = (a - a.min()) / (a.max() - a.min() + 1e-6)
    a = blur_periodic(a, blur_frac * n)
    return (a - a.min()) / (a.max() - a.min())


def main(only=None, size=2048):
    os.makedirs(MAPS, exist_ok=True)
    only = set(only.split(',')) if only else None
    rep = {}

    def want(k):
        return only is None or k in only

    if want('path'):
        m = make_path_mask(size)
        save_rgb(os.path.join(MAPS, 'path_mask.png'), m)
        rep['path_mask'] = {'R_mean': float(m[..., 0].mean()), 'R_gt_half': float((m[..., 0] > 0.5).mean()), 'size': size,
                            'bare_area_m2': float((m[..., 0] > 0.5).mean() * 22 * 21)}
    if want('ground'):
        h = make_ground_height(size)
        save_gray(os.path.join(MAPS, 'ground_height.png'), h)
        save_rgb(os.path.join(MAPS, 'ground_normal.png'), to_rgb(height_to_normal(h, strength=GROUND_STRENGTH, tile=True)))
        rep['ground_normal'] = {'size': size}
    if want('moss'):
        h = make_moss_height(1024)
        save_gray(os.path.join(MAPS, 'moss_height.png'), h)
        save_rgb(os.path.join(MAPS, 'moss_normal.png'), to_rgb(height_to_normal(h, strength=MOSS_STRENGTH, tile=True)))
        rep['moss_normal'] = {'size': 1024}
    if want('pebble'):
        h = scan_height('clean_pebbles_disp_1k.jpg', 0.006)
        save_gray(os.path.join(MAPS, 'pebble_height.png'), h)
        save_rgb(os.path.join(MAPS, 'pebble_normal.png'), to_rgb(height_to_normal(h, strength=PEBBLE_STRENGTH, tile=True)))
        rep['pebble_normal'] = {'size': 1024}
    if want('stone'):
        h = scan_height('rock_08_disp_1k.jpg', 0.004)
        save_gray(os.path.join(MAPS, 'stone_height.png'), h)
        save_rgb(os.path.join(MAPS, 'stone_normal.png'), to_rgb(height_to_normal(h, strength=STONE_STRENGTH, tile=True)))
        rep['stone_normal'] = {'size': 1024}
    json.dump(rep, open(os.path.join(MAPS, 'maps_report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    only = None
    size = 2048
    a = sys.argv[1:]
    if '--only' in a:
        only = a[a.index('--only') + 1]
    if '--size' in a:
        size = int(a[a.index('--size') + 1])
    main(only, size)
