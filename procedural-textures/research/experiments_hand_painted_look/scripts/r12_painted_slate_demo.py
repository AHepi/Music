# What this does: a small "painted slate" recipe built ONLY to show, stage by stage, what each stylising control adds (and to score it against the
# slate reference). It is a bake_harness recipe: build_node_group(parameters) returns a shader node group with input 'Vector' and outputs 'Colour' and 'Height'.
# parameters['stage'] 0..4 switches the stylising controls on one after the other:
#   0 plain: slate tiles in rows, one soft colour per tile + soft noise shading (the usual "procedural default")
#   1 + painted patches: tall stretched cells (drips) with a palette colour per cell, flat colours, hard edges
#   2 + ragged edges: domain warp (coarse and fine) on the patch coordinates
#   3 + outlines: dark core line under each tile, a lighter shadow band, dark gaps between tiles, a bright lip
#   4 + stains: olive moss patches and tan chips with hard edges
# Height = the lightness of the finished colour (the reference's maps were made the same way).
# Not a final slate recipe: tile widths do not vary, there are no chips on the edges; it is a test bench for the stylising controls.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hp_tools as hp  # noqa: E402
import recipe_tools as rt  # noqa: E402

ROWS = 8
COLUMNS = 6
SIZE_PX = 1254.0
DEFAULTS = {'stage': 4, 'seed': 0.0, 'drip_u': 34.0, 'drip_v': 5.0, 'drip_amount': 0.75}
OUTLINE_CORE = '#0e0f11'
OUTLINE_SHADOW = '#1e2022'
LIP = '#6d6c67'
OLIVE_DARK = '#3a3c31'
OLIVE_LIGHT = '#4f4e40'
TAN = '#6d6c67'
SLATE_TONES = [('#1e2022', 9.8), ('#2d3133', 15.9), ('#3a4045', 28.7), ('#4a5254', 20.7), ('#6d6c67', 3.8)]     # without the darkest outline colour and without olive


def hex_rgba(hex_text):
    return (*hp.srgb_hex_to_linear(hex_text), 1.0)


