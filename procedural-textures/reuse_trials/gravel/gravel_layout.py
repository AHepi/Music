# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# GRAVEL LAYOUT: the small box that answers "which stone am I on, and where on it?" for every dot, and hands the shared layers the same
# eleven numbers the slate LAYOUT gives them (the "bundle": piece_id, row, local_x, local_y, piece_width, piece_height, edge_distance,
# top_edge_distance, gap_mask, piece_mask, base_height; their meaning is in recipes/slate_layers/interface/interface.md). It paints nothing.
# Here a "piece" is one stone and the "gap" is the soil between the stones.
#
# It is mostly a COPY of lib/contrib/stone_tools.polygon_stones (one random angular stone per square of a grid), changed in four ways:
#   1. it works inside a node box with the project's layer interface (the original needs a different helper object),
#   2. it also hands out where the dot is on its stone (the original worked this out inside and threw it away),
#   3. it stacks THREE grids of different sizes (big, middle, small stones). A dot takes the stone of the biggest grid it lies on, so
#      middle and small stones fill the gaps between the big ones and are partly hidden behind them (a heap),
#   4. (after the first full-size look) every stone edge is made ragged by a seamless noise, so the stones are not clean geometric polygons;
#   5. each grid is TURNED by its own angle (and slid), so the squares of the three grids do not line up: the first look (round 1) showed a
#      plaid of soil lines when all three grids were upright. A turned grid still repeats exactly when its two steps are whole numbers: the grid
#      is written as (a, b) = (across, up) steps of one square; the picture then holds a x a + b x b squares, the grid is turned by atan(b / a),
#      and a square's number is wrapped by subtracting whole multiples of the two steps (so the last square is followed by the first).
# How one stone is made: its square of the grid holds one stone. The stone is the part of the square where ALL of five straight-edge
# tests are true ("how far along direction k is the dot, compared with the radius of face k"). Direction, radius of every face, size,
# and a small shift of the stone's centre are random numbers made from the square's number, so they are the same for every dot of the
# square and the tile repeats exactly (square numbers are wrapped with a modulo, so square 0 follows the last square).
# A slow seamless noise bends all three grids a little so that rows of squares are not ruler straight.
#
# The eleven numbers, as the gravel makes them:
#   piece_id           one random number per stone (different between the three grids)
#   row                the size class: 0 = big, 0.5 = middle, 1 = small (no shared layer reads it)
#   local_x, local_y   across and down the stone, 0..1, local_y = 0 at the TOP of the stone (the stone is taken as a square of 2.2 radii)
#   piece_width/height 2.2 x the stone's nominal radius, in tile units
#   edge_distance      how far inside the VISIBLE stone the dot is (tile units); 0 at its edge and everywhere in the soil. A stone half hidden
#                      behind a bigger one counts the edge of the bigger stone too.
#   top_edge_distance  how far below the top of the stone's square the dot is (an approximation: the real top edge of a polygon is lower)
#   gap_mask / piece_mask  the soil / the stone (soft over about half a dot)
#   base_height        the bare relief: soil low, with a dip right next to each stone (this carries the soil's shadow, SOIL reads it),
#                      stones high with a rounded bevel and a gentle dome, a small random lift per stone
# Settings are named 'gravel_layout.<name>'. The number of grid squares and of faces change how many nodes the box has, so they are read when
# the box is built; everything else is a socket in the Shader editor.
# Sizes are TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.008 = 10 dots).
import math
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'gravel_layout'
GROUP_NAME = 'GRAVEL LAYOUT'
CLASS_NAMES = ('big', 'middle', 'small')
CLASS_SEED_OFFSET = {'big': 0.0, 'middle': 100.0, 'small': 200.0}
CLASS_SHIFT = {'big': (0.0, 0.0), 'middle': (0.37, 0.61), 'small': (0.71, 0.23)}      # grid slide, in squares

