# MASK TEST COPY (20 October 2026): this is a copy of the slate DAMAGE layer with one addition, a STAMP MODE for the flaked edges (FLAKES, kind 1 below).
# Setting 'damage.mask_mode' chooses where flakes are: 'nodes' (the old node-made flakes, exactly the old picture), 'stamps' (chips cut from generated
# pictures and sat on the lower edge and lower corners of each slate) or 'both' (node flakes times stamp chips). Pits, scratches, cracks, notches and
# corner breaks stay node-made in every mode. Notes: ../../notes - generated mask stamps test.md and stamps.py.
#
# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# DAMAGE is where the slates are hurt. It paints (in this order, later ones on top):
#   1. FLAKES   pale and tan patches where the slate has flaked off along its edges, mostly the lower edge and the lower corners
#               (the reference has this: pale cream next to the edge, tan above it, a little darker brown at the tips).
#   2. PITS     small round pits scattered over the slate face (tan ring, dark middle).
#   3. SCRATCHES thin pale lines a few dots wide, short, in any direction.
#   4. CRACKS   thin dark lines that run from an edge, mostly downslope, some across, getting thinner towards the tip.
#   5. NOTCHES  small dark bites out of the edge (the black joint shows through), with a pale fresh-break rim.
#   6. CORNER BREAKS a lower corner broken off: a dark chunk (the black below) with a pale rim.
# Every kind SINKS the surface where material is gone (negative Height) and makes it rougher; the colour is flat painted patches with
# hard edges (the look the whole slate recipe aims for).
#
# What it reads: ONLY the layout bundle (where the slate edges are, how far from an edge, where on the slate) and its own controls and
# seed. It never looks at another layer. Its Mask ("where damage shows") is offered to MOSS through the declared link 'Damage Mask'
# (see ../interface/interface.md, section 5): moss may keep away from fresh damage or gather beside it.
#
# How the flaked edge is made (the main idea, in a concrete example): at every dot we ask "how far is this dot from the slate edge?"
# (edge_distance, in tile units) and "how far in is the flaking allowed to reach HERE?" (the reach). The reach is big at the bottom
# edge and bottom corners, small at the sides, tiny at the top, and different for every slate (some slates are barely touched, some
# are badly flaked). The reach is multiplied by a seamless noise (a different noise for every slate): where the noise is high the
# flake reaches far in (a tooth of flaking), where it is low it does not show at all (a clean stretch of edge). A dot is flaked when
# its edge distance is smaller than the reach there. Two noises are blended: one stretched UP-DOWN (so the flakes are teeth that
# point up from the edge, like the reference) and one round (so there are loose islands above the edge as well).
#
# Sizes are TILE UNITS (1.0 = the base tile; at 1254 dots per tile 0.0064 = 8 dots), so the look is the same at any picture size.
# Random numbers: one set per slate from its piece_id (hash), and seamless noise whose W coordinate is shifted by piece_id, so every
# slate has its own damage and the tile still repeats exactly. The layer's Seed changes only this layer's pattern.
# The Amount control (0..1) is used smartly: it scales how MUCH damage there is (the threshold and the depth of the flakes, the chance of a
# crack, a scratch, a pit, a corner break), so the paint stays crisp at every Amount; 0 switches the layer off completely.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layer_interface as li  # noqa: E402
from layer_interface import Control  # noqa: E402
import stamps  # noqa: E402

LAYER_KEY = 'damage'
GROUP_NAME = 'DAMAGE'
DEFAULT_SEED = 21.0

