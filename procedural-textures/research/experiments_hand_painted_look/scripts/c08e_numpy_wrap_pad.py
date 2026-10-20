# What this does: the fix that works from a finished PNG: wrap-pad the picture with numpy (np.pad mode 'wrap': copy the left edge strip to the right side, etc.),
# save it as a bigger PNG, run the compositor filter on that, cut the middle out. Compares with the padded bake (B) and the plain filter (A).
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
BASE = os.path.join(hp.OUT, 'pictures', 'c08_seams'); SIZE, PAD = 1254, 96
plain = hp.load(os.path.join(BASE, 'source_tile.png'))
padded = np.pad(plain, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='wrap')
hp.save(padded, os.path.join(BASE, 'E_wrap_padded_source.png'))
def kuw(tree, image, extras):
    k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(image.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', 'Anisotropic'); k.inputs['Size'].default_value = 8.0
    return k.outputs['Image']
hp.run_compositor(os.path.join(BASE, 'E_wrap_padded_source.png'), os.path.join(BASE, 'E_wrap_padded_filtered_full.png'), kuw)
F = hp.load(os.path.join(BASE, 'E_wrap_padded_filtered_full.png')); E = F[PAD:PAD + SIZE, PAD:PAD + SIZE]
hp.save(E, os.path.join(BASE, 'E_wrap_padded_filtered.png'))
A = hp.load(os.path.join(BASE, 'A_plain_aniso.png')); B = hp.load(os.path.join(BASE, 'B_padded_aniso.png'))
def seam(a):
    g = a.mean(axis=2); inner = (np.abs(np.diff(g, axis=1)).mean() + np.abs(np.diff(g, axis=0)).mean()) / 2; wrap = (np.abs(g[:, 0] - g[:, -1]).mean() + np.abs(g[0] - g[-1]).mean()) / 2; return float(wrap / inner)
ys, xs = np.indices((SIZE, SIZE)); dist = np.minimum.reduce([xs, SIZE - 1 - xs, ys, SIZE - 1 - ys])
res = {'seam_ratio_source': seam(plain), 'seam_ratio_A_plain_filter': seam(A), 'seam_ratio_B_padded_bake': seam(B), 'seam_ratio_E_numpy_wrap_pad': seam(E),
       'edge10px_diff_E_vs_B': float(np.abs(E - B).mean(axis=2)[dist < 10].mean()), 'edge10px_diff_E_vs_A': float(np.abs(E - A).mean(axis=2)[dist < 10].mean())}
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c08e_numpy_wrap_pad.json'), 'w'), indent=1)
# seam detector picture: edge strength of the 2 x 2 tiling around the centre, for A, B, E
def edge(im):
    g = im.mean(axis=2); gx = np.abs(np.diff(g, axis=1, prepend=g[:, :1])); gy = np.abs(np.diff(g, axis=0, prepend=g[:1])); return np.clip((gx + gy) * 5, 0, 1)
tiles = []
for im in (A, B, E):
    t = np.tile(im, (2, 2, 1)); c = SIZE
    tiles.append(edge(t[c - 300:c + 300, c - 300:c + 300]))
hp.save(np.stack([np.hstack(tiles)] * 3, axis=-1), os.path.join(BASE, 'seam_detector_A_B_E.png'))
