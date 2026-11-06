"""
What this file does: makes rocks by rules and lays them on a ground you give. Every rock is its own shape, made from its
seed the way real rocks come about: a lump of stone broken along a few flat faces where it split, then worn by weather,
which rounds its edges (the older the rock, the rounder), pits its skin and, on flat stones, leaves a flatter top. Four
kinds: 'boulder' (old weathered boulders, the garden's set stones), 'angular' (freshly broken stone, sharp faces),
'flat' (slabs: stepping stones and the flat stones at the water's edge) and 'river' (stones worn smooth by water).

There are three ways to lay them, and where they go is always yours to say:

  - scatter() lays many over a ground you give, within the area or weights you give, with Blender's own particle
    system: the rocks are particle copies of a handful of shapes (several in every scatter, so no two neighbours look
    alike), each copy turned at random, tilted with the ground under it and sunk into the soil by a share of its height
    (none floats). Sizes run between the two you give, big rocks fewer than small ones. The tool chooses each rock's
    spot by the rules (inside your area, kept apart so that few overlap, small ones gathering at the foot of big ones
    if you ask) and hands the spots to the particle system as tiny faces on the ground, one particle each: Blender's
    own spreading cannot keep rocks apart. A narrow area (a pond's bank along a big ground) gets enough places to
    choose from: when a size of rock comes up short, more places are found on the part of the ground the area reaches.
  - at_spots() lays rocks with a set place (a lantern's seat, a basin's front stone, the rocks a picture puts here and
    there) as particle copies too, one on each spot you give, each its own shape made at its own size, as high as you
    ask (`top`: its highest point reaches that height, never left floating on dry ground), with real bumps on the ones
    you choose (`relief`).
  - place() sets single rocks at points you give, from the same shapes and rules: big rocks near the eye. Each is its
    own object with real bumps from the photograph's height picture (the relief), which the scattered copies cannot
    have (copies share their shape, so the same bumps would repeat).

All three cover the rocks with a photographed rock surface from the shelf (colour, normal, roughness and height
pictures: PBR, decision 84), at the photograph's real size, each rock showing its own part of it (shifted, never
turned: on a round rock a turned picture meets itself in hard seams), a little lighter or darker, greyer than the
photograph (garden granite is grey; the photographs under warm lamps read brown);
darker and glossy at their feet where the ground is wet (the ground tool's 'wetness'), a little wet all over after
rain, and with moss on their tops if you ask (the moss tool), each rock its own amount of it if you ask (`moss_spread`).
Where rocks stand in a pond, give the water's height (`water`): a dark wet band just above the water and the stone
darker below it.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import ground, rocks
    yard = ground.make(size=(10, 10), relief=0.08, seed=3)
    laid = rocks.scatter(yard, kind='boulder', count=24, sizes=(0.15, 0.9), area=(-3, -3, 3, 0), seed=2)
    rocks.scatter(yard, kind='river', count=60, sizes=(0.06, 0.25), area=[(0, 0), (3, 1), (1, 4)], seed=3)
    big = rocks.place([(1.0, 2.0), (2.6, 1.4)], kind='boulder', size=[1.4, 0.8], ground=yard, moss=0.7, seed=5)
    steps = rocks.place([(0, -1), (0.5, -1.6)], kind='flat', size=0.6, ground=yard, turn=[20, 75], seed=6)
    print(laid['placed'], 'rocks scattered')
    # rocks with a set place, as particle copies: a lantern's seat whose top is at 0.12 m (asked higher than a flat
    # stone can reach without floating, it is lowered: seat['lowered']), and two rocks in a pond whose water is at
    # z = 0, the near one with real bumps; each rock its own amount of moss
    seat = rocks.at_spots([(2.2, -2.0)], kind='flat', size=0.7, top=0.12, ground=yard, tilt=0.0, moss=0.9, seed=7)
    pond = rocks.at_spots([(-1.0, 3.0), (-1.6, 3.4)], size=[0.8, 0.5], top=[0.25, None], ground=yard, relief=[0.03, 0.0],
                          moss=1.0, moss_spread=(0.35, 1.4), water=0.0, seed=8)
    lantern_foot = seat['spots'][0][4]          # the height its top reached: stand the lantern there
    # a narrow bank: a keep-or-not test of one place, as your own, is an area too
    bank = rocks.scatter(yard, count=120, sizes=(0.16, 1.1), area=lambda x, y: 4.0 < (x * x + y * y) ** 0.5 < 4.6,
                         spacing=0.75, gather=0.6, moss=1.0, moss_spread=(0.35, 1.4), water=0.0, seed=57)

From the command line:

    python3 rocks.py --help
    python3 rocks.py --blend IN.blend --ground Ground --out OUT.blend [--kind boulder --count 30 --sizes 0.15 0.9 --seed 2]
    python3 rocks.py --blend IN.blend --ground Ground --out OUT.blend --area -2 -2 2 1 --kind river --moss 0.6

Options of scatter(), with their defaults:
    ground      the ground: a mesh object (the ground tool's, or your own); required. It is not changed.
    kind        'boulder', 'angular', 'flat' or 'river' ('boulder')
    count       how many rocks (30); fewer are laid if the area cannot hold them apart ('placed' says how many)
    sizes       the smallest and largest rock, metres across ((0.15, 0.9))
    fall        how fast the numbers fall with size: 2 gives about four times as many rocks half the size (2.0)
    area        where: None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], a function
                of an (n, 2) array of points giving weights 0 to 1, or a test of one place, keep(x, y), giving True or
                False (None); a narrow area gets more places to choose from when it comes up short
    spacing     how far apart rocks keep: 1 lets their feet just touch, 0.7 lets them lean together, 1.5 keeps a gap (1.0)
    gather      0 spreads the smaller rocks evenly; 1 gathers them at the feet of the bigger ones (0.0)
    buried      share of each rock's height sunk in the soil, on average (each rock a little more or less), 0.05 to
                0.8; None gives the kind its own (boulder 0.42: set deep, as garden boulders are; angular 0.25,
                flat 0.4, river 0.2)
    tilt        how far each rock tips from lying square on the ground, 0 to 0.3 (None: the kind's own, about 0.05)
    shapes      how many shapes each size of rock is copied from (8)
    surface     the photographed rock set (None: boulder and flat 'lichen_rock', angular 'rock_wall_02', river
                'seaside_rock'); any shelf set or 'SURFACE • <set>' name. Flat stones wore the dark smooth
                'seaside_rock' until the garden's rocks pass: in shade a flat stone in it drew as a black patch
    moss        moss on their tops: 0 none, 1 thick (0.0)
    moss_colour the moss's darkest green, (red, green, blue), linear; its cushions vary lighter and yellower (None:
                the brighter green of the owner's garden picture, (0.07, 0.105, 0.02); MOSS_DARK, the tool's first
                (0.05, 0.075, 0.018), read grey-olive at dusk)
    moss_spread each rock its own amount of moss: the moss times a number between these two, by each rock's own random
                number, as shaded and open rocks differ, such as (0.35, 1.4) (None: every rock the same). Not for a
                material you give one big object of your own (a carved basin): its one number thins or thickens it all
    moss_style  'cushions': real moss with thickness (thick on the tops and in the hollows, thinning at the edges,
                spilling over the rims), a pile of tiny tufts laid by the particle system, the stone under and round it
                green, pale lichen on the bare stone: the moss tool's cushions, grown inside each shape so the particle
                copies carry them; 'paint': the moss as a colour on the stone only, as before 6 November 2026
                (None: 'cushions')
    moss_thickness  the cushions' depth in the middle, metres; on small rocks at most 0.08 of their size (0.03)
    moss_pile   the cushions' tufts: 1 about 16,000 a square metre of cushion, 0 none, up to 3 (1.0)
    lichen      pale lichen crusts on the bare stone, 0 none to 1.5 (None: 0.6 on rocks with cushions, else 0)
    normal_strength  how strongly the photograph's normal picture shows its relief: 0 plain, 1 its full relief, up to
                2 (None: the set's own, 1)
    water       the height of the water's surface, metres, where rocks stand in a pond: a dark wet band from
                `water_band` above it down to it, the stone darker and glossier below (None: no water line). It goes
                by height alone: any rock lower than the water darkens, in a pond or not
    water_band  how high the wet band climbs above the water, metres (0.07)
    wet_feet    how dark and glossy their feet are where the ground is wet, 0 to 1 (0.7)
    rain        how wet they are all over, 0 dry to 1 soaked (0.3)
    grey        how much greyer than the photograph, 0 its own colour to 1 grey (None: boulder 0.55, angular 0.45,
                flat 0.3, river 0.25: garden granite is grey, and a photograph under warm lamps reads brown)
    tint        a colour the photograph is multiplied by, (red, green, blue) (None: boulders a little green,
                (0.9, 1.0, 0.93); (1, 1, 1) leaves it as it is)
    seed        the same seed lays the same rocks (0)
    collection  where the objects go (a new collection 'rocks')
Options of place(), with their defaults:
    points      where: a list of (x, y) or (x, y, z) points; with a ground, z is the ground's height there; required
    kind, buried, tilt, surface, moss, moss_colour, moss_spread, normal_strength, water, water_band, wet_feet, rain,
    grey, tint, seed, collection    as scatter()
    size        metres across: one number for all, or one per point (1.0)
    ground      a ground to sit them on (its height and slope under each point), or None (z as given, upright) (None)
    turn        degrees about the upright: one number, one per point, or None for a random turn (None)
    relief      metres of real bumps from the photograph's height picture, 0 none (0.04); costs drawing time
    detail      how finely the bumps are made: 1 coarse, 2, 3 fine (2)
Options of at_spots(), with their defaults:
    spots       where: a list of (x, y) or (x, y, z) places; with a ground, z is the ground's height there; required
    kind, buried, tilt, surface, moss, moss_colour, moss_spread, normal_strength, wet_feet, rain, grey, tint, seed,
    collection    as scatter() (tilt=0 for a seat that must stay level)
    size        metres across: one number for all, or one per spot (1.0)
    top         the height each rock's highest point should reach (the rock it replaces, the foot of what stands on
                it): one number, one per spot (None in the list sits that one at the soil line), or None for all (None).
                On dry ground a rock is never left floating: one that would is lowered until most of its sunk part is
                in the soil (the result's 'lowered' says which). Where its foot is under the `water`, it stands as
                asked, its foot hidden by the water; without `water`, a rock asked to stand high in a deep pond is
                pulled down towards the pond's bed
    ground      a ground to sit them on (its height, facing and wetness under each spot), or None (None)
    facing      the ground's facing, the rock's up: one (x, y, z) direction, one per spot, or None (None: the ground's
                own facing under each spot, or straight up without a ground)
    relief      metres of real bumps, one number or one per spot, 0 none (0.0): give it to the ones near the eye
    detail      how finely the bumps are made: 1 coarse, 2, 3 fine (2)
    water, water_band   as scatter(); the water also lets rocks in a pond keep the height asked (see top)
    name        the sheets' name, '<name> <n>' (None: 'rocks <kind> at spots')

What it makes: scatter() makes one object per size band ('rocks <kind> <from>-<to> m'), each a sheet of tiny faces
lying on the ground, one per rock, hidden, with a particle system that copies the shapes onto them; the shapes (made at
the band's size, origin at the soil line) are kept in collections that are not in the scene ('rocks shapes • ...').
at_spots() makes one such sheet per rock, with one tiny face and one particle copy of a shape made at that rock's own
size, and gives back each spot's soil line and the height its top reached ('spots': (x, y, z, size, top)): a ray
cannot find a particle copy, so stand a lantern on a seat by that height. place() makes one object per rock
('rock <kind> <n>'). The materials are copies named 'rocks • <set> • ...'; the store's own materials are left as they
were. In a material, the nodes 'Moss amount', 'Moss spread', 'Water line' and 'Wet feet' are named, so a script can
find them by name; never by their values, as two of them may hold the same number. With cushions, each shape (and each
rock set singly) also carries the cushions as faces in the material 'moss • cushions' and a particle system 'moss pile'
copying the tufts (collection 'moss • tufts • ...'); each shape gets its own amount of moss by moss_spread.
"""

