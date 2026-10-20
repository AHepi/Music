# What this does: a fully procedural, seamless ROOF SLATE recipe made only from Blender shader nodes.
# Idea in one sentence: cut the tile into 8 rows; in every row choose how many slates there are (6, 7 or 8), slide the row by a random
# amount and squeeze/stretch the slate widths with a gentle repeating wave, so no two rows line up; then draw each slate with a
# black gap at the bottom and sides, a light chipped rim along the bottom edge, vertical brush-stroke colour steps, olive moss
# patches near the top and pale lichen near the bottom.
# Chain, in order:
#   1) row = floor(v * 8), row random numbers (slate count, slide, wave phase)
#   2) u moved by slide + two repeating sine waves (period fits exactly into the tile, so it still wraps), times the slate count
#      -> column number and 0..1 position across the slate
#   3) black gap bottom/sides, chipped light rim along the bottom
#   4) slate colour = base blue-grey chosen per slate + stretched-noise brush strokes in hard steps
#   5) moss = stretched noise limited to the upper part of some slates; lichen = small pale spots near the bottom
#   6) height = brightness of the colour, stretched
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd  # noqa: E402

DEFAULT_PARAMETERS = {'rows': 8, 'seed': 5.0, 'bottom_gap': 0.009, 'side_gap': 0.0065, 'rim': 0.014}


