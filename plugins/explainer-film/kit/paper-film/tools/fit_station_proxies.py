"""What this does: builds simple 3D stand-ins ("proxies") for the petrol station in painting 409 -
the forecourt ground, the two canopy posts, the kiosk, the canopy deck and the pump island - placed
so each one lands on its edges in the painting, in the same space as the stage's painted room (camera
at the origin looking along -z, fov 40, distances from the depth picture with near 6 and far 70).
It writes their corners to a JSON file the test scene loads, and draws their outlines over the
painting (a "wireframe overlay") so the fit can be checked to within a few pixels before anything
is drawn in 3D. Edge positions measured by eye on the painting are listed below.
Use: python3 -I fit_station_proxies.py PAINTING.jpg DEPTH.png OUT.json OVERLAY.jpg"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw

painting_path, depth_path, out_json, overlay_path = sys.argv[1:5]
W, H = 1536, 2736
NEAR, FAR, FOV = 6.0, 70.0, 40.0
TAN_Y = np.tan(np.radians(FOV / 2)); TAN_X = TAN_Y * W / H

def ray(px, py):
    return np.array([(px / W * 2 - 1) * TAN_X, (1 - py / H * 2) * TAN_Y, -1.0])
def project(p):
    d = -p[2]
    return np.array([((p[0] / d / TAN_X) + 1) / 2 * W, (1 - (p[1] / d / TAN_Y)) / 2 * H])
def hit_plane(px, py, normal, offset):            # plane: normal . p = offset
    r = ray(px, py); return r * (offset / normal.dot(r))

# 1. the ground: a flat plane fitted to the painted room's forecourt (open concrete in front of the island)
depth = np.asarray(Image.open(depth_path).convert('L'), dtype=float) / 255
h, w = depth.shape
ys, xs = np.mgrid[0:h, 0:w]
u, v = (xs + 0.5) / w, 1 - (ys + 0.5) / h
dist = 1 / (depth / NEAR + (1 - depth) / FAR)
P = np.stack([(2 * u - 1) * TAN_X * dist, (2 * v - 1) * TAN_Y * dist, -dist], -1)
py_full = (ys + 0.5) / h * H; px_full = (xs + 0.5) / w * W
area = (py_full > 1900) & (py_full < 2650) & (px_full > 350)      # open forecourt, clear of the car and island
pts = P[area]
keep = np.ones(len(pts), bool)
for _ in range(8):
    A = np.c_[pts[keep][:, 0], pts[keep][:, 2], np.ones(keep.sum())]
    (a, b, c), *_ = np.linalg.lstsq(A, pts[keep][:, 1], rcond=None)
    err = np.abs(pts[:, 0] * a + pts[:, 2] * b + c - pts[:, 1])
    keep = err < max(0.03, np.percentile(err[keep], 75))
up = np.array([-a, 1.0, -b]); up /= np.linalg.norm(up)               # y = a x + b z + c  ->  up . p = c / |(-a,1,-b)|
ground_offset = c / np.linalg.norm([-a, 1.0, -b])
horizon_y = (1 + (b / TAN_Y)) / 2 * H                                 # where the ground's horizon sits at the picture's centre
print(f'ground: y = {a:+.4f} x {b:+.4f} z {c:+.3f}; horizon at about y {horizon_y:.0f} px')

# 2. the station's own directions: along the kiosk's front wall, and towards the camera
k1, k2 = hit_plane(1290, 1455, up, ground_offset), hit_plane(1520, 1480, up, ground_offset)
along = k2 - k1; along -= up * up.dot(along); along /= np.linalg.norm(along)
toward = np.cross(up, along)
if toward[2] < 0: toward = -toward                                    # pointing at the camera (+z)

def box(base_centre, size_along, size_toward, height, turn=0.0):
    """Eight corners of an upright box standing on base_centre (turned `turn` degrees about up)."""
    t = np.radians(turn)
    e1 = along * np.cos(t) + toward * np.sin(t); e2 = np.cross(up, e1)
    if e2.dot(toward) < 0: e2 = -e2
    corners = []
    for lift in (0, height):
        for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corners.append(base_centre + e1 * s1 * size_along / 2 + e2 * s2 * size_toward / 2 + up * lift)
    return np.array(corners)

ISLAND_HEIGHT = 0.12
island_offset = ground_offset + ISLAND_HEIGHT

def fit_post(base_px, top_py, edges_px, turn):
    """A square post: find base point, width and height so its outline meets the painted edges."""
    best = None
    for dx in np.linspace(-20, 20, 41):
        base = hit_plane(base_px[0] + dx, base_px[1], up, island_offset)
        for size in np.linspace(0.15, 0.6, 46):
            corners = box(base, size, size, 1.0, turn)
            xs_ = [project(c)[0] for c in corners[:4]]
            left, right = min(xs_), max(xs_)
            mid = sorted(xs_)[1] if np.argmax([c.dot(toward) for c in corners[:4]]) is not None else None
            front = corners[:4][np.argmax([c.dot(toward) - c[2] * 0 for c in corners[:4]])]
            error = abs(left - edges_px[0]) + abs(right - edges_px[2]) + 0.5 * abs(project(front)[0] - edges_px[1])
            if best is None or error < best[0]: best = (error, base, size)
    error, base, size = best
    # height: lift until the top lands on the painted top
    lo, hi = 0.5, 20.0
    for _ in range(50):
        mid_h = (lo + hi) / 2
        if project(base + up * mid_h)[1] > top_py: lo = mid_h
        else: hi = mid_h
    return box(base, size, size, lo, turn), error

proxies = {}
proxies['post_front'], e1_ = fit_post((1253, 1740), 533, (1221, 1249, 1286), turn=0)
proxies['post_rear'], e2_ = fit_post((875, 1589), 650, (848, 875, 902), turn=0)
print(f'posts fitted (edge error {e1_:.1f} and {e2_:.1f} px)')

# kiosk: an upright block whose front wall runs through the painted wall base, from its left end to past the frame
k_left = hit_plane(1012, 1430, up, ground_offset)
k_left = k1 + along * along.dot(k_left - k1)
k_right = k1 + along * along.dot(hit_plane(1700, 1500, up, ground_offset) - k1)
top_point = None
lo, hi = 0.5, 30.0
for _ in range(50):
    mid_h = (lo + hi) / 2
    if project(k2 + up * mid_h)[1] > 878: lo = mid_h
    else: hi = mid_h
kiosk_height = lo
KIOSK_DEPTH = 5.0
front_centre = (k_left + k_right) / 2
kiosk = []
for lift in (0, kiosk_height):
    for p_ in (k_left, k_right, k_right - toward * KIOSK_DEPTH, k_left - toward * KIOSK_DEPTH):
        kiosk.append(p_ + up * lift)
proxies['kiosk'] = np.array(kiosk)

# canopy deck: a slab seen from underneath. Its underside sits at the front post's top. Painted points:
# the near corner of the underside (1197, 385), the left end of the front edge (538, 668), the back
# edge passing (1536, 750), and the top of the fascia above the near corner (1191, 221).
post_top = proxies['post_front'][4:].mean(0)
deck_offset = up.dot(post_top)
# The painting's canopy is not a true rectangle in this space (AI paintings bend perspective), so the
# deck is the four painted corners on that plane: left end, near corner, and the right fascia and the
# back edge continued a little past the frame's right edge.
def extend(p0, p1, x):
    return (x, p0[1] + (p1[1] - p0[1]) * (x - p0[0]) / (p1[0] - p0[0]))
corners_px = [(538, 668), (1197, 385), extend((1197, 385), (1536, 438), 1800), extend((538, 668), (1536, 750), 1800)]
deck = [hit_plane(px, py, up, deck_offset) for px, py in corners_px]
lo, hi = 0.05, 5.0                                                       # thickness: the fascia top over the near corner
for _ in range(50):
    mid_t = (lo + hi) / 2
    if project(deck[1] + up * mid_t)[1] > 221: lo = mid_t
    else: hi = mid_t
proxies['canopy'] = np.array(deck + [p_ + up * lo for p_ in deck])
print(f'canopy: {lo:.2f} thick; its left end top lands at y {project(deck[0] + up * lo)[1]:.0f} (painted 562)')

# pump island: a low slab along the painted front base line, reaching back to the rear post
i_front_left, i_front_right = hit_plane(694, 1567, up, ground_offset), hit_plane(1478, 1868, up, ground_offset)
back_dist = toward.dot(i_front_left - proxies['post_rear'][:4].mean(0)) + 0.6
island = []
for lift in (0, ISLAND_HEIGHT):
    for p_ in (i_front_left, i_front_right, i_front_right - toward * back_dist, i_front_left - toward * back_dist):
        island.append(p_ + up * lift)
proxies['island'] = np.array(island)

# overlay: every proxy edge drawn on the painting
im = Image.open(painting_path).convert('RGB'); d = ImageDraw.Draw(im)
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
colours = {'post_front': (255, 0, 255), 'post_rear': (255, 0, 255), 'kiosk': (0, 255, 255), 'canopy': (255, 255, 0), 'island': (0, 255, 0)}
for name, corners in proxies.items():
    pts2 = [project(c) for c in corners]
    for i, j in EDGES:
        d.line([tuple(pts2[i]), tuple(pts2[j])], fill=colours[name], width=2)
im.save(overlay_path, quality=90)
json.dump({'what': 'proxy boxes for painting 409, corners in the painted room\'s space (8 per box: base 4, top 4)',
           'ground': [a, b, c], 'up': up.tolist(), 'island_height': ISLAND_HEIGHT,
           'boxes': {k: v.round(4).tolist() for k, v in proxies.items()}}, open(out_json, 'w'), indent=1)
for k, v in proxies.items():
    print(f'{k}: distance {-v[:, 2].mean():.1f}, size {np.ptp(v, 0).round(2).tolist()}')
