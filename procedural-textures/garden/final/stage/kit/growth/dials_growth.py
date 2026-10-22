# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The EXTRA dials of the growth layer. The dials of the plan's Appendix A (weeds_amount, cushions_amount, distance, distance_fade, piece_size, weed_cover, gutter_tuft_share,
# wall_foot_share, cushion_cover, min_spacing, toadflax_clumps, rubbish_thin_max, rubbish_heap_min, dead_grass_share, flower_share, max_pieces, wet_dark, tilt_random) are already in
# apply/dial_table.json; the plan allows finer ones in the same style. They are added here (ensure() is called by apply_growth.register).
#   piece_inflate_limit   how many times bigger than real a plant may be drawn so that it stays min_dots plate dots wide at a distance. The common dial `inflate_limit` is 6 in the
#                         look; standing plants keep their resolution, so the growth layer has its own, lower one (about 3), as the plan says.
#   moss_smother_from/to  the rubbish values between which moss cushions thin out and stop (0.30 and 0.60 in the plan's rule), beside weeds' rubbish_thin_max / rubbish_heap_min.
#   existing_avoid        how much of a place's existing growth (the add-on's own moss) is left alone: 0 = grow on it, 1 = none on it.
#   avoid_m               a weed or cushion is not stood within this distance of a 3D piece of the objects the set names in growth.avoid_pieces_of (the earlier rubbish layer's litter).
#   colour_gain           multiplies the colour of every piece (brightness tuning against the plate; 1 = species.json as written).
#   min_dots_scale        multiplies every kind's smallest width in plate dots (6 for weeds, 5 for moss in species.json).
#   colour_sat            multiplies the saturation of every piece (the plan: saturation 0.45 or more; the period check: no bright green, saturation 0.6 and value 0.6 or more).
#   show_kind             checking views only: -1 = all kinds; 0, 1, 2 ... = only that kind of the species list (the number printed in pieces.json's kinds table).
#   realise               1 turns the instances into plain meshes (for sets whose later steps need real geometry); 0 keeps instances (cheap).
#   cand_density_scale    multiplies the candidate points laid for every kind (the Poisson density); more = a finer choice of places, slower. Changing it does not change the count.
from apply import dials


def row(name, lo, hi, default, doc, unit=''):
    return dict(name=name, lo=lo, hi=hi, unit=unit, default=default, doc=doc)


EXTRA = [
    row('piece_inflate_limit', 1.0, 6.0, 3.0, 'How many times bigger than real a plant may be drawn so that it stays at least min_dots plate dots wide at a distance (the growth layer\'s own, lower limit).'),
    row('moss_smother_from', 0.1, 0.6, 0.30, 'Rubbish value above which moss cushions start to thin out.'),
    row('moss_smother_to', 0.3, 0.95, 0.60, 'Rubbish value at which moss cushions have stopped.'),
    row('existing_avoid', 0.0, 1.0, 0.8, 'How much the places that already have growth (the set\'s existing_growth) are left alone: 0 grow on it, 1 none on it.'),
    row('avoid_m', 0.0, 0.3, 0.05, 'Nearest a plant may stand to a 3D piece of the objects named in growth.avoid_pieces_of (litter).', 'm'),
    row('colour_gain', 0.4, 2.5, 1.0, 'Multiplies the colour of every piece (tuning the plate brightness).'),
    row('min_dots_scale', 0.5, 3.0, 1.0, 'Multiplies every kind\'s smallest width in plate dots (species.json min_dots: 6 for weeds, 5 for moss) that a plant is widened to at a distance (never past piece_inflate_limit).'),
    row('colour_sat', 0.2, 1.5, 1.0, 'Multiplies the colour saturation of every piece (1 = species.json as written).'),
    row('show_kind', -1, 20, -1, 'Checking view only: -1 all kinds, otherwise only the kind with that number.'),
    row('realise', 0, 1, 0, 'Turn the instances into plain meshes (1) or keep instances (0).'),
    row('cand_density_scale', 0.3, 3.0, 1.0, 'Multiplier of the candidate points of every kind (finer choice of places, slower).'),
]

_done = False


def ensure():
    global _done
    if not _done:
        dials.register_layer('growth', EXTRA)
        _done = True
