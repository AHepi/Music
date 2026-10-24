# What this does: puts together "The Works", chapter 2's imagined place ("34 Plan - chapter 2 full redesign",
# part 1 "A. The Works", part "People", findings T1, T2, T8 and T15): two factories at the head of one short
# cobbled lane at blue dusk, seen from four views, and draws its plates and writes its files for the film.
#
# It opens the Works lane (works-lane.blend, built by pit-village/build_street.py with the settings in
# LANE_SETTINGS below; see build_works.sh) and adds:
#   - the cross street at the lane's mouth and, across it, a terrace on a raised footway (1 m up, a stone retaining
#     wall with railings and steps) whose middle house's upstairs window is W3's camera (eye 5.6 m above the lane);
#     a yard wall along the lane's corner houses
#   - the bank: a small stone-fronted building in place of the left terrace's third cottage, with a canted bay
#     window (its own glass, a material named bank-window-glass, dark until page 9), iron bars, a shallow room
#     behind (its light off unless --bank-lit), a brass plate "BANK" by the door and a hanging sign "BANK" on a
#     bracket at first-floor height, square to the lane so W3 sees it face-on (high enough that W1's camera,
#     which stands under it, never sees it)
#   - low walls with stone copings from the terraces' ends to the works wall
#   - the works wall across the lane's head (4 m, stone coping): No. 1's half dark red-brown brick, No. 2's
#     half pale buff; two 3 m gateways, each between brick piers with stone caps and a wrought-iron arch over
#     it (the gate arch) carrying the gate board; the high dividing wall between the two yards [T15], dark on the
#     lane's side and No. 1's, No. 2's buff brick inside No. 2's yard
#   - the two factories and the far town (assets/models/inflation-chapter-2-newcomers/works/*.glb), with the
#     ground levelled under the yards' setts (round 2: the lane's rutted ground showed through them)
#   - the two iron gates: OWN SURFACES, never in a plate; their leaves are separate objects the film swings
#     (works-gates.glb), No. 1's chained and padlocked
#   - the gate boards "No. 1" and "No. 2"; at each gate the PETROL and DIESEL drums standing in front of the waiting
#     men's outer end (No. 1's left, No. 2's right), both words turned to the gate view's camera; a gas lamp on each
#     outer pier's inner face, hanging over the gateway; the brazier against No. 1's right gate leaf, a lit hurricane
#     lantern and a lunch tin on No. 1's drums' lids
#   - crates in No. 2's gateway with the hand truck, a handcart loaded with crates at the right pavement's kerb, and
#     the crates that pop up in No. 1's gateway on "things" (own surfaces, never in a plate: works-pop-up.glb)
#   - the seven men waiting at No. 1, gathered in front of its shut gate (round 5: a loose crowd two deep, backs to the
#     camera, the stooped man at the brazier, a thin rim of light on them), and the eight men for No. 2's slowed state
#     gathered the same way (works-no-2-men.glb: painted in W2's slowed helper plate, dark own-surface silhouettes in W4)
#   - people at work inside each lit doorway, in dark clothes (round 5): No. 2's two in every No. 2 plate, No. 1's two
#     only once its men have gone in (painted into the plates; works-doorway-workers.glb for the record)
#   - inside No. 2's yard, for W4 (round 5): a work jacket with sleeves and drape folds hanging from a wooden peg on
#     the gate's inside post (the inner pier), a crate stood on end under it as a table with a flat cap (a real
#     peak), a tin mug and a pay envelope "WAGES" (2.6 times life size, so the word reads) propped against the
#     jacket's hem, all touching; the upturned crate at the post's foot by the hinge (seen from the lane too, so it
#     stays where it was); the back of No. 2's gate board lettered "No. 2" as well (a second board, back to back);
#     W4's own light: one warm pool on that corner from a lamp out of the frame, the rest of the yard in dusk, and
#     No. 2's gateway crates left out of W4's plate (the film hides them on page 14: works-shot.json w4.left_out)
#   - the people's own lights: the brazier's fire, the lantern, the gate lamps, the lane's gas lamps, No. 2's
#     lit doorway and gateway and the warm beam from its yard out through the gateway onto the pavement, a light
#     in each doorway's room of machines; No. 1's empty yard in a faint cool dusk light (so its shut gate's bars
#     show as a silhouette); one curtained window dimly lit on each gate view's quiet side; and four named cameras
#
# The four views (each camera level, at a person's spot, facing straight along the lane, never turning):
#   W3  both gates, from the end house's upstairs window across the cross street, on the lane's centre line
#   W1  No. 1's gate from its own (left) pavement, 0.4 m toward the kerb from the pavement's middle (or in line with
#       the gate's outer pier's edge, --gate-views), sliding 1.2 m toward the gate, from 10.0 m to 8.8 m from the
#       works wall (round 5: 3 m nearer than round 4)
#   W2  No. 2's gate, the mirror of W1 on the right pavement
#   W4  No. 2's gate from inside its yard, a little beside the gate's hinge post, looking out down the lane, sliding
#       1.2 m toward the gate, from 6.7 m to 5.5 m from it (round 5)
# Each has a plate spot and a composed spot (the end of its slide; W3 holds still, so the two are the same).
#
# Layout (metres, Blender space, z up): x across the lane (0 on its centre line, No. 1 at minus x); y up the
# lane (0 at its mouth, WALL_Y at the works wall's face); the factories' own layout (works_kit.py) is moved
# WALL_Y up the lane. In three.js a point (x, y, z) is (x, z, -y).
#
# Run (a virtual screen is needed for EEVEE: Xvfb :96 -screen 0 1920x1080x24 &):
#   DISPLAY=:96 blender -b works-lane.blend --python assemble_works.py -- [settings] [things to do]
# Settings:
#   --view w1|w2|w3|w4     the view the scene camera is left on (film lens, composed spot), for previews and the
#                          shot checker (default w3)
#   --state NAME           the state to dress for --view and --preview (default: the view's main state; see
#                          STATES: quiet, working, slowed, w4)
#   --gate-views pavement|pier   where W1 and W2 stand across their pavement: the pavement's middle (default) or
#                          in line with the outer pier's inner edge (the plan's first spot)
#   --gate-shift METRES    move both gates this far toward the lane's centre line (default 0; round 2's other
#                          suggestion), with their piers, boards, drums, lamps and the men
#   --bank-lit             light the bank's room and make its glass see-through (page 9's look)
# Things to do (any of):
#   --preview FILE         a small picture (540 x 960) of --view with the film's lens at its composed spot
#   --previews FOLDER      small pictures of every view in one go (PREVIEWS below; the shaders are made once), as
#                          VIEW-STATE.png; --only NAME,NAME draws only those
#   --plates FOLDER        the plates (PLATES below: 1536 x 2730, the plate's lens, at each view's plate spot, the gates'
#                          leaves, the chain and the pop-up crates never in them), as PNG; read Blender's log for
#                          "Shadow buffer full" and "Could not allocate shadow atlas"; --only NAME,NAME draws only those
#   --export               the film's files into the works folder (or --out FOLDER), see export_for_film
#   --save FILE            the dressed scene as a .blend (for looking at; no .blend1 backup)
#   --samples N            EEVEE samples (preview 16, plates 48)
#   --preview-width N      the previews' width (default 540; 1080 is the film's own size, which the shot checker's
#                          light rules judge more surely: dark figures at dusk have faint edges at half size)
# Then the shot checker (paper-film/tools/check-shot.sh, with BLEND=works-lane.blend and the check files
# examples/inflation-chapter-2-newcomers/works-VIEW-shot-check.json) measures --view.
# Light on this machine: EEVEE runs without a graphics card, and each light that casts shadows costs about two
# seconds a sample, so only the fire, the yards' spill and the dusk sky's light cast them (a plate takes about 6
# minutes at 48 samples; with every light casting shadows it was about 25).

import fnmatch
import json
import math
import os
import re
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'pit-village')))
import works_kit as kit            # noqa: E402
import set_dressing as dressing    # noqa: E402

KIT_FOLDER = kit.KIT_FOLDER
CHAPTER_MODELS = os.path.join(KIT_FOLDER, 'assets', 'models', 'inflation-chapter-2-newcomers')
WORKS_MODELS = kit.WORKS_FOLDER
PROPS_2 = os.path.join(CHAPTER_MODELS, 'props')
FIGURES = os.path.join(CHAPTER_MODELS, 'figures')
PIT_PROPS = dressing.PROPS_FOLDER
SCRIPT_NAME = 'assemble_works.py'

given = kit.arguments()
VIEW = kit.option('--view', 'w3')
STATE_ASKED = kit.option('--state')
GATE_VIEWS = kit.option('--gate-views', 'pavement')
GATE_SHIFT = float(kit.option('--gate-shift', '0'))
BANK_LIT = kit.flag('--bank-lit')
SAMPLES = kit.option('--samples')
PREVIEW_WIDTH = int(kit.option('--preview-width', '540'))
OUT_FOLDER = os.path.abspath(kit.option('--out', WORKS_MODELS))

# ------------------------------------------------------------------------------------------ the layout

# the lane as build_works.sh builds it with build_street.py (the settings are also written into the shot facts)
LANE_SETTINGS = ['--colliery', 'off', '--carriageway', '6', '--pavement', '2.2', '--length', '22', '--behind', '0',
                 '--slope', '0', '--cottages', '4']
KERB_X = 3.0                 # the kerb's face (the carriageway is 6 m)
KERB_TOP_X = 3.18            # the kerb stone's back edge, where the pavement's flags begin
HOUSE_FRONT_X = 5.2          # the terraces' fronts (the pavements are 2.2 m, kerb included)
PAVEMENT_MIDDLE_X = (KERB_X + HOUSE_FRONT_X) / 2
# W1 and W2 stand on their pavement 0.4 m toward the kerb from its middle (1.5 m from the house fronts): round 4. The
# nearest house front then fills less of the frame's side (to about 0.2 across, from 0.28), the lane head's corner by
# the outer pier (the brazier, the drums) shows clear of the terrace's end, and the lines still meet on the gate.
GATE_VIEW_X = PAVEMENT_MIDDLE_X - 0.4
# How far W1's and W2's plate spot and composed spot (the end of the 1.2 m slide) stand from the works wall's face. Round
# 5 brought both 3 m nearer (round 4: 13.0 and 11.8; round 4's check: the story sat small and high, 0.53 to 0.65 down,
# over a bare floor of paving), now that the waiting men stand gathered at the gate rather than in a queue down the
# kerb: the nearest man is then about 7 m from the composed spot, his feet about 0.72 down, the gate about half the
# frame's width.
GATE_VIEW_PLATE = 10.0
GATE_VIEW_COMPOSED = 8.8
COTTAGE_WIDTH = 4.5
TERRACE_END_Y = 18.0         # four cottages from the mouth (y = 0)
WALL_Y = 22.0                # the works wall's face on the lane side (the lane's length)
WALL_THICKNESS = 0.6
WALL_HEIGHT = 4.0
COPING = 0.2                 # the wall's stone coping
GATE_WIDTH = 3.0             # each gateway, pier to pier
GATE_CENTRE_X = 3.5 - GATE_SHIFT     # each gateway's middle (No. 1 at minus), 7 m apart unless shifted
OUTER_PIER_WIDTH = 0.9
INNER_PIER_WIDTH = 0.9       # wide enough for the jacket and cap on No. 2's inner pier's yard face (W4)
PIER_PROUD = 0.12            # how far the piers stand out from the wall's two faces
SIDE_WALL_X = 3.5 + 1.5 + 0.9                            # the corners' yard walls, in line with the outer piers' far edges
PIER_HEIGHT = 4.75
BOARD_BOTTOM = 4.08          # the gate board hangs from the gate arch, its top under the arch's lower band
GATE_PLANE_Y = WALL_Y + 0.3  # the gate leaves stand in the middle of the wall's thickness
DIVIDING_WALL_HEIGHT = 5.5   # higher than the works wall, so it shows over it and between the gates [T15]
SIDE_WALL_HEIGHT = 1.8       # the yard walls closing the corners at the lane's head
CROSS_STREET = {'north_kerb_y': -1.5, 'south_kerb_y': -6.5, 'far_side_y': -8.0}   # its carriageway is 5 m
END_TERRACE_FRONT_Y = CROSS_STREET['far_side_y']
# The end terrace stands on a raised footway 1 m above the cross street (a stone retaining wall with railings and a
# flight of steps), so W3's camera at its middle house's upstairs window has its eye 5.6 m above the lane. Round 3's
# check wanted the queue's tail in W3's bottom third (0.70 to 0.75 down) while W1, which stands on the same pavement
# to join the queue, keeps every man at least 6 m away: with the eye 4.6 m up the tail's feet could only reach 0.66.
RAISED_FOOTWAY = 1.0
STREET_TOP = 0.14            # the pavements' top, from which the views' eye heights are measured
W3_EYE = 5.6
BANK_Y = (2 * COTTAGE_WIDTH, 3 * COTTAGE_WIDTH)          # the bank stands where the left terrace's third cottage was
BANK_SIGN_Y = BANK_Y[0] + 0.42                           # its hanging sign, at the bank's near corner
BANK_SIGN_BOTTOM = 3.75                                  # first-floor height: above W1's frame (W1 stands under it)
LANE_LAMPS = [(-1, 1.0), (1, 0.6)]                       # gas lamps on the kerbs at the lane's mouth: behind W1's and W2's
                                                         # cameras and just below W3's frame; W4 sees them down the lane
FILM_FOV, PLATE_FOV = 60.4, 64.4
FILM_ASPECT = 1080 / 1920
SKY_STRENGTH = 1.6                                       # the blue dusk (about 1.4 to 1.96, as at the notice corner)


def gate_centre(prefix):
    return -GATE_CENTRE_X if prefix == 'no-1' else GATE_CENTRE_X


def outer_pier_inner_edge(prefix):
    """The x of the outer pier's face toward its gateway (the gate's hinge side on the outer pier)."""
    side = -1 if prefix == 'no-1' else 1
    return side * (GATE_CENTRE_X + GATE_WIDTH / 2)


def inner_pier_gate_edge(prefix):
    """The x of the inner pier's face toward its gateway (the inner leaf's hinge post)."""
    side = -1 if prefix == 'no-1' else 1
    return side * (GATE_CENTRE_X - GATE_WIDTH / 2)


def pavement_top(x, y):
    return dressing.ground_height(x, y, 2.0)


def gate_view_x(prefix):
    side = -1 if prefix == 'no-1' else 1
    if GATE_VIEWS == 'pier':
        return outer_pier_inner_edge(prefix) - side * 0.02
    return side * GATE_VIEW_X


# the views: plate spot and composed spot (x, y), eye height above what the camera stands on, which way it
# faces (+1 up the lane, -1 down it), and what it is about
def views():
    w1_x, w2_x = gate_view_x('no-1'), gate_view_x('no-2')
    w4_x = inner_pier_gate_edge('no-2') + W4_FROM_HINGE   # a little beside No. 2's inner leaf's hinge post (round 5)
    return {
        'w3': {'plate': (0.0, END_TERRACE_FRONT_Y + 0.05), 'composed': None, 'eye': W3_EYE, 'base': STREET_TOP, 'faces': 1,
               'stands_on': f'the end house\'s upstairs floor (the end terrace stands on a raised footway {RAISED_FOOTWAY:g} m above the '
                            f'street; the eye {W3_EYE:g} m above the lane\'s pavements)',
               'subject': (0.0, WALL_Y, 2.0), 'about': 'both gates, from the end house\'s upstairs window across the cross street'},
        'w1': {'plate': (w1_x, WALL_Y - GATE_VIEW_PLATE), 'composed': (w1_x, WALL_Y - GATE_VIEW_COMPOSED), 'eye': 1.7, 'faces': 1,
               'stands_on': 'the pavement', 'subject': (gate_centre('no-1'), GATE_PLANE_Y, 1.5),
               'about': 'No. 1\'s shut gate with the waiting men gathered in front of it'},
        'w2': {'plate': (w2_x, WALL_Y - GATE_VIEW_PLATE), 'composed': (w2_x, WALL_Y - GATE_VIEW_COMPOSED), 'eye': 1.7, 'faces': 1,
               'stands_on': 'the pavement', 'subject': (gate_centre('no-2'), GATE_PLANE_Y, 1.5), 'about': 'No. 2\'s open gate with nobody waiting'},
        'w4': {'plate': (w4_x, GATE_PLANE_Y + W4_PLATE_FROM_GATE), 'composed': (w4_x, GATE_PLANE_Y + W4_COMPOSED_FROM_GATE), 'eye': 1.7,
               'faces': -1, 'stands_on': 'No. 2\'s yard',
               # focused on the jacket and the WAGES envelope (the film's focus distance), the gate 1 m beyond
               'subject': (W4_GROUP_X, WALL_Y + WALL_THICKNESS + PIER_PROUD + 0.25, 1.1),
               'about': 'No. 2\'s gate from inside its yard, looking out down the lane: the jacket, cap, mug and WAGES of someone '
                        'with a job, and the men waiting outside the half-shut gate'},
    }


# W4 (round 5; round 4's check: the yard's bottom 30% bare, a flat cut-out jacket and a disc of a cap, the blank back of
# No. 2's board, "AY UP" on a crate cut by the frame, WAGES a white speck, the yard lit warm like daytime). The camera
# stands 0.2 m beside the hinge post's line, toward the gateway's middle, so the back of No. 2's board shows its whole
# "No. 2" in the composed frame (in line with the post its "No." was cut by the frame's left edge), and slides from 6.7
# m to 5.5 m from the gate (round 4: 7.2 to 6.0), so the WAGES letters come out about 20 pixels tall and the crate
# table's foot about 0.84 down. The group stands on No. 2's inner pier's yard face: hidden from W1, W2 and W3 by the
# pier itself (everything left of x 1.84 there), so it changes none of their plates.
W4_FROM_HINGE = 0.2
W4_PLATE_FROM_GATE, W4_COMPOSED_FROM_GATE = 6.7, 5.5
W4_GROUP_X = 1.375           # the peg and the crate table's middle, on the inner pier's yard face (x 1.1 to 2.0); the table
                             # then stands a clear 6 cm right of the upturned crate (at 1.45 their edges ran along each other)


