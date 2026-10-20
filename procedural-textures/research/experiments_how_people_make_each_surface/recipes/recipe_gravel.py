# What this does: a fully procedural, seamless (tile-wrapping) GRAVEL / ballast recipe made only from Blender shader nodes.
# Idea in one sentence: paint a crumbly orange-brown soil, then lay four layers of angular stones on it (tiny crumbs, small, medium, large),
# each layer one random irregular polygon per grid cell with its own tone (mostly dark and blue-grey, a few rusty orange), a light face
# toward the top-left, a dark face away from it, a dark outline, and flat painterly mottling on top of each stone.
# Chain, in order:
#   1) soil = seamless noise in hard steps + a fine crumb noise
#   2) for each layer (cells across the tile: 72, 30, 15, 8): stone_tools.polygon_stones -> mask, outline, face brightness, random tone
#   3) stone colour = tone ramp (hard steps), + rusty stain on some, + light / dark face, + mottling noise in two flat steps
#   4) height = brightness of the colour, stretched
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd  # noqa: E402
import stone_tools as st  # noqa: E402

DEFAULT_PARAMETERS = {'seed': 9.0, 'sides': None, 'presence_scale': 1.0}     # sides: number of faces of every stone (None = 5, large ones 6); presence_scale: more / fewer stones


def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    b = bd.Builder('Gravel recipe', shift=p.get('shift', (0.0, 0.0)))
    seed = p['seed']

    # ---------------------------------------------------------------- 1) soil
    soil_noise = b.tnoise(26, 26, detail=5, roughness=0.6, distortion=0.4, seed=seed)
    soil = b.ramp(soil_noise, [(0.0, '#3d2318'), (0.28, '#4d2d1e'), (0.45, '#5e3823'), (0.6, '#73452a'), (0.75, '#8a5330'), (0.88, '#a0622f')], 'CONSTANT')
    crumb = b.tnoise(90, 90, detail=2, roughness=0.6, seed=seed + 1.0)
    soil = b.mix(soil, '#c58650', b.mul(b.maprange(crumb, 0.62, 0.64), 0.8))
    soil = b.mix(soil, '#2e1b13', b.mul(b.maprange(crumb, 0.38, 0.36), 0.7))

    # ---------------------------------------------------------------- 3) how one stone layer is painted
    stone_tones = [(0.0, '#101215'), (0.22, '#16181c'), (0.40, '#1f2228'), (0.52, '#2a2f38'), (0.64, '#38414e'), (0.76, '#4b5967'), (0.88, '#5e7080'), (0.95, '#7d5a3d')]

    def paint(surface, layer, rusty_chance, mottle_scale, seed_add):
        body = b.ramp(layer['random_tone'], stone_tones, 'CONSTANT')
        rust_mix = b.window(layer['g'], 1.0 - rusty_chance, 1.0 - rusty_chance + 0.002)
        rust = b.ramp(layer['r'], [(0.0, '#6a3b20'), (0.5, '#84492a'), (0.8, '#9c5a33')], 'CONSTANT')
        body = b.mix(body, rust, rust_mix)
        # flat painterly mottling: two hard-edged noise steps whose pattern differs from stone to stone (noise seed = stone random number)
        mottle = b.tnoise(mottle_scale, mottle_scale, detail=3, roughness=0.55, distortion=0.3, seed=seed + seed_add)
        body = b.mix(body, b.mix(body, '#aab6c0', 0.22), b.mul(b.maprange(mottle, 0.58, 0.60), 0.8))
        body = b.mix(body, b.mix(body, '#000000', 0.35), b.mul(b.maprange(mottle, 0.40, 0.38), 0.8))
        light_face = b.window(layer['face'], 0.28, 0.30)
        dark_face = b.invert(b.window(layer['face'], -0.30, -0.28))
        body = b.mix(body, b.mix(body, '#bfcad4', 0.20), b.mul(light_face, 0.9))
        body = b.mix(body, b.mix(body, '#000000', 0.42), b.mul(dark_face, 0.9))
        surface = b.mix(surface, body, layer['mask'])
        return b.mix(surface, '#0d0e11', b.mul(layer['outline'], 0.9))

    surface = soil
    sides = p['sides'] or 5
    k = p['presence_scale']
    tiny = st.polygon_stones(b, 72, seed + 10.0, presence=min(1.0, 0.55 * k), radius_low=0.22, radius_high=0.46, warp=0.6, outline_width=0.12, sides=sides)
    small = st.polygon_stones(b, 30, seed + 11.0, presence=min(1.0, 0.62 * k), radius_low=0.26, radius_high=0.48, warp=0.6, sides=sides)
    medium = st.polygon_stones(b, 15, seed + 12.0, presence=min(1.0, 0.60 * k), radius_low=0.28, radius_high=0.48, warp=0.6, sides=sides)
    large = st.polygon_stones(b, 8, seed + 13.0, presence=min(1.0, 0.55 * k), radius_low=0.30, radius_high=0.48, warp=0.5, sides=(p['sides'] or 6))
    surface = paint(surface, tiny, 0.45, 40, 20.0)
    after_tiny = surface
    surface = paint(surface, small, 0.12, 22, 21.0)
    after_small = surface
    surface = paint(surface, medium, 0.10, 14, 22.0)
    after_medium = surface
    surface = paint(surface, large, 0.10, 9, 23.0)

    if p.get('stage'):
        views = {'1 soil only': soil, '2 + tiny stones': after_tiny, '3 + small stones': after_small, '4 + medium stones': after_medium, '5 + large stones': surface}
        surface = views[p['stage']]
    height = b.maprange(b.height_from_colour(surface), 0.03, 0.45)
    return b.finish(surface, height, 0.85, 0.0)
