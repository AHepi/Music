# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# MOSS is the living growth on the slates: moss and lichen. It decides WHERE growth gathers, paints it as flat clumps with hard,
# ragged edges in a family of olive tones, scatters small pale-tan lichen discs and rings, raises the surface a little (fuzzy) and
# makes it rougher. It uses no picture of any kind: everything is made of Blender nodes.
#
# THE IDEA IN ONE PICTURE. At every dot of a slate we work out a number called the GROWTH STRENGTH. Moss is painted where the strength
# is above a line (the "threshold"); a bigger Coverage lowers the line. The strength is a sum of small pieces, each one a plain rule:
#     strength = patch gate x ( drips below the upper edge          water runs down from the top edge in thin strands of different length
#                             + joints                              the damp strip along the side joints of a slate
#                             + lower part                          the lower part of a slate stays wet
#                             + damp spots                          slates that sit low, and the sloping rim, hold water
#                             + damage                              (optional) moss may grow on broken places, or keep away from them )
#              + clump noise                                        tall, wobbly seamless-free noise made on the slate's own coordinates: this
#                                                                   is what breaks the rules into clumps and gives every slate its own pattern
#              + fringe and ragged edge                             thin vertical strokes and fine wobble added just where the line is crossed,
#                                                                   so the edge of a clump grows thin teeth pointing down
# The PATCH GATE is a very slow seamless noise (a few big areas of the roof, with large clean areas between), multiplied by each
# slate's own "how mossy am I" random number (some slates are nearly clean, a few are covered).
#
# WHY IT LOOKS PAINTED, NOT LIKE CAMOUFLAGE. (1) The clump noise is stretched TALL (default 1.8 times taller than wide) and its
# coordinates are pushed sideways by a slow wobble that grows as you go down the slate, so a clump runs down like a drip, not like a
# round blob. (2) The drips start at the slate's own upper edge (top_edge_distance follows the chips of that edge) and have different
# lengths from strand to strand (a noise that depends on the sideways position only). (3) The colour of a clump is cut into FLAT tone steps
# (five olive tones) by stretched cells, so there is no smooth shading: every cell of the paint is one tone with a hard edge. The rim of a clump
# is lighter, the part under the upper edge darker (shadow). (4) Edges have a fine, tall raggedness and thin down-pointing fringe teeth.
#
# LICHEN: small round discs (and rings with a darker middle) in pale tan, on a jittered grid (one possible disc per grid place; a disc never
# crosses the edge of its place, so the tile repeats exactly). They like the same wet places as moss and the lower part of a slate.
#
# What it reads: the layout bundle, its own controls and seed, and ONE declared link: DAMAGE's Mask (see ../interface/interface.md, section 5).
#   * 'Damage Avoid' (0..1): moss is cut back on dots where the damage mask is 1 (fresh damage is clean), so moss height does not fill a chip.
#   * 'Damage Attract' (0..1): moss grows MORE on damaged dots (old flakes and cracks are good places for moss). It only shows when the stack
#     order puts moss over damage (setting recipe.stack_order); with the default order damage is painted over moss.
# Sizes are TILE UNITS (1.0 = the base tile; at 1254 dots per tile 0.0064 = 8 dots), so the look is the same at any picture size.
# Seamless: the patch gate and the lichen grid read the tile coordinate (Vector) in the exact-repeat way; everything else is made on the slate's own
# coordinates (local_x, local_y times the slate size), which are the same wherever the slate is wrapped round the picture edge.
# Outputs (fixed by the interface): Mask (growth), Colour (the painted colour), Height (slightly raised, fuzzy), Roughness (rougher).
# Amount (0..1) is used smartly: it scales Coverage and Lichen Amount, so the paint stays crisp at every Amount; 0 switches the layer off exactly.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layer_interface as li  # noqa: E402
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'moss'
GROUP_NAME = 'MOSS'
DEFAULT_SEED = 31.0

