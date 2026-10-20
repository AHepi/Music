# What this does: the "everyone's first try" brick wall, built the way the Blender Bazaar tutorial (JSAbbott / Blender Nation, 2024-25) and
# several forum threads describe it: the stock Brick Texture node, two brick colours and a mortar colour (hex codes from the tutorial), a Noise
# Texture (scale 300) mixed into the colours, a second noise for the mortar, plus a Voronoi "paint" layer through a constant Color Ramp.
# It is NOT seamless in colour (the Brick node's random colour does not repeat) and is here only to see how close the stock chain gets.
# Parameters: mode = 'brick' (default), 'slate' (narrow rows, black mortar, blue greys) or 'planks' (long boards + Wave Texture grain).
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd


def build_node_group(parameters):
    mode = parameters.get('mode', 'brick')
    b = bd.Builder('Stock brick node ' + mode)
    vector = b.uv()
    if mode == 'brick':
        settings = dict(scale=2.0, width=0.5, height=0.1667, mortar_size=0.014, smooth=0.1, bias=0.0, c1='#6D3137', c2='#B55B51', mortar='#909090')
    elif mode == 'slate':
        settings = dict(scale=1.0, width=0.17, height=0.125, mortar_size=0.02, smooth=0.1, bias=0.0, c1='#2f3a42', c2='#51636d', mortar='#0c0d0e')
    else:
        settings = dict(scale=1.0, width=1.0, height=0.2, mortar_size=0.015, smooth=0.1, bias=0.0, c1='#5b3b28', c2='#8a5a38', mortar='#150f0c')
    noise = b.noise(vector, 300.0 if mode == 'brick' else 25.0, 4.0, 0.5).outputs['Factor']
    colour1 = b.ramp(noise, [(0.0, '#3c1a1f' if mode == 'brick' else settings['c1']), (1.0, settings['c1'])])
    colour2 = b.ramp(noise, [(0.0, '#7d3b34' if mode == 'brick' else settings['c2']), (1.0, settings['c2'])])
    brick = b.node('ShaderNodeTexBrick', offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2)
    b._put(brick, 'Vector', vector)
    b._put(brick, 'Color1', colour1); b._put(brick, 'Color2', colour2)
    b._put(brick, 'Mortar', bd.as_colour(settings['mortar']))
    b._put(brick, 'Scale', settings['scale']); b._put(brick, 'Mortar Size', settings['mortar_size'])
    b._put(brick, 'Mortar Smooth', settings['smooth']); b._put(brick, 'Bias', settings['bias'])
    b._put(brick, 'Brick Width', settings['width']); b._put(brick, 'Row Height', settings['height'])
    colour = brick.outputs['Color']
    # Voronoi "paint" through a constant ramp (the tutorial's step 19-22)
    voronoi = b.node('ShaderNodeTexVoronoi', feature='SMOOTH_F1')
    b._put(voronoi, 'Vector', vector); b._put(voronoi, 'Scale', 3.0)
    paint_mask = b.ramp(voronoi.outputs['Distance'], [(0.0, '#000000'), (0.55, '#ffffff')], 'CONSTANT')
    paint_value = b.brightness(paint_mask)
    if mode == 'brick':
        colour = b.mix(colour, voronoi.outputs['Color'], b.mul(paint_value, 0.25))
    elif mode == 'planks':
        wave = b.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', wave_profile='SIN')
        b._put(wave, 'Vector', vector); b._put(wave, 'Scale', 40.0); b._put(wave, 'Distortion', 6.0); b._put(wave, 'Detail', 3.0)
        grain = wave.outputs['Fac']
        colour = b.mix(colour, '#2a1a10', b.mul(grain, 0.45))
    height = b.mixf(0.2, 0.7, brick.outputs['Fac'])
    return b.finish(colour, height, 0.9, 0.0)