# The states (plan 34's states table). men_1 / men_2: the waiting men at No. 1 / No. 2; workers_1 / workers_2: how many
# of each doorway's people at work show (round 5); pop_up_1: No. 1's pop-up crates show (own surfaces, never in a plate:
# for the previews and the shot checker, as the film shows them from "things"); windows: which thirds of each
# factory's windows are lit; doorway: its loading doorway lit; doors_open: No. 1's cart doors open; gate: each gate's
# leaves' angle (0 shut, 90 square to the wall, swung into the yard); spill: how strongly each factory's lit doorway
# and gateway light the yard and the lane (1 flat out). A state the film reaches by a time cut ("men gone", and the
# men's coming in "slowed") keeps the spill of the state before it, so the plates differ only where the men stood and
# where the windows changed (the state picture then swaps only that); "working" adds No. 1's spill, reached by a blend.
STATES = {
    'quiet': {'about': 'No. 1 quiet (7 men waiting, windows dark, gate shut and chained), No. 2 flat out (all lit, gate wide open, two '
                       'people at work in its doorway)',
              'men_1': True, 'men_2': False, 'workers_1': 0, 'workers_2': 2, 'windows_1': set(), 'doorway_1': False, 'doors_open_1': False,
              'windows_2': {1, 2, 3}, 'doorway_2': True, 'gate_1': 0, 'gate_2': 96, 'chained': True, 'spill_1': 0.0, 'spill_2': 1.0},
    'working': {'about': 'No. 1 working (the men gone in, two of them at its looms, every window lit, cart doors open, gate open, the '
                         'crates popped up in its gateway), No. 2 flat out',
                'men_1': False, 'men_2': False, 'workers_1': 2, 'workers_2': 2, 'pop_up_1': True, 'windows_1': {1, 2, 3}, 'doorway_1': True,
                'doors_open_1': True,
                'windows_2': {1, 2, 3}, 'doorway_2': True, 'gate_1': 84, 'gate_2': 96, 'chained': False, 'spill_1': 0.7, 'spill_2': 1.0},
    'men gone': {'about': 'No. 1 the moment after "go" (the men gone in, two of them at its looms, the gate open, its cart doors open and '
                          'doorway lit, its windows still dark), No. 2 flat out',
                 'men_1': False, 'men_2': False, 'workers_1': 2, 'workers_2': 2, 'windows_1': set(), 'doorway_1': True, 'doors_open_1': True,
                 'windows_2': {1, 2, 3}, 'doorway_2': True, 'gate_1': 84, 'gate_2': 96, 'chained': False, 'spill_1': 0.0, 'spill_2': 1.0},
    'quiet, no men': {'about': 'as quiet, with No. 1\'s seven men left out: what they hide (its cart doors shut, its doorway and '
                               'windows dark), for the behind picture of page 3\'s slide',
                      'men_1': False, 'men_2': False, 'workers_1': 0, 'workers_2': 2, 'windows_1': set(), 'doorway_1': False, 'doors_open_1': False,
                      'windows_2': {1, 2, 3}, 'doorway_2': True, 'gate_1': 0, 'gate_2': 96, 'chained': True, 'spill_1': 0.0, 'spill_2': 1.0},
    'slowed': {'about': 'No. 2 slowed (8 men waiting, a third of its windows lit, gate half shut, one person left at work in its '
                        'doorway); No. 1 quiet',
               'men_1': True, 'men_2': True, 'workers_1': 0, 'workers_2': 1, 'windows_1': set(), 'doorway_1': False, 'doors_open_1': False,
               'windows_2': {1}, 'doorway_2': True, 'gate_2': 42, 'gate_1': 0, 'chained': True, 'spill_1': 0.0, 'spill_2': 1.0},
    # W4's own light (round 5; round 4's check: warm light over 23.6% of the frame, the yard lit like daytime, the top
    # third too bright): No. 2's yard spill lights stay off in this view (spill_shares), one warm pool from a lamp out of
    # the frame falls on the jacket's corner (corner_lamp), and the rest of the yard is in the dusk. No. 2's three
    # gateway crates are left out (left_out): from inside the yard they stood big in the frame's bottom-left corner,
    # where the eye comes in, cut by the frame's edge ("AY UP"); the film hides them on page 14 by these names.
    'w4': {'about': 'page 14: No. 2 slowed seen from inside its yard, the 8 men outside its half-shut gate; one warm pool of lamplight '
                    'on the jacket\'s corner, the rest of the yard in the dusk, the gateway crates taken in',
           'men_1': False, 'men_2': True, 'workers_1': 0, 'workers_2': 1, 'windows_1': set(), 'doorway_1': False, 'doors_open_1': False,
           'windows_2': {1}, 'doorway_2': True, 'gate_2': 42, 'gate_1': 0, 'chained': True, 'spill_1': 0.0, 'spill_2': 1.0,
           'spill_shares': {'no-2-doorway-spill': 0.0, 'no-2-gateway-spill': 0.0, 'no-2-yard-spill': 0.0, 'no-2-gateway-beam': 0.0},
           'corner_lamp': True, 'left_out': ['no-2-crate-1', 'no-2-crate-2', 'no-2-crate-3']},
}
MAIN_STATE = {'w3': 'quiet', 'w1': 'quiet', 'w2': 'quiet', 'w4': 'w4'}

# The plates: name: (view, state, men_2 shown in the plate, what it is). The gates' leaves, the chain and the pop-up
# crates are never in a plate (own surfaces).
PLATES = {
    'works-w3-plate': ('w3', 'quiet', False, 'W3, the master: No. 1 quiet with its 7 men gathered at the gate, No. 2 flat out with two at work in its doorway'),
    'works-w1-plate': ('w1', 'quiet', False, 'W1 main: the 7 men waiting at the gate, No. 1\'s windows dark'),
    'works-w1-working-plate': ('w1', 'working', False, 'W1 helper: the men gone in (two at the looms), No. 1\'s windows lit, its cart doors open'),
    'works-w1-men-gone-plate': ('w1', 'men gone', False, 'W1 helper (for page 3\'s "go"): the men gone in (two at the looms), No. 1\'s '
                                                       'cart doors open, its windows still dark'),
    'works-w1-behind-plate': ('w1', 'quiet, no men', False, 'W1 helper (for page 3\'s slide): as the main plate with the 7 men left '
                                                           'out, its cart doors shut and windows dark, what the men hide'),
    'works-w2-plate': ('w2', 'quiet', False, 'W2 main: No. 2 flat out, two at work in its doorway, nobody at the gate'),
    'works-w2-slowed-plate': ('w2', 'slowed', True, 'W2 helper: No. 2 slowed, 8 men waiting at the gate, one left at work inside, two thirds '
                                                    'of its windows dark'),
    'works-w4-plate': ('w4', 'w4', False, 'W4: inside No. 2\'s yard, no men (they are own-surface silhouettes), no gate leaves, no gateway '
                                          'crates; one warm pool of lamplight on the jacket\'s corner, the rest in the dusk'),
}

# ------------------------------------------------------------------------------------------ small helpers

bpy.context.preferences.filepaths.save_version = 0      # no .blend1 backups
dressing.set_ground_fallback(0.0, 0.0)                    # the Works lane is level


def move_to_collection(objects, name):
    target = kit.collection(name)
    for o in objects:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        target.objects.link(o)


