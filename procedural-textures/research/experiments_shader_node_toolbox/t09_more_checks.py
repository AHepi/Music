# What this does: a few last measured checks: Voronoi 1D/4D inputs, the random per-cell Color values, how a typed colour value turns into a
# saved picture value (linear versus screen), and White Noise range. Writes more_checks.json
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
bh = pt.bh
OUT = os.path.dirname(os.path.abspath(__file__)); R = {}
D = 'ShaderNodeTex'
def vor(dim, wv=0.0, out='Distance', size=64, chan=None):
    def body(w):
        v = w.add(D + 'Voronoi', 'v', x=0, voronoi_dimensions=dim, Scale=5.0)
        w.link('in', 'Vector', 'v', 'Vector') if dim != '1D' else None
        for s in v.inputs:
            if s.identifier == 'W' and s.enabled: s.default_value = wv
        w.link('v', out, 'out', 'Height' if chan is None else 'Colour')
    return pt.render_float(body, 'Height' if chan is None else 'Colour', size)
a0, a1 = vor('4D', 0.0), vor('4D', 0.5)
R['voronoi_4D_W0_vs_W0.5_mean_abs_difference'] = round(float(np.abs(a0 - a1).mean()), 4)
b0, b1 = vor('1D', 0.2), vor('1D', 0.9)
R['voronoi_1D_std_across_picture_(0=constant)'] = round(float(b0.std()), 6)
R['voronoi_1D_W0.2_vs_W0.9_values'] = [round(float(b0.mean()), 4), round(float(b1.mean()), 4)]
c = vor('3D', out='Color', chan=True)
R['voronoi_cell_Color_channels_mean_std_min_max'] = [[round(float(c[..., i].mean()), 3), round(float(c[..., i].std()), 3), round(float(c[..., i].min()), 3), round(float(c[..., i].max()), 3)] for i in range(3)]
# white noise range
def wn(w):
    n = w.add(D + 'WhiteNoise', 'n', x=0, noise_dimensions='2D')
    w.add('ShaderNodeVectorMath', 'snap', x=-1, operation='SNAP'); w.nodes['snap'].inputs[1].default_value = (1 / 32, 1 / 32, 1 / 32)
    w.link('in', 'Vector', 'snap', 0); w.link('snap', 0, 'n', 0); w.link('n', 'Value', 'out', 'Height')
a = pt.render_float(wn, 'Height', 128)
R['white_noise_min_mean_max'] = [round(float(a.min()), 3), round(float(a.mean()), 3), round(float(a.max()), 3)]
R['white_noise_distinct_values_on_32x32_blocks'] = int(len(np.unique(np.round(a, 5))))
# colour entry: what a typed colour becomes in a saved picture
def col(v):
    def body(w):
        c = w.add('ShaderNodeRGB', 'c', x=0); c.outputs[0].default_value = (v, v, v, 1)
        w.link('c', 0, 'out', 'Colour')
    scene, tile = bh.new_bake_scene(8)
    g = pt.tree_from('cc', body)
    tile.data.materials.append(bh.show_channel_material(g, 'Colour'))
    bh.render_to(scene, os.path.join(OUT, '_c.png'), False, False)
    im = bpy.data.images.load(os.path.join(OUT, '_c.png'), check_existing=False); im.colorspace_settings.name = 'Non-Color'
    px = np.array(im.pixels[:]).reshape(-1, 4)
    return round(float(px[:, 0].mean()) * 255, 1)
R['typed_linear_value_to_saved_sRGB_png_0..255'] = {str(v): col(v) for v in (0.0, 0.05, 0.214, 0.5, 1.0)}
json.dump(R, open(os.path.join(OUT, 'more_checks.json'), 'w'), indent=1)
print(json.dumps(R, indent=1))
