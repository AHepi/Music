# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# GRIME is the one NEW paint layer of the brick trial. It paints the two things no shared layer can paint, because MOSS and DAMAGE stop at
# the edge of a brick (they multiply by piece_mask) and COLOUR AND FADE lies under the mortar paint:
#   1. MOTTLE   the mortar is not one flat colour: flat patches of a paler, a palest and a darker mortar tone, a few dots across and a little
#               wider than tall (they follow the joints). Painted ONLY where the layout says "gap" (gap_mask = 1).
#   2. SOOT     dark clouds that run down the wall over bricks AND mortar alike: a slow seamless noise stretched up-down (taller than wide),
#               roughened by a finer up-down streak noise, gives each cloud a solid middle and a soft rim; a fine grain noise then breaks
#               the rim into flat specks, so a cloud dissolves into stipple (two flat tones: a lighter soot that lets the brick show through
#               a little, and a darker heart). The threshold comes from a "cover" share, the way COLOUR AND FADE does it, so
#               'soot_cover 0.2' means roughly 20 percent of the picture.
# The soot is painted over the mottle inside this layer, and the result is handed out as ONE Mask and ONE Colour (the same "over" rule
# OUTLINE AND SHADOW uses), so COMBINE can stack it LAST, over everything.
#
# What it reads: Vector, Tile Count, gap_mask and its own controls and Seed. It never looks at another layer (no declared links).
# Sockets: exactly the shared layer interface (layer_interface.make_layer_group): Vector, Tile Count, the eleven bundle numbers, Seed, Amount,
# its own controls; outputs Mask, Colour, Height, Roughness. Amount 0 = Mask, Height and Roughness exactly 0 (finish_layer).
# Seamless: every noise is read on a "donut" made from Vector (the tile coordinate turned into circles), with a feature count of
# (features per tile x Tile Count), so the tile repeats exactly and a 2 x 2 area has the same look per dot.
# Sizes are TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.008 = 10 dots).
# Height: the mottle lifts pale mortar a little and sinks dark mortar a little; soot changes no height (it is a stain). With COMBINE's
# tone_blend 1 the finished height follows the finished brightness anyway.
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'grime'
GROUP_NAME = 'GRIME'
DEFAULT_SEED = 51.0
TWO_PI = 6.2831853
SOFT = 0.012                 # soft width of a threshold in noise units (a thin, about one-dot ramp at the edge of a flat patch)