CONTROLS = [
    Control('big_grid_a', 'Big Grid Step Across', 9, -64, 64, 'the BIG stones\' grid is a square grid turned by atan(b / a); a and b are whole numbers and the tile holds a x a + b x b squares (9 and 4: 97 squares, a square about 127 dots wide, grid turned 24 degrees)', build_time=True),
    Control('big_grid_b', 'Big Grid Step Up', 4, -64, 64, 'see Big Grid Step Across', build_time=True),
    Control('middle_grid_a', 'Middle Grid Step Across', 17, -128, 128, 'the MIDDLE stones\' grid (17 and 17: 578 squares, a square about 52 dots wide, turned 45 degrees)', build_time=True),
    Control('middle_grid_b', 'Middle Grid Step Up', 17, -128, 128, 'see Middle Grid Step Across', build_time=True),
    Control('small_grid_a', 'Small Grid Step Across', 46, -256, 256, 'the SMALL stones\' grid (46 and -30: 3016 squares, a square about 23 dots wide, turned -33 degrees)', build_time=True),
    Control('small_grid_b', 'Small Grid Step Up', -30, -256, 256, 'see Small Grid Step Across', build_time=True),
    Control('big_sides', 'Big Stone Faces', 5, 3, 8, 'how many flat faces a big stone has', build_time=True),
    Control('middle_sides', 'Middle Stone Faces', 5, 3, 8, 'how many flat faces a middle stone has', build_time=True),
    Control('small_sides', 'Small Stone Faces', 4, 3, 8, 'how many flat faces a small stone has', build_time=True),
    Control('seed', 'Seed', 1.0, 0.0, 1000.0, 'random seed of the layout: changes where the stones are, their sizes and shapes, nothing else'),
    Control('big_presence', 'Big Stone Presence', 0.75, 0.0, 1.0, 'share of the big grid squares that hold a stone'),
    Control('middle_presence', 'Middle Stone Presence', 0.9, 0.0, 1.0, 'share of the middle grid squares that hold a stone'),
    Control('small_presence', 'Small Stone Presence', 0.8, 0.0, 1.0, 'share of the small grid squares that hold a stone'),
    Control('big_radius_low', 'Big Stone Radius Low', 0.26, 0.05, 0.5, 'smallest radius of a big stone, in squares (0.5 = touches the border of its square)'),
    Control('big_radius_high', 'Big Stone Radius High', 0.36, 0.05, 0.5, 'largest radius of a big stone, in squares (keep radius x 1.22 + jitter below 0.5 or the square border cuts the stone flat)'),
    Control('middle_radius_low', 'Middle Stone Radius Low', 0.26, 0.05, 0.5, 'smallest radius of a middle stone, in squares'),
    Control('middle_radius_high', 'Middle Stone Radius High', 0.36, 0.05, 0.5, 'largest radius of a middle stone, in squares'),
    Control('small_radius_low', 'Small Stone Radius Low', 0.24, 0.05, 0.5, 'smallest radius of a small stone, in squares'),
    Control('small_radius_high', 'Small Stone Radius High', 0.36, 0.05, 0.5, 'largest radius of a small stone, in squares'),
    Control('jitter', 'Jitter', 0.08, 0.0, 0.3, 'how far a stone may sit off the middle of its square, in squares'),
    Control('warp', 'Warp', 0.5, 0.0, 2.0, 'how far (in squares) a slow noise bends the grids, so the rows of squares are not straight'),
    Control('ragged_edges', 'Ragged Edges', 0.12, 0.0, 0.5, 'how far a noise pushes every stone edge in or out, as a share of the stone radius (0 = clean geometric polygons)'),
    Control('edge_softness', 'Edge Softness', 0.0004, 0.0, 0.005, 'width of the soft ramp of the masks at a stone edge, in tile units (0.0004 = half a dot)'),
    Control('soil_level', 'Soil Level', 0.12, 0.0, 1.0, 'base relief height of the soil (0..1)'),
    Control('stone_level', 'Stone Level', 0.50, 0.0, 1.0, 'base relief height of the stones (0..1)'),
    Control('level_jitter', 'Level Jitter', 0.04, 0.0, 0.3, 'how much each stone is higher or lower than the others (plus and minus this much)'),
    Control('bevel_width', 'Bevel Width', 0.003, 0.0001, 0.05, 'how wide the rounded slope from soil up to the stone is, in tile units'),
    Control('dome', 'Dome', 0.08, 0.0, 0.5, 'how much higher the middle of a stone is than its rim (height scale 0..1)'),
    Control('shadow_reach', 'Shadow Reach', 0.0064, 0.0005, 0.03, 'how far from a stone the soil is pushed down, in tile units (0.0064 = 8 dots); SOIL paints its shadow from this dip'),
    Control('shadow_depth', 'Shadow Depth', 0.06, 0.0, 0.3, 'how deep the soil dips right next to a stone (height scale 0..1)'),
]
OUTPUTS = [(name, 'float', li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]


def three_random_numbers(b, cell_x, cell_y, seed):
    """Three random numbers (0..1) for a pair of whole numbers: the White Noise node's Color output (red, green, blue)."""
    node = b.white(b.vec(cell_x, cell_y, seed), '3D')
    return b.channels(node.outputs['Color'])


def one_class(b, S, name, step_a, step_b, tiles, sides, u, v, warp_x, warp_y, ragged):
    """One grid of stones (a square grid turned by the whole-number step (step_a, step_b)). Returns a dict of sockets: inside (tile units,
    + inside the stone, - outside, about -1 tile when the square holds no stone), piece_id, dx, dy_up (the dot's offset from the stone's
    centre, in picture directions, tile units), radius (nominal, tile units)."""
    squares_per_tile = step_a * step_a + step_b * step_b
    side = 1.0 / math.sqrt(squares_per_tile)                      # side of one square, in tile units
    a_all, b_all, squares_all = float(step_a * tiles), float(step_b * tiles), float(squares_per_tile * tiles * tiles)    # for the whole picture
    seed = b.add(S('Seed'), CLASS_SEED_OFFSET[name])
    shift_x, shift_y = CLASS_SHIFT[name]
    bend = b.mul(S('Warp'), 2.0 * side / float(tiles))             # a bend of 'Warp' squares, in picture fractions
    pu = b.add(u, b.mul(b.sub(warp_x, 0.5), bend))
    pv = b.add(v, b.mul(b.sub(warp_y, 0.5), bend))
    grid_x = b.add(b.sub(b.mul(pu, a_all), b.mul(pv, b_all)), shift_x)       # the turned grid's own coordinates
    grid_y = b.add(b.add(b.mul(pu, b_all), b.mul(pv, a_all)), shift_y)
    whole_x, whole_y = b.floor(grid_x), b.floor(grid_y)
    # wrap the square number: subtract whole multiples of the two steps of the grid until the number lies in one fixed corner of the repeat
    alpha = b.floor(b.div(b.add(b.mul(whole_x, a_all), b.mul(whole_y, b_all)), squares_all))
    beta = b.floor(b.div(b.sub(b.mul(whole_y, a_all), b.mul(whole_x, b_all)), squares_all))
    cell_x = b.add(b.sub(whole_x, b.mul(alpha, a_all)), b.mul(beta, b_all))
    cell_y = b.sub(b.sub(whole_y, b.mul(alpha, b_all)), b.mul(beta, a_all))
    across = b.sub(b.frac(grid_x), 0.5)                          # dot position inside its square, -0.5 .. 0.5, in the grid's own directions
    upward = b.sub(b.frac(grid_y), 0.5)
    r_presence, r_size, r_turn = three_random_numbers(b, cell_x, cell_y, seed)
    r_shift_x, r_shift_y, r_id = three_random_numbers(b, cell_x, cell_y, b.add(seed, 11.0))
    jitter = b.mul(S('Jitter'), 2.0)
    offset_x = b.sub(across, b.mul(b.sub(r_shift_x, 0.5), jitter))        # the dot's offset from the stone's own centre, in squares
    offset_y = b.sub(upward, b.mul(b.sub(r_shift_y, 0.5), jitter))
    low, high = S(f'{name.capitalize()} Stone Radius Low'), S(f'{name.capitalize()} Stone Radius High')
    radius = b.add(low, b.mul(r_size, b.sub(high, low)))          # nominal radius, in squares
    present = b.gt(r_presence, b.sub(1.0, S(f'{name.capitalize()} Stone Presence')))
    best = None
    for face in range(sides):                                     # the stone = where all the face tests are true
        random_turn, random_radius, _spare = three_random_numbers(b, cell_x, cell_y, b.add(seed, 40.0 + face))
        angle = b.add(b.mul(r_turn, 2.0 * math.pi), b.add(2.0 * math.pi * face / sides, b.mul(b.sub(random_turn, 0.5), 0.9)))
        along = b.add(b.mul(offset_x, b.math('COSINE', angle)), b.mul(offset_y, b.math('SINE', angle)))
        distance = b.sub(along, b.mul(radius, b.add(0.78, b.mul(random_radius, 0.44))))               # negative inside this face's half-plane
        best = distance if best is None else b.mx(best, distance)
    inside_squares = b.mixf(-1.0, b.mul(best, -1.0), present)     # + inside, - outside; -1 square if no stone here
    # offsets back into picture directions (the grid is turned): across = (a x + b y) / (a x a + b x b), up = (a y - b x) / (a x a + b x b), in tile units
    scale = 1.0 / float(squares_per_tile)
    to_picture_x = b.mul(b.add(b.mul(offset_x, float(step_a)), b.mul(offset_y, float(step_b))), scale)
    to_picture_up = b.mul(b.sub(b.mul(offset_y, float(step_a)), b.mul(offset_x, float(step_b))), scale)
    radius_tile = b.mul(radius, side)
    inside_tile = b.add(b.mul(inside_squares, side), b.mul(ragged, b.mul(S('Ragged Edges'), radius_tile)))      # the ragged edge: + inside, - outside
    return {'inside': inside_tile, 'piece_id': r_id, 'dx': to_picture_x, 'dy_up': to_picture_up, 'radius': radius_tile}


def build_group(parameters):
    """Make the GRAVEL LAYOUT node group. Reads 'gravel_layout.*' settings and 'recipe.tiles_across'."""
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    tiles = int(parameters.get('recipe.tiles_across', 1))
    inputs = [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1 left to right, y = 0..1 BOTTOM to top of the picture')]
    for control in CONTROLS:
        if not control.build_time:
            inputs.append((control.label, control.kind, values[control.key], control.low, control.high, control.text))
    tree, b = li.make_plain_group(GROUP_NAME, inputs, OUTPUTS)
    S = b.input
    u, v, _ = b.xyz(S('Vector'))

    # a slow seamless noise bends all three grids (two numbers: sideways and up-down)
    warp = b.tnoise_vector(2.5 * tiles, 2.5 * tiles, 2.0, 0.5, b.add(b.mul(S('Seed'), 1.7), 3.0))
    warp_x, warp_y, _ = b.channels(warp)

    # a seamless noise that makes every stone edge ragged (-1 .. +1, about 18 dots between wobbles, with finer ones on top)
    ragged = b.mul(b.sub(b.tileable_noise(S('Vector'), 70.0 * tiles, 3.0, 0.55, b.add(b.mul(S('Seed'), 3.1), 7.0)), 0.5), 5.0)
    classes = {}
    for name in CLASS_NAMES:
        classes[name] = one_class(b, S, name, int(values[f'{name}_grid_a']), int(values[f'{name}_grid_b']), tiles, int(values[f'{name}_sides']), u, v, warp_x, warp_y, ragged)
    big, middle, small = classes['big'], classes['middle'], classes['small']

    # ---------------------------------------------------------------------------------------------- who is on top
    # the VISIBLE inside distance of each stone: a stone also ends where a bigger stone starts (the bigger one lies on top of it)
    visible_big = big['inside']
    visible_middle = b.mn(middle['inside'], b.mul(big['inside'], -1.0))
    visible_small = b.mn(small['inside'], b.mn(b.mul(middle['inside'], -1.0), b.mul(big['inside'], -1.0)))
    best = b.mx(visible_big, b.mx(visible_middle, visible_small))              # + on a visible stone, - on the soil (minus the distance to the nearest stone)
    on_big, on_middle, on_small = b.gt(visible_big, 0.0), b.gt(visible_middle, 0.0), b.gt(visible_small, 0.0)    # at most one is 1

    def pick(key):
        """The number `key` of the stone that is on top here (the small grid's number on the soil)."""
        return b.mixf(b.mixf(small[key], middle[key], on_middle), big[key], on_big)

    piece_id, dx, dy_up, radius = pick('piece_id'), pick('dx'), pick('dy_up'), pick('radius')
    size_class = b.mixf(b.mixf(1.0, 0.5, on_middle), 0.0, on_big)

    # ---------------------------------------------------------------------------------------------- the bundle
    piece_mask = b.math('MULTIPLY_ADD', best, b.div(1.0, b.mx(S('Edge Softness'), 1e-6)), 0.5, clamp=True)
    edge_distance = b.mx(best, 0.0)
    extent = b.mx(b.mul(radius, 2.2), 1e-5)                                    # the stone taken as a square of 2.2 radii
    local_x = b.math('ADD', b.add(b.div(dx, extent), 0.5), 0.0, clamp=True)
    local_y = b.math('ADD', b.sub(0.5, b.div(dy_up, extent)), 0.0, clamp=True)       # 0 at the TOP
    top_edge_distance = b.mul(b.mul(local_y, extent), piece_mask)
    # relief: soil low with a dip beside every stone, stone high with a bevel and a gentle dome
    soil_distance = b.mx(b.mul(best, -1.0), 0.0)
    soil_height = b.sub(S('Soil Level'), b.mul(S('Shadow Depth'), b.sub(1.0, b.smoothstep(soil_distance, 0.0, S('Shadow Reach')))))
    stone_height = b.add(b.add(S('Stone Level'), b.mul(b.sub(b.mul(piece_id, 2.0), 1.0), S('Level Jitter'))),
                         b.mul(S('Dome'), b.smoothstep(edge_distance, 0.0, b.mul(radius, 0.8))))
    lift = b.smoothstep(edge_distance, 0.0, b.mx(S('Bevel Width'), 1e-5))
    base_height = b.math('MULTIPLY_ADD', b.sub(stone_height, soil_height), lift, soil_height)
    for name, socket in (('piece_id', piece_id), ('row', size_class), ('local_x', local_x), ('local_y', local_y),
                         ('piece_width', extent), ('piece_height', extent), ('edge_distance', edge_distance),
                         ('top_edge_distance', top_edge_distance), ('gap_mask', b.sub(1.0, piece_mask)), ('piece_mask', piece_mask),
                         ('base_height', base_height)):
        b.output(name, socket)
    return tree