import argparse
import json
import math
import os
import random
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import store  # noqa: E402

# each kind: its proportions (width and height as shares of its length), how lumpy its first form is, how many flat
# breaks and how deep they cut, how long it has weathered (smoothing passes: the edges' rounding), how pitted its skin,
# whether it has a flat top (and bottom), the share of its height sunk in the soil, how far it tips, its rock set
KINDS = {
    'boulder': {'width': (0.68, 0.92), 'height': (0.5, 0.78), 'lumps': 0.26, 'breaks': (2, 4), 'cut': (0.55, 0.85),
                'age': (14, 26), 'pits': 0.012, 'flat_top': False, 'buried': 0.42, 'tilt': 0.05,
                'surface': 'lichen_rock', 'grey': 0.55, 'tint': (0.9, 1.0, 0.93), 'what': 'old weathered boulders: a lumpy body, a few broken faces worn round'},
    'angular': {'width': (0.55, 0.85), 'height': (0.45, 0.8), 'lumps': 0.14, 'breaks': (5, 9), 'cut': (0.5, 0.85),
                'age': (1, 3), 'pits': 0.006, 'flat_top': False, 'buried': 0.25, 'tilt': 0.08,
                'surface': 'rock_wall_02', 'grey': 0.45, 'tint': (0.95, 1.0, 0.97), 'what': 'freshly broken stone: many flat faces meeting at sharp edges'},
    'flat': {'width': (0.6, 0.9), 'height': (0.2, 0.3), 'lumps': 0.18, 'breaks': (2, 4), 'cut': (0.6, 0.9),
             'age': (8, 16), 'pits': 0.006, 'flat_top': True, 'buried': 0.4, 'tilt': 0.025,
             'surface': 'lichen_rock', 'grey': 0.3, 'tint': (0.97, 1.0, 0.98), 'what': 'slabs with a flatter top: stepping stones, the flat stones at the water\'s edge'},
    'river': {'width': (0.55, 0.82), 'height': (0.32, 0.55), 'lumps': 0.1, 'breaks': (0, 1), 'cut': (0.75, 0.92),
              'age': (34, 50), 'pits': 0.003, 'flat_top': False, 'buried': 0.2, 'tilt': 0.05,
              'surface': 'seaside_rock', 'grey': 0.25, 'tint': (1.0, 1.0, 1.0), 'what': 'stones worn smooth by water: rounded, flattened, no edges'},
}
ORDER = ('boulder', 'angular', 'flat', 'river')
BAND = 1.6                       # the sizes within one size band span at most this factor
MATERIAL_PREFIX = 'rocks • '
# the moss's darkest green (linear; its cushions vary lighter and yellower): the brighter green of the owner's garden
# picture, which the garden's rocks pass used (the tool's first green, MOSS_DARK, read grey-olive at dusk)
MOSS_COLOUR = (0.07, 0.105, 0.02)
MOSS_DARK = (0.05, 0.075, 0.018)

TOOL = {
    'name': 'rocks',
    'what': 'rocks made by rules, each its own shape from its seed (broken faces, edges rounded by weather, a flatter top '
            'on flat stones): weathered boulders, broken angular stone, flat stones and smooth river stones; scattered '
            'over a ground you give with Blender\'s particle system (sizes between two you give, big ones fewer, each '
            'turned, tilted with the ground and sunk into it, kept apart; a narrow area such as a pond\'s bank still gets '
            'as many as fit), laid as particle copies on spots you give (each its own shape at its own size, its top as '
            'high as you ask, never floating on dry ground), or set singly at points you give with real bumps; covered '
            'with photographed rock (PBR), each rock its own part, wet and dark at the feet, moss on top if asked (each '
            'rock its own amount if asked): real moss cushions with thickness and a pile of tufts (the moss tool), pale '
            'lichen on the bare stone, or the moss as a colour only; a dark wet water line where they stand in a pond',
    'call': "laid = rocks.scatter(yard, kind='boulder', count=24, sizes=(0.15, 0.9), area=(-3, -3, 3, 0), seed=2);  "
            "seat = rocks.at_spots([(2.2, -2.0)], kind='flat', size=0.7, top=0.12, ground=yard, tilt=0.0, moss=0.9, water=0.0, seed=7);  "
            "big = rocks.place([(1.0, 2.0)], kind='boulder', size=1.4, ground=yard, moss=0.7, seed=5)",
    'options': {
        'ground': 'scatter: a mesh object to lay them on, not changed (required); at_spots and place: a ground to sit them '
                  'on, or None (z as given)',
        'kind': "'boulder', 'angular', 'flat' or 'river' ('boulder')",
        'count': 'scatter: how many rocks; fewer if the area cannot hold them apart, the result\'s placed says how many (30)',
        'sizes': 'scatter: the smallest and largest, metres across ((0.15, 0.9))',
        'fall': 'scatter: how fast the numbers fall with size: 2 gives about four times as many rocks half the size (2.0)',
        'area': 'scatter: None (the whole ground), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], a function '
                'of an (n, 2) array of points giving weights 0 to 1, or a test of one place keep(x, y) giving True or '
                'False; a narrow area gets more places to choose from when it comes up short (None)',
        'spacing': 'scatter: how far apart: 1 their feet just touch, 0.7 they lean together, 1.5 a gap (1.0)',
        'gather': 'scatter: 0 the smaller rocks spread evenly, 1 they gather at the feet of the bigger ones (0.0)',
        'spots': 'at_spots: a list of (x, y) or (x, y, z) places, one rock each (required)',
        'top': 'at_spots: the height each rock\'s highest point should reach, one number, one per spot, or None to sit '
               'it at the soil line; on dry ground never left floating (lowered into the soil); with water given, one '
               'whose foot is under the water stands as asked (None)',
        'facing': 'at_spots: the ground\'s facing, the rock\'s up: one (x, y, z), one per spot, or None (the ground\'s '
                  'own under each spot, or straight up) (None)',
        'name': "at_spots: the sheets' name (None: 'rocks <kind> at spots')",
        'points': 'place: a list of (x, y) or (x, y, z) points (required)',
        'size': 'at_spots and place: metres across, one number or one per spot (1.0)',
        'turn': 'place: degrees about the upright, one number, one per point, or None for random (None)',
        'relief': 'at_spots and place: metres of real bumps from the height picture, 0 none; at_spots one number or one '
                  'per spot (at_spots 0.0, place 0.04)',
        'detail': 'at_spots and place: how finely the bumps are made, 1 to 3 (2)',
        'buried': 'share of each rock\'s height sunk in the soil, 0.05 to 0.8 (None: boulder 0.42, angular 0.25, flat 0.4, river 0.2)',
        'tilt': 'how far each rock tips from square on the ground, 0 to 0.3 (None: the kind\'s own, about 0.05)',
        'shapes': 'scatter: how many shapes each size band is copied from (8)',
        'surface': "the photographed rock set (None: boulder and flat 'lichen_rock', angular 'rock_wall_02', river 'seaside_rock')",
        'moss': 'moss on their tops: 0 none, 1 thick (0.0); real cushions with tufts unless moss_style=\'paint\'',
        'moss_style': "'cushions': real moss with thickness, spilling over the rims, a pile of tufts laid by the particle "
                      "system, the stone under and round it green, pale lichen on the bare stone (the moss tool); 'paint': the "
                      "moss as a colour on the stone only, as before 6 November 2026 (None: 'cushions')",
        'moss_thickness': 'the cushions\' depth in the middle, metres; on small rocks at most 0.08 of their size (0.03)',
        'moss_pile': 'the cushions\' tufts: 1 about 16,000 a square metre of cushion, 0 none, up to 3 (1.0)',
        'lichen': 'pale lichen crusts on the bare stone, 0 none to 1.5 (None: 0.6 on rocks with cushions, else 0)',
        'moss_colour': "the moss's darkest green, (red, green, blue), linear (None: the brighter green of the owner's "
                       "garden picture, (0.07, 0.105, 0.02); rocks.MOSS_DARK is the first, darker one)",
        'moss_spread': 'each rock its own amount of moss: the moss times a number between these two, by each rock\'s own '
                       'random number, such as (0.35, 1.4) (None: all the same)',
        'normal_strength': 'how strongly the photograph\'s normal picture shows its relief: 0 plain, 1 full, up to 2 '
                           '(None: the set\'s own, 1)',
        'water': 'the height of the water\'s surface where rocks stand in a pond: a dark wet band above it, the stone '
                 'darker below (None: no water line)',
        'water_band': 'how high the wet band climbs above the water, metres (0.07)',
        'wet_feet': 'how dark and glossy their feet are where the ground is wet, 0 to 1 (0.7)',
        'rain': 'how wet all over, 0 dry to 1 soaked (0.3)',
        'grey': 'how much greyer than the photograph, 0 its own colour to 1 grey (None: boulder 0.55, angular 0.45, flat 0.3, river 0.25)',
        'tint': 'a colour the photograph is multiplied by, (red, green, blue) (None: boulders a little green, (0.9, 1.0, 0.93))',
        'seed': 'the same seed, the same rocks (0)',
        'collection': "where the objects go (a new collection 'rocks')",
    },
    'materials': ['SURFACE • lichen_rock', 'SURFACE • rock_wall_02', 'SURFACE • seaside_rock', 'any SURFACE rock set'],
    'source': "made for the owner's word of 6 November 2026 (\"The next thing to work on is the rocks. They need to be "
              "procedurally generated in a particle system. And better textured\"), after the garden builders' hand-placed "
              "noise balls ('/home/claude/build-57-garden/closer pass/render_final.py', rock(), lines 747-810); the "
              "broken faces from stones.py's stone shapes; how garden rocks sit from the board brief/boards/japanese garden. "
              "From the garden's rocks pass ('/home/claude/build-57-garden/rocks/render_final.py', section 'rocks pass', "
              "lines 1940-2165), where the builder made by hand on top of this tool: at_spots() from its rocks_at() "
              "(lines 1968-2022: one particle copy per spot, each its own shape, its top at a height given, kept from "
              "floating on land only); the narrow area's extra places for its ground_part() (lines 2025-2036, the ground "
              "cut to the pond's bank so it got enough places), and keep(x, y) areas for its on_bank(); moss_spread "
              "from its 0.35 to 1.4 times by each rock's own random number (lines 2144-2163); the brighter moss green "
              "(0.07, 0.105, 0.02) it put in by hand (lines 2100-2112), now the default; normal_strength for its "
              "photograph relief at 1.0 (line 2107); the water line from its dark wet band above the pond (lines "
              "2113-2143); flat stones in lichen_rock as it put every rock (line 1954). The real moss cushions, their tufts "
              "and the lichen from the moss tool, after the owner's word on seeing that pass (\"Ok. I meant the rocks with "
              "moss. Not the pavement lol. Those are still lacking a lot of detail\")",
    'trap': 'the particle copies are drawn only when the picture is drawn (a ray from above cannot find them, so measure '
            'ground heights before scattering, and stand things on an at_spots rock by the top it gives back); real '
            'bumps come only on rocks set with place() or at_spots(relief=), at a cost in drawing time and memory (about '
            '80,000 faces a rock at detail 2); a rock\'s photograph is at its real size within a third (each size band is '
            'drawn from shapes made at its middle size); each rock\'s part of the picture is shifted, never turned (on a '
            'round rock a turned picture meets itself in hard seams); an area too small to hold the rocks apart holds '
            'fewer than asked, biggest first (widen it or give spacing=0.6); at_spots without water= pulls a rock asked '
            'to stand high in a deep pond down towards its bed (give the water\'s height); the water line goes by height '
            'alone, so every rock lower than the water darkens; moss_spread thins or thickens the moss of a single big '
            'object of your own as a whole; with a low sun ahead of the camera every rock is a dark lump: light them '
            'from the side; with moss the rocks carry real cushions and their tufts by default: a rock\'s highest point '
            '(at_spots\' top) is then on its moss, its faces grow by about a quarter and a scatter of mossy rocks draws a '
            'little slower (moss_style=\'paint\' for the colour only); scattered copies share their shapes\' cushions',
}


