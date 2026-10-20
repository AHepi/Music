# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# METAL LAYOUT: the new box that answers "which piece of steel am I on, and where on it?" for every dot of a riveted steel wall, and hands
# the shared layers the same eleven numbers the slate LAYOUT gives them (the "bundle": piece_id, row, local_x, local_y, piece_width,
# piece_height, edge_distance, top_edge_distance, gap_mask, piece_mask, base_height; their meaning is in
# recipes/slate_layers/interface/interface.md). It paints nothing.
#
# What the wall is made of (words used: a BAR is one long steel strap; a PANEL is the bare plate between the bars; a CREASE is the thin dark
# line along every bar edge; a SEAM is a thin dark line across a panel):
#  1. UPRIGHT BARS and LYING BARS. A few of each (2 and 2 by default), spread evenly over the tile with a random push each and a random
#     starting place, so a new Seed gives a new wall. Upright bars have nearly the same width; lying bars have random widths between two
#     settings. All positions are worked out once, when the box is built (from the Seed), and written into the nodes as plain numbers.
#  2. WHO LIES ON TOP. Where an upright bar crosses a lying bar, one of them lies on top, in a chequered way (bar numbers added up: even =
#     the lying bar on top). So every bar passes UNDER at least one other bar and is cut there: no piece runs right round the tile, which
#     matters because the shared layers read patterns on each piece's own coordinates, and a piece that met itself at the tile edge would show
#     a seam. A bar that crosses the tile edge is simply one piece that continues on the other side (its coordinates do not restart there).
#  3. PIECES. Every dot belongs to exactly one piece: a stretch of an upright bar between two cuts, a stretch of a lying bar between two cuts,
#     or a panel between two upright and two lying bars. The dot finds its column (by counting how many upright-bar edges lie to its left)
#     and its row (the same with lying-bar edges above it), which is cheap: a few "is it past this line?" tests.
#  3b. DIAGONAL BRACES (added in the second round). Some panels (Brace Share, only panels that are not very long and thin) get one brace
#     that runs from one corner of the panel to the opposite corner, like the diagonal braces of the reference. A brace is one more
#     piece kind: inside the panel, the dots within Brace Half Width of the corner-to-corner line belong to the BRACE, with their own
#     coordinates (local_x along the brace, local_y across it, 0 at its upper side). The brace is cut off by the panel's own edges, so it
#     passes under the bars at both ends, and the tile still repeats because a brace never leaves its panel. The shared layers need no
#     change for this: they only read the bundle.
#  4. CREASES AND SEAMS. Along every piece edge a thin band (Crease Width, split between the two pieces) is the gap (gap_mask 1): the dark
#     crease of the reference. Some panels (Seam Share) also get one thin seam across them, upright or lying, at a random place; the seam is
#     a gap line inside the panel (the panel is not split in two).
#  5. BUNDLE. local_x, local_y (0 at the TOP of the piece), the piece's size, the distance to its nearest edge (creases and seams count),
#     the distance below its upper edge, the two masks, and base_height: bars high (Bar Level), plate lower (Plate Level), creases low,
#     with a short rounded slope (Bevel Width) at every edge. The shared layers and the new ones can tell a bar from the plate by this level.
#
# ONE DELIBERATE CHANGE OF MEANING (recorded in the notes): on LYING bars, top_edge_distance starts at Bar Top Offset instead of 0. A lying
# bar's upper edge lies ABOVE the plate, so nothing casts a shadow on it; the shared OUTLINE AND SHADOW layer draws its shadow band under every
# piece's upper edge, and with this offset its band (and MOSS's drips from the upper edge) do not reach onto lying bars. Upright bar stretches
# keep the normal meaning: their upper end lies UNDER a lying bar, so the shadow there is right.
#
# Settings are named 'metal_layout.<name>'. Bar counts, the seed and bar widths set where things are, so they are read when the box is built;
# the rest are sockets in the Shader editor. Sizes are TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.008 = 10 dots).
# Limits: at least 2 upright and 2 lying bars (with fewer, a bar would cross nothing and run round the whole tile). A brace stays inside one
# panel (it never runs on across a bar), so a long diagonal that crosses several panels is not possible.
import math
import random
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'metal_layout'
GROUP_NAME = 'METAL LAYOUT'

