# What this does: finds the simplest compositor-only padding that gives exactly the padded bake: Transform node (Extension Repeat, no move) or Translate by 1 pixel.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
BASE = os.path.join(hp.OUT, 'pictures', 'c08_seams'); SIZE, PAD = 1254, 96
plain = os.path.join(BASE, 'source_tile.png')
def make_transform(size=8.0, kind='Anisotropic'):
    def f(tree, image, extras):
        t = tree.nodes.new('CompositorNodeTransform'); tree.links.new(image.outputs['Image'], t.inputs['Image'])
        hp.set_menu(t, 'Extension X', 'Repeat'); hp.set_menu(t, 'Extension Y', 'Repeat'); hp.set_menu(t, 'Interpolation', 'Nearest')
        k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(t.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = size
        return k.outputs['Image']
    return f
def make_translate1(size=8.0, kind='Anisotropic'):
    def f(tree, image, extras):
        t = tree.nodes.new('CompositorNodeTranslate'); tree.links.new(image.outputs['Image'], t.inputs['Image'])
        hp.set_menu(t, 'Extension X', 'Repeat'); hp.set_menu(t, 'Extension Y', 'Repeat'); hp.set_menu(t, 'Interpolation', 'Nearest'); t.inputs['X'].default_value = 1.0; t.inputs['Y'].default_value = 1.0
        k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(t.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = size
        return k.outputs['Image']
    return f
B = hp.load(os.path.join(BASE, 'B_padded_aniso.png'))
res = {}
for name, make in (('transform_repeat', make_transform), ('translate_1px_repeat', make_translate1)):
    full = os.path.join(BASE, f'D_{name}_full.png')
    hp.run_compositor(plain, full, make(), canvas=(SIZE + 2 * PAD, SIZE + 2 * PAD))
    F = hp.load(full)
    best = None
    for r0 in range(PAD - 2, PAD + 3):
        for c0 in range(PAD - 2, PAD + 3):
            d = float(np.abs(F[r0:r0 + SIZE, c0:c0 + SIZE] - B).mean())
            if best is None or d < best[0]: best = (d, r0, c0)
    res[name] = {'best_crop_row_start': best[1], 'best_crop_col_start': best[2], 'mean_abs_diff_to_padded_bake': best[0]}
    print(name, res[name], flush=True)
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c08d_pad_variants.json'), 'w'), indent=1)
