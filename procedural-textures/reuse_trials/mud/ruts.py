# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# RUTS is a NEW paint layer for the mud trial (no shared layer can draw long winding bands). It paints the wheel ruts: long, wandering dark
# bands with a thin darker groove down the middle, a lighter bank beside them (on the side the light comes from) and thin grey-blue wet
# streaks inside. It has exactly the same sockets as every shared layer (Vector, Tile Count, the eleven layout numbers, Seed, Amount, then
# its own controls; outputs Mask, Colour, Height, Roughness), so the recipe wires it like the others.
#
# How a rut is made (two families of ruts; each family is the same recipe with another direction):
#   1. STRIPES. Take a straight-line coordinate s = a x u + b x v with WHOLE numbers a and b (for example 3 u + v). Whole numbers matter:
#      s then grows by a whole number across the tile, so the stripes meet themselves at the tile edge and the tile repeats. Lines where
#      s is a whole number are straight, parallel rut centre lines (their direction is set by a and b).
#   2. MEANDER. A slow seamless noise pushes s about (Meander), so the straight lines bend into S-shaped curves.
#   3. WHERE THEY EXIST. A second slow seamless noise decides how wide each rut is along its length: wide where the noise is high, thin where
#      it is lower, gone where it is low (Cover says how much of the picture holds ruts). So ruts start and end instead of crossing the whole tile.
#   4. THE PARTS. Distance from the centre line d (tile units): the BAND is where d is under half the band width; the GROOVE is the middle of the
#      band; the BANK is a strip just outside the band on one side (Bank Side); WET STREAKS are thin short lines that wander inside the band
#      (their length and position come from a seamless noise read ALONG the rut, with another line for every rut).
#   5. COLOUR AND RELIEF. The band is painted in three flat dark earth tones (a fine seamless noise cut into flat steps, so the band is made of
#      dark clods and not one flat colour), the groove darker, the bank paler earth, the streaks blue-grey. The band and groove sink the
#      surface, the bank raises it, the streaks are smoother (wet).
# What it reads: Vector, Tile Count, its own controls and seed. Nothing from the layout bundle is needed (the bundle sockets are there because
# every layer has them). It reads no other layer. Amount 0 switches it off (the shared finish_layer guarantees Mask, Height and Roughness 0).
# Sizes are TILE units (1.0 = the base tile; at 1254 dots 0.016 = 20 dots).
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'ruts'
GROUP_NAME = 'RUTS'
DEFAULT_SEED = 51.0

# the two families: (a, b) of the stripe coordinate s = a u + b v, and (c, d) of the "along the rut" coordinate t = c u + d v (a d - b c = -1 or 1, so
# (s, t) is a whole-number mix of (u, v) and both repeat with the tile). Family 1: centre lines run along (1, -3) = steeply down to the right.
# Family 2: centre lines run along (3, -1) = gently down to the right.
FAMILIES = [((3, 1), (1, 0)), ((1, 3), (0, 1))]
SPACING = 3.1623            # sqrt(3^2 + 1^2): how many stripe units fit in one tile-length across a stripe, so d (tile units) = stripe units / SPACING

