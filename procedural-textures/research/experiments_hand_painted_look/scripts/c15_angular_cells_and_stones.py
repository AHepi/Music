# What this does: (1) shows how the Voronoi distance metric (Euclidean, Manhattan, Chebychev, Minkowski) and Randomness change the SHAPE of paint patches
# (round blobs vs angular chunks like cut stones), checking the tile still repeats; (2) builds a two-level "painted stone" test: big stone cells with a dark
# rim, and inside each stone a second set of facet cells (its own random pattern per stone) painted in flat tones, to see how far plain nodes get towards
# the gravel reference look.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp, recipe_tools as rt
BASE = os.path.join(hp.OUT, 'pictures')
hp.SAMPLES = 4
GRAVEL = [('#171617', 16.8), ('#26282b', 18.2), ('#373b3f', 14.3), ('#4e5457', 11.4), ('#6b6f6e', 8.1), ('#422f22', 9.8), ('#5a3c28', 13.8), ('#7a5940', 7.6)]

def metric_cells(distance, exponent, randomness, name, scale=9.0, warp=0.004):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    hp.instance(w, hp.warp_vector_group(name + ' warp'), 'warp', x=0, Amount=warp, Scale=60.0); w.link('in', 'Vector', 'warp', 'Vector')
    hp.instance(w, hp.anisotropic_noise_group(name + ' cells', cells=True, distance=distance, exponent=exponent), 'cells', x=1, **{'Scale__U': scale, 'Scale__V': scale, 'Randomness': randomness})
    w.link('warp', 'Vector', 'cells', 'Vector')
    hp.cell_random(w, 'pick', 'cells', 'Color', 0.0, x=2); hp.palette_ramp(w, 'palette', GRAVEL, x=3); w.link('pick', 'Value', 'palette', 'Fac'); w.link('palette', 'Color', 'out', 'Colour')
    return tree
metrics = [('EUCLIDEAN', None, 'Euclidean'), ('MANHATTAN', None, 'Manhattan'), ('CHEBYCHEV', None, 'Chebychev'), ('MINKOWSKI', 0.5, 'Minkowski 0.5'), ('MINKOWSKI', 1.5, 'Minkowski 1.5'), ('MINKOWSKI', 4.0, 'Minkowski 4')]
hp.sweep(lambda i: metric_cells(metrics[i][0], metrics[i][1], 1.0, f'm{i}'), list(range(len(metrics))), os.path.join(BASE, 'c15_distance_metric'), labels=[m[2] for m in metrics], size=300, title='Voronoi Distance metric (Randomness 1)', cell=230)
rv = [0.0, 0.3, 0.6, 0.8, 1.0]
hp.sweep(lambda r: metric_cells('CHEBYCHEV', None, r, f'cr{r}'), rv, os.path.join(BASE, 'c15_chebychev_randomness'), labels=[f'Chebychev, Randomness {r}' for r in rv], size=300, title='Angular cells: Chebychev metric, Randomness', cell=230)
period = {}
for d, e in (('MANHATTAN', None), ('CHEBYCHEV', None), ('MINKOWSKI', 1.5)):
    period[d + str(e)] = hp.periodicity_check(lambda: metric_cells(d, e, 1.0, 'pc'), 'Colour', 192)
    print('periodicity', d, e, period[d + str(e)])

# 2) painted stones: stones with rims, facets inside
def stones(name='stones', stone_scale=8.0, facet_scale=3.0, rim_px=3.0, size=640, facet_metric='CHEBYCHEV'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    hp.instance(w, hp.warp_vector_group(name + ' warp'), 'warp', x=0, Amount=0.006, Scale=50.0, Seed=3.0); w.link('in', 'Vector', 'warp', 'Vector')
    hp.instance(w, hp.anisotropic_noise_group(name + ' stones', cells=True, distance='EUCLIDEAN'), 'stone', x=1, **{'Scale__U': stone_scale, 'Scale__V': stone_scale, 'Randomness': 0.9})
    w.link('warp', 'Vector', 'stone', 'Vector')
    hp.instance(w, hp.anisotropic_noise_group(name + ' rim', cells=True, feature='DISTANCE_TO_EDGE'), 'rim', x=1, y=-3, **{'Scale__U': stone_scale, 'Scale__V': stone_scale, 'Randomness': 0.9})
    w.link('warp', 'Vector', 'rim', 'Vector')
    hp.cell_random(w, 'stone id', 'stone', 'Color', 0.0, x=2)
    # a different seed (W) for the facets of every stone: seed = stone id x 50
    w.math('facet seed', 'MULTIPLY', None, 50.0, x=3, y=-2); w.link('stone id', 'Value', 'facet seed', 0)
    hp.instance(w, hp.anisotropic_noise_group(name + ' facets', cells=True, distance=facet_metric), 'facets', x=4, y=-2, **{'Scale__U': facet_scale * stone_scale, 'Scale__V': facet_scale * stone_scale, 'Randomness': 1.0})
    w.link('warp', 'Vector', 'facets', 'Vector'); w.link('facet seed', 0, 'facets', 'Seed')
    hp.cell_random(w, 'facet rand', 'facets', 'Color', 7.0, x=5, y=-2)
    # stone tone: dark/blue-grey/brown family by stone id; facet adds +-0.25 steps
    w.math('facet offset', 'MULTIPLY_ADD', None, 0.5, -0.25, x=6, y=-2); w.link('facet rand', 'Value', 'facet offset', 0)
    w.math('tone', 'ADD', x=7, y=-1, clamp=True); w.link('stone id', 'Value', 'tone', 0); w.link('facet offset', 0, 'tone', 1)
    hp.palette_ramp(w, 'palette', GRAVEL, x=8, y=-1); w.link('tone', 0, 'palette', 'Fac')
    w.math('rim mask', 'LESS_THAN', None, 0.5 * rim_px * stone_scale / size, x=3, y=-3); w.link('rim', 'Distance', 'rim mask', 0)
    w.add('ShaderNodeMix', 'paint', x=9, data_type='RGBA', blend_type='MIX'); w.link('rim mask', 0, 'paint', 'Factor'); w.link('palette', 'Color', 'paint', 'A')
    w.nodes['paint'].inputs['B'].default_value = (*hp.srgb_hex_to_linear('#0b0b0c'), 1.0)
    w.link('paint', 'Result', 'out', 'Colour')
    return tree
hp.sweep(lambda i: stones(f'st{i}', facet_scale=[1.0, 2.0, 3.0, 4.0][i]), list(range(4)), os.path.join(BASE, 'c15_painted_stones_facets'), labels=[f'facets per stone ~{[1,2,3,4][i]}x' for i in range(4)], size=320, title='Painted stones: facet cells inside every stone (Chebychev), dark rim', cell=240)
hp.photograph_group(lambda: stones('stbig', stone_scale=8.0, facet_scale=2.5, size=1254, rim_px=4.0), 'Colour', os.path.join(BASE, 'c15_painted_stones_1254.png'), 1254)
period['stones'] = hp.periodicity_check(lambda: stones('stp', size=192), 'Colour', 192)
print('periodicity stones', period['stones'])
json.dump(period, open(os.path.join(hp.OUT, 'data', 'c15_periodicity.json'), 'w'), indent=1)
