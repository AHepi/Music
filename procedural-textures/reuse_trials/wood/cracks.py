# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# CRACKS (new layer for the wood trial): long thin dark splits that run ALONG the grain of a board and can start anywhere on it, narrowing to a
# point at both ends, with a pale fresh-wood lip along one side. The shared DAMAGE layer cannot do this: its cracks always start at a piece edge
# (on the turned boards that is the board end), so on wood they bunch at the butt joints. This box has exactly the same sockets as the shared
# layers (made by layer_interface.make_layer_group from the frozen snapshot), so COMBINE and the recipe treat it like any other layer.
#
# How a crack is placed, without any loop over cracks (so the cost is the same however many cracks there are):
#   * the board is cut ACROSS into Lanes (3 = three bands from the board's top edge to its bottom edge) and every lane is cut ALONG into stretches of
#     Stretch Length (each lane's stretches are slid by their own random amount, so the stretch ends of neighbouring lanes do not line up);
#   * every stretch (one cell = one lane x one stretch of one board) rolls its own random numbers: does it hold a crack (Crack Amount), where across
#     the lane the crack runs, how long it is (between Shortest Share and the whole stretch), where in the stretch it starts, how wide it is;
#   * the crack line wanders sideways by a slow 1D noise along the board (Wobble); its half-width is the full Crack Width in the middle and narrows to
#     a point at both ends; a dot is in the crack when its distance across to the line is below the half-width there;
#   * the lip is a pale band of Lip Width along the side Lip Side says (1 = below the crack, -1 = above it, 0 = both), narrowing like the crack.
# A crack never leaves its cell, so it never crosses a butt joint or another crack's lane: the tile repeats exactly, because everything is read on the
# board's own coordinates (local_x, local_y x piece_height, in tile units), which are the same wherever a board is wrapped round the picture edge.
#
# What it reads: the bundle (piece_id, local_x, local_y, piece_width, piece_height, piece_mask), its own controls and Seed. No other layer.
# Outputs: Mask (crack or lip), Colour (crack colour in the crack, lip colour on the lip), Height (crack sunk, lip a little raised), Roughness (crack
# rougher). Amount scales the chance of a crack in each cell; Amount 0 switches the layer off completely (finish_layer).
# Sizes are TILE units (1.0 = the base tile; at 1254 dots per tile 0.0028 = 3.5 dots).
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'cracks'
GROUP_NAME = 'CRACKS'
DEFAULT_SEED = 61.0
SOFT = 0.0007                # soft width of the crack and lip edges, in tile units (about one dot at 1254)