CONTROLS = [
    Control('steep_cover', 'Steep Cover', 0.5, 0.0, 1.0, 'how much of the picture holds ruts of the steep family (0 = none, 1 = ruts run the whole length)'),
    Control('gentle_cover', 'Gentle Cover', 0.35, 0.0, 1.0, 'how much of the picture holds ruts of the gentle family (0 = none)'),
    Control('band_width', 'Band Width', 0.016, 0.002, 0.05, 'width of the dark band of a rut where it is widest, in tile units (0.016 = 20 dots; the reference ruts are about 20 dots)'),
    Control('groove_share', 'Groove Share', 0.3, 0.0, 0.8, 'width of the darker groove in the middle of the band, as a share of the band width'),
    Control('bank_share', 'Bank Share', 0.4, 0.0, 1.5, 'width of the lighter bank beside the band, as a share of the band width (0 = no bank)'),
    Control('bank_side', 'Bank Side', 1.0, -1.0, 1.0, 'which side of the rut the lit bank is on: 1 = one side, -1 = the other (the light comes from the upper left)'),
    Control('meander', 'Meander', 1.1, 0.0, 3.0, 'how far the ruts wander sideways, in rut spacings (0 = straight lines, 1 = S-shaped curves)'),
    Control('meander_features', 'Meander Features', 2.5, 0.5, 12.0, 'how many wanders fit across one base tile'),
    Control('presence_features', 'Presence Features', 4.0, 1.0, 20.0, 'how many stretches of rut and gap fit across one base tile'),
    Control('streak_amount', 'Streak Amount', 0.55, 0.0, 1.0, 'how much of the band holds wet blue-grey streaks (0 = none)'),
    Control('streak_width', 'Streak Width', 0.0022, 0.0005, 0.01, 'width of a wet streak, in tile units (0.0022 = 2.8 dots)'),
    Control('clod_features', 'Clod Features', 140.0, 20.0, 400.0, 'how many dark clods (noise features) fit across one base tile inside the band'),
    Control('band_colour_dark', 'Band Colour Dark', '#2a1b16', kind='colour', text='the darkest earth tone of the band'),
    Control('band_colour', 'Band Colour', '#3a271f', kind='colour', text='the middle earth tone of the band'),
    Control('band_colour_light', 'Band Colour Light', '#4c3326', kind='colour', text='the lightest earth tone of the band'),
    Control('groove_colour', 'Groove Colour', '#150f0d', kind='colour', text='the near-black groove in the middle of the band'),
    Control('bank_colour_dark', 'Bank Colour Dark', '#6a4632', kind='colour', text='the darkest earth tone of the lit bank'),
    Control('bank_colour', 'Bank Colour', '#7a523b', kind='colour', text='the middle earth tone of the lit bank'),
    Control('bank_colour_light', 'Bank Colour Light', '#94684b', kind='colour', text='the lightest (palest) earth tone of the lit bank'),
    Control('streak_colour', 'Streak Colour', '#535e67', kind='colour', text='the blue-grey of the wet streaks'),
    Control('band_sink', 'Band Sink', 0.10, 0.0, 0.4, 'how far the band sinks the surface (0..1 relief scale); the groove sinks it half as much again'),
    Control('bank_raise', 'Bank Raise', 0.05, 0.0, 0.3, 'how far the bank rises (0..1 relief scale)'),
]
DECLARED_LINKS = []          # RUTS reads no other layer

