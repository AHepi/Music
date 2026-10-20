# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# COLOUR AND FADE paints the BARE SLATES: each slate's own base tone, how the paint has faded and run down it in streaks, and the big
# sun-bleached and damp-darkened areas that cross several slates. It is the BOTTOM layer: COMBINE uses its Colour as the paint everywhere
# and the other layers (moss, damage, outline) paint over it. It uses no picture of any kind: everything is made of Blender nodes.
#
# THE IDEA IN ONE PICTURE. There is a short LIST OF PAINT COLOURS (the palette: nine blue-greys, darkest to lightest) and, for every dot,
# one number called the TONE STEP (0 = the darkest paint, 8 = the lightest). The tone step is a SUM of small pieces:
#     tone step = the slate's own base step          each slate rolls its own; a few land well above or below the rest
#               + tongues                            pointed tongues of darker paint hang from the top edge of the slate, tongues of
#                                                    lighter (bleached) paint reach up from the bottom edge: "dark above, bleached below"
#               + mottling                           tall flat patches of one tone each (stretched Voronoi cells), one step lighter or darker
#               + specks                             many small flat patches a few dots across
#               + big patches                        sun-bleached and damp areas that cross several slates (slow seamless noise, cut by thresholds)
# The dot is then painted with the palette colour at that step, ROUNDED to a whole number. Rounding is what makes the paint FLAT: a dot
# is never "between" two paints, so the picture is made of flat patches with hard edges. The setting 'patch_hardness' softens every hard
# edge (1 = hard painted edge, 0 = the tones blend smoothly). Some slates and some single patches then lean towards a greener or warmer
# grey (the tints), and a very faint grain keeps the flat patches from being perfectly flat.
#
# Which Blender tools are used (details in the guide): Noise Texture 1D (the pointed tongues), 2D (wobble, bend, specks, grain), Voronoi 2D
# set to Smooth F1 (the tall patches), the project's seamless 4D noise (the big patches that cross slates), White Noise (one set of random
# numbers per slate, from the slate's piece_id and this layer's seed), Map Range / Math / Mix nodes (the palette lookup is a short chain
# of "if the step is above this line take the next colour" Mix nodes, so every palette colour stays a live colour knob in the Shader editor).
#
# What the layer reads: the layout bundle only (piece_id, local_x, local_y, piece_width, piece_height, piece_mask), plus Vector and Tile
# Count. Streaks use the SLATE'S OWN coordinates (local_x x piece_width, local_y x piece_height, in tile units), so they start at the top
# of each slate; every slate gets its own pattern (the noise is offset by random numbers made from piece_id); and the pattern is the
# same wherever the slate is wrapped round the picture edge, so the tile still repeats exactly. The big patches read the seamless noise
# on Vector (times Tile Count), so they repeat exactly too and cross slates and joints.
#
# Outputs (fixed by ../interface/interface.md):
#   Mask      = FADE STRENGTH: 0 where the dot is just the slate's own base tone, up to 1 where the weathering has moved it three or more
#               tone steps. (This layer is the bottom of the stack, so COMBINE does not use the Mask: it is a debug picture.)
#   Colour    = the finished slate paint, fade applied, on every dot (joints get the colour their slate would have; OUTLINE covers them).
#   Height    = a relief that FOLLOWS THE TONE (lighter paint stands higher, as in the reference maps, whose height was made from the
#               colour). 0 for the slate's middle tone.
#   Roughness = lighter (bleached) paint a little rougher, darker paint a little smoother. 0 for the middle tone.
# Amount: 0 = no variation at all (every slate gets the one middle tone, no fade; Mask, Height and Roughness are exactly 0), 1 = full.
#
# All sizes are in TILE units (1.0 = the whole base tile). To think in dots at 1254 dots per tile multiply by 1254 (0.012 = 15 dots).
# Declared links: none. This layer reads nothing from any other layer.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layer_interface as li  # noqa: E402
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'colour_and_fade'
GROUP_NAME = 'COLOUR AND FADE'
DEFAULT_SEED = 11.0

