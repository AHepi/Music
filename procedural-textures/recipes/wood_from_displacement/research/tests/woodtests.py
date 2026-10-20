# What this does: the small test node setups for the research guide "08 Research - making big non-repeating surfaces from one map".
# Each function builds Blender nodes (through nodekit.py) that read the uploaded wood height map and colour map in a different
# way and returns the number (height) or three numbers (colour) to show. They are tests, not the finished recipe.
# Coordinates used everywhere: X = across the picture in dots, Yd = down the picture in dots, one tile = 1254 dots (the size of
# the source map), so one source dot = one dot of the default tile. "area" = how many tiles wide and high the picture covers.
import json
import math
import nodekit as nk

BASE = 'proc-work/'
PATH_H = BASE + 'reference/wood/height_as_uploaded.png'
PATH_C = BASE + 'reference/wood/colour.png'
SIZE = 1254.0

# slices of the source that start 3 dots above a dark gap and run to just above the next one (measured in measurement json):
# each slice = one gap (on top) + one board row. Order: row 2, row 3, row 4, row 5 of the source picture.
SLICE_START = [180.0, 457.0, 697.0, 967.0]
SLICE_LENGTH = [277.0, 240.0, 270.0, 287.0]


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _load_palette():
    """12 control points (height 0..1, linear colour) of the palette 'colour made from height' measured from the real colour map."""
    data = json.load(open(BASE + 'recipes/wood_from_displacement/research/measurements_wood_source_map.json'))['colour_versus_height']
    colours, edges = data['palette_from_height_32_bins_srgb_0_to_255'], data['palette_bin_height_edges_0_to_255']
    points = []
    for k in (0, 1, 2, 4, 8, 12, 16, 20, 24, 27, 29, 31):
        points.append(((edges[k] + edges[k + 1]) / 2.0 / 255.0, tuple(_srgb_to_linear(v) for v in colours[k])))
    return points


PALETTE = _load_palette()


def palette_colour(kit, h):
    """Wood colour made from a height value alone (piecewise straight lines through the measured palette)."""
    out = [PALETTE[0][1][c] for c in range(3)]
    for (h0, c0), (h1, c1) in zip(PALETTE[:-1], PALETTE[1:]):
        t = kit.clamp((h - h0) / (h1 - h0))
        for c in range(3):
            out[c] = out[c] + (c1[c] - c0[c]) * t
    return tuple(out)


def tile_coordinates(kit, area):
    u, v = kit.uv()
    return u * (SIZE * area), (1.0 - v) * (SIZE * area)


INTERP = ['Linear']          # picture reading mode used by sample() unless told otherwise (a test may change it)


def sample(kit, channel, xs, ys, extension='EXTEND', interpolation=None):
    """Read the source at (xs, ys) dots. channel 'height' -> one number, 'colour' -> (r, g, b)."""
    interpolation = interpolation or INTERP[0]
    if channel == 'height':
        return kit.image(PATH_H, xs, ys, colour=False, extension=extension, interpolation=interpolation)[0]
    return kit.image(PATH_C, xs, ys, colour=True, extension=extension, interpolation=interpolation)


def dark_line(kit, d, wobble, width=6.0):
    """1 on a dark butt-joint line, 0 away from it. d = distance in dots to the nearest board end."""
    return 1.0 - kit.smoothstep(0.0, width, d + wobble)


# ----------------------------------------------------------------------------------------------------------- A0 plain repeat
def build_plain_repeat(kit, channel, area=1.0, **p):
    """What we start from: the source repeated as it is (the picture wraps around; its seam shows)."""
    X, Yd = tile_coordinates(kit, area)
    xs, ys = X % SIZE, Yd % SIZE
    return sample(kit, channel, xs, ys, extension='REPEAT')