CONTROLS = [
    Control('seed', 'Seed', 1, 0, 1000, 'random seed of the layout: where the bars are, how wide the lying bars are, which panels get a seam', build_time=True),
    Control('upright_count', 'Upright Bars', 2, 2, 6, 'how many upright bars cross one base tile (at least 2)', build_time=True),
    Control('lying_count', 'Lying Bars', 2, 2, 6, 'how many lying bars cross one base tile (at least 2)', build_time=True),
    Control('upright_half_width', 'Upright Half Width', 0.054, 0.01, 0.1, 'half the width of an upright bar, in tile units (0.054 = 68 dots, so a bar about 136 dots wide)', build_time=True),
    Control('upright_width_jitter', 'Upright Width Jitter', 0.004, 0.0, 0.03, 'how much an upright bar\'s half width varies, plus or minus, in tile units', build_time=True),
    Control('lying_half_width_low', 'Lying Half Width Low', 0.038, 0.01, 0.1, 'narrowest half width of a lying bar, in tile units (0.038 = 48 dots)', build_time=True),
    Control('lying_half_width_high', 'Lying Half Width High', 0.067, 0.01, 0.1, 'widest half width of a lying bar, in tile units (0.067 = 84 dots)', build_time=True),
    Control('position_jitter', 'Position Jitter', 0.35, 0.0, 0.8, 'how far a bar is pushed from its even place, as a share of half the distance between bars (0 = evenly spaced)', build_time=True),
    Control('brace_share', 'Brace Share', 0.5, 0.0, 1.0, 'share of the panels (of a suitable shape) that get a diagonal brace from corner to corner'),
    Control('brace_half_width', 'Brace Half Width', 0.04, 0.01, 0.1, 'half the width of a brace, in tile units (0.04 = 50 dots, so a brace about 100 dots wide)'),
    Control('brace_aspect_low', 'Brace Aspect Low', 0.65, 0.2, 1.0, 'a panel gets a brace only when its height is at least this many times its width (keeps the brace near 45 degrees)'),
    Control('brace_aspect_high', 'Brace Aspect High', 1.55, 1.0, 5.0, 'a panel gets a brace only when its height is at most this many times its width'),
    Control('brace_flip_share', 'Brace Flip Share', 0.2, 0.0, 1.0, 'share of the braces that run the other way (from the upper right to the lower left)'),
    Control('crease_width', 'Crease Width', 0.0028, 0.0, 0.02, 'width of the dark crease along every piece edge, in tile units (0.0028 = 3.5 dots; half lies on each side of the edge)'),
    Control('seam_share', 'Seam Share', 0.6, 0.0, 1.0, 'share of the panels that have one thin seam across them'),
    Control('seam_width', 'Seam Width', 0.0016, 0.0, 0.01, 'width of a panel seam, in tile units (0.0016 = 2 dots)'),
    Control('edge_softness', 'Edge Softness', 0.0004, 0.0, 0.005, 'width of the soft ramp of the masks at a crease edge, in tile units (0.0004 = half a dot)'),
    Control('bar_level', 'Bar Level', 0.62, 0.0, 1.0, 'base relief height of a bar (0..1)'),
    Control('plate_level', 'Plate Level', 0.45, 0.0, 1.0, 'base relief height of a panel of bare plate (0..1)'),
    Control('crease_level', 'Crease Level', 0.30, 0.0, 1.0, 'base relief height in a crease or seam (0..1)'),
    Control('bevel_width', 'Bevel Width', 0.003, 0.0001, 0.05, 'how wide the rounded slope from a crease up to the face of a piece is, in tile units'),
    Control('bar_top_offset', 'Bar Top Offset', 0.05, 0.0, 0.3, 'on LYING bars, top_edge_distance starts at this instead of 0, so the shadow band and drips that the shared layers draw under an upper edge do not reach onto a bar that lies above the plate (0 = the plain meaning)'),
]
SEED_SALT = 7919


