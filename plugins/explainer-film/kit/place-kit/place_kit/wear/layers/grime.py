"""What this does: the GRIME layer: soot on surfaces under eaves and overhangs (near the top of a wall), run-off streaks that run down from sills and eaves, and a darker damp
band at the foot of walls. An earlier outdoor test measured how much is right: dark grime on about a quarter of an area and about a third darker (more is mush), so the pattern is
cut from a slow noise with a threshold that keeps that share (the dials area_share and darkening). It goes on before the water. Reads the masks Sheltered, Height Share,
Height Above Foot, Dampness. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: area_share 0.25 and darkening 0.33 darken a quarter of a wall by a third, in vertical streaks under the eave; the rest stays as it was.
"""
from ..layer_base import LayerBase


def build_grime():
    layer = LayerBase('grime', masks=['Sheltered', 'Height Share', 'Height Above Foot', 'Dampness'])
    # the noise is about 0.5 on average with a spread of about 0.12, so a threshold 0.67 spreads above the mean keeps about a quarter
    threshold = layer.sub(0.62, layer.multiply(layer.sub(layer.dial('Area Share'), 0.25), 1.2))
    streaks = layer.smooth_between(layer.noise(5.0, 3.0, stretch=(1.0, 1.0, 0.12)), threshold, layer.add(threshold, 0.1))
    patches = layer.smooth_between(layer.noise(1.6, 3.0), threshold, layer.add(threshold, 0.12))
    soot = layer.multiply(layer.multiply(layer.mask('Sheltered'), layer.smooth_between(layer.mask('Height Share'), 0.5, 0.95)), layer.multiply(layer.dial('Soot Under Shelter'), layer.add(0.4, layer.multiply(patches, 0.6))))
    runoff = layer.multiply(layer.multiply(streaks, layer.dial('Runoff Streaks')), layer.sub(1.0, layer.multiply(layer.mask('Height Share'), 0.4)))
    band = layer.multiply(layer.multiply(layer.mask('Dampness'), layer.one_minus(layer.smooth_between(layer.mask('Height Above Foot'), 0.1, 0.8))), layer.dial('Damp Band'))
    fac = layer.multiply(layer.clamp(layer.maximum(soot, layer.maximum(runoff, band))), layer.amount)
    colour = layer.mix_colour(layer.multiply(fac, layer.multiply(layer.dial('Darkening'), 3.0)), layer.group_input('Colour'), layer.darken(layer.group_input('Colour'), 0.68))
    colour = layer.mix_colour(layer.clamp(layer.multiply(fac, 1000.0)), layer.group_input('Colour'), colour)
    return layer.finish(colour=colour, mask=fac)