# ----------------------------------------------------------------------------------------------------------- A1 / A2 / A3 pieces
# Where knots sit in the 4 clean source rows (rows 2, 3, 4, 5 of the source). Measured in measurements_wood_source_map.json.
PLAIN_LOW = [470.0, 0.0, 290.0, 0.0]          # left end of the knot-free stretch of each source row
PLAIN_HIGH = [1254.0, 1254.0, 710.0, 1254.0]  # right end of the knot-free stretch (row 4 has two knots, so only the middle is free)
KNOT_X_ROW2 = 350.0
KNOT_X_ROW4 = [170.0, 832.0]


def build_pieces(kit, channel, area=1.0, mode='full', tile_mode=True, boards_per_row=3, rows=5, seed=1.0,
                 jitter=0.5, tone=0.30, joints=True, zoom=0.12, p_knot=0.2, colour_source='map', **p):
    """Per-piece random sampling ("texture bombing by pieces").
    mode 'rows_only': every board reads the source row that is at the same height, only moved sideways by its own random amount and
                      sometimes flipped left-right (the simplest version).
    mode 'full'     : every board picks one of the 4 clean source rows (with its dark gap on top), a random start along it,
                      a random direction, a random zoom and a random tone. Knots can land anywhere (pure chance).
    mode 'curated'  : like 'full', but knots are rationed: only a board that is chosen to be a knot board (chance p_knot) shows a knot, put
                      at a random place inside the board; all other boards start in the knot-free stretch of their source row.
    tile_mode True  : random numbers repeat after one tile (5 rows, boards_per_row boards) so the picture wraps without a seam.
    tile_mode False : random numbers come from the global row/board number, so a bigger area never repeats."""
    INTERP[0] = p.get('interpolation', 'Linear')
    X, Yd = tile_coordinates(kit, area)
    P = SIZE / rows                                  # row pitch in dots
    Lb = SIZE / boards_per_row                       # nominal board length in dots
    r = kit.floor(Yd / P)
    y_in = Yd - r * P
    rh = (r % rows) if tile_mode else r
    shift = kit.rand1(rh, 1.0, 0.0, seed) * Lb       # each row is shifted sideways by its own random amount
    Xs = X - shift

    def edge(i):
        ih = (i % boards_per_row) if tile_mode else i
        return i * Lb + (kit.rand1(rh, ih, 2.0, seed) - 0.5) * (jitter * Lb)

    i0 = kit.floor(Xs / Lb)
    e0, e1 = edge(i0), edge(i0 + 1)
    i = i0 - kit.less(Xs, e0) + kit.greater(Xs, e1)          # the board is the one before, the same, or the one after
    start, end = edge(i) + shift, edge(i + 1) + shift
    ih = (i % boards_per_row) if tile_mode else i
    q1, q2, q3 = kit.rand(rh, ih, 3.0, seed)         # per board: start along source row, flip, tone
    q4, q5, q6 = kit.rand(rh, ih, 4.0, seed)         # per board: warmth, knot board?, which source row
    q7, q8, q9 = kit.rand(rh, ih, 5.0, seed)         # per board: which knot, zoom, spare
    flip = kit.greater(q2, 0.5)
    t_board = X - start                              # dots from the left end of this board
    wobble = kit.sin(y_in * 0.11 + q1 * 6.28) * 2.5
    if mode == 'rows_only':
        sc = 1.0
        ys = Yd % SIZE
        xs = kit.pingpong(q1 * SIZE + (1.0 - 2.0 * flip) * t_board, SIZE)
    else:
        if mode == 'curated':
            is_knot = kit.less(q5, p_knot)
            band = kit.where(is_knot, kit.where(kit.less(q6, 0.5), 0.0, 2.0), kit.floor(q6 * 4.0))
        else:
            band = kit.floor(q6 * 4.0)
        a_b = kit.pick(band, [kit.const(v) for v in SLICE_START])
        len_b = kit.pick(band, [kit.const(v) for v in SLICE_LENGTH])
        sc = (len_b / P) * (1.0 + zoom * (q8 - 0.5) * 2.0)       # source dots per output dot (fit the row pitch, plus a random zoom)
        Lw = (end - start) * sc                                  # length of the source window this board shows
        if mode == 'curated':
            lo = kit.pick(band, [kit.const(v) for v in PLAIN_LOW])
            hi = kit.pick(band, [kit.const(v) for v in PLAIN_HIGH])
            x0_plain = lo + kit.maximum(hi - lo - Lw, 0.0) * q1
            knot_x = kit.where(kit.less(band, 1.0), KNOT_X_ROW2, kit.where(kit.less(q7, 0.5), KNOT_X_ROW4[0], KNOT_X_ROW4[1]))
            x0_knot = kit.clamp(knot_x - Lw * (0.25 + 0.5 * q1), 0.0, SIZE - Lw)
            x0 = kit.where(is_knot, x0_knot, x0_plain)
        else:
            x0 = q1 * kit.maximum(SIZE - Lw, 0.0)
        ys = kit.pingpong(a_b + y_in * sc, SIZE)          # (mirror back if a zoomed window runs past the bottom of the map)
        xs = kit.pingpong(x0 + kit.where(flip, Lw - t_board * sc, t_board * sc), SIZE)
    if channel == 'height':
        value = sample(kit, 'height', xs, ys)
        if joints:
            j = dark_line(kit, kit.minimum(X - start, end - X), wobble)
            value = kit.lerp(value, 0.04, j)
        return value
    if colour_source == 'height_palette':
        red, green, blue = palette_colour(kit, sample(kit, 'height', xs, ys))
    else:
        red, green, blue = sample(kit, 'colour', xs, ys)
    t = 1.0 + (q3 - 0.5) * tone                      # per-board brightness
    warm = (q4 - 0.5) * 0.12                         # per-board warm/cool shift
    red, green, blue = red * (t * (1.0 + warm)), green * t, blue * (t * (1.0 - warm))
    if joints:
        j = dark_line(kit, kit.minimum(X - start, end - X), wobble)
        dark = 0.012
        red, green, blue = kit.lerp(red, dark, j), kit.lerp(green, dark * 0.8, j), kit.lerp(blue, dark * 0.7, j)
    return red, green, blue


