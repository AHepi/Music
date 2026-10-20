# What this does: the remaining compositor facts for the guide.
#   1. Kuwahara seam size: how big the wrap-around jump gets for Size 4, 8, 16 without padding.
#   2. Kuwahara on colour numbers as sRGB-encoded values (what the eye sees) vs linear light (the default for a colour picture).
#   3. Posterize in the compositor on a colour picture: default vs on the encoded numbers.
#   4. Outlines from a patch-number picture: Filter Sobel + threshold, then widened with Dilate/Erode (Distance) or with Mask To SDF; measured line widths.
#   5. 16-bit height through the compositor (does Kuwahara keep the 16-bit precision?).
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src_text = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c05_outlines_in_shader.py')).read().split('results = {}')[0]
exec(compile(src_text, 'c05head', 'exec'))     # gives hp, rt, np, field_group, ...
BASE = os.path.join(hp.OUT, 'pictures', 'c09_compositor_details'); os.makedirs(BASE, exist_ok=True)
SIZE = 1254
tile = os.path.join(hp.OUT, 'pictures', 'c08_seams', 'source_tile.png')
res = {}

def kuw(kind, size, **extra):
    def f(tree, image, extras):
        k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(image.outputs['Image'], k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = float(size)
        for key, value in extra.items(): k.inputs[key.replace('__', ' ')].default_value = value
        return k.outputs['Image']
    return f
def seam(a):
    g = a.mean(axis=2); inner = (np.abs(np.diff(g, axis=1)).mean() + np.abs(np.diff(g, axis=0)).mean()) / 2; wrap = (np.abs(g[:, 0] - g[:, -1]).mean() + np.abs(g[0] - g[-1]).mean()) / 2; return float(wrap / inner)

# 1 seam vs size
res['seam_ratio_source'] = seam(hp.load(tile))
res['seam_ratio_plain_filter'] = {}
for kind, size in (('Anisotropic', 4), ('Anisotropic', 16), ('Classic', 4), ('Classic', 16)):
    out = os.path.join(BASE, f'seam_{kind[:5]}_{size}.png')
    hp.run_compositor(tile, out, kuw(kind, size))
    res['seam_ratio_plain_filter'][f'{kind} Size {size}'] = seam(hp.load(out))
print('1', res['seam_ratio_plain_filter'], flush=True)

# 2 colour space
a = os.path.join(BASE, 'kuwahara_linear_light.png'); b = os.path.join(BASE, 'kuwahara_encoded_values.png')
hp.run_compositor(tile, a, kuw('Anisotropic', 10))
hp.run_compositor(tile, b, kuw('Anisotropic', 10), input_linear=True, output_linear=True)    # numbers taken as they are in the file
A = hp.load(a); Bc = hp.load(b); S = hp.load(tile)
res['kuwahara_encoded_vs_linear_mean_abs_diff'] = float(np.abs(A - Bc).mean())
res['kuwahara_mean_colour_shift_linear'] = [float(v) for v in (A.mean(axis=(0, 1)) - S.mean(axis=(0, 1)))]
res['kuwahara_mean_colour_shift_encoded'] = [float(v) for v in (Bc.mean(axis=(0, 1)) - S.mean(axis=(0, 1)))]
print('2', res['kuwahara_encoded_vs_linear_mean_abs_diff'], flush=True)

# 3 posterize spaces
def post(steps):
    def f(tree, image, extras):
        n = tree.nodes.new('CompositorNodePosterize'); tree.links.new(image.outputs['Image'], n.inputs['Image']); n.inputs['Steps'].default_value = float(steps); return n.outputs['Image']
    return f
for steps in (4, 8):
    hp.run_compositor(tile, os.path.join(BASE, f'posterize_{steps}_linear.png'), post(steps))
    hp.run_compositor(tile, os.path.join(BASE, f'posterize_{steps}_encoded.png'), post(steps), input_linear=True, output_linear=True)
    for tag in ('linear', 'encoded'):
        p = hp.load(os.path.join(BASE, f'posterize_{steps}_{tag}.png'))
        res[f'posterize_{steps}_{tag}_distinct_colours'] = int(len(np.unique((p * 255).round().astype(int).reshape(-1, 3), axis=0)))
        res[f'posterize_{steps}_{tag}_mean_abs_change'] = float(np.abs(p - S).mean())

# 4 outlines from a patch-number picture
hp.SAMPLES = 1
idpath = os.path.join(BASE, 'patch_id.png')
def idgroup():
    tree, w = hp.new_group('id only', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    hp.instance(w, field_group('cells', scale=6.0, warp_amount=0.006, warp_scale=60.0), 'f', x=0); w.link('in', 'Vector', 'f', 'Vector'); w.link('f', 'Id', 'out', 'Height'); return tree
hp.photograph_group(idgroup, 'Height', idpath, SIZE)
hp.SAMPLES = 4
def edge_mask(tree, image):
    f = tree.nodes.new('CompositorNodeFilter'); tree.links.new(image.outputs['Image'], f.inputs['Image']); hp.set_menu(f, 'Type', 'Sobel')
    bw = tree.nodes.new('CompositorNodeRGBToBW'); tree.links.new(f.outputs['Image'], bw.inputs['Image'])
    m = tree.nodes.new('ShaderNodeMath'); m.operation = 'GREATER_THAN'; tree.links.new(bw.outputs['Val'], m.inputs[0]); m.inputs[1].default_value = 0.05
    return m.outputs['Value']
def to_color(tree, value_socket):
    c = tree.nodes.new('CompositorNodeCombineColor')
    for ch in ('Red', 'Green', 'Blue'): tree.links.new(value_socket, c.inputs[ch])
    return c.outputs['Image']
def outline_plain(tree, image, extras): return to_color(tree, edge_mask(tree, image))
def outline_dilate(size):
    def f(tree, image, extras):
        m = edge_mask(tree, image)
        d = tree.nodes.new('CompositorNodeDilateErode'); tree.links.new(m, d.inputs['Mask']); hp.set_menu(d, 'Type', 'Distance'); d.inputs['Size'].default_value = size
        return to_color(tree, d.outputs['Mask'])
    return f
def outline_dilate_steps(size):
    def f(tree, image, extras):
        m = edge_mask(tree, image)
        d = tree.nodes.new('CompositorNodeDilateErode'); tree.links.new(m, d.inputs['Mask']); hp.set_menu(d, 'Type', 'Steps'); d.inputs['Size'].default_value = size
        return to_color(tree, d.outputs['Mask'])
    return f
def outline_sdf(width):
    def f(tree, image, extras):
        m = edge_mask(tree, image)
        sdf = tree.nodes.new('CompositorNodeMaskToSDF'); tree.links.new(m, sdf.inputs['Mask'])
        lt = tree.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; tree.links.new(sdf.outputs['SDF'], lt.inputs[0]); lt.inputs[1].default_value = float(width)
        return to_color(tree, lt.outputs['Value'])
    return f
timings = {}
widths = {}
def width_of(path):
    a = hp.load(path)[..., 0] > 0.5
    runs = []
    for y in range(10, SIZE - 10, 7):
        row = a[y]
        edges = np.flatnonzero(np.diff(np.r_[0, row.astype(int), 0]))
        for s, e in zip(edges[::2], edges[1::2]):
            if e - s < 60: runs.append(e - s)
    return float(np.median(runs)) if runs else 0.0, float(a.mean())
for label, fn in [('sobel_only', outline_plain)] + [(f'dilate_distance_{k}', outline_dilate(k)) for k in (1, 2, 3, 4)] + [(f'dilate_steps_{k}', outline_dilate_steps(k)) for k in (1, 3)] + [(f'sdf_less_than_{k}', outline_sdf(k)) for k in (1.0, 2.0, 3.0, 4.0)]:
    out = os.path.join(BASE, 'outline_' + label + '.png')
    t = time.time(); hp.run_compositor(idpath, out, fn, input_linear=True, output_linear=True); timings[label] = round(time.time() - t, 2)
    widths[label] = width_of(out)
    print('4', label, widths[label], timings[label], flush=True)
res['outline_from_patch_picture'] = {k: {'median_line_width_px': v[0], 'share_of_picture': v[1], 'seconds': timings[k]} for k, v in widths.items()}

# 5 16-bit height through Kuwahara
hp.SAMPLES = 1
def hgroup():
    tree, w = hp.new_group('smooth height', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    hp.instance(w, rt.tileable_noise_group(), 'n', x=0, Scale=6.0, Detail=5.0); w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height'); return tree
hpath = os.path.join(BASE, 'height16.png')
hp.photograph_group(hgroup, 'Height', hpath, 512, sixteen=True)
h0 = hp.load(hpath)[..., 0]
for label, fn, sixteen in (('classic_8bit', kuw('Classic', 3), False), ('classic_16bit', kuw('Classic', 3), True)):
    out = os.path.join(BASE, f'height_{label}.png')
    hp.run_compositor(hpath, out, fn, input_linear=True, output_linear=True, sixteen=sixteen)
    h1 = hp.load(out)[..., 0]
    res[f'height_through_kuwahara_{label}_distinct_values'] = int(len(np.unique(np.round(h1 * 65535))))
res['height_source_16bit_distinct_values'] = int(len(np.unique(np.round(h0 * 65535))))
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c09_compositor_details.json'), 'w'), indent=1)
print(json.dumps(res, indent=1)[:4000])
