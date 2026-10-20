# What this does: tests Voronoi cells as flat paint patches (random colour per cell, palette colour per cell, small hue/value change per cell) and
# domain warping (pushing the coordinate around with seamless noise before the cells or noise read it), with sweeps of every setting. It also checks that the
# tile still wraps (seam ratio near 1.0) and prints the numbers. Pictures go to ../pictures/c02_*/ and ../pictures/c03_*/.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

BASE = os.path.join(hp.OUT, 'pictures')
seams = {}

def cells_colour(kind='palette', scale=6.0, randomness=1.0, warp_amount=0.0, warp_scale=3.0, hue_jitter=0.0, value_jitter=0.0, palette=hp.BRICK_PALETTE, name='cells'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    src = 'in'; src_socket = 'Vector'
    if warp_amount > 0:
        hp.instance(w, hp.warp_vector_group(), 'warp', x=0, Amount=warp_amount, Scale=warp_scale)
        w.link('in', 'Vector', 'warp', 'Vector'); src, src_socket = 'warp', 'Vector'
    hp.instance(w, rt.tileable_voronoi_group(), 'cells', x=1, Scale=scale, Randomness=randomness)
    w.link(src, src_socket, 'cells', 'Vector')
    if kind == 'raw':
        w.link('cells', 'Color', 'out', 'Colour'); return tree
    hp.cell_random(w, 'rand pick', 'cells', 'Color', seed=0.0, x=2)
    hp.palette_ramp(w, 'palette', palette, x=3)
    w.link('rand pick', 'Value', 'palette', 'Fac')
    last = ('palette', 'Color')
    if hue_jitter > 0 or value_jitter > 0:
        hp.cell_random(w, 'rand hue', 'cells', 'Color', seed=11.0, x=2, y=-2)
        hp.cell_random(w, 'rand val', 'cells', 'Color', seed=23.0, x=2, y=-3)
        w.math('hue amount', 'MULTIPLY_ADD', None, hue_jitter, 0.5, x=3, y=-2)   # (rand - 0.5) * jitter + 0.5 below
        # (rand * jitter) + (0.5 - jitter/2)
        w.nodes['hue amount'].inputs[0].default_value = 0.0
        w.nodes['hue amount'].inputs[1].default_value = hue_jitter
        w.nodes['hue amount'].inputs[2].default_value = 0.5 - hue_jitter / 2
        w.link('rand hue', 'Value', 'hue amount', 0)
        w.math('val amount', 'MULTIPLY_ADD', x=3, y=-3)
        w.nodes['val amount'].inputs[1].default_value = value_jitter
        w.nodes['val amount'].inputs[2].default_value = 1.0 - value_jitter / 2
        w.link('rand val', 'Value', 'val amount', 0)
        w.add('ShaderNodeHueSaturation', 'hsv', x=4)
        w.link('hue amount', 0, 'hsv', 'Hue'); w.link('val amount', 0, 'hsv', 'Value')
        w.link('palette', 'Color', 'hsv', 'Color')
        last = ('hsv', 'Color')
    w.link(last[0], last[1], 'out', 'Colour')
    return tree

hp.SAMPLES = 4
# 1) Voronoi: raw colour vs palette vs palette + jitter
hp.sweep(lambda v: cells_colour(*v[0], **v[1]) if False else None, [0], os.path.join(BASE, 'c02_dummy'), size=8) if False else None
variants = [('raw Voronoi Color', dict(kind='raw')), ('palette per cell', dict(kind='palette')), ('palette + hue/value jitter', dict(kind='palette', hue_jitter=0.04, value_jitter=0.35)),
            ('+ scale 12', dict(kind='palette', scale=12, hue_jitter=0.04, value_jitter=0.35)), ('+ warp 0.04', dict(kind='palette', warp_amount=0.04, hue_jitter=0.04, value_jitter=0.35))]
arrays = hp.sweep(lambda i: cells_colour(**variants[i][1], name=f'v{i}'), list(range(len(variants))), os.path.join(BASE, 'c02_cells_as_paint'), labels=[v[0] for v in variants], size=384, title='Voronoi cells as paint patches', cell=300)
for (label, _), a in zip(variants, arrays): seams[label] = hp.seam_ratio_of(a)
# 2) Randomness sweep
vals = [0.0, 0.25, 0.5, 0.75, 1.0]
arrays = hp.sweep(lambda r: cells_colour(randomness=r, hue_jitter=0.04, value_jitter=0.35, name=f'r{r}'), vals, os.path.join(BASE, 'c02_randomness'), labels=[f'Randomness {v}' for v in vals], size=320, title='Voronoi Randomness (palette per cell)', cell=240)
for v, a in zip(vals, arrays): seams[f'randomness {v}'] = hp.seam_ratio_of(a)
# 3) Scale sweep
vals = [3, 6, 10, 16, 24]
arrays = hp.sweep(lambda s: cells_colour(scale=s, hue_jitter=0.04, value_jitter=0.35, name=f's{s}'), vals, os.path.join(BASE, 'c02_scale'), labels=[f'Scale {v}' for v in vals], size=320, title='Voronoi Scale = cells across one tile', cell=240)
# 4) Domain warp amount (coarse warp)
vals = [0.0, 0.01, 0.03, 0.06, 0.1, 0.18]
arrays = hp.sweep(lambda a: cells_colour(scale=6, warp_amount=a, warp_scale=3, hue_jitter=0.04, value_jitter=0.35, name=f'wa{a}'), vals, os.path.join(BASE, 'c03_warp_amount'), labels=[f'Warp Amount {v}' for v in vals], size=320, title='Domain warp: Amount (warp noise Scale 3)', cell=240)
for v, a in zip(vals, arrays): seams[f'warp amount {v}'] = hp.seam_ratio_of(a)
# 5) Warp noise scale at fixed amount
vals = [1, 2, 4, 8, 16, 32]
arrays = hp.sweep(lambda s: cells_colour(scale=6, warp_amount=0.05, warp_scale=s, hue_jitter=0.04, value_jitter=0.35, name=f'ws{s}'), vals, os.path.join(BASE, 'c03_warp_scale'), labels=[f'Warp Scale {v}' for v in vals], size=320, title='Domain warp: Scale of the warp noise (Amount 0.05)', cell=240)
# 6) ragged edges: fine warp small amount
vals = [0.0, 0.003, 0.006, 0.01, 0.016, 0.025]
arrays = hp.sweep(lambda a: cells_colour(scale=6, warp_amount=a, warp_scale=48, hue_jitter=0.04, value_jitter=0.35, name=f'wr{a}'), vals, os.path.join(BASE, 'c03_ragged_edges'), labels=[f'Amount {v}' for v in vals], size=320, title='Ragged paint edges: fine warp (Scale 48), small Amount', cell=240)
for v, a in zip(vals, arrays): seams[f'ragged {v}'] = hp.seam_ratio_of(a)
json.dump(seams, open(os.path.join(hp.OUT, 'data', 'c02_c03_seam_ratios.json'), 'w'), indent=1)
print('seam ratios (1.0 = seamless; flat-patch pictures are noisy under this measure):', json.dumps({k: round(v, 2) for k, v in seams.items()}))
# the strict test: does the picture at 1..2 equal the picture at 0..1?
period = {}
def negative_control():
    tree, w = hp.new_group('plain blender noise', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeTexNoise', 'n', x=0, Scale=6.0); w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Color', 'out', 'Colour'); return tree
period['negative control: plain Blender Noise'] = hp.periodicity_check(negative_control, 'Colour', 192)
period['cells with palette'] = hp.periodicity_check(lambda: cells_colour(), 'Colour', 192)
period['cells + hue/value jitter'] = hp.periodicity_check(lambda: cells_colour(hue_jitter=0.04, value_jitter=0.35), 'Colour', 192)
period['cells + warp 0.1 (scale 3)'] = hp.periodicity_check(lambda: cells_colour(warp_amount=0.1, warp_scale=3), 'Colour', 192)
period['cells + ragged warp 0.01 (scale 48)'] = hp.periodicity_check(lambda: cells_colour(warp_amount=0.01, warp_scale=48), 'Colour', 192)
for k, v in period.items(): print('periodicity', k, {a: round(b, 4) for a, b in v.items()})
json.dump(period, open(os.path.join(hp.OUT, 'data', 'c02_c03_periodicity.json'), 'w'), indent=1)