# ----------------------------------------------------------------------------------------------------------- B hex / stochastic tiling
def logistic_gauss(kit, u):
    """Turn an even spread (0..1) into a bell-shaped spread. Uses the logistic curve as a stand-in for the Gaussian one
    (the exact version needs a lookup table). 1.702 makes the logistic curve match the Gaussian curve best."""
    u = kit.clamp(u, 0.004, 0.996)
    return kit.log(u / (1.0 - u)) / 1.702


def logistic_gauss_inverse(kit, g):
    return 1.0 / (1.0 + kit.exp(g * -1.702))


def build_hex(kit, channel, area=1.0, variant='gauss', sharp=3.0, cells=7.0, rows=8.0, tile_mode=True, seed=1.0, **p):
    """Hex ("stochastic") tiling: the surface is split into a triangle grid; each corner of a triangle carries a randomly shifted copy
    of the whole source map; the three copies that meet in a triangle are mixed with weights that are 1 at their own corner and 0 at
    the other two.  variant:
       'hard'     - only the strongest of the three copies is shown (hex-shaped patches, hard edges: random patches)
       'linear'   - plain weighted mix (the simple 3-sample hex blend people build in nodes: contrast and detail wash out)
       'variance' - weighted mix, then the grey spread is put back by dividing by sqrt(sum of squared weights)
       'gauss'    - Heitz and Neyret style: turn each sample into a bell-shaped spread, mix, divide by sqrt(sum w^2), turn back
    cells x rows triangles-pairs per tile (7 x 8 makes the triangle grid wrap exactly after one tile: the 8/7 ratio is 1 per cent off the
    perfect hex shape). Heights only (colours would need the Burley luminance trick)."""
    X, Yd = tile_coordinates(kit, area)
    u, v = X / SIZE, Yd / SIZE
    i = u * cells - v * (rows / 2.0)
    j = v * rows
    bi, bj = kit.floor(i), kit.floor(j)
    fx, fy = i - bi, j - bj
    z = 1.0 - fx - fy
    lower = kit.greater(z, 0.0)
    w1 = kit.where(lower, z, -z)
    w2 = kit.where(lower, fy, 1.0 - fy)
    w3 = kit.where(lower, fx, 1.0 - fx)
    # the exact vertex rule: lower triangle: v1=(0,0), v2=(0,1), v3=(1,0); upper triangle: v1=(1,1), v2=(1,0), v3=(0,1)
    verts = [(bi + (1.0 - lower), bj + (1.0 - lower)),
             (bi + (1.0 - lower), bj + lower),
             (bi + lower, bj + (1.0 - lower))]
    weights = [w1, w2, w3]
    samples = []
    for k, (vi, vj) in enumerate(verts):
        if tile_mode:
            jm = vj % rows
            shift = kit.floor(vj / rows)
            im = (vi + shift * (rows / 2.0)) % cells
        else:
            im, jm = vi, vj
        ox, oy, o3 = kit.rand(im, jm, 7.0, seed)
        Xl, Yl = (X % SIZE, Yd % SIZE) if tile_mode else (X, Yd)      # inside one tile, so the picture repeats exactly after one tile
        xs = kit.pingpong(Xl + ox * SIZE, SIZE)
        ys = kit.pingpong(Yl + oy * SIZE, SIZE)
        samples.append(sample(kit, 'height', xs, ys))
    if variant == 'hard':
        best = kit.where(kit.greater(w1, kit.maximum(w2, w3)), samples[0], kit.where(kit.greater(w2, w3), samples[1], samples[2]))
        return best
    ws = [kit.power(w, sharp) for w in weights] if variant != 'linear' else [kit.power(w, 1.0) for w in weights]
    total = ws[0] + ws[1] + ws[2]
    ws = [w / total for w in ws]
    if variant == 'linear':
        return samples[0] * ws[0] + samples[1] * ws[1] + samples[2] * ws[2]
    if variant == 'variance':
        mix = samples[0] * ws[0] + samples[1] * ws[1] + samples[2] * ws[2]
        norm = kit.sqrt(ws[0] * ws[0] + ws[1] * ws[1] + ws[2] * ws[2])
        return kit.clamp((mix - 0.5) / norm + 0.5)
    gs = [logistic_gauss(kit, s) for s in samples]
    mix = gs[0] * ws[0] + gs[1] * ws[1] + gs[2] * ws[2]
    norm = kit.sqrt(ws[0] * ws[0] + ws[1] * ws[1] + ws[2] * ws[2])
    return logistic_gauss_inverse(kit, mix / norm)


