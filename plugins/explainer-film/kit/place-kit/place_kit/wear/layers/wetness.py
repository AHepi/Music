"""What this does: the WETNESS layer: a wet surface is darker and smoother (an earlier outdoor test measured roughness about 0.9 dry and about 0.3 wet), gathers in low places as puddles,
climbs a wall's foot where it is damp and gets a thin clear coat. The room's STATE sets how much: dry (amount 0: the layer is in the material but does nothing, which the audit
accepts), damp or wet. The roughness map does the work, not the specular map, and walls get no mirror shine. Puddles come from the plan masks (the same low places the growth keeps
plants out of). Cracks, chips and edge wear go on AFTER the water so they stay dull when wet. Reads the masks Dampness, Above Water, Height Above Foot and the dials darken,
wet_roughness, puddles, film_coat. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: state damp on a road darkens it a little and fills the ruts' bottoms with standing water that reflects the sky.
"""
from ..layer_base import LayerBase


def build_wetness():
    layer = LayerBase('wetness', masks=['Dampness', 'Above Water', 'Height Above Foot'])
    general = layer.multiply(layer.amount, layer.add(0.5, layer.multiply(layer.mask('Dampness'), 0.5)))
    foot = layer.multiply(layer.multiply(layer.mask('Dampness'), layer.one_minus(layer.smooth_between(layer.mask('Height Above Foot'), 0.0, 0.8))), layer.amount)
    puddle = layer.multiply(layer.multiply(layer.one_minus(layer.mask('Above Water')), layer.dial('Puddles')), layer.multiply(layer.amount, 2.0))
    puddle = layer.clamp(puddle)
    wet = layer.clamp(layer.maximum(layer.multiply(general, 0.5), layer.maximum(foot, puddle)))
    colour = layer.net.hue_saturation_value(layer.group_input('Colour'), value=layer.sub(1.0, layer.add(layer.multiply(layer.dial('Darken'), wet), layer.multiply(puddle, 0.25))))
    colour = layer.mix_colour(layer.clamp(layer.multiply(wet, 1000.0)), layer.group_input('Colour'), colour)
    roughness = layer.mix(wet, layer.group_input('Roughness'), layer.dial('Wet Roughness'))
    roughness = layer.mix(puddle, roughness, 0.03)
    coat = layer.maximum(layer.group_input('Coat Weight'), layer.add(layer.multiply(layer.multiply(layer.dial('Film Coat'), wet), 0.5), layer.multiply(puddle, 0.8)))
    coat = layer.mix(layer.clamp(layer.multiply(wet, 1000.0)), layer.group_input('Coat Weight'), coat)
    smooth = layer.net.new('ShaderNodeNewGeometry').outputs['Normal']
    normal = layer.net.mix_vector(puddle, layer.group_input('Normal'), smooth)
    return layer.finish(colour=colour, roughness=roughness, coat=coat, normal=normal, mask=wet)
