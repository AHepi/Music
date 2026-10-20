# What this does: takes the finished painted-slate colour picture (stage 4 of the demo), runs the Kuwahara filter on it (wrap-padded so the tile still repeats),
# and then tests three ways to make the height and normal maps for the stylised colour:
#   H1  height = lightness of the stylised colour (the way the reference maps were made);
#   H2  height = the height the recipe made BEFORE the filter (colour got stylised, height did not);
#   H3  the same Kuwahara filter run separately on the height.
# For each: correlation of colour lightness with height, how well the sharp edges line up (overlap of the strongest 5 percent of edges), and the
# texture_compare score is run afterwards by the caller. Writes folders stage5_aniso_h1, _h2, _h3 and stage5_classic_h1.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
BASE = os.path.join(hp.OUT, 'data', 'slate_demo')
PAD = 96
bh = hp.bh

def kuw(kind, size):
    def f(tree, image, extras):
        k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(image.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = float(size)
        return k.outputs['Image']
    return f

def filter_padded(path_in, path_out, kind, size, data=False, sixteen=False):
    img = hp.load(path_in) if not data else np.repeat(hp.load(path_in)[..., :1], 3, axis=2)
    tmp = os.path.join(BASE, 'tmp_padded_in.png')
    hp.save(np.pad(img, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='wrap'), tmp, sixteen=sixteen)
    out_full = os.path.join(BASE, 'tmp_padded_out.png')
    hp.run_compositor(tmp, out_full, kuw(kind, size), input_linear=data, output_linear=data, sixteen=sixteen)
    full = hp.load(out_full); n = img.shape[0]
    hp.save(full[PAD:PAD + n, PAD:PAD + n], path_out, sixteen=sixteen)
    return full[PAD:PAD + n, PAD:PAD + n]

def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def height_from_colour(rgb):
    lin = srgb_to_linear(rgb); y = lin @ np.array([0.2126, 0.7152, 0.0722])
    return np.clip((y ** (1 / 2.2)) / 0.46, 0, 1)

def blur_wrap(a, sigma):
    radius = int(np.ceil(sigma * 3)); xs = np.arange(-radius, radius + 1); k = np.exp(-xs ** 2 / (2 * sigma ** 2)); k /= k.sum()
    out = sum(k[i] * np.roll(a, radius - i, axis=1) for i in range(len(k)))
    return sum(k[i] * np.roll(out, radius - i, axis=0) for i in range(len(k)))

def grad(a):
    gx = np.roll(a, -1, axis=1) - np.roll(a, 1, axis=1); gy = np.roll(a, -1, axis=0) - np.roll(a, 1, axis=0); return np.hypot(gx, gy)

def metrics(rgb, height):
    lum = height_from_colour(rgb)
    gl, gh = grad(lum), grad(height)
    top = lambda g: g >= np.percentile(g, 95)
    a, b = top(gl), top(gh)
    return {'corr_lightness_height': float(np.corrcoef(lum.ravel(), height.ravel())[0, 1]), 'corr_edge_strength': float(np.corrcoef(gl.ravel(), gh.ravel())[0, 1]),
            'strongest_5pct_edges_overlap_dice': float(2 * (a & b).sum() / (a.sum() + b.sum()))}

def write_set(folder, colour, height, reference='slate'):
    os.makedirs(folder, exist_ok=True)
    hp.save(colour, os.path.join(folder, 'colour.png'))
    hp.save(height, os.path.join(folder, 'height.png'), sixteen=True)
    strength = bh.fit_sobel_strength(height, bh.reference_normal_slope_spread(reference))
    hp.save(bh.sobel_normal(height, strength) * 0.5 + 0.5, os.path.join(folder, 'normal.png'))
    return strength

res = {}
src_colour = os.path.join(BASE, 'stage4', 'colour.png'); src_height = os.path.join(BASE, 'stage4', 'height.png')
C0 = hp.load(src_colour); H0 = hp.load(src_height)[..., 0]
res['stage4_before_filter'] = metrics(C0, H0)
for kind, size, tag in (('Anisotropic', 6, 'aniso'), ('Classic', 4, 'classic')):
    C = filter_padded(src_colour, os.path.join(BASE, f'kuwahara_{tag}_colour.png'), kind, size)
    H1 = height_from_colour(C)
    s1 = write_set(os.path.join(BASE, f'stage5_{tag}_h1'), C, H1)
    res[f'{tag}_h1_height_from_stylised_colour'] = metrics(C, H1)
    if tag == 'aniso':
        write_set(os.path.join(BASE, 'stage5_aniso_h1_smooth08'), C, blur_wrap(H1, 0.8))
        res['aniso_h1_smooth08'] = metrics(C, blur_wrap(H1, 0.8))
        s2 = write_set(os.path.join(BASE, 'stage5_aniso_h2'), C, H0)
        res['aniso_h2_height_not_filtered'] = metrics(C, H0)
        H3 = filter_padded(src_height, os.path.join(BASE, 'kuwahara_aniso_height.png'), kind, size, data=True, sixteen=True)[..., 0]
        s3 = write_set(os.path.join(BASE, 'stage5_aniso_h3'), C, H3)
        res['aniso_h3_height_filtered_separately'] = metrics(C, H3)
    print(tag, 'done', flush=True)
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c14_kuwahara_consistency.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