def wall_plan(values, tiles=1):
    """Where the bars are, worked out once from the seed (plain numbers). Returns (columns, rows) as lists of (left/top edge, width) in
    shares of the WHOLE picture, sorted, and the place the counting starts (the left edge of the first upright bar; the top edge of the first
    lying bar). With several base tiles across (tiles), the picture holds tiles x as many bars, each 1/tiles as wide (new content, not copies)."""
    rng = random.Random(int(values['seed']) * SEED_SALT + 17)
    upright_count, lying_count = max(2, int(values['upright_count'])) * tiles, max(2, int(values['lying_count'])) * tiles

    def spread(count, half_width_of):
        phase = rng.random()
        bars = []
        for index in range(count):
            push = rng.uniform(-1.0, 1.0) * values['position_jitter'] * 0.5 / count
            centre = (phase + (index + 0.5) / count + push) % 1.0
            half = half_width_of() / tiles
            bars.append(((centre - half) % 1.0, 2.0 * half))
        bars.sort()
        start = bars[0][0]
        relative = [((edge - start) % 1.0, width) for edge, width in bars]
        for (edge_a, width_a), (edge_b, _) in zip(relative, relative[1:] + [(1.0, 0.0)]):
            if edge_a + width_a >= edge_b - 0.01:
                raise ValueError('METAL LAYOUT: two bars overlap; use fewer bars, narrower bars or less Position Jitter')
        return start, relative

    up_half, up_jitter = values['upright_half_width'], values['upright_width_jitter']
    column_start, columns = spread(upright_count, lambda: up_half + rng.uniform(-1.0, 1.0) * up_jitter)
    low, high = values['lying_half_width_low'], values['lying_half_width_high']
    row_start, rows = spread(lying_count, lambda: rng.uniform(low, high))
    return column_start, columns, row_start, rows


def band_finder(b, position, bars):
    """For a position 0..1 counted from the first bar's leading edge: which band it is in (bar 0, gap 0, bar 1, gap 1 ...), where that band
    starts, how wide it is, whether it is a bar (1) or a gap (0), the bar number, and the "past this edge?" tests (reused for the cuts)."""
    edges = []                                             # (place, kind) kind 'end' = a bar ends here, 'start' = the next bar starts
    for index, (edge, width) in enumerate(bars):
        if index > 0:
            edges.append((edge, 'start'))
        edges.append((edge + width, 'end'))
    places = [place for place, _ in edges]
    start, width, on_bar, number = 0.0, places[0], 1.0, 0.0
    past = {}
    for index, (place, kind) in enumerate(edges):
        previous = places[index - 1] if index > 0 else 0.0
        following = places[index + 1] if index + 1 < len(places) else 1.0
        step = b.gt(position, place)
        past[round(place, 9)] = step
        start = b.math('MULTIPLY_ADD', step, place - previous, start)
        width = b.math('MULTIPLY_ADD', step, (following - place) - (place - previous), width)
        on_bar = b.math('MULTIPLY_ADD', step, -1.0 if kind == 'end' else 1.0, on_bar)
        if kind == 'start':
            number = b.add(number, step)
    return start, width, on_bar, number, past


def stretch_finder(b, position, cut_ends, cut_starts, past):
    """Where the stretch of a bar that this dot lies on starts (counted along the bar), how long it is, and its number (0, 1, ...).
    cut_ends: places where a crossing bar on top ENDS (a stretch starts there); cut_starts: where the next crossing bar on top starts."""
    count = len(cut_ends)
    lengths = [((cut_starts[(k + 1) % count] + (1.0 if k + 1 == count else 0.0)) - cut_ends[k]) for k in range(count)]
    start, length, number = cut_ends[-1] - 1.0, lengths[-1], 0.0
    previous_start, previous_length = cut_ends[-1] - 1.0, lengths[-1]
    for k in range(count):
        step = past[round(cut_ends[k], 9)]
        start = b.math('MULTIPLY_ADD', step, cut_ends[k] - previous_start, start)
        length = b.math('MULTIPLY_ADD', step, lengths[k] - previous_length, length)
        number = b.add(number, step)
        previous_start, previous_length = cut_ends[k], lengths[k]
    return start, length, b.mod(number, float(count))                     # past the last cut the stretch wraps round: it is stretch 0 again


