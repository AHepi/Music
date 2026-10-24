"""What this does: the RUST layer for iron: rust in bands that depend on how high up the object a spot is, rust runs below joins, and collars of rust where iron meets another
material (at the object's edges). Rust is orange-brown, rough and not shiny (it also lowers the metallic value). It sits in the first group with dirt, before the water.
Reads the masks Height Share, Edge Dist and the dials band, runs, collar. Amount 0 gives exactly the input. Needs Blender (bpy).
A concrete example: band 0.4 and runs 0.3 on an iron hoop give rusty bands with streaks running down from them.
"""
from ..layer_base import LayerBase, linear

RUST = linear(78, 31, 11)


def build_rust():
    layer = LayerBase('rust', masks=['Height Share', 'Edge Dist'])
    spread = layer.dial('Band')
    base = layer.sm(layer.add(layer.noise(4.0, 3.0), layer.mul(layer.sub(layer.mask('Height Share'), 0.5), 0.25)), layer.sub(1.0, layer.add(layer.mul(spread, 0.9), 0.05)), layer.add(layer.sub(1.0, layer.add(layer.mul(spread, 0.9), 0.05)), 0.15))
    runs = layer.mul(layer.sm(layer.noise(7.0, 2.0, stretch=(1.0, 1.0, 0.15)), layer.sub(1.0, layer.mul(layer.dial('Runs'), 0.9)), layer.add(layer.sub(1.0, layer.mul(layer.dial('Runs'), 0.9)), 0.12)), layer.sub(1.0, layer.mask('Height Share')))
    collar = layer.mul(layer.one_minus(layer.sm(layer.mask('Edge Dist'), 0.0, 0.04)), layer.dial('Collar'))
    rust = layer.mul(layer.clamp(layer.mx(base, layer.mx(runs, collar))), layer.amount)
    colour = layer.mix_colour(layer.mul(rust, 0.85), layer.g('Colour'), RUST)
    roughness = layer.mix(rust, layer.g('Roughness'), 0.85)
    metallic = layer.mul(layer.g('Metallic'), layer.one_minus(layer.mul(rust, 0.9)))
    return layer.finish(colour=colour, roughness=roughness, metallic=metallic, mask=rust)
