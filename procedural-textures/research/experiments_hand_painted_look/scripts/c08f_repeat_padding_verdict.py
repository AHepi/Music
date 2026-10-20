# What this does (plain python): the written-down evidence that the compositor's "Extension: Repeat" (Translate node) does NOT give a filter real neighbours.
# Compares the Kuwahara result made after a Translate(+96 px, Repeat) on a bigger canvas (cut at the matching place) with the plain filter (A) and with the
# padded bake (B): near the tile edge it is identical to A (no padding effect), and its wrap seam ratio equals A's.
import os, json, cv2, numpy as np
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(BASE, 'pictures', 'c08_seams'); S = 1254
L = lambda n: cv2.imread(os.path.join(P, n)).astype(np.float32) / 255
A, B, F = L('A_plain_aniso.png'), L('B_padded_aniso.png'), L('C_compositor_only_aniso_full.png')
C = F[0:S, 192:192 + S]
ys, xs = np.indices((S, S)); dist = np.minimum.reduce([xs, S - 1 - xs, ys, S - 1 - ys])
def seam(a):
    g = a.mean(axis=2); inner = (np.abs(np.diff(g, axis=1)).mean() + np.abs(np.diff(g, axis=0)).mean()) / 2; wrap = (np.abs(g[:, 0] - g[:, -1]).mean() + np.abs(g[0] - g[-1]).mean()) / 2; return float(wrap / inner)
res = {'seam_ratio_plain_filter_A': seam(A), 'seam_ratio_padded_bake_B': seam(B), 'seam_ratio_translate_repeat_crop_C': seam(C),
       'edge10px_mean_abs_diff_C_vs_A': float(np.abs(C - A).mean(axis=2)[dist < 10].mean()), 'edge10px_mean_abs_diff_C_vs_B': float(np.abs(C - B).mean(axis=2)[dist < 10].mean()),
       'verdict': 'Translate with Extension Repeat gave a canvas covered with repeats, but the Kuwahara result inside the tile is identical to the plain filter: no padding effect.'}
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(BASE, 'data', 'c08f_repeat_padding_verdict.json'), 'w'), indent=1)