SOFT = 0.0008                # soft width of every painted edge, in tile units (0.0008 = one dot): painted look = hard edges


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    tiles, seed, vector = S('Tile Count'), S('Seed'), S('Vector')
    u, v, _ = b.xyz(vector)
    big_u, big_v = b.mul(u, tiles), b.mul(v, tiles)           # position across the whole picture, in base-tile units

    def hard(value):
        """1 where `value` (a distance in tile units) is above 0, with a one-dot soft edge."""
        return b.smoothstep(value, 0.0, SOFT)

    clod_noise = b.tileable_noise(vector, b.mul(S('Clod Features'), tiles), 1.0, 0.5, b.add(b.mul(seed, 1.3), 3.0))
    dark_step = b.gt(clod_noise, 0.47)                         # three flat dark tones: below 0.47, 0.47 to 0.53, above 0.53
    light_step = b.gt(clod_noise, 0.53)
    band_colour = b.mix(b.mix(S('Band Colour Dark'), S('Band Colour'), dark_step), S('Band Colour Light'), light_step)
    bank_colour = b.mix(b.mix(S('Bank Colour Dark'), S('Bank Colour'), dark_step), S('Bank Colour Light'), light_step)

    mask_all = None
    colour = None
    sunk = None
    smooth = None
    for index, (across_pair, along_pair) in enumerate(FAMILIES):
        cover = S('Steep Cover') if index == 0 else S('Gentle Cover')
        phase = b.mul(seed, 0.137 + 0.071 * index)
        stripe = b.add(b.add(b.mul(big_u, float(across_pair[0])), b.mul(big_v, float(across_pair[1]))), phase)
        along = b.add(b.mul(big_u, float(along_pair[0])), b.mul(big_v, float(along_pair[1])))
        wander = b.tileable_noise(vector, b.mul(S('Meander Features'), tiles), 3.0, 0.5, b.add(b.mul(seed, 2.1), 11.0 + 17.0 * index))
        fine = b.tileable_noise(vector, b.mul(tiles, 45.0), 2.0, 0.5, b.add(b.mul(seed, 2.7), 23.0 + 5.0 * index))
        bent = b.add(b.add(stripe, b.mul(b.mul(b.sub(wander, 0.5), 2.0), S('Meander'))), b.mul(b.sub(fine, 0.5), 0.12))
        centre_offset = b.sub(b.frac(b.add(bent, 0.5)), 0.5)                                  # -0.5 .. 0.5 stripe units; 0 on a centre line
        signed = b.div(centre_offset, SPACING)                                                 # tile units
        distance = b.absolute(signed)
        stripe_number = b.floor(b.add(bent, 0.5))                                              # which rut of the family (the same across a band)

        presence = b.tileable_noise(vector, b.mul(S('Presence Features'), tiles), 2.0, 0.5, b.add(b.mul(seed, 1.7), 31.0 + 13.0 * index))
        line = b.sub(0.62, b.mul(cover, 0.22))
        width_factor = b.smoothstep(presence, b.sub(line, 0.07), b.add(line, 0.05))            # 0 where there is no rut, 1 where it is full width
        half_band = b.mul(b.mul(S('Band Width'), 0.5), width_factor)
        band = hard(b.sub(half_band, distance))
        groove = hard(b.sub(b.mul(half_band, S('Groove Share')), distance))
        bank_reach = b.add(half_band, b.mul(b.mul(S('Band Width'), S('Bank Share')), width_factor))
        on_bank_side = b.gt(b.mul(signed, S('Bank Side')), 0.0)
        bank = b.mul(b.mul(hard(b.sub(bank_reach, distance)), on_bank_side), b.sub(1.0, band))

        # wet streaks: a thin line that wanders inside the band; where and how long comes from a noise read along the rut (one line per rut)
        along_line = b.vec(along, b.add(b.mul(stripe_number, 0.173), 0.31 + 0.2 * index), 0.0)
        streak_noise = b.tileable_noise(along_line, b.mul(tiles, 28.0), 2.0, 0.5, b.add(b.mul(seed, 0.9), 41.0 + 7.0 * index))
        streak_wander = b.mul(b.sub(b.tileable_noise(along_line, b.mul(tiles, 14.0), 1.0, 0.5, b.add(b.mul(seed, 1.1), 53.0 + 3.0 * index)), 0.5), b.mul(half_band, 1.2))
        streak_present = b.smoothstep(streak_noise, b.sub(0.62, b.mul(S('Streak Amount'), 0.2)), b.add(b.sub(0.62, b.mul(S('Streak Amount'), 0.2)), 0.04))
        streak = b.mul(b.mul(hard(b.sub(S('Streak Width'), b.absolute(b.sub(signed, streak_wander)))), streak_present), band)

        family_colour = bank_colour
        family_colour = b.mix(family_colour, band_colour, band)
        family_colour = b.mix(family_colour, S('Groove Colour'), groove)
        family_colour = b.mix(family_colour, S('Streak Colour'), streak)
        family_mask = b.mx(band, bank)
        family_sunk = b.add(b.mul(band, S('Band Sink')), b.mul(groove, b.mul(S('Band Sink'), 0.5)))
        family_raise = b.mul(bank, S('Bank Raise'))
        family_wet = streak
        if mask_all is None:
            mask_all, colour, sunk, smooth = family_mask, family_colour, b.sub(family_raise, family_sunk), family_wet
        else:                                                                                  # the second family is painted over the first
            colour = b.mix(colour, family_colour, family_mask)
            sunk = b.mixf(sunk, b.sub(family_raise, family_sunk), family_mask)
            smooth = b.mx(smooth, family_wet)
            mask_all = b.mx(mask_all, family_mask)

    height = sunk
    roughness = b.sub(b.mul(mask_all, 0.05), b.mul(smooth, 0.4))
    b.finish_layer(mask=mask_all, colour=colour, height=height, roughness=roughness)
    return tree