def import_glb(path, location=(0, 0, 0), turn=0.0, collection_name='props', name=None):
    """Imports a .glb into a collection under a holder (an empty named `name`) at location, turned about z."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    imported = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in imported if o.parent is None]
    holder = bpy.data.objects.new(name or os.path.basename(path)[:-4], None)
    kit.collection(collection_name).objects.link(holder)
    move_to_collection(imported, collection_name)
    for root in roots:
        root.parent = holder
    holder.location = location
    holder.rotation_euler = (0, 0, math.radians(turn))
    bpy.context.view_layer.update()
    return holder


def parts_of(holder):
    return [holder] + list(holder.children_recursive)


def bounds_of(objects):
    return kit.bounds([o for o in objects if o.type == 'MESH'])


def prop(file_name, x, y, turn=0.0, name=None, collection_name='props', folder=None, lift=0.0, start=2.0):
    """Stands a prop on whatever is under (x, y) (a ray down from `start`)."""
    return dressing.place_prop(file_name, x, y, turn, name=name, lift=lift, collection=collection_name, start=start,
                               folder=folder or PROPS_2)


def point_light(name, location, energy, colour, soft=0.3, shadow=True, collection_name='works-lights'):
    light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'POINT'))
    light.data.energy, light.data.color, light.data.shadow_soft_size = energy, colour, soft
    light.data.use_shadow = shadow
    light.location = location
    kit.collection(collection_name).objects.link(light)
    return light


def delete_objects(objects):
    for o in list(objects):
        bpy.data.objects.remove(o, do_unlink=True)


def same_pictures(first, second):
    """Two materials wear the same pictures (by name without Blender's .001 endings, and size)."""
    def pictures(material):
        if not material.use_nodes:
            return []
        return sorted((re.sub(r'\.\d{3}$', '', node.image.name), tuple(node.image.size)) for node in material.node_tree.nodes
                      if node.type == 'TEX_IMAGE' and node.image)
    return pictures(first) == pictures(second)


def merge_duplicate_materials():
    """A prop imported twice brings its materials twice ('crate-stencil' and 'crate-stencil.001'). The film finds
    the lettering by its exact material name, and every copy would carry its pictures again in the .glb, so a copy
    wearing the same pictures is replaced by the first."""
    merged = 0
    for material in list(bpy.data.materials):
        found = re.match(r'^(.*)\.\d{3}$', material.name)
        if not found:
            continue
        first = bpy.data.materials.get(found.group(1))
        if first is None or first == material or not same_pictures(first, material):
            continue
        for o in bpy.data.objects:
            if o.type == 'MESH':
                for slot in o.material_slots:
                    if slot.material == material:
                        slot.material = first
        merged += 1
    for image in list(bpy.data.images):
        found = re.match(r'^(.*)\.\d{3}$', image.name)
        first = bpy.data.images.get(found.group(1)) if found else None
        if first is not None and first != image and tuple(first.size) == tuple(image.size):
            image.user_remap(first)
    bpy.data.orphans_purge(do_recursive=True)
    return merged


# ------------------------------------------------------------------------------------------ the lane's changes

def level_ground_under_the_yards():
    """The lane's ground rises in ruts beyond its head (build_street's colliery yard); the factories' yard setts are
    only 2 cm above 0, so the ruts showed through them (round 2). Everything beyond the lane's head goes below them."""
    ground = bpy.data.objects['ground']
    lowered = 0
    for vertex in ground.data.vertices:
        point = ground.matrix_world @ vertex.co
        if point.y > WALL_Y - 0.5 and vertex.co.z > -0.08:
            vertex.co.z = -0.08
            lowered += 1
    ground.data.update()
    return lowered


def move_lane_lamps():
    """build_street.py stands one gas lamp at y 11 on the right kerb, where it would stand in front of W2's camera.
    The Works' lane lamps stand behind W1's and W2's cameras instead, one on each kerb."""
    iron = bpy.data.objects['gas_lamp_0_post'].data
    glass = bpy.data.objects['gas_lamp_0_glass'].data
    delete_objects([bpy.data.objects[name] for name in ('gas_lamp_0_post', 'gas_lamp_0_glass', 'gas_lamp_0_light', 'lamp_0')
                    if name in bpy.data.objects])
    for index, (side, y) in enumerate(LANE_LAMPS):
        x = side * (KERB_TOP_X + 0.35)
        foot = pavement_top(x, y)
        for part, data in (('post', iron), ('glass', glass)):
            o = bpy.data.objects.new(f'gas_lamp_{index}_{part}', data)
            o.location = (x, y, foot)
            kit.collection('lamps').objects.link(o)
        point_light(f'gas_lamp_{index}_light', (x, y, foot + 3.08), 200.0, (1.0, 0.72, 0.4), soft=0.12, collection_name='preview_lights')


DIM_WINDOWS = ('left_row_a_cottage_04_glass_upper_1', 'right_row_a_cottage_04_glass_upper_0')
DIM_SHARE = 0.6              # how bright a curtained window glows beside a lit one


def dim_window_material(lit_name):
    """A copy of a cottage's lit window glowing at DIM_SHARE of its brightness (a lamp behind drawn curtains)."""
    name = lit_name.replace('window_lit_glow_', 'window_dim_glow_')
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    material = bpy.data.materials[lit_name].copy()
    material.name = name
    for node in material.node_tree.nodes:
        for socket_name in ('Emission Strength', 'Strength'):
            socket = node.inputs.get(socket_name)
            if socket is not None and not socket.is_linked:
                socket.default_value *= DIM_SHARE
    return material


def cottage_objects(prefix):
    return [o for o in bpy.data.objects if o.name.startswith(prefix + '_') and o.type in ('MESH', 'LIGHT')]


def end_terrace():
    """A terrace across the cross street, facing up the lane (copies of the lane's own cottages turned to face +y).
    W3's camera stands in the upstairs window of its middle house; W4 sees the terrace at the end of the lane."""
    sources = ['right_row_a_cottage_01', 'left_row_a_cottage_02', 'right_row_a_cottage_02', 'left_row_a_cottage_04',
               'right_row_a_cottage_03', 'left_row_a_cottage_01', 'right_row_a_cottage_04']
    count = len(sources)
    made = 0
    for index, source in enumerate(sources):
        walls = bpy.data.objects.get(f'{source}_walls')
        if walls is None:
            continue
        # a cottage's front faces -x on the right of the lane and +x on the left; turn it to face +y
        facing = math.pi if source.startswith('right') else 0.0
        turn = math.pi / 2 - facing
        centre_x = (index - (count - 1) / 2) * COTTAGE_WIDTH
        source_place = Matrix.Translation(Vector((walls.location.x, walls.location.y, 0.0)))
        target = Matrix.Translation(Vector((centre_x, END_TERRACE_FRONT_Y, 0.0))) @ Matrix.Rotation(turn, 4, 'Z') @ source_place.inverted()
        for o in cottage_objects(source):
            copy = o.copy()
            copy.name = o.name.replace(source, f'end_row_cottage_{index + 1:02d}')
            copy.matrix_world = Matrix.Translation(Vector((0.0, 0.0, RAISED_FOOTWAY))) @ target @ o.matrix_world
            for c in o.users_collection:
                c.objects.link(copy)
            made += 1
    # slide the terrace along so that an upstairs window of its middle house stands on the lane's centre line
    bpy.context.view_layer.update()
    middle = f'end_row_cottage_{(count + 1) // 2:02d}'
    windows = [o.matrix_world.translation.x for o in bpy.data.objects if o.name.startswith(middle + '_glass_upper')]
    shift = -min(windows, key=abs) if windows else 0.0
    for o in bpy.data.objects:
        if o.name.startswith('end_row_cottage_'):
            o.location.x += shift
    return made


def cross_street():
    """The cross street at the lane's mouth: setts, kerbs and flagged pavements, and a yard wall where the lane's
    corner houses' back yards meet it."""
    setts = bpy.data.materials['street_setts']
    kerb = bpy.data.materials['kerb_stone']
    flags = bpy.data.materials['pavement_flags']
    brick = bpy.data.materials['cottage_brick']
    builder = kit.MeshBuilder()
    north, south, far = CROSS_STREET['north_kerb_y'], CROSS_STREET['south_kerb_y'], CROSS_STREET['far_side_y']
    reach = 40.0
    builder.box((-reach, south, -0.06), (reach, north, 0.04), setts)
    builder.box((-KERB_X, north, -0.06), (KERB_X, 0.0, 0.04), setts)                  # where the lane's setts meet it
    for x0, x1 in ((-reach, -KERB_X), (KERB_X, reach)):
        builder.box((x0, north, -0.2), (x1, north + 0.18, 0.13), kerb)
        builder.box((x0, north + 0.18, -0.1), (x1, 0.0, 0.14), flags)
    # the far side: a raised footway in front of the end terrace, a stone retaining wall at the carriageway's edge with
    # a coping and iron railings, and a flight of steps down to the street on the left
    stone = kit.surface_material('footway-wall-stone', 'large_sandstone_blocks', tint=(0.48, 0.46, 0.42), tile_metres=1.5)
    iron = kit.surface_material('footway-railing-iron', 'rusty_metal_02', tint=(0.07, 0.07, 0.07), roughness=0.55, metallic=0.6)
    top = STREET_TOP + RAISED_FOOTWAY
    wall_face, wall_back = south, south - 0.35
    steps = (-8.6, -7.1)                                    # the flight's ends along the street (outside W4's gateway)
    for x0, x1 in ((-reach, steps[0]), (steps[1], reach)):
        builder.box((x0, wall_back, -0.1), (x1, wall_face, top), stone)
        builder.box((x0, wall_back - 0.03, top), (x1, wall_face + 0.05, top + 0.12), stone)                 # the coping
    builder.box((-reach, far, -0.1), (reach, wall_back, top), flags)
    # the steps: five treads coming down from the footway into the street, between two sloping cheek walls
    treads = 5
    for k in range(treads):
        builder.box((steps[0], wall_back, -0.1), (steps[1], wall_face + 0.3 * (k + 1), top - (k + 1) * top / (treads + 1)), stone)
    for x in steps:
        builder.prism([(wall_back, -0.1), (wall_face + 0.3 * treads, -0.1), (wall_face + 0.3 * treads, 0.3), (wall_face, top + 0.25), (wall_back, top + 0.25)],
                      x - 0.12, x + 0.12, stone, axis='x')
    # the railings: posts every 0.25 m on the coping where the lane meets the street, a top rail and a foot rail
    for x0, x1 in ((-16.0, steps[0] - 0.15), (steps[1] + 0.15, 16.0)):
        x = x0
        while x <= x1 + 0.001:
            builder.rod((x, wall_back + 0.15, top + 0.12), (x, wall_back + 0.15, top + 1.0), 0.012, iron, sides=5)
            x += 0.25
        for z in (top + 0.24, top + 0.98):
            builder.rod((x0, wall_back + 0.15, z), (x1, wall_back + 0.15, z), 0.02, iron, sides=6)
    for side in (-1, 1):
        builder.box((side * 12.3 if side > 0 else -reach, -0.25, 0.0), (reach if side > 0 else -12.3, 0.0, 2.1), brick)
    builder.finish('cross-street', collection_name='cross-street')


def low_walls():
    """The corners at the lane's head: between each terrace's last cottage and the works wall the lane widens to the
    outer pier's far edge, flagged, closed on the outside by a yard wall with a stone coping. The PETROL and DIESEL
    drums stand there against the pier. (Along the house fronts' line, as first built, the drums stood between W1's
    camera and the brazier and hid it completely; behind a low wall's return they were hidden themselves.)"""
    stone = kit.surface_material('low-wall-coping', 'large_sandstone_blocks', tint=(0.5, 0.48, 0.44), tile_metres=1.5)
    brick_left = kit.surface_material('low-wall-brick-left', 'red_brick', tint=(0.5, 0.4, 0.36))
    brick_right = bpy.data.materials['cottage_stone']
    flags = bpy.data.materials['pavement_flags']
    builder = kit.MeshBuilder()
    for side, brick in ((-1, brick_left), (1, brick_right)):
        base = pavement_top(side * (HOUSE_FRONT_X - 0.1), (TERRACE_END_Y + WALL_Y) / 2)
        top = base + SIDE_WALL_HEIGHT
        x0, x1 = sorted((side * SIDE_WALL_X, side * (SIDE_WALL_X + 0.35)))
        builder.box((x0, TERRACE_END_Y - 0.05, 0.0), (x1, WALL_Y + 0.05, top), brick)
        builder.box((x0 - 0.05, TERRACE_END_Y - 0.05, top), (x1 + 0.05, WALL_Y + 0.05, top + 0.1), stone)
        f0, f1 = sorted((side * (HOUSE_FRONT_X + 0.25), side * SIDE_WALL_X))
        builder.box((f0, TERRACE_END_Y, -0.1), (f1, WALL_Y, base), flags)
    builder.finish('lane-head-corners', collection_name='works-wall')
    return pavement_top(-(HOUSE_FRONT_X - 0.1), 19.0) + SIDE_WALL_HEIGHT + 0.1     # the coping's top


# ------------------------------------------------------------------------------------------ the works wall

def works_wall():
    """The works wall across the lane's head, its gate piers, the iron gate arches and the dividing wall."""
    brick = {'no-1': kit.surface_material('works-wall-no-1-brick', 'castle_brick_02_red', tint=(0.36, 0.24, 0.2)),
             'no-2': kit.surface_material('works-wall-no-2-brick', 'white_sandstone_bricks', tint=(0.78, 0.73, 0.63))}
    pier_brick = {'no-1': kit.surface_material('works-pier-no-1-brick', 'large_red_bricks', tint=(0.5, 0.36, 0.3)),
                  'no-2': kit.surface_material('works-pier-no-2-brick', 'white_sandstone_bricks', tint=(0.86, 0.81, 0.7))}
    stone = kit.surface_material('works-coping-stone', 'large_sandstone_blocks', tint=(0.46, 0.44, 0.41), tile_metres=1.5)
    sooty = kit.surface_material('dividing-wall-brick', 'castle_brick_02_red', tint=(0.24, 0.18, 0.16))
    iron = kit.surface_material('works-gate-arch-iron', 'rusty_metal_02', tint=(0.07, 0.07, 0.07), roughness=0.55, metallic=0.6)
    y0, y1 = WALL_Y, WALL_Y + WALL_THICKNESS
    builder = kit.MeshBuilder()
    pieces = {}
    for prefix, side in (('no-1', -1), ('no-2', 1)):
        centre = gate_centre(prefix)
        near_edge, far_edge = centre - side * GATE_WIDTH / 2, centre + side * GATE_WIDTH / 2     # inner and outer
        outer_pier = sorted((far_edge, far_edge + side * OUTER_PIER_WIDTH))
        inner_pier = sorted((near_edge, near_edge - side * INNER_PIER_WIDTH))
        pieces[prefix] = {'outer_pier': outer_pier, 'inner_pier': inner_pier, 'opening': sorted((near_edge, far_edge))}
        # the wall from the outer pier out to the yard's side
        x0, x1 = sorted((outer_pier[0] if side < 0 else outer_pier[1], side * 24.0))
        builder.box((x0, y0, 0.0), (x1, y1, WALL_HEIGHT), brick[prefix])
        builder.box((x0, y0 - 0.06, WALL_HEIGHT), (x1, y1 + 0.06, WALL_HEIGHT + COPING), stone)
        # the yard's side wall back to the mill
        builder.box((min(side * 24.0, side * 24.6), y1, 0.0), (max(side * 24.0, side * 24.6), WALL_Y + 8.5, WALL_HEIGHT), brick[prefix])
        # the piers: brick, a stone plinth, a stone cap and a low pyramid on top
        for (x0, x1) in (outer_pier, inner_pier):
            builder.box((x0, y0 - PIER_PROUD, 0.0), (x1, y1 + PIER_PROUD, PIER_HEIGHT), pier_brick[prefix])
            builder.box((x0 - 0.03, y0 - PIER_PROUD - 0.03, 0.0), (x1 + 0.03, y1 + PIER_PROUD + 0.03, 0.45), stone)
            builder.box((x0 - 0.08, y0 - PIER_PROUD - 0.08, PIER_HEIGHT), (x1 + 0.08, y1 + PIER_PROUD + 0.08, PIER_HEIGHT + 0.2), stone)
            middle = ((x0 + x1) / 2, (y0 + y1) / 2)
            half_x, half_y = (x1 - x0) / 2, (y1 - y0) / 2 + PIER_PROUD
            top = PIER_HEIGHT + 0.2
            apex = builder.bm.verts.new((middle[0], middle[1], top + 0.3))
            corners = [builder.bm.verts.new((middle[0] + sx * half_x, middle[1] + sy * half_y, top)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            faces = [builder.bm.faces.new([corners[k], corners[(k + 1) % 4], apex]) for k in range(4)]
            builder._tag(faces, stone)
        # the gate arch: two iron bands from pier to pier rising over the gateway, with short bars between them
        x_left, x_right = pieces[prefix]['opening']
        half_span = (x_right - x_left) / 2
        for spring, rise, radius in ((4.3, 0.62, 0.028), (4.62, 0.78, 0.028)):
            bend = (half_span ** 2 + rise ** 2) / (2 * rise)
            points = []
            for k in range(17):
                along = -half_span + 2 * half_span * k / 16
                points.append(Vector((centre + along, GATE_PLANE_Y - 0.25, spring + math.sqrt(bend ** 2 - along ** 2) - (bend - rise))))
            for a, b in zip(points, points[1:]):
                builder.rod(a, b, radius, iron, sides=6)
            pieces[prefix].setdefault('arch', []).append({'spring': spring, 'rise': rise, 'bend': bend})
        lower, upper = pieces[prefix]['arch']
        for k in range(1, 16):
            along = -half_span + 2 * half_span * k / 16
            low_z = lower['spring'] + math.sqrt(lower['bend'] ** 2 - along ** 2) - (lower['bend'] - lower['rise'])
            high_z = upper['spring'] + math.sqrt(upper['bend'] ** 2 - along ** 2) - (upper['bend'] - upper['rise'])
            builder.rod((centre + along, GATE_PLANE_Y - 0.25, low_z), (centre + along, GATE_PLANE_Y - 0.25, high_z), 0.012, iron, sides=5)
        # two hangers for the board
        for along in (-0.5, 0.5):
            low_z = lower['spring'] + math.sqrt(lower['bend'] ** 2 - along ** 2) - (lower['bend'] - lower['rise'])
            builder.rod((centre + along, GATE_PLANE_Y - 0.25, low_z), (centre + along, GATE_PLANE_Y - 0.25, BOARD_BOTTOM + 0.7), 0.01, iron, sides=5)
    # between the two gates the wall rises as the end of the high dividing wall, which runs back between the two
    # yards to their back [T15]: one dark wall that belongs to neither works
    builder.finish('works-wall', collection_name='works-wall')
    # its own object, so a view can point at it: W3's lines meet on it
    # (its end between the gates is as high as the piers, so W3's lines meet on its coping, at the piers' heads; the
    # dividing wall rises higher behind it)
    m0, m1 = pieces['no-1']['inner_pier'][1], pieces['no-2']['inner_pier'][0]
    divider = kit.MeshBuilder()
    divider.box((m0, y0, 0.0), (m1, y1, PIER_HEIGHT), sooty)
    divider.box((m0, y0 - 0.06, PIER_HEIGHT), (m1, y1 + 0.06, PIER_HEIGHT + 0.18), stone)
    divider.box((-0.25, y1, 0.0), (0.25, WALL_Y + 20.0, DIVIDING_WALL_HEIGHT), sooty)
    divider.box((-0.31, y1, DIVIDING_WALL_HEIGHT), (0.31, WALL_Y + 20.0, DIVIDING_WALL_HEIGHT + 0.18), stone)
    # inside No. 2's yard its faces are No. 2's own buff brick (round 3's check: W4 saw No. 1's red brick right beside
    # No. 2's buff pier): a thin facing on the dividing wall's No. 2 side and on the yard side of its end between the
    # gates; the lane side and No. 1's side stay dark
    divider.box((0.25, y1, 0.0), (0.27, WALL_Y + 20.0, DIVIDING_WALL_HEIGHT), brick['no-2'])
    divider.box((0.0, y1, 0.0), (m1, y1 + 0.02, PIER_HEIGHT), brick['no-2'])
    divider.finish('dividing-wall', collection_name='works-wall')
    return pieces


# ------------------------------------------------------------------------------------------ the bank

def bank():
    """The small stone-fronted bank in place of the left terrace's third cottage (y 9 to 13.5), facing the lane (+x).
    A canted bay window with its own glass (bank-window-glass) and iron bars, a shallow room behind it, a door with a
    stone surround and the brass plate, two upstairs windows, a cornice and parapet, a slate roof."""
    delete_objects({o for o in bpy.data.objects if o.name.startswith('left_row_a_cottage_03_')})
    ashlar = kit.surface_material('bank-ashlar', 'large_sandstone_blocks', tint=(0.66, 0.62, 0.55), tile_metres=1.2)
    dark_stone = kit.surface_material('bank-plinth', 'large_sandstone_blocks', tint=(0.36, 0.34, 0.31), tile_metres=1.2)
    slate = bpy.data.materials['roof_slate']
    paint = bpy.data.materials['paint_black']
    door_paint = bpy.data.materials['paint_bottle_green']
    room = kit.surface_material('bank-room-wall', 'grey_plaster_02', tint=(0.62, 0.52, 0.38))
    room_floor = kit.surface_material('bank-room-counter', 'distressed_painted_planks', tint=(0.32, 0.2, 0.12))
    upper_glass = kit.plain_material('bank-upper-glass', (0.03, 0.035, 0.045), roughness=0.15)
    iron = kit.surface_material('bank-bar-iron', 'rusty_metal_02', tint=(0.06, 0.06, 0.06), roughness=0.5, metallic=0.6)
    glass = bpy.data.materials.new('bank-window-glass')
    glass.use_nodes = True
    shader = glass.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (0.035, 0.04, 0.05, 1)
    shader.inputs['Roughness'].default_value = 0.12
    glass['tile_metres'] = 1.0
    if BANK_LIT:
        dressing.see_through(glass, 0.25)
        if hasattr(glass, 'surface_render_method'):
            glass.surface_render_method = 'BLENDED'
    front = -HOUSE_FRONT_X                       # the front's face (it faces +x)
    back = front - 7.0
    y0, y1 = BANK_Y[0] + 0.02, BANK_Y[1] - 0.02
    floor = pavement_top(front + 0.1, (y0 + y1) / 2)
    eaves, parapet = 6.6, 7.25
    bay = (y0 + 0.43, y0 + 2.43)                 # the bay window's opening along the front
    door = (y1 - 1.18, y1 - 0.33)
    uppers = [(y0 + 0.9, y0 + 1.9), (y0 + 2.6, y0 + 3.6)]
    sill, head = floor + 0.75, floor + 2.65
    upper_sill, upper_head = 3.95, 5.3
    builder = kit.MeshBuilder()
    wall_back = front - 0.35
    # the front wall, built in bands round its openings
    def band(z0, z1, gaps):
        edges = [y0] + [v for gap in sorted(gaps) for v in gap] + [y1]
        for k in range(0, len(edges), 2):
            if edges[k + 1] - edges[k] > 0.001:
                builder.box((wall_back, edges[k], z0), (front, edges[k + 1], z1), ashlar)
    door_z = door_top(floor)
    band(floor, sill, [door])
    band(sill, door_z, [bay, door])
    band(door_z, head, [bay])
    band(head, upper_sill, [])
    band(upper_sill, upper_head, uppers)
    band(upper_head, eaves, [])
    # side walls, back wall, the parapet and cornice, the roof
    for ya, yb in ((y0, y0 + 0.3), (y1 - 0.3, y1)):
        builder.prism([(back, 0.0), (wall_back, 0.0), (wall_back, eaves), ((front + back) / 2, eaves + 2.6), (back, eaves)], ya, yb, ashlar, axis='y')
    builder.box((back, y0, 0.0), (back + 0.3, y1, eaves), ashlar)
    builder.box((front - 0.05, y0 - 0.02, eaves), (front + 0.18, y1 + 0.02, eaves + 0.22), dark_stone)          # cornice
    builder.box((wall_back, y0, eaves + 0.22), (front, y1, parapet), ashlar)                                     # parapet
    builder.box((wall_back - 0.04, y0 - 0.02, parapet), (front + 0.06, y1 + 0.02, parapet + 0.12), dark_stone)   # its coping
    ridge_x, ridge_z = (front + back) / 2, eaves + 2.6
    builder.roof_slope((wall_back, y0, eaves + 0.15), (wall_back, y1, eaves + 0.15), (ridge_x, y1, ridge_z), (ridge_x, y0, ridge_z), slate)
    builder.roof_slope((back, y1, eaves), (back, y0, eaves), (ridge_x, y0, ridge_z), (ridge_x, y1, ridge_z), slate)
    # the plinth and the sill course under the upstairs windows
    builder.box((front - 0.02, y0, floor - 0.2), (front + 0.05, y1, floor + 0.45), dark_stone)
    builder.box((front - 0.02, y0, upper_sill - 0.12), (front + 0.08, y1, upper_sill), dark_stone)
    # the upstairs windows: recessed dark glass, glazing bars, stone heads
    for ya, yb in uppers:
        builder.box((wall_back + 0.1, ya, upper_sill), (wall_back + 0.12, yb, upper_head), upper_glass)
        builder.box((wall_back + 0.12, (ya + yb) / 2 - 0.025, upper_sill), (wall_back + 0.16, (ya + yb) / 2 + 0.025, upper_head), paint)
        for z in (upper_sill + 0.45, upper_sill + 0.9):
            builder.box((wall_back + 0.12, ya, z - 0.02), (wall_back + 0.16, yb, z + 0.02), paint)
        builder.box((front - 0.02, ya - 0.12, upper_head), (front + 0.06, yb + 0.12, upper_head + 0.22), dark_stone)
    # the door: recessed panelled door, a stone surround with a hood, two steps
    builder.box((wall_back + 0.12, door[0], floor), (wall_back + 0.17, door[1], door_z), door_paint)
    for k in range(2):
        za = floor + 0.25 + k * 1.0
        builder.box((wall_back + 0.17, door[0] + 0.1, za), (wall_back + 0.19, door[1] - 0.1, za + 0.75), door_paint)
    for ya, yb in ((door[0] - 0.18, door[0]), (door[1], door[1] + 0.18)):
        builder.box((front - 0.02, ya, floor), (front + 0.07, yb, door_z), dark_stone)
    builder.box((front - 0.02, door[0] - 0.25, door_z), (front + 0.2, door[1] + 0.25, door_z + 0.25), dark_stone)
    builder.box((front, door[0] - 0.1, floor - 0.12), (front + 0.45, door[1] + 0.1, floor + 0.02), dark_stone)
    # the canted bay window: a stone stall below, three panes of glass (own surface), iron bars, a lead-grey top
    out = 0.5
    corners = [Vector((front, bay[0])), Vector((front + out, bay[0] + out)), Vector((front + out, bay[1] - out)), Vector((front, bay[1]))]
    for a, b in zip(corners, corners[1:]):
        builder.quad([(a.x, a.y, floor), (b.x, b.y, floor), (b.x, b.y, sill), (a.x, a.y, sill)], dark_stone)
        builder.quad([(a.x, a.y, sill), (b.x, b.y, sill), (b.x, b.y, head), (a.x, a.y, head)], glass)
        builder.quad([(a.x, a.y, head), (b.x, b.y, head), (b.x, b.y, head + 0.28), (a.x, a.y, head + 0.28)], paint)
        across = (b - a)
        length = across.length
        for k in range(1, int(length / 0.13)):
            spot = a + across * (k / int(length / 0.13))
            normal = Vector((across.y, -across.x)).normalized()      # outward
            bar = spot + normal * 0.05
            builder.rod((bar.x, bar.y, sill + 0.02), (bar.x, bar.y, head - 0.02), 0.011, iron, sides=5)
        for z in (sill + 0.06, head - 0.06):
            n = Vector((across.y, -across.x)).normalized()
            builder.rod(((a + n * 0.05).x, (a + n * 0.05).y, z), ((b + n * 0.05).x, (b + n * 0.05).y, z), 0.014, iron, sides=5)
    for corner in corners:
        builder.box((corner.x - 0.04, corner.y - 0.04, sill), (corner.x + 0.04, corner.y + 0.04, head), paint)
    builder.prism([(corners[0].x, corners[0].y), (corners[1].x, corners[1].y), (corners[2].x, corners[2].y), (corners[3].x, corners[3].y)],
                  sill - 0.06, sill, dark_stone, axis='z')
    builder.prism([(corners[0].x, corners[0].y), (corners[1].x + 0.04, corners[1].y), (corners[2].x + 0.04, corners[2].y), (corners[3].x, corners[3].y)],
                  head + 0.28, head + 0.36, dark_stone, axis='z')
    # the shallow room behind the bay: a back wall, side walls, a ceiling and a counter (lit only on page 9)
    room_back = wall_back - 1.3
    builder.box((room_back - 0.05, bay[0], sill - 0.1), (room_back, bay[1], head + 0.2), room)
    for ya, yb in ((bay[0] - 0.05, bay[0]), (bay[1], bay[1] + 0.05)):
        builder.box((room_back, ya, sill - 0.1), (wall_back, yb, head + 0.2), room)
    builder.box((room_back, bay[0], head + 0.2), (wall_back, bay[1], head + 0.25), room)
    builder.box((room_back, bay[0], sill - 0.15), (front + out, bay[1], sill - 0.1), room_floor)
    builder.box((room_back + 0.1, bay[0] + 0.1, sill - 0.1), (room_back + 0.6, bay[1] - 0.1, sill + 0.3), room_floor)
    builder.finish('bank-building', collection_name='bank')
    light = point_light('bank_room_light', (wall_back - 0.6, (bay[0] + bay[1]) / 2, head - 0.3), 60.0 if BANK_LIT else 0.0, (1.0, 0.66, 0.36), soft=0.3)
    light.hide_render = not BANK_LIT
    # the signs: the brass plate beside the door and the hanging sign at first-floor height, square to the lane
    plate = import_glb(os.path.join(PROPS_2, 'bank-brass-plate.glb'), (front + 0.005, (bay[1] + door[0] - 0.18) / 2, floor + 1.35), 90, 'signs',
                       'bank-brass-plate')
    sign = import_glb(os.path.join(PROPS_2, 'bank-hanging-sign.glb'), (0, 0, 0), 0, 'signs', 'bank-hanging-sign')
    low, high = bounds_of(parts_of(sign))
    sign.location = (front - low.x + 0.0, BANK_SIGN_Y, BANK_SIGN_BOTTOM)
    bpy.context.view_layer.update()
    return {'front_x': front, 'y': [BANK_Y[0], BANK_Y[1]], 'window': {'centre': [round(front + out * 0.6, 3), round((bay[0] + bay[1]) / 2, 3), round((sill + head) / 2, 3)],
                                                                   'from': [front, bay[0], sill], 'to': [front + out, bay[1], head],
                                                                   'glass_material': 'bank-window-glass', 'room_light': 'bank_room_light'},
            'sign': [round(v, 3) for v in sign.location], 'sign_board_centre': [round(front + (high.x - low.x) / 2 + 0.2, 3), BANK_SIGN_Y, BANK_SIGN_BOTTOM + 0.375],
            'brass_plate': [round(v, 3) for v in plate.location], 'door': [front, (door[0] + door[1]) / 2, floor]}


def door_top(floor):
    return floor + 2.45


# ------------------------------------------------------------------------------------------ the factories and the town

def factories_and_town():
    holders = {}
    for file_name, collection_name in (('no-1-quiet-factory.glb', 'factories'), ('no-2-flat-out-factory.glb', 'factories'), ('far-town.glb', 'town')):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(WORKS_MODELS, file_name))
        imported = [o for o in bpy.data.objects if o not in before]
        roots = [o for o in imported if o.parent is None]
        assert len(roots) == 1, f'{file_name} has {len(roots)} roots'
        move_to_collection(imported, collection_name)
        roots[0].location = (0, WALL_Y, 0)
        holders[file_name[:-4]] = roots[0]
    bpy.context.view_layer.update()
    return holders


# ------------------------------------------------------------------------------------------ gates, gate furniture, people

GATE_LEAVES = {}     # prefix: [(leaf object, its rest matrix, hinge point, +1 turns left / -1 right)]
CHAIN_HEIGHT = 2.05


def gates():
    """The two pairs of iron gates (own surfaces, never in a plate), each under a holder no-1-gate / no-2-gate, and
    No. 1's chain and padlock (no-1-chain). The pair's fixed cross bar is left out: it would hang across an open
    gateway."""
    found = {}
    for prefix in ('no-1', 'no-2'):
        holder = import_glb(os.path.join(PIT_PROPS, 'iron-gates-pair.glb'), (gate_centre(prefix), GATE_PLANE_Y, 0.0), 0, 'gates', f'{prefix}-gate')
        for o in list(holder.children_recursive):
            if o.type == 'MESH' and re.sub(r'\.\d{3}$', '', o.name) == 'large_iron_gate':
                bpy.data.objects.remove(o, do_unlink=True)
        bpy.context.view_layer.update()
        leaves = []
        for o in holder.children_recursive:
            if o.type != 'MESH':
                continue
            for side, sign in (('left_door', 1), ('right_door', -1)):
                if side in o.name:
                    low, high = bounds_of([o])
                    hinge = Vector((low.x if sign > 0 else high.x, GATE_PLANE_Y, 0.0))
                    leaves.append((o, o.matrix_world.copy(), hinge, sign))
        bolt = [o for o in holder.children_recursive if 'bolt' in o.name]
        GATE_LEAVES[prefix] = {'leaves': leaves, 'bolt': [(o, o.matrix_world.copy()) for o in bolt]}
        found[prefix] = {'centre': [gate_centre(prefix), GATE_PLANE_Y, 0.0], 'width': 2.95,
                         'hinges': {('left' if sign > 0 else 'right'): [round(v, 3) for v in hinge] for _, _, hinge, sign in leaves},
                         'leaf_height': 2.929, 'opening': [gate_centre(prefix) - GATE_WIDTH / 2, gate_centre(prefix) + GATE_WIDTH / 2]}
    # the chain round the meeting stiles high up, above the waiting men's heads, where W1 sees it (round 3: at 1.3 m it
    # was hidden behind the front man)
    chain = import_glb(os.path.join(PROPS_2, 'chain-and-padlock.glb'), (gate_centre('no-1'), GATE_PLANE_Y, CHAIN_HEIGHT), 0, 'gates', 'no-1-chain')
    found['no-1']['chain'] = [round(v, 3) for v in chain.location]
    return found


def set_gate(prefix, angle):
    """Swing a gate's leaves into the yard by angle degrees (0 shut), about their hinges, as the film does."""
    entry = GATE_LEAVES[prefix]
    for leaf, rest, hinge, sign in entry['leaves']:
        turn = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(sign * angle), 4, 'Z') @ Matrix.Translation(-hinge)
        leaf.matrix_world = turn @ rest
    left = [item for item in entry['leaves'] if item[3] > 0]
    for bolt, rest in entry['bolt']:
        if left:
            _, left_rest, hinge, _ = left[0]
            turn = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(angle), 4, 'Z') @ Matrix.Translation(-hinge)
            bolt.matrix_world = turn @ rest
    bpy.context.view_layer.update()


