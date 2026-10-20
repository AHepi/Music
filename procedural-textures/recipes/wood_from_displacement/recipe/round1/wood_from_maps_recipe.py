# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# This is THE WOOD-FROM-MAPS RECIPE: the one file the bake harness loads (lib/bake_harness.py asks for build_node_group(parameters)).
# It makes one Blender node group called "WOOD FROM MAPS" whose input is 'Vector' (the surface coordinate, 0..1 in both directions
# over the baked picture) and whose outputs are 'Colour', 'Roughness', 'Metallic' and 'Height' (what the harness photographs).
#
# What it does with the person's maps (this is the whole idea):
#   The uploaded wood DISPLACEMENT map (height) and COLOUR map show 5 rows of weathered boards, but they cannot simply be repeated:
#   they do not wrap (a plain 2 x 2 repeat shows a straight seam) and every repeat shows the same knots and stains. So the recipe
#   uses the maps only as SOURCE MATERIAL and arranges new boards out of them, with nodes only:
#     1. ROWS      The surface is cut into rows (5 per tile, slightly different heights). Every row runs from the middle of a dark gap
#                  to the middle of the next one, as the source rows do (the source is cut gap-middle to gap-middle), so the cut
#                  between two rows lies inside a dark gap, where it cannot be seen, and so does the edge of the tile.
#     2. BOARDS    Every row is cut into boards of random length, shifted sideways by chance from row to row.
#     3. WINDOW    Every board chooses its OWN window of the source: which source row (never the same as its neighbour), where along it, flipped left-right or
#                  upside-down or not, zoomed a little. Knots are rationed (only some boards may show one).
#     4. READ      The height map and the colour map are read at exactly the same position, so colour and relief always match.
#     5. STAINS    Dark stain splotches from the source are stamped on top at random places (two shifted layers of stamps).
#     6. JOINTS    Where one window meets the next there is a dark ragged crack (the board joint) that hides the cut.
#     7. PATCHES   Large soft light/dark drift and dark blotches (not copied from any map) change the look from place to place.
#     8. COLOUR    MAIN version: the colour read from the colour map, plus a small tone change per board.
#                  COMPARISON version (setting colour.source = height_palette): the colour is made from the height with a palette.
#   The normal map is NOT read from the uploaded normal map (a flipped board would have its slopes pointing the wrong way): it is made
#   from the arranged height afterwards (tools/make_normal_from_height.py, strength 8).
#
# Default tile or bigger area, from the same nodes:
#     recipe.tiles_across = 1   one tile of 1254 x 1254 dots that repeats without a seam (every random number repeats after one tile)
#     recipe.tiles_across = 2, 4, 8 ...  a bigger area of NEW boards with the same look per dot (the random numbers keep counting up,
#                          so nothing repeats on purpose). Bake it with 1254 x that many dots (or fewer, it then comes out smaller).
#
# Settings: a flat list of numbers and words in settings.json next to this file, named 'group.control' (for example 'stains.amount').
# Order of strength: the default written in this file  <  settings.json  <  the parameters the caller passes in (for example the
# harness option --params '{"layout.boards_per_row": 2}'). Special parameters (not settings):
#     shift     [u, v]  slides the whole pattern by that much of the picture; used only by the half-tile-shift test.
#     window    [x, y, size]  bakes only a part of a big area: x and y are the top-left corner and size the width, all in TILES
#               (for example [1.5, 2, 1] = the one tile that starts one and a half tiles from the left and two from the top).
#               Default: the whole area [0, 0, tiles_across]. Used to look at full-size crops of a 4 x 4 area.
#     debug_view  shows one thing instead of the finished picture:  'boards' (a random colour per board), 'source_x' / 'source_y'
#               (in the Height output, exactly: which dot of the source map every dot of the picture was taken from, as x / 1254 or
#               y / 1254; used for the reuse count), 'rows' (grey per row), 'flips' (red = flipped left-right, green = upside-down).
#     settings_file  another settings file to use instead of settings.json.
import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))        # the proc-work folder
for folder in (HERE, os.path.join(PROC, 'lib')):
    if folder not in sys.path:
        sys.path.insert(0, folder)
import recipe_tools as rt  # noqa: E402
import wood_node_kit as nk  # noqa: E402

SETTINGS_FILE = os.path.join(HERE, 'settings.json')