# ----------------------------------------------------------------------------------------------- the shapes

def _check_kind(kind):
    if kind not in KINDS:
        raise ValueError('kind is one of %s, not %r' % (', '.join(repr(k) for k in ORDER), kind))
    return KINDS[kind]


def _rock_bmesh(kind, seed, detail):
    """One rock shape 1 m long (its longest way across, along X), resting with its lowest point at z = 0, as a bmesh.
    detail: the voxel steps across 1 m when its skin is remade (about 30 for small rocks, 64 for big ones)."""
    spec = KINDS[kind]
    pick = random.Random(7919 * (ORDER.index(kind) + 1) + 104729 * seed)
    offset = Vector((pick.uniform(-200, 200), pick.uniform(-200, 200), pick.uniform(-200, 200)))
    width, height = pick.uniform(*spec['width']), pick.uniform(*spec['height'])
    lumps = spec['lumps'] * pick.uniform(0.75, 1.25)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4 if detail >= 40 else 3, radius=0.5)
    for vertex in bm.verts:
        direction = vertex.co.normalized()
        bulge = (noise.noise(direction * 1.1 + offset) * lumps + noise.noise(direction * 2.6 + offset * 1.3) * lumps * 0.45
                 + noise.noise(direction * 5.5 + offset * 0.7) * lumps * 0.15)
        vertex.co = direction * 0.5 * (1.0 + bulge)
        vertex.co.y *= width
        vertex.co.z *= height
    # the faces where it broke: flat cuts, a little hollow, in directions spread round it (a flat stone's top and bottom
    # first, almost level)
    cuts = []
    if spec['flat_top']:
        cuts.append((Vector((pick.uniform(-0.08, 0.08), pick.uniform(-0.08, 0.08), 1.0)).normalized(), pick.uniform(0.62, 0.78)))
        cuts.append((Vector((pick.uniform(-0.1, 0.1), pick.uniform(-0.1, 0.1), -1.0)).normalized(), pick.uniform(0.7, 0.85)))
    angle = pick.uniform(0.0, 2.0 * math.pi)
    for number in range(pick.randint(*spec['breaks'])):
        rise = pick.uniform(-0.35, 0.85) if not spec['flat_top'] else pick.uniform(-0.2, 0.2)
        cuts.append((Vector((math.cos(angle), math.sin(angle), rise)).normalized(), pick.uniform(*spec['cut'])))
        angle += 2.0 * math.pi * (0.618 + pick.uniform(-0.12, 0.12))
    for normal, depth in cuts:
        reach = max(v.co.dot(normal) for v in bm.verts)
        low = min(v.co.dot(normal) for v in bm.verts)
        plane = low + (reach - low) * (0.5 + 0.5 * depth) if depth > 0 else reach
        result = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6,
                                        plane_co=normal * plane, plane_no=normal, clear_outer=True)
        rim = [e for e in result['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        if rim:
            bmesh.ops.holes_fill(bm, edges=rim, sides=0)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return bm, pick, offset


def _remade(bm, detail, name):
    """The bmesh's skin remade as even small faces (Blender's voxel remesh), so weathering can round it evenly."""
    mesh = bpy.data.meshes.new(name + ' • first form')
    bm.to_mesh(mesh)
    bm.free()
    holder = bpy.data.objects.new(name + ' • first form', mesh)
    workshop = bpy.data.scenes.new('rocks • making')
    workshop.collection.objects.link(holder)
    remesh = holder.modifiers.new('even skin', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 1.0 / detail
    remesh.adaptivity = 0.0
    layer = workshop.view_layers[0]
    layer.update()
    depsgraph = layer.depsgraph
    if depsgraph is None:
        with bpy.context.temp_override(scene=workshop, view_layer=layer):
            depsgraph = bpy.context.evaluated_depsgraph_get()
    remade = bpy.data.meshes.new_from_object(holder.evaluated_get(depsgraph))
    bpy.data.objects.remove(holder)
    bpy.data.meshes.remove(mesh)
    bpy.data.scenes.remove(workshop)
    out = bmesh.new()
    out.from_mesh(remade)
    bpy.data.meshes.remove(remade)
    return out


def rock_mesh(kind='boulder', seed=0, size=1.0, buried=None, detail=48, name=None):
    """One rock's mesh, `size` metres long, its origin at the soil line: the lowest `buried` share of its height lies
    under z = 0. The same kind and seed give the same rock at any size."""
    spec = _check_kind(kind)
    name = name or 'rock %s %d' % (kind, seed)
    bm, pick, offset = _rock_bmesh(kind, seed, detail)
    bm = _remade(bm, detail, name)
    # weathering: the edges rounded by smoothing passes (an old rock many, a fresh break few), then its skin pitted
    passes = pick.randint(*spec['age'])
    for _ in range(passes):
        bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    pits = spec['pits']
    for vertex in bm.verts:
        p = vertex.co * 9.0 + offset
        grain = noise.noise(p) * 0.6 + noise.noise(p * 2.7) * 0.3 + noise.noise(p * 7.3) * 0.1
        vertex.co += vertex.normal * grain * pits
    if spec['flat_top']:                       # a flat stone's top worn nearly level, its rim rounded
        top = max(v.co.z for v in bm.verts)
        bottom = min(v.co.z for v in bm.verts)
        level = top - (top - bottom) * 0.12
        for vertex in bm.verts:
            if vertex.co.z > level:
                vertex.co.z = level + (vertex.co.z - level) * 0.35
    # 1 m long, centred over the origin, lowest point at the soil line minus its buried share
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    across = max(max(xs) - min(xs), max(ys) - min(ys))
    middle = Vector(((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0, min(zs)))
    share = spec['buried'] if buried is None else float(buried)
    share = min(0.85, max(0.03, share * pick.uniform(0.75, 1.25)))
    tall = (max(zs) - min(zs)) / across
    for vertex in bm.verts:
        vertex.co = (vertex.co - middle) / across * size
        vertex.co.z -= share * tall * size
    for face in bm.faces:
        face.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh['rock_kind'] = kind
    mesh['rock_seed'] = seed
    mesh['rock_buried'] = share
    mesh['rock_height'] = tall * size
    mesh['rock_weathering'] = passes
    return mesh


def _shapes(kind, seeds, size, buried, material, detail):
    """A collection (not in the scene) of rock shapes of one kind, made at `size`, for the particle copies; made once,
    then shared."""
    name = 'rocks shapes • %s • %.3f m • %s • %s • %s' % (kind, size, buried, material.name, '-'.join(str(s) for s in seeds))
    found = bpy.data.collections.get(name)
    if found is not None and len(found.objects) == len(seeds):
        return found
    shapes = bpy.data.collections.new(name)
    for seed in seeds:
        mesh = rock_mesh(kind, seed, size, buried, detail, name='rock shape %s %d' % (kind, seed))
        mesh.materials.append(material)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.track_axis = 'POS_Z'           # the particle system stands the shape's up (Z) on the ground's normal
        obj.up_axis = 'Y'
        if material.get('rocks_cushions'):
            _grow_cushions(obj, mesh, material, seed, size)
            if material.get('rocks_relief', 0.0) > 0:       # real bumps need a finer skin (after the pile)
                finer = obj.modifiers.new('finer for the bumps', 'SUBSURF')
                finer.subdivision_type = 'SIMPLE'
                finer.levels = 0
                finer.render_levels = 2
        shapes.objects.link(obj)
    return shapes


# ----------------------------------------------------------------------------------------------- the material

def _surface(kind, surface):
    name = surface or KINDS[kind]['surface']
    if not name.startswith('SURFACE'):
        name = 'SURFACE • ' + name
    try:
        material = store.material(name)
    except KeyError as missing:
        raise ValueError('surface is a photographed set on the shelf (such as lichen_rock): %s' % missing.args[0])
    if material is None or not material.name.startswith('SURFACE •'):
        raise ValueError('surface is a photographed set on the shelf (such as lichen_rock), not %r' % (surface,))
    return material


def _pieces_by_object(group):
    """A copy of the SURFACE materials' 'Pieces' group in which a rock without its own 'pp_piece' (a particle copy, or a
    rock set singly) takes its object's own random number instead, so each rock shows its own part of the picture."""
    name = 'rocks • pieces by object'
    found = bpy.data.node_groups.get(name)
    if found is not None:
        return found
    copy = group.copy()
    copy.name = name
    nodes, links = copy.nodes, copy.links
    target = None
    for node in nodes:
        if node.type == 'MATH' and node.operation == 'MAXIMUM' and all(
                s.is_linked and s.links[0].from_node.type == 'ATTRIBUTE' for s in node.inputs[:2]):
            target = node
    if target is None:
        return group
    info = nodes.new('ShaderNodeObjectInfo')
    spread = nodes.new('ShaderNodeMath')
    spread.operation = 'MULTIPLY_ADD'
    links.new(info.outputs['Random'], spread.inputs[0])
    spread.inputs[1].default_value = 0.98
    spread.inputs[2].default_value = 0.01
    either = nodes.new('ShaderNodeMath')
    either.operation = 'MAXIMUM'
    users = [link.to_socket for link in links if link.from_node == target]
    links.new(target.outputs[0], either.inputs[0])
    links.new(spread.outputs[0], either.inputs[1])
    for socket in users:
        links.new(either.outputs[0], socket)
    return copy


def _new_options(moss_colour, moss_spread, normal_strength, water, water_band):
    """The newer material options checked and made plain: (moss colour, moss spread, normal strength, water, band)."""
    colour = tuple(float(c) for c in (MOSS_COLOUR if moss_colour is None else moss_colour))
    if len(colour) != 3 or not all(0.0 <= c <= 1.0 for c in colour):
        raise ValueError('moss_colour is three numbers (red, green, blue), each 0 to 1, not %r' % (moss_colour,))
    spread = (1.0, 1.0) if moss_spread is None else tuple(float(c) for c in moss_spread)
    if len(spread) != 2 or not 0.0 <= spread[0] <= spread[1] <= 3.0:
        raise ValueError('moss_spread is two numbers, the first not bigger, 0 to 3 (such as (0.35, 1.4)), not %r' % (moss_spread,))
    if normal_strength is not None:
        normal_strength = float(normal_strength)
        if not 0.0 <= normal_strength <= 2.0:
            raise ValueError('normal_strength is 0 (plain) to 2 (twice the photograph\'s relief), not %r' % (normal_strength,))
    if water is not None:
        water = float(water)
        if not -1000.0 <= water <= 1000.0:
            raise ValueError('water is the water\'s height in metres, not %r' % (water,))
    water_band = float(water_band)
    if not 0.0 <= water_band <= 0.5:
        raise ValueError('water_band is 0 to 0.5 m, not %r' % (water_band,))
    return colour, spread, normal_strength, water, water_band


MOSS_STYLES = ('cushions', 'paint')


def _moss_options(moss, moss_style, moss_thickness, moss_pile, lichen):
    """The moss's style and its cushions' options checked: (style, thickness, pile, lichen). 'cushions' (the default):
    real moss with thickness and a pile of tufts, the moss tool's cushions; 'paint': the moss as a colour on the stone
    only, as before 6 November 2026."""
    style = 'cushions' if moss_style is None else moss_style
    if style not in MOSS_STYLES:
        raise ValueError("moss_style is 'cushions' (real moss with thickness and tufts) or 'paint' (a colour only), not %r" % (moss_style,))
    moss_thickness, moss_pile = float(moss_thickness), float(moss_pile)
    if not 0.002 <= moss_thickness <= 0.15:
        raise ValueError('moss_thickness is 0.002 to 0.15 m (3 cm: 0.03), not %r' % (moss_thickness,))
    if not 0.0 <= moss_pile <= 3.0:
        raise ValueError('moss_pile is 0 (no tufts) to 3, not %r' % (moss_pile,))
    lichen = (0.6 if style == 'cushions' and float(moss) > 0 else 0.0) if lichen is None else float(lichen)
    if not 0.0 <= lichen <= 1.5:
        raise ValueError('lichen is 0 (none) to 1.5, not %r' % (lichen,))
    return style, moss_thickness, moss_pile, lichen


def _grow_cushions(obj, mesh, material, seed, size):
    """Real moss on a rock made with a cushions material (its 'rocks_cushions'): cushions with thickness in the rock's
    own mesh (a second material, so the particle copies carry them) and the pile of tufts on the object (a hair particle
    system copying tufts); a rock with real bumps also gets its finer skin here, after the pile."""
    settings = material.get('rocks_cushions') if material is not None else None
    if not settings:
        return 0.0
    import moss as moss_tool
    c = json.loads(settings)
    pick = random.Random(7717 + int(seed))
    lo, hi = c.get('spread', [1.0, 1.0])
    amount = min(1.5, c['amount'] * pick.uniform(lo, hi))         # each shape its own amount of moss, as moss_spread asks
    area = moss_tool.on_mesh(mesh, amount=amount, thickness=min(c['thickness'], 0.08 * size), colour=c['colour'],
                             wet=c['wet'], seed=int(seed), base=0.5 * c['relief'] + 0.002, patch=min(0.16, 0.3 * size))
    if obj is not None:
        if obj.vertex_groups.get('moss pile') is None:
            obj.vertex_groups.new(name='moss pile')
        if c['pile'] > 0:
            moss_tool.pile(obj, area, c['pile'], 0.015, c['colour'], c['wet'], int(seed))
    return area


def _moss_each_its_own(copy, amount_node, spread):
    """Each rock its own amount of moss: the moss amount times a number between spread[0] and spread[1], by the rock's
    own random number (each particle copy has its own, and so has each rock set singly); shuffled first, so the amount
    of moss and the part of the picture a rock shows do not go together."""
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    info = nodes.new('ShaderNodeObjectInfo')
    shuffled = nodes.new('ShaderNodeMath')
    shuffled.operation = 'MULTIPLY_ADD'
    links.new(info.outputs['Random'], shuffled.inputs[0])
    shuffled.inputs[1].default_value = 17.31
    shuffled.inputs[2].default_value = 0.27
    own = nodes.new('ShaderNodeMath')
    own.operation = 'FRACT'
    links.new(shuffled.outputs[0], own.inputs[0])
    spread_node = nodes.new('ShaderNodeMapRange')
    spread_node.name = spread_node.label = 'Moss spread'
    spread_node.inputs['To Min'].default_value = spread[0]
    spread_node.inputs['To Max'].default_value = spread[1]
    links.new(own.outputs[0], spread_node.inputs['Value'])
    times = nodes.new('ShaderNodeMath')
    times.operation = 'MULTIPLY'
    times.inputs[1].default_value = amount_node.inputs[1].default_value
    links.new(spread_node.outputs['Result'], times.inputs[0])
    links.new(times.outputs[0], amount_node.inputs[1])


def _water_line(copy, water, band):
    """Where a rock stands in water: a dark wet band from `band` metres above the water's height down to it, and the
    stone darker and glossier below it (the height read from where each point is, so it works on particle copies)."""
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    geometry = nodes.new('ShaderNodeNewGeometry')
    height = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geometry.outputs['Position'], height.inputs['Vector'])
    line = nodes.new('ShaderNodeMapRange')
    line.name = line.label = 'Water line'
    line.inputs['From Min'].default_value = water + band
    line.inputs['From Max'].default_value = water - 0.01
    links.new(height.outputs['Z'], line.inputs['Value'])
    base = principled.inputs['Base Color']
    before = base.links[0].from_socket if base.links else None
    darker = nodes.new('ShaderNodeMix')
    darker.data_type = 'RGBA'
    darker.blend_type = 'MULTIPLY'
    links.new(line.outputs['Result'], darker.inputs[0])
    if before is not None:
        links.new(before, darker.inputs[6])
    else:
        darker.inputs[6].default_value = base.default_value
    darker.inputs[7].default_value = (0.42, 0.43, 0.4, 1.0)
    links.new(darker.outputs[2], base)
    rough = principled.inputs['Roughness']
    rough_before = rough.links[0].from_socket if rough.links else None
    glossy = nodes.new('ShaderNodeMix')
    glossy.data_type = 'FLOAT'
    links.new(line.outputs['Result'], glossy.inputs[0])
    if rough_before is not None:
        links.new(rough_before, glossy.inputs[2])
    else:
        glossy.inputs[2].default_value = rough.default_value
    glossy.inputs[3].default_value = 0.18
    links.new(glossy.outputs[0], rough)


def material(kind='boulder', surface=None, moss=0.0, wet_feet=0.7, rain=0.3, relief=0.0, grey=None, tint=None,
             moss_colour=None, moss_spread=None, normal_strength=None, water=None, water_band=0.07, moss_style=None,
             moss_thickness=0.03, moss_pile=1.0, lichen=None):
    """The rocks' material: a copy of a photographed rock SURFACE with each rock its own part of the picture, wet dark
    feet where the ground under it is wet (read through the UV the scatter or place writes: u is the ground's wetness),
    wet all over by `rain`, moss on top by `moss` (in `moss_colour`, each rock its own amount by `moss_spread`), the
    photograph's relief at `normal_strength`, a dark wet water line where it stands in water at the height `water`, and
    with `relief` metres of real bumps (for rocks set singly). Made once for the same choices, then shared; the store's
    own material is left as it was."""
    _check_kind(kind)
    source = _surface(kind, surface)
    moss, wet_feet, rain, relief = float(moss), float(wet_feet), float(rain), float(relief)
    grey = KINDS[kind]['grey'] if grey is None else float(grey)
    tint = tuple(float(c) for c in (KINDS[kind]['tint'] if tint is None else tint))
    if len(tint) != 3 or not all(0.0 <= c <= 2.0 for c in tint):
        raise ValueError('tint is three numbers (red, green, blue) each 0 to 2, not %r' % (tint,))
    for value, label, high in ((moss, 'moss', 1.5), (wet_feet, 'wet_feet', 1.0), (rain, 'rain', 1.0), (relief, 'relief', 0.5),
                               (grey, 'grey', 1.0)):
        if not 0.0 <= value <= high:
            raise ValueError('%s is 0 to %s, not %r' % (label, high, value))
    colour, spread, normal_strength, water, water_band = _new_options(moss_colour, moss_spread, normal_strength, water, water_band)
    style, moss_thickness, moss_pile, lichen = _moss_options(moss, moss_style, moss_thickness, moss_pile, lichen)
    name = '%s%s • %s%s%s%s%s' % (MATERIAL_PREFIX, source.name.replace('SURFACE • ', ''), kind,
                                  ' • moss %.2f' % moss if moss > 0 else '', ' • bumps %.3f m' % relief if relief > 0 else '',
                                  ' • water %.2f m' % water if water is not None else '',
                                  ' • cushions' if style == 'cushions' and moss > 0 else '')
    key = '%s|%.3f|%.3f|%.3f|%.3f|%.3f|%.3f,%.3f,%.3f' % (source.name, moss, wet_feet, rain, relief, grey, *tint)
    if moss > 0:
        key += '|moss %.4f,%.4f,%.4f|%.3f-%.3f' % (*colour, *spread)
    if normal_strength is not None:
        key += '|normal %.3f' % normal_strength
    if water is not None:
        key += '|water %.4f %.4f' % (water, water_band)
    if moss > 0 and style == 'cushions':
        key += '|cushions %.4f %.3f' % (moss_thickness, moss_pile)
    if lichen > 0:
        key += '|lichen %.3f' % lichen
    found = bpy.data.materials.get(name)
    if found is None or found.get('rocks_key') != key:
        found = next((m for m in bpy.data.materials if m.name.startswith(name) and m.get('rocks_key') == key), found)
    if found is not None and found.get('rocks_key') == key:
        return found
    copy = source.copy()
    copy.name = name
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    if normal_strength is not None and nodes.get('Normal picture') is not None and 'Strength' in nodes['Normal picture'].inputs:
        nodes['Normal picture'].inputs['Strength'].default_value = normal_strength
    pieces = nodes.get('Pieces')
    if pieces is not None and pieces.type == 'GROUP' and pieces.node_tree is not None:
        pieces.node_tree = _pieces_by_object(pieces.node_tree)
        if 'Shade' in pieces.inputs:
            pieces.inputs['Shade'].default_value = 0.2
        if 'Turn' in pieces.inputs:
            # never turned: the turn is about the axis a face looks along most, which on a round rock changes from place
            # to place, so turned pictures meet in hard seams (a dark patch cut sharp across a boulder); shifted only
            pieces.inputs['Turn'].default_value = 0.0
    for node in nodes:
        if node.type == 'TEX_IMAGE' and node.projection == 'BOX':
            node.projection_blend = 0.5        # a round rock: the three sides of the box blend softly, no seams
    weather = nodes.get('Weather')
    if weather is not None and 'Color' in weather.inputs and weather.inputs['Color'].is_linked and (grey > 0 or tint != (1.0, 1.0, 1.0)):
        # the photograph's colour made greyer (garden granite is grey; a photograph under warm light reads brown) and tinted
        photograph = weather.inputs['Color'].links[0].from_socket
        greyer = nodes.new('ShaderNodeHueSaturation')
        greyer.inputs['Saturation'].default_value = 1.0 - grey
        links.new(photograph, greyer.inputs['Color'])
        tinted = nodes.new('ShaderNodeMix')
        tinted.data_type = 'RGBA'
        tinted.blend_type = 'MULTIPLY'
        tinted.inputs[0].default_value = 1.0
        links.new(greyer.outputs['Color'], tinted.inputs[6])
        tinted.inputs[7].default_value = (*tint, 1.0)
        links.new(tinted.outputs[2], weather.inputs['Color'])
    if weather is not None:
        if 'Wet' in weather.inputs:
            weather.inputs['Wet'].default_value = rain
        if 'Grime' in weather.inputs:
            weather.inputs['Grime'].default_value = max(weather.inputs['Grime'].default_value, 0.35)
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    if wet_feet > 0:
        # the feet: the rock's own height above the soil line (its origin), up to 0.14 m, times the ground's wetness
        coordinates = nodes.new('ShaderNodeTexCoord')
        coordinates.from_instancer = True              # a particle copy reads the UV of the sheet it stands on
        own = nodes.new('ShaderNodeTexCoord')
        height = nodes.new('ShaderNodeSeparateXYZ')
        links.new(own.outputs['Object'], height.inputs['Vector'])
        uv = nodes.new('ShaderNodeSeparateXYZ')
        links.new(coordinates.outputs['UV'], uv.inputs['Vector'])
        foot = nodes.new('ShaderNodeMapRange')
        foot.inputs['From Min'].default_value = 0.14
        foot.inputs['From Max'].default_value = -0.02
        links.new(height.outputs['Z'], foot.inputs['Value'])
        soft = nodes.new('ShaderNodeMath')
        soft.operation = 'POWER'
        links.new(foot.outputs['Result'], soft.inputs[0])
        soft.inputs[1].default_value = 1.6
        wet_here = nodes.new('ShaderNodeMath')
        wet_here.operation = 'MULTIPLY'
        links.new(soft.outputs[0], wet_here.inputs[0])
        links.new(uv.outputs['X'], wet_here.inputs[1])
        amount = nodes.new('ShaderNodeMath')
        amount.operation = 'MULTIPLY'
        amount.use_clamp = True
        links.new(wet_here.outputs[0], amount.inputs[0])
        amount.inputs[1].default_value = wet_feet
        base = principled.inputs['Base Color']
        before = base.links[0].from_socket if base.links else None
        darker = nodes.new('ShaderNodeMix')
        darker.data_type = 'RGBA'
        darker.blend_type = 'MULTIPLY'
        links.new(amount.outputs[0], darker.inputs[0])
        if before is not None:
            links.new(before, darker.inputs[6])
        darker.inputs[7].default_value = (0.5, 0.49, 0.48, 1.0)
        links.new(darker.outputs[2], base)
        rough = principled.inputs['Roughness']
        rough_before = rough.links[0].from_socket if rough.links else None
        glossy = nodes.new('ShaderNodeMix')
        glossy.data_type = 'FLOAT'
        links.new(amount.outputs[0], glossy.inputs[0])
        if rough_before is not None:
            links.new(rough_before, glossy.inputs[2])
        else:
            glossy.inputs[2].default_value = rough.default_value
        glossy.inputs[3].default_value = 0.2
        links.new(glossy.outputs[0], rough)
    if relief > 0:
        height_picture = next((n for n in nodes if n.type == 'TEX_IMAGE' and n.image and '_disp' in n.image.name), None)
        output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        if height_picture is not None:
            bumps = nodes.new('ShaderNodeDisplacement')
            bumps.inputs['Midlevel'].default_value = 0.5
            bumps.inputs['Scale'].default_value = relief
            links.new(height_picture.outputs['Color'], bumps.inputs['Height'])
            links.new(bumps.outputs['Displacement'], output.inputs['Displacement'])
            try:
                copy.displacement_method = 'BOTH'
            except AttributeError:
                copy.cycles.displacement_method = 'BOTH'
    if wet_feet > 0:
        amount.name = amount.label = 'Wet feet'
    if moss > 0 or lichen > 0:
        import moss as moss_tool
        before_moss = {n.name for n in copy.node_tree.nodes}
        if style == 'cushions':
            # the stone under and round the real cushions green (it follows them), in its cracks, pale lichen on the rest
            mossy = moss_tool.add(copy, amount=moss, foot=0.0, facing=(0.3, 0.9), scale=4.0, colour=colour, lichen=lichen,
                                  hollows=0.8)
        else:
            mossy = moss_tool.add(copy, amount=moss, foot=0.0, facing=(0.3, 0.9), scale=4.0, colour=colour, lichen=lichen)
        bpy.data.materials.remove(copy)
        mossy.name = name
        copy = mossy
    if moss > 0:
        # the moss tool's amount: the one clamped multiply it adds (named here, so a script can find it by its name)
        amount_node = next((n for n in copy.node_tree.nodes if n.name not in before_moss and n.type == 'MATH'
                            and n.operation == 'MULTIPLY' and n.use_clamp and not n.inputs[1].is_linked
                            and abs(n.inputs[1].default_value - moss) < 1e-5), None)
        if amount_node is not None:
            amount_node.name = amount_node.label = 'Moss amount'
            if spread != (1.0, 1.0):
                _moss_each_its_own(copy, amount_node, spread)
        elif spread != (1.0, 1.0):
            raise RuntimeError('the moss tool\'s amount was not found, so each rock cannot have its own moss')
    if water is not None:
        _water_line(copy, water, water_band)
    if moss > 0 and style == 'cushions':
        # what the shapes made with this material grow on their tops: real cushions with a pile of tufts (moss.on_mesh)
        copy['rocks_cushions'] = json.dumps({'amount': moss, 'thickness': moss_thickness, 'pile': moss_pile,
                                             'colour': list(colour), 'wet': max(0.3, rain), 'relief': relief,
                                             'spread': list(spread)})
    copy['rocks_relief'] = relief
    copy['rocks_key'] = key
    copy['store_what'] = 'rocks (%s) in %s' % (kind, source.name)
    return copy


# ----------------------------------------------------------------------------------------------- the ground

class _Ground:
    """The caller's ground as world triangles: places on it, its smooth normal there and its wetness."""

    def __init__(self, obj):
        if obj is None or obj.type != 'MESH' or not len(obj.data.polygons):
            raise ValueError('rocks need a ground: a mesh object with faces (the ground tool makes one)')
        mesh = obj.data
        mesh.calc_loop_triangles()
        tris = numpy.zeros(len(mesh.loop_triangles) * 3, dtype=numpy.int64)
        mesh.loop_triangles.foreach_get('vertices', tris)
        self.tris = tris.reshape(-1, 3)
        co = numpy.zeros(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get('co', co)
        matrix = numpy.array(obj.matrix_world)
        co = co.reshape(-1, 3)
        self.points = co @ matrix[:3, :3].T + matrix[:3, 3]
        normals = numpy.zeros(len(mesh.vertices) * 3)
        mesh.vertex_normals.foreach_get('vector', normals)
        normals = normals.reshape(-1, 3) @ numpy.linalg.inv(matrix[:3, :3])
        normals[normals[:, 2] < 0] *= -1.0
        self.normals = normals / numpy.maximum(numpy.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
        a, b, c = (self.points[self.tris[:, k]] for k in range(3))
        self.areas = 0.5 * numpy.linalg.norm(numpy.cross(b - a, c - a), axis=1)
        self.wetness = None
        attribute = mesh.attributes.get('wetness')
        if attribute is not None and attribute.domain == 'POINT' and attribute.data_type == 'FLOAT':
            values = numpy.zeros(len(mesh.vertices))
            attribute.data.foreach_get('value', values)
            self.wetness = numpy.clip(numpy.nan_to_num(values), 0.0, 1.0)
        self.tree = BVHTree.FromPolygons(self.points.tolist(), self.tris.tolist(), all_triangles=True)
        self.top = float(self.points[:, 2].max()) + 10.0

    def sample(self, rng, n, among=None):
        """n random places on the ground, spread by area: (positions (n, 3), normals (n, 3), wetness (n,)); `among`: only
        on these triangles (their numbers), or None for the whole ground."""
        if among is None:
            tri = rng.choice(len(self.tris), size=n, p=self.areas / self.areas.sum())
        else:
            areas = self.areas[among]
            tri = among[rng.choice(len(among), size=n, p=areas / areas.sum())]
        root = numpy.sqrt(rng.random(n))
        share = rng.random(n)
        bary = numpy.column_stack([1.0 - root, root * (1.0 - share), root * share])
        return self._at(tri, bary)

    def _at(self, tri, bary):
        corners = self.tris[tri]
        position = (self.points[corners] * bary[:, :, None]).sum(axis=1)
        normal = (self.normals[corners] * bary[:, :, None]).sum(axis=1)
        normal /= numpy.maximum(numpy.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
        wet = (self.wetness[corners] * bary).sum(axis=1) if self.wetness is not None else numpy.ones(len(tri))
        return position, normal, wet

    def under(self, x, y):
        """The ground straight under (x, y): (position, normal, wetness), or None where there is no ground."""
        hit = self.tree.ray_cast(Vector((x, y, self.top)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is None:
            return None
        tri = hit[2]
        a, b, c = (Vector(self.points[self.tris[tri, k]]) for k in range(3))
        p = hit[0]
        v0, v1, v2 = b - a, c - a, p - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01 or 1e-18
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        bary = numpy.clip(numpy.array([[1.0 - v - w, v, w]]), 0.0, 1.0)
        bary /= bary.sum()
        position, normal, wet = self._at(numpy.array([tri]), bary)
        return position[0], normal[0], wet[0]


def _weights(area):
    """The area as a function of an (n, 2) array of points giving weights 0 to 1."""
    if area is None:
        return lambda xy: numpy.ones(len(xy))
    if callable(area):
        how = []                 # 'array': area(xy) weighs many places at once; 'place': area(x, y) says keep or not

        def weigh(xy):
            xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
            weights = None
            if not how:
                try:
                    weights = area(xy)
                    how.append('array')
                except TypeError:            # a test of one place, keep(x, y), as a builder's own keep-or-not test
                    how.append('place')
            if weights is None:
                if how[0] == 'place':
                    try:
                        weights = [float(area(float(x), float(y))) for x, y in xy]
                    except TypeError as wrong:
                        raise ValueError('an area function weighs an (n, 2) array of places, or tests one place as '
                                         'keep(x, y); this one does neither (%s)' % wrong)
                else:
                    weights = area(xy)
            weights = numpy.asarray(weights, dtype=numpy.float64).reshape(-1)
            if len(weights) != len(xy):
                raise ValueError('the area function gave %d weights for %d points (one each, 0 to 1)' % (len(weights), len(xy)))
            return numpy.clip(numpy.nan_to_num(weights), 0.0, 1.0)
        return weigh
    values = list(area)
    if len(values) == 4 and all(isinstance(v, (int, float, numpy.number)) for v in values):
        x0, x1 = sorted((float(values[0]), float(values[2])))
        y0, y1 = sorted((float(values[1]), float(values[3])))
        return lambda xy: ((xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)).astype(float)
    try:
        polygon = numpy.array([(float(p[0]), float(p[1])) for p in values], dtype=numpy.float64)
    except (TypeError, IndexError, ValueError):
        raise ValueError('area is None, a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...] or a function; not %r' % (area,))
    if len(polygon) < 3:
        raise ValueError('a polygon area needs at least three (x, y) points')

    def inside(xy):
        x, y = xy[:, 0], xy[:, 1]
        found = numpy.zeros(len(xy), dtype=bool)
        previous = polygon[-1]
        for point in polygon:
            (xi, yi), (xj, yj) = point, previous
            if yi != yj:
                found ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            previous = point
        return found.astype(float)
    return inside


def _touched(surface_ground, weigh):
    """The ground's triangles the area reaches (a weight above 0 at a corner or at the middle) and the ring of triangles
    round them, as their numbers; None when it reaches none of them (then the whole ground is sampled)."""
    corners = weigh(surface_ground.points[:, :2]) > 0.0
    middles = weigh(surface_ground.points[surface_ground.tris].mean(axis=1)[:, :2]) > 0.0
    reached = middles | corners[surface_ground.tris].any(axis=1)
    if not reached.any():
        return None
    near = numpy.zeros(len(surface_ground.points), dtype=bool)
    near[surface_ground.tris[reached].ravel()] = True
    return numpy.flatnonzero(near[surface_ground.tris].any(axis=1))


def _bands(sizes, count, fall):
    """The size bands, smallest first: [(from, to, how many), ...], numbers falling with size by `fall`."""
    low, high = float(sizes[0]), float(sizes[1])
    if not 0.02 <= low <= high <= 8.0:
        raise ValueError('sizes are two numbers, metres across, the first not bigger: 0.02 to 8, not %r' % (sizes,))
    bands = max(1, int(math.ceil(math.log(high / low) / math.log(BAND) - 1e-9))) if high > low * 1.0001 else 1
    edges = [low * (high / low) ** (k / float(bands)) for k in range(bands + 1)]
    middles = [math.sqrt(edges[k] * edges[k + 1]) for k in range(bands)]
    shares = numpy.array([m ** -float(fall) for m in middles])
    shares /= shares.sum()
    numbers = numpy.floor(shares * count).astype(int)
    for k in numpy.argsort(-(shares * count - numbers))[:count - numbers.sum()]:
        numbers[k] += 1
    return [(edges[k], edges[k + 1], int(numbers[k])) for k in range(bands)]


def _sheet(name, spots, collection):
    """A mesh of tiny faces lying on the ground, one per spot, each facing the ground's normal there, with a UV map
    whose u is the ground's wetness there (the rocks' material reads it through the particle copies)."""
    side = 0.002
    verts, faces, uvs = [], [], []
    for position, normal, wet in spots:
        n = Vector(normal).normalized()
        p = Vector(position)
        t = n.orthogonal().normalized()
        b = n.cross(t)
        base = len(verts)
        for k in range(3):
            a = 2.0 * math.pi * k / 3.0
            verts.append(tuple(p + (t * math.cos(a) + b * math.sin(a)) * side))
        faces.append((base, base + 1, base + 2))
        uvs.extend([(float(wet), 0.5)] * 3)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    layer = mesh.uv_layers.new(name='UVMap')
    layer.data.foreach_set('uv', [c for uv in uvs for c in uv])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.show_instancer_for_render = False
    obj.show_instancer_for_viewport = False
    return obj


def _collection(collection):
    if collection is None:
        collection = bpy.data.collections.new('rocks')
        bpy.context.scene.collection.children.link(collection)
    elif isinstance(collection, str):
        named = bpy.data.collections.get(collection)
        if named is None:
            named = bpy.data.collections.new(collection)
            bpy.context.scene.collection.children.link(named)
        collection = named
    return collection


# ----------------------------------------------------------------------------------------------- scatter

def scatter(ground, kind='boulder', count=30, sizes=(0.15, 0.9), fall=2.0, area=None, spacing=1.0, gather=0.0,
            buried=None, tilt=None, shapes=8, surface=None, moss=0.0, wet_feet=0.7, rain=0.3, grey=None, tint=None, seed=0,
            collection=None, moss_colour=None, moss_spread=None, normal_strength=None, water=None, water_band=0.07,
            moss_style=None, moss_thickness=0.03, moss_pile=1.0, lichen=None):
    """Rocks of one kind over the ground, within the area, by Blender's particle system (see the note at the top).
    Returns {'objects': the sheets (one per size band), 'placed': how many, 'asked': count, 'bands': [(from, to, laid)],
    'spots': [(x, y, z, size_from, size_to)], 'material': the material, 'shapes': the shape collections}."""
    spec = _check_kind(kind)
    count = int(count)
    if not 1 <= count <= 20000:
        raise ValueError('count is 1 to 20000 rocks, not %r' % (count,))
    if not 0.4 <= float(spacing) <= 3.0:
        raise ValueError('spacing is 0.4 to 3 (1: their feet just touch), not %r' % (spacing,))
    if not 0.0 <= float(gather) <= 1.0:
        raise ValueError('gather is 0 to 1, not %r' % (gather,))
    if not 0.0 <= float(fall) <= 4.0:
        raise ValueError('fall is 0 (as many big as small) to 4, not %r' % (fall,))
    tilt = spec['tilt'] if tilt is None else float(tilt)
    if not 0.0 <= tilt <= 0.3:
        raise ValueError('tilt is 0 to 0.3, not %r' % (tilt,))
    if buried is not None and not 0.05 <= float(buried) <= 0.8:
        raise ValueError('buried is 0.05 to 0.8 of a rock\'s height, not %r' % (buried,))
    shapes = int(shapes)
    if not 1 <= shapes <= 32:
        raise ValueError('shapes is 1 to 32, not %r' % (shapes,))
    surface_ground = _Ground(ground)
    weigh = _weights(area)
    bands = _bands(sizes, count, fall)
    rng = numpy.random.default_rng(1000003 * int(seed) + 17 * ORDER.index(kind) + 5)
    # the places rocks may go: many random places on the ground, kept by the area's weights
    pool = max(4000, 60 * count)
    position, normal, wet = surface_ground.sample(rng, pool)
    keep = rng.random(pool) < weigh(position[:, :2])
    position, normal, wet = position[keep], normal[keep], wet[keep]
    order = rng.permutation(len(position))
    position, normal, wet = position[order], normal[order], wet[order]
    taken = numpy.zeros(len(position), dtype=bool)
    laid_xy, laid_r = [], []
    cell = max(0.82 * bands[-1][1] * float(spacing), 1e-3)     # a grid of cells as wide as the biggest rocks' reach, twice
    grid = {}
    material_made = material(kind, surface, moss, wet_feet, rain, 0.0, grey, tint, moss_colour=moss_colour,
                             moss_spread=moss_spread, normal_strength=normal_strength, water=water, water_band=water_band,
                             moss_style=moss_style, moss_thickness=moss_thickness, moss_pile=moss_pile, lichen=lichen)
    collection = _collection(collection)
    result = {'objects': [], 'placed': 0, 'asked': count, 'bands': [], 'spots': [], 'material': material_made, 'shapes': []}
    reached = []                                             # the triangles the area reaches, found when first needed

    def by_priority(first, reach):
        """The places from number `first` on, in the order they are tried (gathered at the feet of laid rocks if asked)."""
        priority = rng.random(len(position) - first)
        if gather > 0 and laid_xy:
            from scipy.spatial import cKDTree
            near_tree = cKDTree(numpy.array(laid_xy))
            distance, nearest = near_tree.query(position[first:, :2])
            ring = numpy.exp(-numpy.maximum(distance - numpy.array(laid_r)[nearest] - reach, 0.0) / max(4.0 * reach, 0.05))
            priority = priority / (1.0 + 6.0 * float(gather) * ring)
        return first + numpy.argsort(priority)

    def lay(order, reach, spots, wanted):
        for i in order:
            if taken[i]:
                continue
            x, y = float(position[i, 0]), float(position[i, 1])
            cx, cy = int(math.floor(x / cell)), int(math.floor(y / cell))
            crowded = False
            for gx in (cx - 1, cx, cx + 1):
                for gy in (cy - 1, cy, cy + 1):
                    for ox, oy, other in grid.get((gx, gy), ()):
                        if math.hypot(ox - x, oy - y) < reach + other:
                            crowded = True
                            break
                    if crowded:
                        break
                if crowded:
                    break
            if crowded:
                continue
            taken[i] = True
            laid_xy.append((x, y))
            laid_r.append(reach)
            grid.setdefault((cx, cy), []).append((x, y, reach))
            spots.append((position[i], normal[i], wet[i]))
            if len(spots) >= wanted:
                break

    for index in reversed(range(len(bands))):               # the biggest first: the small ones find room round them
        low, high, wanted = bands[index]
        if wanted <= 0:
            continue
        reach = 0.5 * 0.82 * high * float(spacing)           # a rock's foot: about 0.4 of its length from its middle
        spots = []
        lay(by_priority(0, reach), reach, spots, wanted)
        # a narrow area (a pond's bank on a big ground) gets few of the places spread over the whole ground: more places
        # are found on the triangles it reaches, round after round, until the band is full or a round lays nothing
        for _ in range(8):
            if len(spots) >= wanted:
                break
            if not reached:
                reached.append(_touched(surface_ground, weigh))
            more_position, more_normal, more_wet = surface_ground.sample(rng, pool, among=reached[0])
            keep = rng.random(pool) < weigh(more_position[:, :2])
            if not keep.any():
                break
            first = len(position)
            position = numpy.concatenate([position, more_position[keep]])
            normal = numpy.concatenate([normal, more_normal[keep]])
            wet = numpy.concatenate([wet, more_wet[keep]])
            taken = numpy.concatenate([taken, numpy.zeros(int(keep.sum()), dtype=bool)])
            before = len(spots)
            lay(by_priority(first, reach), reach, spots, wanted)
            if len(spots) == before:
                break
        result['bands'].append((low, high, len(spots)))
        if not spots:
            continue
        middle = math.sqrt(low * high)
        band_seeds = [int(seed) * 1000 + index * 50 + k for k in range(shapes)]
        detail = 64 if middle >= 0.6 else (44 if middle >= 0.25 else 30)
        made = _shapes(kind, band_seeds, middle, buried, material_made, detail)
        result['shapes'].append(made)
        name = 'rocks %s %.2f-%.2f m' % (kind, low, high)
        sheet = _sheet(name, spots, collection)
        modifier = sheet.modifiers.new('rocks', 'PARTICLE_SYSTEM')
        system = modifier.particle_system
        system.seed = int(seed) * 7 + index
        settings = system.settings
        settings.name = name
        settings.type = 'HAIR'
        settings.use_advanced_hair = True
        settings.count = len(spots)
        settings.hair_length = 1.0
        settings.emit_from = 'FACE'
        settings.distribution = 'JIT'
        settings.use_emit_random = False
        settings.use_even_distribution = True
        settings.userjit = 1
        settings.jitter_factor = 0.0
        settings.render_type = 'COLLECTION'
        settings.instance_collection = made
        settings.use_collection_pick_random = True
        settings.particle_size = high / middle
        settings.size_random = 1.0 - low / high
        settings.use_rotations = True
        settings.rotation_mode = 'NOR'
        settings.rotation_factor_random = tilt
        settings.phase_factor_random = 2.0
        settings.use_rotation_instance = False
        settings.use_scale_instance = True
        settings.display_method = 'RENDER'
        sheet['rocks_kind'] = kind
        sheet['rocks_sizes'] = (low, high)
        sheet['rocks'] = len(spots)
        result['objects'].append(sheet)
        result['placed'] += len(spots)
        result['spots'].extend((float(p[0]), float(p[1]), float(p[2]), low, high) for p, _, _ in spots)
    result['bands'].reverse()
    return result


# ----------------------------------------------------------------------------------------------- place

def _per_point(value, n, label):
    if value is None or isinstance(value, (int, float)):
        return [value] * n
    values = list(value)
    if len(values) != n:
        raise ValueError('%s is one number or one per point (%d points), not %r' % (label, n, value))
    return values


def place(points, kind='boulder', size=1.0, ground=None, turn=None, buried=None, tilt=None, surface=None, moss=0.0,
          wet_feet=0.7, rain=0.3, relief=0.04, detail=2, grey=None, tint=None, seed=0, collection=None, moss_colour=None,
          moss_spread=None, normal_strength=None, water=None, water_band=0.07, moss_style=None, moss_thickness=0.03,
          moss_pile=1.0, lichen=None):
    """Single rocks at the points you give (see the note at the top). Returns the rock objects, in the points' order."""
    spec = _check_kind(kind)
    points = [tuple(float(c) for c in p) for p in points]
    if not points or any(len(p) not in (2, 3) for p in points):
        raise ValueError('points is a list of (x, y) or (x, y, z) points')
    sizes = _per_point(size, len(points), 'size')
    turns = _per_point(turn, len(points), 'turn')
    if any(not 0.02 <= float(s) <= 8.0 for s in sizes):
        raise ValueError('size is 0.02 to 8 m across, not %r' % (size,))
    tilt = spec['tilt'] if tilt is None else float(tilt)
    if not 0.0 <= tilt <= 0.3:
        raise ValueError('tilt is 0 to 0.3, not %r' % (tilt,))
    if buried is not None and not 0.05 <= float(buried) <= 0.8:
        raise ValueError('buried is 0.05 to 0.8 of a rock\'s height, not %r' % (buried,))
    if int(detail) not in (1, 2, 3):
        raise ValueError('detail is 1, 2 or 3, not %r' % (detail,))
    surface_ground = _Ground(ground) if ground is not None else None
    made_material = material(kind, surface, moss, wet_feet, rain, relief, grey, tint, moss_colour=moss_colour,
                             moss_spread=moss_spread, normal_strength=normal_strength, water=water, water_band=water_band,
                             moss_style=moss_style, moss_thickness=moss_thickness, moss_pile=moss_pile, lichen=lichen)
    collection = _collection(collection)
    pick = random.Random(31337 + 101 * int(seed) + ORDER.index(kind))
    rocks_made = []
    for number, (point, rock_size, rock_turn) in enumerate(zip(points, sizes, turns)):
        x, y = point[0], point[1]
        z = point[2] if len(point) == 3 else 0.0
        up, wet = Vector((0.0, 0.0, 1.0)), 1.0
        if surface_ground is not None:
            found = surface_ground.under(x, y)
            if found is None:
                raise ValueError('there is no ground under the point (%.2f, %.2f)' % (x, y))
            z, up, wet = float(found[0][2]), Vector(found[1]), float(found[2])
        rock_seed = int(seed) * 1000 + 500 + number
        mesh = rock_mesh(kind, rock_seed, float(rock_size), buried, 64 if rock_size >= 0.5 else 44,
                         name='rock %s %d' % (kind, rock_seed))
        mesh.materials.append(made_material)
        cushioned = bool(made_material.get('rocks_cushions'))
        if cushioned:
            _grow_cushions(None, mesh, made_material, rock_seed, float(rock_size))
        layer = mesh.uv_layers.new(name='UVMap')
        layer.data.foreach_set('uv', [c for _ in range(len(mesh.loops)) for c in (wet, 0.5)])
        obj = bpy.data.objects.new('rock %s %d' % (kind, number), mesh)
        collection.objects.link(obj)
        if cushioned:
            obj.vertex_groups.new(name='moss pile')
            c = json.loads(made_material['rocks_cushions'])
            if c['pile'] > 0:
                import moss as moss_tool
                moss_tool.pile(obj, None, c['pile'], 0.015, c['colour'], c['wet'], rock_seed)
        angle = math.radians(float(rock_turn)) if rock_turn is not None else pick.uniform(0.0, 2.0 * math.pi)
        lean = Vector((pick.gauss(0.0, 1.0), pick.gauss(0.0, 1.0), 0.0)) * tilt * 0.6
        upright = (up + lean).normalized()
        frame = upright.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        obj.matrix_world = Matrix.Translation((x, y, z)) @ frame @ Matrix.Rotation(angle, 4, 'Z')
        if relief > 0:
            finer = obj.modifiers.new('finer for the bumps', 'SUBSURF')
            finer.subdivision_type = 'SIMPLE'
            finer.levels = 0
            finer.render_levels = int(detail)
        obj['pp_ground'] = z
        obj['rock_kind'] = kind
        rocks_made.append(obj)
    return rocks_made


# ----------------------------------------------------------------------------------------------- at_spots

def _per_spot_facing(facing, n):
    if facing is None:
        return [None] * n
    values = list(facing)
    if len(values) == 3 and all(isinstance(v, (int, float, numpy.number)) for v in values):
        return [Vector(values).normalized()] * n
    if len(values) != n:
        raise ValueError('facing is None, one (x, y, z) direction, or one per spot (%d spots), not %r' % (n, facing))
    out = []
    for value in values:
        if value is None:
            out.append(None)
            continue
        direction = Vector(tuple(float(c) for c in value))
        if len(direction) != 3 or direction.length < 1e-9:
            raise ValueError('a facing is an (x, y, z) direction, not %r' % (value,))
        out.append(direction.normalized())
    return out


def at_spots(spots, kind='boulder', size=1.0, top=None, ground=None, facing=None, buried=None, tilt=None, surface=None,
             moss=0.0, wet_feet=0.7, rain=0.3, relief=0.0, detail=2, grey=None, tint=None, moss_colour=None,
             moss_spread=None, normal_strength=None, water=None, water_band=0.07, seed=0, collection=None, name=None,
             moss_style=None, moss_thickness=0.03, moss_pile=1.0, lichen=None):
    """Rocks of one kind on spots you give, each a particle copy of its own rule-made shape made at its own size (one
    tiny face on a hidden sheet per rock, and a particle system that copies the shape onto it): rocks with a set place
    (a lantern's seat, a basin's front stone, the rocks a picture puts somewhere) laid by the particle system like the
    scattered ones. With `top`, a rock is set so its highest point reaches that height (the rock it replaces); on dry
    ground it is never left floating (lowered until most of its sunk part is in the soil), but where its foot is under
    the `water` you give it stands as asked, its foot hidden by the water.
    Returns {'objects': the sheets (one per rock), 'placed': how many, 'spots': [(x, y, z, size, top)] where z is the
    height its own soil line (its origin) was set at and top the height its highest point reached (a ray cannot find a
    particle copy: stand things on it by this), 'lowered': the spots' numbers that were lowered so as not to float, 'materials': the materials used (one per
    relief asked), 'shapes': the shape collections}."""
    spec = _check_kind(kind)
    spots = [tuple(float(c) for c in p) for p in spots]
    if not spots or any(len(p) not in (2, 3) for p in spots):
        raise ValueError('spots is a list of (x, y) or (x, y, z) places')
    n = len(spots)
    sizes = _per_point(size, n, 'size')
    tops = _per_point(top, n, 'top')
    reliefs = _per_point(relief, n, 'relief')
    facings = _per_spot_facing(facing, n)
    if any(not 0.02 <= float(s) <= 8.0 for s in sizes):
        raise ValueError('size is 0.02 to 8 m across, not %r' % (size,))
    if any(not 0.0 <= float(r) <= 0.5 for r in reliefs):
        raise ValueError('relief is 0 to 0.5 m, not %r' % (relief,))
    tilt = spec['tilt'] if tilt is None else float(tilt)
    if not 0.0 <= tilt <= 0.3:
        raise ValueError('tilt is 0 to 0.3, not %r' % (tilt,))
    if buried is not None and not 0.05 <= float(buried) <= 0.8:
        raise ValueError('buried is 0.05 to 0.8 of a rock\'s height, not %r' % (buried,))
    if int(detail) not in (1, 2, 3):
        raise ValueError('detail is 1, 2 or 3, not %r' % (detail,))
    surface_ground = _Ground(ground) if ground is not None else None
    if water is not None:
        water = float(water)
    collection = _collection(collection)
    name = name or 'rocks %s at spots' % kind
    materials = {}
    result = {'objects': [], 'placed': 0, 'spots': [], 'lowered': [], 'materials': [], 'shapes': []}
    for number, (spot, across, wanted_top, bumps, up) in enumerate(zip(spots, sizes, tops, reliefs, facings)):
        across, bumps = float(across), float(bumps)
        x, y = spot[0], spot[1]
        z = spot[2] if len(spot) == 3 else 0.0
        wet = 1.0
        if surface_ground is not None:
            found = surface_ground.under(x, y)
            if found is None:
                raise ValueError('there is no ground under the spot (%.2f, %.2f)' % (x, y))
            z, wet = float(found[0][2]), float(found[2])
            if up is None:
                up = Vector(found[1])
        up = up if up is not None else Vector((0.0, 0.0, 1.0))
        key = round(bumps, 4)
        if key not in materials:
            materials[key] = material(kind, surface, moss, wet_feet, rain, bumps, grey, tint, moss_colour=moss_colour,
                                      moss_spread=moss_spread, normal_strength=normal_strength, water=water,
                                      water_band=water_band, moss_style=moss_style, moss_thickness=moss_thickness,
                                      moss_pile=moss_pile, lichen=lichen)
        made_material = materials[key]
        shape_detail = 64 if across >= 0.6 else (44 if across >= 0.25 else 30)
        shapes = _shapes(kind, [int(seed) * 1000 + number], across, buried, made_material, shape_detail)
        shape = shapes.objects[0]
        finer = shape.modifiers.get('finer for the bumps')
        if bumps > 0 and finer is None:
            finer = shape.modifiers.new('finer for the bumps', 'SUBSURF')      # real bumps need a finer skin
            finer.subdivision_type = 'SIMPLE'
            finer.levels = 0
        if finer is not None:
            finer.render_levels = int(detail)
        shape_top = max(v.co.z for v in shape.data.vertices)                   # its highest point above its soil line
        soil = z
        if wanted_top is not None:
            z = float(wanted_top) - shape_top
            if surface_ground is not None:
                sunk = float(shape.data.get('rock_buried', 0.4)) * float(shape.data.get('rock_height', 0.3))
                foot_hidden = water is not None and z - sunk < water
                if z > soil + 0.8 * sunk and not foot_hidden:      # it would float: lowered into the soil
                    z = soil + 0.8 * sunk
                    result['lowered'].append(number)
        sheet = _sheet('%s %d' % (name, number), [((x, y, z), tuple(up), wet)], collection)
        modifier = sheet.modifiers.new('rocks', 'PARTICLE_SYSTEM')
        system = modifier.particle_system
        system.seed = int(seed) * 7 + number
        settings = system.settings
        settings.name = '%s %d' % (name, number)
        settings.type = 'HAIR'
        settings.use_advanced_hair = True
        settings.count = 1
        settings.hair_length = 1.0
        settings.emit_from = 'FACE'
        settings.distribution = 'JIT'
        settings.use_emit_random = False
        settings.use_even_distribution = True
        settings.userjit = 1
        settings.jitter_factor = 0.0
        settings.render_type = 'COLLECTION'
        settings.instance_collection = shapes
        settings.use_collection_pick_random = False
        settings.particle_size = 1.0
        settings.size_random = 0.0
        settings.use_rotations = True
        settings.rotation_mode = 'NOR'
        settings.rotation_factor_random = tilt
        settings.phase_factor_random = 2.0
        settings.use_rotation_instance = False
        settings.use_scale_instance = True
        settings.display_method = 'RENDER'
        sheet['rocks_kind'] = kind
        sheet['rocks_sizes'] = (across, across)
        sheet['rocks'] = 1
        result['objects'].append(sheet)
        result['shapes'].append(shapes)
        result['placed'] += 1
        result['spots'].append((x, y, z, across, z + shape_top))
    result['materials'] = list(materials.values())
    return result


# ----------------------------------------------------------------------------------------------- command line

def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--ground', help='the ground object (a mesh) to scatter rocks over')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--kind', default='boulder', choices=ORDER, help="the kind of rock; default 'boulder'")
    parser.add_argument('--count', type=int, default=30, help='how many rocks; default 30')
    parser.add_argument('--sizes', type=float, nargs=2, default=(0.15, 0.9), help='smallest and largest, metres; default 0.15 0.9')
    parser.add_argument('--area', type=float, nargs=4, help='a rectangle x0 y0 x1 y1 to scatter in; default the whole ground')
    parser.add_argument('--gather', type=float, default=0.0, help='0 spread evenly to 1 gathered at the feet of big ones; default 0')
    parser.add_argument('--moss', type=float, default=0.0, help='moss on their tops, 0 to 1; default 0')
    parser.add_argument('--moss-colour', type=float, nargs=3, help="the moss's darkest green, red green blue; default 0.07 0.105 0.02")
    parser.add_argument('--moss-spread', type=float, nargs=2, help='each rock its own amount of moss, such as 0.35 1.4; default all the same')
    parser.add_argument('--normal-strength', type=float, help="the photograph's relief, 0 plain to 2; default the set's own (1)")
    parser.add_argument('--water', type=float, help="the water's height, for a dark wet water line on rocks standing in it; default none")
    parser.add_argument('--water-band', type=float, default=0.07, help='how high the wet band climbs above the water, metres; default 0.07')
    parser.add_argument('--moss-style', choices=MOSS_STYLES, help="'cushions' real moss with tufts (default) or 'paint' a colour only")
    parser.add_argument('--moss-thickness', type=float, default=0.03, help="the cushions' depth, metres; default 0.03")
    parser.add_argument('--moss-pile', type=float, default=1.0, help="the cushions' tufts, 0 none to 3; default 1")
    parser.add_argument('--lichen', type=float, help='pale lichen on the bare stone, 0 to 1.5; default 0.6 with cushions')
    parser.add_argument('--seed', type=int, default=0, help='the same seed, the same rocks; default 0')
    args = parser.parse_args(argv)
    if not (args.blend and args.ground and args.out):
        parser.error('--blend, --ground and --out are needed to scatter rocks')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    ground = bpy.data.objects[args.ground]
    laid = scatter(ground, kind=args.kind, count=args.count, sizes=tuple(args.sizes), area=tuple(args.area) if args.area else None,
                   gather=args.gather, moss=args.moss, seed=args.seed, moss_colour=args.moss_colour,
                   moss_spread=args.moss_spread, normal_strength=args.normal_strength, water=args.water,
                   water_band=args.water_band, moss_style=args.moss_style, moss_thickness=args.moss_thickness,
                   moss_pile=args.moss_pile, lichen=args.lichen)
    print('rocks: %d of %d laid in %d size bands' % (laid['placed'], laid['asked'], len(laid['objects'])))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))


if __name__ == '__main__':
    main()