def gate_furniture(pieces):
    """Boards, drums, gate lamps, the brazier, lantern and lunch tin; returns where they stand."""
    found = {}
    lamp_lights = {}
    for prefix, side in (('no-1', -1), ('no-2', 1)):
        centre = gate_centre(prefix)
        board = import_glb(os.path.join(PROPS_2, f'gate-board-{prefix}.glb'), (centre, GATE_PLANE_Y - 0.32, BOARD_BOTTOM), 0, 'signs', f'gate-board-{prefix}')
        found[f'{prefix}-board'] = [round(v, 3) for v in board.location]
        # the gate lamp (round 5): a gas lamp on a wall bracket on the outer pier's INNER face (toward the gateway), near
        # its front edge, hanging out over the gateway's outer corner. Its light is about half as strong as before and
        # reaches only the gate's leaves, the chain, the board, the waiting men and the yard (light linking), so it
        # falls on the bars, the chain and the board and edges the men's caps and shoulders, never on the brick facing
        # the camera (round 4's check: on the pier's lane face it lit the pier into a big bright orange slab on W1's
        # quiet side, brighter than the gate). The bracket's wall plate stands 0.39 m behind the lamp's own origin and
        # its lamp 0.22 m in front of it (the prop as built), so turned a quarter it hangs 0.6 m into the gateway.
        inner_face = outer_pier_inner_edge(prefix)
        lamp = import_glb(os.path.join(PIT_PROPS, 'gas-lamp-wall-bracket.glb'), (inner_face - side * 0.38, LAMP_Y, LAMP_FOOT), 90 if side < 0 else -90,
                          'props', f'{prefix}-gate-lamp')
        bulb_points = []
        for o in lamp.children_recursive:
            for m in (o.data.materials if o.type == 'MESH' else []):
                if m and m.name.startswith('street_lamp_02_bulb'):
                    dressing.make_glow(m, (1.0, 0.72, 0.4), 4.0)
                elif m and m.name.startswith('street_lamp_02_glass'):
                    dressing.make_glow(m, (1.0, 0.5, 0.18), 0.35)
            if o.type == 'MESH':
                for polygon in o.data.polygons:
                    material = o.data.materials[polygon.material_index] if polygon.material_index < len(o.data.materials) else None
                    if material and material.name.startswith('street_lamp_02_bulb'):
                        bulb_points.append(o.matrix_world @ polygon.center)
        bulb = sum(bulb_points, Vector()) / len(bulb_points) if bulb_points else Vector((inner_face - side * 0.6, LAMP_Y, LAMP_FOOT + 1.07))
        # the light a hand's breadth toward the lane from the glass, so the board (hanging a little in front of the
        # lamp's line) catches it on its face
        lamp_lights[prefix] = point_light(f'{prefix}-gate-lamp-light', (bulb.x, bulb.y - 0.2, bulb.z), GATE_LAMP_ENERGY, (1.0, 0.72, 0.45), soft=0.15)
        found[f'{prefix}-gate-lamp'] = [round(v, 3) for v in bulb]
        # the drums by the outer pier, along the low wall, their stencils turned to the lane
        spots = DRUM_SPOTS[prefix]
        for word, (x, y, turn) in spots.items():
            holder = prop(f'steel-drum-{word}.glb', x, y, turn, name=f'{prefix}-drum-{word}', collection_name='signs')
            found[f'{prefix}-drum-{word}'] = [round(v, 3) for v in holder.location]
    return found, lamp_lights


FIRE_ENERGY = 80.0                       # the brazier's light (round 4: 110 W, against the outer pier)
LAMP_Y = WALL_Y - PIER_PROUD + 0.1       # the gate lamp's bracket on the outer pier's inner face, 0.1 m in from its front edge
LAMP_FOOT = 2.2                          # the bracket's foot: the lamp's glass at about 3.3 m, its top under the board
GATE_LAMP_ENERGY = 7.0                   # half round 4's 14 W (which lit the pier's face); it reaches only the gate, its board, the men and the yard


def brazier_and_lantern(coping_top):
    """No. 1's brazier against its gate's right leaf, burning; a lit hurricane lantern on the DIESEL drum's lid and a
    lunch tin on the PETROL drum's."""
    x, y = BRAZIER
    drum = prop('brazier-drum.glb', x, y, 25, name='brazier-drum', folder=PIT_PROPS)
    fire = dressing.brazier_fire(x, y, light_above_coals=0.55, coal_top=0.84, dark_every=1.33, glow=3.5, energy=FIRE_ENERGY, shadow_soft=0.35)
    coals = [o for o in bpy.data.objects if o.name.startswith('brazier_coal_')]
    # brazier_fire finds the ground with a ray from high above, which can meet the gate arch or board over the brazier
    # (it now stands against the gate leaf): the coals and the fire's light go into the drum whatever the ray met
    drop = (fire.location.z - 0.55) - (drum.location.z + 0.84)
    for o in coals + [fire]:
        o.location.z -= drop
    move_to_collection(coals + [fire], 'props')
    move_to_collection([fire], 'works-lights')
    # the fire lights everything but its own drum and the works wall with its piers (round 5: standing against the gate
    # leaf beside No. 1's inner pier, it lit the pier's face into the brightest patch of W1; the gate's bars, the men,
    # the road and the drums keep its light)
    dressing.light_reaches(fire, list(drum.children_recursive) + [bpy.data.objects['works-wall']], only=False)
    lantern = prop('hurricane-lantern.glb', LANTERN[0], LANTERN[1], 20, name='hurricane-lantern', folder=PIT_PROPS, start=1.2)
    for material in bpy.data.materials:
        if material.name.startswith('Lantern_01_glass'):
            dressing.make_glow(material, (1.0, 0.62, 0.3), 6.0)
    lantern_light = point_light('lantern_light', (LANTERN[0], LANTERN[1], lantern.location.z + 0.16), 15.0, (1.0, 0.6, 0.3), soft=0.05)
    lunch_tin = prop('lunch-tin.glb', LUNCH_TIN[0], LUNCH_TIN[1], -15, name='lunch-tin', start=1.2)
    return {'brazier': [round(v, 3) for v in drum.location], 'coals_z': round(fire.location.z - 0.55, 3),
            'fire_light': [round(v, 3) for v in fire.location], 'lantern': [round(v, 3) for v in lantern.location],
            'lantern_light': [round(v, 3) for v in lantern_light.location], 'lunch_tin': [round(v, 3) for v in lunch_tin.location]}


with open(os.path.join(FIGURES, 'index.json')) as handle:
    FIGURE_FACTS = {entry['file'][:-4]: entry for entry in json.load(handle)}
GRIP = FIGURE_FACTS['worker-hand-on-bar']['grip_bar_at']
STOOP_AHEAD = FIGURE_FACTS['worker-stooped-to-brazier']['brazier_ahead']
LEAN_AT = FIGURE_FACTS['worker-leaning-on-wall']['wall_at_x']

# No. 1's gate furniture and its waiting men (x, y in metres; turn in degrees, 0 = back to a camera looking up the lane)
_N1 = -GATE_CENTRE_X                     # No. 1's gateway middle
_N1_OUTER = _N1 - GATE_WIDTH / 2         # its outer pier's inner face
# Round 5 (round 4's check: the men in single file down the kerb were seen end-on from W1 and W3 and read as one dark
# column; the drums stood among them). The waiting men now stand GATHERED IN FRONT OF THE SHUT GATE, a loose crowd two
# deep across the gateway, backs to the lane, 0.3 to 0.5 m between shoulders, heads at different heights. The brazier
# stands against the gate's right leaf with the stooped man warming his hands at it from its front-left, so its fire
# warms the gate's lower bars and edges the men's right sides. The PETROL and DIESEL drums stand IN FRONT of the crowd's
# left end, on the pavement, the lantern on DIESEL's lid and the lunch tin on PETROL's: nobody stands between them and
# W1 or W3, they are the nearest story things in W1 (the bottom of DIESEL about 0.71 down), and the men stand behind
# them. (Round 4's check asked for the drums against the dividing wall right of No. 1's right pier: from W1's new
# composed spot, 3 m nearer, everything right of the right pier lies past 0.93 across, out of the frame or past the
# phone buttons, so they stand here instead, where the same aim, no man in front of them from W1 or W3, holds.) No. 2's
# side is the mirror: its drums in front of the right end of its eight men (page 12), its crates in the yard moved left
# so the drums do not hide them from W2.
DRUM_SPOTS = {    # x, y, turn (degrees; the stencil faces -y at 0, + turns it toward +x): words turned to the gate view
    'no-1': {'petrol': (-5.3, 20.45, 12.0), 'diesel': (-4.3, 20.0, 8.0)},
    'no-2': {'petrol': (5.2, 20.45, -12.0), 'diesel': (4.3, 20.0, -8.0)},
}
BRAZIER = (-2.35, 21.82)                                            # against No. 1's right gate leaf, in the road
LANTERN = (DRUM_SPOTS['no-1']['diesel'][0] - 0.01, DRUM_SPOTS['no-1']['diesel'][1] - 0.2)   # on DIESEL's lid, at its front
LUNCH_TIN = (DRUM_SPOTS['no-1']['petrol'][0] - 0.01, DRUM_SPOTS['no-1']['petrol'][1] - 0.16)   # on PETROL's lid, at its front
STOOP_GAP = 0.1          # the stooped man stands this far further from the brazier than his pose's own reach (round 3's
                         # check: his coat met the drum)
