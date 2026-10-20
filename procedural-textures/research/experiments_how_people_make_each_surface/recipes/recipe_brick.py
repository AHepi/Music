# What this does: a fully procedural, seamless (tile-wrapping) BRICK WALL recipe made only from Blender shader nodes.
# Idea in one sentence: work out which brick every pixel is on, give each brick its own random numbers, draw a rough-edged brick
# shape inside a dark outline with tan mortar around it, then paint each brick with hard-edged patches (lighter orange, soot
# streaks, pale spalled spots) whose pattern is different on every brick.
# Chain, in order:  1) layout = 4 columns x 12 rows, every second row shifted half a brick (rows_and_columns)
#   2) per-brick random numbers from a White Noise of (column, row)   3) rough edge = distance to the nearest brick side
#   plus a little seamless noise   4) brick colour = per-brick base ramp, then hard-edged patches on top
#   5) mortar colour = tan + fine grain   6) dark outline = a thin band just inside the brick edge   7) height = brightness of the colour
# Use with the bake harness (see ../bake_and_score.sh):  recipes/recipe_brick.py   (build_node_group(parameters) is what the harness calls)
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd  # noqa: E402

DEFAULT_PARAMETERS = {
    'columns': 4, 'rows': 12, 'row_shift': 0.5,        # 4 whole bricks across and 12 rows (even number) so the tile wraps
    'gap': 0.0185,                                      # width of the mortar joint in tile units (0.0185 = 23 pixels at 1254)
    'edge_wobble': 0.0065,                              # how far chips bite into the brick edge (tile units)
    'outline': 0.0045,                                  # width of the dark outline just inside the edge
    'seed': 3.0,
}