# The palette, darkest to lightest: nine blue-greys in steps of about 11 brightness (22 to 112 of 255), a little bluer in the darks and greyer in
# the lights. Chosen by hand after ONE look at the reference (tests/colour_and_fade/measure_reference_character.py: its blue-grey paint runs from
# brightness 25 to 112, median 63, with cooler blue-greys and greener grey-greens at the same lightness). No colour is copied from any one spot.
PALETTE_DEFAULTS = ['#141719', '#1e2225', '#282d32', '#33393e', '#3d444a', '#475057', '#525b62', '#5d676d', '#687278']
PALETTE_NAMES = ['Tone 1 (darkest)', 'Tone 2', 'Tone 3', 'Tone 4', 'Tone 5', 'Tone 6', 'Tone 7', 'Tone 8', 'Tone 9 (lightest)']

CONTROLS = [Control(f'tone_{i + 1}', PALETTE_NAMES[i], PALETTE_DEFAULTS[i], kind='colour',
                    text='palette colour number %d of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine' % (i + 1))
            for i in range(9)]
CONTROLS += [
    Control('green_tint', 'Green Tint', '#4c5959', kind='colour', text='a greener grey that some slates lean towards (only its hue is used; its lightness is matched to the paint it tints)'),
    Control('warm_tint', 'Warm Tint', '#5d5a54', kind='colour', text='a warmer, browner grey that a few slates lean towards (only its hue is used)'),
    Control('tone_centre', 'Tone Centre', 3.6, 0.0, 8.0, 'the tone step of the average slate (0 = darkest palette colour, 8 = lightest; 3.6 puts the average slate on the fourth to fifth colour)'),
    Control('tone_spread', 'Tone Spread', 0.5, 0.0, 3.0, 'how different the base tones of the slates are, in tone steps (the typical slate is within this many steps of the centre)'),
    Control('outlier_share', 'Outlier Share', 0.08, 0.0, 0.6, 'share of slates that are clearly darker or lighter than the rest (they are pushed Outlier Size steps up or down)'),
    Control('outlier_size', 'Outlier Size', 1.8, 0.0, 4.0, 'how many tone steps an outlier slate is pushed up or down'),
    Control('tint_amount', 'Tint Amount', 0.5, 0.0, 1.0, 'how far the tinted slates lean towards the green or warm grey (0 = every slate is pure blue-grey)'),
    Control('tint_green_share', 'Tint Green Share', 0.8, 0.0, 1.0, 'of the tinted slates, the share that lean green (the rest lean warm)'),
    Control('patch_tint', 'Patch Tint', 0.4, 0.0, 1.0, 'how far some single paint patches lean towards the green grey (a blue slate with a few greener patches in it; 0 = patches differ only in lightness)'),
    Control('fade_amount', 'Fade Amount', 1.0, 0.0, 2.0, 'strength of the weathering inside each slate (the fade down the slate and the streaks); 0 = clean flat slates, 1 = like the reference, 2 = very weathered'),
    Control('fade_direction', 'Fade Direction', 1.0, -1.0, 1.0, 'which way the slate fades: 1 = dark under the slate above and bleached towards the bottom edge (the reference); -1 = the reverse (bleached above, darker below); 0 = no up-down trend, streaks only'),
    Control('fade_length', 'Fade Length', 0.07, 0.01, 0.4, 'how far the longest paint tongue runs down (or up) the slate, in tile units (0.07 = 88 dots, over half a slate; small = short stubby drips, large = streaks all the way down)'),
    Control('streak_width', 'Streak Width', 0.034, 0.004, 0.1, 'how wide one paint tongue / streak is, in tile units (0.034 = 43 dots)'),
    Control('streak_contrast', 'Streak Contrast', 1.15, 0.0, 3.0, 'how strongly the patches inside a slate differ from their neighbours, as a multiple of the usual (about one tone step); 0 = no mottling, only the fade'),
    Control('top_darkening', 'Top Darkening', 0.6, 0.0, 3.0, 'extra darkening of the first fifth of the slate, under the slate above, in tone steps (the fade keeps going darker upwards; OUTLINE AND SHADOW adds the thin shadow line)'),
    Control('speck_amount', 'Speck Amount', 0.9, 0.0, 2.0, 'strength of the many small paint specks (a speck is a flat patch of one tone step lighter or darker, a few dots across); 0 = none'),
    Control('speck_cover', 'Speck Cover', 0.10, 0.0, 0.6, 'roughly the share of each slate covered by specks'),
    Control('speck_size', 'Speck Size', 0.011, 0.003, 0.05, 'width of a speck in tile units (0.011 = 14 dots; they are a little taller than wide)'),
    Control('patch_hardness', 'Patch Hardness', 1.0, 0.0, 1.0, 'how hard the edge of each paint patch is: 1 = a clean step from one palette colour to the next (flat painted patches), 0 = the colours blend smoothly'),
    Control('streak_bend', 'Streak Bend', 0.024, 0.0, 0.05, 'how far a slow wander pushes the streaks and tongues sideways and up and down, in tile units (0.024 = 30 dots); 0 = perfectly straight patch edges, more = wavy, uneven tongue widths'),
    Control('edge_ragged', 'Edge Ragged', 0.0035, 0.0, 0.02, 'how far a fine wobble pushes every patch edge sideways, in tile units (0.0035 = 4 dots; 0 = smooth patch outlines)'),
    Control('bleach_amount', 'Sun Bleach Amount', 0.5, 0.0, 1.0, 'strength of the sun-bleached patches (areas of paler paint that cross several slates); 0 = none'),
    Control('bleach_cover', 'Sun Bleach Cover', 0.22, 0.0, 0.7, 'roughly the share of the picture covered by sun-bleached patches'),
    Control('stain_amount', 'Damp Stain Amount', 0.4, 0.0, 1.0, 'strength of the damp, darker patches that cross several slates; 0 = none'),
    Control('stain_cover', 'Damp Stain Cover', 0.18, 0.0, 0.7, 'roughly the share of the picture covered by damp darker patches'),
    Control('patch_size', 'Big Patch Size', 0.32, 0.08, 1.0, 'size of the sun-bleach and damp patches, in tile units (0.32 = about three patches across one tile)'),
    Control('drift_amount', 'Slow Drift', 0.25, 0.0, 2.0, 'a slow wave of lighter and darker over the whole roof, in tone steps (it makes neighbouring slates belong together)'),
    Control('grain_amount', 'Grain', 0.05, 0.0, 0.3, 'a very faint fine grain inside every flat patch (a share of the paint\'s brightness; the reference paint is not perfectly flat); 0 = perfectly flat paint'),
    Control('tone_height', 'Tone Height', 2.0, 0.0, 6.0, 'how much the relief follows the paint: the height change per unit of paint brightness (the reference height was made from its colour; 0 = no tone relief)'),
    Control('tone_roughness', 'Tone Roughness', 1.0, 0.0, 4.0, 'how much lighter paint is rougher and darker paint smoother (0 = no change of roughness with tone)'),
]
DECLARED_LINKS = []          # this layer reads nothing from any other layer