# Colours were chosen by hand after ONE look at the reference (its moss runs from brightness 42 to 74: #2b2c23 to #545340; its tan lichen from
# 87 to 107). Nothing is copied from any one spot.
CONTROLS = [
    # ---- how much, and where in the big picture
    Control('coverage', 'Coverage', 0.2, 0.0, 1.0, 'how much of the slate surface is moss: 0 = none, 0.2 = about a tenth of the slate dots (like the reference), 0.4 = about a fifth, 1 = nearly everything'),
    Control('patchiness', 'Patchiness', 0.9, 0.0, 1.0, 'how much the moss gathers into a few big mossy areas with large clean areas between: 0 = spread evenly over all slates, 1 = only in the big areas'),
    Control('patch_size', 'Patch Size', 0.35, 0.1, 1.0, 'size of the big mossy and clean areas, in tile units (0.35 = about three areas across the tile)'),
    Control('slate_variation', 'Slate Variation', 0.85, 0.0, 1.0, 'how different the slates are from each other: 0 = every slate equally mossy, 1 = some nearly clean, some thick with moss'),
    # ---- where it likes to grow (each is a preference; 0 = does not care)
    Control('drip_preference', 'Drip Preference', 0.8, 0.0, 1.5, 'how strongly moss gathers just below the upper edge of a slate and runs down in drips'),
    Control('drip_length', 'Drip Length', 0.1, 0.005, 0.25, 'how far an average drip can run down a slate, in tile units (0.06 = 75 dots); single strands are shorter and longer than this'),
    Control('drip_width', 'Drip Width', 0.05, 0.008, 0.12, 'width of one drip strand, in tile units (0.04 = 50 dots); positions between strands stay clean'),
    Control('joint_preference', 'Joint Preference', 0.35, 0.0, 1.5, 'how strongly moss gathers along the side joints of a slate'),
    Control('lower_preference', 'Lower Part Preference', 0.2, 0.0, 1.5, 'how strongly moss gathers in the lower part of a slate'),
    Control('damp_preference', 'Damp Spot Preference', 0.3, 0.0, 1.5, 'how strongly moss gathers where the surface sits low (slates that lie lower and the sloping rim of every slate)'),
    Control('damage_avoid', 'Damage Avoid', 0.8, 0.0, 1.0, 'how much moss keeps off fresh damage: 1 = no moss at all on a damaged dot, 0 = does not care'),
    Control('damage_attract', 'Damage Attract', 0.0, 0.0, 1.0, 'how much moss prefers damaged dots (old flakes): only visible when moss is stacked over damage'),
    # ---- the shape of the clumps
    Control('cluster_size', 'Cluster Size', 0.05, 0.01, 0.2, 'width of a moss clump, in tile units (0.05 = 63 dots)'),
    Control('clump_strength', 'Clump Strength', 1.5, 0.0, 3.0, 'how much the clump noise (instead of the rules) decides where moss is: 0 = only the rules (a band under the upper edge), 3 = free blobs everywhere'),
    Control('drip_stretch', 'Drip Stretch', 1.8, 1.0, 5.0, 'how much taller than wide the clumps are: 1 = round blobs, 1.8 = drips, 4 = long thin streaks'),
    Control('flow_wobble', 'Flow Wobble', 0.012, 0.0, 0.05, 'how far a drip wanders sideways as it runs down, in tile units (0.012 = 15 dots)'),
    Control('edge_raggedness', 'Edge Raggedness', 0.6, 0.0, 1.5, 'how ragged and broken the edge of a clump is (0 = smooth outline, 1 = very ragged with loose flecks)'),
    Control('fringe_amount', 'Fringe Amount', 0.25, 0.0, 1.5, 'how long the thin fringe teeth that hang down from the edges of a clump are (0 = none; 0.25 = teeth up to about 20 dots long; 1.5 = long hairs)'),
    Control('fringe_width', 'Fringe Width', 0.009, 0.002, 0.02, 'width of one fringe tooth, in tile units (0.009 = 11 dots)'),
    # ---- the olive colours (darkest to lightest) and how they are used
    Control('tone_1', 'Moss Tone 1 (darkest)', '#2b2c23', kind='colour', text='the darkest olive: deep shadow under the upper edge and the heart of thick moss'),
    Control('tone_2', 'Moss Tone 2', '#35372a', kind='colour', text='dark olive'),
    Control('tone_3', 'Moss Tone 3', '#3f4032', kind='colour', text='middle olive'),
    Control('tone_4', 'Moss Tone 4', '#49493a', kind='colour', text='light olive'),
    Control('tone_5', 'Moss Tone 5 (lightest)', '#545342', kind='colour', text='yellow-green: the youngest growth at the rim of a clump'),
    Control('tone_centre', 'Moss Tone Centre', 0.6, 0.0, 1.0, 'which tone is typical: 0 = mostly the darkest olive, 1 = mostly the lightest'),
    Control('tone_spread', 'Moss Tone Spread', 0.8, 0.0, 1.0, 'how many different tones one clump uses: 0 = every clump one flat tone, 1 = the whole range'),
    Control('rim_lightening', 'Rim Lightening', 0.5, 0.0, 1.0, 'how much lighter (yellow-green) the rim of a clump is than its middle'),
    Control('top_shading', 'Top Shading', 0.3, 0.0, 1.0, 'how much darker moss is right under the upper edge of a slate (the shadow of the row above)'),
    Control('tone_patch_size', 'Tone Patch Size', 0.02, 0.006, 0.08, 'width of one flat patch of one tone inside a clump, in tile units (0.02 = 25 dots); patches are 2.7 times taller than wide at the default Drip Stretch'),
    # ---- lichen
    Control('lichen_amount', 'Lichen Amount', 0.35, 0.0, 1.0, 'how many lichen discs there are (0 = none): the share of grid places that hold a disc'),
    Control('lichen_clustering', 'Lichen Clustering', 0.7, 0.0, 1.0, 'how much lichen gathers into colonies with bare slate between them: 0 = scattered evenly, 1 = only in colonies'),
    Control('lichen_size', 'Lichen Size', 0.0042, 0.001, 0.012, 'typical radius of a small lichen disc, in tile units (0.0042 = 5 dots); the few big discs and rings are about three times that'),
    Control('lichen_colour', 'Lichen Colour', '#645c4f', kind='colour', text='the tan of a lichen disc (a ring has this colour)'),
    Control('lichen_light', 'Lichen Light', '#746a5c', kind='colour', text='the paler tan of a lichen ring and of the brightest discs'),
    Control('lichen_dark', 'Lichen Dark', '#524c40', kind='colour', text='the darker tan in the middle of a ring'),
    # ---- relief and roughness
    Control('raise', 'Raise', 1.0, 0.0, 4.0, 'multiplies how much moss and lichen raise the surface (1 = moss +0.035, lichen +0.025 of the height scale)'),
    Control('roughness_gain', 'Roughness Gain', 1.0, 0.0, 4.0, 'multiplies how much rougher moss and lichen are (1 = moss +0.14)'),
]
# (socket label, kind, default, plain text, (layer it comes from, that layer's output))  -- the recipe wires these
DECLARED_LINKS = [
    ('Damage Mask', 'float', 0.0, 'DAMAGE\'s Mask: where the slate is damaged, so moss can avoid fresh damage or gather on old damage', ('damage', 'Mask')),
]

