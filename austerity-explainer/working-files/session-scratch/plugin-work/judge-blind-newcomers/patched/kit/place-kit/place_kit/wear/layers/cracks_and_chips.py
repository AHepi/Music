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
    n = layer.n
    scaled = n.vector_math('MULTIPLY', layer.position, n.combine(1.0 / CELL_METRES, 1.0 / CELL_METRES, 1.0 / CELL_METRES))
    offset = n.vector_math('ADD', scaled, n.combine(layer.mul(layer.object_seed, 41.3), layer.mul(layer.object_seed, 23.7), layer.mul(layer.g('Seed'), 0.77)))
    distance = n.voronoi_edge(offset, scale=1.0)
    width_cells = layer.mul(layer.floor_size(layer.dial('Crack Width Metres')), 1.0 / CELL_METRES)
    line = layer.one_minus(layer.sm(distance, 0.0, width_cells))
    density = layer.dial('Crack Density')
    keep = layer.sm(layer.noise(2.2, 2.0), layer.sub(1.0, layer.mul(density, 0.9)), layer.add(layer.sub(1.0, layer.mul(density, 0.9)), 0.12))
    crack = layer.mul(layer.clamp(layer.mul(line, keep)), layer.amount)
    chip_band = layer.one_minus(layer.sm(layer.mask('Edge Dist'), 0.0, layer.add(0.03, layer.mul(layer.dial('Chip Amount'), 0.05))))
    chip = layer.mul(layer.mul(chip_band, layer.sm(layer.noise(14.0, 2.0), 0.5, 0.7)), layer.mul(layer.dial('Chip Amount'), layer.amount))
    chip = layer.clamp(layer.mul(chip, 3.0))
    pale = layer.lighten(layer.g('Colour'), value=1.35, saturation=0.8)
    colour = layer.mix_colour(layer.mul(crack, 0.85), layer.g('Colour'), CRACK)
    colour = layer.mix_colour(layer.mul(chip, 0.8), colour, pale)
    colour = layer.mix_colour(layer.clamp(layer.mul(layer.add(crack, chip), 1000.0)), layer.g('Colour'), colour)
    roughness = layer.mix(layer.clamp(layer.mul(chip, 1000.0)), layer.g('Roughness'), layer.clamp(layer.add(layer.g('Roughness'), layer.mul(chip, 0.1))))
    dented = n.bump(layer.mul(layer.mul(line, keep), -1.0), layer.g('Normal'), strength=0.8, distance=0.01)
    normal = n.mix_vector(layer.clamp(layer.mul(crack, 1000.0)), layer.g('Normal'), dented)
    return layer.finish(colour=colour, roughness=roughness, normal=normal, mask=layer.clamp(layer.add(crack, chip)))
