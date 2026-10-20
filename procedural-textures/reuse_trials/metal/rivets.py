# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# RIVETS: a NEW paint layer with exactly the same sockets as the shared layers (it is built with the shared layer_interface.py, unchanged).
# No shared layer can make a rivet: a rivet is a round domed head on the CENTRE LINE of a bar, at regular places along it, shaded as if lit
# from one side. That is what this layer paints:
#   1. WHERE. Only on bars (base_height above Bar Level Line: the METAL LAYOUT makes bars higher than the plate). A bar piece is upright when
#      it is taller than wide, lying otherwise. Along the bar, the piece's length is split into equal places about Spacing long (a whole
#      number of them, at least one) and one rivet sits in the middle of each place, pushed along a little by its own random number
#      (Spacing Jitter). The rivet never leaves its place, and everything is counted on the piece's own coordinates, so the tile repeats exactly.
#   2. THE HEAD. A disc of Radius, cut into Facet Slices slices round the middle and two rings (an inner flat top and an outer steep ring),
#      each facet ONE flat colour: brighter where the facet faces the light (Light Angle), darker where it faces away (the faceted, painted
#      look of the reference rivets). A dark rim ring round the head (the gap under it), then an uneven rust halo outside it.
#   3. RUST ON THE HEAD. Some facets lean towards the halo's rust colour (Head Rust), from a fine noise on the piece's coordinates.
# Outputs (the fixed interface): Mask (head, rim and halo), Colour, Height (a dome, a lower rim), Roughness (a change).
# It reads only the layout bundle (local_x, local_y, piece_width, piece_height, piece_id, piece_mask, base_height), its controls and its Seed.
# Amount 0 switches it off exactly (finish_layer). Sizes are TILE units (at 1254 dots per tile 0.0155 = 19.5 dots).
import math
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'rivets'
GROUP_NAME = 'RIVETS'
DEFAULT_SEED = 61.0

