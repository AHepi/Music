"""What this does: the WETNESS layer: a wet surface is darker and smoother (an earlier outdoor test measured roughness about 0.9 dry and about 0.3 wet), gathers in low places as puddles,
climbs a wall's foot where it is damp and gets a thin clear coat. The room's STATE sets how much: dry (amount 0: the layer is in the material but does nothing, which the audit
accepts), damp or wet. The roughness map does the work, not the specular map, and walls get no mirror shine. Puddles come from the plan masks (the same low places the growth keeps
plants out of), and only on the GROUND (an object whose property pk_holds_puddles is 1) and only where the face is nearly level: the plan masks describe the ground under a roof too,
and an earlier version put mirror puddles on a thatched roof above a hollow, which drew as white sparkles. A surface that soaks water up (earth, straw, cloth, weathered wood: the
material's film_coat dial is 0 there, set by the wear pass from data/surfaces.json) darkens but gets no clear film. Cracks, chips and edge wear go on AFTER the water so they stay
dull when wet. Reads the masks Dampness, Above Water, Height Above Foot, Up and the dials darken, wet_roughness, puddles, film_coat. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: state damp on a road darkens it a little and fills the ruts' bottoms with standing water that reflects the sky; the roof above stays dull.
"""
from ..layer_base import LayerBase

HOLDS_PUDDLES = 'pk_holds_puddles'          # 1 on ground objects (written by the wear pass); an object without it reads 0, so no puddle is ever drawn on it


def build_wetness():
    layer = LayerBase('wetness', masks=['Dampness', 'Above Water', 'Height Above Foot', 'Up'])
    general = layer.multiply(layer.amount, layer.add(0.5, layer.multiply(layer.mask('Dampness'), 0.5)))
    foot = layer.multiply(layer.multiply(layer.mask('Dampness'), layer.one_minus(layer.smooth_between(layer.mask('Height Above Foot'), 0.0, 0.8))), layer.amount)
    level = layer.multiply(layer.smooth_between(layer.mask('Up'), 0.7, 0.85), layer.net.attr(HOLDS_PUDDLES))          # loose: a displaced ground is bumpy under its water
    puddle = layer.multiply(layer.multiply(layer.one_minus(layer.mask('Above Water')), layer.dial('Puddles')), layer.multiply(layer.amount, 2.0))
    puddle = layer.clamp(layer.multiply(puddle, level))
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
