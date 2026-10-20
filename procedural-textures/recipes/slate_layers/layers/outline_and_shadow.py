# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# OUTLINE AND SHADOW is the dark drawing around every slate. It is painted LAST, over everything, and it makes five things:
#   1. THE BLACK JOINTS   the dark gaps between slates (the layout's gap_mask) plus a little painted black that spills out of the gap, with a
#                         hand-drawn ragged edge (a 6-dot gap plus a black core, the way a painter draws it).
#   2. THE SIDE OUTLINES  a thin dark line just inside every slate edge (about 2 dots wide), a little different width everywhere.
#   3. THE SHADOW BAND    the shadow the slate above throws on the TOP of the slate below: darkest right under the black joint, fading
#                         over about 38 dots, painted in four flat steps (not a smooth blur) whose lower edges are ragged like drips,
#                         with a few teeth of solid black hanging down from the black band.
#   4. THE LIP            a pale, broken line along the LOWER edge of a slate, just above its black joint (the edge catching the light); it
#                         starts about 3 dots inside the edge, after a thin dark rim, as in the reference.
#   5. THE EDGE DARKENING a faint darkening of the slate close to every edge (about 6 dots), so slates do not look flat-cut.
# It also gives the relief: the shadow band is a slope (the slate rises out of the joint), the lip is a small raised rim, the side
# outline is a small groove. (The joints themselves are already low in the layout's base_height; this layer only adds to that.)
#
# What it reads: ONLY the layout bundle (gap_mask, piece_mask, edge_distance, top_edge_distance, local_x, local_y, piece_id, piece_width,
# piece_height) and its own controls and seed. It never looks at another layer.
#
# How the pieces are put together, in one concrete example (the shadow band): at every dot we ask "how far below the slate's upper edge am I?"
# (top_edge_distance, in tile units). The shadow reaches down `Shadow Width` from the edge, but the reach is made longer or shorter by a
# seamless noise that is stretched UP-DOWN (it changes quickly left to right and slowly up and down), so the lower border of the shadow has
# teeth pointing down, like painted drips. How far into the reach this dot is (1 right at the edge, 0 at the end) is cut into `Shadow Tiers`
# flat steps (4 by default; 0 = a smooth blur) and multiplied by `Shadow Darkness`. That number is the strength with which the shadow
# colour is laid over the picture underneath, so the slate's own paint still shows through the shadow.
#
# How the five pieces share one Colour output: each piece has its own colour and its own strength (0..1) at every dot. They are laid over
# each other in a fixed order (edge darkening, shadow, lip, side outline, black joint; later ones on top) exactly like paint layers, and the
# layer outputs the result as ONE colour and ONE Mask (the combined strength). COMBINE then lays that over the picture below, and the
# result is the same as painting the five pieces one after the other. (See `lay_over` below.)
#
# Sizes are TILE UNITS (1.0 = the base tile; at 1254 dots per tile 0.0064 = 8 dots), so the look is the same at any picture size.
# Seamless noise: the tile coordinate is turned into circles (a "donut") so the noise repeats exactly at the tile edge; the noise is read at
# a feature count of (features per tile x Tile Count), so a 2 x 2 area has twice as many features and the same look per dot.
# The Amount control scales the whole layer (0 = off: Mask, Height and Roughness are exactly 0).
#
# Keep (needed by the recipe): LAYER_KEY, GROUP_NAME, DEFAULT_SEED, CONTROLS, DECLARED_LINKS, build_group(parameters), and the call
# b.finish_layer(mask, colour, height, roughness) at the end.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layer_interface as li  # noqa: E402
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'outline_and_shadow'
GROUP_NAME = 'OUTLINE AND SHADOW'
DEFAULT_SEED = 41.0