STOOP_TURN = -40.0       # he faces the brazier from its front-left, turned up and to the right
# men: (figure, name, (x, y), turn, scale). Scale: a little taller or shorter than the figure as built (heads at
# different heights); the ground under each (pavement or road) changes it again
MEN_1 = [
    # the front man's right hand round a bar of the left leaf, so the chain where the leaves meet shows to his right
    ('worker-hand-on-bar', 'man-1', (-4.06 - GRIP[0], GATE_PLANE_Y - 0.03 - GRIP[1]), 0, 1.0),
    # stooped over the brazier from its front-left, turned toward it, his back to W1 and W3
    ('worker-stooped-to-brazier', 'man-2', (BRAZIER[0] + (STOOP_AHEAD + STOOP_GAP) * math.sin(math.radians(STOOP_TURN)),
                                            BRAZIER[1] - (STOOP_AHEAD + STOOP_GAP) * math.cos(math.radians(STOOP_TURN))), STOOP_TURN, 1.0),
    # the front row, at the gate (between man 1 and the stooped man, and by the outer pier)
    ('worker-arms-folded', 'man-3', (-3.49, 21.55), 6, 1.03),
    ('worker-hands-in-pockets', 'man-4', (-5.3, 21.45), -10, 0.97),
    # the back row, behind the drums, each between two of the front row
    ('worker-arms-folded', 'man-5', (-4.77, 20.72), 12, 0.98),
    ('worker-hands-in-pockets', 'man-6', (-3.93, 20.62), -4, 1.04),
    ('worker-hands-in-pockets', 'man-7', (-3.14, 20.82), -14, 0.96),
]
# No. 2's eight (its slowed state, page 12): the same arrangement, mirrored and without a fire: a loose crowd two deep
# across its gateway, backs to the lane, behind the drums at its right end; from W4, inside the yard, they stand
# outside the half-shut gate
_N2 = GATE_CENTRE_X
MEN_2 = [
    ('worker-hands-in-pockets', 'no-2-man-1', (2.35, 21.5), 6, 1.0),
    ('worker-arms-folded', 'no-2-man-2', (3.15, 21.62), -8, 1.03),
    ('worker-hands-in-pockets', 'no-2-man-3', (3.95, 21.48), 10, 0.97),
    ('worker-arms-folded', 'no-2-man-4', (4.75, 21.58), -4, 1.0),
    ('worker-hands-in-pockets', 'no-2-man-5', (2.15, 20.78), 12, 0.98),
    ('worker-arms-folded', 'no-2-man-6', (2.75, 20.68), -12, 1.04),
    ('worker-hands-in-pockets', 'no-2-man-7', (3.55, 20.8), 4, 0.96),
    ('worker-arms-folded', 'no-2-man-8', (5.05, 20.95), -16, 1.01),
]
# The people at work inside each lit doorway (round 5; round 4's check: both lit doorways showed an empty room, so
# "flat out" and "the workers go in" had no picture): existing figure shapes in dark work clothes, from behind or
# side-on, so they show as dark shapes against the lit far wall. (figure, name, (x, y), turn). No. 2's are in every
# No. 2 plate (in the slowed state only the first); No. 1's only in the working and "men gone" helper plates, so on
# "go" the men leave the gate and appear inside. They are painted into the plates and are not in the film's set: they
# stand 17 m and more from every camera, in front of the far wall.
_ROOM_1, _ROOM_2 = WALL_Y + 8.0, WALL_Y + 8.0                       # each mill front's face (the doorway rooms start here)
WORKERS = {
    'no-1': [
        # bent over the front of the nearer loom, from behind, his hands over its cloth
        ('worker-stooped-to-brazier', 'no-1-worker-1', (-3.0, _ROOM_1 + 1.9 - STOOP_AHEAD - 0.12), 10),
        # side-on, facing the second loom's way, his raised hand on the nearer loom's back post
        ('worker-hand-on-bar', 'no-1-worker-2', (-4.05 - GRIP[1], _ROOM_1 + 3.05 + GRIP[0]), -90),
    ],
    'no-2': [
        # at the lathe's headstock, from behind, bent over its bed
        ('worker-stooped-to-brazier', 'no-2-worker-1', (1.9, _ROOM_2 + 2.2 - STOOP_AHEAD - 0.12), 18),
        # side-on at the press, his raised hand on its column, the flywheel to his right
        ('worker-hand-on-bar', 'no-2-worker-2', (2.77 - GRIP[1], _ROOM_2 + 4.9 + GRIP[0]), -90),
    ],
}
WORKER_CLOTH = (0.025, 0.024, 0.026)     # their dark work clothes (every surface of the figure)


def place_figure(file_name, name, x, y, turn, collection_name, scale=1.0):
    ground = dressing.ground_height(x, y, 1.0)     # found before the figure stands there (its coat would stop the ray)
    holder = import_glb(os.path.join(FIGURES, f'{file_name}.glb'), (x, y, ground), turn, collection_name, name)
    holder.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    return holder


def foot_shadow(holder, collection_name):
    """A small soft dark patch on the ground under a man (two see-through ovals), part of him: the men cast no long
    shadows from the fire and the lamps (round 2: those shadows made the state picture's swap area cover 42% of the
    frame), so this keeps them standing on the ground."""
    material = bpy.data.materials.get('foot-shadow')
    if material is None:
        material = bpy.data.materials.new('foot-shadow')
        material.use_nodes = True
        shader = material.node_tree.nodes['Principled BSDF']
        shader.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1)
        shader.inputs['Roughness'].default_value = 1.0
        shader.inputs['Alpha'].default_value = 0.4
        if hasattr(material, 'surface_render_method'):
            material.surface_render_method = 'BLENDED'
        material['tile_metres'] = 1.0
    builder = kit.MeshBuilder()
    ground = holder.location.z
    for half_x, half_y, lift in ((0.36, 0.3, 0.006), (0.24, 0.2, 0.009)):
        outline = [(holder.location.x + half_x * math.cos(2 * math.pi * k / 20), holder.location.y + half_y * math.sin(2 * math.pi * k / 20)) for k in range(20)]
        face = builder.bm.faces.new([builder.bm.verts.new((x, y, ground + lift)) for x, y in outline])
        builder._tag([face], material)
    patch = builder.finish(f'{holder.name}-foot-shadow', collection_name=collection_name)
    patch.visible_shadow = False
    patch.parent = holder
    patch.matrix_parent_inverse = holder.matrix_world.inverted()
    return patch


def people():
    placed = {'men-no-1': [], 'men-no-2': []}
    for collection_name, men in (('men-no-1', MEN_1), ('men-no-2', MEN_2)):
        for file_name, name, (x, y), turn, scale in men:
            holder = place_figure(file_name, name, x, y, turn, collection_name, scale)
            for part in holder.children_recursive:
                if part.type == 'MESH':
                    part.visible_shadow = False        # no long shadows from the fire and the lamps
            foot_shadow(holder, collection_name)
            placed[collection_name].append({'name': name, 'figure': file_name, 'feet': [round(v, 3) for v in holder.location], 'turn_degrees': turn,
                                            'height_metres': round(FIGURE_FACTS[file_name]['height_metres'] * scale, 3)})
    bpy.context.view_layer.update()
    return placed


def workers():
    """The people at work inside each lit doorway (WORKERS), in dark work clothes, each in its own collection
    (workers-no-1, workers-no-2) so a state can show them."""
    cloth = bpy.data.materials.new('worker-dark-cloth')
    cloth.use_nodes = True
    shader = cloth.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*WORKER_CLOTH, 1)
    shader.inputs['Roughness'].default_value = 0.9
    cloth['tile_metres'] = 1.0
    placed = {}
    for prefix, people_inside in WORKERS.items():
        collection_name = f'workers-{prefix}'
        placed[prefix] = []
        for file_name, name, (x, y), turn in people_inside:
            holder = place_figure(file_name, name, x, y, turn, collection_name)
            for part in holder.children_recursive:
                if part.type == 'MESH':
                    part.visible_shadow = False
                    for slot in part.material_slots:
                        slot.material = cloth
            foot_shadow(holder, collection_name)
            placed[prefix].append({'name': name, 'figure': file_name, 'feet': [round(v, 3) for v in holder.location], 'turn_degrees': turn})
    bpy.context.view_layer.update()
    return placed


def yard_things(pieces):
    """Crates in No. 2's gateway with the hand truck, the handcart of crates coming up the lane, No. 1's pop-up crates
    (own surfaces), and W4's things on No. 2's gate's inside post."""
    found = {}
    n2 = gate_centre('no-2')
    # beyond the reach of the gate's leaves (1.48 m from the gate's line), in the gateway's middle: in W2 they stand at
    # the meeting point, left of the DIESEL drum's line (round 5: the drums now stand in front of the gateway's right
    # end, and in round 4's place the drum hid the lower right crate's words from W2)
    crate_y = GATE_PLANE_Y + 1.95
    # three crates, two side by side and one on top (round 5: a fourth on top hid the man at the press from W2)
    for k, (x, y, lift, turn) in enumerate(((n2 - 0.55, crate_y, 0.0, 4), (n2 + 0.35, crate_y + 0.15, 0.0, -6), (n2 - 0.1, crate_y + 0.07, 0.51, 2))):
        prop('crate-this-way-up.glb', x, y, turn, name=f'no-2-crate-{k + 1}', lift=lift, start=0.3)
    truck = prop('hand-truck.glb', n2 + 0.95, crate_y + 1.05, 200, name='hand-truck', start=0.5)
    dressing.tint([o for o in truck.children_recursive], (0.45, 0.4, 0.38))
    found['no-2-crates'] = [round(n2 - 0.1, 3), crate_y, 0.55]
    # the handcart on the right pavement, its shafts toward the works, loaded with three THIS WAY UP crates, their words
    # toward the lane's mouth (W3): two on its bed, one on top (round 5; round 4's check: a small empty cart at W3's
    # right edge; now its middle is at about 0.85 across and its wheels about 0.8 down in W3)
    cart = prop('handcart.glb', HANDCART[0], HANDCART[1], 90, name='handcart', folder=PIT_PROPS)
    bpy.context.view_layer.update()
    bed_top = None
    for k, (dy, turn) in enumerate(((-0.33, 3), (0.3, -4))):
        crate = prop('crate-this-way-up.glb', HANDCART[0], HANDCART[1] + dy, turn, name=f'handcart-crate-{k + 1}', start=1.5)
        bed_top = crate.location.z
    bpy.context.view_layer.update()
    prop('crate-this-way-up.glb', HANDCART[0] + 0.03, HANDCART[1] - 0.05, -2, name='handcart-crate-3', start=2.5)
    found['handcart'] = [round(v, 3) for v in cart.location]
    found['handcart_bed_top'] = round(bed_top, 3) if bed_top is not None else None
    # No. 1's pop-up crates (own surfaces: they pop up in its open gateway on "things"): two side by side and one on top,
    # in the gateway's middle, clear of the open right leaf (x -2.07), of the brazier's line from W1 and of the DIESEL
    # drum's, so from W1's composed spot every crate's THIS WAY UP shows whole (round 4's check: behind the DIESEL drum
    # and its lantern only "THI" and "UP" showed)
    n1 = gate_centre('no-1')
    popups = []
    for k, (x, y, lift, turn) in enumerate(POP_UP_CRATES):
        holder = import_glb(os.path.join(PROPS_2, 'crate-this-way-up.glb'), (n1 + x, WALL_Y + y, 0.02 + lift), turn, 'pop-up', f'no-1-crate-{k + 1}')
        popups.append([round(v, 3) for v in holder.location])
    found['no-1-pop-up-crates'] = popups
    found['no-1-gateway'] = [n1, WALL_Y + 1.4, 0.0]
    # W4: the upturned crate at the inner pier's foot, its end in front of the hinge, so from W4 it overlaps the gate's
    # leaf. It shows from the lane too (W2 and W3 see it through the gateway), so it stays exactly where it was; the
    # rest of W4's corner (w4_corner) stands where only W4 sees it
    post = pieces['no-2']['inner_pier']
    post_face = WALL_Y + WALL_THICKNESS + PIER_PROUD
    crate = prop('crate-this-way-up.glb', post[1] + 0.05, post_face + 0.5, 90, name='w4-upturned-crate', start=0.5)
    crate.rotation_euler = (math.pi, 0, math.radians(90))
    crate.location.z += 0.5
    bpy.context.view_layer.update()
    found['w4'] = {'upturned_crate': [round(v, 3) for v in crate.location], **w4_corner(pieces)}
    return found


HANDCART = (3.85, 8.6)      # on the right pavement, coming up it toward the works, at its kerb: behind W2's camera, in W3's bottom third
# No. 1's pop-up crates: (x from the gateway's middle, y from the works wall's face, lift, turn); the third on the first two
POP_UP_CRATES = ((-0.35, 1.45, 0.0, -4), (0.5, 1.5, 0.0, 5), (0.08, 1.47, 0.5, 2))


# ------------------------------------------------------------------------------------------ W4's corner (round 5)

# Someone with a job, in one touching group on No. 2's inner pier's yard face (plan 34, W4; round 4's check, finding
# 10). A crate stood on end against the pier is his table; his jacket hangs from a wooden peg above it, its hem just
# behind the table's top; on the table his flat cap, his tin mug and his pay envelope, propped against the jacket's
# hem with "WAGES" toward W4. Everything stands left of x 1.70 (Blender), where No. 2's inner pier hides it from W1, W2
# and W3 (from W2 the pier's corner hides everything left of about x 1.84 there), so their plates do not change.
W4_PEG_Z = 1.61              # the peg's height: the jacket's hem then hangs 5 cm below the table's top, just behind it, so
                             # the table clearly overlaps it (level with the top, their edges only just met)
W4_TABLE_GAP = 0.16          # the table's back from the pier's face (the jacket hangs between)
W4_ENVELOPE_TOP_OUT = 0.195  # the envelope's top edge from the pier's face: against the jacket's front (its folds reach 0.19)
W4_ENVELOPE_SCALE = 2.6      # the pay envelope drawn bigger than life (rule 8), so "WAGES" comes out about 20 pixels tall
W4_ENVELOPE_LEAN = 16.0      # degrees the envelope leans back from upright, its top against the jacket
W4_CAP_TURN = 8.0            # degrees the cap's peak is turned from +x (toward the gate) toward +y (toward W4): W4 sees the
                             # cap nearly side on, the peak standing out of its outline (turned 32 degrees it read as a beret)
# W4's one pool of light: a lamp out of the frame to the right, on the dividing wall's side a little above the table,
# its warm light raking across the corner from the right (so the jacket's folds, sleeves and the cap's peak have light
# and shadow, and the jacket throws its shadow on the pier toward the gate), fading softly round the group (a spot with
# a wide soft edge); none of the yard's spill lights. (Linked away from the dividing wall, it left a hard lit edge down
# the pier's side.)
W4_LAMP = {'at': (0.55, 24.55, 2.05), 'aim': (1.65, 23.1, 0.55), 'energy': 340.0, 'cone_degrees': 58.0, 'blend': 0.85,
           'colour': (1.0, 0.56, 0.27)}
W4_LAMP_NAME = 'w4-corner-lamp'


def _ring_frame(tangent):
    """Two directions square to a tube's path (for its rings), the first kept as near +x as it can be."""
    tangent = tangent.normalized()
    across = Vector((1, 0, 0)) - tangent * tangent.x
    if across.length < 1e-4:
        across = Vector((0, 1, 0)) - tangent * tangent.y
    across.normalize()
    return across, tangent.cross(across).normalized()


