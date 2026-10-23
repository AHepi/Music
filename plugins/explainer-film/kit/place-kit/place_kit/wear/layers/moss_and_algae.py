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
    damp = layer.smooth_between(layer.mask('Dampness'), layer.multiply(layer.dial('Damp Need'), 0.5), 0.85)
    shade = layer.smooth_between(layer.mask('Shade'), layer.multiply(layer.dial('Shade Need'), 0.5), 0.9)
    clear = layer.multiply(layer.multiply(layer.one_minus(layer.smooth_between(layer.mask('Footfall'), 0.3, 0.6)), layer.one_minus(layer.mask('Keepclear'))), layer.one_minus(layer.mask('Track')))
    clump_per_metre = layer.net.math('DIVIDE', 1.0, layer.net.math('MAXIMUM', layer.dial('Clump Size Metres'), 0.02))
    clump = layer.smooth_between(layer.noise(clump_per_metre, 4.0), layer.sub(1.0, layer.dial('Cover')), layer.add(layer.sub(1.0, layer.dial('Cover')), 0.12))
    low_bias = layer.sub(1.0, layer.multiply(layer.mask('Height Share'), 0.85))
    region = layer.smooth_between(layer.noise(0.8, 2.0), 0.4, 0.62)           # moss grows in big regions, not evenly everywhere (an even spread reads as camouflage)
    site = layer.clamp(layer.multiply(layer.multiply(layer.multiply(damp, shade), layer.multiply(layer.multiply(clear, low_bias), region)), 2.0))
    fac = layer.multiply(layer.clamp(layer.multiply(site, clump)), layer.amount)
    # a moss colour no brighter than the surface it grows on
    base_light = layer.net.luminance(layer.group_input('Colour'))
    moss = layer.net.hue_saturation_value(MOSS, value=layer.net.clamp01(layer.net.math('DIVIDE', layer.multiply(base_light, 0.9), 0.08)))
    colour = layer.mix_colour(layer.multiply(fac, 0.85), layer.group_input('Colour'), moss)
    colour = layer.mix_colour(layer.clamp(layer.multiply(fac, 1000.0)), layer.group_input('Colour'), colour)
    roughness = layer.mix(layer.clamp(layer.multiply(fac, 1000.0)), layer.group_input('Roughness'), layer.clamp(layer.add(layer.group_input('Roughness'), layer.multiply(fac, 0.1))))
    bumped = layer.net.bump(clump, layer.group_input('Normal'), strength=0.4, distance=0.01)
    normal = layer.net.mix_vector(layer.clamp(layer.multiply(fac, 1000.0)), layer.group_input('Normal'), bumped)
    return layer.finish(colour=colour, roughness=roughness, normal=normal, mask=fac)
