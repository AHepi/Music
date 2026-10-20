# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# This is THE WOOD-FROM-MAPS RECIPE (round 2): the one file the bake harness loads (lib/bake_harness.py asks for build_node_group(parameters)).
# It makes one Blender node group called "WOOD FROM MAPS" whose input is 'Vector' (the surface coordinate, 0..1 in both directions
# over the baked picture) and whose outputs are 'Colour', 'Roughness', 'Metallic' and 'Height' (what the harness photographs).
#
# What it does with the person's maps (this is the whole idea):
#   The uploaded wood DISPLACEMENT map (height) and COLOUR map show 5 rows of weathered boards, but they cannot simply be repeated:
#   they do not wrap (a plain 2 x 2 repeat shows a straight seam) and every repeat shows the same knots, cracks and stains. So the recipe
#   uses the maps only as SOURCE MATERIAL and arranges new boards out of them, with nodes only:
#     1. ROWS      The surface is cut into rows (5 per tile, heights differing by up to 20 percent). Every row runs from the middle of a
#                  dark gap to the middle of the next, as the source rows do, and the row edges wave a little.
#     2. BOARDS    Every row is cut into boards of random length (2 per tile-wide stretch, so most boards are 0.3 to 0.8 of a tile long),
#                  shifted sideways by chance from row to row. The cut between two boards is not straight: it steps and wobbles.
#     3. WINDOW    Every board chooses its OWN window of the source: which source row (the next board takes a different one, and so
#                  does the next row; a few exceptions are counted in the guide, section 11.2), where along it, flipped left-right or upside-down or not, stretched along the board by up to 25 percent,
#                  bent by a slow wobble and tilted by up to 3.5 degrees (the sideways shift of the tilt is capped at 8 dots), so that no two windows have the same shape.
#     4. LANDMARKS The most recognisable places of the source (3 knots, zigzag cracks, splinters, big rust clouds, 12 in all) are painted
#                  out of every window by default (replaced by clean grain taken from another place of the source) and only shown in a
#                  board that draws a lucky number (knots 15 percent, others 12 percent). So a knot or a zigzag comes back rarely.
#     5. READ      The height map and the colour map are read at exactly the same position, so colour and relief always match.
#     6. STAINS    Dark stain splotches from the source are stamped on top at random places (two shifted layers of stamps), away from joints.
#     7. JOINTS    Where one window meets the next there is a dark ragged crack of random width (the board joint) that hides the cut;
#                  inside many boards a partial stepped crack (a half joint) is added for looks; along every row edge a dark band is added
#                  only where the source gap is not already dark (so the real gap rubble of the source stays).
#     8. PATCHES   Large soft light/dark drift and dark blotches (not copied from any map) change the look from place to place.
#     9. COLOUR    MAIN version: the colour read from the colour map, plus a small tone change per board.
#                  COMPARISON version (setting colour.source = height_palette): the colour is made from the height with a palette.
#   The normal map is NOT read from the uploaded normal map (a flipped board would have its slopes pointing the wrong way): it is made
#   from the arranged height afterwards (tools/make_normal_from_height.py, strength 8).
#
# Default tile or bigger area, from the same nodes:
#     recipe.tiles_across = 1   one tile of 1254 x 1254 dots that repeats without a seam (every random number repeats after one tile)
#     recipe.tiles_across = 2, 4, 8 ...  a bigger area of NEW boards with the same look per dot (the random numbers keep counting up and
#                          are salted differently from the tile, so nothing repeats on purpose and the first tile of an area is NOT the
#                          default tile). Bake it with 1254 x that many dots (or fewer, it then comes out smaller).
#
# Settings: a flat list of numbers and words in settings.json next to this file, named 'group.control' (for example 'stains.amount').
# Order of strength: the default written in this file  <  settings.json  <  the parameters the caller passes in (for example the
# harness option --params '{"layout.boards_per_row": 3}'). Special parameters (not settings):
#     shift     [u, v]  slides the whole pattern by that much of the picture; used only by the half-tile-shift test.
#     window    [x, y, size]  bakes only a part of a big area: x and y are the top-left corner and size the width, all in TILES
#               (for example [1.5, 2, 1] = the one tile that starts one and a half tiles from the left and two from the top).
#     debug_view  shows one thing instead of the finished picture:  'boards' (a random colour per board), 'source_x' / 'source_y'
#               (in the Height output, exactly: which dot of the source map every dot of the picture was taken from, as x / 1254 or
#               y / 1254; used for the reuse count), 'rows' (grey per row), 'flips' (red = flipped left-right, green = upside-down),
#               'landmarks' (Height = which landmark is SHOWN here, number / 16; colour red = shown, green = painted out).
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
    'layout.rows_per_tile': 5, 'layout.row_height_variation': 0.20, 'layout.boards_per_row': 2, 'layout.board_length_variation': 0.8,
    'windows.zoom': 0.25, 'windows.flip_left_right': 0.5, 'windows.flip_upside_down': 0.4, 'windows.warp_along': 12.0, 'windows.warp_across': 5.0,
    'windows.warp_size': 200.0, 'windows.tilt': 3.5, 'windows.tilt_max': 8.0, 'windows.edge_margin': 28.0,
    'landmarks.knot_chance': 0.15, 'landmarks.mark_chance': 0.12, 'landmarks.edge_ragged': 0.30,
    'boards.tone_variation': 0.12, 'boards.row_tone_variation': 0.16, 'boards.warmth_variation': 0.12, 'boards.height_shift': 0.10,
    'joints.width': 3.6, 'joints.width_variation': 0.6, 'joints.step_share': 0.7, 'joints.step_size': 90.0, 'joints.darkness': 0.9, 'joints.darkness_variation': 0.5, 'joints.wobble': 2.0, 'joints.wobble_length': 22.0,
    'joints.raggedness': 0.8, 'joints.notches': 0.6, 'joints.edge_lip': 0.4, 'joints.pebbles': 0.45, 'joints.edge_shade': 0.2,
    'joints.half_share': 0.35, 'joints.half_depth': 0.32, 'joints.half_run': 70.0, 'joints.half_width': 5.0,
    'gaps.band_width': 3.2, 'gaps.band_variation': 0.9, 'gaps.wobble': 4.0, 'gaps.wobble_length': 140.0,
    'stains.amount': 0.16, 'stains.size': 85.0, 'stains.zoom': 0.25, 'stains.dark_limit': 100.0, 'stains.dark_softness': 30.0, 'stains.keep_away': 15.0, 'stains.edge_hardness': 0.8,
    'masks.drift_amount': 0.10, 'masks.drift_size': 2.0, 'masks.blotch_amount': 0.15, 'masks.blotch_size': 5.0, 'masks.darken_height': 0.0,
    'colour.source': 'map', 'colour.warm_cool_amount': 1.0,
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
    seed_h = seed if tile else seed + 100.0        # an area is salted differently from the tile: the first tile of an area is not the default tile
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

    def x_noise(count, key, code, detail=1.0):
        """A cloud pattern that depends only on the position along the surface and on a key (a row edge number, ...): about 'count'
        clouds per tile; in the default tile it repeats exactly after one tile (the position is turned into a circle first)."""
        kz = key * 7.31 + 0.37
        if tile:
            a_ = Px * (2.0 * math.pi / T)
            r_ = count / (2.0 * math.pi)
            return kit.noise4(kit.cos(a_) * r_, kit.sin(a_) * r_, kz, seed_h * 13.0 + code, 1.0, detail=detail)
        return kit.noise3(Px * (count / T), kz, seed_h * 13.0 + code + 0.53, 1.0, detail=detail)

    # =============================================================================================== 1 ROWS
    kit.begin('1 ROWS: rows of different height (they add up to one tile); every row runs from the middle of a gap to the middle of the next; the edges wave')
    R = int(s['layout.rows_per_tile'])
    wob_amp = float(s['gaps.wobble'])
    wob_len = float(s['gaps.wobble_length'])
    _wob_cache = {}

    def wobble(key):
        """How far the row edge with this number is pushed down (dots, plus or minus gaps.wobble) at this place along the surface."""
        cache_key = key if isinstance(key, (int, float)) else None
        if cache_key is not None and cache_key in _wob_cache:
            return _wob_cache[cache_key]
        n1 = x_noise(T / wob_len, key, 1.0)
        n2 = x_noise(T / (wob_len * 0.3), key, 2.0)
        value = wob_amp * ((n1 * 2.0 - 1.0) * 0.7 + (n2 * 2.0 - 1.0) * 0.3)
        if cache_key is not None:
            _wob_cache[cache_key] = value
        return value

    if tile:
        ty = 0.0
        Pm = Py % T
        w0 = wobble(0.0)                                  # the tile edge itself waves: its dots may belong to the last row of the tile before (edge pushed down) or to the first row (edge pushed up)
        Pyl = kit.label(Pm + T * kit.less(Pm, w0) - T * kit.greater(Pm, T + w0), 'Pyl: dots down inside the tile')
        Yg = Pm
        key_of = lambda m: float(m % R)
    else:
        tyc = kit.floor(Py / T + 0.5)
        ty = tyc - kit.less(Py, tyc * T + wobble(tyc * float(R)))
        Pyl = kit.label(Py - ty * T, 'Pyl: dots down inside this tile row')
        Yg = Py
        key_of = lambda m: ty * float(R) + float(m)
    hv = float(s['layout.row_height_variation'])
    ra = kit.rand(ty, 0.0, 11.0, seed_h)
    rb = kit.rand(ty, 1.0, 11.0, seed_h)
    rnd = list(ra) + list(rb)
    weights = [1.0 + hv * (2.0 * rnd[m] - 1.0) for m in range(R)]
    total = weights[0]
    for m in range(1, R):
        total = total + weights[m]
    heights = [weights[m] * (T / total) for m in range(R)]        # row heights, adding up to one tile
    plain = [0.0]
    running = heights[0]
    for m in range(1, R):
        plain.append(running)
        if m < R - 1:
            running = running + heights[m]
    plain.append(T)
    bnd = [plain[m] + wobble(key_of(m)) for m in range(R + 1)]   # the (waving) row edges: bnd[m] is the top of row m
    steps = [1.0] + [kit.greater(Pyl, bnd[m]) for m in range(1, R)] + [0.0]       # steps[m] = 1 when the dot is in row m or below
    row_no = steps[1]
    for m in range(2, R):
        row_no = row_no + steps[m]
    row_top, row_bot = 0.0, 0.0
    for m in range(R):
        onehot = steps[m] - steps[m + 1]
        row_top = row_top + onehot * bnd[m]
        row_bot = row_bot + onehot * bnd[m + 1]
    row_h = kit.label(row_bot - row_top, 'height of this row')
    y_in = kit.label(Pyl - row_top, 'dots below the top of the row')
    kit.label(row_no, 'row number in the tile')
    rh = row_no if tile else row_no + R * ty                # the row number the random numbers are made from

    def torus(count):
        """Four numbers that go round in circles once per tile, 'count' features per tile: anything made from them repeats exactly after one tile."""
        a_, b_ = Px * (2.0 * math.pi / T), Yg * (2.0 * math.pi / T)
        r_ = count / (2.0 * math.pi)
        return kit.cos(a_) * r_, kit.sin(a_) * r_, kit.cos(b_) * r_, kit.sin(b_) * r_

    def patchy(count, code, detail=2.0):
        """Soft cloud pattern 0..1 with about 'count' clouds across one tile; repeats exactly after one tile when the tile repeats."""
        if tile:
            x_, y_, z_, w_ = torus(count)
            return kit.noise4(x_, y_, z_, w_ + (seed_h + code) * 11.0, 1.0, detail=detail)
        return kit.noise3(Px * (count / T), Yg * (count / T), (seed_h + code) * 11.0, 1.0, detail=detail)

    # =============================================================================================== 2 BOARDS
    kit.begin('2 BOARDS: random lengths, every row shifted sideways by chance, the cut between boards steps and wobbles')
    B = int(s['layout.boards_per_row'])
    Lb = T / B
    jit = float(s['layout.board_length_variation'])
    row_shift = kit.rand1(rh, 1.0, 0.0, seed_h) * Lb
    j0 = kit.floor((Px - row_shift) / Lb)

    def hidx(k):
        return (k % float(B)) if tile else k

    step_share, step_max = float(s['joints.step_share']), float(s['joints.step_size'])
    wobble_amp, wobble_len = float(s['joints.wobble']), float(s['joints.wobble_length'])

    def edge(k):
        """The cut of board edge k. Returns (position at this height of the row, plain position, size of the step, height of the step in the row, random numbers).
        The cut is a staircase with one step: above the step it lies half a step to the left, below it half a step to the right (like the stepped
        butt joints of the source); a few edges have no step. The position also wobbles a little."""
        rr = kit.rand(rh, hidx(k), 2.0, seed_h)                 # jitter, width, size of the step
        r2 = kit.rand(rh, hidx(k), 9.0, seed_h)                 # height of the step in the row, has a step?, spare
        key = rh * 11.3 + hidx(k) * 3.7
        n_w = kit.noise3(y_in * (1.0 / wobble_len), key + 0.5, 22.0 + seed_h * 7.0, 1.0, detail=1.0)
        plain_pos = k * Lb + (rr[0] - 0.5) * (jit * Lb) + row_shift
        step_size = (rr[2] * 2.0 - 1.0) * step_max * kit.less(r2[1], step_share)
        step_at = row_h * (0.30 + 0.40 * r2[0])
        pos = plain_pos + (kit.greater(y_in, step_at) - 0.5) * step_size + wobble_amp * (n_w * 2.0 - 1.0)
        strength = 1.0 - float(s['joints.darkness_variation']) * r2[2]      # some joints are faint, some strong
        return pos, plain_pos, step_size, step_at, rr, strength

    E_m1, P_m1, S_m1, A_m1, r_m1, K_m1 = edge(j0 - 1.0)
    E_0, P_0, S_0, A_0, r_0, K_0 = edge(j0)
    E_1, P_1, S_1, A_1, r_1, K_1 = edge(j0 + 1.0)
    E_2, P_2, S_2, A_2, r_2, K_2 = edge(j0 + 2.0)
    s_a, s_b = kit.less(Px, E_0), kit.greater(Px, E_1)         # the board is the one before, the same, or the one after
    j = j0 - s_a + s_b

    def pick(m1, a0, a1, a2, for_start):
        """The value of the left edge (for_start) or of the right edge of the board we are in."""
        if for_start:
            return a0 + s_a * (m1 - a0) + s_b * (a1 - a0)
        return a1 + s_a * (a0 - a1) + s_b * (a2 - a1)
    start = kit.label(pick(E_m1, E_0, E_1, E_2, True), 'left end of this board (at this height)')
    end = kit.label(pick(E_m1, E_0, E_1, E_2, False), 'right end of this board (at this height)')
    plain_s, plain_e = pick(P_m1, P_0, P_1, P_2, True), pick(P_m1, P_0, P_1, P_2, False)
    size_s, size_e = pick(S_m1, S_0, S_1, S_2, True), pick(S_m1, S_0, S_1, S_2, False)
    at_s, at_e = pick(A_m1, A_0, A_1, A_2, True), pick(A_m1, A_0, A_1, A_2, False)
    strength_l, strength_r = pick(K_m1, K_0, K_1, K_2, True), pick(K_m1, K_0, K_1, K_2, False)
    width_l = pick(r_m1[1], r_0[1], r_1[1], r_2[1], True)
    width_r = pick(r_m1[1], r_0[1], r_1[1], r_2[1], False)
    jb, jb_next = hidx(j), hidx(j + 1.0)
    d_left, d_right = Px - start, end - Px
    # the stretch of the picture this board's window must cover, whatever the steps do (the window does not depend on the height in the row)
    reach = 0.5 * step_max + wobble_amp + 2.0
    start_w, end_w = plain_s - reach, plain_e + reach
    nominal = kit.label(end_w - start_w, 'length of the window of this board in the picture (with room for the steps)')
    q1, q2, q3 = kit.rand(rh, jb, 3.0, seed_h)     # start along the source row, flip left-right, tone
    q4, q5, q6 = kit.rand(rh, jb, 4.0, seed_h)     # warmth, tilt, spare
    q7, q8, q9 = kit.rand(rh, jb, 5.0, seed_h)     # spare, stretch along the board, flip upside-down
    q10, q11, q12 = kit.rand(rh, jb, 6.0, seed_h)  # roughness change, half joint yes/no, half joint position
    q13, q14, q15 = kit.rand(rh, jb, 7.0, seed_h)  # half joint: top or bottom, depth, direction of the run
    q16, q17, q18 = kit.rand(rh, jb, 8.0, seed_h)  # half joint: run length, width, spare

    # =============================================================================================== 3 WINDOW
    kit.begin('3 WINDOW: which piece of the source map this board shows (bent, tilted, stretched)')
    zoom = float(s['windows.zoom'])
    margin = float(s['windows.edge_margin'])
    tops, bots = s['source.slice_start'], s['source.slice_end']
    # which source row: the next board takes the next source row (and the next row of boards steps by two), so touching boards take different ones (counted on the 4 x 4 area: 1 percent of touching pairs are exceptions, because a long board can touch a board two places away)
    off_band = kit.floor(kit.rand1(0.0, 2.5, 6.5, seed_h) * 3.999)
    band = kit.label((rh * 2.0 + jb + off_band) % 4.0, 'source row of this board (0=R2 1=R3 2=R4 3=R5)')
    ytop_b, ybot_b = kit.table(band, [tops, bots], scale=T)
    slice_len = ybot_b - ytop_b
    z = 1.0 + zoom * (2.0 * q8 - 1.0)
    sc_nat = kit.label(slice_len / row_h, 'source dots per picture dot, down the row')
    sc_x = kit.label(kit.minimum(sc_nat * z, (T - 2.0 * margin) / nominal), 'source dots per picture dot, along the board')
    Lw = nominal * sc_x                                           # length of the source window this board shows
    x0 = margin + (T - 2.0 * margin - Lw) * q1
    flip_h = kit.less(q2, float(s['windows.flip_left_right']))
    t_board = Px - start_w
    uu0 = t_board / nominal
    uu = kit.where(flip_h, 1.0 - uu0, uu0)
    xs0 = x0 + uu * Lw
    vv0 = y_in / row_h
    flip_v = kit.less(q9, float(s['windows.flip_upside_down']))
    vv = kit.where(flip_v, 1.0 - vv0, vv0)
    ys0 = ytop_b + vv * slice_len                                 # the top and the bottom of the row are the gap middles of the source, always
    env = kit.smoothstep(0.0, 0.2, vv0) * kit.smoothstep(0.0, 0.2, 1.0 - vv0)        # the bending dies away at the row edges so they stay on the gap
    wsz = 1.0 / float(s['windows.warp_size'])
    key_b = rh * 13.1 + jb * 5.7
    n_wx = kit.noise3(t_board * wsz, y_in * wsz, key_b + 31.0 + seed_h * 3.3, 1.0, detail=1.0)
    n_wy = kit.noise3(t_board * wsz, y_in * wsz, key_b + 47.0 + seed_h * 3.3, 1.0, detail=1.0)
    warp_x = (n_wx * 2.0 - 1.0) * float(s['windows.warp_along'])
    warp_y = (n_wy * 2.0 - 1.0) * float(s['windows.warp_across']) * env
    tilt_max = float(s['windows.tilt_max'])           # the sideways shift of a tilt is capped: a big shift that dies away at the row edge would squeeze the grain there (round 2, first try: smeared strips)
    tilt_y = kit.clamp((q5 * 2.0 - 1.0) * math.tan(math.radians(float(s['windows.tilt']))) * (uu - 0.5) * Lw, -tilt_max, tilt_max) * env
    if identity:
        xs, ys = kit.pingpong(Px, T), kit.pingpong(Py, T)
    else:
        xs = kit.pingpong(xs0 + warp_x, T)
        ys = kit.pingpong(ys0 + warp_y + tilt_y, T)

    # =============================================================================================== 4 LANDMARKS AND READ THE MAPS
    kit.begin('4 LANDMARKS + READ THE MAPS: recognisable places are painted out unless this board drew a lucky number; the same position is read from both maps')
    lm = s['landmarks.list']
    n_lm = len(lm)
    shown_sum, painted_sum = 0.0, 0.0
    Sx, Sy, M = 0.0, 0.0, 0.0
    if not identity and n_lm:
        draws = []
        for g in range(0, n_lm, 3):
            a_, b_, c_ = kit.rand(rh, jb, 20.0 + g / 3.0, seed_h)
            draws += [a_, b_, c_]
        nzl = kit.noise3(xs * (1.0 / 30.0), ys * (1.0 / 30.0), 51.0 + seed * 3.0, 1.0, detail=1.0)      # ragged edge of the painted-out discs
        ragged = float(s['landmarks.edge_ragged'])
        for i, (lx, ly, lr, ldx, ldy, kind) in enumerate(lm):
            chance = float(s['landmarks.knot_chance']) if int(kind) == 0 else float(s['landmarks.mark_chance'])
            painted = kit.greater(draws[i], chance)                  # 1 = this board paints the landmark out
            ddx, ddy = xs - lx, ys - ly
            dist = kit.sqrt(ddx * ddx + ddy * ddy) + (nzl - 0.5) * (ragged * lr)
            m_i = kit.saturate((lr - dist) / 2.5 + 0.5) * painted
            sel = kit.greater(m_i, 0.002)
            Sx = Sx + sel * float(ldx)
            Sy = Sy + sel * float(ldy)
            M = kit.maximum(M, m_i)
            if debug == 'landmarks':
                inside = kit.less(dist, lr)
                shown_sum = shown_sum + inside * (1.0 - painted) * ((i + 1.0) / 16.0)
                painted_sum = painted_sum + inside * painted * ((i + 1.0) / 16.0)
        xs2, ys2 = kit.pingpong(xs + Sx, T), kit.pingpong(ys + Sy, T)
    hgt = kit.image(path_height, xs, ys, colour=False, size=T)[0]
    if use_map_colour:
        col = kit.image(path_colour, xs, ys, colour=True, size=T)
    if not identity and n_lm:
        hgt_b = kit.image(path_height, xs2, ys2, colour=False, size=T)[0]
        hgt = kit.lerp(hgt, hgt_b, M)
        if use_map_colour:
            col_b = kit.image(path_colour, xs2, ys2, colour=True, size=T)
            col = tuple(kit.lerp(a_, b_, M) for a_, b_ in zip(col, col_b))
    kit.label(hgt, 'height read from the displacement map')
    if not use_map_colour:
        amount = float(s['colour.warm_cool_amount'])
        if amount > 0:
            # three palettes measured from the colour map: dull blue-grey wood, plain brown wood, orange bare wood; two slow cloud patterns pick where the
            # orange and the blue-grey patches are (the height alone cannot tell them apart)
            to_stops = lambda key: [(p / 255.0, srgb_hex_to_linear(c)) for p, c in s[key]]
            stops_mid, stops_cool, stops_warm = to_stops('colour.palette_mid'), to_stops('colour.palette_cool'), to_stops('colour.palette_warm')
            warm_mask = kit.smoothstep(0.50, 0.66, patchy(7.0, 8.0, detail=2.0)) * amount
            cool_mask = kit.smoothstep(0.50, 0.66, patchy(9.0, 9.0, detail=2.0)) * amount * (1.0 - warm_mask)

            def palette_colour(height):
                m_, c_, w_ = kit.ramp(height, stops_mid), kit.ramp(height, stops_cool), kit.ramp(height, stops_warm)
                return tuple(kit.lerp(kit.lerp(m_[i], c_[i], cool_mask), w_[i], warm_mask) for i in range(3))
        else:
            palette = s['colour.palette']                              # [[height 0..255, "#rrggbb"], ...] measured from the colour map
            stops = [(p / 255.0, srgb_hex_to_linear(c)) for p, c in palette]

            def palette_colour(height):
                return kit.ramp(height, stops)
        col = palette_colour(hgt)

    # =============================================================================================== 5 STAINS
    kit.begin('5 STAINS: dark splotches of the source map stamped on top (two layers of stamps, shifted against each other), kept away from joints and row edges')
    stain_amount = float(s['stains.amount'])
    d_min = kit.minimum(d_left, d_right)
    edge_dist = kit.minimum(y_in, row_h - y_in)
    keep_away = float(s['stains.keep_away'])
    clear = kit.smoothstep(keep_away, keep_away + 8.0, d_min) * kit.smoothstep(6.0, 16.0, edge_dist)
    if stain_amount > 0 and not identity:
        centres = s['source.stain_centres']
        n_st = len(centres)
        cell = T / 5.0
        radius = float(s['stains.size'])
        for layer in range(2):
            off = layer * cell * 0.5
            ci, cj = kit.floor((Px + off) / cell), kit.floor((Yg + off) / cell)
            cih, cjh = ((ci % 5.0), (cj % 5.0)) if tile else (ci, cj)
            qa, qb, qc = kit.rand(cih, cjh, 31.0 + layer, seed_h)
            qd, qe, qf = kit.rand(cih, cjh, 41.0 + layer, seed_h)
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
            disc = (1.0 - kit.smoothstep(float(s['stains.edge_hardness']) * radius, radius, dist)) * present
            dark_limit, soft = float(s['stains.dark_limit']) / 255.0, float(s['stains.dark_softness']) / 255.0
            mask = disc * kit.saturate((dark_limit - st_h) / soft) * clear       # only the dark part of the stamp is painted
            hgt = kit.lerp(hgt, st_h, mask)
            if use_map_colour:
                st_c = kit.image(path_colour, xs_st, ys_st, colour=True, size=T)
            else:
                st_c = palette_colour(st_h)
            col = tuple(kit.lerp(c, sc_, mask) for c, sc_ in zip(col, st_c))

    # =============================================================================================== 6 JOINTS
    kit.begin('6 JOINTS, HALF JOINTS AND ROW EDGES: a dark ragged crack where one window meets the next, stepped partial cracks inside boards, a dark band along the row edges')

    def pebble_cells(count):
        if tile:
            x_, y_, z_, w_ = torus(count)
            return kit.cells4_rand(x_, y_, z_, w_ + seed_h * 5.0, 1.0)
        return kit.cells_rand(Px, Yg, count / T)

    fy = 1.0 / float(s['joints.wobble_length'])
    base_half = float(s['joints.width']) * 0.5
    wvar = float(s['joints.width_variation'])
    rag, notch_amount = float(s['joints.raggedness']), float(s['joints.notches'])
    key_left = rh * 11.3 + jb * 3.7
    key_right = rh * 11.3 + jb_next * 3.7
    n_a = kit.noise3(y_in * fy, key_left, 1.0 + seed_h * 7.0, 1.0, detail=2.0)       # how far the crack of the left end reaches into this board
    n_b = kit.noise3(y_in * fy, key_right, 2.0 + seed_h * 7.0, 1.0, detail=2.0)      # the same for the right end
    n_c = kit.noise3(y_in * fy * 0.4, key_left + 0.5, 3.0 + seed_h * 7.0, 1.0, detail=1.0)
    n_d = kit.noise3(y_in * fy * 0.4, key_right + 0.5, 4.0 + seed_h * 7.0, 1.0, detail=1.0)
    half_left = kit.maximum(base_half * (1.0 + wvar * (2.0 * width_l - 1.0)) * (1.0 + rag * (2.0 * n_a - 1.0)) + notch_amount * 7.0 * kit.smoothstep(0.62, 0.72, n_c), 1.0)
    half_right = kit.maximum(base_half * (1.0 + wvar * (2.0 * width_r - 1.0)) * (1.0 + rag * (2.0 * n_b - 1.0)) + notch_amount * 7.0 * kit.smoothstep(0.62, 0.72, n_d), 1.0)
    crack_l = 1.0 - kit.smoothstep(half_left - 0.7, half_left + 0.7, d_left)
    crack_r = 1.0 - kit.smoothstep(half_right - 0.7, half_right + 0.7, d_right)
    crack_v = kit.maximum(crack_l * strength_l, crack_r * strength_r)
    # the sideways part of a stepped joint: a crack along the grain from the upper part of the cut to the lower part
    def step_crack(plain_pos, step_size, step_at, width_factor):
        up, low = plain_pos - 0.5 * step_size, plain_pos + 0.5 * step_size
        hh = kit.maximum(0.75 * base_half * (1.0 + wvar * (2.0 * width_factor - 1.0)), 1.0)
        along_x = kit.greater(Px, kit.minimum(up, low) - hh) * kit.less(Px, kit.maximum(up, low) + hh) * kit.greater(kit.absolute(step_size), 1.0)
        return (1.0 - kit.smoothstep(hh - 0.7, hh + 0.7, kit.absolute(y_in - step_at))) * along_x
    crack_v = kit.maximum(crack_v, kit.maximum(step_crack(plain_s, size_s, at_s, width_l) * strength_l, step_crack(plain_e, size_e, at_e, width_r) * strength_r))

    # a half joint inside the board (for looks, it hides no cut): a crack from the top or the bottom edge of the row that tapers to a point,
    # steps to the side and then runs a little way along the grain, like the stepped half-height cracks of the source
    half_on = kit.less(q11, float(s['joints.half_share']))
    from_top = kit.less(q13, 0.5)
    dfe = kit.where(from_top, y_in, row_h - y_in)                # dots from the row edge it starts at
    xh = plain_s + (0.22 + 0.56 * q12) * (plain_e - plain_s) + 4.0 * (kit.noise3(y_in * (1.0 / 30.0), rh * 5.1 + jb * 2.3, 61.0 + seed_h, 1.0, detail=1.0) * 2.0 - 1.0) + (q18 * 2.0 - 1.0) * 0.12 * dfe
    depth = row_h * float(s['joints.half_depth']) * (0.6 + 0.8 * q14)
    taper = kit.saturate(1.0 - dfe / depth)                      # a wedge: widest at the row edge, a point at the bottom of the crack
    half_w = (1.0 + (float(s['joints.half_width']) - 1.0) * q17) * taper
    crack_hv = (1.0 - kit.smoothstep(half_w - 0.6, half_w + 0.6, kit.absolute(Px - xh))) * kit.greater(taper, 0.1)
    run_dir = 1.0 - 2.0 * kit.greater(q15, 0.5)
    run_len = float(s['joints.half_run']) * (0.5 + q16)
    along = (Px - xh) * run_dir
    crack_hr = (1.0 - kit.smoothstep(0.7, 1.7, kit.absolute(dfe - depth))) * kit.smoothstep(0.0, 6.0, along) * (1.0 - kit.smoothstep(0.55 * run_len, run_len, along))
    crack_half = kit.maximum(crack_hv, crack_hr) * half_on
    crack_v = kit.maximum(crack_v, crack_half)

    # the dark band along every row edge (the cut between two rows lies in the middle of it): only added where the source is not already dark,
    # so the rubble of the real gaps of the source stays visible; its width changes from place to place
    next_id = ((row_no + 1.0) % float(R)) if tile else (rh + 1.0)
    band_half = float(s['gaps.band_width']) * 0.5
    bvar = float(s['gaps.band_variation'])
    count_band = round(T / 31.0)
    n_t = x_noise(count_band, rh, 5.0, detail=2.0)
    n_u = x_noise(count_band, next_id, 5.0, detail=2.0)          # the edge below this row: the same noise as the top of the next row
    half_top = kit.maximum(band_half * (1.0 + bvar * (2.0 * n_t - 1.0)), 0.8)
    half_bottom = kit.maximum(band_half * (1.0 + bvar * (2.0 * n_u - 1.0)), 0.8) * (1.0 + 1.2 * kit.less(kit.absolute(band - 3.0), 0.5))      # the bottom of the last source row is bare wood (no gap below it): its band is made wider
    band_t = 1.0 - kit.smoothstep(half_top - 0.7, half_top + 0.7, y_in)
    band_b = 1.0 - kit.smoothstep(half_bottom - 0.7, half_bottom + 0.7, row_h - y_in)
    wood_here = kit.saturate((hgt - 0.12) / 0.20)                # 0 where the source is already dark (a real gap), 1 on wood
    crack_band = kit.maximum(band_t, band_b) * wood_here
    crack = kit.label(kit.maximum(crack_v * float(s['joints.darkness']), crack_band), 'joint crack or row gap (1 = inside)')
    shade = (1.0 - kit.smoothstep(base_half, base_half + 14.0, d_min)) * float(s['joints.edge_shade'])
    # a worn light lip along the wood next to the crack (a bevel: lighter and a little higher)
    out_left, out_right = d_left - half_left, d_right - half_right
    lip_l = kit.smoothstep(0.0, 0.6, out_left) * (1.0 - kit.smoothstep(1.2, 2.8, out_left))
    lip_r = kit.smoothstep(0.0, 0.6, out_right) * (1.0 - kit.smoothstep(1.2, 2.8, out_right))
    lip = kit.maximum(lip_l, lip_r) * float(s['joints.edge_lip'])
    # what lies inside the crack: dark dirt with a few pebbles of different sizes in small groups (the real gaps of the source bring their own)
    dist_p, rnd_p = pebble_cells(round(0.1 * T))
    thr = 0.09 + 0.19 * rnd_p
    clump = kit.smoothstep(0.35, 0.65, patchy(6.0, 7.0, detail=1.0))
    pebbles = (1.0 - kit.smoothstep(thr, thr + 0.09, dist_p)) * clump * float(s['joints.pebbles'])
    dirt = patchy(round(0.25 * T), 5.0)

    # =============================================================================================== 7 PATCHES
    kit.begin('7 PATCHES: large soft drift and dark blotches (made here, not copied from a map)')
    drift = patchy(float(s['masks.drift_size']), 1.0)
    blotch = kit.smoothstep(0.60, 0.78, patchy(float(s['masks.blotch_size']), 2.0))
    gain = (1.0 + (drift - 0.5) * (2.0 * float(s['masks.drift_amount']))) * (1.0 - float(s['masks.blotch_amount']) * blotch)

    # =============================================================================================== 8 COLOUR
    kit.begin('8 COLOUR: tone per board, patches, joints')
    row_tone = kit.rand1(rh, 3.3, 0.0, seed_h)
    tone = kit.label(1.0 + (q3 - 0.5) * float(s['boards.tone_variation']) + (row_tone - 0.5) * float(s['boards.row_tone_variation']), 'tone of this board (a little from the board, more from the row)')
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
        kit.combine_colour(flip_h, flip_v, half_on, out.inputs['Colour'])
        kit.to_socket(flip_h * 0.25 + flip_v * 0.5 + half_on * 0.25, out.inputs['Height'])
        kit.to_socket(0.0, out.inputs['Roughness'])
    elif debug == 'landmarks':
        kit.combine_colour(kit.saturate(shown_sum * 16.0), kit.saturate(painted_sum * 16.0), 0.0, out.inputs['Colour'])
        kit.to_socket(shown_sum, out.inputs['Height'])
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