# ----------------------------------------------------------------------------------------------------------- C random tile bag
def build_bag(kit, channel, area=1.0, tiles=16, tile_mode=True, boards_per_row=3, rows=5, seed=1.0, joints=True, **p):
    """Random tile picking ("1-D Wang tiles"): a bag of 'tiles' fixed windows of the source (each = one gap + one board, a fixed start
    along the row); every board position pulls one tile out of the bag by chance. No flips, zoom or tone: only the choice differs."""
    import random
    rng = random.Random(7)
    table_band = [float(rng.randrange(4)) for _ in range(tiles)]
    table_x0 = [rng.uniform(0, 700) for _ in range(tiles)]
    X, Yd = tile_coordinates(kit, area)
    P = SIZE / rows
    Lb = SIZE / boards_per_row
    r = kit.floor(Yd / P)
    y_in = Yd - r * P
    rh = (r % rows) if tile_mode else r
    shift = kit.rand1(rh, 1.0, 0.0, seed) * Lb
    Xs = X - shift
    i = kit.floor(Xs / Lb)
    ih = (i % boards_per_row) if tile_mode else i
    pick = kit.floor(kit.rand1(rh, ih, 8.0, seed) * tiles * 0.9999)
    band = kit.pick(pick, [kit.const(v) for v in table_band])
    x0 = kit.pick(pick, [kit.const(v) for v in table_x0])
    a_b = kit.pick(band, [kit.const(v) for v in SLICE_START])
    sc = kit.pick(band, [kit.const(v) for v in SLICE_LENGTH]) / P
    t_board = Xs - i * Lb
    xs = kit.pingpong(x0 + t_board * sc, SIZE)
    ys = kit.pingpong(a_b + y_in * sc, SIZE)
    d = kit.minimum(t_board, Lb - t_board)
    j = dark_line(kit, d, 0.0)
    if channel == 'height':
        return kit.lerp(sample(kit, 'height', xs, ys), 0.04, j)
    red, green, blue = sample(kit, 'colour', xs, ys)
    return kit.lerp(red, 0.012, j), kit.lerp(green, 0.01, j), kit.lerp(blue, 0.008, j)