# Colours were chosen by looking at the reference once (the tan and pale flakes there measure about #675a4a to #887b6b, the palest
# accents #8e8c84; the near-black is the joint colour). Nothing is copied patch by patch.
CONTROLS = [
    # ---- flakes along the edges
    Control('chip_amount', 'Chip Amount', 0.45, 0.0, 1.0, 'how much of the slate edges is flaked (0 = none; 0.45 = patches along about a third of the lower edges; 1 = almost all of it)'),
    Control('chip_depth', 'Chip Depth', 0.025, 0.0, 0.08, 'how far a flake reaches in from the lower edge, in tile units (0.025 = 31 dots); the sides reach less (Side Share)'),
    Control('chip_frequency', 'Chip Frequency', 62.0, 10.0, 400.0, 'how many flakes (noise features) fit across one base tile: 62 = a flake tooth about 20 dots wide (1254 / 62); more = smaller flakes'),
    Control('chip_clustering', 'Chip Clustering', 0.8, 0.0, 3.0, 'how strongly flakes gather into stretches of one edge with clean stretches between (0 = spread evenly along the edge; 0.8 = clusters; 3 = a few big patches)'),
    Control('chip_breakup', 'Chip Breakup', 0.6, 0.0, 2.0, 'how broken up the flaked patches are: 0 = solid smooth patches; 1 = ragged, with holes and loose flecks around them'),
    Control('side_share', 'Side Share', 0.12, 0.0, 1.0, 'how far flakes reach in along the sides, as a share of the lower edge (the top edge gets less still)'),
    Control('corner_gain', 'Corner Gain', 1.0, 0.0, 4.0, 'extra flaking at the two lower corners (1 = twice as deep right at the corner)'),
    Control('slate_variation', 'Slate Variation', 0.6, 0.0, 1.0, 'how different the slates are from each other (0 = every slate equally damaged; 1 = some nearly clean, some badly hurt)'),
    # ---- STAMP MODE (mask test): only used when the setting 'damage.mask_mode' is 'stamps' or 'both'; 'damage.stamp_atlas' = the atlas JSON file
    Control('stamp_amount', 'Stamp Amount', 0.8, 0.0, 3.0, 'stamp mode: how likely each chip slot is used on a slate (multiplied by Chip Amount and by how damaged the slate is)'),
    Control('stamp_width', 'Stamp Width', 0.045, 0.01, 0.2, 'stamp mode: width of an average chip, in tile units (0.045 = 56 dots); each chip is 0.7 to 1.5 times this'),
    Control('stamp_turn', 'Stamp Turn', 8.0, 0.0, 90.0, 'stamp mode: the largest turn of a chip either way, in degrees (small: the teeth should keep pointing up)'),
    Control('stamp_overhang', 'Stamp Overhang', 0.35, 0.0, 0.8, 'stamp mode: how much of a chip lies below the slate edge (cut off there), as a share of the chip height'),
    Control('stamp_softness', 'Stamp Edge Softness', 0.12, 0.01, 0.5, 'stamp mode: softness of the chip edge (0.01 = hard)'),
    # ---- notches and corner breaks
    Control('notch_amount', 'Notch Amount', 0.30, 0.0, 1.0, 'how many small dark bites there are in the slate edges (0 = none)'),
    Control('notch_depth', 'Notch Depth', 0.010, 0.0, 0.04, 'deepest bite into an edge, in tile units (0.010 = 13 dots)'),
    Control('corner_break_amount', 'Corner Break Amount', 0.08, 0.0, 1.0, 'chance that a lower corner of a slate has broken off (only the two lower corners can break: the upper ones lie under the row above)'),
    Control('corner_break_size', 'Corner Break Size', 0.022, 0.0, 0.08, 'size of a broken corner along each edge, in tile units (0.022 = 28 dots)'),
    # ---- cracks and scratches
    Control('crack_amount', 'Crack Amount', 0.35, 0.0, 1.0, 'chance that a slate has a crack, per crack slot (each slate has Crack Slots slots, default 1; 0 = no cracks)'),
    Control('crack_length', 'Crack Length', 0.07, 0.0, 0.2, 'average length of a crack, in tile units (0.07 = 88 dots, about half a slate height)'),
    Control('crack_width', 'Crack Width', 0.0028, 0.0004, 0.01, 'width of a crack where it starts at the edge, in tile units (0.0028 = 3.5 dots); it narrows to a point'),
    Control('crack_across_share', 'Crack Across Share', 0.25, 0.0, 1.0, 'share of cracks that run across the slate from a side edge instead of down it (0 = all run downslope)'),
    Control('scratch_amount', 'Scratch Amount', 0.18, 0.0, 1.0, 'chance that a slate has a scratch, per scratch slot (each slate has Scratch Slots slots)'),
    Control('scratch_length', 'Scratch Length', 0.03, 0.0, 0.2, 'average length of a scratch, in tile units (0.03 = 38 dots)'),
    # ---- pits
    Control('pit_amount', 'Pit Amount', 0.06, 0.0, 0.5, 'share of the pit places that really hold a pit (0.06 gives about 200 pits per tile at the default Pit Low Bias)'),
    Control('pit_size', 'Pit Size', 0.0034, 0.0005, 0.005, 'typical pit radius in tile units (0.0034 = 4 dots)'),
    Control('pit_low_bias', 'Pit Low Bias', 0.6, 0.0, 1.0, 'how much the pits gather near the lower edge of the slates (0 = evenly over the slate; 1 = only near the lower edge, like the flakes)'),
    # ---- colours
    Control('break_colour', 'Break Colour', '#7c6f5d', kind='colour', text='the tan of weathered flaked slate and the lichen on it (the middle tone of a flake)'),
    Control('break_colour_light', 'Break Colour Light', '#8f8d85', kind='colour', text='the pale of freshly broken slate: right at the edge of a flake, in scratches and in the rim of a bite'),
    Control('break_colour_dark', 'Break Colour Dark', '#5a4f43', kind='colour', text='the darker tan-brown at the far tip of a flake and in the middle of a pit'),
    Control('hole_colour', 'Hole Colour', '#0b0c0e', kind='colour', text='the black seen where a piece is missing (corner breaks, bites) and inside cracks'),
    # ---- relief and roughness
    Control('sink_depth', 'Sink Depth', 1.0, 0.0, 4.0, 'multiplies how deep everything is sunk (1 = as tuned: a flake about -0.05, a crack -0.12, a broken corner -0.32 of the height scale)'),
    Control('roughness_gain', 'Roughness Gain', 1.0, 0.0, 4.0, 'multiplies how much rougher damaged places are (1 = flakes +0.12, cracks and pits +0.2)'),
    # ---- how many places each slate has for cracks and scratches (changes the number of nodes, so it is read while building)
    Control('crack_slots', 'Crack Slots', 1, 0, 6, 'how many cracks a slate can have at most', build_time=True),
    Control('scratch_slots', 'Scratch Slots', 2, 0, 8, 'how many scratches a slate can have at most', build_time=True),
]
DECLARED_LINKS = []          # DAMAGE reads no other layer; MOSS reads DAMAGE's Mask

