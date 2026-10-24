"""What this does: the WETNESS layer: a wet surface is darker and smoother (an earlier outdoor test measured roughness about 0.9 dry and about 0.3 wet), gathers in low places as puddles,
climbs a wall's foot where it is damp and gets a thin clear coat. The room's STATE sets how much: dry (amount 0: the layer is in the material but does nothing, which the audit
accepts), damp or wet. The roughness map does the work, not the specular map, and walls get no mirror shine. Puddles come from the plan masks (the same low places the growth keeps
plants out of). Cracks, chips and edge wear go on AFTER the water so they stay dull when wet. Reads the masks Dampness, Above Water, Height Above Foot and the dials darken,
wet_roughness, puddles, film_coat. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: state damp on a lane darkens it a little and fills the ruts' bottoms with standing water that reflects the sky.
"""
from ..layer_base import LayerBase


def build_wetness():
    layer = LayerBase('wetness', masks=['Dampness', 'Above Water', 'Height Above Foot'])
    general = layer.mul(layer.amount, layer.add(0.5, layer.mul(layer.mask('Dampness'), 0.5)))
    foot = layer.mul(layer.mul(layer.mask('Dampness'), layer.one_minus(layer.sm(layer.mask('Height Above Foot'), 0.0, 0.8))), layer.amount)
    puddle = layer.mul(layer.mul(layer.one_minus(layer.mask('Above Water')), layer.dial('Puddles')), layer.mul(layer.amount, 2.0))
    puddle = layer.clamp(puddle)
    wet = layer.clamp(layer.mx(layer.mul(general, 0.5), layer.mx(foot, puddle)))
    colour = layer.n.hsv(layer.g('Colour'), value=layer.sub(1.0, layer.add(layer.mul(layer.dial('Darken'), wet), layer.mul(puddle, 0.25))))
    colour = layer.mix_colour(layer.clamp(layer.mul(wet, 1000.0)), layer.g('Colour'), colour)
    roughness = layer.mix(wet, layer.g('Roughness'), layer.dial('Wet Roughness'))
    roughness = layer.mix(puddle, roughness, 0.03)
    coat = layer.mx(layer.g('Coat Weight'), layer.add(layer.mul(layer.mul(layer.dial('Film Coat'), wet), 0.5), layer.mul(puddle, 0.8)))
    coat = layer.mix(layer.clamp(layer.mul(wet, 1000.0)), layer.g('Coat Weight'), coat)
    smooth = layer.n.new('ShaderNodeNewGeometry').outputs['Normal']
    normal = layer.n.mix_vector(puddle, layer.g('Normal'), smooth)
    return layer.finish(colour=colour, roughness=roughness, coat=coat, normal=normal, mask=wet)