# The default of every setting (settings.json repeats them all; the file wins, then the caller's parameters).
DEFAULTS = {
    'recipe.tiles_across': 1, 'recipe.tile_repeats': -1, 'recipe.seed': 1,
    'layout.rows_per_tile': 5, 'layout.row_height_variation': 0.05, 'layout.boards_per_row': 3, 'layout.board_length_variation': 0.6, 'layout.joined_share': 0.5, 'layout.joined_max_length': 0.72,
    'windows.zoom': 0.10, 'windows.flip_left_right': 0.5, 'windows.flip_upside_down': 0.4, 'windows.knot_share': 0.12,
    'boards.tone_variation': 0.24, 'boards.warmth_variation': 0.12, 'boards.height_shift': 0.10,
    'joints.width': 4.0, 'joints.gap_band_width': 4.0, 'joints.raggedness': 0.8, 'joints.notches': 0.8, 'joints.edge_lip': 0.5, 'joints.pebbles': 0.8, 'joints.edge_shade': 0.35, 'joints.wobble_length': 22.0,
    'stains.amount': 0.18, 'stains.size': 85.0, 'stains.zoom': 0.25, 'stains.dark_limit': 135.0, 'stains.dark_softness': 55.0,
    'masks.drift_amount': 0.10, 'masks.drift_size': 2.0, 'masks.blotch_amount': 0.15, 'masks.blotch_size': 5.0, 'masks.darken_height': 0.0,
    'colour.source': 'map',
    'roughness.base': 0.78, 'roughness.from_height': 0.20, 'roughness.board_variation': 0.04,
    'bake.exact_dots': 1, 'bake.shrink_samples': 8, 'bake.shrink_filter': 1.0, 'debug.source_unchanged': 0,
}


def load_settings(path=None):
    """The settings.json dict (empty if the file is missing)."""
    path = path or SETTINGS_FILE
    if os.path.exists(path):
        with open(path) as handle:
            return json.load(handle)
    return {}


def effective_settings(parameters):
    """defaults, overridden by settings.json, overridden by the caller's parameters."""
    merged = dict(DEFAULTS)
    merged.update(load_settings(parameters.get('settings_file')))
    merged.update({k: v for k, v in parameters.items() if k not in ('shift', 'window', 'debug_view', 'settings_file')})
    return merged


def srgb_hex_to_linear(hex_text):
    return rt.srgb_hex_to_linear(hex_text)[:3]


