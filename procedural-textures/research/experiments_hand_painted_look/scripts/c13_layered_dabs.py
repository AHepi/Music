# What this does: tests "painting in layers": an underpainting of big cells, then several layers of smaller cells that only cover part of the picture
# (a per-cell yes/no), each with its own palette picks. Same trick the Blender Artists "NPR skin shader" breakdown describes (one Voronoi, different W for each
# layer). Sweeps: number of layers, coverage of each layer, stretch of the layers. All layers use the seamless cells, so the tile still repeats.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp, recipe_tools as rt
BASE = os.path.join(hp.OUT, 'pictures')
hp.SAMPLES = 4

def layered(layers=3, coverage=0.5, base_scale=5.0, growth=1.8, stretch=1.0, warp_fine=0.004, warp_coarse=0.015, palette=hp.BRICK_PALETTE, name='layers'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    hp.instance(w, hp.warp_vector_group(name + ' coarse'), 'warp a', x=0, Amount=warp_coarse, Scale=4.0, Seed=1.0); w.link('in', 'Vector', 'warp a', 'Vector')
    hp.instance(w, hp.warp_vector_group(name + ' fine'), 'warp b', x=1, Amount=warp_fine, Scale=70.0, Seed=2.0); w.link('warp a', 'Vector', 'warp b', 'Vector')
    colour = None
    for k in range(layers):
        scale = base_scale * (growth ** k)
        hp.instance(w, hp.anisotropic_noise_group(f'{name} cells {k}', cells=True), f'cells{k}', x=2, y=-4 * k, **{'Scale__U': scale, 'Scale__V': scale / stretch, 'Seed': 17.0 * k})
        w.link('warp b', 'Vector', f'cells{k}', 'Vector')
        hp.cell_random(w, f'pick{k}', f'cells{k}', 'Color', 3.0 + k, x=3, y=-4 * k)
        node = hp.palette_ramp(w, f'palette{k}', palette, x=4, y=-4 * k); w.link(f'pick{k}', 'Value', f'palette{k}', 'Fac')
        if colour is None:
            colour = (f'palette{k}', 'Color'); continue
        hp.cell_random(w, f'cover{k}', f'cells{k}', 'Color', 40.0 + k, x=3, y=-4 * k - 1)
        w.math(f'mask{k}', 'LESS_THAN', None, coverage, x=5, y=-4 * k - 1); w.link(f'cover{k}', 'Value', f'mask{k}', 0)
        w.add('ShaderNodeMix', f'over{k}', x=6, y=-4 * k, data_type='RGBA', blend_type='MIX')
        w.link(f'mask{k}', 0, f'over{k}', 'Factor'); w.link(*colour, f'over{k}', 'A'); w.link(f'palette{k}', 'Color', f'over{k}', 'B')
        colour = (f'over{k}', 'Result')
    w.link(*colour, 'out', 'Colour')
    return tree

vals = [1, 2, 3, 4, 5]
hp.sweep(lambda n: layered(layers=n, name=f'ly{n}'), vals, os.path.join(BASE, 'c13_layers_count'), labels=[f'{n} layer{"s" if n > 1 else ""}' for n in vals], size=320, title='Layered dabs: number of layers (coverage 0.5, each layer 1.8 x finer)', cell=240)
cv = [0.15, 0.3, 0.5, 0.7, 0.9]
hp.sweep(lambda c: layered(layers=4, coverage=c, name=f'cv{c}'), cv, os.path.join(BASE, 'c13_layers_coverage'), labels=[f'coverage {c}' for c in cv], size=320, title='Layered dabs: how much of the picture each top layer covers (4 layers)', cell=240)
sv = [0.5, 1.0, 2.0, 4.0, 8.0]
hp.sweep(lambda s: layered(layers=4, stretch=s, name=f'sx{s}'), sv, os.path.join(BASE, 'c13_layers_stretch'), labels=[f'stretch x{s} (long in v)' for s in sv], size=320, title='Layered dabs: stretching the cells (stretch > 1 = long in the up direction)', cell=240)
print(json.dumps(hp.periodicity_check(lambda: layered(layers=4, stretch=2.0, name='pcheck'), 'Colour', 192)))
