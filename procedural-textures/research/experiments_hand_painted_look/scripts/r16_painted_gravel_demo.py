# What this does: a bake_harness recipe that tries the stone-painting tools on the GRAVEL reference: a speckled earth layer, a layer of small stones and a layer of
# big stones, each stone a Voronoi cell with a dark rim (Distance To Edge) and flat facet patches inside (second set of cells, own seed per stone). Height = lightness of the colour.
# parameters: 'layers' 1..3 (how many of earth / small stones / big stones are drawn), 'facets' 0/1.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hp_tools as hp  # noqa: E402
import recipe_tools as rt  # noqa: E402

DEFAULTS = {'layers': 3, 'facets': 1, 'seed': 0.0, 'earth_scale': 48.0, 'scales': [17.0, 6.0], 'coverage': [0.60, 0.45], 'rim_px': [2.5, 4.0], 'facet_scale': [2.0, 2.5], 'value_jitter': 0.0, 'grain': 0.0}
SIZE_PX = 1254.0
EARTH = [('#422f22', 25.0), ('#5a3c28', 40.0), ('#7a5940', 35.0)]
STONES = [('#171617', 22.0), ('#26282b', 22.0), ('#373b3f', 18.0), ('#4e5457', 14.0), ('#6b6f6e', 8.0), ('#5a3c28', 8.0), ('#7a5940', 8.0)]


