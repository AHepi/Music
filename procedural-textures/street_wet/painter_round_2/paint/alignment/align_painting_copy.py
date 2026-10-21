"""WHAT THIS FILE IS (plain words): a COPY of the film kit's align_painting.py (paper-film/tools/align_painting.py), made for the wet street painter test.
The film kit's own file was not touched. What the copy does is the same: it finds the small stretch and shift the painter put on the picture,
by moving the painting until its edges sit on the outlines of the props that Blender measured for the plate's camera, then undoes it.
Only three things differ from the original, none of them in the search itself:
  1. it imports check_shot.py from the copy beside it (so nothing is written into the film kit's folder);
  2. it also prints, for each prop group, how many of the group's outline points sit on a painting edge before and after
     (the original prints only the total), so a prop that lines up worse than the rest can be seen;
  3. it prints a warning if the best stretch or shift lies at the edge of the search range (then the range is too small).
Use: python3 -I align_painting_copy.py CHECK_FILE PLATE_FACTS PAINTING OUT_PAINTING [GROUP ...]
"""
import os
import sys
import types
sys.dont_write_bytecode = True

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_shot  # noqa: E402

check_file, facts, painting_path, out_path = sys.argv[1:5]
rest = sys.argv[5:]
against = rest[rest.index('--against') + 1] if '--against' in rest else None
only = [a for i, a in enumerate(rest) if a != '--against' and (i == 0 or rest[i - 1] != '--against')]
shot = check_shot.Shot(types.SimpleNamespace(check=check_file, facts=facts, picture=painting_path, out='/tmp', title='', render_log=None))
lab = cv2.cvtColor(cv2.GaussianBlur(shot.picture, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
edges = cv2.Canny(lab[:, :, 0], 20, 60) > 0
for colour in (1, 2):
    edges |= cv2.Canny(lab[:, :, colour], 10, 30) > 0
near = cv2.dilate(edges.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
points = []
if against:   # the lined-up painting's own edges, away from the props this painting no longer has
    reference = cv2.resize(cv2.imread(against), (shot.width, shot.height), interpolation=cv2.INTER_AREA)
    ref_lab = cv2.cvtColor(cv2.GaussianBlur(reference, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
    ref_edges = cv2.Canny(ref_lab[:, :, 0], 40, 100) > 0
    gone = np.zeros_like(ref_edges)
    for g in (only or shot.core):
        if g in shot.visible:
            gone |= shot.visible[g] | shot.alone.get(g, np.zeros_like(gone))
    gone = cv2.dilate(gone.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    ys, xs = np.nonzero(ref_edges & ~gone)
    points.append(np.stack([xs, ys], 1))
else:
    for g in (only or shot.core + shot.check.get('pairs_also', [])):
        if g in shot.visible and shot.visible[g].sum() > 400:
            mask = shot.visible[g].astype(np.uint8)
            ys, xs = np.nonzero((mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0)
            points.append(np.stack([xs, ys], 1))
points = np.concatenate(points).astype(np.float64)
W, H = shot.width, shot.height
centre = np.array([W / 2, H / 2])


def agree(scale, dx, dy):
    # where each outline point falls in the (unaligned) painting
    p = (points - centre) * scale + centre + [dx, dy]
    x, y = np.round(p[:, 0]).astype(int), np.round(p[:, 1]).astype(int)
    inside = (x >= 0) & (x < W) & (y >= 0) & (y < H)
    return near[y[inside], x[inside]].mean()


best = max((agree(s, dx, dy), s, dx, dy) for s in np.arange(0.985, 1.0151, 0.0025) for dx in range(-12, 13, 2) for dy in range(-12, 13, 2))
_, s0, dx0, dy0 = best
best = max((agree(s, dx, dy), s, dx, dy) for s in np.arange(s0 - 0.002, s0 + 0.0021, 0.0005)
           for dx in np.arange(dx0 - 2, dx0 + 2.01, 0.5) for dy in np.arange(dy0 - 2, dy0 + 2.01, 0.5))
score, scale, dx, dy = best
print(f'unaligned agreement {agree(1, 0, 0):.3f}; best {score:.3f} at stretch {scale:.4f}, shift {dx:+.1f}, {dy:+.1f} pixels (of {W} wide)')
if abs(scale - 0.985) < 1e-6 or abs(scale - 1.015) < 0.0006 or abs(dx) >= 12 or abs(dy) >= 12:
    print('WARNING: the best stretch or shift is at the edge of the search range; the range may be too small')
# (change 2) per group, before and after
groups_report = {}
for g in (only or shot.core + shot.check.get('pairs_also', [])):
    if g in shot.visible and shot.visible[g].sum() > 400:
        mask = shot.visible[g].astype(np.uint8)
        ys, xs = np.nonzero((mask - cv2.erode(mask, np.ones((3, 3), np.uint8))) > 0)
        pts = np.stack([xs, ys], 1).astype(np.float64)
        def agree_g(s, ddx, ddy, pts=pts):
            p = (pts - centre) * s + centre + [ddx, ddy]
            x, y = np.round(p[:, 0]).astype(int), np.round(p[:, 1]).astype(int)
            ok = (x >= 0) & (x < W) & (y >= 0) & (y < H)
            return near[y[ok], x[ok]].mean()
        groups_report[g] = (len(pts), agree_g(1, 0, 0), agree_g(scale, dx, dy))
for g, (n, a0, a1) in groups_report.items():
    print(f'  {g:16s} {n:5d} outline points: {a0:.2f} before, {a1:.2f} after')
full = cv2.imread(painting_path)
fh, fw = full.shape[:2]
k = fw / W
# output pixel x takes the painting's pixel at (x - c) * scale + c + d
matrix = np.array([[scale, 0, (1 - scale) * fw / 2 + dx * k], [0, scale, (1 - scale) * fh / 2 + dy * k]])
aligned = cv2.warpAffine(full, matrix, (fw, fh), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(out_path, aligned)
print('saved', out_path)