def _tube(builder, points, radii, material, sides=18, squash=1.0, close_start=True, close_end=True, end_material=None):
    """A smooth tube through points (a sleeve), radius radii[k] at points[k]; squash < 1 flattens it front to back."""
    rings = []
    for k, point in enumerate(points):
        tangent = (points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)])
        across, other = _ring_frame(tangent)
        rings.append([builder.bm.verts.new(point + (across * math.cos(2 * math.pi * i / sides) + other * math.sin(2 * math.pi * i / sides) * squash) * radii[k])
                      for i in range(sides)])
    faces = []
    for a, b in zip(rings, rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append(builder.bm.faces.new([a[i], a[j], b[j], b[i]]))
    builder._tag(faces, material, smooth=True)
    if close_start:
        builder._tag([builder.bm.faces.new(list(reversed(rings[0])))], material)
    if close_end:
        builder._tag([builder.bm.faces.new(rings[-1])], end_material or material)
    return faces


def hanging_jacket(centre_x, wall_y, peg_z, wool, lining, horn, wood):
    """A wool work jacket hung by its collar on a wooden peg, its back toward the wall at wall_y (the jacket hangs on
    the +y side): empty shoulders slumped from the collar, drape folds fanning down the front from the peg, the sleeves
    hanging at the sides, standing a little clear of the body so they read as sleeves, the dark cuff openings, a rolled
    collar running into the lapels with the dark lining in the V, the buttoned front edge, three horn buttons, two
    pocket flaps, a hem hanging a little unevenly. Returns the jacket and the peg (two objects).
    (Round 4's check: the jacket from the props library read as a flat brown cut-out with buttons: its sleeves lay
    inside its outline and the yard's flat light showed no folds.)"""
    def table(rows, drop):
        for (d0, v0), (d1, v1) in zip(rows, rows[1:]):
            if drop <= d1:
                return v0 + (v1 - v0) * (drop - d0) / (d1 - d0)
        return rows[-1][1]
    widths = [(0.0, 0.07), (0.05, 0.1), (0.1, 0.15), (0.15, 0.19), (0.2, 0.205), (0.3, 0.212), (0.5, 0.222), (0.8, 0.238)]
    thicknesses = [(0.0, 0.05), (0.1, 0.075), (0.22, 0.1), (0.5, 0.095), (0.8, 0.085)]
    # how far the jacket's back stands out from the wall: off the peg at the top, settling toward the wall lower down
    backs = [(0.0, 0.085), (0.25, 0.06), (0.8, 0.028)]
    length = 0.8

    def surface(x, sine, drop):
        """(y out from the wall) of the body's surface at x across its middle, sine being the ring angle's sine (1: the
        front, -1: the back): a flattened tube, with the drape folds on its front fanning out from the peg."""
        half, thick, back = table(widths, drop), table(thicknesses, drop), table(backs, drop)
        shape = 0.5 + 0.5 * math.copysign(abs(sine) ** 0.65, sine)
        y = back + thick * shape
        if sine > 0:
            depth = 0.005 + 0.026 * min(1.0, max(0.0, (drop - 0.1) / 0.55))
            fan = math.atan2(x, drop + 0.12)
            y += sine * depth * math.sin(fan * 8.5 + 0.9)
            if abs(x) < 0.014 and drop > 0.27:
                y += 0.006 * sine          # the buttoned front edge stands proud
        return y

    def hem_drop(x):
        return length + 0.012 * math.sin(x * 21.0 + 0.7) + 0.008 * math.sin(x * 47.0) - 0.012 * x / 0.24

    builder = kit.MeshBuilder()
    around = 56
    drops = [0.03, 0.06, 0.1, 0.14, 0.18, 0.23, 0.29, 0.36, 0.44, 0.52, 0.6, 0.67, 0.73, 0.78, None]
    rings = []
    for drop in drops:
        ring = []
        for k in range(around):
            angle = 2 * math.pi * k / around
            x = table(widths, drop if drop is not None else length) * math.cos(angle)
            d = drop if drop is not None else hem_drop(x)
            ring.append(builder.bm.verts.new((centre_x + x, wall_y + surface(x, math.sin(angle), d), peg_z - d)))
        rings.append(ring)
    faces = []
    for upper, lower in zip(rings, rings[1:]):
        for k in range(around):
            j = (k + 1) % around
            faces.append(builder.bm.faces.new([upper[k], upper[j], lower[j], lower[k]]))
    builder._tag(faces, wool, smooth=True)
    builder._tag([builder.bm.faces.new(list(reversed(rings[0])))], wool)
    builder._tag([builder.bm.faces.new(rings[-1])], lining)          # the hem's opening, dark inside

    def front_point(x, drop, out=0.0):
        return Vector((centre_x + x, wall_y + surface(x, 1.0, drop) + out, peg_z - drop))

    # the collar: a soft roll round the back of the neck over the peg, running on down the front as the two lapels to the
    # top button (a V), the dark lining showing in the V
    path = []
    for k in range(29):
        share = k / 28
        side = -1 if share < 0.5 else 1
        reach = abs(share - 0.5) * 2
        if reach < 0.35:
            around_neck = reach / 0.35
            x = side * 0.075 * math.sin(around_neck * math.pi / 2)
            drop = 0.012 + 0.022 * (1 - math.cos(around_neck * math.pi / 2))
            path.append(Vector((centre_x + x, wall_y + table(backs, 0.0) + 0.035 + 0.02 * around_neck, peg_z - drop)))
        else:
            down = (reach - 0.35) / 0.65
            x = side * (0.07 - 0.058 * down)
            drop = 0.02 + 0.25 * down
            path.append(front_point(x, max(drop, 0.03), 0.008))
    _tube(builder, path, [0.032 if abs(k / 28 - 0.5) < 0.18 else 0.012 for k in range(29)], wool, sides=12, squash=0.6)
    v_top, v_bottom = 0.05, 0.25
    corners = [front_point(-0.05, v_top, -0.004), front_point(0.05, v_top, -0.004), front_point(0.0, v_bottom, -0.002)]
    v_face = builder.bm.faces.new([builder.bm.verts.new(point) for point in corners])
    builder._tag([v_face], lining)
    # the sleeves: from the slumped shoulders down the body's sides, a little in front of it and standing out past its
    # edge, bent forward at the elbow, the cuff openings dark
    for side in (-1, 1):
        points, radii = [], []
        for k in range(14):
            share = k / 13
            drop = 0.13 + 0.58 * share
            # from inside the slumped shoulder (its top end hidden in the body, so the shoulder's line runs on into the
            # sleeve: round 5's first try started at the shoulder's edge and stood up like a box's corner) out past the
            # body's edge, then hanging, bent a little forward at the elbow
            x = side * (0.12 + 0.11 * math.sin(math.pi / 2 * min(1.0, share * 2.2)) - 0.012 * share)
            out = table(backs, drop) + 0.045 + 0.035 * math.sin(math.pi * share) + 0.015 * share
            points.append(Vector((centre_x + x, wall_y + out, peg_z - drop)))
            radii.append(0.03 + 0.032 * math.sin(math.pi / 2 * min(1.0, share * 4.0)) - 0.012 * share)
        _tube(builder, points, radii, wool, sides=18, squash=0.9, close_start=True, close_end=True, end_material=lining)
    # three horn buttons on the front edge and two pocket flaps
    for drop in (0.3, 0.42, 0.54):
        centre = front_point(0.012, drop, 0.003)
        builder.rod(centre - Vector((0, 0.004, 0)), centre + Vector((0, 0.006, 0)), 0.012, horn, sides=12)
    for side in (-1, 1):
        x = side * 0.11
        top = front_point(x, 0.585, 0.002)
        builder.box((top.x - 0.075, top.y - 0.012, top.z - 0.05), (top.x + 0.075, top.y + 0.012, top.z), wool)
    # every face out (the rings and tubes are drawn by hand), the lining's V toward the yard
    import bmesh
    bmesh.ops.recalc_face_normals(builder.bm, faces=list(builder.bm.faces))
    v_face.normal_update()
    if v_face.normal.y < 0:
        v_face.normal_flip()
    jacket = builder.finish('w4-jacket', collection_name='props')
    # the peg: a turned wooden peg in a small block screwed to the pier, tipped up a little so the collar stays on it
    peg = kit.MeshBuilder()
    peg.box((centre_x - 0.05, wall_y - 0.01, peg_z - 0.05), (centre_x + 0.05, wall_y + 0.025, peg_z + 0.06), wood)
    peg.rod((centre_x, wall_y + 0.02, peg_z), (centre_x, wall_y + 0.13, peg_z + 0.02), 0.016, wood, sides=12, end_radius=0.013)
    peg.rod((centre_x, wall_y + 0.12, peg_z + 0.018), (centre_x, wall_y + 0.15, peg_z + 0.024), 0.022, wood, sides=12, end_radius=0.02)
    peg_object = peg.finish('w4-peg', collection_name='props')
    return jacket, peg_object


def flat_cap(tweed, lining):
    """A tweed flat cap as it lies on a table, crown up, its peak toward +x (one object at the origin, the band's middle
    on the table): a band, a crown pulled forward over the peak and fuller at the back, and a stiff curved peak standing
    clear in front of the band. (Round 4's check: the cap on its nail read as a flat disc.)"""
    builder = kit.MeshBuilder()
    side_half, length_half, band = 0.092, 0.108, 0.028    # the band's half widths (across, front to back) and height
    sides = 40

    def band_point(angle, z):
        return Vector((length_half * math.cos(angle), side_half * math.sin(angle), z))
    # the band (open at the bottom: the dark lining shows only from below)
    low = [builder.bm.verts.new(band_point(2 * math.pi * k / sides, 0.0)) for k in range(sides)]
    high = [builder.bm.verts.new(band_point(2 * math.pi * k / sides, band)) for k in range(sides)]
    builder._tag([builder.bm.faces.new([low[k], low[(k + 1) % sides], high[(k + 1) % sides], high[k]]) for k in range(sides)], tweed, smooth=True)
    builder._tag([builder.bm.faces.new(list(reversed(low)))], lining)
    # the crown: rings drawn in from a rim a little outside the band (over it at the back and sides, pulled forward over
    # the peak at the front) up to the top; fuller and higher at the back, low at the front where it is snapped to the peak
    rows = 9
    crown = []
    for r in range(rows + 1):
        share = r / rows                       # 0: the rim, 1: the middle of the top
        ring = []
        for k in range(sides):
            angle = 2 * math.pi * k / sides
            front = max(0.0, math.cos(angle))   # 1 at the front (+x), toward the peak
            reach = 1.0 - share ** 1.4
            x = (length_half + 0.012 + 0.03 * front) * math.cos(angle) * reach + 0.012 * (1 - reach)
            y = (side_half + 0.01) * math.sin(angle) * reach
            rise = 0.052 - 0.026 * front * (1 - share) + 0.008 * (1 - front)
            z = band + rise * math.sin(math.pi / 2 * min(1.0, share * 1.5)) - 0.012 * front * (1 - share)
            ring.append(builder.bm.verts.new((x, y, z)))
        crown.append(ring)
    faces = []
    for a, b in zip(crown, crown[1:]):
        for k in range(sides):
            faces.append(builder.bm.faces.new([a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]]))
    builder._tag(faces, tweed, smooth=True)
    builder._tag([builder.bm.faces.new(crown[-1])], tweed)
    # the rim of the crown down onto the band (a short skirt, so no gap shows under the overhang)
    skirt = []
    for k in range(sides):
        angle = 2 * math.pi * k / sides
        skirt.append(builder.bm.faces.new([high[k], crown[0][k], crown[0][(k + 1) % sides], high[(k + 1) % sides]]))
    builder._tag(skirt, tweed, smooth=True)
    # the peak: a stiff, curved half-oval of cloth over board, standing out 7 cm in front of the band, its tip a little down
    steps, depth, half_width, thick = 12, 0.085, 0.088, 0.006
    top_rows, bottom_rows = [], []
    for i in range(steps + 1):
        across = -1 + 2 * i / steps
        reach = depth * math.sqrt(max(0.0, 1 - across ** 2)) + 0.004
        top_row, bottom_row = [], []
        for j in range(5):
            out = j / 4
            x = length_half * math.sqrt(max(0.0, 1 - across ** 2)) * 0.96 + reach * out
            y = half_width * across
            z = 0.006 - 0.007 * out ** 1.5 - 0.006 * across ** 2
            top_row.append(builder.bm.verts.new((x, y, z + thick)))
            bottom_row.append(builder.bm.verts.new((x, y, z)))
        top_rows.append(top_row)
        bottom_rows.append(bottom_row)
    faces = []
    for i in range(steps):
        for j in range(4):
            faces.append(builder.bm.faces.new([top_rows[i][j], top_rows[i][j + 1], top_rows[i + 1][j + 1], top_rows[i + 1][j]]))
            faces.append(builder.bm.faces.new([bottom_rows[i][j], bottom_rows[i + 1][j], bottom_rows[i + 1][j + 1], bottom_rows[i][j + 1]]))
        faces.append(builder.bm.faces.new([top_rows[i][4], bottom_rows[i][4], bottom_rows[i + 1][4], top_rows[i + 1][4]]))
    for rows_ in (0, steps):
        for j in range(4):
            faces.append(builder.bm.faces.new([top_rows[rows_][j], bottom_rows[rows_][j], bottom_rows[rows_][j + 1], top_rows[rows_][j + 1]]))
    builder._tag(faces, tweed, smooth=True)
    import bmesh
    bmesh.ops.recalc_face_normals(builder.bm, faces=list(builder.bm.faces))     # every face out (drawn by hand)
    return builder.finish('w4-cap-cloth', collection_name='props')


def lightened(material, name, share):
    """A copy of an imported glTF material with its colour factor (the multiply over its picture) raised by share: the
    library jacket's near-black wool showed no folds in the lamplight; a little lighter, its folds and sleeves show."""
    copy = material.copy()
    copy.name = name
    for node in copy.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeMix' and node.data_type == 'RGBA' and node.blend_type == 'MULTIPLY':
            for socket in (node.inputs[6], node.inputs[7]):
                if not socket.is_linked:
                    socket.default_value = (*(min(1.0, v * share) for v in socket.default_value[:3]), 1.0)
        elif node.bl_idname == 'ShaderNodeBsdfPrincipled' and not node.inputs['Base Color'].is_linked:
            node.inputs['Base Color'].default_value = (*(min(1.0, v * share) for v in node.inputs['Base Color'].default_value[:3]), 1.0)
    return copy


def w4_corner(pieces):
    """W4's corner on No. 2's inner pier's yard face (see W4_PEG_Z above): returns where its things are."""
    post = pieces['no-2']['inner_pier']
    wall_y = WALL_Y + WALL_THICKNESS + PIER_PROUD                # the pier's yard face
    x = W4_GROUP_X
    # the cloth: the props library's jacket and cap bring the wool and the tweed (their own models are not used)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PROPS_2, 'jacket-and-cap-on-nail.glb'))
    old = [o for o in bpy.data.objects if o not in before]
    cloth = {}
    for o in old:
        for slot in (o.material_slots if o.type == 'MESH' else []):
            if slot.material:
                cloth[re.sub(r'\.\d{3}$', '', slot.material.name)] = slot.material
    delete_objects(old)
    wool, tweed = lightened(cloth['jacket-wool'], 'w4-jacket-wool', 1.7), lightened(cloth['cap-tweed'], 'w4-cap-tweed', 1.8)
    wool['tile_metres'], tweed['tile_metres'] = 0.27, 0.27
    lining = kit.plain_material('w4-jacket-lining', (0.025, 0.022, 0.02), roughness=0.9)
    horn = kit.plain_material('w4-button-horn', (0.04, 0.032, 0.026), roughness=0.4)
    wood = kit.surface_material('w4-peg-wood', 'distressed_painted_planks', tint=(0.34, 0.25, 0.17), roughness=0.7)
    jacket, peg = hanging_jacket(x, wall_y, W4_PEG_Z, wool, lining, horn, wood)
    holder = bpy.data.objects.new('w4-jacket-on-peg', None)
    kit.collection('props').objects.link(holder)
    for part in (jacket, peg):
        part.parent = holder
    # the table: a packing crate stood on its end against the pier, its stencilled sides turned to face across the yard
    # (seen edge on from W4 they would show a sliver of words), and their stencils taken off: a plain box
    table = import_glb(os.path.join(PROPS_2, 'crate-this-way-up.glb'), (0, 0, 0), 0, 'props', 'w4-crate-table')
    table.rotation_mode = 'ZYX'          # a quarter turn about z (the stencilled sides to face across), then up onto its end
    table.rotation_euler = (math.radians(90), 0, math.radians(90))
    bpy.context.view_layer.update()
    delete_objects([o for o in table.children_recursive if 'stencil' in o.name])
    low, high = bounds_of(parts_of(table))
    ground = dressing.ground_height(x, wall_y + 0.5, 1.0)
    table.location += Vector((x - (low.x + high.x) / 2, wall_y + W4_TABLE_GAP - low.y, ground - low.z))
    bpy.context.view_layer.update()
    low, high = bounds_of(parts_of(table))
    top = high.z
    # the cap on the table's front left, its peak toward the gate and turned a little toward W4
    cap = flat_cap(tweed, lining)
    cap_holder = bpy.data.objects.new('w4-cap', None)
    kit.collection('props').objects.link(cap_holder)
    cap.parent = cap_holder
    cap_holder.location = (high.x - 0.15, low.y + 0.36, top)
    cap_holder.rotation_euler = (0, 0, math.radians(W4_CAP_TURN))
    # the mug on the table's front right, its handle turned away from W4
    mug = import_glb(os.path.join(PROPS_2, 'tin-mug.glb'), (low.x + 0.07, low.y + 0.15, top), 200, 'props', 'w4-mug')
    # the pay envelope, stood up on its long edge at the table's back, "WAGES" toward W4, leaning back against the jacket
    envelope = import_glb(os.path.join(PROPS_2, 'wages-envelope.glb'), (0, 0, 0), 0, 'props', 'w4-wages')
    envelope.scale = (W4_ENVELOPE_SCALE,) * 3
    envelope.rotation_mode = 'ZXY'       # a half turn about z (the word's foot toward W4), then stood up and leaned back
    envelope.rotation_euler = (math.radians(W4_ENVELOPE_LEAN - 90.0), 0, math.radians(180))
    bpy.context.view_layer.update()
    e_low, e_high = bounds_of(parts_of(envelope))
    # its top edge against the jacket's front (about 0.135 m out from the pier there), its foot on the table's top
    envelope.location += Vector((x + 0.03 - (e_low.x + e_high.x) / 2, wall_y + W4_ENVELOPE_TOP_OUT - e_low.y, top - e_low.z))
    bpy.context.view_layer.update()
    e_low, e_high = bounds_of(parts_of(envelope))
    j_low, j_high = bounds_of([jacket])
    return {'jacket_on_peg': [round(x, 3), round(wall_y, 3), W4_PEG_Z], 'jacket_box': [[round(v, 3) for v in j_low], [round(v, 3) for v in j_high]],
            'crate_table': [round(v, 3) for v in table.location], 'table_top': round(top, 3), 'cap': [round(v, 3) for v in cap_holder.location],
            'mug': [round(v, 3) for v in mug.location], 'wages': [round(v, 3) for v in envelope.location],
            'wages_box': [[round(v, 3) for v in e_low], [round(v, 3) for v in e_high]], 'lamp': {k: v for k, v in W4_LAMP.items()},
            'board_back': gate_board_back(),
            'left_out': list(STATES['w4']['left_out']),
            'about': 'W4\'s corner on No. 2\'s inner pier (round 5): the jacket on its peg, the crate table under it with the cap, the mug and the '
                     'WAGES envelope (2.6 times life size), the upturned crate by the hinge; one warm pool from a lamp out of the frame '
                     '(light only); left_out: No. 2\'s gateway crates, not in the W4 plate, so the film hides them on page 14 '
                     '(then projection.refresh())'}


