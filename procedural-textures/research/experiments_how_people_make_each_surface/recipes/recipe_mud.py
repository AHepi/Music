# What this does: a fully procedural, seamless (tile-wrapping) WET MUD recipe with ruts, blue-grey puddles and stones, made only from
# Blender shader nodes.
# Idea in one sentence: bend a diagonal coordinate s = u + v with a slow noise and a repeating sine wave so that bands of constant s are
# long S-shaped curves (the ruts); paint the ground in flat brown steps with streaks that follow the ruts; fill the lowest parts of a
# big soft noise with blue-grey puddles that have ragged edges and a dark wet rim; scatter angular stones made from shrunk Voronoi cells
# at three sizes (big, medium, pebbles that gather in clusters).
# Chain, in order:
#   1) s = u + v + 0.35 x (noise - 0.5) + 0.05 x sin(2 pi (2u - v)); every whole number added to u or v adds a whole number to s, so it still wraps
#   2) rut cross-section c = |fract(3 s) - 0.5|: dark groove where c is small, lighter banks just outside it
#   3) ground = noise in hard steps + streaks from a noise stretched ALONG the ruts (noise read in (s, v) coordinates)
#   4) puddle = low part of a soft noise plus a fine jagged noise, ruts pull it lower; wet rim = a band just outside the puddle
#   5) stones: three layers of random polygons, one per grid cell (stone_tools.polygon_stones): size and tone from the cell's random numbers, light / dark face from the direction each flat face looks
#   6) height = brightness of the colour, stretched
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd  # noqa: E402
import stone_tools as st  # noqa: E402

DEFAULT_PARAMETERS = {'seed': 6.0, 'rut_count': 4}


