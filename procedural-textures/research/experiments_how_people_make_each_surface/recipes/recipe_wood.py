# What this does: a fully procedural, seamless (tile-wrapping) AGED WOOD PLANKS recipe made only from Blender shader nodes.
# Idea in one sentence: cut the tile into 6 horizontal boards of different heights (by bending the up-down coordinate with a repeating
# wave); inside the boards, split the wood into long thin splinter strips with a stretched Voronoi (each strip gets its own random
# tone from the cell's Color output and the dark crack is the cell's Distance to Edge); then add grain, four round knots with
# growth rings, dark splatter blotches in clouds, and a dark gap between boards with tiny pebbles in it.
# Chain, in order:
#   1) boards: v bent by two repeating sine waves, then floor(v * 6) = board number, fraction = position across the board
#   2) per-board random numbers (warm/grey, tint, noise seed, where the end joints are)
#   3) splinter strips = Voronoi stretched 4 across x 26 up the tile: Color -> tone ramp (hard steps), Distance to Edge -> dark crack lines;
#      grain = stretched seamless noise (4 features across the tile, 150 up it); weathered-grey patches = stretched noise limited by the board's greyness
#   4) cracks = Voronoi "Distance to Edge" stretched along the boards, shown only where a second noise is high, and thinner where it is lower
#   5) knots = rings round a fixed centre (distance with an ellipse, then fract() of distance times a ring count, wobbled by noise)
#   6) splatter = small noise blobs allowed only inside a cloud noise;  7) gaps and end joints in near-black with pebbles
#   8) height = brightness of the colour, stretched
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd  # noqa: E402

DEFAULT_PARAMETERS = {'boards': 6, 'seed': 2.0, 'gap': 0.0048,
                      'knots': [(0.79, 0.915, 1.0), (0.28, 0.705, 1.15), (0.135, 0.375, 1.0), (0.665, 0.29, 0.8)]}


