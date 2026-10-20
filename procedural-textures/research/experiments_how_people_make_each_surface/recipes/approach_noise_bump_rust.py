# What this does: the "procedural rusted metal" chain from JSAbbott's Blender Bazaar tutorial (24 Feb 2024, Blender 4.0): Noise (scale 3, detail 12)
# through a ramp (white stop 0.495) for height; colour = ramp 1 (mid grey '#858585', black stop 0.4, white 0.75) and ramp 2 (rust orange/red stops
# '#832912', '#8B310B') mixed with Screen. Whole plate has no layout (no straps, no rivets). Not seamless.
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd


def build_node_group(parameters):
    b = bd.Builder('Rust chain from the tutorial')
    vector = b.uv()
    n3 = b.noise(vector, 3.0, 12.0, 0.5).outputs['Factor']
    n6 = b.noise(vector, 6.0, 24.0, 0.5).outputs['Factor']
    metal = b.ramp(n3, [(0.4, '#000000'), (0.75, '#858585')])
    rust = b.ramp(n3, [(0.0, '#000000'), (0.3, '#8B310B'), (0.7, '#832912')])
    colour = b.mix(metal, rust, 0.5, 'SCREEN')
    height = b.add(b.maprange(n3, 0.495, 1.0), b.mul(n6, 0.1))
    return b.finish(colour, b.clamp01(height), 0.5, 1.0)
