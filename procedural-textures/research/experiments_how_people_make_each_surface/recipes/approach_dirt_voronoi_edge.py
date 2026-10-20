# What this does: the "procedural dirt with puddles" chain from JSAbbott's Blender Bazaar tutorial (4 March 2024, Blender 4.0), built node by node
# from the page's step list: Voronoi Distance to Edge (scale 3) overlaid with a fine Noise (scale 175, detail 15) -> Color Ramp -> a second ramp
# '#3A251C' / '#A4764A' / '#BE8655' -> Add a Noise (scale 7.5); puddle mask = Noise -> Voronoi (scale 1) -> Color Ramp, used as roughness.
# Not seamless (plain Blender noise). Here only to see what the chain looks like next to the mud reference.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd


def build_node_group(parameters):
    b = bd.Builder('Dirt chain from the tutorial')
    vector = b.uv()
    voronoi = b.node('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE'); b._put(voronoi, 'Vector', vector); b._put(voronoi, 'Scale', 3.0)
    noise175 = b.noise(vector, 175.0, 15.0, 0.5).outputs['Factor']
    overlay = b.mix(b.grey_to_colour(voronoi.outputs['Distance']), b.grey_to_colour(noise175), 1.0, 'OVERLAY')
    ramp1 = b.ramp(b.brightness(overlay), [(0.0, '#000000'), (0.55, '#ffffff')])
    ramp1_value = b.brightness(ramp1)
    colour = b.ramp(ramp1_value, [(0.0, '#3A251C'), (0.5, '#A4764A'), (1.0, '#BE8655')])
    noise75 = b.noise(vector, 7.5, 15.0, 0.5).outputs['Factor']
    colour = b.mix(colour, b.grey_to_colour(noise75), 0.25, 'ADD')
    puddle_noise = b.noise(vector, 2.0, 15.0, 0.5).outputs['Factor']
    puddle_voronoi = b.node('ShaderNodeTexVoronoi'); b._put(puddle_voronoi, 'Vector', b.vec(puddle_noise, puddle_noise, 0.0)); b._put(puddle_voronoi, 'Scale', 1.0)
    puddle_ramp = b.ramp(puddle_voronoi.outputs['Distance'], [(0.45, '#ffffff'), (0.6, '#000000')])
    puddle_mask = b.brightness(puddle_ramp)
    # the tutorial only drives Roughness with the puddle mask; to SEE it in the colour picture we also darken and tint the puddle area a little
    colour = b.mix(colour, '#59656f', b.mul(b.invert(puddle_mask), 0.0))
    height = b.brightness(colour)
    return b.finish(colour, height, b.mixf(0.9, 0.05, b.invert(puddle_mask)), 0.0)