TWO_PI = 6.2831853
SOFT = 0.0008                # width of the soft edge of every damage patch, in tile units (0.0008 = one dot at 1254): painted look = hard edges
PIT_PLACES = 80              # pit places across one base tile (a jittered grid; a pit never crosses the edge of its place, so the tile repeats exactly)
MIN_FLAKE = 0.0016            # the shallowest flake that is drawn, in tile units (0.0016 = 2 dots at 1254)
CORNER_ZONE = 0.05           # how far from a lower corner the extra corner flaking fades out, in tile units


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    crack_slots, scratch_slots = int(values['crack_slots']), int(values['scratch_slots'])
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    tiles = S('Tile Count')
    seed = S('Seed')
    amt = b.mn(S('Amount'), 1.0)
    piece_mask = g['piece_mask']
    edge_distance = g['edge_distance']
    width, height = g['piece_width'], g['piece_height']

    # ------------------------------------------------------------------------------------------------ helpers
    # the seamless noise is read from a "donut" (the tile coordinate turned into circles, so the noise repeats exactly). The four circle
    # numbers (cos and sin of u and of v) are worked out ONCE here and shared by every noise below: that keeps the layer cheap.
    u, v, _ = b.xyz(S('Vector'))
    turns_u, turns_v = b.mul(u, TWO_PI), b.mul(v, TWO_PI)
    cos_u, sin_u = b.math('COSINE', turns_u), b.math('SINE', turns_u)
    cos_v, sin_v = b.math('COSINE', turns_v), b.math('SINE', turns_v)

    def piece_noise(scale_u, scale_v, detail, roughness, offset):
        """Seamless noise (0..1) that is different on every slate and changes with this layer's Seed. scale_u / scale_v = how many noise features
        fit across the whole picture left-right / up-down (different numbers stretch the noise)."""
        shift = b.math('MULTIPLY_ADD', g['piece_id'], 500.0, b.add(b.mul(seed, 7.3), offset))
        radius_u, radius_v = b.mul(scale_u, 1.0 / TWO_PI), b.mul(scale_v, 1.0 / TWO_PI)
        position = b.vec(b.mul(cos_u, radius_u), b.mul(sin_u, radius_u), b.mul(cos_v, radius_v))
        node = b.noise(position, 1.0, detail, roughness, 0.0, b.math('MULTIPLY_ADD', sin_v, radius_v, shift), '4D', 'FBM', 2.0)
        return b.maprange(node.outputs['Factor'], 0.3, 0.7, 0.0, 1.0, True)

    def slate_random(slot, w=0.0):
        """Four random numbers for this slate: (value, red, green, blue). Same on every dot of the slate; new with the Seed."""
        node = b.hash4(b.vec(g['piece_id'], seed, float(slot)), w)
        red, green, blue = b.channels(node.outputs['Color'])
        return node.outputs['Value'], red, green, blue

    def hard(value):
        """1 where `value` (a distance in tile units) is above 0, with a one-dot soft edge."""
        return b.smoothstep(value, 0.0, SOFT)

    def either(a, c):
        return b.mx(a, c)

    # ------------------------------------------------------------------------------------------------ where am I on the slate (tile units)
    x_from_left = b.mul(g['local_x'], width)
    x_from_right = b.mul(b.sub(1.0, g['local_x']), width)
    y_from_top = b.mul(g['local_y'], height)
    y_from_bottom = b.mul(b.sub(1.0, g['local_y']), height)
    side_near = b.mn(x_from_left, x_from_right)

    # ------------------------------------------------------------------------------------------------ per-slate random numbers
    slate_a, rand_b, rand_c, _spare = slate_random(1, 0.0)        # slate_a: how damaged this slate is; rand_b, rand_c: do the two lower corners break?
    slate_b, rand_f, rand_g, _spare = slate_random(2, 0.5)        # slate_b: pit factor; rand_f, rand_g: size of each broken corner

    def slate_factor(random_value, low=0.25, spread=1.5):
        """How much more or less than average this slate gets (Slate Variation 0 = 1 for everyone)."""
        varied = b.math('MULTIPLY_ADD', b.power(random_value, 1.5), spread, low)
        return b.mixf(1.0, varied, S('Slate Variation'))

    damage_factor = slate_factor(slate_a)

    # ------------------------------------------------------------------------------------------------ 1. FLAKES along the edges
    bottom_weight = b.smoothstep(g['local_y'], 0.45, 0.97)                                    # 1 near the lower edge
    top_damp = b.math('MULTIPLY_ADD', b.smoothstep(g['local_y'], 0.03, 0.40), 0.7, 0.3)      # 0.3 right at the upper edge, 1 lower down
    side_share = S('Side Share')
    region = b.mul(b.math('MULTIPLY_ADD', bottom_weight, b.sub(1.0, side_share), side_share), top_damp)
    corner_distance = b.sqrt(b.add(b.mul(side_near, side_near), b.mul(y_from_bottom, y_from_bottom)))
    corner_near = b.sub(1.0, b.smoothstep(corner_distance, 0.0, CORNER_ZONE))
    reach = b.mul(b.mul(S('Chip Depth'), region), b.math('MULTIPLY_ADD', corner_near, S('Corner Gain'), 1.0))
    reach = b.mul(b.mul(reach, damage_factor), amt)                                           # Amount also scales how deep the flakes reach: Amount 0.5 = half as deep and fewer

    feature_count = b.mul(tiles, S('Chip Frequency'))
    tall_noise = piece_noise(feature_count, b.mul(feature_count, 0.55), 2.0, 0.55, 11.0)      # teeth that point up from the edge
    round_noise = piece_noise(b.mul(feature_count, 0.7), b.mul(feature_count, 0.7), 3.0, 0.5, 23.0)    # loose islands
    cluster_noise = piece_noise(b.mul(tiles, 9.0), b.mul(tiles, 9.0), 0.0, 0.5, 37.0)       # flakes come in clusters along an edge
    teeth_noise = b.math('MULTIPLY_ADD', tall_noise, 0.6, b.mul(round_noise, 0.4))
    flake_noise = b.mixf(round_noise, teeth_noise, bottom_weight)                              # up-down teeth only near the lower edge (they would run as long strips along a side edge)
    flake_noise = b.math('MULTIPLY_ADD', b.sub(cluster_noise, 0.5), S('Chip Clustering'), flake_noise)
    threshold = b.sub(0.80, b.mul(b.mul(S('Chip Amount'), amt), 0.45))                         # more Chip Amount: lower threshold: more flaking
    excess = b.mx(b.sub(flake_noise, threshold), 0.0)
    flake_reach = b.mul(excess, b.div(reach, 0.45))                                            # how far in the flake reaches at this dot
    flake_reach = b.mx(b.sub(flake_reach, MIN_FLAKE), 0.0)                                      # flakes shallower than about 2 dots do not show (they would be thin lines along every edge)
    breakup_noise = piece_noise(b.mul(tiles, 110.0), b.mul(tiles, 110.0), 1.0, 0.5, 71.0)               # fine noise: punches holes in flakes, makes loose flecks, and cuts the notches
    near_flake = b.smoothstep(flake_reach, 0.0, 0.008)                                                 # only next to a flake that is really there (not along a clean edge)
    breakup = b.mul(b.mul(b.sub(breakup_noise, 0.5), b.mul(S('Chip Breakup'), 0.02)), near_flake)   # plus or minus 0.01 tile (12 dots) at Chip Breakup 1
    flake = hard(b.add(b.sub(flake_reach, edge_distance), breakup))

    depth_ratio = b.div(edge_distance, b.mx(flake_reach, 1e-5))                                # 0 at the edge, 1 at the far tip of the flake

    # ---- STAMP MODE (mask test). A build-time setting; 'nodes' builds exactly the old graph. The chips are stamps sat on the LOWER edge: four along the
    # lower edge and one at each lower corner. A dot's height above the edge is its edge_distance (so the stamps follow the slate's real, chipped edge).
    mask_mode = str(parameters.get('damage.mask_mode', 'nodes'))
    if mask_mode in ('stamps', 'both'):
        atlas = stamps.load_atlas(str(parameters['damage.stamp_atlas']))
        turn_radians = b.mul(S('Stamp Turn'), 3.14159265 / 180.0)
        stamp_masks = []
        chip_height_scale = b.mul(S('Stamp Width'), atlas.aspect)
        # Height above the lower edge: edge_distance follows the slate's real chipped, sloping edge, but it also measures the distance to a SIDE edge, and
        # along a side edge that would smear the stamp up the side (first try: L-shaped chips). So edge_distance is used only where the side is not the
        # nearest edge; near the sides the straight distance from the nominal lower edge is used instead.
        bottom_is_nearest = b.lt(edge_distance, b.sub(side_near, 0.003))
        height_above_edge = b.mixf(y_from_bottom, edge_distance, bottom_is_nearest)
        y_in_stamp = b.sub(0.0, height_above_edge)                                       # up from the lower edge = minus 'down'
        near_lower_edge = b.mul(b.gt(g['local_y'], 0.5), b.lt(y_from_bottom, 0.05))      # only the lower part of the slate: not along the sides or the top
        for slot, kind in enumerate(['bottom', 'bottom', 'bottom', 'bottom', 'corner_left', 'corner_right']):
            r = stamps.slot_randoms(b, g['piece_id'], seed, 300 + slot)
            size = b.mul(S('Stamp Width'), b.math('MULTIPLY_ADD', r['size'], 0.8, 0.7))
            if kind == 'bottom':
                centre_x = b.mul(b.math('MULTIPLY_ADD', r['along'], 0.94, 0.03), width)
                gain = 1.0
            elif kind == 'corner_left':
                centre_x = b.mul(b.math('MULTIPLY_ADD', r['along'], 0.04, 0.0), 1.0)
                gain = b.math('MULTIPLY_ADD', S('Corner Gain'), 0.5, 0.5)
            else:
                centre_x = b.sub(width, b.mul(b.math('MULTIPLY_ADD', r['along'], 0.04, 0.0), 1.0))
                gain = b.math('MULTIPLY_ADD', S('Corner Gain'), 0.5, 0.5)
            centre_y = b.mul(b.sub(S('Stamp Overhang'), 0.5), b.mul(size, atlas.aspect))     # the chip sits on the lower edge, its lowest part below it
            chance = b.mn(b.mul(b.mul(b.mul(S('Stamp Amount'), b.mul(S('Chip Amount'), amt)), damage_factor), gain), 1.0)
            active = b.lt(r['chance'], chance)
            turn = b.mul(b.sub(r['turn'], 0.5), b.mul(turn_radians, 2.0))
            mirror = b.sub(1.0, b.mul(b.gt(r['mirror'], 0.5), 2.0))
            mask, _depth_here = stamps.place(b, atlas, x_from_left, y_in_stamp, centre_x, centre_y, size, turn, mirror, r['pick'], active)
            stamp_masks.append(mask)
        union = stamp_masks[0]
        for extra_mask in stamp_masks[1:]:
            union = b.mx(union, extra_mask)
        chip_mask = b.mul(stamps.harden(b, union, S('Stamp Edge Softness')), near_lower_edge)
        if mask_mode == 'stamps':
            flake = b.mul(chip_mask, piece_mask)
            depth_ratio = b.div(height_above_edge, b.mul(chip_height_scale, 0.8))             # 0 at the edge, 1 about the top of a chip
        else:
            flake = b.mul(flake, chip_mask)
    patch_noise = round_noise                                                                   # the same round noise also decides which tone a part of a flake gets
    tone = b.math('MULTIPLY_ADD', b.sub(patch_noise, 0.5), 0.7, depth_ratio)
    flake_colour = b.mix(b.mix(S('Break Colour Light'), S('Break Colour'), b.gt(tone, 0.28)), S('Break Colour Dark'), b.gt(tone, 0.70))

    # ------------------------------------------------------------------------------------------------ 2. PITS (jittered grid, one pit place per cell)
    cells = b.mul(tiles, float(PIT_PLACES))
    grid_u, grid_v = b.mul(u, cells), b.mul(v, cells)
    cell_i, cell_j = b.mod(b.floor(grid_u), cells), b.mod(b.floor(grid_v), cells)       # whole numbers, wrapped: cell `cells` is cell 0 again, so the pits repeat exactly
    in_cell_u, in_cell_v = b.frac(grid_u), b.frac(grid_v)
    pit_hash = b.hash4(b.vec(cell_i, cell_j, b.mul(seed, 1.3)), 0.2)
    pit_chance, pit_x, pit_y = b.channels(pit_hash.outputs['Color'])
    pit_size_rand = pit_hash.outputs['Value']
    pit_radius = b.mn(b.mul(b.mul(S('Pit Size'), b.math('MULTIPLY_ADD', pit_size_rand, 1.0, 0.5)), float(PIT_PLACES)), 0.4)   # in cell units (PIT_PLACES cells per BASE tile), at most 0.4 so it stays inside its cell
    centre_u = b.math('MULTIPLY_ADD', b.sub(1.0, b.mul(pit_radius, 2.0)), pit_x, pit_radius)
    centre_v = b.math('MULTIPLY_ADD', b.sub(1.0, b.mul(pit_radius, 2.0)), pit_y, pit_radius)
    du, dv = b.sub(in_cell_u, centre_u), b.sub(in_cell_v, centre_v)
    pit_distance = b.sqrt(b.add(b.mul(du, du), b.mul(dv, dv)))
    soft_in_cells = SOFT * PIT_PLACES
    pit_low = b.math('MULTIPLY_ADD', bottom_weight, S('Pit Low Bias'), b.sub(1.0, S('Pit Low Bias')))        # 1 at the lower edge, 1 - bias higher up
    pit_chance_here = b.mul(b.mul(b.mul(S('Pit Amount'), amt), slate_factor(slate_b, 0.2, 1.6)), pit_low)
    has_pit = b.lt(pit_chance, pit_chance_here)
    pit_ring = b.mul(b.smoothstep(b.sub(pit_radius, pit_distance), 0.0, soft_in_cells), has_pit)
    pit_core = b.mul(b.smoothstep(b.sub(b.mul(pit_radius, 0.5), pit_distance), 0.0, soft_in_cells), pit_ring)
    pit_colour = b.mix(S('Break Colour'), S('Break Colour Dark'), pit_core)

    # ------------------------------------------------------------------------------------------------ shared wobble for cracks, scratches, corner breaks
    wobble = piece_noise(b.mul(tiles, 45.0), b.mul(tiles, 45.0), 2.0, 0.5, 53.0)
    wobble_shift = b.mul(b.sub(wobble, 0.5), 2.0)                                              # -1 .. +1

    # ------------------------------------------------------------------------------------------------ 3. SCRATCHES (short thin lines, any direction)
    scratch_mask = None
    for k in range(scratch_slots):
        pick, across_pos, down_pos, angle_rand = slate_random(50 + k, 0.3)
        length_rand, width_rand, _unused_a, _unused_b = slate_random(70 + k, 0.7)
        active = b.lt(pick, b.mul(S('Scratch Amount'), amt))
        centre_x = b.mul(b.math('MULTIPLY_ADD', across_pos, 0.8, 0.1), width)
        centre_y = b.mul(b.math('MULTIPLY_ADD', down_pos, 0.8, 0.1), height)
        angle = b.mul(angle_rand, 3.14159)
        cos_a, sin_a = b.math('COSINE', angle), b.math('SINE', angle)
        dx, dy = b.sub(x_from_left, centre_x), b.sub(y_from_top, centre_y)
        along = b.add(b.mul(dx, cos_a), b.mul(dy, sin_a))
        across = b.add(b.mul(b.sub(0.0, dx), sin_a), b.mul(dy, cos_a))
        across = b.add(across, b.mul(wobble_shift, 0.0012))
        half_length = b.mul(b.mul(S('Scratch Length'), 0.5), b.math('MULTIPLY_ADD', length_rand, 1.0, 0.5))
        half_width = b.mul(0.0007, b.math('MULTIPLY_ADD', width_rand, 0.8, 0.6))
        pinch = b.maprange(b.sub(half_length, b.absolute(along)), 0.0, b.mx(b.mul(half_length, 0.5), 1e-5), 0.0, 1.0, True)
        scratch = b.mul(hard(b.sub(b.mul(half_width, pinch), b.absolute(across))), active)
        scratch_mask = scratch if scratch_mask is None else either(scratch_mask, scratch)
    if scratch_mask is None:
        scratch_mask = b.mul(g['piece_mask'], 0.0)

    # ------------------------------------------------------------------------------------------------ 4. CRACKS (from an edge, mostly downslope)
    crack_core_mask, crack_lip_mask = None, None
    for k in range(crack_slots):
        pick, across_flag, position, lean_rand = slate_random(10 + k, 0.2)
        length_rand, far_flag, _spare_a, _spare_b = slate_random(30 + k, 0.7)
        active = b.lt(pick, b.mul(S('Crack Amount'), amt))
        is_across = b.lt(across_flag, S('Crack Across Share'))
        start_far = b.gt(far_flag, 0.5)
        run_down = b.mixf(y_from_bottom, y_from_top, start_far)                    # distance from the edge the crack starts at (downslope crack)
        run_across = b.mixf(x_from_left, x_from_right, start_far)                  # the same for a crack that runs in from a side edge
        run = b.mixf(run_down, run_across, is_across)
        offset = b.mixf(x_from_left, y_from_bottom, is_across)                     # sideways position of this dot relative to the crack's line
        offset_size = b.mixf(width, height, is_across)
        extent = b.mixf(height, width, is_across)
        line_start = b.mul(b.math('MULTIPLY_ADD', position, 0.7, 0.15), offset_size)
        lean = b.mul(b.sub(lean_rand, 0.5), 0.7)
        length = b.mn(b.mul(S('Crack Length'), b.math('MULTIPLY_ADD', length_rand, 0.9, 0.55)), b.mul(extent, 0.95))
        centre = b.add(b.math('MULTIPLY_ADD', lean, run, line_start), b.mul(wobble_shift, 0.0035))
        distance = b.absolute(b.sub(offset, centre))
        progress = b.div(run, b.mx(length, 1e-5))
        taper = b.power(b.maprange(b.sub(1.0, progress), 0.0, 1.0, 0.0, 1.0, True), 0.6)
        inside = b.mul(b.gt(run, 0.0), b.lt(run, length))
        crack_half = b.mul(b.mul(S('Crack Width'), 0.5), taper)
        core = b.mul(b.mul(hard(b.sub(crack_half, distance)), inside), active)
        lip_side = b.gt(b.sub(offset, centre), 0.0)
        lip = b.mul(b.mul(hard(b.sub(b.add(crack_half, 0.0006), distance)), inside), b.mul(active, lip_side))
        crack_core_mask = core if crack_core_mask is None else either(crack_core_mask, core)
        crack_lip_mask = lip if crack_lip_mask is None else either(crack_lip_mask, lip)
    if crack_core_mask is None:
        crack_core_mask = b.mul(g['piece_mask'], 0.0)
        crack_lip_mask = crack_core_mask
    crack_lip_only = b.mul(crack_lip_mask, b.sub(1.0, crack_core_mask))

    # ------------------------------------------------------------------------------------------------ 5. NOTCHES (dark bites out of the edge)
    notch_noise = breakup_noise                                                                 # the fine noise again (shared: noise is the expensive part)
    notch_threshold = b.sub(0.95, b.mul(b.mul(S('Notch Amount'), amt), 0.30))
    notch_excess = b.mx(b.sub(notch_noise, notch_threshold), 0.0)
    notch_region = b.math('MULTIPLY_ADD', bottom_weight, 0.6, 0.4)
    notch_reach = b.mul(b.mul(notch_excess, b.div(S('Notch Depth'), 0.30)), notch_region)
    notch = hard(b.sub(notch_reach, edge_distance))
    notch_rim_reach = b.add(notch_reach, 0.0018)
    notch_there = b.gt(notch_reach, 0.0025)                                                        # a pale rim only round a bite that is deep enough to see
    notch_rim = b.mul(hard(b.sub(notch_rim_reach, edge_distance)), notch_there)

    # ------------------------------------------------------------------------------------------------ 6. CORNER BREAKS (a whole corner gone)
    # only the two LOWER corners can break: the upper corners lie under the row of slates above, and each node costs time at every dot
    corner_flags = [
        # (distance along the side edge, distance up the side from the lower edge, random number for "does it break", random number for its size)
        (x_from_left, y_from_bottom, rand_b, rand_f),
        (x_from_right, y_from_bottom, rand_c, rand_g),
    ]
    chunk_mask, chunk_rim_mask = None, None
    for dx_corner, dy_corner, chance_random, size_random in corner_flags:
        broken = b.lt(chance_random, b.mul(S('Corner Break Amount'), amt))
        size = b.mul(S('Corner Break Size'), b.math('MULTIPLY_ADD', size_random, 0.8, 0.6))
        raggedness = b.mul(b.mul(b.sub(wobble, 0.5), 1.5), size)
        cut = b.add(b.add(dx_corner, b.mul(dy_corner, 1.1)), raggedness)              # a ragged diagonal cut across the corner
        chunk = b.mul(hard(b.sub(size, cut)), broken)
        rim = b.mul(hard(b.sub(b.add(size, 0.0030), cut)), broken)
        chunk_mask = chunk if chunk_mask is None else either(chunk_mask, chunk)
        chunk_rim_mask = rim if chunk_rim_mask is None else either(chunk_rim_mask, rim)

    # ------------------------------------------------------------------------------------------------ colour: later kinds paint over earlier ones
    colour = flake_colour
    colour = b.mix(colour, pit_colour, pit_ring)
    colour = b.mix(colour, S('Break Colour Light'), scratch_mask)
    colour = b.mix(colour, S('Break Colour Light'), crack_lip_only)
    colour = b.mix(colour, S('Hole Colour'), crack_core_mask)
    colour = b.mix(colour, S('Break Colour Light'), notch_rim)
    colour = b.mix(colour, S('Hole Colour'), notch)
    colour = b.mix(colour, S('Break Colour Light'), chunk_rim_mask)
    colour = b.mix(colour, S('Hole Colour'), chunk_mask)

    # ------------------------------------------------------------------------------------------------ mask, height (sunk), roughness (rougher)
    mask = flake
    for part in (pit_ring, scratch_mask, crack_core_mask, crack_lip_only, notch_rim, notch, chunk_rim_mask, chunk_mask):
        mask = either(mask, part)

    flake_relief = b.mul(b.mul(flake, 0.05), b.mul(b.math('MULTIPLY_ADD', b.sub(1.0, b.mn(depth_ratio, 1.0)), 0.4, 0.6), b.math('MULTIPLY_ADD', patch_noise, 0.4, 0.8)))   # deeper next to the edge, a little uneven
    sunk = flake_relief
    for part, depth in ((pit_ring, 0.06), (scratch_mask, 0.02), (crack_core_mask, 0.12), (crack_lip_only, 0.03), (notch, 0.15), (chunk_mask, 0.32), (chunk_rim_mask, 0.04)):
        sunk = either(sunk, b.mul(part, depth))
    sunk = b.mul(sunk, piece_mask)                                                              # damage only counts on the slate, not in the joints
    height = b.mul(b.mul(sunk, S('Sink Depth')), -1.0)

    rough = b.mul(flake, 0.12)
    for part, more in ((pit_ring, 0.2), (scratch_mask, 0.05), (crack_core_mask, 0.2), (notch, 0.2), (chunk_mask, 0.2), (chunk_rim_mask, 0.12)):
        rough = either(rough, b.mul(part, more))
    roughness = b.mul(b.mul(rough, piece_mask), S('Roughness Gain'))

    mask = b.mul(mask, piece_mask)
    b.finish_layer(mask=mask, colour=colour, height=height, roughness=roughness, apply_amount=False)
    return tree