def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    b = bd.Builder('Brick recipe', shift=p.get('shift', (0.0, 0.0)))
    layout = b.rows_and_columns(p['columns'], p['rows'], p['row_shift'])
    cid, rid, fx, fy = layout['column_id'], layout['row_id'], layout['fx'], layout['fy']
    # ---- per-brick random numbers (each 0..1), different for every brick, identical after one tile of movement
    r_tint = b.hash2(cid, rid, p['seed'])
    r_soot = b.hash2(cid, rid, p['seed'] + 11.0)
    r_spall = b.hash2(cid, rid, p['seed'] + 23.0)
    r_seed = b.mul(b.hash2(cid, rid, p['seed'] + 37.0), 50.0)

    # ---- distance from the nearest brick side, in tile units (so the mortar joint has the same width in both directions)
    dist_x = b.div(b.mn(fx, b.invert(fx)), p['columns'])
    dist_y = b.div(b.mn(fy, b.invert(fy)), p['rows'])
    edge_distance = b.mn(dist_x, dist_y)
    wobble_noise = b.tnoise(70, 70, detail=3, roughness=0.65, seed=p['seed'])
    wobble = b.mul(b.sub(wobble_noise, 0.5), 2 * p['edge_wobble'])            # roughly -wobble .. +wobble
    wobbly_distance = b.add(edge_distance, wobble)
    half_gap = p['gap'] / 2.0
    brick_mask = b.window(wobbly_distance, half_gap, half_gap)               # 1 on the brick, 0 on the mortar (hard edge)
    outline_mask = b.invert(b.window(wobbly_distance, half_gap + p['outline'], half_gap + p['outline']))   # 1 on the dark outline band

    # ---- per-brick coordinates for patterns that are different on every brick (noise on the brick's own 0..1 square)
    brick_aspect = (1.0 / p['columns']) / (1.0 / p['rows'])
    local = b.vec(b.mul(fx, brick_aspect), fy, 0.0)

    # ---- brick base colour: 5 base reds picked by the brick's random number, hard steps between them
    base = b.ramp(r_tint, [(0.0, '#6d3226'), (0.2, '#7f3a26'), (0.45, '#93422a'), (0.7, '#a64b2c'), (0.9, '#b5542e')], 'CONSTANT')
    # lighter / darker flat patches that differ from brick to brick: noise on local coordinates with the brick's own W seed
    blotch = b.noise(local, 1.3, 4.0, 0.55, 0.45, r_seed, '4D').outputs['Factor']
    blotch_hard = b.maprange(blotch, 0.46, 0.50)                                # hard-edged mask
    patch_light = b.mix(base, '#c4602f', blotch_hard)                          # bright orange patches
    blotch2 = b.noise(local, 2.2, 3.0, 0.6, 0.35, b.add(r_seed, 7.0), '4D').outputs['Factor']
    patch_dark = b.mix(patch_light, '#5b2b20', b.mul(b.maprange(blotch2, 0.54, 0.57), 0.85))
    # spalled pale patches (the clay face has flaked off): only on some bricks (random > 0.6)
    spall_noise = b.noise(local, 1.8, 4.0, 0.6, 0.6, b.add(r_seed, 13.0), '4D').outputs['Factor']
    spall = b.mul(b.maprange(spall_noise, 0.60, 0.63), b.window(r_spall, 0.55, 0.56))
    with_spall = b.mix(patch_dark, '#a5805f', spall)
    # soot streaks: stretched noise (long in the up-down direction) on the brick's local square, strong only on some bricks
    soot_vector = b.vec(b.mul(fx, brick_aspect * 2.2), b.mul(fy, 0.8), 0.0)
    soot_noise = b.noise(soot_vector, 1.0, 3.0, 0.55, 0.5, b.add(r_seed, 29.0), '4D').outputs['Factor']
    soot_limit = b.maprange(r_soot, 0.35, 0.8, 0.70, 0.46)                      # sooty bricks accept more of the noise
    soot = b.maprange(soot_noise, soot_limit, b.add(soot_limit, 0.03))
    soot_vertical_fade = b.maprange(fy, 0.0, 1.0, 1.0, 0.55)                  # streaks hang from the top of the brick
    soot_final = b.mul(b.mul(soot, soot_vertical_fade), 0.95)
    brick_colour = b.mix(with_spall, '#2a211e', soot_final)

    # ---- mortar: tan with fine grain and lighter chips, darker next to the bricks
    grain = b.tnoise(90, 90, detail=3, roughness=0.6, seed=p['seed'] + 5.0)
    chips = b.tnoise(26, 26, detail=4, roughness=0.6, seed=p['seed'] + 9.0)
    mortar = b.ramp(grain, [(0.30, '#86735c'), (0.5, '#a08c72'), (0.72, '#b5a287')])
    mortar = b.mix(mortar, '#cdbb9f', b.maprange(chips, 0.58, 0.62))
    mortar_shadow = b.invert(b.window(wobbly_distance, half_gap - 0.004, half_gap + 0.004, soft=True))
    mortar = b.mix(mortar, '#43372d', b.mul(mortar_shadow, 0.7))

    # ---- combine: brick over mortar, then the dark outline
    surface = b.mix(mortar, brick_colour, brick_mask)
    surface = b.mix(surface, '#241b17', b.mul(outline_mask, brick_mask))
    surface_after_outline = surface
    big_soot = b.tnoise(6, 2.6, detail=5, roughness=0.62, distortion=1.0, seed=p['seed'] + 31.0)
    big_soot_mask = b.mul(b.maprange(big_soot, 0.585, 0.595), 0.9)           # hard edged smudges that run across several bricks
    surface = b.mix(surface, '#1d1614', b.mul(big_soot_mask, brick_mask))
    # a grain of fine noise over everything so flat areas are not perfectly flat
    fine = b.tnoise(140, 140, detail=1, roughness=0.5, seed=p['seed'] + 2.0)
    surface = b.mix(surface, b.mix(surface, '#000000', 0.18), b.maprange(fine, 0.55, 0.75))

    if p.get('stage'):                       # 'stage' = show the picture as it looks after one step only (used for the layer-by-layer strips in the guide)
        flat_mortar = '#8a7e6c'
        views = {'1 layout only': b.mix(flat_mortar, '#9c452c', brick_mask), '2 + colour per brick': b.mix(flat_mortar, base, brick_mask),
                 '3 + flat patches': b.mix(flat_mortar, patch_dark, brick_mask), '4 + spalls and soot': b.mix(flat_mortar, brick_colour, brick_mask),
                 '5 + mortar, outline': surface_after_outline, '6 + smudges, grain': surface}
        surface = views[p['stage']]
    height = b.maprange(b.height_from_colour(surface), 0.06, 0.55)      # stretch so mortar is near white and soot near black like the reference
    rough = b.mixf(0.9, 0.97, b.invert(brick_mask))
    return b.finish(surface, height, rough, 0.0)