CONTROLS = [
    Control('crack_amount', 'Crack Amount', 0.6, 0.0, 1.0, 'share of the cells (one lane x one stretch of a board) that hold a crack (0 = none)'),
    Control('lanes', 'Lanes', 3.0, 1.0, 8.0, 'how many crack lanes lie side by side across one board (whole number); at most one crack per lane and stretch'),
    Control('stretch_length', 'Stretch Length', 0.25, 0.02, 1.0, 'length of one stretch along the board, in tile units (0.25 = 313 dots): the longest a crack can be'),
    Control('shortest_share', 'Shortest Share', 0.3, 0.05, 1.0, 'the shortest crack as a share of its stretch (cracks are between this share and the whole stretch long)'),
    Control('crack_width', 'Crack Width', 0.0028, 0.0004, 0.012, 'width of a crack in its middle, in tile units (0.0028 = 3.5 dots); it narrows to a point at both ends'),
    Control('width_variation', 'Width Variation', 0.4, 0.0, 1.0, 'how different the cracks are in width (0 = all the same; 0.4 = plus or minus 40 percent)'),
    Control('lane_middle_share', 'Lane Middle Share', 0.6, 0.0, 1.0, 'how much of the lane width the crack line may sit in (0.6 = the middle 60 percent; 1 = right up to the lane edges)'),
    Control('wobble', 'Wobble', 0.003, 0.0, 0.02, 'how far a crack wanders sideways as it runs along the board, in tile units (0.003 = 4 dots)'),
    Control('wobble_scale', 'Wobble Scale', 25.0, 2.0, 200.0, 'wobbles per tile unit along the board (25 = one wander about every 50 dots)'),
    Control('lip_width', 'Lip Width', 0.0020, 0.0, 0.01, 'width of the pale lip beside the crack, in tile units (0.0020 = 2.5 dots)'),
    Control('lip_side', 'Lip Side', 1.0, -1.0, 1.0, 'which side of the crack gets the pale lip: 1 = below it, -1 = above it, 0 = both sides'),
    Control('lip_strength', 'Lip Strength', 0.8, 0.0, 1.0, 'how strongly the lip colour covers the paint below (0 = no lip)'),
    Control('crack_colour', 'Crack Colour', '#120d0b', kind='colour', text='the near-black inside a crack'),
    Control('lip_colour', 'Lip Colour', '#9c7350', kind='colour', text='the pale fresh wood along a crack'),
    Control('crack_depth', 'Crack Depth', 0.12, 0.0, 0.5, 'how deep a crack sinks the surface (height scale 0..1)'),
    Control('lip_raise', 'Lip Raise', 0.02, 0.0, 0.2, 'how much the lip is raised (height scale 0..1)'),
    Control('crack_roughness', 'Crack Roughness', 0.2, -1.0, 1.0, 'how much rougher the crack is (added to roughness)'),
]
DECLARED_LINKS = []          # CRACKS reads no other layer


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    seed = S('Seed')
    lanes = b.mx(b.floor(b.add(S('Lanes'), 0.5)), 1.0)

    # ---- where am I on the board (tile units); lane and stretch
    across = b.mul(g['local_x'], g['piece_width'])                        # 0 at the board's top edge
    along = b.mul(g['local_y'], g['piece_height'])                        # 0 at the board's left end
    lane_width = b.div(g['piece_width'], lanes)
    lane = b.mn(b.floor(b.mul(g['local_x'], lanes)), b.sub(lanes, 1.0))
    in_lane = b.sub(across, b.mul(lane, lane_width))                      # 0 at the lane's top, lane_width at its bottom
    lane_slide = b.hash4(b.vec(g['piece_id'], lane, seed), 1.0).outputs['Value']
    stretch_place = b.add(b.div(along, b.mx(S('Stretch Length'), 1e-4)), lane_slide)
    stretch = b.floor(stretch_place)
    in_stretch = b.frac(stretch_place)                                     # 0 .. 1 along the stretch

    # ---- one set of random numbers per cell (board, lane, stretch)
    cell_a = b.hash4(b.vec(b.math('MULTIPLY_ADD', lane, 17.0, g['piece_id']), stretch, seed), 2.0)
    cell_b = b.hash4(b.vec(b.math('MULTIPLY_ADD', lane, 17.0, g['piece_id']), stretch, seed), 3.0)
    centre_roll, length_roll, start_roll = b.channels(cell_a.outputs['Color'])
    width_roll, wobble_roll, _spare = b.channels(cell_b.outputs['Color'])
    active = b.lt(cell_a.outputs['Value'], b.mul(S('Crack Amount'), b.mn(S('Amount'), 1.0)))

    # ---- the crack's extent along the stretch, and its pointed shape
    length_share = b.math('MULTIPLY_ADD', length_roll, b.sub(1.0, S('Shortest Share')), S('Shortest Share'))
    start = b.mul(start_roll, b.sub(1.0, length_share))
    progress = b.div(b.sub(in_stretch, start), b.mx(length_share, 1e-4))           # 0 .. 1 inside the crack
    inside = b.mul(b.gt(progress, 0.0), b.lt(progress, 1.0))
    taper = b.power(b.math('MULTIPLY', b.mul(progress, b.sub(1.0, progress)), 4.0, clamp=True), 0.6)

    # ---- the crack line across the lane, with a slow sideways wander along the board
    middle = S('Lane Middle Share')
    line = b.mul(b.math('MULTIPLY_ADD', centre_roll, middle, b.mul(b.sub(1.0, middle), 0.5)), lane_width)
    wander = b.noise(None, 1.0, 1.0, 0.5, 0.0, b.math('MULTIPLY_ADD', along, S('Wobble Scale'), b.mul(wobble_roll, 100.0)), '1D').outputs['Factor']
    line = b.math('MULTIPLY_ADD', b.sub(wander, 0.5), b.mul(S('Wobble'), 2.0), line)
    offset = b.sub(in_lane, line)                                                   # minus = above the crack, plus = below it
    distance = b.absolute(offset)
    width_factor = b.math('MULTIPLY_ADD', b.sub(width_roll, 0.5), b.mul(S('Width Variation'), 2.0), 1.0)
    half = b.mul(b.mul(b.mul(S('Crack Width'), 0.5), width_factor), taper)
    live = b.mul(b.mul(inside, active), g['piece_mask'])
    core = b.mul(b.smoothstep(b.sub(half, distance), 0.0, SOFT), live)
    lip_reach = b.add(half, b.mul(S('Lip Width'), taper))
    side = S('Lip Side')
    on_side = b.mx(b.lt(b.absolute(side), 0.5), b.gt(b.mul(offset, side), 0.0))    # the chosen side (both when Lip Side is near 0)
    lip_band = b.mul(b.mul(b.smoothstep(b.sub(lip_reach, distance), 0.0, SOFT), on_side), live)
    lip = b.mul(b.mul(lip_band, b.sub(1.0, core)), S('Lip Strength'))

    # ---- outputs
    mask = b.mx(core, lip)
    colour = b.mix(S('Lip Colour'), S('Crack Colour'), core)
    height = b.sub(b.mul(lip_band, b.mul(b.sub(1.0, core), S('Lip Raise'))), b.mul(core, S('Crack Depth')))
    roughness = b.mul(core, S('Crack Roughness'))
    b.finish_layer(mask=mask, colour=colour, height=height, roughness=roughness, apply_amount=False)
    return tree