def build_wang_naive(kit, channel, area=1.0, cells=4, seed=1.0, **p):
    """Two-colour Wang tiles done the plain way: every square cell has 4 edges, each edge has colour 0 or 1 given by chance (shared with
    the neighbour), which names one of 16 tiles; each of the 16 tiles is a fixed window of the source. The windows do NOT agree along
    their edges (a real Wang set needs an offline step that makes them agree), so this shows what goes wrong."""
    import random
    rng = random.Random(11)
    table_x = [rng.uniform(0, SIZE - 320) for _ in range(16)]
    table_y = [rng.uniform(0, SIZE - 320) for _ in range(16)]
    X, Yd = tile_coordinates(kit, area)
    c = SIZE / cells
    ci, cj = kit.floor(X / c), kit.floor(Yd / c)
    cim, cjm = ci % cells, cj % cells
    top = kit.floor(kit.rand1(cim, cjm, 21.0, seed) + 0.5)
    left = kit.floor(kit.rand1(cim, cjm, 22.0, seed) + 0.5)
    bottom = kit.floor(kit.rand1(cim, (cj + 1.0) % cells, 21.0, seed) + 0.5)
    right = kit.floor(kit.rand1((ci + 1.0) % cells, cjm, 22.0, seed) + 0.5)
    index = top + right * 2.0 + bottom * 4.0 + left * 8.0
    x0 = kit.pick(index, [kit.const(v) for v in table_x])
    y0 = kit.pick(index, [kit.const(v) for v in table_y])
    lx, ly = X - ci * c, Yd - cj * c
    scale = 320.0 / c
    xs, ys = x0 + lx * scale, y0 + ly * scale
    if channel == 'height':
        return sample(kit, 'height', xs, ys)
    return sample(kit, 'colour', xs, ys)


# ----------------------------------------------------------------------------------------------------------- D bombing of stamps
KNOT_STAMPS = [(988.0, 104.0), (350.0, 378.0), (170.0, 806.0)]                 # centres of the three whole knots in the source
STAIN_STAMPS = [(438.0, 85.0), (321.0, 392.0), (1082.0, 815.0), (1087.0, 407.0), (812.0, 288.0), (837.0, 917.0), (460.0, 1131.0), (678.0, 507.0)]