# The defaults were set by looking at the reference once (its general character, nothing slate by slate): the black core under a row is about
# 8 to 10 dots; a vertical joint is about 5 dots of dark; right under the black the picture is about 40 percent as bright as the slate and
# climbs back to full brightness over about 30 to 40 dots; just above the black there is a faint bright lip about 6 dots wide; the slate is
# a little darker for about 5 dots next to any dark joint. Then every number was tuned by eye (see outline_work/ in the folder).
CONTROLS = [
    # ---- the black joints
    Control('joint_width', 'Joint Width', 0.0008, 0.0, 0.006, 'how far the painted black spills out of the gap BETWEEN SLATES OF A ROW into each slate, in tile units (0.0008 = 1 dot); the gap itself is the layout\'s Joint Width'),
    Control('band_width', 'Band Width', 0.0004, 0.0, 0.008, 'how far the painted black spills out of the band BETWEEN ROWS into the slates above and below, in tile units (0.0004 = 0.5 dot); the band itself is the layout\'s Row Gap'),
    Control('joint_colour', 'Joint Colour', '#0e0f11', kind='colour', text='the near-black of the joints'),
    # ---- the thin dark outline along the slate edges
    Control('side_outline_width', 'Side Outline Width', 0.0020, 0.0, 0.008, 'width of the thin dark line just inside every slate edge, in tile units (0.0020 = 2.5 dots)'),
    Control('side_outline_darkness', 'Side Outline Darkness', 0.6, 0.0, 1.0, 'how strongly the outline colour covers the slate paint (0 = invisible, 1 = solid)'),
    Control('outline_colour', 'Outline Colour', '#14161a', kind='colour', text='the dark blue-black of the thin outline (a little lighter than the joint black)'),
    # ---- the shadow band on the top of each slate
    Control('shadow_width', 'Shadow Width', 0.030, 0.0, 0.06, 'how far the shadow of the slate above reaches down the slate below, in tile units (0.030 = 38 dots; the reference band is about 21 dots of dark plus a soft tail to 40 dots)'),
    Control('shadow_darkness', 'Shadow Darkness', 0.7, 0.0, 1.0, 'how strongly the shadow colour covers the slate paint right under the joint (0 = no shadow, 1 = solid black); it is weaker lower down'),
    Control('shadow_tiers', 'Shadow Tiers', 4.0, 0.0, 8.0, 'how many flat painted steps the shadow is cut into (0 = a smooth blur; 4 = four flat tones; 1 = one flat band)'),
    Control('shadow_drip', 'Shadow Drip', 0.5, 0.0, 1.0, 'how ragged the lower border of the shadow is, as a share of Shadow Width (0 = a straight line; 0.5 = teeth pointing down like drips; 1 = very ragged)'),
    Control('black_drips', 'Black Drips', 0.009, 0.0, 0.03, 'how far black drips hang down from the black band into the shadow, in tile units (0.009 = 11 dots at most; they are teeth of different length, most places have none; 0 = no drips)'),
    Control('shadow_colour', 'Shadow Colour', '#0f1114', kind='colour', text='the colour of the shadow: very dark blue-grey that is laid over the slate paint'),
    # ---- the pale lip along the lower edge
    Control('lip_offset', 'Lip Offset', 0.0026, 0.0, 0.02, 'how far inside the slate edge the pale lip starts, in tile units (0.0026 = 3.3 dots: between the black joint and the lip is a thin dark rim, as in the reference)'),
    Control('lip_width', 'Lip Width', 0.0030, 0.0, 0.02, 'width of the pale lip along the lower edge of a slate, in tile units (0.0030 = 3.8 dots), measured from the slate edge, after Lip Offset'),
    Control('lip_brightness', 'Lip Brightness', 0.25, 0.0, 1.0, 'how strongly the pale colour covers the slate paint on the lip (0 = no lip, 1 = solid pale)'),
    Control('lip_breakup', 'Lip Breakup', 0.4, 0.0, 1.0, 'how broken the lip is (0 = one unbroken line, 1 = only short pale pieces)'),
    Control('lip_colour', 'Lip Colour', '#8c8e8b', kind='colour', text='the pale grey of the lip (the reference lip and chips measure about #6d6c67 to #7a7975 on top of the paint)'),
    # ---- the slight darkening toward every edge
    Control('edge_darkening', 'Edge Darkening', 0.3, 0.0, 1.0, 'how strongly the slate is darkened right next to its edges (0 = not at all)'),
    Control('edge_darkening_width', 'Edge Darkening Width', 0.0045, 0.0, 0.03, 'how far from an edge the darkening reaches, in tile units (0.0045 = 5.6 dots)'),
    # ---- hand-drawn look
    Control('wobble', 'Wobble', 0.5, 0.0, 1.0, 'how hand-drawn the lines are: every outline and joint edge gets wider and narrower by this share (0 = ruler-straight lines, 0.5 = plus or minus half)'),
    Control('wobble_scale', 'Wobble Scale', 90.0, 10.0, 400.0, 'how many wobbles fit across one base tile: 90 = a wobble about 14 dots long; more = finer'),
    Control('slate_variation', 'Slate Variation', 0.5, 0.0, 1.0, 'how different the slates are from each other in shadow depth, shadow reach and lip (0 = every slate drawn the same)'),
    # ---- relief and roughness
    Control('shadow_height', 'Shadow Height', 0.12, 0.0, 0.5, 'how far the slate surface is pushed down at the top edge under the joint (a slope that rises over the Shadow Width); height scale 0..1'),
    Control('lip_height', 'Lip Height', 0.04, 0.0, 0.3, 'how much the lip is raised (height scale 0..1)'),
    Control('outline_height', 'Outline Height', 0.05, 0.0, 0.3, 'how deep the thin outline groove is (height scale 0..1)'),
    Control('joint_roughness', 'Joint Roughness', 0.12, -1.0, 1.0, 'how much rougher than a bare slate the black joints are (added to roughness)'),
    Control('shadow_roughness', 'Shadow Roughness', 0.06, -1.0, 1.0, 'how much rougher the shadow band is (dirt gathers there)'),
    Control('lip_roughness', 'Lip Roughness', -0.15, -1.0, 1.0, 'how much smoother the lip is (an edge worn smooth catches the light); minus = smoother'),
]
DECLARED_LINKS = []          # OUTLINE AND SHADOW reads no other layer