def pick(b, index_socket, values_by_index):
    """The value that belongs to bar number index_socket (a whole number 0, 1, ...): a sum of 'is it this bar?' times its value."""
    total = None
    for index, value in enumerate(values_by_index):
        this = b.math('COMPARE', index_socket, float(index), 0.25)
        total = b.mul(this, value) if total is None else b.math('MULTIPLY_ADD', this, value, total)
    return total


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    inputs = [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1 left to right, y = 0..1 bottom to top')]
    inputs += [(c.label, c.kind, values[c.key], c.low, c.high, c.text) for c in CONTROLS if not c.build_time]
    outputs = [(name, 'float', li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]
    tree, b = li.make_plain_group(GROUP_NAME, inputs, outputs)
    S = b.input
    tiles = int(parameters.get('recipe.tiles_across', 1))
    column_start, columns, row_start, rows = wall_plan(values, tiles)
    seed = float(values['seed'])

    # ---- 1. where the dot is, counted from the first upright bar's left edge and from the first lying bar's top edge (both 0..1, wrapping)
    u, v, _ = b.xyz(S('Vector'))
    x = b.frac(b.sub(u, column_start))
    y = b.frac(b.sub(b.sub(1.0, v), row_start))                                # picture-down: 0 at the top of the first lying bar

    # ---- 2. column and row bands
    col_start, col_width, on_upright, upright_number, past_x = band_finder(b, x, columns)
    row_start_d, row_height, on_lying, lying_number, past_y = band_finder(b, y, rows)

    # ---- 3. who lies on top at a crossing (chequered), and which kind of piece this dot is on
    lying_on_top = b.sub(1.0, b.mod(b.add(upright_number, lying_number), 2.0))
    upright_piece = b.mul(on_upright, b.sub(1.0, b.mul(on_lying, lying_on_top)))
    lying_piece = b.mul(on_lying, b.sub(1.0, b.mul(on_upright, b.sub(1.0, lying_on_top))))
    bar = b.add(upright_piece, lying_piece)

    # ---- 4. stretches of bars between the crossings where they pass under (cut places known when the box is built)
    up_starts, up_lengths, up_numbers = [], [], []
    for i in range(len(columns)):
        cuts = [j for j in range(len(rows)) if (i + j) % 2 == 0]               # lying bars that lie on top of upright bar i
        ends = [rows[j][0] + rows[j][1] for j in cuts]
        starts = [rows[j][0] for j in cuts]
        s, length, number = stretch_finder(b, y, ends, starts, past_y)
        up_starts.append(s), up_lengths.append(length), up_numbers.append(number)
    lie_starts, lie_lengths, lie_numbers = [], [], []
    for j in range(len(rows)):
        cuts = [i for i in range(len(columns)) if (i + j) % 2 == 1]            # upright bars that lie on top of lying bar j
        ends = [columns[i][0] + columns[i][1] for i in cuts]
        starts = [columns[i][0] for i in cuts]
        s, length, number = stretch_finder(b, x, ends, starts, past_x)
        lie_starts.append(s), lie_lengths.append(length), lie_numbers.append(number)
    up_start, up_length, up_number = pick(b, upright_number, up_starts), pick(b, upright_number, up_lengths), pick(b, upright_number, up_numbers)
    lie_start, lie_length, lie_number = pick(b, lying_number, lie_starts), pick(b, lying_number, lie_lengths), pick(b, lying_number, lie_numbers)

    # ---- 5. the piece's own coordinates (tile units from its left and top edge) and size
    across = b.mixf(b.sub(x, col_start), b.sub(x, lie_start), lying_piece)
    width = b.mixf(col_width, lie_length, lying_piece)
    down = b.mixf(b.sub(y, row_start_d), b.sub(y, up_start), upright_piece)
    height = b.mixf(row_height, up_length, upright_piece)
    if tiles > 1:                                                              # shares of the whole picture -> tile units (shares of ONE base tile)
        across, width, down, height = (b.mul(value, float(tiles)) for value in (across, width, down, height))
    # ---- 5b. diagonal braces: in a panel that has one, the dots near its corner-to-corner line are a BRACE piece with their own coordinates
    panel = b.mul(b.sub(1.0, on_upright), b.sub(1.0, on_lying))
    brace_hash = b.hash4(b.vec(upright_number, lying_number, seed * 0.37 + 11.0), 9.0)
    brace_roll, flip_roll, _unused = b.channels(brace_hash.outputs['Color'])
    aspect = b.div(height, b.mx(width, 1e-6))
    suitable = b.mul(b.gt(aspect, S('Brace Aspect Low')), b.lt(aspect, S('Brace Aspect High')))
    brace_on = b.mul(b.mul(panel, suitable), b.lt(brace_roll, S('Brace Share')))
    flip = b.lt(flip_roll, S('Brace Flip Share'))
    across_m = b.mixf(across, b.sub(width, across), flip)                          # mirrored when the brace runs the other way
    diagonal = b.sqrt(b.add(b.mul(width, width), b.mul(height, height)))
    side = b.div(b.sub(b.mul(across_m, height), b.mul(down, width)), diagonal)     # distance from the corner-to-corner line, plus = its upper side
    along = b.div(b.add(b.mul(across_m, width), b.mul(down, height)), diagonal)    # distance along the line from the starting corner
    brace_half = S('Brace Half Width')
    brace_here = b.mul(brace_on, b.lt(b.absolute(side), brace_half))
    across_p = b.mixf(across, along, brace_here)                                   # the piece's own coordinates: panel, or brace where there is one
    width_p = b.mixf(width, diagonal, brace_here)
    down_p = b.mixf(down, b.sub(brace_half, side), brace_here)
    height_p = b.mixf(height, b.mul(brace_half, 2.0), brace_here)
    local_x = b.div(across_p, width_p)
    local_y = b.div(down_p, height_p)

    # ---- 6. creases (along every piece edge) and seams (one thin line across some panels)
    half_crease = b.mul(S('Crease Width'), 0.5)
    nearest = b.mn(b.mn(across, b.sub(width, across)), b.mn(down, b.sub(height, down)))
    brace_edge = b.absolute(b.sub(b.absolute(side), brace_half))                   # distance to the nearest side of the brace (inside or outside it)
    nearest = b.mn(nearest, b.mixf(1.0, brace_edge, brace_on))
    edge = b.sub(nearest, half_crease)
    roll = b.hash4(b.vec(upright_number, lying_number, seed * 0.37), 7.0)
    seam_roll, seam_turn, seam_place = b.channels(roll.outputs['Color'])
    seam_on = b.mul(b.mul(panel, b.sub(1.0, brace_on)), b.lt(seam_roll, S('Seam Share')))
    seam_lying = b.lt(seam_turn, 0.5)
    place = b.math('MULTIPLY_ADD', seam_place, 0.4, 0.3)
    seam_distance = b.mixf(b.absolute(b.sub(across, b.mul(place, width))), b.absolute(b.sub(down, b.mul(place, height))), seam_lying)
    seam_edge = b.sub(seam_distance, b.mul(S('Seam Width'), 0.5))
    edge = b.mixf(edge, b.mn(edge, seam_edge), seam_on)
    soft = b.mx(S('Edge Softness'), 1e-6)
    piece_mask = b.smoothstep(edge, b.mul(soft, -1.0), soft)
    gap_mask = b.sub(1.0, piece_mask)
    edge_distance = b.mx(edge, 0.0)
    top_edge_distance = b.math('MULTIPLY_ADD', b.add(lying_piece, brace_here), S('Bar Top Offset'), b.mx(b.sub(down_p, half_crease), 0.0))

    # ---- 7. one random number per piece: kind (1 upright, 2 lying, 3 panel, 4 brace), bar or panel number, stretch number
    kind = b.math('MULTIPLY_ADD', b.add(lying_piece, brace_here), 1.0, b.math('MULTIPLY_ADD', panel, 2.0, 1.0))      # 1 upright, 2 lying, 3 panel, 4 brace
    number = b.mixf(b.mixf(b.math('MULTIPLY_ADD', lying_number, 10.0, upright_number), lying_number, lying_piece), upright_number, upright_piece)
    stretch = b.math('MULTIPLY_ADD', upright_piece, up_number, b.mul(lying_piece, lie_number))
    piece_id = b.hash4(b.vec(kind, number, stretch), seed * 1.3 + 0.5).outputs['Value']

    # ---- 8. bare relief: bars high, plate lower, creases low, a short rounded slope at every edge
    level = b.mixf(S('Plate Level'), S('Bar Level'), b.add(bar, brace_here))
    ramp = b.smoothstep(edge, 0.0, b.mx(S('Bevel Width'), 1e-5))
    base_height = b.math('MULTIPLY_ADD', b.sub(level, S('Crease Level')), ramp, S('Crease Level'))

    bundle = {'piece_id': piece_id, 'row': b.div(lying_number, float(len(rows))), 'local_x': local_x, 'local_y': local_y,
              'piece_width': width_p, 'piece_height': height_p, 'edge_distance': edge_distance, 'top_edge_distance': top_edge_distance,
              'gap_mask': gap_mask, 'piece_mask': piece_mask, 'base_height': base_height}
    for name in li.BUNDLE_NAMES:
        b.output(name, bundle[name])
    return tree
