# What this does (plain words): compares the honesty checker's own re-bake of the default tile (verify/after_look_fixes/default_rebake/)
# with the delivered default tile (outputs/default/), picture by picture, dot by dot, and prints how many dots differ and by how much.
# Colour and roughness are 8-bit (steps of 255), height is 16-bit (steps of 65535). Use: python3 -I compare_rebake.py REBAKE_FOLDER DELIVERED_FOLDER [name ...]
import sys, os, json
import cv2, numpy as np
a_dir, b_dir = sys.argv[1], sys.argv[2]
names = sys.argv[3:] or ['colour', 'height', 'roughness', 'metallic', 'normal']
out = {}
for n in names:
    pa, pb = os.path.join(a_dir, n + '.png'), os.path.join(b_dir, n + '.png')
    if not (os.path.exists(pa) and os.path.exists(pb)):
        print(n, 'missing', os.path.exists(pa), os.path.exists(pb)); continue
    a = cv2.imread(pa, cv2.IMREAD_UNCHANGED).astype(np.int64); b = cv2.imread(pb, cv2.IMREAD_UNCHANGED).astype(np.int64)
    if a.shape != b.shape:
        print(n, 'SHAPE', a.shape, b.shape); continue
    d = np.abs(a - b)
    dd = d.max(axis=-1) if d.ndim == 3 else d
    top = 65535 if a.max() > 255 else 255
    r = {'shape': list(a.shape), 'dots_differing_pct': round(float((dd > 0).mean() * 100), 4), 'max_diff': int(dd.max()), 'mean_diff': round(float(dd.mean()), 5),
         'dots_diff_over_1_pct': round(float((dd > 1).mean() * 100), 4), 'dots_diff_over_2_pct': round(float((dd > 2).mean() * 100), 4), 'scale': top}
    out[n] = r
    print(n, r)
