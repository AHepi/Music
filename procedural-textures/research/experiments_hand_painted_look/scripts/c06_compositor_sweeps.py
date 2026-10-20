# What this does: makes a "crumbly" colour picture (soft fractal noise through a brick palette: lots of fine colour detail, no flat patches) and pushes it
# through each stylising compositor node with sweeps of every setting, so we can see what each setting does. Source baked at 1254 x 1254 like the real maps;
# the sweep pictures keep a 420 x 420 crop. Timings are printed (CPU compositor, 2 threads).
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

BASE = os.path.join(hp.OUT, 'pictures', 'c06_compositor')
os.makedirs(BASE, exist_ok=True)
SIZE = 1254
SRC = os.path.join(BASE, 'source_grainy.png')
hp.SAMPLES = 4

def crumbly():
    """Grainy cells: flat-coloured Voronoi cells (brick palette, wobbly edges) covered with fine grain and a soft large-scale shading. This is the 'before':
    a picture with hard patch edges AND lots of fine detail that a painter would leave out."""
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
t0 = time.time()
hp.photograph_group(crumbly, 'Colour', SRC, SIZE)
print('baked source in %.1fs' % (time.time() - t0))

CROP = (420, 420, 420)   # y0, x0, size : crop shown in the strips
def run(label, folder, make, **kw):
    out = os.path.join(BASE, folder); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, label + '.png')
    t = time.time()
    hp.run_compositor(SRC, path, make, **kw)
    return time.time() - t, path

def kuwa(kind, **inputs):
    def make(tree, image, extras):
        n = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(image.outputs['Image'], n.inputs['Image']); hp.set_menu(n, 'Type', kind)
        for k, v in inputs.items(): n.inputs[k.replace('__', ' ')].default_value = v
        return n.outputs['Image']
    return make
timings = {}
manifest = {}
def sweep(folder, name, items):
    manifest[folder] = []
    for label, make in items:
        secs, path = run(label.replace(' ', '_').replace('=', ''), folder, make)
        timings[f'{folder}/{label}'] = round(secs, 2)
        manifest[folder].append({'label': label, 'file': os.path.basename(path)})
        print(folder, label, round(secs, 2), 's', flush=True)

sweep('classic_size', 'Kuwahara Classic: Size', [(f'Classic Size {s}', kuwa('Classic', Size=float(s))) for s in (1, 2, 3, 5, 8, 12)])
sweep('classic_precision', 'Classic: High Precision', [('Classic Size 8 off', kuwa('Classic', Size=8.0)), ('Classic Size 8 High Precision', kuwa('Classic', Size=8.0, High__Precision=True))])
sweep('aniso_size', 'Anisotropic: Size', [(f'Aniso Size {s}', kuwa('Anisotropic', Size=float(s))) for s in (2, 4, 6, 8, 12, 16)])
sweep('aniso_uniformity', 'Anisotropic: Uniformity', [(f'Uniformity {u}', kuwa('Anisotropic', Size=8.0, Uniformity=u)) for u in (0, 1, 2, 4, 8, 16)])
sweep('aniso_sharpness', 'Anisotropic: Sharpness', [(f'Sharpness {s}', kuwa('Anisotropic', Size=8.0, Sharpness=s)) for s in (0.0, 0.25, 0.5, 1.0)])
sweep('aniso_eccentricity', 'Anisotropic: Eccentricity', [(f'Eccentricity {e}', kuwa('Anisotropic', Size=8.0, Eccentricity=e)) for e in (0.0, 0.5, 1.0, 2.0, 3.0)])

def chain(n, kind='Anisotropic', size=6.0):
    def make(tree, image, extras):
        last = image.outputs['Image']
        for i in range(n):
            k = tree.nodes.new('CompositorNodeKuwahara'); tree.links.new(last, k.inputs['Image']); hp.set_menu(k, 'Type', kind); k.inputs['Size'].default_value = size; last = k.outputs['Image']
        return last
    return make
sweep('aniso_iterations', 'Anisotropic: chained passes', [(f'Aniso Size 6 x{n}', chain(n)) for n in (1, 2, 3, 4)])
sweep('classic_iterations', 'Classic: chained passes', [(f'Classic Size 4 x{n}', chain(n, 'Classic', 4.0)) for n in (1, 2, 3, 4)])

def simple(node_type, in_name, out_name, **inputs):
    def make(tree, image, extras):
        n = tree.nodes.new(node_type); tree.links.new(image.outputs['Image'], n.inputs[in_name])
        for k, v in inputs.items():
            if k.startswith('menu_'): hp.set_menu(n, k[5:].replace('__', ' '), v)
            else: n.inputs[k.replace('__', ' ')].default_value = v
        return n.outputs[out_name]
    return make
sweep('posterize', 'Posterize', [(f'Posterize Steps {s}', simple('CompositorNodePosterize', 'Image', 'Image', Steps=float(s))) for s in (2, 3, 4, 6, 8, 16)])
sweep('pixelate', 'Pixelate', [(f'Pixelate Size {s}', simple('CompositorNodePixelate', 'Color', 'Color', Size=s)) for s in (1, 2, 4, 8, 16, 32)])
sweep('bilateral', 'Bilateral Blur', [(f'Bilateral Size {s} Thr {t}', simple('CompositorNodeBilateralblur', 'Image', 'Image', Size=s, Threshold=t)) for s, t in ((4, 0.1), (8, 0.1), (8, 0.3), (16, 0.1), (16, 0.5))])
sweep('blur_types', 'Blur node types (Size 6)', [(f'Blur {t}', simple('CompositorNodeBlur', 'Image', 'Image', menu_Type=t, Size=(6.0, 6.0))) for t in ('Flat', 'Tent', 'Gaussian', 'Fast Gaussian')])
sweep('filter_types', 'Filter node types', [(f'Filter {t}', simple('CompositorNodeFilter', 'Image', 'Image', menu_Type=t)) for t in ('Soften', 'Box Sharpen', 'Diamond Sharpen', 'Laplace', 'Sobel', 'Prewitt', 'Kirsch', 'Shadow')])
sweep('despeckle', 'Despeckle', [(f'Despeckle ct {c}', simple('CompositorNodeDespeckle', 'Image', 'Image', Color__Threshold=c, Neighbor__Threshold=0.5)) for c in (0.05, 0.2, 0.5)])
json.dump({'timings_seconds_at_1254': timings, 'manifest': manifest}, open(os.path.join(hp.OUT, 'data', 'c06_compositor_sweeps.json'), 'w'), indent=1)