def stamp_layer(kit, X, Yd, channel, base, cell, density, sources, radius, kind, layer, seed, tile_mode, zoom=0.25):
    """One layer of stamps placed one per grid cell (kept inside its cell so the pixel only has to look at its own cell).
    kind 'knot'  : the stamp replaces what is under it (soft round edge).
    kind 'stain' : only the dark stain part of the stamp is painted (grey below 135 of 255 counts as stain), so wood grain inside
                   the stamp circle is not copied."""
    n_cells = SIZE / cell
    ci, cj = kit.floor(X / cell), kit.floor(Yd / cell)
    cih, cjh = ((ci % n_cells), (cj % n_cells)) if tile_mode else (ci, cj)
    q1, q2, q3 = kit.rand(cih, cjh, 31.0 + layer, seed)
    q4, q5, q6 = kit.rand(cih, cjh, 41.0 + layer, seed)
    present = kit.less(q1, density)
    room = cell - 2.0 * radius
    cx = ci * cell + radius + q2 * room
    cy = cj * cell + radius + q3 * room
    dx, dy = X - cx, Yd - cy
    dist = kit.sqrt(dx * dx + dy * dy)
    which = kit.floor(q4 * len(sources) * 0.9999)
    sx = kit.pick(which, [kit.const(s[0]) for s in sources])
    sy = kit.pick(which, [kit.const(s[1]) for s in sources])
    z = 1.0 + (q5 - 0.5) * 2.0 * zoom                         # source dots per output dot
    fx = 1.0 - 2.0 * kit.greater(q6, 0.5)                     # flip left-right by chance
    xs, ys = sx + dx * z * fx, sy + dy * z
    mask = (1.0 - kit.smoothstep(0.62 * radius, radius, dist)) * present
    if channel == 'height':
        stamp = sample(kit, 'height', xs, ys)
    else:
        stamp_rgb = sample(kit, 'colour', xs, ys)
        stamp = sample(kit, 'height', xs, ys)                 # the height of the same dot decides how much stain to paint
    if kind == 'stain':
        mask = mask * kit.clamp((135.0 / 255.0 - stamp) / (55.0 / 255.0))
    if channel == 'height':
        return kit.lerp(base, stamp, mask)
    return tuple(kit.lerp(b, s, mask) for b, s in zip(base, stamp_rgb))


def build_bombing(kit, channel, area=1.0, tile_mode=True, knots=True, stains=True, density_knot=0.22, density_stain=0.45,
                  seed=1.0, base_mode='curated', p_knot=0.0, tone=0.30, colour_source='map', **p):
    """Base surface = boards from build_pieces with NO knots of their own (p_knot 0); then knots and stains are 'bombed' on top as stamps."""
    base = build_pieces(kit, channel, area, mode=base_mode, tile_mode=tile_mode, p_knot=p_knot, seed=seed, boards_per_row=p.get('boards_per_row', 2), tone=tone, colour_source=colour_source)
    X, Yd = tile_coordinates(kit, area)
    if stains:
        base = stamp_layer(kit, X, Yd, channel, base, SIZE / 5.0, density_stain, STAIN_STAMPS, 85.0, 'stain', 0.0, seed, tile_mode)
    if knots:
        base = stamp_layer(kit, X, Yd, channel, base, SIZE / 4.0, density_knot, KNOT_STAMPS, 80.0, 'knot', 1.0, seed, tile_mode, zoom=0.15)
    return base


# ----------------------------------------------------------------------------------------------------------- E large-scale masks
def periodic_noise(kit, X, Yd, scale, tile_mode, seed, detail=2.0):
    """Soft cloud pattern 0..1 with 'scale' clouds across one tile. In tile mode it wraps exactly after one tile (donut trick);
    otherwise it is plain noise that never repeats."""
    if tile_mode:
        a, b = X / SIZE * (2.0 * math.pi), Yd / SIZE * (2.0 * math.pi)
        r = scale / (2.0 * math.pi)
        return kit.noise4d(kit.cos(a) * (r * 1.0), kit.sin(a) * r, kit.cos(b) * r, kit.sin(b) * r + seed * 11.0, 1.0, detail)
    return kit.noise(X / SIZE * scale, Yd / SIZE * scale, seed * 11.0, 1.0, detail)


