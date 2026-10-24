"""What this does: lines a painting up with the plate it was painted from. A painter (an image model) can return
the picture very slightly stretched or shifted; the film shines the painting back onto the 3D set, so even a few
pixels show as painted edges beside the real ones. It finds the stretch and shift that put the painting's edges on
the props' outlines (as Blender measured them for the plate's camera), then warps the painting by it.

Use: python3 -I align_painting.py CHECK_FILE PLATE_FACTS PAINTING OUT_PAINTING
"""
import sys
import types

import cv2
import numpy as np

sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot  # noqa: E402

check_file, facts, painting_path, out_path = sys.argv[1:5]
shot = check_shot.Shot(types.SimpleNamespace(check=check_file, facts=facts, picture=painting_path, out='/tmp', title='', render_log=None))
lab = cv2.cvtColor(cv2.GaussianBlur(shot.picture, (0, 0), 1.5), cv2.COLOR_BGR2LAB)
edges = cv2.Canny(lab[:, :, 0], 20, 60) > 0
for colour in (1, 2):
    edges |= cv2.Canny(lab[:, :, colour], 10, 30) > 0
near = cv2.dilate(edges.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
points = []
for g in shot.core + shot.check.get('pairs_also', []):
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
full = cv2.imread(painting_path)
fh, fw = full.shape[:2]
k = fw / W
# output pixel x takes the painting's pixel at (x - c) * scale + c + d
matrix = np.array([[scale, 0, (1 - scale) * fw / 2 + dx * k], [0, scale, (1 - scale) * fh / 2 + dy * k]])
aligned = cv2.warpAffine(full, matrix, (fw, fh), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(out_path, aligned)
print('saved', out_path)
