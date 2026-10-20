# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# LAYOUT answers one question for every dot of the picture: "which slate am I on, and where on it?". It draws no paint at all. It makes
# the slates (rows, widths, joints, chipped edges, rounded corners) and hands every other layer the same set of numbers, the
# "LAYOUT BUNDLE": piece_id, row, local_x, local_y, piece_width, piece_height, edge_distance, top_edge_distance, gap_mask, piece_mask
# and base_height (full meaning in ../interface/interface.md). Any other surface that can produce the same eleven numbers (bricks,
# planks, tiles ...) can use the same DAMAGE, MOSS and COLOUR AND FADE layers.
#
# How it is made, in the order the nodes run (everything is shader nodes written by Python; nothing is a picture):
#  1. ROWS. The picture is cut into rows. Row edges are jittered steps of an even grid: edge k = (k + a small random number) x row height.
#     Because the random number belongs to the edge, the next row starts exactly where this one ends, and the last row ends exactly where
#     the first one starts again (the "wrap"), so the layout tiles exactly. Row heights therefore vary slightly. The tile edge cuts through
#     the middle of a row ("Row Phase" 0.5), never along a joint.
#  2. SLIDE. Every row is slid sideways by its own random amount, so the joints of one row are not above the joints of the next.
#  3. SLATES IN A ROW. Each row holds K slates (6 per tile across). Each slate gets a random width (log-normal: a bell-shaped number
#     put through exp), and all the widths of the row are scaled together so they add up to exactly the row length. The random numbers
#     come from a hash of (row number, slate number, seed), so every dot of the row computes the same widths without any loop.
#  4. JOINTS. Between neighbouring slates is a dark joint. It leans a little (each joint has its own small lean).
#  5. SHAPE. Each slate is a rectangle with rounded corners. Its four edges are pushed IN by seamless noise (chips: the noise only ever
#     removes slate, never adds), a different noise for every slate and a different strength for sides, top and bottom.
#  6. BUNDLE. From the distances to the four edges come edge_distance, the two masks, local_x/local_y and the rest. base_height is the
#     bare relief: joints low, slate level high, a rounded bevel along the edges, a tiny random lift per slate.
#
# Structural settings (rows per tile, slates per row per tile, tiles across) change how many nodes the group has, so they are read when
# the group is built ("build" settings). Everything else is a socket you can turn in the Shader editor.
# Sizes are in TILE units (1.0 = the whole base tile). To think in dots at 1254 dots per tile: multiply by 1254 (0.0064 = 8 dots).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layer_interface as li  # noqa: E402
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'layout'
GROUP_NAME = 'LAYOUT'

