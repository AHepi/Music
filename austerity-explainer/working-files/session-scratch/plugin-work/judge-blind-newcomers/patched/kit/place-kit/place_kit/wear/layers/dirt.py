"""What this does: the DIRT layer: a thin film of soil over the surface, mud splashed up the foot of walls and posts (from the object's own lowest point), pale dust on
up-facing surfaces, and polish (smoother, slightly darker) where feet and wheels wear a surface smooth. Dirt goes on BEFORE the water, so water then sits on top of it.
It reads the masks Footfall, Height Above Foot, Up and the dials film, foot_splash, foot_height_metres, dust, polish. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: on a wall, foot_splash browns the lowest 45 cm; on the ground the class defaults switch the splash off and raise the polish on the wheel tracks.
"""
from ..layer_base import LayerBase, linear

SOIL = linear(46, 34, 24)


def build_dirt():
    layer = LayerBase('dirt', masks=['Footfall', 'Height Above Foot', 'Up'])
    film = layer.mul(layer.sm(layer.noise(1.3), 0.38, 0.75), layer.dial('Film'))
    splash = layer.mul(layer.mul(layer.one_minus(layer.sm(layer.mask('Height Above Foot'), 0.0, layer.dial('Foot Height Metres'))), layer.dial('Foot Splash')),
                       layer.add(0.7, layer.mul(layer.noise(6.0, 2.0), 0.3)))
    dust = layer.mul(layer.mul(layer.mask('Up'), layer.dial('Dust')), layer.sm(layer.noise(2.5, 2.0), 0.3, 0.7))
    fac = layer.mul(layer.clamp(layer.mx(film, layer.mx(splash, layer.mul(dust, 0.6)))), layer.amount)
    colour = layer.mix_colour(layer.mul(fac, 0.95), layer.g('Colour'), SOIL)
    polish = layer.mul(layer.mul(layer.mask('Footfall'), layer.dial('Polish')), layer.amount)
    roughness = layer.clamp(layer.sub(layer.add(layer.g('Roughness'), layer.mul(fac, 0.08)), layer.mul(polish, 0.25)))
    # a mix at amount 0 must be exact: keep the original roughness when both factors are 0
    roughness = layer.mix(layer.clamp(layer.mul(layer.add(fac, polish), 1000.0)), layer.g('Roughness'), roughness)
    return layer.finish(colour=colour, roughness=roughness, mask=fac)
