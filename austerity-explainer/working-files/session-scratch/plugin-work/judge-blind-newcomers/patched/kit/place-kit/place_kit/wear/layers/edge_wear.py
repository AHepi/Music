"""What this does: the EDGE WEAR layer: edges and corners rubbed pale and smooth by hands, feet and years. The distance to the object's own edges comes from the object's
bounds (no Bevel or Ambient Occlusion node: they differ or fail in EEVEE), the rubbed zone is broken up by noise so it is not a clean stripe, and it is never thinner than
three picture dots. Colour goes paler, roughness drops. It goes after the water. Reads the masks Edge Dist and the dials width_metres, pale, roughness_drop. Amount 0 gives
exactly the input. Needs Blender (bpy).
A concrete example: width_metres 0.02 rubs a 2 cm band along every edge of a post, paler where the noise says it was touched most.
"""
from ..layer_base import LayerBase


def build_edge_wear():
    layer = LayerBase('edge_wear', masks=['Edge Dist'])
    width = layer.floor_size(layer.dial('Width Metres'))
    band = layer.one_minus(layer.sm(layer.mask('Edge Dist'), 0.0, width))
    broken = layer.mul(band, layer.add(0.45, layer.mul(layer.noise(10.0, 2.0), 0.9)))
    fac = layer.mul(layer.clamp(broken), layer.amount)
    colour = layer.mix_colour(layer.mul(fac, layer.mul(layer.dial('Pale'), 4.0)), layer.g('Colour'), layer.lighten(layer.g('Colour'), value=1.5, saturation=0.8))
    colour = layer.mix_colour(layer.clamp(layer.mul(fac, 1000.0)), layer.g('Colour'), colour)
    roughness = layer.mix(layer.clamp(layer.mul(fac, 1000.0)), layer.g('Roughness'), layer.clamp(layer.sub(layer.g('Roughness'), layer.mul(fac, layer.dial('Roughness Drop')))))
    return layer.finish(colour=colour, roughness=roughness, mask=fac)