TWO_PI = 6.2831853
SOFT = 0.0006                # soft width of every painted edge, in tile units (0.0006 = 0.75 dot): painted look = hard edges, one dot of anti-aliasing


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    tiles, seed = S('Tile Count'), S('Seed')
    piece_mask, gap_mask = g['piece_mask'], g['gap_mask']
    edge_distance, top_edge_distance = g['edge_distance'], g['top_edge_distance']

    # ------------------------------------------------------------------------------------------------ helpers
    u, v, _ = b.xyz(S('Vector'))
    turns_u, turns_v = b.mul(u, TWO_PI), b.mul(v, TWO_PI)
    cos_u, sin_u = b.math('COSINE', turns_u), b.math('SINE', turns_u)
    cos_v, sin_v = b.math('COSINE', turns_v), b.math('SINE', turns_v)

    def seamless(scale_u, scale_v, detail, roughness, offset):
        """Seamless noise 0..1. scale_u / scale_v = how many features fit across the whole picture left-right / up-down (different numbers
        stretch the noise). The four circle numbers are shared by every noise in this layer (cheap)."""
        shift = b.add(b.mul(seed, 7.3), offset)
        radius_u, radius_v = b.mul(scale_u, 1.0 / TWO_PI), b.mul(scale_v, 1.0 / TWO_PI)
        position = b.vec(b.mul(cos_u, radius_u), b.mul(sin_u, radius_u), b.mul(cos_v, radius_v))
        node = b.noise(position, 1.0, detail, roughness, 0.0, b.math('MULTIPLY_ADD', sin_v, radius_v, shift), '4D', 'FBM', 2.0)
        return b.maprange(node.outputs['Factor'], 0.3, 0.7, 0.0, 1.0, True)

    def hard(value):
        """1 where `value` (a distance in tile units) is above 0, with a one-dot soft edge."""
        return b.smoothstep(value, 0.0, SOFT)

    def lay_over(under_colour, under_strength, colour, strength):
        """Paint `colour` with `strength` (0..1) over what is already painted (under_colour with under_strength). Returns (colour, strength).
        The same as the usual 'over' rule: new strength = 1 - (1 - old) x (1 - new); the colour is a mix weighted by who contributes how much."""
        total = b.sub(1.0, b.mul(b.sub(1.0, under_strength), b.sub(1.0, strength)))
        share = b.div(strength, b.mx(total, 1e-6))
        return b.mix(under_colour, colour, share), total

    # ------------------------------------------------------------------------------------------------ noises (the hand-drawn look)
    per_tile = b.mul(tiles, S('Wobble Scale'))
    wobble_a = seamless(per_tile, per_tile, 2.0, 0.55, 3.0)                              # widths of joint spill and outline
    wobble_b = seamless(b.mul(per_tile, 0.6), b.mul(per_tile, 0.6), 3.0, 0.55, 17.0)     # which parts of the lip are broken
    signed_a = b.mul(b.sub(wobble_a, 0.5), 2.0)                                         # -1 .. +1
    width_factor = b.mx(b.add(1.0, b.mul(signed_a, S('Wobble'))), 0.0)                  # 1 = as set, 0.5 .. 1.5 at Wobble 0.5
    drip_noise = seamless(b.mul(tiles, 55.0), b.mul(tiles, 12.0), 1.0, 0.5, 29.0)       # changes fast left-right, slowly up-down: teeth that point down

    # ------------------------------------------------------------------------------------------------ which kind of edge is the nearest (sides, lower, upper)?
    # The nearest edge is a LOWER edge when the dot's distance above the nominal lower edge is about the same as edge_distance (it can be larger by the depth
    # of a chip, 0.0055 at most); where a side edge is nearer, edge_distance is clearly smaller. The same for the upper edge. Soft over 0.007 .. 0.014.
    y_from_bottom = b.mul(b.sub(1.0, g['local_y']), g['piece_height'])
    y_from_top = b.mul(g['local_y'], g['piece_height'])
    bottom_weight = b.sub(1.0, b.smoothstep(b.sub(y_from_bottom, edge_distance), 0.007, 0.014))     # 1 along the lower edge, fades out round the corners
    top_weight = b.sub(1.0, b.smoothstep(b.sub(y_from_top, edge_distance), 0.007, 0.014))                      # 1 along the upper edge
    row_edge_weight = b.mx(bottom_weight, top_weight)                                              # 1 where the nearest edge borders the band between rows

    # ------------------------------------------------------------------------------------------------ per-slate random numbers
    pick = b.hash4(b.vec(g['piece_id'], seed, 5.0), 0.3)
    r_shadow = pick.outputs['Value']
    r_reach, r_lip, _spare = b.channels(pick.outputs['Color'])
    variation = S('Slate Variation')
    shadow_factor = b.mixf(1.0, b.math('MULTIPLY_ADD', r_shadow, 0.9, 0.55), variation)     # 0.55 .. 1.45 of the set darkness
    reach_factor = b.mixf(1.0, b.math('MULTIPLY_ADD', r_reach, 0.7, 0.65), variation)       # 0.65 .. 1.35 of the set reach
    lip_factor = b.mixf(1.0, b.math('MULTIPLY_ADD', r_lip, 1.2, 0.4), variation)            # 0.4 .. 1.6 of the set lip width

    # ------------------------------------------------------------------------------------------------ 5. EDGE DARKENING (the faintest, painted first)
    darken_reach = b.mul(S('Edge Darkening Width'), b.math('MULTIPLY_ADD', signed_a, 0.5, 1.0))
    darken_distance = b.div(edge_distance, b.mx(darken_reach, 1e-5))                      # 0 at the edge, 1 where the darkening ends
    edge_dark_strength = b.mul(b.mul(S('Edge Darkening'), b.sub(1.0, b.smoothstep(darken_distance, 0.0, 1.0))), piece_mask)

    # ------------------------------------------------------------------------------------------------ 3. SHADOW BAND (top of the slate, below the joint)
    reach = b.mul(b.mul(S('Shadow Width'), reach_factor), b.math('MULTIPLY_ADD', b.sub(drip_noise, 0.5), b.mul(S('Shadow Drip'), 2.0), 1.0))
    reach = b.mx(reach, 1e-5)
    tier_wander = seamless(b.mul(tiles, 30.0), b.mul(tiles, 30.0), 2.0, 0.5, 41.0)          # slow noise: every step border wanders a little on its own, so the steps are not exact copies of each other
    depth = b.maprange(b.div(top_edge_distance, reach), 0.0, 1.0, 1.0, 0.0, True)           # 1 right at the top edge, 0 at the end of the reach
    depth = b.math('MULTIPLY_ADD', b.sub(tier_wander, 0.5), b.mul(S('Shadow Drip'), 0.5), depth, clamp=True)
    depth = b.mul(depth, b.smoothstep(b.sub(1.0, b.div(top_edge_distance, reach)), 0.0, 0.02))   # still exactly 0 beyond the reach
    tiers = S('Shadow Tiers')
    stepped = b.div(b.floor(b.add(b.mul(depth, tiers), 0.9999)), b.mx(tiers, 1e-5))          # depth cut into flat steps: 1, 2/3, 1/3 for three tiers (0 stays 0)
    flat_or_smooth = b.gt(tiers, 0.5)
    shadow_shape = b.mixf(depth, stepped, flat_or_smooth)
    shadow_strength = b.mul(b.mul(b.mn(b.mul(S('Shadow Darkness'), shadow_factor), 1.0), shadow_shape), piece_mask)
    smooth_depth = b.smoothstep(depth, 0.0, 1.0)                                              # the same reach but smooth: used for the relief (a slope, not steps)

    # black drips: teeth of black that hang down from the black band into the shadow (the reference has them under most rows)
    teeth = seamless(b.mul(tiles, 50.0), b.mul(tiles, 28.0), 1.0, 0.5, 53.0)
    teeth_length = b.mul(S('Black Drips'), b.power(b.maprange(teeth, 0.58, 0.9, 0.0, 1.0, True), 1.2))
    drip_black = b.mul(hard(b.sub(teeth_length, top_edge_distance)), piece_mask)

    # ------------------------------------------------------------------------------------------------ 4. THE LIP (lower edge of the slate)
    outline_here = b.mul(S('Side Outline Width'), width_factor)                               # width of the thin outline here (wobbled)
    lip_from = b.mul(S('Lip Offset'), width_factor)
    lip_to = b.add(lip_from, b.mul(S('Lip Width'), lip_factor))
    inside_lip = b.mul(hard(b.sub(edge_distance, b.sub(lip_from, SOFT))), hard(b.sub(lip_to, edge_distance)))   # 1 between lip start and lip end
    break_from = b.sub(b.mul(S('Lip Breakup'), 0.7), 0.12)                                     # at Breakup 0 the threshold is below 0: nothing is broken
    unbroken = b.smoothstep(wobble_b, break_from, b.add(break_from, 0.12))                     # 1 where the lip is drawn, 0 in the gaps of the lip
    lip_here = b.mul(b.mul(inside_lip, bottom_weight), unbroken)
    lip_strength = b.mul(b.mul(S('Lip Brightness'), lip_here), piece_mask)

    # ------------------------------------------------------------------------------------------------ 2. SIDE OUTLINE
    outline_shape = hard(b.sub(outline_here, edge_distance))
    outline_strength = b.mul(b.mul(S('Side Outline Darkness'), outline_shape), piece_mask)

    # ------------------------------------------------------------------------------------------------ 1. BLACK JOINT (gap plus a ragged spill)
    spill = b.mul(b.mixf(S('Joint Width'), S('Band Width'), row_edge_weight), width_factor)
    spill_shape = hard(b.sub(spill, edge_distance))
    joint_strength = b.mx(b.mx(gap_mask, spill_shape), drip_black)

    # ------------------------------------------------------------------------------------------------ stack the paint: later ones lie on top
    colour, strength = S('Outline Colour'), edge_dark_strength                  # the faint edge darkening is first (it uses the outline colour)
    colour, strength = lay_over(colour, strength, S('Shadow Colour'), shadow_strength)
    colour, strength = lay_over(colour, strength, S('Lip Colour'), lip_strength)
    colour, strength = lay_over(colour, strength, S('Outline Colour'), outline_strength)
    colour, strength = lay_over(colour, strength, S('Joint Colour'), joint_strength)

    # ------------------------------------------------------------------------------------------------ relief and roughness
    # the shadow is a slope pushed DOWN under the joint; the lip a small rim UP; the outline a small groove DOWN; the joint is already low in base_height
    height = b.mul(b.mul(smooth_depth, S('Shadow Height')), b.mul(piece_mask, -1.0))
    height = b.add(height, b.mul(b.mul(lip_here, S('Lip Height')), piece_mask))
    height = b.sub(height, b.mul(b.mul(outline_shape, S('Outline Height')), piece_mask))
    roughness = b.mul(joint_strength, S('Joint Roughness'))
    roughness = b.add(roughness, b.mul(b.mul(shadow_shape, S('Shadow Roughness')), piece_mask))
    roughness = b.add(roughness, b.mul(b.mul(lip_here, S('Lip Roughness')), piece_mask))

    b.finish_layer(mask=strength, colour=colour, height=height, roughness=roughness)
    return tree