CONTROLS = [
    # ---- soot clouds (over bricks and mortar)
    Control('soot_cover', 'Soot Cover', 0.12, 0.0, 0.8, 'roughly the share of the whole picture under soot, bricks and mortar alike (0 = no soot)'),
    Control('soot_dark_share', 'Soot Dark Share', 0.45, 0.0, 1.0, 'of the soot, roughly the share that is the darker heart'),
    Control('soot_size', 'Soot Size', 0.09, 0.02, 1.0, 'width of one soot cloud, in tile units (0.09 = 113 dots)'),
    Control('soot_tallness', 'Soot Tallness', 1.8, 0.5, 6.0, 'how much taller than wide a soot cloud is (1 = round; 2 = runs down the wall)'),
    Control('soot_streaks', 'Soot Streaks', 0.5, 0.0, 2.0, 'how much a fine up-down streak noise breaks the cloud edges into runs and drips (0 = smooth cloud edges)'),
    Control('streak_width', 'Streak Width', 0.012, 0.002, 0.05, 'width of one fine soot run, in tile units (0.012 = 15 dots); they are about four times taller than wide'),
    Control('soot_softness', 'Soot Softness', 0.04, 0.001, 0.2, 'how wide the fading rim of a soot cloud is, in noise units (0.04 = a rim about a third of the cloud; small = hard-edged blobs)'),
    Control('soot_grain', 'Soot Grain', 0.007, 0.002, 0.05, 'size of the flat specks a soot cloud dissolves into at its rim, in tile units (0.007 = 9 dots)'),
    Control('soot_strength', 'Soot Strength', 0.7, 0.0, 1.0, 'how strongly the lighter soot covers what is under it (the dark heart covers fully at 1)'),
    Control('soot_heart_strength', 'Soot Heart Strength', 0.95, 0.0, 1.0, 'how strongly the dark heart of the soot covers what is under it'),
    Control('soot_colour', 'Soot Colour', '#45332b', kind='colour', text='the lighter soot: a dark brown-black'),
    Control('soot_colour_dark', 'Soot Colour Dark', '#2c221e', kind='colour', text='the darker heart of the soot'),
    # ---- mortar mottle (only in the gaps)
    Control('mottle_amount', 'Mottle Amount', 1.0, 0.0, 1.0, 'how strongly the mottle patches cover the flat mortar colour (0 = flat mortar)'),
    Control('mottle_size', 'Mottle Size', 0.009, 0.002, 0.05, 'width of one mottle patch, in tile units (0.009 = 11 dots)'),
    Control('mottle_stretch', 'Mottle Stretch', 1.5, 0.3, 4.0, 'how much wider than tall a mottle patch is (1.5 = a little wider: the patches follow the joints)'),
    Control('pale_cover', 'Pale Cover', 0.22, 0.0, 0.8, 'share of the mortar painted the pale mortar tone'),
    Control('palest_cover', 'Palest Cover', 0.07, 0.0, 0.5, 'share of the mortar painted the palest tone (inside the pale patches)'),
    Control('dark_cover', 'Dark Cover', 0.22, 0.0, 0.8, 'share of the mortar painted the darker, dirty mortar tone'),
    Control('pale_colour', 'Pale Colour', '#8e7259', kind='colour', text='the pale mortar tone'),
    Control('palest_colour', 'Palest Colour', '#a48669', kind='colour', text='the palest mortar tone (fresh lime)'),
    Control('dark_colour', 'Dark Colour', '#5e483a', kind='colour', text='the darker, dirty mortar tone'),
    # ---- relief and roughness
    Control('mottle_height', 'Mottle Height', 0.03, 0.0, 0.3, 'how much pale mortar stands up and dark mortar sinks (height scale 0..1)'),
    Control('mottle_roughness', 'Mottle Roughness', 0.05, -1.0, 1.0, 'roughness change in the mortar where the mottle paints'),
    Control('soot_roughness', 'Soot Roughness', -0.04, -1.0, 1.0, 'roughness change under soot (minus = a little smoother)'),
]
DECLARED_LINKS = []          # GRIME reads no other layer