CONTROLS = [
    Control('spacing', 'Spacing', 0.18, 0.04, 0.6, 'distance between rivets along a bar, in tile units (0.18 = 226 dots; the length of a bar is split into a whole number of places this long)'),
    Control('spacing_jitter', 'Spacing Jitter', 0.25, 0.0, 0.6, 'how far a rivet moves along the bar from the middle of its place, as a share of the place (0 = evenly spaced)'),
    Control('radius', 'Radius', 0.0155, 0.002, 0.04, 'radius of a rivet head, in tile units (0.0155 = 19.5 dots)'),
    Control('bar_level_line', 'Bar Level Line', 0.535, 0.0, 1.0, 'rivets only where the bare relief (base_height) is above this: on bars, not on the plate'),
    Control('light_angle', 'Light Angle', 135.0, 0.0, 360.0, 'where the light comes from, in degrees (0 = from the right, 90 = from the top, 135 = from the upper left)'),
    Control('facet_slices', 'Facet Slices', 8.0, 3.0, 24.0, 'how many flat slices the head is cut into round its middle'),
    Control('inner_ring', 'Inner Ring', 0.45, 0.1, 0.9, 'size of the flatter top of the head, as a share of the radius'),
    Control('shade_contrast', 'Shade Contrast', 1.0, 0.0, 2.0, 'how much brighter the lit facets are than the facets in shade'),
    Control('dark_colour', 'Dark Colour', '#1c1714', kind='colour', text='the colour of a facet facing away from the light'),
    Control('middle_colour', 'Middle Colour', '#3b3532', kind='colour', text='the colour of a facet side-on to the light'),
    Control('light_colour', 'Light Colour', '#7d6a60', kind='colour', text='the colour of a facet facing the light'),
    Control('rim_colour', 'Rim Colour', '#1a1210', kind='colour', text='the dark ring round the head (the shadow gap under it)'),
    Control('rim_width', 'Rim Width', 0.19, 0.0, 0.6, 'width of the dark ring, as a share of the radius'),
    Control('halo_colour', 'Halo Colour', '#5a3422', kind='colour', text='the rust round and on the head'),
    Control('halo_width', 'Halo Width', 0.5, 0.0, 1.5, 'how far the rust halo reaches outside the rim, as a share of the radius'),
    Control('halo_amount', 'Halo Amount', 0.6, 0.0, 1.0, 'how much of the halo ring is rusty (0 = no halo, 1 = a full ring)'),
    Control('head_rust', 'Head Rust', 0.3, 0.0, 1.0, 'how much of the head itself leans towards the rust colour'),
    Control('dome_height', 'Dome Height', 0.08, 0.0, 0.4, 'how high the head stands in the middle (height scale 0..1)'),
    Control('roughness_change', 'Roughness Change', -0.1, -1.0, 1.0, 'how much smoother (minus) or rougher (plus) the head is than the bar'),
]
DECLARED_LINKS = []          # RIVETS reads no other layer
TWO_PI = 2.0 * math.pi
SOFT = 0.0007                # soft width of the disc edges, in tile units (about one dot at 1254)


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    seed = S('Seed')
    width, height = g['piece_width'], g['piece_height']
    upright = b.gt(height, width)

    # ---- 1. along and across the bar (tile units), and the rivet place this dot is in
    along = b.mixf(b.mul(g['local_x'], width), b.mul(g['local_y'], height), upright)
    length = b.mixf(width, height, upright)
    across = b.mixf(b.mul(b.sub(g['local_y'], 0.5), height), b.mul(b.sub(g['local_x'], 0.5), width), upright)
    places = b.mx(b.math('ROUND', b.div(length, b.mx(S('Spacing'), 1e-4))), 1.0)
    place_length = b.div(length, places)
    place_number = b.mn(b.floor(b.div(along, place_length)), b.sub(places, 1.0))
    roll = b.hash4(b.vec(g['piece_id'], place_number, seed), 0.6)
    push = b.mul(b.mul(b.sub(roll.outputs['Value'], 0.5), S('Spacing Jitter')), place_length)
    centre = b.add(b.mul(b.add(place_number, 0.5), place_length), push)
    offset_along = b.sub(along, centre)
    # offsets in the picture: x to the right, y UP (so that the light angle reads the usual way)
    picture_x = b.mixf(offset_along, across, upright)
    picture_y = b.mul(b.mixf(across, offset_along, upright), -1.0)          # local_y runs DOWN the piece
    radius = b.mx(S('Radius'), 1e-4)
    distance = b.div(b.sqrt(b.add(b.mul(picture_x, picture_x), b.mul(picture_y, picture_y))), radius)   # 1 at the edge of the head

    # ---- 2. facets: which slice, which ring; one flat brightness per facet
    angle = b.math('ARCTAN2', picture_y, picture_x)                                                   # -pi .. pi
    slices = b.mx(S('Facet Slices'), 1.0)
    slice_number = b.floor(b.mul(b.div(b.add(angle, math.pi), TWO_PI), slices))
    facet_angle = b.sub(b.mul(b.div(b.add(slice_number, 0.5), slices), TWO_PI), math.pi)
    light = b.mul(S('Light Angle'), math.pi / 180.0)
    facing = b.math('COSINE', b.sub(facet_angle, light))                                             # 1 facing the light, -1 away
    outer = b.gt(distance, S('Inner Ring'))
    tilt = b.mixf(0.35, 0.9, outer)                                                                  # the top is flatter than the outer ring
    shade = b.math('MULTIPLY_ADD', b.mul(b.mul(facing, tilt), S('Shade Contrast')), 0.5, 0.5)        # 0 .. 1
    shade = b.maprange(shade, 0.0, 1.0, 0.0, 1.0, True)
    head_colour = b.mix(b.mix(S('Dark Colour'), S('Middle Colour'), b.smoothstep(shade, 0.0, 0.5)), S('Light Colour'), b.smoothstep(shade, 0.5, 1.0))
    rust_roll = b.hash4(b.vec(g['piece_id'], place_number, b.add(seed, slice_number)), b.add(outer, 1.7))
    head_rusty = b.lt(rust_roll.outputs['Value'], S('Head Rust'))
    head_colour = b.mix(head_colour, S('Halo Colour'), b.mul(head_rusty, 0.7))

    # ---- 3. rim and halo
    rim_outer = b.add(1.0, S('Rim Width'))
    soft = b.div(SOFT, radius)
    head = b.smoothstep(b.sub(1.0, distance), b.mul(soft, -1.0), soft)
    rim = b.mul(b.smoothstep(b.sub(rim_outer, distance), b.mul(soft, -1.0), soft), b.sub(1.0, head))
    halo_reach = b.add(rim_outer, S('Halo Width'))
    halo_ring = b.mul(b.smoothstep(b.sub(halo_reach, distance), b.mul(soft, -1.0), soft), b.sub(1.0, b.add(head, rim)))
    halo_noise = b.noise(b.vec(b.div(picture_x, radius), b.div(picture_y, radius), b.add(b.mul(g['piece_id'], 50.0), b.add(place_number, seed))),
                         1.3, 2.0, 0.6).outputs['Factor']
    halo_on = b.lt(halo_noise, b.math('MULTIPLY_ADD', S('Halo Amount'), 0.45, 0.28))                    # noise sits round 0.5: Amount 0 = none, 1 = nearly all
    halo = b.mul(halo_ring, halo_on)

    # ---- 4. only on bars, only on the piece
    on_bar = b.mul(b.gt(g['base_height'], S('Bar Level Line')), g['piece_mask'])
    head, rim, halo = b.mul(head, on_bar), b.mul(rim, on_bar), b.mul(halo, on_bar)
    colour = b.mix(b.mix(S('Halo Colour'), S('Rim Colour'), b.gt(rim, 0.5)), head_colour, b.gt(head, 0.5))
    mask = b.mx(b.mx(head, rim), halo)
    dome = b.mul(b.sqrt(b.mx(b.sub(1.0, b.mul(distance, distance)), 0.0)), S('Dome Height'))
    height_change = b.sub(b.mul(head, dome), b.mul(rim, b.mul(S('Dome Height'), 0.3)))
    roughness = b.add(b.mul(head, S('Roughness Change')), b.mul(halo, 0.1))
    b.finish_layer(mask=mask, colour=colour, height=height_change, roughness=roughness)
    return tree