def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    b = bd.Builder('Mud recipe', shift=p.get('shift', (0.0, 0.0)))
    u, v = b.uv_xy()
    seed = p['seed']

    # ---------------------------------------------------------------- 1) the rut coordinate
    bend_noise = b.tnoise(2, 2, detail=3, roughness=0.5, seed=seed)
    wave = b.math('SINE', b.add(b.sub(b.mul(u, 2 * math.pi * 2), b.mul(v, 2 * math.pi)), 1.0))
    s = b.add(b.add(b.add(u, v), b.mul(b.sub(bend_noise, 0.5), 0.55)), b.mul(wave, 0.045))
    bend_noise2 = b.tnoise(2, 2, detail=3, roughness=0.5, seed=seed + 20.0)
    wave2 = b.math('SINE', b.add(b.add(b.mul(u, 2 * math.pi), b.mul(v, 2 * math.pi * 3)), 2.0))
    s2 = b.add(b.add(b.sub(u, v), b.mul(b.sub(bend_noise2, 0.5), 0.5)), b.mul(wave2, 0.04))     # a second family of ruts running the other way
    c = b.absolute(b.sub(b.frac(b.mul(s, p['rut_count'])), 0.5))                  # 0 on the rut centre line, 0.5 half way between two ruts
    c2 = b.absolute(b.sub(b.frac(b.mul(s2, 2.0)), 0.5))
    rut_gate2 = b.window(b.tnoise(3, 3, detail=2, roughness=0.5, seed=seed + 21.0), 0.45, 0.55)      # the second family only shows in places
    groove = b.invert(b.window(c, 0.035, 0.05))
    groove2 = b.mul(b.invert(b.window(c2, 0.03, 0.045)), rut_gate2)
    groove = b.mx(groove, groove2)
    bank = b.mul(b.window(c, 0.05, 0.05), b.invert(b.window(c, 0.09, 0.14)))
    inner_line = b.mul(groove, b.invert(b.window(b.absolute(b.sub(c, 0.02)), 0.006, 0.008)))      # a thin dark line inside the groove (wheel edge)

    # ---------------------------------------------------------------- 3) ground colour
    ground_noise = b.tnoise(12, 12, detail=5, roughness=0.6, distortion=0.35, seed=seed + 1.0)
    ground = b.ramp(ground_noise, [(0.0, '#4a2f22'), (0.30, '#5b3a28'), (0.45, '#6d4630'), (0.58, '#80533a'), (0.72, '#966244'), (0.86, '#ab7552')], 'CONSTANT')
    streak = b.tnoise(34, 5, detail=4, roughness=0.6, seed=seed + 2.0, coords=(s, v))     # noise stretched along the rut direction
    ground = b.mix(ground, '#3b2820', b.mul(b.maprange(streak, 0.56, 0.58), 0.8))
    ground = b.mix(ground, '#b3805a', b.mul(b.maprange(streak, 0.68, 0.70), 0.7))
    clumps = b.tnoise(46, 46, detail=2, roughness=0.55, seed=seed + 3.0)
    ground = b.mix(ground, '#a06c49', b.mul(b.maprange(clumps, 0.64, 0.66), 0.7))
    ground = b.mix(ground, '#4d3226', b.mul(b.maprange(clumps, 0.34, 0.32), 0.6))
    ground_no_ruts = ground
    # ruts: dark wet groove, lighter banks, a thin darker wheel line
    ground = b.mix(ground, '#2f211b', b.mul(groove, 0.9))
    ground = b.mix(ground, '#bb875f', b.mul(bank, 0.6))
    ground = b.mix(ground, '#1c1411', b.mul(inner_line, 0.8))

    # ---------------------------------------------------------------- 4) puddles
    puddle_noise = b.tnoise(3.5, 3.5, detail=4, roughness=0.55, distortion=0.3, seed=seed + 4.0)
    jag = b.tnoise(60, 60, detail=2, roughness=0.55, seed=seed + 5.0)
    puddle_value = b.sub(b.add(puddle_noise, b.mul(b.sub(jag, 0.5), 0.18)), b.mul(groove, 0.05))
    puddle = b.invert(b.window(puddle_value, 0.40, 0.40))
    rim = b.mul(b.invert(b.window(puddle_value, 0.44, 0.44)), b.invert(puddle))
    cloud = b.tnoise(7, 7, detail=3, roughness=0.55, distortion=0.2, seed=seed + 6.0)
    water = b.ramp(cloud, [(0.0, '#434c57'), (0.38, '#546270'), (0.5, '#66767f'), (0.62, '#778894'), (0.8, '#8c9aa5')], 'CONSTANT')
    dark_reflection = b.mul(b.maprange(b.tnoise(14, 14, detail=3, roughness=0.5, seed=seed + 7.0), 0.60, 0.62), 0.7)
    water = b.mix(water, '#2f3640', dark_reflection)
    ground_with_ruts = ground
    surface = b.mix(ground, '#35261f', b.mul(rim, 0.85))
    surface = b.mix(surface, water, puddle)
    surface_puddles = surface

    # ---------------------------------------------------------------- 5) stones (random polygons, one per grid cell: see stone_tools.polygon_stones)
    def paint_stones(surface, layer, dark_tones, tan_chance):
        tone = b.ramp(layer['random_tone'], dark_tones, 'CONSTANT')
        tan = b.ramp(layer['random_tone'], [(0.0, '#6f5239'), (0.5, '#85644a'), (0.8, '#9a7757')], 'CONSTANT')
        body = b.mix(tone, tan, b.window(layer['g'], 1.0 - tan_chance, 1.0 - tan_chance + 0.002))
        light_face = b.window(layer['face'], 0.30, 0.32)
        dark_face = b.invert(b.window(layer['face'], -0.30, -0.28))
        body = b.mix(body, b.mix(body, '#c8d0d8', 0.34), b.mul(light_face, 0.9))
        body = b.mix(body, b.mix(body, '#000000', 0.45), b.mul(dark_face, 0.9))
        surface = b.mix(surface, body, layer['mask'])
        return b.mix(surface, '#12151a', b.mul(layer['outline'], 0.9))

    dark_tones = [(0.0, '#1d2229'), (0.3, '#272d36'), (0.6, '#323a46'), (0.85, '#414b59')]
    big = st.polygon_stones(b, 12, seed + 10.0, presence=0.12, radius_low=0.22, radius_high=0.40, warp=0.5)
    medium = st.polygon_stones(b, 24, seed + 11.0, presence=0.28, radius_low=0.20, radius_high=0.40, warp=0.6)
    cluster = b.window(b.tnoise(5, 5, detail=3, roughness=0.5, seed=seed + 12.0), 0.50, 0.51)
    small = st.polygon_stones(b, 52, seed + 13.0, presence=0.7, radius_low=0.16, radius_high=0.40, warp=0.6)
    small['mask'] = b.mul(small['mask'], cluster)
    small['outline'] = b.mul(small['outline'], cluster)
    surface = paint_stones(surface, small, dark_tones, 0.15)
    surface_pebbles = surface
    surface = paint_stones(surface, medium, dark_tones, 0.22)
    surface = paint_stones(surface, big, dark_tones, 0.15)

    if p.get('stage'):
        views = {'1 flat brown ground, streaks': ground_no_ruts, '2 + ruts': ground_with_ruts, '3 + puddles': surface_puddles, '4 + pebble clusters': surface_pebbles,
                 '5 + medium and big stones': surface}
        surface = views[p['stage']]
    height = b.maprange(b.height_from_colour(surface), 0.03, 0.50)
    rough = b.mixf(b.mixf(0.9, 0.7, rim), 0.12, puddle)
    return b.finish(surface, height, rough, 0.0)
