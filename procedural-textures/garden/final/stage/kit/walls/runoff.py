# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# RUNOFF (node group WK RUNOFF, slot A). Rain streaks on walls below sills, ledges, cap edges, eaves and downpipe joints (rules G2 and S2 on the wall). The element that suits a wall
# best: a vertical streak survives a wall seen from a slant, where small horizontal detail does not.
# Where: the standard masks drip (a column of run-off below every source), drip_dist (how far below it) and drip_kind (ledge, pipe joint, pipe foot, eave, cap), used only where a wall
# sheet applies (frame_valid).
# How: inside a run-off column, vertical streaks laid out by noise stretched far taller than wide; the streak pitch and width come from `width_dots` (never narrower than width_dots plate
# dots, measured ALONG the wall, so a wall seen from the side gets wider streaks); the two edges of every ledge (the sill ends) carry a streak of their own (pair_share), only on
# source_share of the sources; each streak has its own length (length_mult x a random 0.5 to 1.3); long and heavy under the downpipes of leak_share of the houses (leak_length).
# Look: on a sooty wall a streak is a PALE washed stripe with dark tide-lines along its edges (tone -0.5, edge_dark), because dark on dark is crushed by the film; on pale plaster
# it is a dark grey-green stain (tone +0.7). Streaks from a downpipe joint or a bracket tint toward rust (iron_rust). Fine detail fades to the layer's average tone, never to clean.
# Amount 0 gives the inputs back exactly (every strength is a product with the amount).
from . import dials_walls
from .walls_common import WallLayer, DRIP_REACH_M, KIND_ITEMS

KEY = 'runoff'
GROUP = 'WK RUNOFF'
MASKS = ['drip', 'drip_dist', 'drip_kind', 'sheltered', 'height', 'frame_valid']
PARTS = ['streaks', 'pairs', 'rust']
RUST = (0.42, 0.16, 0.06)
PALE_STRIPE = (0.40, 0.34, 0.26)   # a washed stripe of clean pale stone (albedo): the pale stripe is lifted at least toward this
STRIPE_DUTY = 0.30           # the share of a run-off column that the stripes cover on average (what the pattern fades to far away)


def kind_window(L, kind, centre):
    """1 where the drip_kind picture reads (about) `centre`, 0 for the other kinds (the picture holds multiples of 0.2)."""
    return L.one_minus(L.sstep(L.absv(L.sub(kind, centre)), 0.04, 0.12))


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    g, dial = L.g, L.dial
    fv = g('M Frame Valid')
    fade = g('Fade Near')

    drip = L.mul(g('M Drip'), fv)
    dist_m = L.mul(g('M Drip Dist'), DRIP_REACH_M)
    kind = g('M Drip Kind')
    k_ledge, k_pipe, k_eave, k_cap = (kind_window(L, kind, KIND_ITEMS[k]) for k in ('ledge', 'pipe_joint', 'eave', 'cap'))
    kind_w = L.mx(L.mx(k_ledge, k_cap), L.mx(k_pipe, L.mul(k_eave, dial('eave_streaks'))))

    # ---- sizes in plate dots, measured along the wall
    wid_m, wid_fade = L.width_dots(0.06, dial('width_dots'), along=True)
    pitch = L.mul(L.mul(wid_m, 3.4), dial('pitch_mult'))
    fa = L.inv(pitch)
    stripes = L.sstep(L.stretch(L.noise(fa, L.mul(fa, 0.16), detail=2.0), 3.6), 0.60, 0.74)       # tall, narrow stripes
    lenvar = L.stretch(L.noise(L.mul(fa, 0.7), 0.0, detail=1.0), 3.0)                            # a length for each stripe (the sideways position only)
    gate_n = L.stretch(L.noise(0.9, 0.55, detail=1.0), 3.0)                                      # which sources carry a streak: about every metre
    keepshare = L.sub(1.0, dial('source_share'))
    presence = L.sstep(gate_n, L.sub(keepshare, 0.15), L.add(keepshare, 0.15))

    # ---- length: each streak runs length_mult x (0.5 .. 1.3) x 0.7 m below its source
    reach = L.mul(L.mul(dial('length_mult'), L.mad(lenvar, 0.8, 0.5)), 0.7)
    envelope = L.one_minus(L.sstep(dist_m, L.mul(reach, 0.3), reach))
    zone = L.sstep(drip, 0.35, 0.8)

    # ---- the two edges of a ledge (the sill ends): where the run-off column is half way between its inside and its outside
    edge_band = L.one_minus(L.sstep(L.absv(L.sub(drip, 0.5)), 0.0, 0.28))
    pairs = L.mul(L.mul(edge_band, presence), L.mul(dial('pair_share'), 1.4))
    streak = L.c01(L.mul(L.mul(L.mx(L.mul(L.mul(zone, stripes), L.mul(presence, 0.8)), pairs), kind_w), envelope))

    # ---- heavy leaks under the downpipe joints of some houses
    leak_env = L.one_minus(L.sstep(dist_m, L.mul(dial('leak_length'), 0.5), dial('leak_length')))
    leak = L.mul(L.mul(L.mul(zone, k_pipe), L.lt(L.house_rand(0.3), dial('leak_share'))), leak_env)
    streak = L.mx(streak, leak)

    # ---- fade to the average tone: far away only the column's tone is left (never clean)
    s_eff = L.lerp(L.mul(fade, wid_fade), L.mul(L.mul(zone, kind_w), L.mul(envelope, STRIPE_DUTY)), streak)

    # ---- the look of a streak: pale washed stripe (tone < 0) or dark stain (tone > 0), dark tide-lines along the edges
    tone = dial('tone')
    pal = L.mul(L.sub(1.0, tone), 0.5)                                       # 1 = all pale, 0 = all dark
    interior = L.sstep(s_eff, 0.45, 0.85)
    edge = L.mul(L.sstep(s_eff, 0.05, 0.3), L.one_minus(L.sstep(s_eff, 0.4, 0.75)))
    strength = dial('strength')
    up = L.mul(L.mul(strength, L.mad(dial('stain_value'), 1.6, 0.6)), L.mul(pal, interior))
    down = L.mul(L.mul(strength, 0.8), L.mul(L.one_minus(pal), interior))
    tide = L.mul(L.mul(dial('edge_dark'), strength), L.mul(edge, 0.9))
    factor = L.mx(L.mul(L.add(1.0, L.sub(up, down)), L.one_minus(tide)), 0.25)

    colour = L.gain(g('Colour'), factor)
    colour = L.lift_to(colour, PALE_STRIPE, L.mul(L.mul(L.mul(dial('strength'), dial('stain_value')), pal), interior))
    rust_fac = L.c01(L.mul(L.mul(dial('iron_rust'), 1.5), L.mul(s_eff, k_pipe)))
    colour = L.tint(colour, RUST, rust_fac)
    colour = L.tint(colour, (0.09, 0.12, 0.07), L.mul(L.mul(L.mx(tone, 0.0), 0.3), interior))     # a dark stain on pale plaster is a little green-grey

    mask = L.mul(L.sstep(s_eff, 0.35, 0.6), L.gt(L.amount, 1e-4))
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), mask=mask, parts={'streaks': streak, 'pairs': L.c01(pairs), 'rust': rust_fac})
