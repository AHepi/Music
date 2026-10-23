"""What this does: the RUBBISH layer (the painted side of litter; the 3D litter pieces are a separate step): muck, scraps and straw-coloured specks gathered where litter really
gathers: at wall feet, along gutters and road edges and in damp low places, and NEVER on the crown of a road or on a wheel track (exact zero). It is the last layer, over everything.
Specks are small and few rather than a dusting everywhere. Reads the masks Wall Dist, Crown, Track, Dampness, Litter Dist and the dials density, straw_share. Amount 0 gives exactly the
input. Needs Blender (bpy).
A concrete example: density 0.3 scatters a few dark and straw-coloured specks along the foot of a wall and the road's edge, and none on the rutted middle.
"""
from ..layer_base import LayerBase, linear

MUCK = linear(26, 19, 13)
STRAW = linear(122, 96, 44)


def build_rubbish():
    layer = LayerBase('rubbish', masks=['Wall Dist', 'Crown', 'Track', 'Dampness', 'Litter Dist'])
    foot = layer.one_minus(layer.smooth_between(layer.mask('Wall Dist'), 0.0, 0.8))
    gather = layer.clamp(layer.add(foot, layer.multiply(layer.mask('Dampness'), 0.35)))
    allowed = layer.multiply(layer.one_minus(layer.mask('Crown')), layer.one_minus(layer.mask('Track')))
    specks = layer.smooth_between(layer.noise(16.0, 1.0), layer.sub(1.0, layer.multiply(layer.dial('Density'), 0.6)), layer.add(layer.sub(1.0, layer.multiply(layer.dial('Density'), 0.6)), 0.08))
    fac = layer.multiply(layer.clamp(layer.multiply(layer.multiply(specks, gather), allowed)), layer.amount)
    straw = layer.smooth_between(layer.noise(9.0, 1.0), layer.sub(1.0, layer.dial('Straw Share')), layer.add(layer.sub(1.0, layer.dial('Straw Share')), 0.1))
    colour = layer.mix_colour(layer.multiply(fac, 0.9), layer.group_input('Colour'), layer.mix_colour(straw, MUCK, STRAW))
    colour = layer.mix_colour(layer.clamp(layer.multiply(fac, 1000.0)), layer.group_input('Colour'), colour)
    roughness = layer.mix(layer.clamp(layer.multiply(fac, 1000.0)), layer.group_input('Roughness'), layer.clamp(layer.add(layer.group_input('Roughness'), layer.multiply(fac, 0.08))))
    return layer.finish(colour=colour, roughness=roughness, mask=fac)