def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    b = bd.Builder('Slate recipe', shift=p.get('shift', (0.0, 0.0)))
    u, v = b.uv_xy()
    rows = p['rows']
    v_rows = b.add(b.mul(v, rows), 0.5)                                       # half a row of shift so the tile edge cuts through slates, not through a gap
    row_id = b.mod(b.floor(v_rows), rows)
    fy = b.frac(v_rows)                                                       # 0 at the bottom of the slate row, 1 at the top
    # ---- per-row random numbers
    r_count = b.hash2(row_id, 0.0, p['seed'])
    r_slide = b.hash2(row_id, 0.0, p['seed'] + 1.0)
    r_phase1 = b.hash2(row_id, 0.0, p['seed'] + 2.0)
    r_phase2 = b.hash2(row_id, 0.0, p['seed'] + 3.0)
    count = b.add(b.floor(b.mul(r_count, 2.999)), 6.0)                        # 6, 7 or 8 slates in this row
    # ---- squeeze and stretch the slate widths: u plus two waves that repeat exactly 3 and 7 times across the tile
    wave1 = b.mul(b.math('SINE', b.add(b.mul(u, 2 * math.pi * 3), b.mul(r_phase1, 2 * math.pi))), 0.40 / (2 * math.pi * 3))
    wave2 = b.mul(b.math('SINE', b.add(b.mul(u, 2 * math.pi * 7), b.mul(r_phase2, 2 * math.pi))), 0.20 / (2 * math.pi * 7))
    u_shifted = b.add(b.add(b.add(u, r_slide), wave1), wave2)
    slate_position = b.mul(u_shifted, count)
    column_raw = b.floor(slate_position)
    fx = b.frac(slate_position)
    column_id = b.mod(column_raw, count)
    r_tint = b.hash2(column_id, row_id, p['seed'] + 10.0)
    r_moss = b.hash2(column_id, row_id, p['seed'] + 11.0)
    r_lichen = b.hash2(column_id, row_id, p['seed'] + 12.0)
    r_seed = b.mul(b.hash2(column_id, row_id, p['seed'] + 13.0), 60.0)

    # ---- edges: black gap bottom and sides, light chipped rim along the bottom
    fy_tile = b.div(fy, rows)
    chip_noise = b.tnoise(110, 45, detail=3, roughness=0.65, seed=p['seed'] + 20.0)
    chip = b.mul(b.sub(chip_noise, 0.5), 0.016)
    bottom_distance = b.add(fy_tile, chip)
    bottom_gap = b.invert(b.window(bottom_distance, p['bottom_gap'], p['bottom_gap']))
    rim_zone = b.invert(b.window(bottom_distance, p['bottom_gap'] + p['rim'], p['bottom_gap'] + p['rim']))
    side_noise = b.tnoise(40, 90, detail=3, roughness=0.65, seed=p['seed'] + 21.0)
    side_distance = b.add(b.div(b.mn(fx, b.invert(fx)), count), b.mul(b.sub(side_noise, 0.5), 0.008))
    side_gap = b.invert(b.window(side_distance, p['side_gap'], p['side_gap']))
    gap = b.mx(bottom_gap, side_gap)

    # ---- slate colour: brush strokes. Noise on the slate's own square, stretched up-down, cut into hard steps
    slate_aspect = b.div(rows, count)                                         # slate width / slate height
    stroke_vector = b.vec(b.mul(fx, b.mul(slate_aspect, 9.0)), b.mul(fy, 1.5), 0.0)
    strokes = b.noise(stroke_vector, 1.0, 4.0, 0.55, 0.35, r_seed, '4D').outputs['Factor']
    dark_set = b.ramp(strokes, [(0.0, '#22272a'), (0.36, '#2b3235'), (0.50, '#353e42'), (0.64, '#414c50'), (0.8, '#4f5b5f')], 'CONSTANT')
    blue_set = b.ramp(strokes, [(0.0, '#2c3943'), (0.36, '#35434d'), (0.50, '#415360'), (0.64, '#506571'), (0.8, '#627a86')], 'CONSTANT')
    slate = b.mix(dark_set, blue_set, b.window(r_tint, 0.45, 0.46))
    slate_strokes_only = slate
    # big blotches that cross the slate (darker, flat)
    blotch = b.noise(b.vec(b.mul(fx, b.mul(slate_aspect, 1.6)), b.mul(fy, 1.3), 0.0), 1.0, 3.0, 0.5, 0.3, b.add(r_seed, 5.0), '4D').outputs['Factor']
    slate = b.mix(slate, '#262b2f', b.mul(b.maprange(blotch, 0.56, 0.59), 0.7))
    slate_with_blotches = slate

    # ---- moss: olive streaks hanging from the upper part, only on some slates
    moss_vector = b.vec(b.mul(fx, b.mul(slate_aspect, 6.0)), b.mul(fy, 1.2), 0.0)
    moss_noise = b.noise(moss_vector, 1.0, 5.0, 0.6, 0.5, b.add(r_seed, 17.0), '4D').outputs['Factor']
    moss_cut = b.maprange(r_moss, 0.3, 0.9, 0.66, 0.5)                          # mossy slates accept more of the noise
    moss_mask = b.mul(b.maprange(moss_noise, moss_cut, b.add(moss_cut, 0.02)), b.maprange(fy, 0.25, 0.9))
    moss_colour = b.ramp(moss_noise, [(0.0, '#59602c'), (0.6, '#6c7436'), (0.75, '#7d8541')], 'CONSTANT')
    slate = b.mix(slate, moss_colour, b.mul(moss_mask, 0.92))
    slate_with_moss = slate

    # ---- pale lichen / dust spots near the bottom edge, and the light rim
    spot_noise = b.noise(b.vec(b.mul(fx, b.mul(slate_aspect, 5.0)), b.mul(fy, 5.0), 0.0), 1.0, 4.0, 0.6, 0.0, b.add(r_seed, 31.0), '4D').outputs['Factor']
    lichen_mask = b.mul(b.mul(b.maprange(spot_noise, 0.60, 0.62), b.maprange(fy, 0.45, 0.05)), b.window(r_lichen, 0.35, 0.36))
    slate = b.mix(slate, '#9b8a76', lichen_mask)
    rim_colour = b.ramp(chip_noise, [(0.0, '#6c7473'), (0.5, '#8a8a82'), (0.7, '#aaa392')], 'CONSTANT')
    rim_broken = b.window(b.tnoise(70, 30, detail=2, roughness=0.6, seed=p['seed'] + 40.0), 0.45, 0.47)
    slate = b.mix(slate, rim_colour, b.mul(b.mul(rim_zone, b.invert(bottom_gap)), rim_broken))
    surface = b.mix(slate, '#0c0d0e', gap)

    if p.get('stage'):
        flat = '#3d474d'
        views = {'1 layout: gaps': b.mix(flat, '#0c0d0e', gap), '2 + brush strokes, tone per slate': b.mix(slate_strokes_only, '#0c0d0e', gap),
                 '3 + blotches': b.mix(slate_with_blotches, '#0c0d0e', gap), '4 + moss': b.mix(slate_with_moss, '#0c0d0e', gap), '5 + lichen, chipped rim': surface}
        surface = views[p['stage']]
    height = b.maprange(b.height_from_colour(surface), 0.02, 0.52)
    return b.finish(surface, height, 0.85, 0.0)