def build_masks(kit, channel, area=1.0, tile_mode=True, tone_big=0.25, stain_big=0.45, board_tone=0.30, knots=True, stains=True,
                seed=1.0, colour_source='map', **p):
    """The whole idea so far in one place: boards from build_pieces (curated, no knots of their own), stamps of knots and stains
    (build_bombing), then LARGE-SCALE masks over everything: a soft light/dark drift (tone_big) and big soft dark blotches (stain_big).
    The large masks do not copy anything from the map, so they are new for every part of a bigger area."""
    base = build_bombing(kit, channel, area, tile_mode=tile_mode, knots=knots, stains=stains, seed=seed, tone=board_tone,
                         colour_source=colour_source, boards_per_row=p.get('boards_per_row', 2))
    X, Yd = tile_coordinates(kit, area)
    drift = periodic_noise(kit, X, Yd, 2.0, tile_mode, seed + 1.0)                 # about 2 patches per tile
    blot = kit.smoothstep(0.62, 0.78, periodic_noise(kit, X, Yd, 5.0, tile_mode, seed + 2.0))   # a few blotches per tile
    gain = (1.0 + (drift - 0.5) * 2.0 * tone_big) * (1.0 - stain_big * blot)
    if channel == 'height':
        return kit.clamp(0.5 + (base - 0.5) * (1.0 - 0.35 * blot) + (drift - 0.5) * 0.10 * tone_big - 0.12 * blot)
    return tuple(c * gain for c in base)


# ----------------------------------------------------------------------------------------------------------- D2 bombing with a repeat zone (new in Blender 5)
def stamp_layer_zone(kit, X, Yd, channel, base, cell, density, sources, radius, kind, layer, seed, tile_mode, zoom=0.25):
    """Same stamps as stamp_layer, but the stamp centre may be anywhere in its cell, so a stamp can reach into the next cell. Each dot therefore visits
    the 3 x 3 cells around it in a REPEAT ZONE (a loop of nodes, new in Blender 5 shaders), 9 turns, and paints every stamp that reaches it."""
    tree = kit.tree
    rin = tree.nodes.new('GeometryNodeRepeatInput')
    rout = tree.nodes.new('GeometryNodeRepeatOutput')
    rin.pair_with_output(rout)
    rout.repeat_items.clear()
    names = ['h'] if channel == 'height' else ['r', 'g', 'b']
    rout.repeat_items.new('FLOAT', 'turn')
    for name in names:
        rout.repeat_items.new('FLOAT', name)
    rin.inputs['Iterations'].default_value = 9
    base_values = [base] if channel == 'height' else list(base)
    rin.inputs['turn'].default_value = 0.0
    for name, value in zip(names, base_values):
        kit._feed(rin.inputs[name], value)
    turn = nk.S(kit, rin.outputs['turn'])
    cur = [nk.S(kit, rin.outputs[name]) for name in names]
    n_cells = SIZE / cell
    ci0, cj0 = kit.floor(X / cell), kit.floor(Yd / cell)
    ci, cj = ci0 + ((turn % 3.0) - 1.0), cj0 + (kit.floor(turn / 3.0) - 1.0)
    cih, cjh = ((ci % n_cells), (cj % n_cells)) if tile_mode else (ci, cj)
    q1, q2, q3 = kit.rand(cih, cjh, 31.0 + layer, seed)
    q4, q5, q6 = kit.rand(cih, cjh, 41.0 + layer, seed)
    present = kit.less(q1, density)
    cx, cy = (ci + 0.1 + 0.8 * q2) * cell, (cj + 0.1 + 0.8 * q3) * cell
    dx, dy = X - cx, Yd - cy
    dist = kit.sqrt(dx * dx + dy * dy)
    which = kit.floor(q4 * len(sources) * 0.9999)
    sx = kit.pick(which, [kit.const(s[0]) for s in sources])
    sy = kit.pick(which, [kit.const(s[1]) for s in sources])
    z = 1.0 + (q5 - 0.5) * 2.0 * zoom
    fx = 1.0 - 2.0 * kit.greater(q6, 0.5)
    xs, ys = sx + dx * z * fx, sy + dy * z
    mask = (1.0 - kit.smoothstep(0.62 * radius, radius, dist)) * present
    stamp_h = sample(kit, 'height', xs, ys)
    if kind == 'stain':
        mask = mask * kit.clamp((135.0 / 255.0 - stamp_h) / (55.0 / 255.0))
    if channel == 'height':
        new = [kit.lerp(cur[0], stamp_h, mask)]
    else:
        srgb = sample(kit, 'colour', xs, ys)
        new = [kit.lerp(c, s, mask) for c, s in zip(cur, srgb)]
    tree.links.new((turn + 1.0).sock, rout.inputs['turn'])
    for name, value in zip(names, new):
        tree.links.new(value.sock, rout.inputs[name])
    out = [nk.S(kit, rout.outputs[name]) for name in names]
    return out[0] if channel == 'height' else tuple(out)


