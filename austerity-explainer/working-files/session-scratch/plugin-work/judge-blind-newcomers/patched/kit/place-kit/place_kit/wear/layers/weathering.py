"""What this does: the WEATHERING layer, kept apart from dirt so a person can tell "old" from "dirty": timber turns silver-grey (silvering), surfaces that face the sky and are
not sheltered fade and bleach in the sun (sun fade), and metal and stone get a green-blue patina where it is damp (patina). Colour changes only (and a little roughness);
the real damage is in the other layers. Reads the masks Sheltered, Dampness, Up and the dials silvering, sun_fade, patina. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: silvering 0.5 on an oak plank pulls its brown toward a pale grey in slow patches, more on the up-facing side.
"""
from ..layer_base import LayerBase, linear

PATINA = linear(70, 120, 100)


def build_weathering():
    layer = LayerBase('weathering', masks=['Sheltered', 'Dampness', 'Up'])
    colour = layer.g('Colour')
    grey = layer.lighten(layer.n.hsv(colour, saturation=0.15), value=1.25)
    silver = layer.mul(layer.mul(layer.dial('Silvering'), layer.add(0.45, layer.mul(layer.mask('Up'), 0.55))), layer.sm(layer.noise(1.8, 3.0), 0.25, 0.7))
    fade = layer.mul(layer.mul(layer.dial('Sun Fade'), layer.one_minus(layer.mask('Sheltered'))), layer.add(0.4, layer.mul(layer.mask('Up'), 0.6)))
    patina = layer.mul(layer.mul(layer.dial('Patina'), layer.mask('Dampness')), layer.sm(layer.noise(3.0, 2.0), 0.4, 0.75))
    silver_fac = layer.mul(layer.clamp(silver), layer.amount)
    fade_fac = layer.mul(layer.clamp(fade), layer.amount)
    patina_fac = layer.mul(layer.clamp(patina), layer.amount)
    result = layer.mix_colour(layer.mul(silver_fac, 0.75), colour, grey)
    faded = layer.n.hsv(result, saturation=layer.sub(1.0, layer.mul(fade_fac, 0.4)), value=layer.add(1.0, layer.mul(fade_fac, 0.12)))
    result = layer.mix_colour(layer.clamp(layer.mul(fade_fac, 1000.0)), result, faded)
    result = layer.mix_colour(layer.mul(patina_fac, 0.6), result, PATINA)
    total = layer.clamp(layer.add(silver_fac, layer.add(fade_fac, patina_fac)))
    roughness = layer.mix(layer.clamp(layer.mul(silver_fac, 1000.0)), layer.g('Roughness'), layer.clamp(layer.add(layer.g('Roughness'), layer.mul(silver_fac, 0.05))))
    return layer.finish(colour=result, roughness=roughness, mask=total)