def palette_pick(b, step, colours):
    """The palette colour for a whole-number tone step (0..8): start with the darkest and, for every colour, switch to it once the step is above its line."""
    colour = colours[0]
    for index in range(1, len(colours)):
        colour = b.mix(colour, colours[index], b.gt(step, index - 0.5))
    return colour


def share_to_spread(b, share):
    """How many standard deviations above the middle you must cut a bell-shaped noise so that about `share` of the dots are above the cut
    (share 0.16 gives 1.0, share 0.5 gives 0). A short formula (Tukey's) built from two Power nodes, so a setting like 'cover 0.2' means roughly
    20 percent of the area whatever noise it is cut from. Noise values are not spread evenly: they bunch around 0.5."""
    return b.mul(b.sub(b.power(b.sub(1.0, share), 0.14), b.power(share, 0.14)), 4.91)


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    bundle = b.bundle()
    seed, amount, tiles, vector = S('Seed'), S('Amount'), S('Tile Count'), S('Vector')
    piece_id, local_y = bundle['piece_id'], bundle['local_y']
    colours = [S(name) for name in PALETTE_NAMES]
    last = float(len(colours) - 1)

    # ---------------------------------------------------------------------------------------------- 1. ONE SET OF RANDOM NUMBERS PER SLATE
    # White Noise of (piece_id, this layer's seed): the same for every dot of a slate, different for each slate and for each seed.
    rolls_a = b.hash4(b.vec(piece_id, b.mul(seed, 0.37), 0.31), 1.0)           # Color = three numbers for the tone bell, Value = outlier pick
    rolls_b = b.hash4(b.vec(piece_id, b.mul(seed, 0.37), 0.77), 2.0)           # Value = up or down, Color = tint pick, fade strength, tint family
    rolls_c = b.hash4(b.vec(piece_id, b.mul(seed, 0.37), 1.43), 3.0)           # Color + Value = where in the patch pattern this slate looks
    rolls_d = b.hash4(b.vec(piece_id, b.mul(seed, 0.37), 2.09), 4.0)           # the same for the other two patch sizes
    start_x, start_y, start_z = b.channels(rolls_c.outputs['Color'])
    start_w = rolls_c.outputs['Value']
    start_u, start_v, start_t = b.channels(rolls_d.outputs['Color'])
    tint_pick, fade_roll, side_roll = b.channels(rolls_b.outputs['Color'])

    # ---------------------------------------------------------------------------------------------- 2. THE SLATE'S OWN BASE TONE STEP
    bell = b.gauss_like(rolls_a.outputs['Color'])                                # mean 0, spread 1
    outlier = b.gt(rolls_a.outputs['Value'], b.sub(1.0, S('Outlier Share')))     # 1 for the few clearly darker or lighter slates
    outlier_sign = b.sub(b.mul(b.gt(rolls_b.outputs['Value'], 0.5), 2.0), 1.0)    # plus or minus
    slate_offset = b.add(b.mul(bell, S('Tone Spread')), b.mul(b.mul(outlier, outlier_sign), S('Outlier Size')))
    base_step = b.add(S('Tone Centre'), b.mul(slate_offset, amount))

    # ---------------------------------------------------------------------------------------------- 3. COORDINATES ON THE SLATE (tile units) AND THE RAGGED-EDGE WOBBLE
    across = b.mul(bundle['local_x'], bundle['piece_width'])                    # distance from the slate's left edge
    down = b.mul(local_y, bundle['piece_height'])                               # distance below the slate's top edge

    def flat_noise(scale_x, scale_y, offset_x, offset_y, detail):
        """Plain 2D noise on the slate's own coordinates (0..1, mostly 0.25..0.75). No seamless trick is needed: the slate carries its own
        coordinates, and the random offsets make every slate (and every use) read a different part of the noise."""
        place = b.vec(b.add(b.mul(across, scale_x), b.mul(offset_x, 100.0)), b.add(b.mul(down, scale_y), b.mul(offset_y, 100.0)), 0.0)
        return b.noise(place, 1.0, detail, 0.5, 0.0, None, '2D').outputs['Factor']

    wobble_scale = 70.0                                                         # wobbles per tile unit: 70 = a wobble about 18 dots long
    push_x = b.mul(b.sub(flat_noise(wobble_scale, wobble_scale, start_x, start_y, 1.0), 0.5), b.mul(S('Edge Ragged'), 2.3))      # noise sits near 0.5: about plus/minus Edge Ragged
    push_y = b.mul(b.sub(flat_noise(wobble_scale, wobble_scale, start_z, start_w, 1.0), 0.5), b.mul(S('Edge Ragged'), 2.3))
    # a slower wander (about 90 dots between wobbles) that bends the streaks so that no patch edge is a ruler-straight line
    wander_x = b.mul(b.sub(flat_noise(11.0, 11.0, start_u, start_v, 0.0), 0.5), b.mul(S('Streak Bend'), 1.6))
    wander_y = b.mul(b.sub(flat_noise(11.0, 11.0, start_t, start_y, 0.0), 0.5), b.mul(S('Streak Bend'), 0.8))
    across_w = b.add(across, push_x)                    # for the tongues: only the fine ragged wobble
    down_w = b.add(down, push_y)
    across_b = b.add(across_w, wander_x)                # for the mottling: also the slow wander
    down_b = b.add(down_w, wander_y)

    # ---------------------------------------------------------------------------------------------- 4. FADE DOWN THE SLATE: TONGUES AND MOTTLING
    # (a) TONGUES. Paint runs down a slate in pointed tongues. Along the top edge of the slate, a row of tongues of random length hangs
    # down; inside each tongue the paint is one step darker. A second row of shorter tongues is darker again. From the bottom edge a row of
    # tongues reaches UP and is lighter (bleached). The row of tongues is a 1D noise made pointy: 1 - |2 noise - 1| has sharp peaks, and
    # each peak is the tip of a tongue. Fade Direction -1 swaps the two (light tongues from the top, dark ones from the bottom).
    fade_gain = b.mul(S('Fade Amount'), amount)
    direction = S('Fade Direction')
    strength = b.add(1.0, b.mul(b.sub(fade_roll, 0.5), 0.6))                                   # each slate fades a little more or less
    width, length = b.mx(S('Streak Width'), 1e-4), b.mx(S('Fade Length'), 1e-4)
    height_of_slate = bundle['piece_height']
    # PATCH HARDNESS: every hard edge below is a "below / above a line" test. With hardness 1 it is a true step (flat patches, hard edges);
    # with less hardness the step is stretched into a ramp, so the edge of a patch fades out over `soft_length` (tile units) or `soft_noise`
    # (noise units) and the tones blend. (Edges made by the colour rounding itself and by the Voronoi cells are softened too, see below.)
    softness = b.sub(1.0, S('Patch Hardness'))
    soft_length = b.add(b.mul(softness, 0.012), 1e-5)        # 0.012 tile units = 15 dots
    soft_noise = b.add(b.mul(softness, 0.04), 1e-5)

    def below(value, line, soft):
        """1 where value < line, 0 where value > line; a ramp of total width 2 x soft across the line (a hard step when soft is tiny)."""
        return b.smoothstep(b.sub(line, value), b.mul(soft, -1.0), soft)

    def tongue_reach(offset, longest, narrowness):
        """How far (tile units) a tongue at this x reaches into the slate: pointed tips, random lengths."""
        along = b.div(b.add(b.add(across_w, b.mul(wander_x, 0.4)), offset), b.mul(width, narrowness))
        raw = b.noise(None, 1.0, 2.0, 0.55, 0.0, along, '1D').outputs['Factor']
        pointy = b.sub(1.0, b.absolute(b.sub(b.mul(b.maprange(raw, 0.27, 0.73, 0.0, 1.0, True), 2.0), 1.0)))
        return b.mul(b.mul(longest, strength), b.add(0.10, b.mul(b.power(pointy, 2.0), 0.90)))

    up_from_bottom = b.sub(height_of_slate, down_w)
    from_top_long = below(down_w, tongue_reach(b.mul(start_x, 37.0), length, 1.0), soft_length)
    from_top_short = below(down_w, tongue_reach(b.mul(start_y, 37.0), b.mul(length, 0.5), 0.7), soft_length)
    from_bottom_long = below(up_from_bottom, tongue_reach(b.mul(start_z, 37.0), b.mul(length, 0.85), 0.9), soft_length)
    from_bottom_short = below(up_from_bottom, tongue_reach(b.mul(start_w, 37.0), b.mul(length, 0.4), 0.6), soft_length)
    top_band = below(down_w, b.mul(b.mul(length, 0.16), b.add(0.7, b.mul(fade_roll, 0.6))), soft_length)     # the shadow of the slate above: a flat dark band with a ragged edge
    tongue_steps = b.mul(direction, b.sub(b.add(b.mul(from_bottom_long, 0.7), b.mul(from_bottom_short, 0.6)),
                                          b.add(b.mul(from_top_long, 0.8), b.mul(from_top_short, 0.7))))
    band_steps = b.mul(b.mul(top_band, S('Top Darkening')), b.mul(b.absolute(direction), -1.0))

    # (b) MOTTLING. Tall Voronoi cells in the slate's own coordinates, each cell one flat random tone change.
    def mottle(size, tallness, offset_x, offset_y, contrast, coverage):
        coordinate = b.vec(b.div(b.add(across_b, offset_x), b.mul(width, size)), b.div(b.add(down_b, offset_y), b.mul(length, b.mul(size, tallness))), 0.0)
        cell = b.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='SMOOTH_F1', distance='EUCLIDEAN', normalize=False)          # Smooth F1 with Smoothness 0 is exactly F1 (hard cells; checked)
        b._put(cell, 'Vector', coordinate)
        b._put(cell, 'Scale', 1.0)
        b._put(cell, 'Randomness', 1.0)
        b._put(cell, 'Smoothness', b.mul(softness, 0.5))
        random_change, random_cover, random_tint = b.channels(cell.outputs['Color'])
        change = b.mul(b.mul(b.sub(random_change, 0.5), 2.0), contrast)
        return b.mul(change, b.gt(random_cover, b.sub(1.0, coverage))), random_tint

    contrast = S('Streak Contrast')
    mottling_medium, patch_tint_roll = mottle(1.5, 2.2, b.mul(start_u, 41.0), b.mul(start_v, 41.0), b.mul(contrast, 1.1), 1.0)
    mottling = mottling_medium
    # (c) SPECKS. Many small flat patches, a few dots across: thresholded noise (the top part of the noise only), each one a step lighter or darker.
    speck_scale = b.div(1.0, b.mx(S('Speck Size'), 1e-4))
    speck_place = b.vec(b.add(b.mul(across_b, speck_scale), b.mul(start_w, 100.0)), b.add(b.mul(down_b, b.div(speck_scale, 1.6)), b.mul(start_t, 100.0)), 0.0)
    speck_presence = b.noise(speck_place, 1.0, 1.0, 0.5, 0.0, None, '2D').outputs['Factor']
    speck_sign = b.noise(b.vmath('ADD', speck_place, (37.0, 91.0, 0.0)), 1.0, 0.0, 0.5, 0.0, None, '2D').outputs['Factor']
    speck_on = b.smoothstep(speck_presence, b.sub(b.math('MULTIPLY_ADD', share_to_spread(b, S('Speck Cover')), 0.119, 0.5), soft_noise),
                            b.add(b.math('MULTIPLY_ADD', share_to_spread(b, S('Speck Cover')), 0.119, 0.5), soft_noise))      # 2D noise, one extra octave: spread 0.119
    speck_steps = b.mul(b.mul(speck_on, b.sub(b.mul(b.gt(speck_sign, 0.5), 2.0), 1.0)), S('Speck Amount'))
    fade_steps = b.mul(b.add(b.add(tongue_steps, band_steps), b.add(mottling, speck_steps)), fade_gain)

    # ---------------------------------------------------------------------------------------------- 5. BIG PATCHES THAT CROSS SLATES (seamless on Vector)
    # One slow seamless noise over the whole picture, cut by thresholds: the top part of the noise is sun-bleached paint, the bottom
    # part is damp, darker paint, the middle is left alone. Because it is read on Vector (the tile coordinate times Tile Count) it repeats
    # exactly at the tile edge and it crosses slates and joints. The coordinate is shaken by the same fine wobble as the streaks (three
    # times as strong), so the outline of a patch is ragged like a paint edge and not a smooth blob.
    shaken = b.vmath('ADD', vector, b.vec(b.mul(push_x, 3.0), b.mul(push_y, 3.0), 0.0))
    patch_features = b.div(tiles, b.mx(S('Big Patch Size'), 1e-3))
    field = b.tileable_noise(shaken, patch_features, 2.0, 0.55, b.add(b.mul(seed, 5.3), 17.0))       # seamless noise, spread about 0.078 around 0.5
    bleach_line = b.math('MULTIPLY_ADD', share_to_spread(b, S('Sun Bleach Cover')), 0.078, 0.5)
    damp_line = b.math('MULTIPLY_ADD', share_to_spread(b, b.sub(1.0, S('Damp Stain Cover'))), 0.078, 0.5)
    bleached = b.smoothstep(field, b.sub(bleach_line, b.mul(soft_noise, 0.75)), b.add(bleach_line, b.mul(soft_noise, 0.75)))
    damp = below(field, damp_line, b.mul(soft_noise, 0.75))
    patch_steps = b.mul(b.sub(b.mul(bleached, S('Sun Bleach Amount')), b.mul(damp, b.mul(S('Damp Stain Amount'), 0.9))), amount)
    drift_steps = b.mul(b.mul(b.sub(field, 0.5), 5.0), b.mul(S('Slow Drift'), amount))

    # ---------------------------------------------------------------------------------------------- 6. ADD IT UP AND PAINT FROM THE PALETTE
    step = b.sum_of([base_step, fade_steps, patch_steps, drift_steps])
    step = b.maprange(step, 0.0, last - 1e-3, 0.0, last - 1e-3, True)                  # keep it inside the palette
    lower = b.floor(step)
    fraction = b.sub(step, lower)
    blend_half = b.mx(b.mul(b.sub(1.0, S('Patch Hardness')), 0.5), 1e-4)
    blend = b.smoothstep(fraction, b.sub(0.5, blend_half), b.add(0.5, blend_half))
    paint = b.mix(palette_pick(b, lower, colours), palette_pick(b, b.add(lower, 1.0), colours), blend)

    # a lean towards a greener or warmer grey (lightness matched, so it changes the hue and not the tone): first some single patches
    # (green only), then a few whole slates (green or warm)
    def lean_towards(colour_in, tint_colour, strength):
        light = b.mx(b.brightness(colour_in), 1e-4)
        target_light = b.mx(b.brightness(tint_colour), 1e-4)
        matched = b.vmath('SCALE', tint_colour, None, b.div(light, target_light))
        return b.mix(colour_in, matched, strength)

    patch_green = b.mul(b.gt(patch_tint_roll, 0.6), b.mul(b.add(0.5, b.mul(b.sub(patch_tint_roll, 0.6), 1.25)), b.mul(S('Patch Tint'), amount)))
    paint = lean_towards(paint, S('Green Tint'), patch_green)
    tinted = b.gt(tint_pick, 0.35)
    tint_strength = b.mul(b.mul(tinted, b.mul(b.sub(tint_pick, 0.35), 1.0 / 0.65)), b.mul(S('Tint Amount'), amount))
    tint_colour = b.mix(S('Warm Tint'), S('Green Tint'), b.gt(side_roll, b.sub(1.0, S('Tint Green Share'))))
    painted = lean_towards(paint, tint_colour, tint_strength)
    # a very faint fine grain (a few dots across) so that flat patches are not perfectly flat; per slate, so it needs no seamless noise
    grain = flat_noise(240.0, 240.0, start_u, start_v, 0.0)
    colour = b.vmath('SCALE', painted, None, b.add(1.0, b.mul(b.mul(b.sub(grain, 0.5), 4.0), b.mul(S('Grain'), amount))))

    # ---------------------------------------------------------------------------------------------- 7. THE OTHER OUTPUTS
    middle = palette_pick(b, b.floor(b.add(S('Tone Centre'), 0.5)), colours)
    tone_shift = b.sub(b.height_from_colour(colour), b.height_from_colour(middle))      # screen brightness against the middle tone
    height = b.mul(b.mul(tone_shift, S('Tone Height')), bundle['piece_mask'])
    roughness = b.mul(b.mul(tone_shift, S('Tone Roughness')), bundle['piece_mask'])
    moved = b.sub(step, base_step)
    fade_strength = b.mul(b.maprange(b.absolute(moved), 0.0, 3.0, 0.0, 1.0, True), bundle['piece_mask'])
    b.finish_layer(mask=fade_strength, colour=colour, height=height, roughness=roughness, apply_amount=False)
    return tree