def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    b = bd.Builder('Wood recipe', shift=p.get('shift', (0.0, 0.0)))
    u, v = b.uv_xy()
    nb = p['boards']
    # ---- boards of different heights: bend v with two waves that repeat exactly 2 and 5 times
    bend1 = b.mul(b.math('SINE', b.add(b.mul(v, 2 * math.pi * 2), 1.3)), 0.40 / (2 * math.pi * 2))
    bend2 = b.mul(b.math('SINE', b.add(b.mul(v, 2 * math.pi * 5), 0.4)), 0.16 / (2 * math.pi * 5))
    v_bent = b.add(b.add(v, bend1), bend2)
    board_pos = b.mul(v_bent, nb)
    board_raw = b.floor(board_pos)
    board_id = b.mod(board_raw, nb)
    fb = b.frac(board_pos)                                                    # 0 at the bottom of the board, 1 at the top
    r_grey = b.hash2(board_id, 0.0, p['seed'])
    r_tint = b.hash2(board_id, 0.0, p['seed'] + 1.0)
    r_cut1 = b.hash2(board_id, 0.0, p['seed'] + 2.0)
    r_cut2 = b.hash2(board_id, 0.0, p['seed'] + 3.0)
    board_seed = b.mul(r_tint, 40.0)

    # ---- end joints: two cuts per board, splitting it into two pieces with their own tint
    cut_a = r_cut1
    cut_b = b.frac(b.add(r_cut1, b.add(0.3, b.mul(r_cut2, 0.4))))
    to_a = b.frac(b.sub(u, cut_a))
    piece = b.lt(to_a, b.frac(b.sub(cut_b, cut_a)))                           # 1 inside the first arc, 0 in the second
    r_piece = b.hash2(board_id, piece, p['seed'] + 4.0)
    joint_a = b.invert(b.window(b.mn(to_a, b.invert(to_a)), 0.0028, 0.0028))
    to_b = b.frac(b.sub(u, cut_b))
    joint_b = b.invert(b.window(b.mn(to_b, b.invert(to_b)), 0.0028, 0.0028))
    joint = b.mul(joint_a, b.window(r_cut2, 0.55, 0.56))

    # ---- splinter strips: long thin Voronoi cells. Each cell gets a random tone; the board's greyness shifts the odds toward grey
    strips = b.tvoronoi(3, 30, seed=p['seed'] + 50.0, feature='F1', randomness=0.85)
    strip_r, strip_g, strip_b = b.channels(strips.outputs['Color'])
    grey_choice = b.add(strip_g, b.mul(b.sub(r_grey, 0.5), 0.7))
    warm = b.ramp(strip_r, [(0.0, '#2b1e17'), (0.18, '#392921'), (0.38, '#46362d'), (0.58, '#543f33'), (0.76, '#684a36'), (0.9, '#7d5a40')], 'CONSTANT')
    grey = b.ramp(strip_r, [(0.0, '#33302e'), (0.3, '#3f3b38'), (0.6, '#4c4642'), (0.85, '#5b544f')], 'CONSTANT')
    blue = b.ramp(strip_r, [(0.0, '#3a3f48'), (0.5, '#454b55'), (0.8, '#535a65')], 'CONSTANT')
    base = b.mix(warm, grey, b.window(grey_choice, 0.70, 0.71))
    base = b.mix(base, blue, b.window(grey_choice, 1.02, 1.03))
    # grain: noise stretched along the board, in hard steps
    grain = b.tnoise(4, 220, detail=4, roughness=0.6, distortion=0.0, seed=board_seed)
    grain_wide = b.tnoise(3, 40, detail=3, roughness=0.55, seed=b.add(board_seed, 9.0))
    light_streak = b.maprange(grain, 0.57, 0.59)
    dark_streak = b.maprange(grain, 0.43, 0.41)
    colour = b.mix(base, '#8d6540', b.mul(light_streak, 0.5))
    colour = b.mix(colour, '#2f221b', b.mul(dark_streak, 0.55))
    # big weathered patches: horizontal, bluish grey, mostly on grey boards
    patch_noise = b.tnoise(3.5, 14, detail=4, roughness=0.6, distortion=0.4, seed=b.add(board_seed, 3.0))
    patch_cut = b.maprange(r_grey, 0.0, 1.0, 0.72, 0.56)
    patch = b.maprange(patch_noise, patch_cut, b.add(patch_cut, 0.02))
    colour = b.mix(colour, '#535968', b.mul(patch, 0.7))
    # lighter bare wood where the surface has flaked: warm orange, thin and long
    flake_noise = b.tnoise(5, 60, detail=3, roughness=0.6, distortion=0.3, seed=b.add(board_seed, 5.0))
    flake = b.maprange(flake_noise, 0.66, 0.675)
    colour = b.mix(colour, '#a8703b', b.mul(flake, 0.65))

    colour_after_grain = colour
    # ---- cracks: the border between neighbouring splinter strips (same cells, Distance to Edge), thick where a gate noise is high
    edges = b.tvoronoi(3, 30, seed=p['seed'] + 50.0, feature='DISTANCE_TO_EDGE', randomness=0.85)
    crack_gate = b.tnoise(5, 7, detail=3, roughness=0.6, seed=p['seed'] + 7.0)
    crack_width = b.add(0.008, b.mul(b.maprange(crack_gate, 0.45, 0.7), 0.04))
    edge_distance = edges.outputs['Distance']
    crack = b.lt(edge_distance, crack_width)
    chip_zone = b.mul(b.lt(edge_distance, b.mul(crack_width, 2.6)), b.invert(crack))
    colour = b.mix(colour, '#8f5f35', b.mul(b.mul(chip_zone, b.window(crack_gate, 0.55, 0.56)), 0.6))
    colour = b.mix(colour, '#1b1310', b.mul(crack, 0.95))

    colour_after_cracks = colour
    # ---- knots: rings round fixed centres
    for index, (ku, kv, size) in enumerate(p['knots']):
        dx = b.sub(u, ku)
        dy = b.mul(b.sub(v, kv), 1.5)
        distance = b.math('SQRT', b.add(b.mul(dx, dx), b.mul(dy, dy)))
        wobble = b.tnoise(9, 9, detail=2, roughness=0.5, seed=p['seed'] + 20.0 + index)
        rings = b.frac(b.add(b.mul(distance, 95.0 / size), b.mul(wobble, 1.2)))
        ring_line = b.invert(b.window(rings, 0.28, 0.30))
        zone = b.invert(b.window(distance, 0.055 * size, 0.057 * size))
        inner = b.mix('#74492c', '#2e1d13', b.mul(ring_line, 0.9))
        core = b.invert(b.window(distance, 0.011 * size, 0.012 * size))
        inner = b.mix(inner, '#120c09', core)
        colour = b.mix(colour, inner, zone)

    colour_after_knots = colour
    # ---- splatter blotches in clouds
    cloud = b.tnoise(3.2, 3.2, detail=3, roughness=0.6, seed=p['seed'] + 30.0)
    spots = b.tnoise(42, 42, detail=2, roughness=0.55, seed=p['seed'] + 31.0)
    blotch = b.mul(b.maprange(cloud, 0.50, 0.52), b.maprange(spots, 0.60, 0.62))
    colour = b.mix(colour, '#4d321f', b.mul(blotch, 0.9))
    spots2 = b.tnoise(70, 70, detail=1, roughness=0.5, seed=p['seed'] + 32.0)
    colour = b.mix(colour, '#3a2519', b.mul(b.mul(b.maprange(cloud, 0.55, 0.57), b.maprange(spots2, 0.64, 0.66)), 0.8))

    # ---- gaps between boards (near-black) with a few pebbles; end joints
    wobble_gap = b.mul(b.sub(b.tnoise(60, 12, detail=2, roughness=0.6, seed=p['seed'] + 40.0), 0.5), 0.006)
    gap_distance = b.add(b.div(fb, nb), wobble_gap)
    gap = b.invert(b.window(gap_distance, p['gap'], p['gap']))
    pebble_cells = b.tvoronoi(110, 110, seed=p['seed'] + 41.0, feature='F1', randomness=1.0)
    pebbles = b.mul(b.lt(pebble_cells.outputs['Distance'], 0.30), b.invert(b.window(gap_distance, p['gap'] * 2.4, p['gap'] * 2.4)))
    colour = b.mix(colour, '#17100d', b.mul(joint, 0.9))
    surface = b.mix(colour, '#150f0c', gap)
    surface = b.mix(surface, '#46454c', b.mul(pebbles, 0.9))

    if p.get('stage'):
        gap_colour = '#150f0c'
        views = {'1 boards and gaps': b.mix('#5b3d2a', gap_colour, gap), '2 + splinter strips': b.mix(base, gap_colour, gap),
                 '3 + grain, grey patches, flakes': b.mix(colour_after_grain, gap_colour, gap), '4 + cracks': b.mix(colour_after_cracks, gap_colour, gap),
                 '5 + knots': b.mix(colour_after_knots, gap_colour, gap), '6 + splatter, joints, pebbles': surface}
        surface = views[p['stage']]
    height = b.maprange(b.height_from_colour(surface), 0.02, 0.48)
    return b.finish(surface, height, 0.88, 0.0)
