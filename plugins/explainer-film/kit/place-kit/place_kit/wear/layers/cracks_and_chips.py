"""What this does: the CRACKS AND CHIPS layer: dark crack lines (the borders of a slow cellular pattern, only some of them, never thinner than three picture dots) that also
dent the surface through a bump, and chips at the object's own edges where the paint, plaster or glaze has come away to show a paler core. It goes on AFTER the water so
cracks and chips stay dull when the surface is wet. Reads the masks Edge Dist and the dials crack_density, crack_width_metres, chip_amount (and Dot Metres). Amount 0 gives
exactly the input. Needs Blender (bpy).
A concrete example: crack_width_metres 0.012 gives hairline cracks about 1.2 cm wide (or three dots, if that is wider); chip_amount 0.3 knocks pale chips off the corners.
"""
from ..layer_base import LayerBase, linear

CRACK = linear(14, 10, 8)
CELL_METRES = 0.6


def build_cracks_and_chips():
    layer = LayerBase('cracks_and_chips', masks=['Edge Dist'])
    net = layer.net
    scaled = net.vector_math('MULTIPLY', layer.position, net.combine(1.0 / CELL_METRES, 1.0 / CELL_METRES, 1.0 / CELL_METRES))
    offset = net.vector_math('ADD', scaled, net.combine(layer.multiply(layer.object_seed, 41.3), layer.multiply(layer.object_seed, 23.7), layer.multiply(layer.group_input('Seed'), 0.77)))
    distance = net.voronoi_edge(offset, scale=1.0)
    width_cells = layer.multiply(layer.floor_size(layer.dial('Crack Width Metres')), 1.0 / CELL_METRES)
    line = layer.one_minus(layer.smooth_between(distance, 0.0, width_cells))
    density = layer.dial('Crack Density')
    keep = layer.smooth_between(layer.noise(2.2, 2.0), layer.sub(1.0, layer.multiply(density, 0.9)), layer.add(layer.sub(1.0, layer.multiply(density, 0.9)), 0.12))
    crack = layer.multiply(layer.clamp(layer.multiply(line, keep)), layer.amount)
    chip_band = layer.one_minus(layer.smooth_between(layer.mask('Edge Dist'), 0.0, layer.add(0.03, layer.multiply(layer.dial('Chip Amount'), 0.05))))
    chip = layer.multiply(layer.multiply(chip_band, layer.smooth_between(layer.noise(14.0, 2.0), 0.5, 0.7)), layer.multiply(layer.dial('Chip Amount'), layer.amount))
    chip = layer.clamp(layer.multiply(chip, 3.0))
    pale = layer.lighten(layer.group_input('Colour'), value=1.35, saturation=0.8)
    colour = layer.mix_colour(layer.multiply(crack, 0.85), layer.group_input('Colour'), CRACK)
    colour = layer.mix_colour(layer.multiply(chip, 0.8), colour, pale)
    colour = layer.mix_colour(layer.clamp(layer.multiply(layer.add(crack, chip), 1000.0)), layer.group_input('Colour'), colour)
    roughness = layer.mix(layer.clamp(layer.multiply(chip, 1000.0)), layer.group_input('Roughness'), layer.clamp(layer.add(layer.group_input('Roughness'), layer.multiply(chip, 0.1))))
    dented = net.bump(layer.multiply(layer.multiply(line, keep), -1.0), layer.group_input('Normal'), strength=0.8, distance=0.01)
    normal = net.mix_vector(layer.clamp(layer.multiply(crack, 1000.0)), layer.group_input('Normal'), dented)
    return layer.finish(colour=colour, roughness=roughness, normal=normal, mask=layer.clamp(layer.add(crack, chip)))