def gate_board_back():
    """The back of No. 2's gate board, lettered "No. 2" as well: a second board back to back with the first (its battens
    inside the first's, 1 mm apart, so no two faces lie in one plane), so from inside the yard (W4) the board reads
    "No. 2" rather than as a big blank plank sign (round 4's check). From the lane it is hidden behind the first board."""
    front = bpy.data.objects['gate-board-no-2']           # the first board (its holder is gate-board-no-2.001)
    back = import_glb(os.path.join(PROPS_2, 'gate-board-no-2.glb'), tuple(front.matrix_world.translation), 180, 'signs', 'gate-board-no-2-back')
    front_low, front_high = bounds_of(parts_of(front))
    back_low, _ = bounds_of(parts_of(back))
    back.location.y += (front_high.y - 0.029) - back_low.y      # the battens (3 cm deep) one inside the other
    bpy.context.view_layer.update()
    return [round(v, 3) for v in back.location]


# ------------------------------------------------------------------------------------------ light, state, cameras

def lights():
    world = bpy.context.scene.world
    background = world.node_tree.nodes.get('Background') if world and world.node_tree else None
    if background:
        background.inputs['Strength'].default_value = SKY_STRENGTH
    found = {}
    # No. 2's lit doorway and its gateway: warm light on the yard, the open gateway and the empty pavement
    n2 = gate_centre('no-2')
    found['no-2-doorway-spill'] = point_light('no-2-doorway-spill', (2.9, WALL_Y + 6.6, 2.6), 900.0, (1.0, 0.62, 0.32), soft=0.6)
    found['no-2-gateway-spill'] = point_light('no-2-gateway-spill', (n2, WALL_Y + 1.8, 2.7), 420.0, (1.0, 0.62, 0.32), soft=0.5)
    found['no-2-yard-spill'] = point_light('no-2-yard-spill', (n2 + 0.6, WALL_Y + 6.2, 2.2), 260.0, (1.0, 0.62, 0.32), soft=0.8)
    found['no-1-doorway-spill'] = point_light('no-1-doorway-spill', (-3.4, WALL_Y + 6.6, 2.6), 0.0, (1.0, 0.62, 0.32), soft=0.6)
    found['no-1-gateway-spill'] = point_light('no-1-gateway-spill', (gate_centre('no-1'), WALL_Y + 1.8, 2.7), 0.0, (1.0, 0.62, 0.32), soft=0.5)
    # No. 1's empty yard in the cool dusk light, so its shut gate's bars (own surfaces, drawn over the plate) show as a
    # dark silhouette against the yard and the shut cart doors behind (round 3's check: dark bars on a dark doorway). It
    # reaches only No. 1's mill front, its shut doors and its yard's setts (light linking), never the lane or the
    # doorway's room, which stays dark until "go"; the same in every state, so no time cut changes it
    yard = point_light('no-1-yard-dusk', (gate_centre('no-1'), WALL_Y + 3.6, 5.2), NO_1_YARD_ENERGY, (0.55, 0.68, 1.0), soft=2.0, shadow=False)
    dressing.light_reaches(yard, [o for o in bpy.data.objects if o.type == 'MESH' and o.name in (
        'no-1-mill-walls', 'no-1-mill-stonework', 'no-1-mill-ironwork', 'no-1-loading-door-left', 'no-1-loading-door-right', 'no-1-yard-setts')])
    found['no-1-yard-dusk'] = yard
    # the light streaming out of each lit yard through its open gateway onto the lane (spill 1 when flat out): a wide
    # soft beam from the yard, its edges cut by the gate's piers, so the gateway's warm light lies along the empty
    # pavement toward W2's camera (round 3's check: the bottom half of W2 was bare grey paving)
    for prefix, side in (('no-1', -1), ('no-2', 1)):
        beam = bpy.data.objects.new(f'{prefix}-gateway-beam', bpy.data.lights.new(f'{prefix}-gateway-beam', 'SPOT'))
        beam.data.color, beam.data.shadow_soft_size = (1.0, 0.64, 0.34), 1.2
        beam.data.spot_size, beam.data.spot_blend = math.radians(64), 0.7
        beam.data.use_shadow = True
        beam.location = (side * 3.3, WALL_Y + 6.8, 3.4)
        aim = Vector((side * 4.0, WALL_Y - 10.0, 0.0)) - beam.location
        beam.rotation_mode = 'QUATERNION'
        beam.rotation_quaternion = aim.to_track_quat('-Z', 'Y')
        kit.collection('works-lights').objects.link(beam)
        found[f'{prefix}-gateway-beam'] = beam
    # a warm light in each doorway's room, on when its doorway is lit: it gives the machines their form against the
    # lit far wall (reaching only the room and its machines)
    for prefix, (x, _) in (('no-1', (-3.4, 0)), ('no-2', (2.9, 0))):
        room = point_light(f'{prefix}-room-light', (x, WALL_Y + 8.0 + 2.2, 3.9), 0.0, (1.0, 0.66, 0.36), soft=0.8, shadow=False)
        dressing.light_reaches(room, [o for o in bpy.data.objects if o.type == 'MESH' and o.name in (f'{prefix}-doorway-room', f'{prefix}-doorway-machines')])
        found[f'{prefix}-room-light'] = room
    # W4's one pool of light on the jacket's corner (W4_LAMP; on only in the W4 state): a spot from a lamp out of the frame
    lamp = bpy.data.objects.new(W4_LAMP_NAME, bpy.data.lights.new(W4_LAMP_NAME, 'SPOT'))
    lamp.data.color, lamp.data.shadow_soft_size = W4_LAMP['colour'], 0.12
    lamp.data.spot_size, lamp.data.spot_blend = math.radians(W4_LAMP['cone_degrees']), W4_LAMP['blend']
    lamp.data.energy, lamp.data.use_shadow = 0.0, True
    lamp.location = W4_LAMP['at']
    lamp.rotation_mode = 'QUATERNION'
    lamp.rotation_quaternion = (Vector(W4_LAMP['aim']) - Vector(W4_LAMP['at'])).to_track_quat('-Z', 'Y')
    lamp.hide_render = True
    kit.collection('works-lights').objects.link(lamp)
    found[W4_LAMP_NAME] = lamp
    return found


def people_lights(lamp_lights):
    """Which of the people's own lights reach the waiting men, and the thin edge of light on them (round 5; round 4's
    check: the men were pure black with no edge light, one black mass the painter could not separate). Each gate lamp
    reaches only its gate's leaves, the chain, its board, its waiting men and its yard's setts (on the lane's paving it
    made a bright pool in front of the men, brighter than the gate). A cool light from each yard,
    behind the bars, and a warm one from the gate lamp's side reach only the waiting men, from behind and above, so each
    man keeps a thin rim along his shoulders and cap. The lantern on the DIESEL drum does not reach the men standing
    behind the drums (it would light their backs: they stay dark shapes). None of these lights reaches anything else,
    and the men cast no shadows, so a state picture still swaps only the men."""
    found = {}
    def meshes(objects):
        return [o for o in objects if o.type == 'MESH']
    for prefix, side in (('no-1', -1), ('no-2', 1)):
        men = meshes(bpy.data.collections[f'men-{prefix}'].all_objects)
        gate = bpy.data.objects.get(f'{prefix}-gate')
        chain = bpy.data.objects.get('no-1-chain') if prefix == 'no-1' else None
        board = bpy.data.objects.get(f'gate-board-{prefix}')
        reach = men + meshes(parts_of(gate) if gate else []) + meshes(parts_of(chain) if chain else []) + meshes(parts_of(board) if board else [])
        reach += [o for o in (bpy.data.objects.get(f'{prefix}-yard-setts'),) if o is not None]
        dressing.light_reaches(lamp_lights[prefix], reach)
        centre = gate_centre(prefix)
        for name, at, energy, colour in ((f'{prefix}-men-rim-yard', (centre + side * 1.2, GATE_PLANE_Y + 1.6, 2.4), MEN_RIM_ENERGY['yard'], (0.55, 0.68, 1.0)),
                                         (f'{prefix}-men-rim-lamp', (centre - side * 1.9, GATE_PLANE_Y + 0.3, 2.9), MEN_RIM_ENERGY['lamp'], (1.0, 0.72, 0.45))):
            rim = point_light(name, at, energy, colour, soft=0.6, shadow=False)
            dressing.light_reaches(rim, men)
            found[name] = rim
    lantern = bpy.data.objects.get('lantern_light')
    if lantern is not None:
        dressing.light_reaches(lantern, meshes(bpy.data.collections['men-no-1'].all_objects), only=False)
    # the people at work inside the doorways stand against the lit far wall: the yards' strong spill lights (in front of
    # the mill fronts) would light their backs a warm brown; they skip them, so they show as dark shapes
    at_work = meshes(list(bpy.data.collections['workers-no-1'].all_objects) + list(bpy.data.collections['workers-no-2'].all_objects))
    for name in SPILL_ENERGY:
        light = bpy.data.objects.get(name)
        if light is not None:
            dressing.light_reaches(light, at_work, only=False)
    return found


MEN_RIM_ENERGY = {'yard': 220.0, 'lamp': 90.0}    # the waiting men's edge lights (they reach only the men)


SPILL_ENERGY = {'no-2-doorway-spill': 900.0, 'no-2-gateway-spill': 420.0, 'no-2-yard-spill': 260.0, 'no-1-doorway-spill': 700.0, 'no-1-gateway-spill': 300.0,
                'no-2-gateway-beam': 4000.0, 'no-1-gateway-beam': 4000.0}
ROOM_ENERGY = 160.0          # each doorway room's light when its doorway is lit
NO_1_YARD_ENERGY = 900.0     # No. 1's yard in the cool dusk (round 5: from 260 W, so the shut gate's bars and the waiting men
                             # stand dark against a pale yard, the brightest part of W1 round its subject)


def show(collection_name, shown):
    c = bpy.data.collections.get(collection_name)
    if c is None:
        return
    c.hide_render = not shown
    for o in c.all_objects:
        o.hide_render = not shown


def set_state(name, plate=False, men_2_in_plate=False):
    state = STATES[name]
    show('men-no-1', state['men_1'])
    show('men-no-2', state['men_2'] and (men_2_in_plate or not plate))
    for prefix in ('no-1', 'no-2'):
        shown = state.get(f'workers_{prefix[-1]}', 0)
        for index, (_, name, _, _) in enumerate(WORKERS[prefix]):
            holder = bpy.data.objects.get(name)
            if holder is not None:
                for o in parts_of(holder):
                    o.hide_render = index >= shown
    show('gates', not plate)
    show('pop-up', state.get('pop_up_1', False) and not plate)
    kit.set_windows('no-1', state['windows_1'])
    kit.set_doorway('no-1', state['doorway_1'])
    kit.set_windows('no-2', state['windows_2'])
    kit.set_doorway('no-2', state['doorway_2'])
    for side in ('left', 'right'):
        leaf = bpy.data.objects.get(f'no-1-loading-door-{side}')
        if leaf is not None:
            leaf.rotation_mode = 'XYZ'
            leaf.rotation_euler.z = math.radians(100 if side == 'right' else -100) if state['doors_open_1'] else 0.0
    set_gate('no-1', state['gate_1'])
    set_gate('no-2', state['gate_2'])
    chain = bpy.data.objects.get('no-1-chain')
    if chain is not None:
        for o in parts_of(chain):
            o.hide_render = plate or not state['chained']
    shares = state.get('spill_shares', {})
    for name_, energy in SPILL_ENERGY.items():
        light = bpy.data.objects.get(name_)
        if light is not None:
            light.data.energy = energy * shares.get(name_, state['spill_1'] if name_.startswith('no-1') else state['spill_2'])
            light.hide_render = light.data.energy <= 0.0
    lamp = bpy.data.objects.get(W4_LAMP_NAME)
    if lamp is not None:
        lamp.data.energy = W4_LAMP['energy'] if state.get('corner_lamp') else 0.0
        lamp.hide_render = lamp.data.energy <= 0.0
    # things a view leaves out of its plate (W4: No. 2's gateway crates), shown in every other state
    for name_ in STATES['w4']['left_out']:
        holder = bpy.data.objects.get(name_)
        if holder is not None:
            for o in parts_of(holder):
                o.hide_render = name_ in state.get('left_out', ())
    for prefix in ('no-1', 'no-2'):
        room = bpy.data.objects.get(f'{prefix}-room-light')
        if room is not None:
            room.data.energy = ROOM_ENERGY if state[f'doorway_{prefix[-1]}'] else 0.0
            room.hide_render = room.data.energy <= 0.0
    bpy.context.view_layer.update()


def cameras():
    made = {}
    for name, view in views().items():
        data = bpy.data.cameras.new(f'camera-{name}')
        data.sensor_fit = 'VERTICAL'
        data.clip_start, data.clip_end = 0.1, 3000.0
        camera = bpy.data.objects.new(f'camera-{name}', data)
        camera.rotation_mode = 'XYZ'
        camera.rotation_euler = Euler((math.radians(90), 0, 0 if view['faces'] > 0 else math.pi), 'XYZ')   # level, never turned
        kit.collection('cameras').objects.link(camera)
        made[name] = camera
    return made


def camera_spot(name, spot):
    view = views()[name]
    x, y = view[spot] if view[spot] else view['plate']
    base = view['base'] if view.get('base') is not None else dressing.ground_height(x, y, 1.0)
    return Vector((x, y, base + view['eye']))    # eye height above the street or the yard


def put_camera(name, spot, fov):
    camera = bpy.data.objects[f'camera-{name}']
    camera.location = camera_spot(name, spot)
    camera.data.angle_y = math.radians(fov)
    bpy.context.scene.camera = camera
    bpy.context.view_layer.update()
    return camera


# ------------------------------------------------------------------------------------------ pictures and export

def render(path, width, height, samples):
    dressing.render(path, width, height, samples)


# the small check pictures: name: (view, state), each with the film's lens at the view's composed spot (W3 holds
# still, so its composed spot is its plate spot)
PREVIEWS = {'w3-quiet': ('w3', 'quiet'), 'w1-quiet': ('w1', 'quiet'), 'w1-working': ('w1', 'working'), 'w2-quiet': ('w2', 'quiet'),
            'w2-slowed': ('w2', 'slowed'), 'w4-w4': ('w4', 'w4')}


def draw_previews(folder, only):
    import time
    os.makedirs(folder, exist_ok=True)
    for picture, (view, state) in PREVIEWS.items():
        if only and picture not in only and view not in only:
            continue
        set_state(state)
        put_camera(view, 'composed', FILM_FOV)
        began = time.time()
        render(os.path.join(folder, f'{picture}.png'), PREVIEW_WIDTH, round(PREVIEW_WIDTH * 16 / 9), int(SAMPLES or 16))
        print(f'assemble_works: preview {picture} drawn in {time.time() - began:.0f} s', flush=True)


def draw_plates(folder, only):
    os.makedirs(folder, exist_ok=True)
    drawn = []
    for picture, (view, state, men_2, what) in PLATES.items():
        if only and picture not in only and view not in only:
            continue
        set_state(state, plate=True, men_2_in_plate=men_2)
        put_camera(view, 'plate', PLATE_FOV)
        print(f'assemble_works: drawing {picture} ({what})', flush=True)
        render(os.path.join(folder, f'{picture}.png'), 1536, 2730, int(SAMPLES or 48))
        drawn.append(picture)
    return drawn


def projector_json(name):
    camera = put_camera(name, 'plate', PLATE_FOV)
    q_blender = camera.matrix_world.to_quaternion()
    q_three = Quaternion((1, 0, 0), math.radians(-90)) @ q_blender
    location = camera.matrix_world.translation
    return {
        'about': f'The plate camera of the Works\' view {name.upper()} ({SCRIPT_NAME}), as the projector for projected-set.js. three.js space '
                 '(y-up): position (x, z, -y) of Blender; quaternion = rotation(-90 deg about x) * Blender quaternion.',
        'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
        'quaternion': [round(q_three.x, 6), round(q_three.y, 6), round(q_three.z, 6), round(q_three.w, 6)],
        'fov': PLATE_FOV, 'aspect': FILM_ASPECT, 'near': 0.1, 'far': 1500,
        'blender': {'location': [round(v, 5) for v in location], 'rotation_quaternion_wxyz': [round(v, 6) for v in q_blender]},
    }


# the film's files: name: (collections, what it holds)
PARTS = {
    'works-set-lane.glb': (('street', 'cottages', 'lamps', 'ground', 'sky', 'cross-street', 'bank', 'works-wall'),
                           'the lane, its terraces and gas lamps, the cross street and the end terrace, the bank, the low walls, the works wall with '
                           'its piers and gate arches, the dividing wall (the painting is shone onto it)'),
    'works-set-factories.glb': (('factories',), 'the two factories (their window groups, chimney-top markers and cart doors by name)'),
    'works-set-town.glb': (('town',), 'the far town'),
    'works-set-props.glb': (('props', 'men-no-1'), 'the props and No. 1\'s seven waiting men (in the paintings; the men are hidden when they go in)'),
    'works-signs.glb': (('signs',), 'own surfaces: the lettered things (gate boards, No. 2\'s with its lettered back for W4, drums, the bank\'s '
                                    'sign and plate)'),
    'works-gates.glb': (('gates',), 'own surfaces, never in a plate: the gate leaves (no-1-gate, no-2-gate) and No. 1\'s chain (no-1-chain)'),
    'works-pop-up.glb': (('pop-up',), 'own surfaces, never in a plate: the crates that pop up in No. 1\'s gateway (no-1-crate-1 to 3)'),
    'works-no-2-men.glb': (('men-no-2',), 'No. 2\'s eight waiting men: painted in W2\'s slowed helper plate, dark own-surface silhouettes in W4'),
    'works-doorway-workers.glb': (('workers-no-1', 'workers-no-2'), 'the people at work inside the two lit doorways (no-1-worker-1 and 2, '
                                  'no-2-worker-1 and 2): painted into the plates, kept here for the record; the film need not load them'),
}