CONTROLS = [
    Control('rows_per_tile', 'Rows Per Tile', 8, 1, 64, 'how many rows of slates fit in one base tile (the reference has 8)', build_time=True),
    Control('slates_per_row', 'Slates Per Row Per Tile', 6, 1, 64, 'how many slates sit side by side in one row of one base tile (the reference has about 6)', build_time=True),
    Control('seed', 'Seed', 1.0, 0.0, 1000.0, 'random seed of the layout: changes the widths, slides, joints and chips, nothing else'),
    Control('row_height_jitter', 'Row Height Jitter', 0.05, 0.0, 0.45, 'how much the row edges wander, as a share of one row height (0.05 = rows differ by about 4 percent; 0 = all rows equal)'),
    Control('row_phase', 'Row Phase', 0.5, 0.0, 1.0, 'where the picture edge cuts through a row, as a share of a row (0.5 = through the middle, 0 = along a joint)'),
    Control('width_spread', 'Width Spread', 0.26, 0.0, 0.8, 'how different the slate widths are (the spread of the log-width BEFORE the widths are scaled to fill the row; 0.26 measures as about 0.22 on the finished slates, like the reference; 0 = all slates equal)'),
    Control('row_slide', 'Row Slide', 1.0, 0.0, 1.0, 'how far each row may be slid sideways (1 = anywhere, 0 = every row starts at the same joint, like a brick stack)'),
    Control('joint_width', 'Joint Width', 0.0014, 0.0, 0.01, 'narrowest dark joint between two slates of a row, in tile units (0.0014 = 1.8 dots); chips make it wider'),
    Control('row_gap', 'Row Gap', 0.0050, 0.0, 0.03, 'narrowest dark band between two rows, in tile units (0.005 = 6.3 dots); chips make it wider (the reference band is about 10.6 dots on average)'),
    Control('row_gap_top_share', 'Row Gap Top Share', 0.10, 0.0, 1.0, 'how much of the band between rows belongs to the top of the slate below (the rest lies under the slate above)'),
    Control('corner_radius', 'Corner Radius', 0.0064, 0.0, 0.05, 'rounding of the slate corners, in tile units (0.0064 = 8 dots)'),
    Control('corner_top_factor', 'Corner Top Factor', 0.6, 0.0, 3.0, 'the two top corners use this share of the corner radius (the reference has sharper top corners)'),
    Control('corner_bottom_factor', 'Corner Bottom Factor', 1.5, 0.0, 3.0, 'the two bottom corners use this multiple of the corner radius (rounder bottoms make the joints flare into the band between rows)'),
    Control('corner_radius_variation', 'Corner Radius Variation', 0.30, 0.0, 1.0, 'how much the corner rounding differs from slate to slate (0 = all the same)'),
    Control('joint_lean', 'Joint Lean', 0.010, 0.0, 0.05, 'largest sideways lean of a joint, as sideways distance per distance down (0.01 = 1.5 dots over a slate height); it is cut down so a joint never leaves its gap'),
    Control('ragged_side', 'Ragged Side', 0.0024, 0.0, 0.01, 'deepest chip into the left and right edges of a slate, in tile units (0.0024 = 3 dots)'),
    Control('ragged_top', 'Ragged Top', 0.0022, 0.0, 0.01, 'deepest chip into the top edge of a slate, in tile units (0.0022 = 2.8 dots)'),
    Control('ragged_bottom', 'Ragged Bottom', 0.0055, 0.0, 0.01, 'deepest chip into the bottom edge of a slate, in tile units (0.0055 = 7 dots)'),
    Control('ragged_scale', 'Ragged Scale', 100.0, 4.0, 400.0, 'how many chips (noise features) fit across one base tile: 100 = a chip about 12 dots long'),
    Control('ragged_detail', 'Ragged Detail', 4.0, 0.0, 8.0, 'how many finer noise layers are added to the chips (0 = smooth wobble, 3 = chipped)'),
    Control('ragged_chip', 'Ragged Chip', 2.0, 0.5, 4.0, 'chip sharpness: 1 = even wobble, 2 and more = mostly straight edge with some deep chips'),
    Control('bottom_tilt', 'Bottom Tilt', 0.02, 0.0, 0.1, 'how much the bottom edge of each slate slopes (random direction per slate), as height difference per width; makes the rows wave a little'),
    Control('edge_softness', 'Edge Softness', 0.0004, 0.0, 0.005, 'width of the soft ramp of the masks at an edge, in tile units (0.0004 = half a dot); 0 = hard (render samples smooth it)'),
    Control('joint_level', 'Joint Level', 0.08, 0.0, 1.0, 'base relief height in the joints (0..1)'),
    Control('slate_level', 'Slate Level', 0.50, 0.0, 1.0, 'base relief height on the slates (0..1)'),
    Control('bevel_width', 'Bevel Width', 0.0035, 0.0001, 0.05, 'how wide the rounded slope from joint level up to slate level is, in tile units (0.0035 = 4.4 dots)'),
    Control('slate_level_jitter', 'Slate Level Jitter', 0.03, 0.0, 0.3, 'how much each slate\'s height differs from the others (plus and minus this much)'),
    Control('slate_ramp', 'Slate Ramp', 0.04, -0.3, 0.3, 'how much higher the bottom of a slate is than its top (a slate lies slanted; plus = bottom higher)'),
]
DEFAULTS = {c.key: c.default for c in CONTROLS}

