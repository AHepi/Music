# What this does: the fix that needs no re-bake. Take a finished tile PNG (1254 x 1254), let the compositor repeat it over a bigger canvas
# (Translate node, Extension = Repeat, canvas = tile + 2 x margin), run Kuwahara there, and cut the middle tile out. Compares with the padded
# bake (B) and the plain filter (A) from c08_compositor_seams.py, and makes a seam-detector picture (edge strength of the 2 x 2 tiling).
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
BASE = os.path.join(hp.OUT, 'pictures', 'c08_seams')
SIZE, PAD = 1254, 96
plain = os.path.join(BASE, 'source_tile.png')
def make(kind, size):
    def f(tree, image, extras):
        t = tree.nodes.new('CompositorNodeTranslate'); tree.links.new(image.outputs['Image'], t.inputs['Image'])
        hp.set_menu(t, 'Extension X', 'Repeat'); hp.set_menu(t, 'Extension Y', 'Repeat'); t.inputs['X'].default_value = float(PAD); t.inputs['Y'].default_value = float(PAD)
        k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(t.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = size
        return k.outputs['Image']
    return f
res = {}
for kind in ('Anisotropic', 'Classic'):
    tag = kind[:5].lower()
    full = os.path.join(BASE, f'C_compositor_only_{tag}_full.png')
    hp.run_compositor(plain, full, make(kind, 8.0), canvas=(SIZE + 2 * PAD, SIZE + 2 * PAD))
    f = hp.load(full); print(kind, 'output', f.shape)
    C = f[PAD:PAD + SIZE, PAD:PAD + SIZE]
    hp.save(C, os.path.join(BASE, f'C_compositor_only_{tag}.png'))
    B = hp.load(os.path.join(BASE, f'B_padded_{tag}.png')); A = hp.load(os.path.join(BASE, f'A_plain_{tag}.png'))
    grey = C.mean(axis=2)
    inner = (np.abs(np.diff(grey, axis=1)).mean() + np.abs(np.diff(grey, axis=0)).mean()) / 2
    wrap = (np.abs(grey[:, 0] - grey[:, -1]).mean() + np.abs(grey[0, :] - grey[-1, :]).mean()) / 2
    res[tag] = {'seam_ratio_C': float(wrap / inner), 'mean_abs_diff_C_vs_B_padded_bake': float(np.abs(C - B).mean()), 'mean_abs_diff_A_vs_B': float(np.abs(A - B).mean()),
                'mean_abs_diff_C_vs_B_within_10px_of_edge': None}
    ys, xs = np.indices(C.shape[:2]); dist = np.minimum.reduce([xs, SIZE - 1 - xs, ys, SIZE - 1 - ys])
    res[tag]['mean_abs_diff_C_vs_B_within_10px_of_edge'] = float(np.abs(C - B).mean(axis=2)[dist < 10].mean())
    res[tag]['mean_abs_diff_A_vs_B_within_10px_of_edge'] = float(np.abs(A - B).mean(axis=2)[dist < 10].mean())
    print(tag, res[tag])
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c08c_compositor_only_padding.json'), 'w'), indent=1)
# seam detector picture: 2 x 2 tiling, edge strength, centre area
def edge(im):
    g = im.mean(axis=2); gx = np.abs(np.diff(g, axis=1, prepend=g[:, :1])); gy = np.abs(np.diff(g, axis=0, prepend=g[:1]))
    return np.clip((gx + gy) * 6, 0, 1)
tiles = []
for name in ('A_plain_aniso', 'B_padded_aniso', 'C_compositor_only_aniso'):
    im = hp.load(os.path.join(BASE, name + '.png')); t = np.tile(im, (2, 2, 1)); c = SIZE
    tiles.append(edge(t[c - 300:c + 300, c - 300:c + 300]))
hp.save(np.stack([np.hstack(tiles)] * 3, axis=-1), os.path.join(BASE, 'seam_detector_A_B_C.png'))
