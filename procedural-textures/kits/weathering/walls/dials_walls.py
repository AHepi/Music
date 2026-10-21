# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The FINER DIALS of the walls layers, added to the kit's dial table (apply/dial_table.json lists the plan's dials; the table is never edited, these rows are registered next to
# them when the layers are registered). Same style as the plan's rows: name, range, kit default, what it does. A look file may name them; a look that does not gets these defaults.
# Lengths in metres unless a dial says plate dots.
from . import walls_common

EXTRA = {
    'soot': [
        dict(name='mottle_stretch', lo=1.0, hi=4.0, unit='', default=2.0, doc='How much taller than wide the soot mottling is (soot clouds run in columns: 1.8 to 2.5).'),
        dict(name='patch_min_dots', lo=8.0, hi=40.0, unit='dots', default=15.0, doc='Smallest soot or washed patch, in plate dots (patches of 15 dots or more survive the painter).'),
        dict(name='rough_gain', lo=0.0, hi=0.3, unit='', default=0.1, doc='How much duller (rougher) the sooted surface becomes; soot is a dry crust.'),
        dict(name='shade_wash', lo=0.0, hi=1.0, unit='', default=0.6, doc='How much shade keeps the rain-washed patches away (0 = shade makes no difference, 1 = none in full shade).'),
        dict(name='pale_warm', lo=0.0, hi=1.0, unit='', default=0.0, doc='Colour of the washed patches: 0 = a neutral pale stone (reads grey-blue under a night sky), 1 = a warm buff stone that keeps the warm hue of brick.'),
        dict(name='washed_pale', lo=0.0, hi=1.0, unit='', default=0.5, doc='Pale-first: how much the washed patches are lifted above the surrounding film, so that they read on a dark wall (0 = only the washed_mult value).'),
    ],
    'runoff': [
        dict(name='pitch_mult', lo=0.5, hi=3.0, unit='', default=1.0, doc='Spacing of the streaks inside a run-off zone (1 = a streak about every 0.25 m).'),
        dict(name='pair_share', lo=0.0, hi=1.0, unit='', default=0.5, doc='How strongly the two edges of every ledge (the sill ends) carry a streak of their own.'),
        dict(name='stain_value', lo=0.0, hi=1.0, unit='', default=0.5, doc='How much brighter than its surround a pale stripe is made, 1 = the strongest allowed (pale-first on dark walls).'),
    ],
    'foot': [
        dict(name='splash_pale', lo=0.0, hi=1.0, unit='', default=0.5, doc='Pale-first: 0 = dark mud splash, 1 = pale dust splash (a dusty brown lighter than a sooted wall, so the band reads on a dark wall).'),
        dict(name='band_min_dots', lo=8.0, hi=40.0, unit='dots', default=15.0, doc='Smallest band height in plate dots (the band is drawn taller than real when the wall is far).'),
        dict(name='salt_dots', lo=3.0, hi=16.0, unit='dots', default=6.0, doc='Smallest salt fleck in plate dots.'),
    ],
    'steps': [
        dict(name='tread_pale', lo=0.0, hi=1.0, unit='', default=0.5, doc='How pale a scrubbed (not whitened) step is.'),
        dict(name='chip_m', lo=0.02, hi=0.12, unit='m', default=0.05, doc='Size of a chipped nosing.'),
        dict(name='white_cream', lo=0.0, hi=1.0, unit='', default=0.0, doc='Colour of whitened stone: 0 = a cold near-white, 1 = a warm cream (donkey stone; a cold white reads blue-white under a night sky).'),
        dict(name='white_value', lo=0.5, hi=1.2, unit='', default=1.0, doc='Brightness of whitened stone against the colour chosen by white_cream (below 1 so it does not read as plastic).'),
        dict(name='riser_share', lo=0.0, hi=1.0, unit='', default=0.8, doc='How much of the whitening or scrubbing also goes on the riser and the foot of the doorway round the step.'),
    ],
    'wallgrowth': [
        dict(name='moss_value', lo=0.1, hi=1.0, unit='', default=0.35, doc='Albedo of the lightest moss tone (a number; the moss is lighter than the stone, never below brightness_floor).'),
        dict(name='algae_strength', lo=0.0, hi=1.0, unit='', default=0.5, doc='How dark the green-black algae film is on its damp, shaded places.'),
        dict(name='hue', lo=70.0, hi=140.0, unit='deg', default=100.0, doc='Hue of moss in degrees (85 to 120 survives the painter as green).'),
        dict(name='saturation', lo=0.3, hi=0.9, unit='', default=0.55, doc='Saturation of moss (0.45 or more so that the painter keeps it green).'),
    ],
    'wallcracks': [
        dict(name='chip_pale', lo=0.0, hi=1.0, unit='', default=0.6, doc='Chips show fresh, paler stone (pale-first on dark walls).'),
        dict(name='step_cm', lo=6.0, hi=40.0, unit='cm', default=15.0, doc='Height of one step of a stepped mining crack (about two brick courses).'),
        dict(name='crack_pale', lo=0.0, hi=1.0, unit='', default=0.5, doc='Pale dust lip along a crack so that it reads on a dark wall.'),
    ],
    'paint': [
        dict(name='grain_dots', lo=3.0, hi=16.0, unit='dots', default=6.0, doc='Smallest flake width in plate dots.'),
    ],
}


def register_all():
    for key, rows in EXTRA.items():
        walls_common.ensure_dials(key, rows)