OUTPUTS = [(name, 'float', li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]


def build_group(parameters):
    """Make the LAYOUT node group. Reads 'layout.*' settings (defaults above) and 'recipe.tiles_across' (how many base tiles across)."""
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    tiles = int(parameters.get('recipe.tiles_across', 1))
    rows_per_tile = int(values['rows_per_tile'])
    slates_per_tile = int(values['slates_per_row'])
    rows = rows_per_tile * tiles              # rows in the whole picture
    slates = slates_per_tile * tiles          # slates in one row of the whole picture
    pitch = 1.0 / rows_per_tile               # height of one row, in tile units

    inputs = [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1 left to right, y = 0..1 BOTTOM to top of the picture')]
    for control in CONTROLS:
        if not control.build_time:
            inputs.append((control.label, control.kind, values[control.key], control.low, control.high, control.text))
    tree, b = li.make_plain_group(GROUP_NAME, inputs, OUTPUTS)
    S = b.input
    seed = S('Seed')

    # ---------------------------------------------------------------------------------------------- 1. ROWS
    u, v, _ = b.xyz(S('Vector'))
    big_x = b.mul(u, tiles)                                   # x across the whole picture, in base-tile units
    big_y = b.sub(float(tiles), b.mul(v, tiles))              # y DOWN the picture (0 = top), in base-tile units
    row_y = b.sub(big_y, b.mul(S('Row Phase'), pitch))        # the same, moved so that row edges sit at (k + jitter) x pitch
    row_guess = b.floor(b.mul(row_y, 1.0 / pitch))            # the row an even grid would give; the true row is this one, one above or one below

    def row_edge_jitter(whole_number):
        """The random shift of row edge number `whole_number` (wrapped, so edge R is edge 0 again): plus or minus Row Height Jitter."""
        wrapped = b.mod(whole_number, float(rows))
        hashed = b.hash4(b.vec(wrapped, seed, 3.1), 0.25).outputs['Value']
        return b.mul(b.sub(hashed, 0.5), b.mul(S('Row Height Jitter'), 2.0))

    guess_above = b.add(row_guess, -1.0)
    guess_below = b.add(row_guess, 1.0)
    guess_below2 = b.add(row_guess, 2.0)
    jitter_a = row_edge_jitter(guess_above)
    jitter_b = row_edge_jitter(row_guess)
    jitter_c = row_edge_jitter(guess_below)
    jitter_d = row_edge_jitter(guess_below2)
    edge_guess = b.mul(b.add(row_guess, jitter_b), pitch)                   # top edge of the guessed row
    edge_guess_next = b.mul(b.add(guess_below, jitter_c), pitch)            # top edge of the row below the guess
    is_above = b.lt(row_y, edge_guess)                                      # 1 if the dot is really one row higher
    is_below = b.sub(1.0, b.lt(row_y, edge_guess_next))                     # 1 if the dot is really one row lower
    row_number = b.add(b.sub(row_guess, is_above), is_below)
    jitter_top = b.math('MULTIPLY_ADD', is_below, b.sub(jitter_c, jitter_b), b.math('MULTIPLY_ADD', is_above, b.sub(jitter_a, jitter_b), jitter_b))
    jitter_bottom = b.math('MULTIPLY_ADD', is_below, b.sub(jitter_d, jitter_c), b.math('MULTIPLY_ADD', is_above, b.sub(jitter_b, jitter_c), jitter_c))
    row_top = b.mul(b.add(row_number, jitter_top), pitch)                   # where this row starts (a little below the one above)
    row_bottom = b.mul(b.add(b.add(row_number, 1.0), jitter_bottom), pitch)
    row_height = b.sub(row_bottom, row_top)
    row_centre = b.mul(b.add(row_top, row_bottom), 0.5)
    row_wrapped = b.mod(row_number, float(rows))                            # 0 .. rows-1, the same for the row and its wrap-around copy
    row_vector = b.vec(row_wrapped, seed, 1.7)                              # the "address" of this row for all random numbers below

    # ---------------------------------------------------------------------------------------------- 2. SLIDE
    slide = b.mul(b.mul(b.hash4(row_vector, 777.5).outputs['Value'], float(tiles)), S('Row Slide'))
    along = b.math('WRAP', b.sub(big_x, slide), 0.0, float(tiles))          # x along the row after the slide, 0 .. tiles

    # ---------------------------------------------------------------------------------------------- 3. SLATES IN A ROW
    raw_widths, piece_ids = [], []
    for j in range(slates):
        node = b.hash4(row_vector, j + 0.5)
        bell = b.gauss_like(node.outputs['Color'])
        raw_widths.append(b.exp(b.mul(bell, S('Width Spread'))))
        piece_ids.append(node.outputs['Value'])
    total = b.sum_of(raw_widths)
    to_row_length = b.div(float(tiles), total)
    widths = [b.mul(raw, to_row_length) for raw in raw_widths]               # add up to exactly `tiles`
    edges = [0.0]                                                            # left edge of slate j (slate 0 starts at 0)
    for j in range(1, slates):
        edges.append(b.add(edges[j - 1], widths[j - 1]))
    passed = [None] + [b.gt(along, edges[j]) for j in range(1, slates)]      # 1 once the dot is to the right of joint j

    def pick(values_per_slate):
        """The value of the slate the dot is on: start with slate 0 and add the step to the next slate for every joint already passed."""
        result = values_per_slate[0]
        for j in range(1, slates):
            result = b.math('MULTIPLY_ADD', passed[j], b.sub(values_per_slate[j], values_per_slate[j - 1]), result)
        return result

    left_edge = 0.0
    for j in range(1, slates):
        left_edge = b.math('MULTIPLY_ADD', passed[j], widths[j - 1], left_edge)   # = edges[slate] without picking edges one by one
    slate_width = pick(widths)
    piece_id = pick(piece_ids)

    # ---------------------------------------------------------------------------------------------- 4. JOINTS (lean)
    lean_nodes = [b.hash4(row_vector, j + 300.5) for j in range(slates)]
    leans = [node.outputs['Value'] for node in lean_nodes]
    tilts = [b.channels(node.outputs['Color'])[0] for node in lean_nodes]       # a second random number per slate
    lean_cap = b.mn(S('Joint Lean'), b.mul(b.div(S('Joint Width'), b.mx(row_height, 1e-4)), 0.9))   # a joint never leaves its gap
    lean_left = b.mul(b.sub(b.mul(pick(leans), 2.0), 1.0), lean_cap)
    lean_right = b.mul(b.sub(b.mul(pick(leans[1:] + leans[:1]), 2.0), 1.0), lean_cap)    # the joint on the right is the next slate's left joint
    from_centre = b.sub(row_y, row_centre)
    left_line = b.math('MULTIPLY_ADD', lean_left, from_centre, left_edge)
    right_line = b.math('MULTIPLY_ADD', lean_right, from_centre, b.add(left_edge, slate_width))
    half_joint = b.mul(S('Joint Width'), 0.5)

    # ---------------------------------------------------------------------------------------------- 5. SHAPE (distances inside the four edges)
    gap_top = b.mul(S('Row Gap'), S('Row Gap Top Share'))
    gap_bottom = b.sub(S('Row Gap'), gap_top)
    inside_left = b.sub(b.sub(along, left_line), half_joint)
    inside_right = b.sub(b.sub(right_line, along), half_joint)
    inside_top = b.sub(b.sub(row_y, row_top), gap_top)
    inside_bottom = b.sub(b.sub(row_bottom, gap_bottom), row_y)
    slope = b.mul(b.sub(b.mul(pick(tilts), 2.0), 1.0), S('Bottom Tilt'))                    # this slate's bottom edge slopes this much
    slate_middle = b.mul(b.add(left_line, right_line), 0.5)
    inside_bottom = b.math('MULTIPLY_ADD', slope, b.sub(along, slate_middle), inside_bottom)    # a sloping bottom edge

    vector = S('Vector')
    chip_scale = b.mul(S('Ragged Scale'), float(tiles))
    seed_sides = b.math('MULTIPLY_ADD', piece_id, 500.0, b.mul(seed, 7.0))
    seed_updown = b.add(seed_sides, 137.0)
    chips_sides = b.power(b.noise01(vector, chip_scale, S('Ragged Detail'), 0.5, seed_sides), S('Ragged Chip'))
    chips_updown = b.power(b.noise01(vector, chip_scale, S('Ragged Detail'), 0.5, seed_updown), S('Ragged Chip'))
    inside_left = b.sub(inside_left, b.mul(chips_sides, S('Ragged Side')))
    inside_right = b.sub(inside_right, b.mul(chips_sides, S('Ragged Side')))
    inside_top = b.sub(inside_top, b.mul(chips_updown, S('Ragged Top')))
    inside_bottom = b.sub(inside_bottom, b.mul(chips_updown, S('Ragged Bottom')))

    # rounded rectangle: distance inside the nearest edge, with corners cut by a circle of radius `radius`
    radius = b.mul(S('Corner Radius'), b.add(1.0, b.mul(S('Corner Radius Variation'), b.sub(b.mul(piece_id, 2.0), 1.0))))
    near_top = b.lt(inside_top, inside_bottom)                                   # 1 when the dot is nearer the top edge than the bottom edge
    radius = b.mul(radius, b.math('MULTIPLY_ADD', near_top, b.sub(S('Corner Top Factor'), S('Corner Bottom Factor')), S('Corner Bottom Factor')))
    side_nearest = b.mn(inside_left, inside_right)
    updown_nearest = b.mn(inside_top, inside_bottom)
    corner_x = b.mx(b.sub(radius, side_nearest), 0.0)
    corner_y = b.mx(b.sub(radius, updown_nearest), 0.0)
    corner_length = b.sqrt(b.add(b.mul(corner_x, corner_x), b.mul(corner_y, corner_y)))
    inside = b.sub(b.add(b.mn(side_nearest, updown_nearest), b.mx(corner_x, corner_y)), corner_length)   # + inside the slate, - in the joint

    # ---------------------------------------------------------------------------------------------- 6. THE BUNDLE
    steepness = b.div(1.0, b.mx(S('Edge Softness'), 1e-6))
    piece_mask = b.math('MULTIPLY_ADD', inside, steepness, 0.5, clamp=True)
    gap_mask = b.sub(1.0, piece_mask)
    edge_distance = b.mx(inside, 0.0)
    top_edge_distance = b.mx(inside_top, 0.0)
    piece_width = b.sub(slate_width, S('Joint Width'))
    piece_height = b.sub(row_height, S('Row Gap'))
    local_x = b.maprange(along, b.add(left_line, half_joint), b.add(b.sub(right_line, half_joint), 1e-6), 0.0, 1.0, True)
    local_y = b.maprange(row_y, b.add(row_top, gap_top), b.add(b.sub(row_bottom, gap_bottom), 1e-6), 0.0, 1.0, True)
    row_out = b.div(row_wrapped, float(rows))

    profile = b.smoothstep(edge_distance, 0.0, b.mx(S('Bevel Width'), 1e-5))
    lift = b.mul(b.sub(b.mul(piece_id, 2.0), 1.0), S('Slate Level Jitter'))
    tilt = b.mul(b.sub(local_y, 0.5), S('Slate Ramp'))
    top_level = b.add(b.add(S('Slate Level'), lift), tilt)
    base_height = b.math('MULTIPLY_ADD', b.sub(top_level, S('Joint Level')), profile, S('Joint Level'))

    for name, socket in (('piece_id', piece_id), ('row', row_out), ('local_x', local_x), ('local_y', local_y), ('piece_width', piece_width),
                         ('piece_height', piece_height), ('edge_distance', edge_distance), ('top_edge_distance', top_edge_distance),
                         ('gap_mask', gap_mask), ('piece_mask', piece_mask), ('base_height', base_height)):
        b.output(name, socket)
    return tree