def build_node_group(parameters):
    p = {**DEFAULTS, **parameters}
    tree, w = hp.new_group('painted gravel demo', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor'), ('Height', 'NodeSocketFloat')])
    hp.instance(w, hp.warp_vector_group('gravel warp'), 'warp', x=0, Amount=0.005, Scale=60.0, Seed=p['seed'] + 3.0); w.link('in', 'Vector', 'warp', 'Vector')
    # earth: tiny flat dabs
    hp.instance(w, hp.anisotropic_noise_group('earth cells', cells=True), 'earth', x=1, y=0, **{'Scale__U': float(p['earth_scale']), 'Scale__V': float(p['earth_scale']), 'Randomness': 1.0, 'Seed': p['seed']})
    w.link('warp', 'Vector', 'earth', 'Vector')
    hp.cell_random(w, 'earth pick', 'earth', 'Color', 1.0, x=2); hp.palette_ramp(w, 'earth palette', EARTH, x=3); w.link('earth pick', 'Value', 'earth palette', 'Fac')
    colour = ('earth palette', 'Color')

    def jitter(label, id_node, id_socket, seed):
        """small brightness change per patch (Hue/Saturation node, Value input 1 +- value_jitter / 2) on the colour that `colour` points to"""
        nonlocal colour
        if float(p['value_jitter']) <= 0:
            return
        hp.cell_random(w, f'{label} jit rand', id_node, id_socket, seed, x=12, y=-9)
        w.math(f'{label} jit value', 'MULTIPLY_ADD', None, float(p['value_jitter']), 1.0 - float(p['value_jitter']) / 2, x=13, y=-9); w.link(f'{label} jit rand', 'Value', f'{label} jit value', 0)
        w.add('ShaderNodeHueSaturation', f'{label} jit', x=14, y=-9); w.link(f'{label} jit value', 0, f'{label} jit', 'Value'); w.link(*colour, f'{label} jit', 'Color')
        colour = (f'{label} jit', 'Color')

    jitter('earth', 'earth', 'Color', 77.0)

    def stone_layer(index, scale, coverage, rim_px, seed, facet_scale):
        nonlocal colour
        n = f'L{index}'
        hp.instance(w, hp.anisotropic_noise_group(f'{n} stones', cells=True), f'{n} stone', x=4, y=-4 * index, **{'Scale__U': scale, 'Scale__V': scale, 'Randomness': 0.9, 'Seed': seed})
        w.link('warp', 'Vector', f'{n} stone', 'Vector')
        hp.instance(w, hp.anisotropic_noise_group(f'{n} rim', cells=True, feature='DISTANCE_TO_EDGE'), f'{n} rim', x=4, y=-4 * index - 2, **{'Scale__U': scale, 'Scale__V': scale, 'Randomness': 0.9, 'Seed': seed})
        w.link('warp', 'Vector', f'{n} rim', 'Vector')
        hp.cell_random(w, f'{n} id', f'{n} stone', 'Color', 2.0 + index, x=5, y=-4 * index)
        hp.cell_random(w, f'{n} cover', f'{n} stone', 'Color', 50.0 + index, x=5, y=-4 * index - 1)
        w.math(f'{n} cover mask', 'LESS_THAN', None, coverage, x=6, y=-4 * index - 1); w.link(f'{n} cover', 'Value', f'{n} cover mask', 0)
        tone_socket = (f'{n} id', 'Value')
        if int(p['facets']):
            w.math(f'{n} facet seed', 'MULTIPLY', None, 50.0, x=6, y=-4 * index); w.link(f'{n} id', 'Value', f'{n} facet seed', 0)
            hp.instance(w, hp.anisotropic_noise_group(f'{n} facets', cells=True, distance='CHEBYCHEV'), f'{n} facets', x=7, y=-4 * index, **{'Scale__U': scale * facet_scale, 'Scale__V': scale * facet_scale, 'Randomness': 1.0})
            w.link('warp', 'Vector', f'{n} facets', 'Vector'); w.link(f'{n} facet seed', 0, f'{n} facets', 'Seed')
            hp.cell_random(w, f'{n} facet rand', f'{n} facets', 'Color', 7.0, x=8, y=-4 * index)
            w.math(f'{n} facet offset', 'MULTIPLY_ADD', None, 0.45, -0.225, x=9, y=-4 * index); w.link(f'{n} facet rand', 'Value', f'{n} facet offset', 0)
            w.math(f'{n} tone', 'ADD', x=10, y=-4 * index, clamp=True); w.link(f'{n} id', 'Value', f'{n} tone', 0); w.link(f'{n} facet offset', 0, f'{n} tone', 1)
            tone_socket = (f'{n} tone', 0)
        hp.palette_ramp(w, f'{n} palette', STONES, x=11, y=-4 * index); w.link(*tone_socket, f'{n} palette', 'Fac')
        stone_colour = (f'{n} palette', 'Color')
        if float(p['value_jitter']) > 0:
            hp.cell_random(w, f'{n} jit rand', f'{n} stone', 'Color', 90.0 + index, x=11, y=-4 * index - 3)
            w.math(f'{n} jit value', 'MULTIPLY_ADD', None, float(p['value_jitter']), 1.0 - float(p['value_jitter']) / 2, x=12, y=-4 * index - 3); w.link(f'{n} jit rand', 'Value', f'{n} jit value', 0)
            w.add('ShaderNodeHueSaturation', f'{n} jit', x=12, y=-4 * index - 2); w.link(f'{n} jit value', 0, f'{n} jit', 'Value'); w.link(*stone_colour, f'{n} jit', 'Color')
            stone_colour = (f'{n} jit', 'Color')
        w.add('ShaderNodeMix', f'{n} place', x=12, y=-4 * index, data_type='RGBA', blend_type='MIX')
        w.link(f'{n} cover mask', 0, f'{n} place', 'Factor'); w.link(*colour, f'{n} place', 'A'); w.link(*stone_colour, f'{n} place', 'B')
        colour = (f'{n} place', 'Result')
        # dark rim only on covered stones
        w.math(f'{n} rim width', 'LESS_THAN', None, 0.5 * rim_px * scale / SIZE_PX, x=6, y=-4 * index - 2); w.link(f'{n} rim', 'Distance', f'{n} rim width', 0)
        w.math(f'{n} rim mask', 'MULTIPLY', x=7, y=-4 * index - 2); w.link(f'{n} rim width', 0, f'{n} rim mask', 0); w.link(f'{n} cover mask', 0, f'{n} rim mask', 1)
        w.add('ShaderNodeMix', f'{n} rim paint', x=13, y=-4 * index, data_type='RGBA', blend_type='MIX')
        w.link(f'{n} rim mask', 0, f'{n} rim paint', 'Factor'); w.link(*colour, f'{n} rim paint', 'A'); w.nodes[f'{n} rim paint'].inputs['B'].default_value = (*hp.srgb_hex_to_linear('#0a0a0b'), 1.0)
        colour = (f'{n} rim paint', 'Result')

    for index in range(1, int(p['layers'])):
        k = index - 1
        stone_layer(index, float(p['scales'][k]), float(p['coverage'][k]), float(p['rim_px'][k]), p['seed'] + 31.0 * index, float(p['facet_scale'][k]))
    if float(p['grain']) > 0:
        hp.instance(w, rt.tileable_noise_group(), 'grain noise', x=15, y=-10, Scale=130.0, Detail=2.0, Seed=p['seed'] + 5.0); w.link('in', 'Vector', 'grain noise', 'Vector')
        w.add('ShaderNodeMapRange', 'grain factor', x=15, y=-11, clamp=True); w.nodes['grain factor'].inputs['From Min'].default_value = 0.3; w.nodes['grain factor'].inputs['From Max'].default_value = 0.7
        w.nodes['grain factor'].inputs['To Min'].default_value = 1.0 - float(p['grain']); w.nodes['grain factor'].inputs['To Max'].default_value = 1.0 + float(p['grain'])
        w.link('grain noise', 'Fac', 'grain factor', 'Value')
        w.add('ShaderNodeMix', 'grain mix', x=16, y=-10, data_type='RGBA', blend_type='MULTIPLY'); w.nodes['grain mix'].inputs['Factor'].default_value = 1.0
        w.link(*colour, 'grain mix', 'A'); w.link('grain factor', 'Result', 'grain mix', 'B')
        colour = ('grain mix', 'Result')
    w.add('ShaderNodeRGBToBW', 'luma', x=16, y=-8); w.link(*colour, 'luma', 'Color')
    w.math('encoded', 'POWER', None, 1.0 / 2.2, x=17, y=-8); w.link('luma', 'Val', 'encoded', 0)
    w.math('height', 'MULTIPLY', None, 1.0 / 0.50, x=18, y=-8, clamp=True); w.link('encoded', 0, 'height', 0)
    w.link(*colour, 'out', 'Colour'); w.link('height', 0, 'out', 'Height')
    return tree