def build_node_group(parameters):
    p = {**DEFAULTS, **parameters}
    stage = int(p['stage'])
    tree, w = hp.new_group('painted slate demo', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor'), ('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'uv', x=0); w.link('in', 'Vector', 'uv', 'Vector')
    # ---- layout: row, row shift, tile number, position inside the tile
    # the layout is pushed up half a row so that the wrap-around edge of the tile lies in the middle of a row, not on a row boundary
    w.math('v rows', 'MULTIPLY_ADD', None, float(ROWS), 0.5, x=1, y=-1); w.link('uv', 'Y', 'v rows', 0)
    w.math('row', 'FLOOR', x=2, y=-1); w.link('v rows', 0, 'row', 0)
    w.math('vf', 'SUBTRACT', x=2, y=-2); w.link('v rows', 0, 'vf', 0); w.link('row', 0, 'vf', 1)
    w.math('row mod', 'MODULO', None, float(ROWS), x=2, y=-3); w.link('row', 0, 'row mod', 0)           # row 8 is row 0 again
    w.add('ShaderNodeCombineXYZ', 'row key', x=3, y=-1, Y=7.7); w.link('row mod', 0, 'row key', 'X')
    w.add('ShaderNodeTexWhiteNoise', 'row shift', x=4, y=-1, noise_dimensions='3D'); w.link('row key', 'Vector', 'row shift', 'Vector')
    w.math('u cols', 'MULTIPLY', None, float(COLUMNS), x=1, y=0); w.link('uv', 'X', 'u cols', 0)
    w.math('ur', 'ADD', x=5, y=0); w.link('u cols', 0, 'ur', 0); w.link('row shift', 'Value', 'ur', 1)
    w.math('tile i', 'FLOOR', x=6, y=0); w.link('ur', 0, 'tile i', 0)
    w.math('uf', 'SUBTRACT', x=6, y=1); w.link('ur', 0, 'uf', 0); w.link('tile i', 0, 'uf', 1)
    w.math('tile key', 'MODULO', None, float(COLUMNS), x=7, y=0); w.link('tile i', 0, 'tile key', 0)
    w.add('ShaderNodeCombineXYZ', 'tile vec', x=8, y=0, Z=3.3); w.link('tile key', 0, 'tile vec', 'X'); w.link('row mod', 0, 'tile vec', 'Y')
    w.add('ShaderNodeTexWhiteNoise', 'tile random', x=9, y=0, noise_dimensions='3D'); w.link('tile vec', 'Vector', 'tile random', 'Vector')
    # tile tone 0.30 .. 0.65
    w.math('tone', 'MULTIPLY_ADD', None, 0.35, 0.30, x=10, y=0); w.link('tile random', 'Value', 'tone', 0)
    # ---- coordinates for the patches: shifted per tile so every tile gets its own pattern
    w.math('shift u', 'MULTIPLY', None, 0.173, x=10, y=-3); w.link('tile random', 'Value', 'shift u', 0)
    w.math('shift v', 'MULTIPLY', None, 0.311, x=10, y=-4); w.link('tile random', 'Value', 'shift v', 0)
    w.math('pu', 'ADD', x=11, y=-3); w.link('uv', 'X', 'pu', 0); w.link('shift u', 0, 'pu', 1)
    w.math('pv', 'ADD', x=11, y=-4); w.link('uv', 'Y', 'pv', 0); w.link('shift v', 0, 'pv', 1)
    w.add('ShaderNodeCombineXYZ', 'patch coords', x=12, y=-3); w.link('pu', 0, 'patch coords', 'X'); w.link('pv', 0, 'patch coords', 'Y')
    src = ('patch coords', 'Vector')
    if stage >= 2:
        hp.instance(w, hp.warp_vector_group('slate coarse warp'), 'warp coarse', x=13, y=-3, Amount=0.012, Scale=5.0, Seed=p['seed'] + 1.0); w.link(*src, 'warp coarse', 'Vector')
        hp.instance(w, hp.warp_vector_group('slate fine warp'), 'warp fine', x=14, y=-3, Amount=0.004, Scale=70.0, Seed=p['seed'] + 2.0); w.link('warp coarse', 'Vector', 'warp fine', 'Vector')
        src = ('warp fine', 'Vector')
    # ---- the colour of the tile body
    if stage == 0:
        hp.instance(w, rt.tileable_noise_group(), 'soft', x=15, y=-3, Scale=7.0, Detail=5.0, Seed=p['seed']); w.link('in', 'Vector', 'soft', 'Vector')
        w.add('ShaderNodeMapRange', 'soft v', x=16, y=-3, clamp=True); w.nodes['soft v'].inputs['From Min'].default_value = 0.3; w.nodes['soft v'].inputs['From Max'].default_value = 0.7
        w.nodes['soft v'].inputs['To Min'].default_value = -0.18; w.nodes['soft v'].inputs['To Max'].default_value = 0.18
        w.link('soft', 'Fac', 'soft v', 'Value')
        w.math('q', 'ADD', x=17, y=-2); w.link('tone', 0, 'q', 0); w.link('soft v', 'Result', 'q', 1)
        node = hp.palette_ramp(w, 'body palette', SLATE_TONES, x=18, y=-2); node.color_ramp.interpolation = 'LINEAR'
        n = len(node.color_ramp.elements)
        for i, e in enumerate(node.color_ramp.elements):
            e.position = i / (n - 1)
        w.link('q', 0, 'body palette', 'Fac')
    else:
        hp.instance(w, hp.anisotropic_noise_group('slate drips', cells=True), 'drips', x=15, y=-3, **{'Scale__U': float(p['drip_u']), 'Scale__V': float(p['drip_v']), 'Randomness': 1.0})
        w.link(*src, 'drips', 'Vector')
        hp.cell_random(w, 'drip random', 'drips', 'Color', 5.0, x=16, y=-3)
        w.math('drip off', 'SUBTRACT', None, 0.5, x=17, y=-3); w.link('drip random', 'Value', 'drip off', 0)
        w.math('drip amount', 'MULTIPLY', None, float(p['drip_amount']), x=18, y=-3); w.link('drip off', 0, 'drip amount', 0)
        w.math('q', 'ADD', x=19, y=-2, clamp=True); w.link('tone', 0, 'q', 0); w.link('drip amount', 0, 'q', 1)
        hp.palette_ramp(w, 'body palette', SLATE_TONES, x=20, y=-2); w.link('q', 0, 'body palette', 'Fac')
    colour = ('body palette', 'Color')

    def mix_colour(name, factor_socket, colour_hex, x, y):
        nonlocal colour
        w.add('ShaderNodeMix', name, x=x, y=y, data_type='RGBA', blend_type='MIX')
        w.link(*factor_socket, name, 'Factor')
        w.link(*colour, name, 'A')
        w.nodes[name].inputs['B'].default_value = hex_rgba(colour_hex)
        colour = (name, 'Result')

    # ---- stage 4: stains (olive patches that run down from the top of a tile, tan chips along the bottom)
    if stage >= 4:
        hp.instance(w, rt.tileable_noise_group(), 'moss noise', x=21, y=-6, Scale=5.0, Detail=5.0, Roughness=0.55, Seed=p['seed'] + 9.0)
        hp.instance(w, hp.warp_vector_group('moss warp'), 'moss warp', x=21, y=-7, Amount=0.01, Scale=40.0, Seed=p['seed'] + 4.0); w.link('in', 'Vector', 'moss warp', 'Vector')
        w.link('moss warp', 'Vector', 'moss noise', 'Vector')
        w.math('top bias', 'MULTIPLY_ADD', None, 0.22, -0.11, x=22, y=-7); w.link('vf', 0, 'top bias', 0)
        w.math('moss value', 'ADD', x=23, y=-6); w.link('moss noise', 'Fac', 'moss value', 0); w.link('top bias', 0, 'moss value', 1)
        w.math('moss dark mask', 'GREATER_THAN', None, 0.60, x=24, y=-6); w.link('moss value', 0, 'moss dark mask', 0)
        w.math('moss light mask', 'GREATER_THAN', None, 0.66, x=24, y=-7); w.link('moss value', 0, 'moss light mask', 0)
        mix_colour('moss dark', ('moss dark mask', 0), OLIVE_DARK, 25, -6)
        mix_colour('moss light', ('moss light mask', 0), OLIVE_LIGHT, 26, -6)
        hp.instance(w, rt.tileable_noise_group(), 'chip noise', x=21, y=-8, Scale=60.0, Detail=2.0, Seed=p['seed'] + 15.0); w.link('in', 'Vector', 'chip noise', 'Vector')
        w.math('chip mask a', 'GREATER_THAN', None, 0.62, x=22, y=-8); w.link('chip noise', 'Fac', 'chip mask a', 0)
        w.math('near bottom', 'LESS_THAN', None, 0.30, x=22, y=-9); w.link('vf', 0, 'near bottom', 0)
        w.math('chip mask', 'MULTIPLY', x=23, y=-8); w.link('chip mask a', 0, 'chip mask', 0); w.link('near bottom', 0, 'chip mask', 1)
        mix_colour('chips', ('chip mask', 0), TAN, 27, -6)

    # ---- stage 3: outlines from the layout (distances in tile units: 1 px = 1/157 of a row, 1/209 of a tile width)
    if stage >= 3:
        hp.instance(w, rt.tileable_noise_group(), 'rag', x=21, y=-10, Scale=90.0, Detail=1.0, Seed=p['seed'] + 21.0); w.link('in', 'Vector', 'rag', 'Vector')
        w.add('ShaderNodeMapRange', 'rag v', x=22, y=-10, clamp=True); w.nodes['rag v'].inputs['From Min'].default_value = 0.35; w.nodes['rag v'].inputs['From Max'].default_value = 0.65
        w.nodes['rag v'].inputs['To Min'].default_value = 0.55; w.nodes['rag v'].inputs['To Max'].default_value = 1.45
        w.link('rag', 'Fac', 'rag v', 'Value')
        # core line under the tile: 10 px of 157
        w.math('core limit', 'MULTIPLY', None, 10.0 / (SIZE_PX / ROWS), x=23, y=-10); w.link('rag v', 'Result', 'core limit', 0)
        w.math('core mask', 'LESS_THAN', x=24, y=-10); w.link('vf', 0, 'core mask', 0); w.link('core limit', 0, 'core mask', 1)
        # shadow band at the top of the tile below: 21 px
        w.math('shadow limit', 'MULTIPLY', None, 21.0 / (SIZE_PX / ROWS), x=23, y=-11); w.link('rag v', 'Result', 'shadow limit', 0)
        w.math('shadow edge', 'SUBTRACT', 1.0, None, x=24, y=-11); w.link('shadow limit', 0, 'shadow edge', 1)
        w.math('shadow mask', 'GREATER_THAN', x=25, y=-11); w.link('vf', 0, 'shadow mask', 0); w.link('shadow edge', 0, 'shadow mask', 1)
        # lip: 5 px of lighter colour right above the core line
        w.math('lip top', 'ADD', None, 0.0, x=25, y=-12); w.link('core limit', 0, 'lip top', 0)
        w.nodes['lip top'].inputs[1].default_value = 5.0 / (SIZE_PX / ROWS)
        w.math('lip a', 'GREATER_THAN', x=26, y=-12); w.link('vf', 0, 'lip a', 0); w.link('core limit', 0, 'lip a', 1)
        w.math('lip b', 'LESS_THAN', x=26, y=-13); w.link('vf', 0, 'lip b', 0); w.link('lip top', 0, 'lip b', 1)
        w.math('lip mask', 'MULTIPLY', x=27, y=-12); w.link('lip a', 0, 'lip mask', 0); w.link('lip b', 0, 'lip mask', 1)
        w.math('lip strength', 'MULTIPLY', None, 0.55, x=28, y=-12); w.link('lip mask', 0, 'lip strength', 0)
        # gaps between tiles: 6 px of 209
        gap = 6.0 / (SIZE_PX / COLUMNS)
        w.math('gap left', 'LESS_THAN', None, gap, x=23, y=-14); w.link('uf', 0, 'gap left', 0)
        w.math('gap right', 'GREATER_THAN', None, 1.0 - gap, x=23, y=-15); w.link('uf', 0, 'gap right', 0)
        w.math('gap mask', 'MAXIMUM', x=24, y=-14); w.link('gap left', 0, 'gap mask', 0); w.link('gap right', 0, 'gap mask', 1)
        mix_colour('lip', ('lip strength', 0), LIP, 28, -6)
        mix_colour('shadow', ('shadow mask', 0), OUTLINE_SHADOW, 29, -6)
        mix_colour('gap', ('gap mask', 0), OUTLINE_CORE, 30, -6)
        mix_colour('core', ('core mask', 0), OUTLINE_CORE, 31, -6)

    # ---- height = lightness of the colour (linear colour -> luminance -> sRGB-like -> stretched)
    w.add('ShaderNodeRGBToBW', 'luma', x=32, y=-2); w.link(*colour, 'luma', 'Color')
    w.math('encoded', 'POWER', None, 1.0 / 2.2, x=33, y=-2); w.link('luma', 'Val', 'encoded', 0)
    w.math('height', 'MULTIPLY', None, 1.0 / 0.46, x=34, y=-2, clamp=True); w.link('encoded', 0, 'height', 0)
    w.link(*colour, 'out', 'Colour')
    w.link('height', 0, 'out', 'Height')
    return tree