def build_bombing_zone(kit, channel, area=1.0, tile_mode=True, seed=1.0, tone=0.30, boards_per_row=2, **p):
    base = build_pieces(kit, channel, area, mode='curated', tile_mode=tile_mode, p_knot=0.0, seed=seed, boards_per_row=boards_per_row, tone=tone)
    X, Yd = tile_coordinates(kit, area)
    base = stamp_layer_zone(kit, X, Yd, channel, base, SIZE / 5.0, 0.45, STAIN_STAMPS, 110.0, 'stain', 0.0, seed, tile_mode)
    base = stamp_layer_zone(kit, X, Yd, channel, base, SIZE / 4.0, 0.22, KNOT_STAMPS, 95.0, 'knot', 1.0, seed, tile_mode, zoom=0.15)
    return base


# ----------------------------------------------------------------------------------------------------------- G image node edge options
def build_edge_demo(kit, channel, area=1.0, extension='MIRROR', **p):
    """Reads a window that runs 450 dots past the right edge and 450 dots past the bottom edge of the map, to show what each
    'Extension' choice of the Image Texture node does there (REPEAT wraps and shows the seam, EXTEND smears the last dot line, MIRROR bounces)."""
    u, v = kit.uv()
    xs = 800.0 + u * 900.0
    ys = 800.0 + (1.0 - v) * 900.0
    return sample(kit, 'height', xs, ys, extension=extension)


# ----------------------------------------------------------------------------------------------------------- B2 Voronoi patches (what most Blender add-ons do)
def build_voronoi_patches(kit, channel, area=1.0, scale=4.0, rotate=False, seed=1.0, **p):
    """Irregular patches from a Voronoi texture; every patch reads the whole source map shifted by its own random amount (and, optionally, mirrored).
    This is the core of add-ons like Patchwork or 'anti tile' node groups, shown here with hard patch edges (the edge softening of those add-ons
    would blur two shifted copies together along the patch edges)."""
    X, Yd = tile_coordinates(kit, area)
    u, v = X / SIZE, Yd / SIZE
    vec = kit._node('ShaderNodeCombineXYZ')
    kit._feed(vec.inputs['X'], u * scale)
    kit._feed(vec.inputs['Y'], v * scale)
    node = kit._node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1')
    kit.tree.links.new(vec.outputs[0], node.inputs['Vector'])
    node.inputs['Randomness'].default_value = 1.0
    sep = kit._node('ShaderNodeSeparateColor')
    kit.tree.links.new(node.outputs['Color'], sep.inputs[0])
    ox, oy, flipc = nk.S(kit, sep.outputs[0]), nk.S(kit, sep.outputs[1]), nk.S(kit, sep.outputs[2])
    xs = kit.pingpong(X + ox * SIZE, SIZE)
    ys = kit.pingpong(Yd + oy * SIZE, SIZE)
    return sample(kit, channel, xs, ys) if channel == 'height' else sample(kit, 'colour', xs, ys)
