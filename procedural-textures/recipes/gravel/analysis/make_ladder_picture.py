# What this does (plain words): makes the ladder picture for the guide: the same 300 x 300 dot patch of the reference and of each description (zoomed 2x), with its
# size and main scores written on it: reference, procedural S, traced M, traced+stamps L (two sizes).
import json, os, sys
import cv2
import numpy as np
G = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
x0, y0, s = 640, 520, 300
items = [('reference', os.path.join(G, '..', '..', 'reference', 'gravel', 'colour.png'), None, None),
         ('S_v4: procedural, 2.4 KB', os.path.join(G, 'outputs', 'S_v4', 'colour.png'), 'S_v4', None),
         ('M: traced big patches + stamps, 49 KB', os.path.join(G, 'outputs', 'M_a600_s120', 'colour.png'), 'M_a600_s120', None),
         ('L: patches>=250 + stamps>=12, 270 KB', os.path.join(G, 'outputs', 'L_a250_s12', 'colour.png'), 'L_a250_s12', None),
         ('L: patches>=100 + stamps>=8, 426 KB', os.path.join(G, 'outputs', 'L_a100_s8', 'colour.png'), 'L_a100_s8', None)]
cells = []
for label, path, name, _ in items:
    im = cv2.imread(path)[y0:y0 + s, x0:x0 + s]
    im = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    banner = np.full((54, im.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, label, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 1, cv2.LINE_AA)
    if name and os.path.exists(os.path.join(G, 'scores', name + '_summary.json')):
        p = json.load(open(os.path.join(G, 'scores', name + '_summary.json')))['pixel']
        cv2.putText(banner, f"SSIM {p['colour_ssim']:.2f}  dE {p['colour_mean_delta_e']:.1f}  edges {p['edge_skill_2px']:.2f}", (6, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 60, 60), 1, cv2.LINE_AA)
    cells.append(np.vstack([banner, im]))
row1 = np.hstack(cells[:3]); row2 = np.hstack(cells[3:] + [np.full_like(cells[0], 255)])
cv2.imwrite(os.path.join(G, 'guide_pictures', 'ladder_crops.png'), np.vstack([row1, row2]))
print('ok')