EDGE = 0.02                  # softness of a moss edge in "growth strength" units: about one dot at the default clump size
LICHEN_PLACES = 60           # lichen grid places across one base tile (a place is about 21 dots wide at 1254)


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    tiles = S('Tile Count')
    seed = S('Seed')
    amt = b.mn(S('Amount'), 1.0)
    piece_mask = g['piece_mask']
    width, height = g['piece_width'], g['piece_height']

    # ------------------------------------------------------------------------------------------------ helpers
    def hard(value, width_of_edge=EDGE):
        """0 below -edge, 1 above +edge: a nearly hard step (about one dot wide where the strength changes by about 40 per tile unit)."""
        return b.smoothstep(value, -width_of_edge, width_of_edge)

    # per-slate random numbers: the same on every dot of one slate, new with the layer's Seed
    def slate_hash(slot, w=0.0):
        node = b.hash4(b.vec(g['piece_id'], seed, float(slot)), w)
        red, green, blue = b.channels(node.outputs['Color'])
        return node.outputs['Value'], red, green, blue

    slate_a, off_x, off_y, off_z = slate_hash(1, 0.0)           # slate_a = how mossy this slate is; the others shift the noise so every slate differs
    slate_b, tone_off_x, tone_off_y, tone_off_z = slate_hash(2, 0.5)

    # ------------------------------------------------------------------------------------------------ where am I on the slate (tile units)
    x_across = b.mul(g['local_x'], width)                          # distance from the left edge of the slate
    x_from_right = b.mul(b.sub(1.0, g['local_x']), width)
    side_near = b.mn(x_across, x_from_right)                       # distance to the nearer side joint
    y_down = g['top_edge_distance']                                # distance below the upper edge (follows its chips)

    def slate_noise(x_in, y_in, features_x, features_y, detail, roughness, z_shift):
        """Plain noise (0..1) read on the slate's OWN coordinates (tile units): the same wherever the slate is wrapped round the picture edge.
        features_x / features_y = noise features per tile unit sideways / downwards (a smaller features_y = taller features).
        y_in = None: the noise depends on the sideways position only (tall strands that never change going down)."""
        down = b.mul(off_y, 90.0) if y_in is None else b.add(b.mul(y_in, features_y), b.mul(off_y, 90.0))
        position = b.vec(b.add(b.mul(x_in, features_x), b.mul(off_x, 90.0)), down,
                         b.add(b.mul(off_z, 90.0), b.add(b.mul(seed, 3.7), z_shift)))
        node = b.noise(position, 1.0, detail, roughness)
        return b.maprange(node.outputs['Factor'], 0.3, 0.7, 0.0, 1.0, True)

    # ------------------------------------------------------------------------------------------------ the sideways wobble that makes the drips flow
    wobble_noise = slate_noise(x_across, y_down, 1.0 / 0.06, 1.0 / 0.12, 1.0, 0.5, 11.0)           # slow: one wiggle about every 0.06 across, 0.12 down
    x_flow = b.add(x_across, b.mul(b.mul(b.sub(wobble_noise, 0.5), 2.0), S('Flow Wobble')))         # sideways position pushed about by the wobble

    # ------------------------------------------------------------------------------------------------ the fringe: vertical brush strokes that push the picture down
    # A noise that depends on the sideways position only (thin upright strokes, Fringe Width wide) shifts the downward position of every dot by its own amount, so
    # every edge of a clump grows teeth that point down, each tooth one stroke wide and up to Fringe Amount x 0.07 tile long, whatever the shape of the clump is.
    stroke = slate_noise(x_flow, None, b.div(1.0, S('Fringe Width')), 0.0, 1.0, 0.5, 61.0)
    y_flow = b.sub(y_down, b.mul(stroke, b.mul(S('Fringe Amount'), 0.07)))

    # ------------------------------------------------------------------------------------------------ the strands (drip lengths) and the clump noise
    strand_features = b.div(1.0, S('Drip Width'))
    strands = slate_noise(x_flow, None, strand_features, 0.0, 3.0, 0.62, 23.0)   # depends on the sideways position only: tall strands
    clump_features = b.div(1.0, S('Cluster Size'))
    clump_features_down = b.div(clump_features, S('Drip Stretch'))
    clump = slate_noise(x_flow, y_flow, clump_features, clump_features_down, 3.0, 0.5, 37.0)

    # ------------------------------------------------------------------------------------------------ the rules (each 0..1)
    # 1. drips below the upper edge: where the strand noise is low there is no drip at all; where it is high the strand reaches up to 2 times the Drip Length
    reach = b.mul(S('Drip Length'), b.maprange(strands, 0.40, 0.70, 0.0, 2.0, True))
    reach = b.add(reach, 0.002)
    drip = b.maprange(b.sub(1.0, b.div(y_flow, reach)), 0.0, 1.0, 0.0, 1.0, True)
    drip = b.power(drip, 0.55)                                          # a rounder tongue: wide for most of its length, then a short taper
    # 1b. the whole upper part of a slate is wetter than the lower part: a gentle slope from 1 at the upper edge to 0 at the lower edge (the reference has about twice as much moss in the upper half)
    upper = b.power(b.sub(1.0, g['local_y']), 1.3)
    # 2. along the side joints
    joint = b.sub(1.0, b.smoothstep(side_near, 0.0, 0.04))
    # 3. the lower part of the slate
    lower = b.smoothstep(g['local_y'], 0.55, 1.0)
    # 4. damp spots: where the bare relief sits low (joint slope, slates that lie lower)
    damp = b.smoothstep(b.sub(1.0, g['base_height']), 0.44, 0.58)
    # 5. damage (declared link)
    damage_here = b.mn(S('Damage Mask'), 1.0)

    supply = b.sum_of([b.mul(drip, S('Drip Preference')), b.mul(upper, b.mul(S('Drip Preference'), 0.3)), b.mul(joint, S('Joint Preference')), b.mul(lower, S('Lower Part Preference')),
                       b.mul(damp, S('Damp Spot Preference')), b.mul(damage_here, b.mul(S('Damage Attract'), 0.8))])

    # ------------------------------------------------------------------------------------------------ the gate: big mossy areas, mossy and clean slates
    patch_features = b.mul(tiles, b.div(1.0, S('Patch Size')))
    patch_noise = b.maprange(b.tileable_noise(S('Vector'), patch_features, 2.0, 0.5, b.mul(seed, 1.7)),
                             0.3, 0.7, 0.0, 1.0, True)
    patch_gate = b.mixf(1.0, b.smoothstep(patch_noise, 0.32, 0.58), S('Patchiness'))
    slate_value = b.math('MULTIPLY_ADD', b.power(slate_a, 1.5), 1.5, 0.25)
    slate_gate = b.mixf(1.0, slate_value, S('Slate Variation'))
    gate = b.mn(b.mul(patch_gate, slate_gate), 1.15)

    # ------------------------------------------------------------------------------------------------ the strength, the threshold, and the ragged edge
    ragged = slate_noise(x_flow, y_flow, 1.0 / 0.012, 1.0 / 0.045, 2.0, 0.5, 51.0)                        # fine, a little taller than wide
    dabs = slate_noise(x_flow, y_flow, 1.0 / 0.010, 1.0 / 0.012, 2.0, 0.5, 91.0)                         # fine, round: islands, holes and loose flecks along the rim of a clump
    strength = b.add(supply, b.mul(b.sub(clump, 0.5), S('Clump Strength')))
    strength = b.add(strength, b.mul(b.sub(ragged, 0.5), b.mul(S('Edge Raggedness'), 0.40)))
    strength = b.add(strength, b.mul(b.sub(dabs, 0.5), b.mul(S('Edge Raggedness'), 0.55)))
    coverage = b.mul(S('Coverage'), amt)
    # The line: Coverage 0 puts it above anything the strength can reach (no moss), Coverage 1 puts it at 0 (nearly everything). The gate then moves it: a clean slate or area
    # needs a much stronger push, a mossy one a little less. (Measured on the default settings: Coverage 0.25 covers about a tenth of the slate dots.)
    threshold = b.add(b.sub(1.9, b.mul(b.power(coverage, 0.5), 1.9)), b.mul(b.sub(1.0, gate), 0.9))
    excess = b.sub(strength, threshold)
    moss_raw = hard(excess)
    keep = b.sub(1.0, b.mul(damage_here, S('Damage Avoid')))
    moss = b.mul(b.mul(b.mul(moss_raw, keep), piece_mask), b.gt(coverage, 0.0))

    # ------------------------------------------------------------------------------------------------ the colour: five flat olive tones
    # The tone of a dot comes from three flat things added together: (1) tall patches (stretched cells, one random tone each), (2) vertical brush stripes (a noise
    # that depends on the sideways position only), (3) a few small light and dark flecks. Then the rim of a clump is lightened and the shadow under the upper edge darkened.
    # The cell coordinates are pushed about by the clump and edge noise, so the borders between tone patches are ragged and curved, not straight.
    def cell_random(patch_width, stretch, push_x, push_y, z_shift):
        node = b.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='F1')
        cell_x = b.add(b.mul(x_flow, b.div(1.0, patch_width)), b.mul(b.sub(ragged, 0.5), push_x))
        cell_y = b.add(b.mul(y_down, b.div(1.0, b.mul(patch_width, stretch))), b.mul(b.sub(clump, 0.5), push_y))
        position = b.vec(b.add(cell_x, b.mul(tone_off_x, 90.0)), b.add(cell_y, b.mul(tone_off_y, 90.0)), b.add(b.mul(tone_off_z, 90.0), b.add(b.mul(seed, 2.9), z_shift)))
        b._put(node, 'Vector', position)
        b._put(node, 'Scale', 1.0)
        b._put(node, 'Randomness', 1.0)
        return b.channels(node.outputs['Color'])[0]

    patch_random = cell_random(S('Tone Patch Size'), b.mul(S('Drip Stretch'), 1.5), 2.0, 2.0, 0.0)
    fleck_random = cell_random(0.007, 1.3, 0.8, 0.8, 9.0)
    stripes = slate_noise(x_flow, None, b.div(1.0, b.mul(S('Tone Patch Size'), 0.5)), 0.0, 1.0, 0.5, 83.0)
    depth = b.maprange(excess, 0.0, 0.45, 0.0, 1.0, True)                                              # 0 at the rim of a clump, 1 deep inside
    shade_zone = b.sub(1.0, b.smoothstep(y_down, 0.0, 0.05))                                           # 1 right under the upper edge
    tone = b.math('MULTIPLY_ADD', b.sub(b.add(b.mul(patch_random, 0.6), b.mul(stripes, 0.4)), 0.5), S('Moss Tone Spread'), S('Moss Tone Centre'))
    tone = b.add(tone, b.mul(b.sub(1.0, depth), b.mul(S('Rim Lightening'), 0.30)))
    tone = b.sub(tone, b.mul(shade_zone, b.mul(S('Top Shading'), 0.35)))
    tone = b.sub(tone, b.mul(depth, 0.08))
    tone = b.add(tone, b.mul(b.gt(fleck_random, 0.90), 0.30))                                          # a few small light flecks (young growth)
    tone = b.sub(tone, b.mul(b.lt(fleck_random, 0.06), 0.25))                                          # and a few dark ones
    moss_colour = S('Moss Tone 1 (darkest)')
    for step, name in enumerate(['Moss Tone 2', 'Moss Tone 3', 'Moss Tone 4', 'Moss Tone 5 (lightest)']):
        moss_colour = b.mix(moss_colour, S(name), b.gt(tone, (step + 1) / 5.0))

    # ------------------------------------------------------------------------------------------------ lichen: discs and rings on jittered grids
    u, v, _ = b.xyz(S('Vector'))
    big_places = b.mul(tiles, float(LICHEN_PLACES // 2))
    still_u, still_v = b.div(b.add(b.floor(b.mul(u, big_places)), 0.5), big_places), b.div(b.add(b.floor(b.mul(v, big_places)), 0.5), big_places)   # the middle of the big grid place: one number per place
    colony_noise = b.maprange(b.tileable_noise(b.vec(still_u, still_v, 0.0), b.mul(tiles, 6.0), 2.0, 0.5, b.add(b.mul(seed, 2.3), 5.0)), 0.3, 0.7, 0.0, 1.0, True)
    colony = b.mixf(1.0, b.smoothstep(colony_noise, 0.40, 0.60), S('Lichen Clustering'))
    wet = b.add(b.mul(patch_gate, 0.35), b.add(b.mul(lower, 0.25), 0.4))                          # 0.4 .. 1: lichen is smaller where it is drier (the radius shrinks smoothly: a disc is never cut in half)
    keep_clear = b.mul(b.mul(piece_mask, b.sub(1.0, b.mul(damage_here, S('Damage Avoid')))), b.gt(g['edge_distance'], 0.003))
    lichen_chance_all = b.mul(b.mul(S('Lichen Amount'), amt), colony)

    def lichen_grid(places_per_tile, size_factor, chance_factor, hash_w, ring_share):
        """One jittered grid of possible lichen discs. Returns (disc, inner disc, is_ring, size random) as 0..1 numbers. A disc never crosses the edge of its
        grid place, and the place number is wrapped, so the tile repeats exactly."""
        places = b.mul(tiles, float(places_per_tile))
        grid_u, grid_v = b.mul(u, places), b.mul(v, places)
        place_i, place_j = b.mod(b.floor(grid_u), places), b.mod(b.floor(grid_v), places)
        in_u, in_v = b.frac(grid_u), b.frac(grid_v)
        node = b.hash4(b.vec(place_i, place_j, b.mul(seed, 1.9)), hash_w)
        chance, pos_x, pos_y = b.channels(node.outputs['Color'])
        size_random = node.outputs['Value']
        radius = b.mn(b.mul(b.mul(S('Lichen Size'), b.mul(size_factor, b.math('MULTIPLY_ADD', b.power(size_random, 2.0), 2.0, 0.5))), float(places_per_tile)), 0.44)
        centre_u = b.math('MULTIPLY_ADD', b.sub(1.0, b.mul(radius, 2.0)), pos_x, radius)         # the centre is placed so that the whole disc stays inside its place
        centre_v = b.math('MULTIPLY_ADD', b.sub(1.0, b.mul(radius, 2.0)), pos_y, radius)
        radius = b.mul(radius, wet)                                                                 # then the disc shrinks in dry places
        du, dv = b.sub(in_u, centre_u), b.sub(in_v, centre_v)
        distance = b.sqrt(b.add(b.mul(du, du), b.mul(dv, dv)))
        distance = b.add(distance, b.mul(b.sub(ragged, 0.5), b.mul(radius, 0.9)))                  # an irregular outline, not a perfect circle
        soft = 0.0008 * places_per_tile
        disc = b.smoothstep(b.sub(radius, distance), 0.0, soft)
        inner = b.smoothstep(b.sub(b.mul(radius, 0.5), distance), 0.0, soft)
        has = b.lt(chance, b.mul(lichen_chance_all, chance_factor))
        return b.mul(b.mul(disc, has), keep_clear), inner, b.gt(size_random, 1.0 - ring_share), size_random

    small_disc, small_inner, small_ring, small_size = lichen_grid(LICHEN_PLACES, 1.0, 0.8, 0.7, 0.3)
    big_disc, big_inner, big_ring, big_size = lichen_grid(LICHEN_PLACES // 2, 2.2, 0.3, 0.3, 0.7)
    lichen = b.mx(small_disc, big_disc)
    small_colour = b.mix(S('Lichen Colour'), S('Lichen Light'), b.gt(small_size, 0.6))
    small_colour = b.mix(small_colour, S('Lichen Dark'), b.mul(small_inner, small_ring))
    big_colour = b.mix(S('Lichen Light'), S('Lichen Colour'), b.gt(big_size, 0.5))
    big_colour = b.mix(big_colour, S('Lichen Dark'), b.mul(big_inner, big_ring))
    lichen_colour = b.mix(small_colour, big_colour, b.gt(big_disc, 0.5))
    lichen_inner = b.mx(b.mul(small_inner, small_ring), b.mul(big_inner, big_ring))

    # ------------------------------------------------------------------------------------------------ the outputs
    mask = b.mx(moss, lichen)
    colour = b.mix(moss_colour, lichen_colour, lichen)
    fuzz = slate_noise(x_across, g['local_y'], 1.0 / 0.004, 1.0 / 0.004, 1.0, 0.5, 71.0)
    moss_height = b.mul(moss, b.math('MULTIPLY_ADD', fuzz, 0.045, 0.02))
    lichen_height = b.mul(lichen, b.math('MULTIPLY_ADD', b.sub(1.0, lichen_inner), 0.012, 0.016))
    height = b.mul(b.add(moss_height, lichen_height), S('Raise'))
    roughness = b.mul(b.add(b.mul(moss, 0.14), b.mul(lichen, 0.08)), S('Roughness Gain'))
    b.finish_layer(mask=mask, colour=colour, height=height, roughness=roughness, apply_amount=False)
    return tree
