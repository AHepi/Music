# What this does: shows what happens to a seamless tile when a compositor filter (Kuwahara) runs on it, and tests fixes.
#   A. plain: filter the 1254 x 1254 tile as it is (the filter has no neighbours at the picture edge);
#   B. padded bake: bake the pattern a margin wider than the tile (the pattern repeats, so the margin is real), filter, cut the middle tile out;
#   C. compositor-only padding: tile the finished PNG with Translate/Transform nodes (Extension = Repeat) on a bigger canvas, filter, crop.
# Measures the error near the tile edge, the jump across the wrap-around edge, and makes 2 x 2 tiling pictures around the seam.
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

BASE = os.path.join(hp.OUT, 'pictures', 'c08_seams'); os.makedirs(BASE, exist_ok=True)
SIZE = 1254
PAD = 96
hp.SAMPLES = 4

def grainy():
    """same grainy cells as c06"""
    tree, w = hp.new_group('grainy source', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    hp.instance(w, hp.warp_vector_group('grainy warp'), 'warp', x=0, Amount=0.02, Scale=10.0); w.link('in', 'Vector', 'warp', 'Vector')
    hp.instance(w, rt.tileable_voronoi_group(), 'cells', x=1, Scale=9.0, Randomness=1.0); w.link('warp', 'Vector', 'cells', 'Vector')
    hp.cell_random(w, 'rand', 'cells', 'Color', 0.0, x=2)
    hp.palette_ramp(w, 'palette', hp.BRICK_PALETTE, x=3); w.link('rand', 'Value', 'palette', 'Fac')
    hp.instance(w, rt.tileable_noise_group(), 'grain', x=2, y=-2, Scale=140.0, Detail=3.0, Roughness=0.6); w.link('in', 'Vector', 'grain', 'Vector')
    hp.instance(w, rt.tileable_noise_group(), 'shade', x=2, y=-3, Scale=5.0, Detail=2.0); w.link('in', 'Vector', 'shade', 'Vector')
    w.add('ShaderNodeMapRange', 'grain v', x=3, y=-2, clamp=True); w.nodes['grain v'].inputs['From Min'].default_value = 0.25; w.nodes['grain v'].inputs['From Max'].default_value = 0.75
    w.nodes['grain v'].inputs['To Min'].default_value = 0.55; w.nodes['grain v'].inputs['To Max'].default_value = 1.45
    w.link('grain', 'Fac', 'grain v', 'Value')
    w.add('ShaderNodeMapRange', 'shade v', x=3, y=-3, clamp=True); w.nodes['shade v'].inputs['From Min'].default_value = 0.3; w.nodes['shade v'].inputs['From Max'].default_value = 0.7
    w.nodes['shade v'].inputs['To Min'].default_value = 0.7; w.nodes['shade v'].inputs['To Max'].default_value = 1.3
    w.link('shade', 'Fac', 'shade v', 'Value')
    w.add('ShaderNodeMix', 'm1', x=4, data_type='RGBA', blend_type='MULTIPLY'); w.nodes['m1'].inputs['Factor'].default_value = 1.0
    w.link('palette', 'Color', 'm1', 'A'); w.link('grain v', 'Result', 'm1', 'B')
    w.add('ShaderNodeMix', 'm2', x=5, data_type='RGBA', blend_type='MULTIPLY'); w.nodes['m2'].inputs['Factor'].default_value = 1.0
    w.link('m1', 'Result', 'm2', 'A'); w.link('shade v', 'Result', 'm2', 'B')
    w.link('m2', 'Result', 'out', 'Colour')
    return tree

plain = os.path.join(BASE, 'source_tile.png')
padded = os.path.join(BASE, 'source_padded_tile.png')
t = time.time()
hp.photograph_group(grainy, 'Colour', plain, SIZE)
hp.photograph_padded(grainy, 'Colour', padded, SIZE, PAD)
print('baked sources %.1fs' % (time.time() - t))
padded_full = padded.replace('.png', '_padded.png')

def kuwahara(size=8.0, kind='Anisotropic'):
    def make(tree, image, extras):
        n = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(image.outputs['Image'], n.inputs['Image']); hp.set_menu(n, 'Type', kind); n.inputs['Size'].default_value = size
        return n.outputs['Image']
    return make

res = {}
for kind, size in (('Anisotropic', 8.0), ('Classic', 8.0)):
    tag = kind[:5].lower()
    # A plain
    hp.run_compositor(plain, os.path.join(BASE, f'A_plain_{tag}.png'), kuwahara(size, kind))
    # B padded bake
    hp.run_compositor(padded_full, os.path.join(BASE, f'B_padded_full_{tag}.png'), kuwahara(size, kind))
    full = hp.load(os.path.join(BASE, f'B_padded_full_{tag}.png'))
    hp.save(full[PAD:PAD + SIZE, PAD:PAD + SIZE], os.path.join(BASE, f'B_padded_{tag}.png'))
    # C compositor-only padding: Image (1254) on a (1254 + 2 PAD) canvas, wrapped with Transform(Repeat) then filter then Crop
    def make_c(tree, image, extras, size=size, kind=kind):
        tr = tree.nodes.new('CompositorNodeTranslate'); tree.links.new(image.outputs['Image'], tr.inputs['Image'])
        hp.set_menu(tr, 'Extension X', 'Repeat'); hp.set_menu(tr, 'Extension Y', 'Repeat')
        tr.inputs['X'].default_value = float(PAD); tr.inputs['Y'].default_value = float(PAD)
        k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(tr.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = size
        return k.outputs['Image']
    # run on a bigger canvas: the scene resolution is taken from the loaded image, so make a canvas-sized copy first
    canvas = np.zeros((SIZE + 2 * PAD, SIZE + 2 * PAD, 3)); canvas[:SIZE, :SIZE] = hp.load(plain)
    hp.save(canvas, os.path.join(BASE, 'canvas_for_C.png'))
    try:
        hp.run_compositor(os.path.join(BASE, 'canvas_for_C.png'), os.path.join(BASE, f'C_compositor_pad_{tag}_full.png'), make_c)
        res[f'C_{tag}_ran'] = True
    except Exception as e:
        res[f'C_{tag}_ran'] = repr(e)
    print(kind, 'done', flush=True)

# measurements
def seam_jump(a):
    grey = a.mean(axis=2)
    inner = (np.abs(np.diff(grey, axis=1)).mean() + np.abs(np.diff(grey, axis=0)).mean()) / 2
    wrap = (np.abs(grey[:, 0] - grey[:, -1]).mean() + np.abs(grey[0, :] - grey[-1, :]).mean()) / 2
    return wrap / inner
src = hp.load(plain)
res['seam_ratio_source'] = seam_jump(src)
for tag in ('anisotropic'[:5], 'classic'[:5]):
    A = hp.load(os.path.join(BASE, f'A_plain_{tag}.png')); B = hp.load(os.path.join(BASE, f'B_padded_{tag}.png'))
    res[f'seam_ratio_A_plain_{tag}'] = seam_jump(A); res[f'seam_ratio_B_padded_{tag}'] = seam_jump(B)
    diff = np.abs(A - B).mean(axis=2)
    # error versus distance from the nearest picture edge
    ys, xs = np.indices(diff.shape)
    dist = np.minimum.reduce([xs, SIZE - 1 - xs, ys, SIZE - 1 - ys])
    res[f'A_vs_B_{tag}_mean_abs_diff_by_distance_from_edge'] = {str(d): float(diff[(dist >= d) & (dist < d + 4)].mean()) for d in (0, 4, 8, 16, 32, 64, 128)}
    res[f'A_vs_B_{tag}_distance_where_error_below_0.002'] = int(next((d for d in range(0, 200) if diff[(dist == d)].mean() < 0.002), 200))
    # 2 x 2 tiling picture around the centre seam, for A and B
    for name, im in (('A_plain', A), ('B_padded', B)):
        tiled = np.tile(im, (2, 2, 1))
        c = SIZE
        crop = tiled[c - 250:c + 250, c - 250:c + 250]
        hp.save(crop, os.path.join(BASE, f'tiled_seam_{name}_{tag}.png'))
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c08_compositor_seams.json'), 'w'), indent=1)
print(json.dumps(res, indent=1)[:3000])