def export_for_film(folder, facts):
    os.makedirs(folder, exist_ok=True)
    set_state('quiet')
    set_gate('no-1', 0)
    set_gate('no-2', 0)       # the film finds each leaf's hinge from the leaf shut
    for c in bpy.data.collections:
        c.hide_render = False
    for o in bpy.data.objects:
        o.hide_render = False
        o.hide_set(False)
        o.hide_viewport = False
    written = {}
    for file_name, (collections, what) in PARTS.items():
        bpy.ops.object.select_all(action='DESELECT')
        chosen = 0
        for o in bpy.context.scene.objects:
            if o.type in ('MESH', 'EMPTY') and any(c.name in collections for c in o.users_collection):
                o.select_set(True)
                chosen += 1
        path = os.path.join(folder, file_name)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_cameras=False,
                                  export_lights=False, export_apply=True, export_extras=True)
        written[file_name] = {'holds': what, 'objects': chosen, 'megabytes': round(os.path.getsize(path) / 1e6, 1)}
        print(f'assemble_works: wrote {file_name} ({written[file_name]["megabytes"]} MB, {chosen} objects)', flush=True)
    for name in views():
        with open(os.path.join(folder, f'works-camera-{name}.json'), 'w') as handle:
            json.dump(projector_json(name), handle, indent=1)
    facts['files'] = written
    with open(os.path.join(folder, 'works-shot.json'), 'w') as handle:
        json.dump(facts, handle, indent=1)
    print('assemble_works: wrote the cameras and works-shot.json into', folder)


def marker_spot(name):
    o = bpy.data.objects.get(name)
    return [round(v, 3) for v in o.matrix_world.translation] if o else None


def men_frame_facts(camera_name, spot, collection_name):
    """Each man's distance from a view's camera and his box on the film's frame."""
    from bpy_extras.object_utils import world_to_camera_view
    camera = put_camera(camera_name, spot, FILM_FOV)
    scene = bpy.context.scene
    found = []
    for holder in [o for o in bpy.data.collections[collection_name].objects if o.parent is None]:
        corners = [o.matrix_world @ Vector(c) for o in holder.children_recursive if o.type == 'MESH' for c in o.bound_box]
        on_frame = [world_to_camera_view(scene, camera, c) for c in corners]
        feet = holder.matrix_world.translation
        found.append({'name': holder.name, 'distance_metres': round((feet.to_2d() - camera.location.to_2d()).length, 2),
                      'film_frame_box': [round(min(p.x for p in on_frame), 3), round(1 - max(p.y for p in on_frame), 3),
                                         round(max(p.x for p in on_frame), 3), round(1 - min(p.y for p in on_frame), 3)]})
    return sorted(found, key=lambda entry: entry['distance_metres'])


# ------------------------------------------------------------------------------------------ main

def build():
    scene = bpy.context.scene
    for o in [o for o in bpy.data.objects if o.name in ('main_camera', 'side_camera')]:
        bpy.data.objects.remove(o, do_unlink=True)
    lowered = level_ground_under_the_yards()
    # the cottages' window lights only warm the pavement under their windows: no shadows (each shadow-casting light
    # slows EEVEE a great deal on this machine)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and '_window_light_' in o.name:
            o.data.use_shadow = False
    # the downpipes of the last cottage on each side stood a metre from W1's and W2's cameras, a dark bar down the frame
    delete_objects({o for o in bpy.data.objects if o.name in ('left_row_a_cottage_04_rainwater', 'right_row_a_cottage_04_rainwater')})
    # the cottages beside W1's and W2's cameras keep their windows dark: a lit window at the frame's edge outshone the
    # gate (the shot checker's rule 10); the cottages nearer the lane's mouth keep theirs for W3 and W4
    for prefix in ('right_row_a_cottage_03_', 'right_row_a_cottage_04_', 'left_row_a_cottage_04_'):
        for o in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
            if o.type == 'LIGHT':
                bpy.data.objects.remove(o, do_unlink=True)
            elif o.type == 'MESH' and '_glass_' in o.name:
                for slot in o.material_slots:
                    if slot.material and slot.material.name.startswith('window_lit_glow_'):
                        slot.material = bpy.data.materials[slot.material.name.replace('window_lit_glow_', 'window_dark_')]
    # ... but each of the two nearest houses keeps one upstairs window faintly lit behind its curtains, the far one of
    # the house beside W1 (left) and of the house beside W2 (right): the quiet side of each gate view is big and dim, and
    # a small light of its own keeps it from reading as a blank wall (composing rule 10)
    for name in DIM_WINDOWS:
        glass = bpy.data.objects.get(name)
        if glass is not None:
            glass.data = glass.data.copy()
            for slot in glass.material_slots:
                if slot.material and slot.material.name.startswith('window_dark_'):
                    slot.material = dim_window_material(slot.material.name.replace('window_dark_', 'window_lit_glow_'))
    move_lane_lamps()
    made_terrace = end_terrace()
    cross_street()
    coping_top = low_walls()
    pieces = works_wall()
    bank_facts = bank()
    holders = factories_and_town()
    gate_facts = gates()
    furniture, lamp_lights = gate_furniture(pieces)
    fire_facts = brazier_and_lantern(coping_top)
    placed = people()
    at_work = workers()
    yard = yard_things(pieces)
    spills = lights()
    spills.update(people_lights(lamp_lights))
    # Only the lights that must throw shadows keep them: the fire, the lit yards' spill (inside the walls) and the dusk
    # sky's light. Each shadow-casting light costs about two seconds a sample on this machine (EEVEE without a
    # graphics card), and the lamps, the lantern and the low afterglow read as well without.
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and not (o.name in ('brazier_light', 'dusk_skylight', W4_LAMP_NAME) or o.name.endswith('-spill') or o.name.endswith('-beam')):
            o.data.use_shadow = False
    made_cameras = cameras()
    merged = merge_duplicate_materials()
    print(f'assemble_works: built (ground lowered at {lowered} points, {made_terrace} end-terrace parts, {merged} duplicate materials merged)', flush=True)
    facts = {
        'about': 'The Works (assemble_works.py; plan 34 part 1 "A. The Works"): where things are, Blender space (x, y, z), metres; three.js is '
                 '(x, z, -y). x across the lane (No. 1 at minus x, always on the left looking up the lane), y up the lane from its mouth, z up.',
        'lane': {'built_with': 'build_street.py -- ' + ' '.join(LANE_SETTINGS), 'works_wall_face_y': WALL_Y, 'kerb_face_x': KERB_X,
                 'house_front_x': HOUSE_FRONT_X, 'terraces_end_y': TERRACE_END_Y, 'cross_street': CROSS_STREET,
                 'gate_views': GATE_VIEWS, 'gate_shift': GATE_SHIFT},
        'film_fov_degrees': FILM_FOV, 'plate_fov_degrees': PLATE_FOV,
        'decisions': {
            'w1_w2_camera_places': 'Settled with the shot checker (round 3), four ways: (A) the pavement\'s middle, 1.1 m from the house '
                                   'fronts, gates 7 m apart: 12 problems in W1 and 4 in W2, the lines meeting on the gate (0.004 away), nothing '
                                   'past the phone buttons; (B) gates moved 0.9 m toward the lane\'s middle, camera in line with the outer pier: '
                                   '15 and 5, the queue\'s nearest man past 0.95 across; (C) gates moved 0.5 m: 15 and 5, the same, the lantern '
                                   'hidden; (D) the first plan\'s spot in line with the outer pier, 0.2 m from the house fronts: inside the '
                                   'bank\'s bay window, everything hidden. Kept: (A).',
            'w4_camera': 'round 5: 0.16 m beside No. 2\'s inner hinge post\'s line, toward the gateway\'s middle (in line with the post, the '
                         'back of the No. 2 board\'s "No." was cut by the frame\'s edge), sliding from 6.7 to 5.5 m from the gate (round 4: 7.2 to '
                         '6.0); its corner\'s things stand where the inner pier hides them from W1, W2 and W3; the gateway crates are left out of '
                         'its plate (works-shot.json w4.left_out: the film hides them on page 14)',
            'lane_head_corners': 'the drums stand in a flagged corner in front of each outer pier: along the house fronts\' line they hid '
                                 'the brazier from W1',
            'men_shadows': 'the men cast no long shadows (each has a small soft patch at his feet), so a state picture swaps only the men '
                           'and their feet (round 2: long shadows made the swap area 42% of the frame)',
            'round_4': 'W1 and W2 stand 0.4 m toward the kerb from the pavement\'s middle (x -3.7 and 3.7): the nearest house front fills '
                       'less of the frame\'s side and the lane head\'s corner shows. W3\'s eye is 5.6 m above the lane (the end terrace on a '
                       'raised footway 1 m up), so the queue\'s tail, 6 m in front of W1\'s composed spot, reaches about 0.70 down in W3. '
                       'No. 1\'s brazier stands against the outer pier with the stooped man at its front-left, the PETROL and DIESEL drums to '
                       'its right with both words whole from W1; the queue stands along the kerb to the right of them, 1.1 m apart. No. 2\'s '
                       'drums stand by its outer pier with a clear gap, both words whole from W2. The handcart is on the right pavement in '
                       'W3\'s bottom third. No. 1\'s yard is in a faint cool light (its gate\'s bars show against it); a warm beam from No. 2\'s '
                       'yard lies along the pavement in W2; one curtained window glows on each gate view\'s quiet side.',
            'round_5': 'W1 and W2 stand 3 m nearer the gates (plate spot 10.0 m and composed spot 8.8 m from the works wall, the slide still '
                       '1.2 m). The waiting men stand gathered in front of each shut gate, a loose crowd two deep, backs to the lane, with a '
                       'thin rim of light from the yard and the gate lamp; at No. 1 the brazier stands against the right gate leaf with the '
                       'stooped man at it, and the PETROL and DIESEL drums stand in front of the crowd\'s left end (at No. 2 its right end), '
                       'so no man stands between them and the gate views or W3 (against the dividing wall, as round 4\'s check asked, they '
                       'would lie past 0.93 across in W1). The gate lamps hang on the outer piers\' inner faces and light only the gates, '
                       'chains, boards, men and ground. People at work show in both lit doorways (No. 1\'s from "go"). No. 1\'s looms are '
                       'chest-high with big driving wheels and cloth; both far walls are broken up. The pop-up crates stand in the gateway\'s '
                       'middle; the handcart, loaded with crates, at the right pavement\'s kerb. W4 (round 5, a second pass): a jacket with '
                       'sleeves on a peg, a crate table under it with a flat cap, a tin mug and a WAGES envelope 2.6 times life size, all '
                       'touching, on No. 2\'s inner pier where only W4 sees them; the No. 2 board lettered on its back; one warm pool of '
                       'lamplight on that corner and the rest of the yard in the dusk; the gateway crates left out of W4\'s plate; W4 0.2 m '
                       'beside the hinge post, sliding from 6.7 to 5.5 m from the gate.'},
        'views': {},
        'gates': gate_facts,
        'chimney_tops': {name: marker_spot(name) for name in ('no-1-chimney-top', 'no-2-chimney-a-top', 'no-2-chimney-b-top')},
        'no-2-tank-top': marker_spot('no-2-tank-top'),
        'doorway_feet': {name: marker_spot(f'{name}-doorway-foot') for name in ('no-1', 'no-2')},
        'gate_lamps': {prefix: [round(v, 3) for v in light.location] for prefix, light in lamp_lights.items()},
        **fire_facts,
        'drums': {key: value for key, value in furniture.items() if '-drum-' in key},
        'boards': {key: value for key, value in furniture.items() if key.endswith('-board')},
        'bank': bank_facts,
        **{key: value for key, value in yard.items()},
        'men': [entry['name'] for entry in placed['men-no-1']],
        'men_at_no_1': placed['men-no-1'],
        'men_at_no_2': placed['men-no-2'],
        'workers': {'about': 'the people at work inside each lit doorway (painted into the plates; not in the film\'s set): No. 2\'s in every '
                             'No. 2 plate (the first only when slowed), No. 1\'s in the working and "men gone" helper plates', **at_work},
        'machines': {'about': 'the middle of the machines seen through each doorway, for the pages\' labels (Blender x, y, z)',
                     'no-2-flywheel': marker_spot('no-2-flywheel-middle'), 'no-1-looms': marker_spot('no-1-looms-middle')},
        'no_2_men': [entry['name'] for entry in placed['men-no-2']],
        'queue_front': placed['men-no-1'][0]['feet'],
        'lights': {name: [round(v, 3) for v in light.location] for name, light in spills.items()},
        'states': {name: {key: (sorted(value) if isinstance(value, set) else value) for key, value in state.items()} for name, state in STATES.items()},
        'plates': {name: {'view': view, 'state': state, 'no_2_men': men_2, 'what': what} for name, (view, state, men_2, what) in PLATES.items()},
        'state_pictures': {
            'about': 'made from the plates standing in for the paintings, with paper-film/tools/make_state_picture.py (outlines from the shot '
                     'checker at each plate camera, --fov 64.4); make them again from the paintings once they are approved',
            'works-w1-men-gone-state.png': 'W1 main plate, with the men-gone helper plate where the men stood, where the cart doorway opened '
                                           'and where two of the men now stand at the looms inside (mask works-w1-men-gone-mask.png, about '
                                           '12% of the frame, round 5): the time cut on "go"',
            'works-w1-working-state.png': 'W1 main plate, with the working helper plate wherever they differ (about 74% of the frame: the '
                                          'windows, the doorway and the yard\'s light on the lane): the blend on "start"',
            'works-w2-slowed-state.png': 'W2 main plate, with the slowed helper plate where the eight men stand, the windows go dark and one of '
                                         'the two people at work inside goes (about 14% of the frame): page 12',
            'works-w1-behind.png': 'W1 main plate, with the behind helper plate (the men left out, all else quiet) where the men stood '
                                   '(about 8% of the frame): the behind picture for page 3\'s slide, so what the men hid is the quiet '
                                   'works (the "men gone" and working pictures have No. 1\'s doorway or windows lit there)'},
    }
    for name, view in views().items():
        facts['views'][name] = {'plate': [round(v, 3) for v in camera_spot(name, 'plate')],
                                'composed': [round(v, 3) for v in camera_spot(name, 'composed')] if view['composed'] else None,
                                'subject': list(view['subject']), 'faces': '+y (up the lane)' if view['faces'] > 0 else '-y (down the lane)',
                                'eye_height_metres': view['eye'], 'stands_on': view['stands_on'], 'about': view['about'],
                                'camera_file': f'works-camera-{name}.json'}
    # how tall the signs' letters come out on the film's frame (1920 pixels tall) at each view's composed spot
    def letter_pixels(view_name, point, letter_metres):
        spot = camera_spot(view_name, 'composed')
        depth = abs(point[1] - spot.y)
        return round(1920 * letter_metres / (2 * depth * math.tan(math.radians(FILM_FOV / 2))), 1)
    board_1, board_2 = furniture['no-1-board'], furniture['no-2-board']
    facts['letter_pixels'] = {
        'about': 'letter heights on the film\'s 1080 x 1920 frame at each view\'s composed spot (letters: gate boards 0.266 and 0.25 m, '
                 'the bank\'s sign 0.305 m, PETROL 0.097 m, DIESEL 0.106 m, W4\'s WAGES 0.047 m)',
        'w3 bank sign': letter_pixels('w3', bank_facts['sign'], 0.305), 'w3 No. 1 board': letter_pixels('w3', board_1, 0.266),
        'w3 No. 2 board': letter_pixels('w3', board_2, 0.25), 'w1 No. 1 board': letter_pixels('w1', board_1, 0.266),
        'w2 No. 2 board': letter_pixels('w2', board_2, 0.25), 'w1 PETROL': letter_pixels('w1', furniture['no-1-drum-petrol'], 0.097),
        'w2 PETROL': letter_pixels('w2', furniture['no-2-drum-petrol'], 0.097),
        'w4 WAGES': letter_pixels('w4', yard['w4']['wages'], round(0.018 * W4_ENVELOPE_SCALE, 3)),
        'w4 No. 2 board back': letter_pixels('w4', yard['w4']['board_back'], 0.25)}
    facts['men_seen'] = {'w1 composed': men_frame_facts('w1', 'composed', 'men-no-1'), 'w1 plate': men_frame_facts('w1', 'plate', 'men-no-1'),
                         'w3': men_frame_facts('w3', 'plate', 'men-no-1'), 'w2 composed (slowed)': men_frame_facts('w2', 'composed', 'men-no-2'),
                         'w4 composed (silhouettes)': men_frame_facts('w4', 'composed', 'men-no-2')}
    return facts


facts = build()
if '--previews' in given:
    only = (kit.option('--only') or '').split(',') if kit.option('--only') else []
    draw_previews(os.path.abspath(kit.option('--previews')), [name for name in only if name])
if '--plates' in given:
    only = (kit.option('--only') or '').split(',') if kit.option('--only') else []
    draw_plates(os.path.abspath(kit.option('--plates')), [name for name in only if name])
if '--export' in given:
    export_for_film(OUT_FOLDER, facts)
else:
    print('assemble_works: men seen:', json.dumps(facts['men_seen'], indent=1))
state = STATE_ASKED or MAIN_STATE[VIEW]
set_state(state)
if kit.option('--preview'):
    put_camera(VIEW, 'composed', FILM_FOV)
    render(kit.option('--preview'), PREVIEW_WIDTH, round(PREVIEW_WIDTH * 16 / 9), int(SAMPLES or 16))
if kit.option('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(kit.option('--save')), relative_remap=True)
put_camera(VIEW, 'composed', FILM_FOV)    # left on the film's view, for a script run after this one (shot_facts.py)
print(f'assemble_works: done (view {VIEW}, state {state})', flush=True)