def share_to_spread(b, share):
    """How many standard deviations above the middle a bell-shaped noise must be cut so that about `share` of the dots lie above the cut
    (Tukey's short formula; the same one COLOUR AND FADE uses)."""
    return b.mul(b.sub(b.power(b.sub(1.0, share), 0.14), b.power(share, 0.14)), 4.91)


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    tiles, seed = S('Tile Count'), S('Seed')
    gap_mask = S('gap_mask')

    # the donut: the four circle numbers are worked out once and shared by every noise below
    u, v, _ = b.xyz(S('Vector'))
    turns_u, turns_v = b.mul(u, TWO_PI), b.mul(v, TWO_PI)
    cos_u, sin_u = b.math('COSINE', turns_u), b.math('SINE', turns_u)
    cos_v, sin_v = b.math('COSINE', turns_v), b.math('SINE', turns_v)

    def seamless(scale_u, scale_v, detail, roughness, offset):
        """Seamless noise (about 0.3..0.7 around 0.5). scale_u / scale_v = how many features fit across the whole picture left-right / up-down."""
        shift = b.add(b.mul(seed, 7.3), offset)
        radius_u, radius_v = b.mul(scale_u, 1.0 / TWO_PI), b.mul(scale_v, 1.0 / TWO_PI)
        position = b.vec(b.mul(cos_u, radius_u), b.mul(sin_u, radius_u), b.mul(cos_v, radius_v))
        return b.noise(position, 1.0, detail, roughness, 0.0, b.math('MULTIPLY_ADD', sin_v, radius_v, shift), '4D', 'FBM', 2.0).outputs['Factor']

    def above(field, share, spread):
        """1 where the noise is in its top `share` (a flat patch with a thin soft edge), 0 elsewhere. spread = the noise's usual spread."""
        line = b.math('MULTIPLY_ADD', share_to_spread(b, share), spread, 0.5)
        return b.smoothstep(field, b.sub(line, SOFT * 0.5), b.add(line, SOFT * 0.5))

    def lay_over(under_colour, under_strength, colour, strength):
        """Paint `colour` with `strength` over what is already painted; returns (colour, strength) - the usual 'over' rule."""
        total = b.sub(1.0, b.mul(b.sub(1.0, under_strength), b.sub(1.0, strength)))
        share = b.div(strength, b.mx(total, 1e-6))
        return b.mix(under_colour, colour, share), total

    # ------------------------------------------------------------------------------------------------ 1. MOTTLE (gaps only)
    mottle_across = b.div(tiles, b.mx(b.mul(S('Mottle Size'), S('Mottle Stretch')), 1e-4))     # features across the picture (wider patches)
    mottle_updown = b.div(tiles, b.mx(S('Mottle Size'), 1e-4))
    tone_field = seamless(mottle_across, mottle_updown, 2.0, 0.5, 11.0)                     # one field: high = pale, low = dark
    pale = above(tone_field, S('Pale Cover'), 0.09)
    palest = above(tone_field, S('Palest Cover'), 0.09)
    dark = above(b.sub(1.0, tone_field), S('Dark Cover'), 0.09)
    in_gap = b.mul(gap_mask, S('Mottle Amount'))
    colour, strength = S('Pale Colour'), b.mul(pale, in_gap)
    colour, strength = lay_over(colour, strength, S('Palest Colour'), b.mul(palest, in_gap))
    colour, strength = lay_over(colour, strength, S('Dark Colour'), b.mul(dark, in_gap))
    mottle_height = b.mul(b.mul(b.sub(b.add(pale, palest), dark), S('Mottle Height')), gap_mask)
    mottle_rough = b.mul(b.mx(b.mx(pale, dark), palest), b.mul(gap_mask, S('Mottle Roughness')))

    # ------------------------------------------------------------------------------------------------ 2. SOOT (everywhere)
    # (a) where the soot clouds are: a slow noise stretched up-down, roughened by fine up-down runs, turned into a DENSITY 0..1 that rises from
    #     0 to 1 across a soft band around the cover threshold (Soot Softness wide), so a cloud has a solid middle and a fading rim.
    # (b) how it is painted: a fine grain noise (Soot Grain size) is compared with the density: a dot is sooty where grain < density. In the
    #     middle of a cloud almost every dot is sooty; near the rim only the low spots of the grain are, so the cloud dissolves into
    #     flat specks (the stippled, mottled look of the reference soot) instead of ending in a hard line. The dark heart is the same test
    #     with a density pushed down by (1 - Soot Dark Share), so it only appears in the middle of the thicker clouds.
    soot_across = b.div(tiles, b.mx(S('Soot Size'), 1e-3))
    soot_updown = b.div(soot_across, b.mx(S('Soot Tallness'), 0.1))
    cloud = seamless(soot_across, soot_updown, 3.0, 0.55, 23.0)
    streak_across = b.div(tiles, b.mx(S('Streak Width'), 1e-4))
    streaks = seamless(streak_across, b.mul(streak_across, 0.25), 2.0, 0.6, 37.0)          # fine runs, four times taller than wide
    field = b.math('MULTIPLY_ADD', b.sub(streaks, 0.5), b.mul(S('Soot Streaks'), 0.5), cloud)
    line = b.math('MULTIPLY_ADD', share_to_spread(b, S('Soot Cover')), 0.085, 0.5)
    density = b.smoothstep(field, b.sub(line, S('Soot Softness')), b.add(line, S('Soot Softness')))
    grain_across = b.div(tiles, b.mx(S('Soot Grain'), 1e-4))
    grain = b.maprange(seamless(grain_across, b.mul(grain_across, 0.7), 2.0, 0.6, 61.0), 0.32, 0.68, 0.0, 1.0, True)
    soot = b.smoothstep(b.sub(density, grain), 0.0, 0.04)
    heart = b.smoothstep(b.sub(b.sub(density, b.sub(1.0, S('Soot Dark Share'))), grain), 0.0, 0.04)
    colour, strength = lay_over(colour, strength, S('Soot Colour'), b.mul(soot, S('Soot Strength')))
    colour, strength = lay_over(colour, strength, S('Soot Colour Dark'), b.mul(heart, S('Soot Heart Strength')))

    roughness = b.add(mottle_rough, b.mul(soot, S('Soot Roughness')))
    b.finish_layer(mask=strength, colour=colour, height=mottle_height, roughness=roughness)
    return tree
