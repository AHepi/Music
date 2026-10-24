"""What this does: the MOSS AND ALGAE layer (the painted side of moss; the 3D moss cushions are a separate step): green growth in clumps where it is damp AND shady, thicker toward the
bottom of walls, and NEVER where feet or wheels pass or where the settings keep things clear (exact zero on those masks). The moss is never brighter than the surface it grows
on (an earlier fix: lime-bright moss on stone looked wrong), a little rougher, with a soft bump. Reads the masks Dampness, Shade, Footfall, Keepclear, Track, Height Share and
the dials cover, clump_size_metres, damp_need, shade_need. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: on a north wall foot in the shade moss spreads in 15 cm clumps; on the wheel tracks of a lane it is exactly 0.
"""
from ..layer_base import LayerBase, linear

MOSS = linear(40, 78, 22)


def build_moss_and_algae():
    layer = LayerBase('moss_and_algae', masks=['Dampness', 'Shade', 'Footfall', 'Keepclear', 'Track', 'Height Share'])
    damp = layer.sm(layer.mask('Dampness'), layer.mul(layer.dial('Damp Need'), 0.5), 0.85)
    shade = layer.sm(layer.mask('Shade'), layer.mul(layer.dial('Shade Need'), 0.5), 0.9)
    clear = layer.mul(layer.mul(layer.one_minus(layer.sm(layer.mask('Footfall'), 0.3, 0.6)), layer.one_minus(layer.mask('Keepclear'))), layer.one_minus(layer.mask('Track')))
    clump_per_metre = layer.n.math('DIVIDE', 1.0, layer.n.math('MAXIMUM', layer.dial('Clump Size Metres'), 0.02))
    clump = layer.sm(layer.noise(clump_per_metre, 4.0), layer.sub(1.0, layer.dial('Cover')), layer.add(layer.sub(1.0, layer.dial('Cover')), 0.12))
    low_bias = layer.sub(1.0, layer.mul(layer.mask('Height Share'), 0.85))
    region = layer.sm(layer.noise(0.8, 2.0), 0.4, 0.62)           # moss grows in big regions, not evenly everywhere (an even spread reads as camouflage)
    site = layer.clamp(layer.mul(layer.mul(layer.mul(damp, shade), layer.mul(layer.mul(clear, low_bias), region)), 2.0))
    fac = layer.mul(layer.clamp(layer.mul(site, clump)), layer.amount)
    # a moss colour no brighter than the surface it grows on
    base_light = layer.n.luminance(layer.g('Colour'))
    moss = layer.n.hsv(MOSS, value=layer.n.clamp01(layer.n.math('DIVIDE', layer.mul(base_light, 0.9), 0.08)))
    colour = layer.mix_colour(layer.mul(fac, 0.85), layer.g('Colour'), moss)
    colour = layer.mix_colour(layer.clamp(layer.mul(fac, 1000.0)), layer.g('Colour'), colour)
    roughness = layer.mix(layer.clamp(layer.mul(fac, 1000.0)), layer.g('Roughness'), layer.clamp(layer.add(layer.g('Roughness'), layer.mul(fac, 0.1))))
    bumped = layer.n.bump(clump, layer.g('Normal'), strength=0.4, distance=0.01)
    normal = layer.n.mix_vector(layer.clamp(layer.mul(fac, 1000.0)), layer.g('Normal'), bumped)
    return layer.finish(colour=colour, roughness=roughness, normal=normal, mask=fac)