def build_node_group(parameters):
    s = effective_settings(parameters)
    T = float(s['source.size'])
    tiles = int(s['recipe.tiles_across'])
    tile = (tiles == 1) if int(s['recipe.tile_repeats']) < 0 else bool(int(s['recipe.tile_repeats']))
    seed = float(s['recipe.seed'])
    debug = parameters.get('debug_view')
    identity = bool(int(s.get('debug.source_unchanged', 0)))
    window = parameters.get('window') or [0.0, 0.0, float(tiles)]
    shift = parameters.get('shift') or [0.0, 0.0]
    path_height = os.path.join(PROC, s['source.height_file'])
    path_colour = os.path.join(PROC, s['source.colour_file'])
    use_map_colour = (s['colour.source'] == 'map')

    # ---- ask the harness's scene for a photograph that reads every source dot exactly (only when one dot of the picture = one source dot)
    scene = bpy.context.scene
    dots_per_pixel = (window[2] * T) / float(scene.render.resolution_x)
    if int(s['bake.exact_dots']):
        if dots_per_pixel <= 1.05:
            scene.cycles.samples = 1
            scene.cycles.filter_width = 0.01
        else:                                                   # the picture is smaller than the source: average over several samples per dot
            scene.cycles.samples = int(s['bake.shrink_samples'])
            scene.cycles.filter_width = float(s['bake.shrink_filter'])

    tree, w = rt.make_group_tree('WOOD FROM MAPS', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'),
                                  ('Height', 'NodeSocketFloat')])
    kit = nk.Kit(tree)
    S = nk.S

    # =============================================================================================== 0 PLACE
    kit.begin('0 PLACE: where on the surface is this dot (in source dots: one tile = 1254 dots)')
    split = kit._node('ShaderNodeSeparateXYZ')
    tree.links.new(w.nodes['in'].outputs['Vector'], split.inputs[0])
    u, v = S(kit, split.outputs['X']), S(kit, split.outputs['Y'])
    if shift[0]:
        u = u + shift[0]
    if shift[1]:
        v = v + shift[1]
    Px = kit.label(u * (window[2] * T) + window[0] * T, 'Px: dots from the left')
    Py = kit.label((1.0 - v) * (window[2] * T) + window[1] * T, 'Py: dots from the top')

    # =============================================================================================== 1 ROWS
    kit.begin('1 ROWS: rows of slightly different height (they add up to one tile); every row runs from the middle of a gap to the middle of the next')
    R = int(s['layout.rows_per_tile'])
    if tile:
        ty = 0.0
        Pyl = Py % T                                      # the tile repeats: only the position inside the tile counts
        Yg = Pyl
    else:
        ty = kit.floor(Py / T)                            # a bigger area: every tile row has its own random numbers
        Pyl = Py - ty * T
        Yg = Py
    hv = float(s['layout.row_height_variation'])
    ra = kit.rand(ty, 0.0, 11.0, seed)
    rb = kit.rand(ty, 1.0, 11.0, seed)
    rnd = list(ra) + list(rb)
    weights = [1.0 + hv * (2.0 * rnd[m] - 1.0) for m in range(R)]
    total = weights[0]
    for m in range(1, R):
        total = total + weights[m]
    heights = [weights[m] * (T / total) for m in range(R)]        # row heights, adding up to one tile
    bounds = [None]
    running = heights[0]
    for m in range(1, R):
        bounds.append(running)
        if m < R - 1:
            running = running + heights[m]
    steps = [None] + [kit.greater(Pyl, bounds[m]) for m in range(1, R)] + [0.0]       # steps[m] = 1 when the dot is in row m or below
    row_no = steps[1]
    row_top = steps[1] * heights[0]
    for m in range(2, R):
        row_no = row_no + steps[m]
        row_top = row_top + steps[m] * heights[m - 1]
    row_h = heights[0]
    for m in range(1, R):
        row_h = row_h + (steps[m] - steps[m + 1]) * (heights[m] - heights[0])
    kit.label(row_no, 'row number in the tile')
    kit.label(row_h, 'height of this row')
    y_in = kit.label(Pyl - row_top, 'dots below the top of the row')
    rh = row_no if tile else row_no + R * ty                # the row number the random numbers are made from

    # =============================================================================================== 2 BOARDS
    kit.begin('2 BOARDS: random lengths, every row shifted sideways by chance')
    B = int(s['layout.boards_per_row'])
    Lb = T / B
    jit = float(s['layout.board_length_variation'])
    row_shift = kit.rand1(rh, 1.0, 0.0, seed) * Lb
    Xs = Px - row_shift
    j0 = kit.floor(Xs / Lb)

    def hash_index(j):
        return (j % float(B)) if tile else j

    def edge(j):
        return j * Lb + (kit.rand1(rh, hash_index(j), 2.0, seed) - 0.5) * (jit * Lb)

    e0, e1 = edge(j0), edge(j0 + 1.0)
    j = j0 - kit.less(Xs, e0) + kit.greater(Xs, e1)          # the board is the one before, the same, or the one after
    # two neighbouring boards (slot 0 + 1, slot 2 + 3 ...) are sometimes JOINED into one long board with only a partial crack where they would meet,
    # like the stepped half-height cracks of the source (a full cut would need a full crack to hide it; a joined pair has no cut)
    slot = j % float(B)
    is_second = slot - 2.0 * kit.floor(slot * 0.5)           # 1 for the second board of a pair
    pf = j - is_second                                       # the first board of the pair
    pairable = kit.less((slot - is_second) + 1.0, B - 0.5)   # is there a partner slot?
    e_pf, e_mid, e_end = edge(pf), edge(pf + 1.0), edge(pf + 2.0)
    joined_draw = kit.less(kit.rand1(rh, hash_index(pf), 8.0, seed), float(s['layout.joined_share']))
    merged = kit.label(joined_draw * pairable * kit.less(e_end - e_pf, float(s['layout.joined_max_length']) * T), 'two boards joined into one')
    j_eff = kit.where(merged, pf, j)
    start = kit.label(kit.where(merged, e_pf, edge(j)) + row_shift, 'left end of this board')
    end = kit.label(kit.where(merged, e_end, edge(j + 1.0)) + row_shift, 'right end of this board')
    jb, jb_next = hash_index(j_eff), hash_index(j_eff + 1.0 + merged)
    q1, q2, q3 = kit.rand(rh, jb, 3.0, seed)     # start along the source row, flip left-right, tone
    q4, q5, q6 = kit.rand(rh, jb, 4.0, seed)     # warmth, knot board?, which source row
    q7, q8, q9 = kit.rand(rh, jb, 5.0, seed)     # fallback row, zoom, flip upside-down
    q10, q11, q12 = kit.rand(rh, jb, 6.0, seed)  # roughness change, spare, spare

    # =============================================================================================== 3 WINDOW
    kit.begin('3 WINDOW: which piece of the source map this board shows')
    zoom = float(s['windows.zoom'])
    starts, lengths = s['source.slice_start'], s['source.slice_length']
    lows, highs = s['source.free_low'], s['source.free_high']
    knots = s['source.knot_x']
    z = 1.0 + zoom * (2.0 * q8 - 1.0)
    nominal = end - start                                       # board length in picture dots
    need = nominal * (max(lengths) * (1.0 + zoom)) / row_h      # the longest window this board could ask of its source row
    # which source row: a random start per row, then one step further for every next board, so two neighbouring boards NEVER take the same source row
    # (two neighbours from the same row would show the same piece side by side, one mirrored: a butterfly pattern across the joint)
    row_offset = kit.floor(kit.rand1(rh, 2.5, 6.5, seed) * 3.999)
    band_raw = (row_offset + jb) % 4.0                          # 0..3 = source rows R2, R3, R4, R5
    room = kit.table(band_raw, [[hi - lo for lo, hi in zip(lows, highs)]], scale=T)
    fits = kit.less(need, room)
    band_plain = kit.where(fits, band_raw, 1.0 + 2.0 * kit.greater(q7, 0.5))     # does not fit: use R3 or R5 (no knots, full length)
    # knots are rationed: a stretch of row one tile wide holds at most ONE knot board (chance = knot_share x boards per row, at most 1).
    # In a bigger area every tile-wide stretch of every row gets its own draw, so the number of knots per dot is the same as in one tile.
    stretch = 0.0 if tile else kit.floor(j_eff / float(B))
    row_has_knot = kit.less(kit.rand1(rh, 2.0 * stretch, 7.0, seed), min(1.0, float(s['windows.knot_share']) * B))
    knot_slot = kit.floor(kit.rand1(rh, 1.0 + 2.0 * stretch, 7.0, seed) * (B - 0.001))
    is_knot = kit.label(row_has_knot * kit.less(kit.absolute((j_eff % float(B)) - knot_slot), 0.5), 'this board shows a knot')
    band_knot = kit.where(kit.less(q6, 0.5), 0.0, 2.0)          # a knot board shows the knot of R2 or of R4
    band = kit.label(kit.where(is_knot, band_knot, band_plain), 'source row of this board (0=R2 1=R3 2=R4 3=R5)')
    slice_start, slice_len, free_lo, free_hi = kit.table(band, [starts, lengths, lows, highs], scale=T)
    knot_x = kit.table(band, [knots], scale=T)
    sc = kit.label((slice_len / row_h) * z, 'source dots per picture dot')
    Lw = nominal * sc                                           # length of the source window this board shows
    x0_plain = free_lo + kit.maximum(free_hi - free_lo - Lw, 0.0) * q1
    x0_knot = kit.minimum(kit.maximum(knot_x - Lw * (0.25 + 0.5 * q1), 0.0), kit.maximum(T - Lw, 0.0))
    x0 = kit.where(is_knot, x0_knot, x0_plain)
    flip_h = kit.less(q2, float(s['windows.flip_left_right']))
    t_board = Px - start
    xs = kit.pingpong(x0 + kit.where(flip_h, Lw - t_board * sc, t_board * sc), T)
    y_rel = y_in * sc
    flip_v = kit.less(q9, float(s['windows.flip_upside_down']))
    y_rel2 = kit.where(flip_v, slice_len * z - y_rel, y_rel)     # upside down: the window is turned over (a gap half sits at both ends, so it still fits)
    ys = kit.pingpong(slice_start + y_rel2, T)
    if identity:
        xs, ys = kit.pingpong(Px, T), kit.pingpong(Py, T)

    # =============================================================================================== 4 READ THE MAPS
    kit.begin('4 READ THE MAPS: the same position is read from the height map and from the colour map')
    hgt = kit.label(kit.image(path_height, xs, ys, colour=False, size=T)[0], 'height read from the displacement map')
    if use_map_colour:
        col = kit.image(path_colour, xs, ys, colour=True, size=T)
    else:
        palette = s['colour.palette']                              # [[height 0..255, "#rrggbb"], ...] measured from the colour map
        stops = [(p / 255.0, srgb_hex_to_linear(c)) for p, c in palette]

        def palette_colour(height):
            return kit.ramp(height, stops)
        col = palette_colour(hgt)

    # =============================================================================================== 5 STAINS
    kit.begin('5 STAINS: dark splotches of the source map stamped on top (two layers of stamps, shifted against each other)')
    stain_amount = float(s['stains.amount'])
    if stain_amount > 0 and not identity:
        centres = s['source.stain_centres']
        n_st = len(centres)
        cell = T / 5.0
        radius = float(s['stains.size'])
        for layer in range(2):
            off = layer * cell * 0.5
            ci, cj = kit.floor((Px + off) / cell), kit.floor((Yg + off) / cell)
            cih, cjh = ((ci % 5.0), (cj % 5.0)) if tile else (ci, cj)
            qa, qb, qc = kit.rand(cih, cjh, 31.0 + layer, seed)
            qd, qe, qf = kit.rand(cih, cjh, 41.0 + layer, seed)
            present = kit.less(qa, stain_amount)
            room_c = cell - 2.0 * radius
            cx = ci * cell - off + radius + qb * room_c
            cy = cj * cell - off + radius + qc * room_c
            dx, dy = Px - cx, Yg - cy
            dist = kit.sqrt(dx * dx + dy * dy)
            which = kit.floor(qd * (n_st - 0.001))
            sx, sy = kit.table(which, [[c[0] for c in centres], [c[1] for c in centres]], scale=T)
            zs = 1.0 + float(s['stains.zoom']) * (2.0 * qe - 1.0)
            fx = 1.0 - 2.0 * kit.greater(qf, 0.5)
            xs_st = kit.pingpong(sx + dx * (zs * fx), T)
            ys_st = kit.pingpong(sy + dy * zs, T)
            st_h = kit.image(path_height, xs_st, ys_st, colour=False, size=T)[0]
            disc = (1.0 - kit.smoothstep(0.62 * radius, radius, dist)) * present
            dark_limit, soft = float(s['stains.dark_limit']) / 255.0, float(s['stains.dark_softness']) / 255.0
            mask = disc * kit.saturate((dark_limit - st_h) / soft)       # only the dark part of the stamp is painted
            hgt = kit.lerp(hgt, st_h, mask)
            if use_map_colour:
                st_c = kit.image(path_colour, xs_st, ys_st, colour=True, size=T)
            else:
                st_c = palette_colour(st_h)
            col = tuple(kit.lerp(c, sc_, mask) for c, sc_ in zip(col, st_c))

    # =============================================================================================== 6 JOINTS
    kit.begin('6 JOINTS AND GAP BANDS: a dark ragged crack where one window meets the next, and a dark band along every row boundary, hide the cuts')
    def torus(count):
        """Four numbers that go round in circles once per tile, 'count' features per tile: anything made from them repeats exactly after one tile."""
        a_, b_ = Px * (2.0 * math.pi / T), Yg * (2.0 * math.pi / T)
        r_ = count / (2.0 * math.pi)
        return kit.cos(a_) * r_, kit.sin(a_) * r_, kit.cos(b_) * r_, kit.sin(b_) * r_

    def patchy(count, code, detail=2.0):
        """Soft cloud pattern 0..1 with about 'count' clouds across one tile; repeats exactly after one tile when the tile repeats."""
        if tile:
            x_, y_, z_, w_ = torus(count)
            return kit.noise4(x_, y_, z_, w_ + (seed + code) * 11.0, 1.0, detail=detail)
        return kit.noise3(Px * (count / T), Yg * (count / T), (seed + code) * 11.0, 1.0, detail=detail)

    def pebble_cells(count):
        if tile:
            x_, y_, z_, w_ = torus(count)
            return kit.cells4(x_, y_, z_, w_ + seed * 5.0, 1.0)
        return kit.cells(Px, Yg, count / T)

    d_left, d_right = Px - start, end - Px
    fy = 1.0 / float(s['joints.wobble_length'])
    base_half = float(s['joints.width']) * 0.5
    rag, notch_amount = float(s['joints.raggedness']), float(s['joints.notches'])
    key_left = rh * 11.3 + jb * 3.7
    key_right = rh * 11.3 + jb_next * 3.7
    n_a = kit.noise3(y_in * fy, key_left, 1.0 + seed * 7.0, 1.0, detail=2.0)       # how far the crack of the left end reaches into this board
    n_b = kit.noise3(y_in * fy, key_right, 2.0 + seed * 7.0, 1.0, detail=2.0)      # the same for the right end
    n_c = kit.noise3(y_in * fy * 0.4, key_left + 0.5, 3.0 + seed * 7.0, 1.0, detail=1.0)
    n_d = kit.noise3(y_in * fy * 0.4, key_right + 0.5, 4.0 + seed * 7.0, 1.0, detail=1.0)
    half_left = kit.maximum(base_half * (1.0 + rag * (2.0 * n_a - 1.0)) + notch_amount * 7.0 * kit.smoothstep(0.62, 0.72, n_c), 1.2)
    half_right = kit.maximum(base_half * (1.0 + rag * (2.0 * n_b - 1.0)) + notch_amount * 7.0 * kit.smoothstep(0.62, 0.72, n_d), 1.2)
    crack_l = 1.0 - kit.smoothstep(half_left - 0.7, half_left + 0.7, d_left)
    crack_r = 1.0 - kit.smoothstep(half_right - 0.7, half_right + 0.7, d_right)
    crack_v = kit.maximum(crack_l, crack_r)
    # inside a joined pair: a partial crack at the place where the two boards would meet (starts at the top or the bottom of the row, tapers away)
    qm1, qm2, qm3 = kit.rand(rh, hash_index(pf), 9.0, seed)
    from_top = kit.less(qm1, 0.5)
    dist_from_edge = kit.where(from_top, y_in, row_h - y_in)
    extent = (0.30 + 0.40 * qm2) * row_h
    envelope = 1.0 - kit.smoothstep(0.5 * extent, extent, dist_from_edge)
    n_m = kit.noise3(y_in * fy, rh * 11.3 + hash_index(pf + 1.0) * 3.7, 8.0 + seed * 7.0, 1.0, detail=2.0)
    half_mid = envelope * kit.maximum(base_half * (1.0 + rag * (2.0 * n_m - 1.0)) + 0.5 * notch_amount * 4.0 * kit.smoothstep(0.62, 0.72, n_m), 1.2)
    d_mid = kit.absolute(Px - (e_mid + row_shift))
    crack_m = merged * (1.0 - kit.smoothstep(half_mid - 0.6, half_mid + 0.6, d_mid)) * kit.greater(envelope, 0.05)
    crack_v = kit.maximum(crack_v, crack_m)
    # the dark band along every row boundary (the cut between two rows lies in the middle of it): same dirt as the joints, ragged edges
    next_id = ((row_no + 1.0) % float(R)) if tile else (rh + 1.0)
    band_half = float(s['joints.gap_band_width']) * 0.5
    n_t = kit.noise3(Px * fy, rh * 7.7, 5.0 + seed * 7.0, 1.0, detail=2.0)
    n_u = kit.noise3(Px * fy, next_id * 7.7, 5.0 + seed * 7.0, 1.0, detail=2.0)       # the boundary below this row: the same noise as the top of the next row
    half_top = kit.maximum(band_half * (1.0 + rag * (2.0 * n_t - 1.0)), 1.2)
    half_bottom = kit.maximum(band_half * (1.0 + rag * (2.0 * n_u - 1.0)), 1.2)
    band_t = 1.0 - kit.smoothstep(half_top - 0.7, half_top + 0.7, y_in)
    band_b = 1.0 - kit.smoothstep(half_bottom - 0.7, half_bottom + 0.7, row_h - y_in)
    crack = kit.label(kit.maximum(crack_v, kit.maximum(band_t, band_b)), 'joint crack or row gap (1 = inside)')
    d_min = kit.minimum(d_left, d_right)
    shade = (1.0 - kit.smoothstep(base_half, base_half + 14.0, d_min)) * float(s['joints.edge_shade'])
    # a worn light lip along the wood next to the crack (a bevel: lighter and a little higher)
    out_left, out_right = d_left - half_left, d_right - half_right
    lip_l = kit.smoothstep(0.0, 0.6, out_left) * (1.0 - kit.smoothstep(1.2, 2.8, out_left))
    lip_r = kit.smoothstep(0.0, 0.6, out_right) * (1.0 - kit.smoothstep(1.2, 2.8, out_right))
    lip = kit.maximum(lip_l, lip_r) * float(s['joints.edge_lip'])
    # what lies inside the crack: dark dirt with small pebbles (like the gaps between the rows of the source)
    pebbles = (1.0 - kit.smoothstep(0.20, 0.34, pebble_cells(round(0.1 * T)))) * float(s['joints.pebbles'])
    dirt = patchy(round(0.25 * T), 5.0)

    # =============================================================================================== 7 PATCHES
    kit.begin('7 PATCHES: large soft drift and dark blotches (made here, not copied from a map)')

    drift = patchy(float(s['masks.drift_size']), 1.0)
    blotch = kit.smoothstep(0.60, 0.78, patchy(float(s['masks.blotch_size']), 2.0))
    gain = (1.0 + (drift - 0.5) * (2.0 * float(s['masks.drift_amount']))) * (1.0 - float(s['masks.blotch_amount']) * blotch)

    # =============================================================================================== 8 COLOUR
    kit.begin('8 COLOUR: tone per board, patches, joints')
    tone = kit.label(1.0 + (q3 - 0.5) * float(s['boards.tone_variation']), 'tone of this board')
    warm = (q4 - 0.5) * float(s['boards.warmth_variation'])
    red, green, blue = col[0] * (tone * (1.0 + warm)), col[1] * tone, col[2] * (tone * (1.0 - warm))
    if not identity:
        red, green, blue = red * gain, green * gain, blue * gain
        dark_a, dark_b, peb = srgb_hex_to_linear('#14100d'), srgb_hex_to_linear('#2d241f'), srgb_hex_to_linear('#4d453e')
        sh_gain = (1.0 - shade) * (1.0 + 0.45 * lip)
        inside = []
        for index, c in enumerate((red, green, blue)):
            crack_colour = kit.lerp(kit.lerp(dark_a[index], dark_b[index], dirt), peb[index], pebbles)
            inside.append(kit.lerp(c * sh_gain, crack_colour, crack))
        red, green, blue = inside

    # =============================================================================================== 9 HEIGHT AND ROUGHNESS
    kit.begin('9 HEIGHT and ROUGHNESS')
    height = hgt
    if not identity:
        dh = float(s['masks.darken_height'])
        height = height + (tone - 1.0) * float(s['boards.height_shift'])
        height = height * (1.0 - float(s['masks.blotch_amount']) * dh * blotch) + (drift - 0.5) * (2.0 * float(s['masks.drift_amount']) * 0.15 * dh)
        height = height * (1.0 - 0.5 * shade)
        height = height + 0.14 * lip
        height = kit.lerp(height, 0.03 + 0.12 * pebbles + 0.04 * dirt, crack)
    height = kit.saturate(height)
    rough = float(s['roughness.base']) + float(s['roughness.from_height']) * (height - 0.5) + float(s['roughness.board_variation']) * (2.0 * q10 - 1.0)
    rough = kit.saturate(rough + 0.1 * crack)

    # =============================================================================================== outputs
    kit.begin('OUTPUTS')
    out = w.nodes['out']
    if debug == 'boards':
        kit.combine_colour(q1, q2, q3, out.inputs['Colour'])
        kit.to_socket(q1, out.inputs['Height'])
        kit.to_socket(0.0, out.inputs['Roughness'])
    elif debug == 'rows':
        g = row_no / float(R)
        kit.combine_colour(g, g, g, out.inputs['Colour'])
        kit.to_socket(g, out.inputs['Height'])
        kit.to_socket(0.0, out.inputs['Roughness'])
    elif debug == 'flips':
        kit.combine_colour(flip_h, flip_v, is_knot, out.inputs['Colour'])
        kit.to_socket(flip_h * 0.25 + flip_v * 0.5 + is_knot * 0.25, out.inputs['Height'])
        kit.to_socket(0.0, out.inputs['Roughness'])
    elif debug in ('source_x', 'source_y'):
        value = (xs if debug == 'source_x' else ys) / T
        kit.combine_colour(value, value, value, out.inputs['Colour'])
        kit.to_socket(value, out.inputs['Height'])
        kit.to_socket(0.0, out.inputs['Roughness'])
    else:
        kit.combine_colour(red, green, blue, out.inputs['Colour'])
        kit.to_socket(height, out.inputs['Height'])
        kit.to_socket(rough, out.inputs['Roughness'])
    out.inputs['Metallic'].default_value = 0.0
    kit.finish()
    tree['node_count'] = len(tree.nodes)
    return tree
