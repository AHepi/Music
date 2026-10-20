# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# KNOTS (new, OPTIONAL layer for the wood trial): a few knots on the boards: a dark core, rings of darker and lighter wood around it, and a faint
# halo of rings beyond. No shared layer makes rings. Same sockets as the shared layers (layer_interface.make_layer_group from the frozen snapshot).
#
# How a knot is placed (no loop over knots): every board is cut ALONG into places of Knot Spacing (slid by a random amount per board); each place
# rolls its own random numbers: does it hold a knot (Knot Amount), where along the place and where across the board its middle is, how big it is.
# A knot is an oval (Knot Stretch times longer along the board than across it) that always stays inside its place, so it never crosses a butt joint
# and the tile repeats exactly (everything is read on the board's own coordinates). Its outline is roughened by a little noise.
#   inside the core (Core Share of the radius)    -> Core Colour
#   rings out to the radius                       -> Ring Count bands, dark (Ring Dark) and light (Ring Light) in turn
#   halo from the radius out to Halo Reach x radius -> the same bands, fading out (grain bending round the knot)
# What it reads: the bundle (piece_id, local_x, local_y, piece_width, piece_height, piece_mask), its own controls and Seed. No other layer.
# Outputs: Mask, Colour, Height (core sunk, dark rings a little low, light rings a little high), Roughness (core rougher).
# Amount scales the chance of a knot in each place; Amount 0 switches the layer off completely (finish_layer).
# Sizes are TILE units (1.0 = the base tile; at 1254 dots per tile 0.035 = 44 dots).
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'knots'
GROUP_NAME = 'KNOTS'
DEFAULT_SEED = 71.0
SOFT = 0.04                  # soft width of the ring edges, in "radius" units

CONTROLS = [
    Control('knot_amount', 'Knot Amount', 0.4, 0.0, 1.0, 'share of the knot places that hold a knot (0 = no knots)'),
    Control('knot_spacing', 'Knot Spacing', 0.5, 0.1, 1.0, 'length of one knot place along a board, in tile units (0.5 = two places per board per tile)'),
    Control('knot_size', 'Knot Size', 0.035, 0.005, 0.1, 'typical radius of a knot across the board, in tile units (0.035 = 44 dots); single knots are 0.6 to 1.4 times this'),
    Control('knot_stretch', 'Knot Stretch', 1.4, 0.2, 3.0, 'how many times longer than wide a knot is along the board, in the board\'s own along-units (with the turn\'s Grain Stretch G the knot looks Knot Stretch x G times longer than wide)'),
    Control('core_share', 'Core Share', 0.2, 0.0, 0.6, 'the dark core as a share of the knot radius'),
    Control('ring_count', 'Ring Count', 4.0, 1.0, 12.0, 'how many dark-and-light ring pairs lie between the core and the knot edge'),
    Control('halo_reach', 'Halo Reach', 1.7, 1.0, 3.0, 'how far the fading rings reach beyond the knot, as a multiple of its radius (1 = no halo)'),
    Control('ring_strength', 'Ring Strength', 0.8, 0.0, 1.0, 'how strongly the rings cover the paint below'),
    Control('roughen', 'Roughen', 0.12, 0.0, 0.5, 'how uneven the rings are (0 = perfect ovals)'),
    Control('core_colour', 'Core Colour', '#140e0c', kind='colour', text='the near-black middle of a knot'),
    Control('ring_dark', 'Ring Dark', '#3b271c', kind='colour', text='the darker rings'),
    Control('ring_light', 'Ring Light', '#8a6446', kind='colour', text='the lighter rings'),
    Control('core_depth', 'Core Depth', 0.08, 0.0, 0.4, 'how deep the core sinks the surface (height scale 0..1)'),
    Control('ring_relief', 'Ring Relief', 0.015, 0.0, 0.1, 'how much the light rings stand above the dark rings (height scale 0..1)'),
]
DECLARED_LINKS = []          # KNOTS reads no other layer


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    seed = S('Seed')
    spacing = b.mx(S('Knot Spacing'), 1e-3)
    across = b.mul(g['local_x'], g['piece_width'])
    along = b.mul(g['local_y'], g['piece_height'])
    board_slide = b.hash4(b.vec(g['piece_id'], seed, 0.5), 1.0).outputs['Value']
    place_value = b.add(b.div(along, spacing), board_slide)
    place = b.floor(place_value)
    in_place = b.mul(b.frac(place_value), spacing)                               # tile units from the start of the place
    roll = b.hash4(b.vec(g['piece_id'], place, seed), 2.0)
    along_roll, across_roll, size_roll = b.channels(roll.outputs['Color'])
    has_knot = b.lt(roll.outputs['Value'], b.mul(S('Knot Amount'), b.mn(S('Amount'), 1.0)))

    # the radius across the board, kept inside the board and inside the place
    radius = b.mul(S('Knot Size'), b.math('MULTIPLY_ADD', size_roll, 0.8, 0.6))
    radius = b.mn(radius, b.mul(g['piece_width'], 0.3))
    radius = b.mn(radius, b.div(b.mul(spacing, 0.22), S('Knot Stretch')))
    centre_along = b.mul(b.math('MULTIPLY_ADD', along_roll, 0.4, 0.3), spacing)
    centre_across = b.mul(b.math('MULTIPLY_ADD', across_roll, 0.4, 0.3), g['piece_width'])
    dx = b.div(b.sub(in_place, centre_along), b.mul(radius, S('Knot Stretch')))
    dy = b.div(b.sub(across, centre_across), radius)
    distance = b.sqrt(b.add(b.mul(dx, dx), b.mul(dy, dy)))                      # 1 at the knot edge
    bumps = b.noise(b.vec(b.mul(dx, 2.5), b.mul(dy, 2.5), b.mul(size_roll, 50.0)), 1.0, 2.0, 0.5).outputs['Factor']
    distance = b.math('MULTIPLY_ADD', b.sub(bumps, 0.5), b.mul(S('Roughen'), 2.0), distance)

    # zones: core, rings, halo
    core = b.smoothstep(b.sub(S('Core Share'), distance), 0.0, SOFT)
    ring_phase = b.frac(b.mul(distance, S('Ring Count')))
    dark_ring = b.smoothstep(b.sub(0.5, ring_phase), 0.0, b.mul(SOFT, S('Ring Count')))
    halo_fade = b.maprange(distance, 1.0, b.mx(S('Halo Reach'), 1.001), 1.0, 0.0, True)
    ring_zone = b.mul(b.gt(distance, S('Core Share')), halo_fade)                # 1 inside the knot, fading to 0 at the halo's end
    live = b.mul(has_knot, g['piece_mask'])
    ring_cover = b.mul(b.mul(ring_zone, S('Ring Strength')), b.math('MULTIPLY_ADD', dark_ring, 0.5, 0.5))   # dark rings cover more than light ones
    mask = b.mul(b.mx(core, ring_cover), live)
    colour = b.mix(b.mix(S('Ring Light'), S('Ring Dark'), dark_ring), S('Core Colour'), core)
    relief = b.mul(b.mul(b.sub(0.5, dark_ring), b.mul(S('Ring Relief'), 2.0)), ring_zone)
    height = b.mul(b.sub(relief, b.mul(core, S('Core Depth'))), live)
    roughness = b.mul(b.mul(core, 0.15), live)
    b.finish_layer(mask=mask, colour=colour, height=height, roughness=roughness, apply_amount=False)
    return tree
