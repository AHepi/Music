# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# FOOT (node group WK FOOT, slot A). The foot of a wall: the dirt splash band (G4), the damp tide-mark with white salts on top of it (S5), eroded mortar and flaked faces in the lowest
# metre (C5). Reads the standard masks height (metres above the ground under the dot), dampness, vertical_foot (where a pipe or post stands), tx_cavity and tx_cell (mortar hollows and
# a number per brick or stone of the photo material), shade.
#   * SPLASH BAND: splash_height tall (never lower than band_min_dots plate dots), darkest at the ground line, with a ragged top edge: a slow wobble plus short fingers
#     (finger_height, splash_ragged) and a scatter of splash dots above it. Heavier and taller at the feet of pipes and posts (pipe_foot_boost). Pale-first: splash_pale makes
#     it a dusty brown LIGHTER than a sooted wall (0 = dark mud) so that it reads on a dark wall.
#   * TIDE-MARK: on tide_share of the houses (decided per house from its own seed) the damp zone rises to tide_height with a ragged top; inside it the wall is a little darker and
#     greener (tide_strength, tide_green); along its top a fuzzy line of white salts (salt_bloom, flecks never smaller than salt_dots plate dots).
#   * WEAR: in the lowest wear_height the mortar is recessed (mortar_wear, a relief on the incoming normal, faded with distance) and spall_share of the bricks or stones have a flaked,
#     fresher face.
# Amount 0: every strength is a product with the amount; the relief is blended by it, so the outputs equal the inputs exactly.
from . import dials_walls
from .walls_common import WallLayer

KEY = 'foot'
GROUP = 'WK FOOT'
MASKS = ['height', 'dampness', 'vertical_foot', 'tx_cavity', 'tx_cell', 'shade', 'frame_valid']
PARTS = ['band', 'tide', 'salt', 'wear']
DUST = (0.40, 0.31, 0.22)         # a dusty brown albedo, lighter than a sooted wall
SALT = (0.42, 0.40, 0.35)
GREEN = (0.10, 0.14, 0.07)
FRESH = (0.26, 0.12, 0.07)        # a flaked brick or stone face


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    g, dial = L.g, L.dial
    fade = g('Fade Near')
    h = L.height_eff(g('M Height'), g('M Frame Valid'))

    # ---- the heights, never lower than the dots they need
    band_m, band_fade = L.width_dots(dial('splash_height'), dial('band_min_dots'), along=False)
    foot_boost = L.mul(g('M Vertical Foot'), dial('pipe_foot_boost'))
    n_slow = L.stretch(L.noise(1.1, 0.0, detail=2.0), 3.0)                                 # a wobble along the wall only
    n_fing = L.stretch(L.noise(L.inv(L.mx(L.mul(dial('finger_height'), 0.5), 0.02)), 0.0, detail=1.0), 3.0)
    dot_m = L.mx(L.mul(g('Dot Across'), dial('salt_dots')), 0.03)
    n_spk = L.stretch(L.noise(L.inv(dot_m), L.mul(L.inv(dot_m), 1.13), detail=1.0), 3.0)
    rag = dial('splash_ragged')
    top = L.mul(band_m, L.mad(L.mul(rag, 0.7), n_slow, L.mad(rag, -0.35, 1.0)))
    top = L.mx(L.mad(L.mul(dial('finger_height'), rag), L.sstep(n_fing, 0.5, 0.8), L.mul(top, L.mad(foot_boost, 0.8, 1.0))), 0.02)

    # ---- splash band: darkest at the ground, ragged top, plus a few splash dots above it
    g_band = L.one_minus(L.sstep(h, 0.0, top))
    band = g_band
    str_ = L.mul(dial('splash_strength'), L.mad(foot_boost, 0.5, 1.0))
    pale = dial('splash_pale')

    # ---- the damp tide-mark: per house, ragged top, greener and darker, salts along the top
    tide_gate = L.lt(L.house_rand(0.7), dial('tide_share'))
    tide_top = L.mad(L.mul(L.mul(dial('finger_height'), 1.4), L.sstep(n_fing, 0.45, 0.8)), 1.0, L.mul(dial('tide_height'), L.mad(n_slow, 0.7, 0.65)))
    inside = L.mul(L.mul(L.one_minus(L.sstep(h, L.sub(tide_top, 0.06), L.add(tide_top, 0.02))), tide_gate), L.mad(L.sstep(g('M Dampness'), 0.2, 0.7), 0.4, 0.6))
    near_top = L.one_minus(L.sstep(L.absv(L.sub(h, L.sub(tide_top, 0.02))), 0.0, 0.07))
    cut = L.sub(1.0, L.mul(dial('salt_bloom'), 14.0))
    salt = L.mul(L.mul(L.mul(near_top, tide_gate), L.sstep(n_spk, cut, L.add(cut, 0.06))), fade)

    # ---- wear in the lowest wear_height: recessed mortar and flaked faces
    wear_zone = L.one_minus(L.sstep(h, L.mul(dial('wear_height'), 0.5), dial('wear_height')))
    wear = L.mul(L.mul(dial('mortar_wear'), L.lerp(fade, 0.28, g('M Tx Cavity'))), wear_zone)
    spall = L.mul(L.mul(L.lt(g('M Tx Cell'), dial('spall_share')), wear_zone), fade)

    # ---- the colour: dark mud (pale = 0) or pale dust (pale = 1) in the band; the tide zone darker and greener; salts; flaked faces
    colour = L.gain(g('Colour'), L.sub(1.0, L.mul(L.mul(str_, L.mul(band, 0.55)), L.one_minus(pale))))
    colour = L.tint(colour, DUST, L.mul(L.mul(str_, band), L.mul(pale, 0.9)))
    colour = L.gain(colour, L.mad(L.mul(dial('tide_strength'), 0.35), L.mul(inside, -1.0), 1.0))
    colour = L.tint(colour, GREEN, L.mul(L.mul(dial('tide_green'), dial('tide_strength')), L.mul(inside, 0.8)))
    colour = L.tint(colour, SALT, L.mul(salt, 0.9))
    colour = L.tint(colour, FRESH, L.mul(spall, 0.7))

    # ---- a damp, dull foot: rougher; relief: recessed mortar and flaked faces (a bump on the incoming normal)
    rough = L.c01(L.mad(L.mx(L.mul(band, 0.5), inside), 0.12, g('Roughness')))
    normal = L.bump_raw(L.mad(spall, -0.004, L.mul(wear, -0.006)))

    mask = L.mul(L.mx(L.sstep(g_band, 0.35, 0.6), L.mx(L.sstep(inside, 0.4, 0.7), L.sstep(salt, 0.3, 0.6))), L.gt(L.amount, 1e-4))
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), roughness=L.blend_float(g('Roughness'), rough), normal=L.blend_normal(g('Normal'), normal, fade), mask=mask,
                          parts={'band': band, 'tide': inside, 'salt': salt, 'wear': L.c01(L.add(wear, spall))})
