# What this does: builds simple but well-shaped people by script in Blender, for chapter 2's redesign
# (plan 34, part "People"): working men of the early twentieth century in long work coats and flat caps,
# in dull browns and greys, in five waiting poses (hands in pockets, arms folded, one hand raised on a
# gate bar, stooped toward a brazier, leaning on a wall), and walking men and women, some with a bundle
# or a bag, for far-off crowds. They are made to read as people from behind and in silhouette at 6 to
# 9 m, not as mannequins or capsules: heads with ears, necks, sloping shoulders, arms that bend at the
# elbow, hands as simple mitts, coat skirts with folds, trouser legs, boots, and each man his own height,
# build, stance and colours. No faces: they are seen from behind or dark.
# Seen from behind, a head must never read as a bald scalp or a blank face (round 1's check, log 34):
#   - dark, matt hair covers the back and sides of every head from under the cap down into the collar
#     (a shiny dark hair caught the street lamps and came out paler than the coats, like a bald head)
#   - every man seen from behind has his collar turned up or a muffler worn high at the back, so almost
#     no neck shows; the caps sit a little low, their band just over the tops of the ears
#   - the women are bare-headed, their hair pinned up, their shawls round their shoulders (a shawl over
#     the head read as a nun's hood)
#
# How a figure is made:
#   - its pose is a few numbers: how far the hips sit and the body leans, where each wrist and foot
#     goes; the elbows and knees follow (two bones of real length, bent toward a given side), so arms
#     and legs always keep their length
#   - each piece of clothing is a smooth shell lofted round those joints: rings round the body for the
#     coat (its skirt hangs straight down round the legs, wide enough to hold them), tubes along the
#     arms and legs, rings round the head for the cap, a D-shaped loft along each foot for the boots
#   - the cloth wears a free Poly Haven surface (CC0: wool, tweed, corduroy, leather, knitted wool,
#     linen), tinted dull and mottled a little so it reads as worn cloth, not plastic. The mottling is
#     seeded from the cloth's name (zlib.crc32, the same on every run), and each tinted picture's file
#     name carries a fingerprint of its surface and colour, so a rebuild gives the same pictures and a
#     changed colour makes a new one
#   - all the pieces are joined into one mesh hung under one root empty named after the figure
# Real sizes: men 1.68 to 1.78 m, women 1.55 to 1.60 m. Each figure stands on height 0 with its feet
# about its origin and faces +y in Blender (so, turned 0, it shows its back to a camera looking up the
# street, +y); its right hand is on +x. In three.js (y up) it faces -z.
#
# Writes NAME.glb for each into assets/models/inflation-chapter-2-newcomers/figures/ and its line in
# index.json there (what it is, its height, pose, triangles, size).
# Run (the cloth surfaces first, into a scratch folder):
#   python3 -I fetch_cloth_textures.py SCRATCH
#   FIGURES_SCRATCH=SCRATCH blender -b --python build_figures.py                        (all)
#   FIGURES_SCRATCH=SCRATCH blender -b --python build_figures.py -- worker-arms-folded  (some)
# Units are metres.

import json
import math
import os
import sys
import tempfile
import zlib

import bmesh
import bpy
import numpy
from mathutils import Matrix, Vector

KIT_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
FIGURES_FOLDER = os.path.join(KIT_FOLDER, 'assets', 'models', 'inflation-chapter-2-newcomers', 'figures')
INDEX_PATH = os.path.join(FIGURES_FOLDER, 'index.json')
# downloads and the tinted cloth pictures (not kept in the repository); FIGURES_SCRATCH chooses the folder
SCRATCH = os.environ.get('FIGURES_SCRATCH', os.path.join(tempfile.gettempdir(), 'figures'))
SURFACES = os.path.join(SCRATCH, 'surfaces')
CLOTH_PICTURES = os.path.join(SCRATCH, 'cloth-pictures')
SOURCE = 'Built by script (paper-film/blender/figures/build_figures.py) with Poly Haven CC0 cloth surfaces'
LICENCE = 'Own work; cloth textures CC0 1.0 (Poly Haven: caban, poly_wool_herringbone, ribbed_corduroy, fabric_leather_02, knitted_fleece, rough_linen)'

# ------------------------------------------------------------------------- body measurements
# for a 1.75 m man standing straight; every figure is scaled by its height over this
STANDARD_HEIGHT = 1.75
PELVIS_HEIGHT = 0.96        # the middle of the hips above the ground
HIP_SIDE = 0.09             # each hip joint out from the middle
HIP_DROP = 0.05             # the hip joints below the middle of the hips
WAIST_UP = 0.14             # the waist above the middle of the hips
CHEST_UP = 0.19             # the chest above the waist
SHOULDER_SIDE = 0.175       # each shoulder joint out from the middle (men)
SHOULDER_UP = 0.110         # the shoulder joints (the middle of the ball of the arm) above the chest: the top of
                            # the shoulder is about 6 cm higher, about 1.46 m
NECK_UP = 0.200             # the bottom of the neck above the chest
NECK_BACK = -0.015          # ... and a little behind it
HEAD_UP = 0.145             # the middle of the head above the bottom of the neck
HEAD_FORWARD = 0.02
UPPER_ARM = 0.295
FOREARM = 0.255
THIGH = 0.42
SHIN = 0.415
ANKLE_HEIGHT = 0.075
HEAD_HALF_SIZE = (0.0775, 0.0975, 0.115)   # half its width, depth (front to back) and height


# ------------------------------------------------------------------------------- the figures
# Positions in a pose are in metres for a 1.75 m man (scaled with the figure), from the point on the ground
# between its feet: x to its right, y the way it faces, z up. Turns are in degrees: (forward, side, twist):
# forward leans toward the way it faces, side leans toward its right, twist turns it to its left.
# Each arm: the wrist's place, which way the elbow points, and the hand ('hidden' in a pocket or tucked,
# 'relaxed', 'grip' round a bar or a handle, 'warming' held out flat, palms down).
# Each foot: where the ankle stands, how far the toe turns out, and pitch (+ the heel lifted off the ground,
# walking off the toes; - the toes lifted, landing on the heel).
FIGURES = {
    'worker-hands-in-pockets': {
        'what': 'working man in a long brown wool coat, collar up, flat cap, hands deep in his coat pockets, '
                'shoulders hunched against the cold, weight on his left leg',
        'kind': 'man', 'height': 1.74, 'build': 1.04, 'coat': ('coat brown', 0.40), 'collar': 'up', 'muffler': None,
        'cap': 'cap grey tweed', 'trousers': 'trousers dark corduroy', 'seed': 1,
        'pose': {
            'pelvis': (-0.025, 0.0, -0.01), 'pelvis_turn': (0, -3, 4), 'lean': (3, 1, 0), 'chest': (6, 2, -4),
            'head': (10, -3, 6), 'shrug': 0.015,
            'right_arm': {'wrist': (0.15, 0.10, 0.92), 'elbow': (1, -0.8, 0), 'hand': 'hidden'},
            'left_arm': {'wrist': (-0.15, 0.10, 0.92), 'elbow': (-1, -0.8, 0), 'hand': 'hidden'},
            'right_foot': {'at': (0.14, 0.05), 'turn': 16},
            'left_foot': {'at': (-0.09, -0.02), 'turn': 9},
        },
    },
    'worker-arms-folded': {
        'what': 'stocky working man in a long grey wool coat with a muffler, flat cap, arms folded across his '
                'chest, feet planted apart',
        'kind': 'man', 'height': 1.70, 'build': 1.09, 'coat': ('coat grey', 0.42), 'collar': 'down', 'muffler': 'muffler oatmeal',
        'cap': 'cap brown tweed', 'trousers': 'trousers brown corduroy', 'seed': 2,
        'pose': {
            'lean': (-3, 0, 0), 'chest': (3, 0, 0), 'head': (6, 2, -10), 'shoulders_forward': 0.03,
            'right_arm': {'wrist': (-0.10, 0.215, 1.20), 'elbow': (0.5, 0.2, -1), 'hand': 'hidden'},
            'left_arm': {'wrist': (0.11, 0.235, 1.16), 'elbow': (-0.5, 0.2, -1), 'hand': 'hidden'},
            'right_foot': {'at': (0.14, 0.01), 'turn': 14},
            'left_foot': {'at': (-0.13, 0.03), 'turn': 12},
        },
    },
    'worker-hand-on-bar': {
        'what': 'tall, thin working man in a long olive-brown tweed coat, collar up, flat cap, his right hand '
                'raised gripping an upright bar in front of him (a gate bar) at shoulder height, his left in his pocket',
        'kind': 'man', 'height': 1.78, 'build': 0.95, 'coat': ('coat olive tweed', 0.43), 'collar': 'up', 'muffler': None,
        'cap': 'cap dark tweed', 'trousers': 'trousers dark corduroy', 'seed': 3,
        'grip_bar': (0.15, 0.40),   # where the bar it holds stands (x, y), so the shot can put one there
        'pose': {
            'pelvis': (0.02, 0.0, 0.0), 'pelvis_turn': (0, 2, -4), 'lean': (4, 2, -6), 'chest': (3, 1, -4), 'head': (-4, 0, -4),
            'right_arm': {'wrist': (0.13, 0.36, 1.50), 'elbow': (1, -0.2, -1), 'hand': 'grip', 'hand_direction': (0.05, 1, 0.05),
                          'hand_back': (1, 0, 0)},
            'left_arm': {'wrist': (-0.15, 0.10, 0.92), 'elbow': (-1, -0.8, 0), 'hand': 'hidden'},
            'right_foot': {'at': (0.11, 0.06), 'turn': 8},
            'left_foot': {'at': (-0.12, -0.14), 'turn': 18},
        },
    },
    'worker-stooped-to-brazier': {
        'what': 'working man in a long charcoal wool coat with a muffler, flat cap, stooping forward with his '
                'knees bent and both hands held out flat, palms down, a hand\'s breadth above the rim of a brazier in '
                'front of him, to warm them',
        'kind': 'man', 'height': 1.68, 'build': 1.0, 'coat': ('coat charcoal', 0.40), 'collar': 'down', 'muffler': 'muffler grey brown',
        'cap': 'cap grey tweed', 'trousers': 'trousers brown corduroy', 'seed': 4,
        'brazier_ahead': 0.62,   # the brazier's middle this far in front of his feet
        # his hands hover over the fire, about 12 cm higher than in round 1 (they seemed to rest on the hot rim of the
        # 0.86 m brazier drum); index.json gives the hands' lowest point, so a shot can check the gap to its rim
        'pose': {
            'pelvis': (0.0, -0.08, -0.07), 'lean': (26, 0, 0), 'chest': (14, 0, 0), 'head': (-22, 0, 0),
            'right_arm': {'wrist': (0.11, 0.40, 1.13), 'elbow': (0.7, 0, -1), 'hand': 'warming', 'hand_direction': (0.05, 1, -0.1),
                          'hand_back': (0, 0, 1)},
            'left_arm': {'wrist': (-0.12, 0.38, 1.15), 'elbow': (-0.7, 0, -1), 'hand': 'warming', 'hand_direction': (-0.05, 1, -0.1),
                         'hand_back': (0, 0, 1)},
            'right_foot': {'at': (0.13, 0.08), 'turn': 10},
            'left_foot': {'at': (-0.12, 0.0), 'turn': 13},
        },
    },
    'worker-leaning-on-wall': {
        'what': 'working man in a long fawn tweed coat, collar up, flat cap, leaning his right shoulder on a '
                'wall, legs crossed at the ankles, hands in his pockets',
        'kind': 'man', 'height': 1.72, 'build': 0.98, 'coat': ('coat fawn tweed', 0.41), 'collar': 'up', 'muffler': None,
        'cap': 'cap dark tweed', 'trousers': 'trousers dark corduroy', 'seed': 5,
        'wall_side': 'right',   # the wall touches his right shoulder
        'pose': {
            'pelvis': (0.11, 0.0, -0.015), 'pelvis_turn': (0, 6, 3), 'lean': (1, 4, 0), 'chest': (2, 1, 0), 'head': (4, -8, 8),
            'right_arm': {'wrist': (0.155, 0.10, 0.92), 'elbow': (1, -0.8, 0), 'hand': 'hidden'},
            'left_arm': {'wrist': (-0.15, 0.10, 0.92), 'elbow': (-1, -0.8, 0), 'hand': 'hidden'},
            'right_foot': {'at': (-0.10, 0.11), 'turn': -16, 'pitch': 26},
            'left_foot': {'at': (-0.04, -0.05), 'turn': 10},
        },
    },
    'walker-man-coat': {
        'what': 'man walking away in a long grey-brown wool coat and flat cap, mid-stride, arms swinging',
        'kind': 'man', 'height': 1.73, 'build': 1.0, 'coat': ('coat grey brown', 0.45), 'collar': 'up', 'muffler': None,
        'cap': 'cap grey tweed', 'trousers': 'trousers dark corduroy', 'seed': 6, 'walker': True,
        'pose': {
            'pelvis_turn': (0, 0, 6), 'lean': (5, 0, 0), 'chest': (2, 0, -10), 'head': (3, 0, 4),
            'right_arm': {'wrist': (0.22, -0.17, 0.85), 'elbow': (0.3, -1, -0.2), 'hand': 'relaxed'},
            'left_arm': {'wrist': (-0.19, 0.19, 0.84), 'elbow': (-0.3, -1, -0.4), 'hand': 'relaxed'},
            'right_foot': {'at': (0.09, 0.33), 'turn': 6, 'pitch': -14},
            'left_foot': {'at': (-0.09, -0.29), 'turn': 8, 'pitch': 30},
        },
    },
    'walker-man-bundle': {
        'what': 'man walking away in a short brown work jacket and flat cap with a tied cloth bundle on his right '
                'shoulder, holding its knot',
        'kind': 'man', 'height': 1.69, 'build': 1.02, 'coat': ('coat brown', 0.76), 'collar': 'down', 'muffler': 'muffler grey brown',
        'cap': 'cap brown tweed', 'trousers': 'trousers brown corduroy', 'seed': 7, 'walker': True,
        'bundle': {'at': (0.21, -0.09, 1.52), 'size': (0.34, 0.26, 0.21), 'turn': 25, 'cloth': 'bundle linen'},
        'pose': {
            'pelvis_turn': (0, 0, -6), 'lean': (7, -2, 0), 'chest': (3, -3, 8), 'head': (2, -6, -4), 'shrug': 0.01,
            'right_arm': {'wrist': (0.17, 0.02, 1.44), 'elbow': (1, 0.3, -1), 'hand': 'grip', 'hand_direction': (0.1, -0.6, 1),
                          'hand_back': (1, 0, 0)},
            'left_arm': {'wrist': (-0.21, -0.16, 0.85), 'elbow': (-0.3, -1, -0.2), 'hand': 'relaxed'},
            'right_foot': {'at': (0.09, -0.28), 'turn': 8, 'pitch': 30},
            'left_foot': {'at': (-0.09, 0.30), 'turn': 6, 'pitch': -12},
        },
    },
    'walker-man-bag': {
        'what': 'man walking away in a short grey work jacket and flat cap, carrying a leather bag in his right hand',
        'kind': 'man', 'height': 1.76, 'build': 0.97, 'coat': ('coat grey', 0.78), 'collar': 'up', 'muffler': None,
        'cap': 'cap dark tweed', 'trousers': 'trousers dark corduroy', 'seed': 8, 'walker': True,
        'bag': {'size': (0.40, 0.17, 0.27), 'cloth': 'bag leather'},
        'pose': {
            'pelvis_turn': (0, 3, 5), 'lean': (4, 3, 0), 'chest': (2, 2, -8), 'head': (2, 0, 0),
            'right_arm': {'wrist': (0.25, 0.0, 0.81), 'elbow': (0.4, -1, 0), 'hand': 'grip', 'hand_direction': (0, 0.2, -1),
                          'hand_back': (1, 0, 0)},
            'left_arm': {'wrist': (-0.19, 0.19, 0.85), 'elbow': (-0.3, -1, -0.4), 'hand': 'relaxed'},
            'right_foot': {'at': (0.09, 0.31), 'turn': 6, 'pitch': -14},
            'left_foot': {'at': (-0.09, -0.28), 'turn': 8, 'pitch': 28},
        },
    },
    # the women are bare-headed, their hair pinned up, their shawls round their shoulders: a shawl drawn over the head
    # read as a nun's hood in round 1's plate. 'shawl_over_head': True still builds the hooded shawl, for a shot that
    # needs one
    'walker-woman-shawl': {
        'what': 'woman walking away in a long dark skirt, bare-headed with her dark hair pinned up in a bun, a grey '
                'knitted shawl round her shoulders, holding it closed in front',
        'shawl_over_head': False, 'hair_style': 'bun',
        'kind': 'woman', 'height': 1.58, 'build': 1.0, 'skirt': 'skirt charcoal', 'bodice': 'coat charcoal', 'shawl': 'shawl grey',
        'seed': 9, 'walker': True,
        'pose': {
            'pelvis_turn': (0, 0, 5), 'lean': (4, 0, 0), 'chest': (3, 0, -6), 'head': (6, 0, 0),
            'right_arm': {'wrist': (-0.03, 0.20, 1.16), 'elbow': (0.6, -0.2, -1), 'hand': 'hidden'},
            'left_arm': {'wrist': (0.03, 0.19, 1.13), 'elbow': (-0.6, -0.2, -1), 'hand': 'hidden'},
            'right_foot': {'at': (0.07, 0.25), 'turn': 6, 'pitch': -10},
            'left_foot': {'at': (-0.07, -0.22), 'turn': 6, 'pitch': 26},
        },
    },
    'walker-woman-bundle': {
        'what': 'woman walking away in a long brown skirt, bare-headed with her dark hair pinned in a low knot at the '
                'nape, a brown knitted shawl round her shoulders, a tied cloth bundle on her left hip held in her left arm',
        'shawl_over_head': False, 'hair_style': 'low knot',
        'kind': 'woman', 'height': 1.60, 'build': 1.02, 'skirt': 'skirt brown', 'bodice': 'coat brown', 'shawl': 'shawl brown',
        'seed': 10, 'walker': True,
        'bundle': {'at': (-0.24, 0.05, 0.98), 'size': (0.40, 0.30, 0.30), 'turn': -10, 'cloth': 'bundle linen'},
        'pose': {
            'pelvis': (-0.02, 0, 0), 'pelvis_turn': (0, -3, -5), 'lean': (4, -3, 0), 'chest': (2, -2, 8), 'head': (4, 3, -4),
            'right_arm': {'wrist': (0.18, -0.15, 0.80), 'elbow': (0.3, -1, -0.2), 'hand': 'relaxed'},
            'left_arm': {'wrist': (-0.17, 0.20, 1.00), 'elbow': (-1, -0.5, -0.4), 'hand': 'hidden'},
            'right_foot': {'at': (0.07, -0.21), 'turn': 6, 'pitch': 24},
            'left_foot': {'at': (-0.07, 0.24), 'turn': 6, 'pitch': -10},
        },
    },
    'walker-woman-hand-bundle': {
        'what': 'small woman walking away in a long charcoal skirt with a brown-grey knitted shawl round her shoulders, '
                'her hair pinned up in a bun, a tied cloth bundle hanging from her right hand by its knot',
        'shawl_over_head': False, 'hair_style': 'bun',
        'kind': 'woman', 'height': 1.55, 'build': 0.97, 'skirt': 'skirt dark brown', 'bodice': 'coat charcoal', 'shawl': 'shawl grey brown',
        'seed': 11, 'walker': True,
        'bundle': {'hang_from': 'right', 'size': (0.32, 0.25, 0.27), 'turn': 5, 'cloth': 'bundle grey linen'},
        'pose': {
            'pelvis_turn': (0, 3, 4), 'lean': (5, 3, 0), 'chest': (2, 2, -6), 'head': (5, 0, 0),
            'right_arm': {'wrist': (0.23, 0.02, 0.82), 'elbow': (0.4, -1, 0), 'hand': 'grip', 'hand_direction': (0, 0.2, -1),
                          'hand_back': (1, 0, 0)},
            'left_arm': {'wrist': (-0.16, 0.17, 0.80), 'elbow': (-0.3, -1, -0.4), 'hand': 'relaxed'},
            'right_foot': {'at': (0.07, 0.24), 'turn': 6, 'pitch': -10},
            'left_foot': {'at': (-0.07, -0.22), 'turn': 6, 'pitch': 26},
        },
    },
}

# the cloth: (Poly Haven surface, its colour in linear light, how many metres one picture covers). Dull
# browns and greys, nothing bright and no party or uniform colours
CLOTHS = {
    'coat brown': ('caban', (0.118, 0.085, 0.062)),
    'coat grey': ('caban', (0.128, 0.126, 0.118)),
    'coat grey brown': ('caban', (0.118, 0.105, 0.088)),
    'coat charcoal': ('caban', (0.068, 0.067, 0.066)),
    'coat olive tweed': ('poly_wool_herringbone', (0.112, 0.100, 0.068)),
    'coat fawn tweed': ('poly_wool_herringbone', (0.175, 0.140, 0.098)),
    'cap grey tweed': ('poly_wool_herringbone', (0.115, 0.112, 0.105)),
    'cap brown tweed': ('poly_wool_herringbone', (0.120, 0.090, 0.064)),
    'cap dark tweed': ('poly_wool_herringbone', (0.062, 0.058, 0.052)),
    'trousers dark corduroy': ('ribbed_corduroy', (0.060, 0.055, 0.050)),
    'trousers brown corduroy': ('ribbed_corduroy', (0.100, 0.075, 0.055)),
    'boot leather': ('fabric_leather_02', (0.030, 0.024, 0.020)),
    'bag leather': ('fabric_leather_02', (0.090, 0.060, 0.040)),
    'muffler oatmeal': ('knitted_fleece', (0.230, 0.200, 0.160)),
    'muffler grey brown': ('knitted_fleece', (0.105, 0.095, 0.085)),
    'skirt charcoal': ('caban', (0.055, 0.053, 0.052)),
    'skirt brown': ('caban', (0.095, 0.068, 0.050)),
    'skirt dark brown': ('caban', (0.065, 0.048, 0.038)),
    'shawl grey': ('knitted_fleece', (0.140, 0.136, 0.128)),
    'shawl brown': ('knitted_fleece', (0.125, 0.092, 0.066)),
    'shawl grey brown': ('knitted_fleece', (0.110, 0.100, 0.088)),
    'bundle linen': ('rough_linen', (0.230, 0.205, 0.165)),
    'bundle grey linen': ('rough_linen', (0.160, 0.155, 0.145)),
}
CLOTH_TILE_METRES = 1.1   # each cloth picture holds 4 x 4 copies of the surface (0.27 m each)
SKIN = (0.17, 0.105, 0.075)   # weathered skin at dusk: 0.30 came out pale grey-white against the dark coats, like masks
SKIN_ROUGHNESS, SKIN_SHINE = 0.8, 0.3   # a little shine only: at 0.6 and the usual 0.5 the lamps made faces and necks glow
HAIR = (0.040, 0.032, 0.027)   # dark brown, darker than every coat (the darkest, charcoal, is 0.068)
# hair is matt: with the usual shine (roughness 0.75, specular 0.5) the dark hair mirrored the dusk sky and the street
# lamps and came out paler than the coats, so from behind the heads read as bald (round 1's plate)
HAIR_ROUGHNESS, HAIR_SHINE = 1.0, 0.05


# ------------------------------------------------------------------------------------ materials

def cloth_picture(cloth_name):
    """The cloth's picture: the Poly Haven surface shrunk to a quarter, repeated 4 x 4 (so one picture covers
    1.1 m and the weave keeps its real size), its colour pulled toward the cloth's own and mottled a little at
    the scale of a hand (wear and dust), so it doesn't read as plastic. Saved as a JPEG in the scratch folder,
    so glTF carries it inside the figure."""
    surface, colour = CLOTHS[cloth_name]
    # the file name carries a fingerprint of the surface and the colour, so a changed colour paints a new picture
    # instead of reusing the old one from the scratch folder
    fingerprint = zlib.crc32(repr((surface, tuple(round(v, 4) for v in colour))).encode())
    path = os.path.join(CLOTH_PICTURES, f"{cloth_name.replace(' ', '-')}-{fingerprint:08x}.jpg")
    if not os.path.exists(path):
        source = bpy.data.images.load(os.path.join(SURFACES, surface, 'Diffuse.jpg'), check_existing=True)
        width, height = source.size
        pixels = numpy.empty(width * height * 4, numpy.float32)
        source.pixels.foreach_get(pixels)
        side = min(width, height) // 4 * 4   # some surfaces are a few pixels short of square (1024 x 1021)
        pixels = pixels.reshape(height, width, 4)[:side, :side, :3]
        quarter = pixels.reshape(side // 4, 4, side // 4, 4, 3).mean(axis=(1, 3))
        grey = quarter.mean(axis=2, keepdims=True)
        weave = 0.35 * quarter + 0.65 * grey          # mostly the weave's light and dark, a little of its colour
        weave = weave / weave.mean(axis=(0, 1))       # average 1
        tiled = numpy.tile(weave, (4, 4, 1))
        size = tiled.shape[0]
        # mottling: a few slow waves that repeat exactly across the picture, so its copies join without a seam; seeded
        # from the cloth's name with zlib.crc32 (Python's hash() of a text changes on every run)
        random = numpy.random.default_rng(zlib.crc32(cloth_name.encode()))
        y, x = numpy.mgrid[0:size, 0:size] / size
        mottle = numpy.zeros((size, size), numpy.float32)
        for _ in range(7):
            waves_across, waves_down = random.integers(1, 5), random.integers(-4, 5)
            mottle += random.uniform(0.3, 1.0) * numpy.sin(2 * math.pi * (waves_across * x + waves_down * y) + random.uniform(0, 2 * math.pi))
        mottle = 1 + 0.10 * mottle / numpy.abs(mottle).max()
        result = numpy.clip(tiled * mottle[:, :, None] * numpy.array(colour, numpy.float32), 0, 1)
        save_picture(cloth_name, result, path)
    return load_picture(path)


def save_picture(name, colours, path):
    """Saves a square picture (rows of linear-light colours) as a JPEG in the scratch folder."""
    size = colours.shape[0]
    image = bpy.data.images.new(name, size, size)
    flat = numpy.ones((size, size, 4), numpy.float32)
    flat[:, :, :3] = colours
    image.pixels.foreach_set(flat.ravel())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.filepath_raw = path
    image.file_format = 'JPEG'
    image.save()
    bpy.data.images.remove(image)


def load_picture(path):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'Non-Color'   # the numbers in it are already linear light
    return image


def hair_picture():
    """Close-cut hair combed down: fine streaks running down the head (the hair shell's pictures run from its
    bottom to its top), each a little lighter or darker, so the head reads as hair, not as a smooth dark scalp.
    Seeded with zlib.crc32, so every run paints the same picture."""
    fingerprint = zlib.crc32(repr(tuple(round(v, 4) for v in HAIR)).encode())
    path = os.path.join(CLOTH_PICTURES, f'hair-{fingerprint:08x}.jpg')
    if not os.path.exists(path):
        size = 256
        random = numpy.random.default_rng(zlib.crc32(b'hair'))
        strands = random.uniform(0.6, 1.4, size)                     # one brightness for each strand across the picture
        strands = numpy.convolve(numpy.concatenate([strands[-2:], strands, strands[:2]]), numpy.ones(3) / 3, 'valid')[:size]
        along = 1 + 0.15 * random.standard_normal((size, size))      # a little unevenness down each strand
        along = (along + numpy.roll(along, 1, axis=0) + numpy.roll(along, 2, axis=0)) / 3
        brightness = strands[None, :] * along
        save_picture('hair', numpy.clip(brightness[:, :, None] * numpy.array(HAIR, numpy.float32), 0, 1), path)
    return load_picture(path)


def cloth_material(cloth_name):
    """A material wearing the cloth's picture, rough. (A wool sheen was tried: under the street's wide dusk sky it
    turned the dark coats pale grey, like statues.)"""
    if cloth_name in bpy.data.materials:
        return bpy.data.materials[cloth_name]
    material = bpy.data.materials.new(cloth_name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    picture = nodes.new('ShaderNodeTexImage')
    picture.image = cloth_picture(cloth_name)
    links.new(picture.outputs['Color'], shader.inputs['Base Color'])
    shiny = 'leather' in cloth_name
    shader.inputs['Roughness'].default_value = 0.55 if shiny else 0.92
    material['tile_metres'] = CLOTH_TILE_METRES
    return material


def plain_material(name, colour, roughness, shine=0.5):
    """One even colour. shine: how much it mirrors the sky and lamps (Blender's specular level; 0.5 is usual)."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*colour, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Specular IOR Level'].default_value = shine
    material['tile_metres'] = 1.0
    return material


def hair_material():
    """Dark matt hair wearing the streaked hair picture."""
    if 'dark hair' in bpy.data.materials:
        return bpy.data.materials['dark hair']
    material = bpy.data.materials.new('dark hair')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    picture = nodes.new('ShaderNodeTexImage')
    picture.image = hair_picture()
    links.new(picture.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = HAIR_ROUGHNESS
    shader.inputs['Specular IOR Level'].default_value = HAIR_SHINE
    material['tile_metres'] = 1.0
    return material


# ----------------------------------------------------------------------------------- geometry

def turn_matrix(forward=0.0, side=0.0, twist=0.0):
    """A turn of part of the body, in degrees: forward leans it toward +y (the way the figure faces), side
    leans it toward its right (+x), twist turns it to its left (about the upright)."""
    return (Matrix.Rotation(math.radians(twist), 3, 'Z') @ Matrix.Rotation(math.radians(side), 3, 'Y')
            @ Matrix.Rotation(math.radians(-forward), 3, 'X'))


def bend(start, end, first_length, second_length, pole):
    """Where an elbow or knee goes: the joint between two bones of these lengths reaching from start to end,
    bent toward the pole direction. If end is out of reach the limb straightens and end is pulled in;
    returns (joint, end)."""
    span = end - start
    along = span.normalized()
    distance = min(max(span.length, abs(first_length - second_length) + 0.01), (first_length + second_length) * 0.998)
    end = start + along * distance
    side = pole - along * pole.dot(along)
    if side.length < 1e-6:
        side = Vector((0, 0, -1)) - along * along.z
    side.normalize()
    cos_angle = (first_length ** 2 + distance ** 2 - second_length ** 2) / (2 * first_length * distance)
    angle = math.acos(max(-1.0, min(1.0, cos_angle)))
    return start + along * (first_length * math.cos(angle)) + side * (first_length * math.sin(angle)), end


def smooth_path(points, samples_per_span=5):
    """A smooth line through the points (Catmull-Rom), and for each of its points how far along the control
    points it is (0 at the first, 1 at the second, ...)."""
    extended = [points[0] * 2 - points[1]] + list(points) + [points[-1] * 2 - points[-2]]
    path, positions = [], []
    for i in range(len(points) - 1):
        before, start, end, after = extended[i:i + 4]
        for k in range(samples_per_span):
            t = k / samples_per_span
            path.append(0.5 * (2 * start + (end - before) * t + (2 * before - 5 * start + 4 * end - after) * t * t
                               + (3 * start - before - 3 * end + after) * t * t * t))
            positions.append(i + t)
    path.append(points[-1].copy())
    positions.append(len(points) - 1)
    return path, positions


def along_profile(profile, position):
    """A value at a place along the control points, from (position, value) pairs, straight lines between."""
    if position <= profile[0][0]:
        return profile[0][1]
    for (start, start_value), (end, end_value) in zip(profile, profile[1:]):
        if position <= end:
            return start_value + (end_value - start_value) * (position - start) / max(1e-9, end - start)
    return profile[-1][1]


def ring(centre, x_axis, y_axis, half_width, half_depth, exponent=2.0, count=24, offset=None):
    """A closed ring of points round centre in the plane of the two axes: an ellipse, or with a bigger
    exponent a rounded box (a coat's shoulders). It starts on +x_axis and runs toward +y_axis. offset(angle)
    pushes each point outward (cloth folds)."""
    points = []
    for k in range(count):
        angle = 2 * math.pi * k / count
        cosine, sine = math.cos(angle), math.sin(angle)
        x = half_width * math.copysign(abs(cosine) ** (2 / exponent), cosine)
        y = half_depth * math.copysign(abs(sine) ** (2 / exponent), sine)
        point = centre + x_axis * x + y_axis * y
        if offset:
            outward = (x_axis * cosine + y_axis * sine).normalized()
            point = point + outward * offset(angle)
        points.append(point)
    return points


def tube_rings(path, radii, count=16, squash=None):
    """Rings round a path (an arm, a leg), each square to the path, turned as little as possible from one
    to the next so the tube doesn't twist. squash: an (x, y) scale for each ring's two axes."""
    tangents = []
    for i in range(len(path)):
        before, after = path[max(0, i - 1)], path[min(len(path) - 1, i + 1)]
        tangents.append((after - before).normalized())
    seed = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
    normal = (seed - tangents[0] * seed.dot(tangents[0])).normalized()
    rings = []
    for point, tangent, radius in zip(path, tangents, radii):
        normal = (normal - tangent * normal.dot(tangent)).normalized()
        binormal = tangent.cross(normal)
        squash_one, squash_other = squash if squash else (1.0, 1.0)
        rings.append(ring(point, normal, binormal, radius * squash_one, radius * squash_other, count=count))
    return rings


def lofted_object(name, rings, material, close_start=False, close_end=False, subdivide=1, thickness=0.0,
                  closed_path=False, skip_face=None):
    """A smooth shell through the rings (each a list of points, all the same length), its texture
    coordinates in metres (round each ring, and along the rings). close_start / close_end cap the ends;
    closed_path joins the last ring back to the first (a muffler round the neck); skip_face(ring_index,
    point_index) leaves a face out (the face opening of a shawl); thickness gives the cloth an edge."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    tile = material.get('tile_metres', 1.0)
    count = len(rings[0])
    verts = [[bm.verts.new(p) for p in r] for r in rings]
    centres = [sum(r, Vector()) / len(r) for r in rings]
    along = [0.0]
    for i in range(1, len(rings)):
        along.append(along[-1] + (centres[i] - centres[i - 1]).length)
    round_distance = []
    for r in rings:
        distances = [0.0]
        for k in range(1, count + 1):
            distances.append(distances[-1] + (r[k % count] - r[k - 1]).length)
        round_distance.append(distances)
    spans = list(range(len(rings) - 1)) + ([len(rings) - 1] if closed_path else [])
    for i in spans:
        j = (i + 1) % len(rings)
        v_here, v_next = along[i], along[i] + (centres[j] - centres[i]).length
        for k in range(count):
            if skip_face and skip_face(i, k):
                continue
            k2 = (k + 1) % count
            face = bm.faces.new((verts[i][k], verts[i][k2], verts[j][k2], verts[j][k]))
            corners = ((round_distance[i][k], v_here), (round_distance[i][k + 1], v_here),
                       (round_distance[j][k + 1], v_next), (round_distance[j][k], v_next))
            for loop, (u, v) in zip(face.loops, corners):
                loop[uv_layer].uv = (u / tile, v / tile)
    for end, wanted, flip in ((0, close_start, True), (len(rings) - 1, close_end, False)):
        if not wanted:
            continue
        ends = verts[end][::-1] if flip else verts[end]
        cap = bm.faces.new(ends)
        for loop in cap.loops:
            loop[uv_layer].uv = (loop.vert.co.x / tile, loop.vert.co.y / tile)
        bmesh.ops.poke(bm, faces=[cap])
    if close_start and close_end:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish_object(name, bm, material, subdivide, thickness)


def ellipsoid_object(name, centre, half_sizes, rotation, material, segments=16, rings=10, subdivide=1, keep=None, thickness=0.0):
    """An egg shape (a head, an ear, a bundle). keep(x, y, z), given a point on the unit sphere, says
    whether it stays (a shell of hair with the face cut away). Its picture wraps once round it, from the
    bottom to the top."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0, calc_uvs=True)
    if keep:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co.x, v.co.y, v.co.z)], context='VERTS')
    for v in bm.verts:
        v.co = centre + rotation @ Vector((v.co.x * half_sizes[0], v.co.y * half_sizes[1], v.co.z * half_sizes[2]))
    return finish_object(name, bm, material, subdivide, thickness)


# far-off walkers are drawn with one less level of smoothing (a quarter of the triangles): at 40 to 60 m a
# figure is about 60 pixels tall, so it can't be seen; build_figure sets this for each figure
smoothing_dropped = 0


def finish_object(name, bm, material, subdivide, thickness):
    subdivide = max(0, subdivide - smoothing_dropped)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if subdivide:
        modifier = obj.modifiers.new('smooth', 'SUBSURF')
        modifier.levels = modifier.render_levels = subdivide
    if thickness:
        modifier = obj.modifiers.new('cloth edge', 'SOLIDIFY')
        modifier.thickness = thickness
        modifier.offset = -1.0
        modifier.use_even_offset = True
    return obj


# --------------------------------------------------------------------------------------- the pose

def solve_pose(figure):
    """Every joint of the figure, in metres, from its pose (see the top of FIGURES)."""
    scale = figure['height'] / STANDARD_HEIGHT
    pose = figure['pose']
    woman = figure['kind'] == 'woman'
    joints = {'scale': scale}
    # the feet: each boot stands where the pose says, maybe pitched up on its toes or back on its heel
    for side, sign in (('right', 1), ('left', -1)):
        foot = pose.get(f'{side}_foot', {})
        x, y = foot.get('at', (sign * 0.11, 0.0))
        pitch = foot.get('pitch', 0.0)
        pivot = Vector((0, (0.13 if pitch > 0 else -0.065) * scale, 0))   # the ball of the foot, or the heel
        placement = (Matrix.Translation(Vector((x * scale, y * scale, foot.get('lift', 0.0) * scale)))
                     @ Matrix.Rotation(math.radians(-sign * foot.get('turn', 8)), 4, 'Z')
                     @ Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-pitch), 4, 'X') @ Matrix.Translation(-pivot))
        joints[f'{side}_foot'] = placement
        joints[f'{side}_ankle'] = placement @ Vector((0, 0, ANKLE_HEIGHT * scale))
    # the hips: lowered if a leg can't otherwise reach its foot (a long stride, bent knees)
    pelvis_turn = turn_matrix(*pose.get('pelvis_turn', (0, 0, 0)))
    pelvis = Vector((0, 0, PELVIS_HEIGHT * scale)) + Vector(pose.get('pelvis', (0, 0, 0))) * scale
    leg = (THIGH + SHIN) * scale * 0.995
    for _ in range(2):
        for side, sign in (('right', 1), ('left', -1)):
            hip = pelvis + pelvis_turn @ (Vector((sign * HIP_SIDE, 0, -HIP_DROP)) * scale)
            ankle = joints[f'{side}_ankle']
            flat = (hip - ankle).to_2d().length
            highest = ankle.z + math.sqrt(max(0.0, leg ** 2 - flat ** 2))
            if hip.z > highest:
                pelvis.z -= hip.z - highest
    joints['pelvis'], joints['pelvis_turn'] = pelvis, pelvis_turn
    for side, sign in (('right', 1), ('left', -1)):
        hip = pelvis + pelvis_turn @ (Vector((sign * HIP_SIDE, 0, -HIP_DROP)) * scale)
        knee_pole = pelvis_turn @ Vector((sign * 0.18, 1, 0))
        knee, ankle = bend(hip, joints[f'{side}_ankle'], THIGH * scale, SHIN * scale, knee_pole)
        joints[f'{side}_hip'], joints[f'{side}_knee'], joints[f'{side}_ankle'] = hip, knee, ankle
    # the spine, the shoulders and the head
    lower = pelvis_turn @ turn_matrix(*pose.get('lean', (0, 0, 0)))
    waist = pelvis + lower @ (Vector((0, 0, WAIST_UP)) * scale)
    upper = lower @ turn_matrix(*pose.get('chest', (0, 0, 0)))
    chest = waist + upper @ (Vector((0, 0, CHEST_UP)) * scale)
    shoulder_side = (0.155 if woman else SHOULDER_SIDE) * (0.5 + 0.5 * figure.get('build', 1.0))
    for side, sign in (('right', 1), ('left', -1)):
        joints[f'{side}_shoulder'] = chest + upper @ (Vector((sign * shoulder_side, pose.get('shoulders_forward', 0.0),
                                                              SHOULDER_UP + pose.get('shrug', 0.0))) * scale)
    neck = chest + upper @ (Vector((0, NECK_BACK, NECK_UP + 0.6 * pose.get('shrug', 0.0))) * scale)
    head_turn = upper @ turn_matrix(*pose.get('head', (0, 0, 0)))
    head = neck + head_turn @ (Vector((0, HEAD_FORWARD, HEAD_UP)) * scale)
    joints.update({'lower': lower, 'waist': waist, 'upper': upper, 'chest': chest, 'neck': neck, 'head_turn': head_turn, 'head': head})
    # the arms
    for side, sign in (('right', 1), ('left', -1)):
        arm = pose.get(f'{side}_arm', {})
        wrist_wanted = Vector(arm.get('wrist', (sign * 0.21, 0.0, 0.84))) * scale
        pole = Vector(arm.get('elbow', (sign * 0.35, -1, -0.3)))
        elbow, wrist = bend(joints[f'{side}_shoulder'], wrist_wanted, UPPER_ARM * scale, FOREARM * scale, pole)
        joints[f'{side}_elbow'], joints[f'{side}_wrist'] = elbow, wrist
    return joints


def leg_point_at_height(joints, side, height):
    """Where a leg's middle line crosses a height (from the hip down), or its nearest end."""
    chain = [joints[f'{side}_hip'], joints[f'{side}_knee'], joints[f'{side}_ankle']]
    if height >= chain[0].z:
        return chain[0]
    for top, bottom in zip(chain, chain[1:]):
        if min(top.z, bottom.z) <= height <= max(top.z, bottom.z) and abs(top.z - bottom.z) > 1e-6:
            return top.lerp(bottom, (top.z - height) / (top.z - bottom.z))
    return chain[-1]


# ----------------------------------------------------------------------------------- the clothing

def folds(seed, amplitude, every=7, vent=0.0):
    """Cloth folds round a ring: a few uneven waves, each figure its own; vent: a crease this deep down the
    middle of the back (a coat's back vent, where its two halves overlap)."""
    phase_one, phase_two = seed * 1.7, seed * 2.9
    def offset(angle):
        from_back = (angle + math.pi / 2 + math.pi) % (2 * math.pi) - math.pi   # 0 at the middle of the back
        return (amplitude * (0.6 * math.sin(every * angle + phase_one) + 0.4 * math.sin((every + 4) * angle + phase_two))
                - vent * math.exp(-(from_back / 0.16) ** 2))
    return offset


def hanging_skirt_rings(joints, top_height, hem_height, top_size, hem_size, seed, fold_depth, count=32, steps=4, back=0.02, vent=0.0):
    """Rings for cloth that hangs straight down from top_height to its hem (a coat's skirt, a long skirt),
    each wide enough to hold both legs where they cross its height, folds deepening toward the hem."""
    scale = joints['scale']
    twist = joints['pelvis_turn']
    x_axis = (twist @ Vector((1, 0, 0))).to_3d()
    x_axis.z = 0
    x_axis.normalize()
    y_axis = Vector((0, 0, 1)).cross(x_axis)
    pelvis = joints['pelvis']
    rings = []
    for step in range(steps):
        share = step / (steps - 1)            # 0 at the hem, 1 at the top
        height = hem_height + (top_height - hem_height) * share
        right, left = leg_point_at_height(joints, 'right', height), leg_point_at_height(joints, 'left', height)
        # cloth hangs from the hips: its middle stays mostly under them, pulled only part way toward the legs
        # near the hem, and it widens to hold both legs wherever they are
        legs_middle = (right + left) / 2
        middle = Vector((pelvis.x, pelvis.y, height)).lerp(legs_middle, 0.45 * (1 - share))
        middle.z = height
        middle -= y_axis * back * scale
        leg_room = 0.095 * scale
        reach_x = max(abs((leg - middle).dot(x_axis)) for leg in (right, left)) + leg_room
        reach_y = max(abs((leg - middle).dot(y_axis)) for leg in (right, left)) + leg_room + 0.02 * scale
        half_width = max(top_size[0] + (hem_size[0] - top_size[0]) * (1 - share), reach_x)
        half_depth = max(top_size[1] + (hem_size[1] - top_size[1]) * (1 - share), reach_y)
        rings.append(ring(middle, x_axis, y_axis, half_width, half_depth, exponent=2.2, count=count,
                          offset=folds(seed, fold_depth * (1 - share) * scale, vent=vent * (1 - share) * scale)))
    return rings


def spine_ring(joints, frame_name, point, size, up=0.0, forward=0.0, exponent=2.4, count=32):
    """A ring round the body square to part of the spine (its turn), at a point lifted `up` along it."""
    frame = joints[frame_name]
    scale = joints['scale']
    centre = point + frame @ Vector((0, forward * scale, up * scale))
    return ring(centre, frame @ Vector((1, 0, 0)), frame @ Vector((0, 1, 0)), size[0] * scale, size[1] * scale, exponent, count)


def build_coat(figure, joints, cloth):
    """The coat (or a short jacket): its skirt hangs from the seat round the legs; above, rings follow the
    spine up to the shoulders, which slope from a turned-up collar (or a collar folded down under a muffler)."""
    build = figure.get('build', 1.0)
    width = lambda w, d: (w * build, d * build)
    seed = figure['seed']
    pelvis, waist, chest, neck = joints['pelvis'], joints['waist'], joints['chest'], joints['neck']
    scale = joints['scale']
    hem = figure['coat'][1] * scale
    seat = pelvis.z - 0.10 * scale
    rings = hanging_skirt_rings(joints, seat, hem, width(0.200 * scale, 0.148 * scale), width(0.236 * scale, 0.176 * scale),
                                seed, 0.019, steps=4 if hem < 0.6 * scale else 2, vent=0.010)
    shrug = figure['pose'].get('shrug', 0.0)
    rings += [
        spine_ring(joints, 'pelvis_turn', pelvis, width(0.196, 0.140)),
        spine_ring(joints, 'lower', waist, width(0.176, 0.128), forward=0.004),            # a little fitted at the waist
        spine_ring(joints, 'upper', chest, width(0.192, 0.138), forward=0.006),
        spine_ring(joints, 'upper', chest, width(0.192, 0.128), up=0.070, forward=0.004),  # under the arms
        # the shoulders: from the seam just inside the arm, sloping up to the neck (the sleeve's cap is the
        # rounded top of the arm, a little lower than the neck)
        spine_ring(joints, 'upper', chest, width(0.180, 0.104), up=SHOULDER_UP + 0.030 + shrug, exponent=2.6),
        spine_ring(joints, 'upper', neck, width(0.112, 0.082), up=-0.016 + 0.4 * shrug, exponent=2.4),
    ]
    if figure['collar'] == 'up':   # stood up round the back of the neck, a little flared, up to the hair at the nape
        rings += [spine_ring(joints, 'upper', neck, (0.080, 0.080), up=0.010, forward=0.006),
                  spine_ring(joints, 'upper', neck, (0.087, 0.089), up=0.074, forward=0.002)]
    else:                          # folded down: a wide, low collar for a muffler to sit in
        rings += [spine_ring(joints, 'upper', neck, (0.086, 0.084), up=0.004, forward=0.008),
                  spine_ring(joints, 'upper', neck, (0.100, 0.097), up=0.024, forward=0.010)]
    coat = lofted_object(f"{figure['name']}-coat", rings, cloth, subdivide=2, thickness=0.012 * scale)
    parts = [coat]
    # a half belt across the back at the waist, with a button at each end: it reads from behind
    frame = joints['lower']
    centre = waist + frame @ Vector((0, 0.004 * scale, -0.01 * scale))
    half_width, half_depth = 0.176 * build * scale, 0.128 * build * scale
    path = []
    for k in range(9):
        angle = math.radians(-90 - 46 + 92 * k / 8)
        cosine, sine = math.cos(angle), math.sin(angle)
        x = half_width * math.copysign(abs(cosine) ** (2 / 2.4), cosine)
        y = half_depth * math.copysign(abs(sine) ** (2 / 2.4), sine)
        outward = (frame @ Vector((cosine, sine, 0))).normalized()
        path.append(centre + frame @ Vector((x, y, 0)) + outward * 0.011 * scale)
    up = frame @ Vector((0, 0, 1))
    belt_rings = []
    for i, point in enumerate(path):
        tangent = (path[min(i + 1, 8)] - path[max(i - 1, 0)]).normalized()
        outward = tangent.cross(up).normalized()
        belt_rings.append([point + up * 0.026 * scale + outward * 0.005, point + up * 0.026 * scale - outward * 0.006,
                           point - up * 0.026 * scale - outward * 0.006, point - up * 0.026 * scale + outward * 0.005])
    parts.append(lofted_object(f"{figure['name']}-belt", belt_rings, cloth, close_start=True, close_end=True, subdivide=1))
    for end in (path[1], path[-2]):
        parts.append(ellipsoid_object(f"{figure['name']}-button", end + (end - centre).normalized() * 0.006,
                                      (0.011 * scale, 0.011 * scale, 0.011 * scale), Matrix.Identity(3),
                                      plain_material('coat button', (0.025, 0.022, 0.02), 0.5), segments=8, rings=6))
    return parts


def build_bodice_and_skirt(figure, joints, skirt_cloth, bodice_cloth):
    """A woman's long skirt, hanging from her waist to her ankles round her legs, and her bodice above."""
    seed = figure['seed']
    scale = joints['scale']
    build = figure.get('build', 1.0)
    pelvis, waist, chest, neck = joints['pelvis'], joints['waist'], joints['chest'], joints['neck']
    rings = hanging_skirt_rings(joints, pelvis.z - 0.04 * scale, 0.055 * scale, (0.190 * build * scale, 0.155 * build * scale),
                                (0.255 * scale, 0.235 * scale), seed, 0.016, steps=5, back=0.03)
    rings += [spine_ring(joints, 'lower', waist, (0.140 * build, 0.110 * build), up=-0.03)]
    skirt = lofted_object(f"{figure['name']}-skirt", rings, skirt_cloth, subdivide=2, thickness=0.010 * scale)
    bodice = lofted_object(f"{figure['name']}-bodice", [
        spine_ring(joints, 'lower', waist, (0.136 * build, 0.106 * build), up=-0.05),
        spine_ring(joints, 'upper', chest, (0.160 * build, 0.122 * build)),
        spine_ring(joints, 'upper', chest, (0.166 * build, 0.116 * build), up=0.08),
        spine_ring(joints, 'upper', chest, (0.170 * build, 0.096 * build), up=SHOULDER_UP + 0.03, exponent=3.0),
        spine_ring(joints, 'upper', neck, (0.105, 0.080), up=-0.02),
        spine_ring(joints, 'upper', neck, (0.062, 0.062), up=0.03),
    ], bodice_cloth, subdivide=2)
    return [skirt, bodice]


def build_shawl(figure, joints, cloth):
    """A knitted shawl over the head and shoulders, hanging over the upper arms and down the back to a point
    at the waist, open round the face: the outline of a working woman of the time seen from behind."""
    scale = joints['scale']
    head, head_turn, chest, upper = joints['head'], joints['head_turn'], joints['chest'], joints['upper']
    build = figure.get('build', 1.0)
    count = 32

    def head_ring(height, half_width, half_depth, forward=0.0):
        centre = head + head_turn @ (Vector((0, forward, height)) * scale)
        return ring(centre, head_turn @ Vector((1, 0, 0)), head_turn @ Vector((0, 1, 0)), half_width * scale, half_depth * scale, 2.0, count)

    def body_ring(up, half_width, half_depth, drop_at_back=0.0, forward=0.0):
        centre = chest + upper @ (Vector((0, forward, up)) * scale)
        drop = lambda angle: -drop_at_back * scale * max(0.0, -math.sin(angle)) ** 1.6
        points = ring(centre, upper @ Vector((1, 0, 0)), upper @ Vector((0, 1, 0)), half_width * build * scale, half_depth * build * scale, 2.2, count)
        return [p + upper @ Vector((0, 0, drop(2 * math.pi * k / count))) for k, p in enumerate(points)]

    rings = [
        body_ring(-0.21, 0.236, 0.170, drop_at_back=0.13, forward=0.014),   # the lower edge, down to the waist at the sides and
        body_ring(-0.07, 0.234, 0.164, drop_at_back=0.03, forward=0.010),   # falling to a point at the back
        body_ring(SHOULDER_UP - 0.02, 0.222, 0.140, forward=0.004),         # over the arms' tops
        body_ring(SHOULDER_UP + 0.045, 0.165, 0.118),                       # sloping in to the neck
    ]
    if figure.get('shawl_over_head', True):
        rings += [head_ring(-0.085, 0.094, 0.110, 0.004), head_ring(-0.010, 0.093, 0.116), head_ring(0.072, 0.084, 0.106),
                  head_ring(0.108, 0.060, 0.074, -0.004)]
        # the face opening: the front of the rings round the head (and the neck below it) left out
        front = lambda k: abs(2 * math.pi * k / count - math.pi / 2) < math.radians(52)
        skip = lambda i, k: 4 <= i <= 6 and front(k) or (i == 3 and abs(2 * math.pi * k / count - math.pi / 2) < math.radians(34))
        close_top = True
    else:   # round the shoulders, closed at the throat and drawn up round the nape, under her pinned-up hair
        rings += [body_ring(NECK_UP + 0.052, 0.078, 0.076)]
        skip, close_top = None, False
    return [lofted_object(f"{figure['name']}-shawl", rings, cloth, close_end=close_top, subdivide=2, thickness=0.012 * scale, skip_face=skip)]


def build_sleeves(figure, joints, cloth, woman=False):
    """Each sleeve: a tube from inside the shoulder, over the shoulder's cap, bending at the elbow (where the
    cloth bunches a little) to a cuff at the wrist."""
    scale = joints['scale']
    build = figure.get('build', 1.0)
    parts = []
    thin = 0.82 if woman else 1.0
    for side, sign in (('right', 1), ('left', -1)):
        shoulder, elbow, wrist = joints[f'{side}_shoulder'], joints[f'{side}_elbow'], joints[f'{side}_wrist']
        inside = shoulder + joints['upper'] @ (Vector((-sign * 0.065, 0, -0.045)) * scale)
        path, positions = smooth_path([inside, shoulder, elbow, wrist], samples_per_span=6)
        profile = [(0, 0.050), (1, 0.061), (1.5, 0.057), (2, 0.052), (2.4, 0.050), (2.85, 0.050), (3, 0.054)]
        radii = []
        for position in positions:
            bunching = 1 + 0.06 * math.sin(position * 19.0) if 1.85 < position < 2.6 else 1.0
            radii.append(along_profile(profile, position) * scale * build * thin * bunching)
        parts.append(lofted_object(f"{figure['name']}-sleeve-{side}", tube_rings(path, radii, count=16), cloth,
                                   close_start=True, close_end=True, subdivide=1))
    return parts


def build_legs_and_boots(figure, joints, trouser_cloth, boot_cloth, woman=False):
    """Trouser legs from inside the coat down over the knee to the boot tops, a little baggy at the bottom;
    the boots: a D-shaped loft along each foot (flat sole, rounded toe, heel) with a short shaft round the ankle."""
    scale = joints['scale']
    parts = []
    thin = 0.80 if woman else 1.0
    for side, sign in (('right', 1), ('left', -1)):
        hip, knee, ankle = joints[f'{side}_hip'], joints[f'{side}_knee'], joints[f'{side}_ankle']
        foot = joints[f'{side}_foot']
        boot_top = foot @ Vector((0, -0.012 * scale, 0.105 * scale))
        top = hip + joints['pelvis_turn'] @ (Vector((-sign * 0.02, 0, 0.06)) * scale)
        path, positions = smooth_path([top, hip, knee, boot_top], samples_per_span=6)
        profile = [(0, 0.092), (1, 0.090), (1.5, 0.076), (2, 0.064), (2.4, 0.061), (2.8, 0.058), (3, 0.063)]
        radii = []
        for position in positions:
            bagging = 1 + 0.07 * math.sin(position * 23.0) if position > 2.7 else 1.0
            radii.append(along_profile(profile, position) * scale * thin * bagging)
        if not woman:
            parts.append(lofted_object(f"{figure['name']}-trousers-{side}", tube_rings(path, radii, count=16), trouser_cloth,
                                       close_start=True, close_end=True, subdivide=1))
        else:   # dark stockings under the long skirt
            parts.append(lofted_object(f"{figure['name']}-leg-{side}", tube_rings(path, [r * 0.8 for r in radii], count=12),
                                       trouser_cloth, close_start=True, close_end=True, subdivide=1))
        # the boot: stations along the foot (where along, half its width, its top's height)
        stations = [(-0.078, 0.020, 0.040), (-0.070, 0.034, 0.080), (-0.045, 0.041, 0.100), (0.015, 0.044, 0.096),
                    (0.075, 0.047, 0.074), (0.135, 0.049, 0.060), (0.180, 0.044, 0.052), (0.207, 0.031, 0.044), (0.222, 0.012, 0.034)]
        boot_size = 0.93 if woman else 1.0
        rings = []
        for along, half_width, top_height in stations:
            points = []
            for k in range(16):
                angle = 2 * math.pi * k / 16
                cosine, sine = math.cos(angle), math.sin(angle)
                height = top_height * abs(sine) ** 0.8 if sine > 0 else 0.004 * abs(sine)
                points.append(foot @ (Vector((-half_width * cosine, along, height)) * scale * boot_size))
            rings.append(points)
        parts.append(lofted_object(f"{figure['name']}-boot-{side}", rings, boot_cloth, close_start=True, close_end=True, subdivide=1))
        shaft_path = [foot @ (Vector((0, -0.012, 0.03)) * scale * boot_size), foot @ (Vector((0, -0.012, 0.14)) * scale * boot_size)]
        shaft_path, _ = smooth_path(shaft_path, samples_per_span=3)
        parts.append(lofted_object(f"{figure['name']}-boot-shaft-{side}", tube_rings(shaft_path, [0.047 * scale * boot_size] * len(shaft_path), count=12),
                                   boot_cloth, close_start=True, close_end=True, subdivide=1))
    return parts


def build_hands(figure, joints, skin):
    """Hands as simple mitts: a palm widening to the knuckles, the fingers together and curled toward the
    palm (a little when relaxed or warming, right round when gripping), and a thumb."""
    scale = joints['scale'] * (0.92 if figure['kind'] == 'woman' else 1.0)
    parts = []
    for side, sign in (('right', 1), ('left', -1)):
        arm = figure['pose'].get(f'{side}_arm', {})
        kind = arm.get('hand', 'relaxed')
        if kind == 'hidden':
            continue
        wrist, elbow = joints[f'{side}_wrist'], joints[f'{side}_elbow']
        direction = Vector(arm['hand_direction']).normalized() if 'hand_direction' in arm else (wrist - elbow).normalized()
        back = Vector(arm['hand_back']) if 'hand_back' in arm else Vector((sign, 0, 0))
        back = (back - direction * back.dot(direction)).normalized()
        across = direction.cross(back)
        curl = {'relaxed': 0.8, 'grip': 1.9, 'warming': 0.25}[kind]
        rings = []
        for along, half_width, half_thickness in ((-0.035, 0.026, 0.019), (0.0, 0.029, 0.020), (0.045, 0.039, 0.021), (0.085, 0.043, 0.019),
                                                  (0.120, 0.040, 0.016), (0.150, 0.033, 0.012), (0.168, 0.018, 0.008)):
            bent = max(0.0, along - 0.075)
            centre = wrist + direction * (along * scale * (1 - 0.25 * curl * bent / 0.1)) - back * (curl * 7.5 * bent * bent * scale)
            rings.append(ring(centre, across, back, half_width * scale, half_thickness * scale, count=12))
        parts.append(lofted_object(f"{figure['name']}-hand-{side}", rings, skin, close_start=True, close_end=True, subdivide=1))
        thumb_side = -across if side == 'right' else across
        thumb_path = [wrist + direction * 0.02 * scale + thumb_side * 0.022 * scale - back * 0.008 * scale,
                      wrist + direction * 0.05 * scale + thumb_side * 0.038 * scale - back * 0.018 * scale,
                      wrist + direction * (0.08 - 0.02 * curl) * scale + thumb_side * (0.040 - 0.012 * curl) * scale - back * (0.026 + 0.01 * curl) * scale]
        path, _ = smooth_path(thumb_path, samples_per_span=3)
        parts.append(lofted_object(f"{figure['name']}-thumb-{side}", tube_rings(path, [0.012 * scale] * (len(path) - 1) + [0.009 * scale], count=8),
                                   skin, close_start=True, close_end=True, subdivide=1))
    return parts


def hair_bottom(forward, back=-0.95, sides=-0.35):
    """How low the hair comes on the head's egg (-1 its bottom, 1 its top) at a place round it (forward: -1 the
    middle of the back, 0 the sides, 1 the face): down to the nape at the back (`back`, inside the collar), to
    below the ears at the sides (`sides`), rising toward the temples."""
    if forward < 0:
        return sides + (back - sides) * min(1.0, -forward / 0.6)
    return sides + 1.25 * forward


def build_head(figure, joints, skin, hair, cap_cloth):
    """The head (an egg with a jaw, a nose and ears that stand out a little), dark hair over its back and
    sides from under the cap down into the collar, the neck, a flat cap (a band seated low, just over the
    ears, a full flat crown that overhangs it, pulled forward to a short peak) and, for some, a knitted
    muffler worn high round the neck. A woman's head is bare, her hair pinned up."""
    scale = joints['scale'] * (0.95 if figure['kind'] == 'woman' else 1.0)
    head, turn, neck = joints['head'], joints['head_turn'], joints['neck']
    name = figure['name']
    head_half_width, head_half_depth, head_half_height = (v * scale for v in HEAD_HALF_SIZE)
    head_half_sizes = (head_half_width, head_half_depth, head_half_height)
    # the hair's cut edge is stepped until smoothed: a walker (drawn with one level of smoothing less) keeps one level
    hair_smoothing = 2 if figure.get('walker') else 1
    parts = [ellipsoid_object(f'{name}-head', head, head_half_sizes, turn, skin, segments=20, rings=14)]
    parts.append(ellipsoid_object(f'{name}-jaw', head + turn @ (Vector((0, 0.030, -0.070)) * scale), (0.060 * scale, 0.062 * scale, 0.048 * scale), turn, skin))
    parts.append(ellipsoid_object(f'{name}-nose', head + turn @ (Vector((0, 0.097, -0.012)) * scale), (0.011 * scale, 0.020 * scale, 0.026 * scale), turn, skin,
                                  segments=8, rings=6))
    for sign in (1, -1):
        ear_turn = turn @ Matrix.Rotation(math.radians(-sign * 18), 3, 'Z')
        # about 5.5 cm tall and 3 cm across, close to the head: bigger, or standing out against the dark hair, lit by
        # a fire they read as pale headphones in the plate
        parts.append(ellipsoid_object(f'{name}-ear', head + turn @ (Vector((sign * 0.073, -0.010, -0.010)) * scale),
                                      (0.009 * scale, 0.016 * scale, 0.027 * scale), ear_turn, skin, segments=10, rings=8))
    # the neck, from inside the collar up into the head
    neck_path, _ = smooth_path([neck - joints['upper'] @ (Vector((0, 0, 0.05)) * scale), neck + (head - neck) * 0.75], samples_per_span=4)
    parts.append(lofted_object(f'{name}-neck', tube_rings(neck_path, [0.052 * scale] * len(neck_path), count=12), skin,
                               close_start=True, close_end=True, subdivide=1))
    if figure['kind'] == 'woman':
        if not figure.get('shawl_over_head', True):   # bare-headed, her hair pinned up: a bun high at the back or a low knot
            parts.append(ellipsoid_object(f'{name}-hair', head, tuple(v * 1.05 for v in head_half_sizes), turn, hair, segments=28, rings=18,
                                          subdivide=hair_smoothing, keep=lambda x, y, z: hair_bottom(y, -0.88, -0.30) < z and not (y > 0.45 and z < 0.62)))
            knot_low = figure.get('hair_style') == 'low knot'
            parts.append(ellipsoid_object(f'{name}-hair-bun', head + turn @ (Vector((0, -0.092, -0.040 if knot_low else 0.045)) * scale),
                                          tuple(v * scale for v in ((0.050, 0.034, 0.036) if knot_low else (0.046, 0.036, 0.042))),
                                          turn, hair, segments=12, rings=8))
        return parts   # otherwise the shawl covers her head
    # short hair: a shell over the back and sides of the head, cut away over the face, down into the collar at the
    # back. Above the cap's band it is left out (the cap hides it there, and it could poke through the crown)
    parts.append(ellipsoid_object(f'{name}-hair', head, (head_half_width * 1.05, head_half_depth * 1.045, head_half_height * 1.03), turn, hair,
                                  segments=28, rings=18, subdivide=hair_smoothing,
                                  keep=lambda x, y, z: hair_bottom(y) < z < 0.72 and not (y > 0.25 and z < 0.55)))
    # the flat cap, in the head's own frame, seated low (its band about 1.5 cm lower than in round 1, just over the
    # tops of the ears): its crown is pulled forward and down onto the peak, high at the back and low at the front,
    # with no band showing in front (a level crown above a band read as a railway or police cap in the plate)
    cap_turn = turn @ Matrix.Rotation(math.radians(-5), 3, 'X')
    cap_centre = head + turn @ (Vector((0, 0.008, -0.014)) * scale)

    def cap_ring(height, half_width, half_depth, forward=0.0, exponent=2.0, slope=0.0):
        sloped = cap_turn @ Matrix.Rotation(math.radians(-slope), 3, 'X')   # its front tipped down by `slope` degrees
        return ring(cap_centre + cap_turn @ (Vector((0, forward, height)) * scale), sloped @ Vector((1, 0, 0)), sloped @ Vector((0, 1, 0)),
                    half_width * scale, half_depth * scale, exponent, 28)
    # the band a little wider than before, as it sits lower round the hair; the crown's top as high as before, so the
    # head never shows through it
    crown = [cap_ring(0.028, 0.086, 0.108, -0.002), cap_ring(0.050, 0.093, 0.116, 0.004, slope=6),
             cap_ring(0.090, 0.101, 0.132, 0.026, 2.2, slope=15), cap_ring(0.124, 0.091, 0.122, 0.030, 2.2, slope=15),
             cap_ring(0.142, 0.054, 0.072, 0.022, slope=12)]
    parts.append(lofted_object(f'{name}-cap', crown, cap_cloth, close_start=True, close_end=True, subdivide=2))
    # its peak: a short stiff brim round the front half of the band, sloping down
    inner, outer = [], []
    for k in range(11):
        angle = math.radians(25 + 130 * k / 10)
        across, ahead = math.cos(angle), math.sin(angle)
        reach = 0.012 + 0.048 * ahead ** 1.5
        inner.append(cap_centre + cap_turn @ (Vector((0.084 * across, 0.106 * ahead, 0.030)) * scale))
        outer.append(cap_centre + cap_turn @ (Vector(((0.084 + reach * 0.6) * across, (0.106 + reach) * ahead, 0.030 - 0.45 * reach)) * scale))
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    inner_verts = [bm.verts.new(p) for p in inner]
    outer_verts = [bm.verts.new(p) for p in outer]
    for k in range(10):
        face = bm.faces.new((inner_verts[k], outer_verts[k], outer_verts[k + 1], inner_verts[k + 1]))
        for loop in face.loops:
            loop[uv_layer].uv = (loop.vert.co.x, loop.vert.co.y)
    parts.append(finish_object(f'{name}-cap-peak', bm, cap_cloth, 1, 0.007 * scale))
    if figure.get('muffler'):
        # worn high at the back, up to the hair at the nape, so no neck shows from behind; lower in front, under the chin
        material = cloth_material(figure['muffler'])
        upper = joints['upper']
        path = [neck + upper @ (Vector((0.076 * math.cos(angle), 0.072 * math.sin(angle) + 0.008, 0.040 - 0.014 * math.sin(angle))) * scale)
                for angle in (2 * math.pi * k / 24 for k in range(24))]
        rings = tube_rings(path + path[:1], [0.033 * scale] * 25, count=12, squash=(1.0, 0.8))[:-1]
        parts.append(lofted_object(f'{name}-muffler', rings, material, closed_path=True, subdivide=1))
    return parts


def build_bundle(figure, joints):
    """A cloth bundle tied at the top (an egg of cloth with two knotted ends), on a shoulder, a hip or hanging
    from a hand by its knot."""
    bundle = figure['bundle']
    scale = joints['scale']
    material = cloth_material(bundle['cloth'])
    width, depth, height = (v * scale for v in bundle['size'])
    if bundle.get('hang_from'):
        wrist = joints[f"{bundle['hang_from']}_wrist"]
        centre = wrist - Vector((0, 0, 0.05 * scale + height / 2))
    else:
        centre = Vector(bundle['at']) * scale
    turn = Matrix.Rotation(math.radians(bundle.get('turn', 0)), 3, 'Z')
    name = figure['name']
    parts = [ellipsoid_object(f'{name}-bundle', centre, (width / 2, depth / 2, height / 2), turn, material, segments=16, rings=10)]
    for sign in (1, -1):
        knot_turn = turn @ Matrix.Rotation(math.radians(sign * 35), 3, 'Y')
        parts.append(ellipsoid_object(f'{name}-bundle-knot', centre + turn @ Vector((sign * 0.03 * scale, 0, height / 2 + 0.018 * scale)),
                                      (0.016 * scale, 0.013 * scale, 0.032 * scale), knot_turn, material, segments=8, rings=6))
    return parts


def build_bag(figure, joints):
    """A leather bag hanging from the hand: a rounded box, wider at the bottom, its top gathered under the grip."""
    bag = figure['bag']
    scale = joints['scale']
    material = cloth_material(bag['cloth'])
    width, depth, height = (v * scale for v in bag['size'])
    wrist = joints['right_wrist']
    top = wrist - Vector((0, 0, 0.06 * scale))
    rings = []
    for share, w, d in ((0.0, 0.85, 0.85), (0.12, 1.0, 1.0), (0.7, 0.96, 0.9), (1.0, 0.8, 0.35)):
        rings.append(ring(top - Vector((0, 0, height * (1 - share))), Vector((0, 1, 0)), Vector((-1, 0, 0)), width / 2 * w, depth / 2 * d, 3.5, 20))
    return [lofted_object(f"{figure['name']}-bag", rings, material, close_start=True, close_end=True, subdivide=1)]


# --------------------------------------------------------------------------------------- building

def build_figure(name):
    global smoothing_dropped
    figure = dict(FIGURES[name], name=name)
    smoothing_dropped = 1 if figure.get('walker') else 0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    joints = solve_pose(figure)
    skin = plain_material('weathered skin', SKIN, SKIN_ROUGHNESS, SKIN_SHINE)
    hair = hair_material()
    boots = cloth_material('boot leather')
    parts = []
    if figure['kind'] == 'man':
        coat = cloth_material(figure['coat'][0])
        parts += build_coat(figure, joints, coat)
        parts += build_sleeves(figure, joints, coat)
        parts += build_legs_and_boots(figure, joints, cloth_material(figure['trousers']), boots)
        parts += build_head(figure, joints, skin, hair, cloth_material(figure['cap']))
    else:
        bodice = cloth_material(figure['bodice'])
        parts += build_bodice_and_skirt(figure, joints, cloth_material(figure['skirt']), bodice)
        parts += build_sleeves(figure, joints, bodice, woman=True)
        parts += build_legs_and_boots(figure, joints, plain_material('dark stocking', (0.02, 0.018, 0.017), 0.8), boots, woman=True)
        parts += build_head(figure, joints, skin, hair, None)
        parts += build_shawl(figure, joints, cloth_material(figure['shawl']))
    parts += build_hands(figure, joints, skin)
    if 'bundle' in figure:
        parts += build_bundle(figure, joints)
    if 'bag' in figure:
        parts += build_bag(figure, joints)
    # one mesh: every piece's smoothing and cloth edge made permanent, then joined
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target='MESH')
    # the lowest point of the bare hands (for a shot to check the gap between warming hands and a brazier's rim)
    hand_heights = [(part.matrix_world @ v.co).z for part in parts if '-hand-' in part.name or '-thumb-' in part.name
                    for v in part.data.vertices]
    joints['hands_lowest'] = min(hand_heights) if hand_heights else None
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = f'{name}-body'
    body.data.name = f'{name}-body'
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    body.parent = root
    bpy.context.view_layer.update()
    return figure, joints, root, body


def measure(body):
    corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
    low = Vector(map(min, *corners))
    high = Vector(map(max, *corners))
    body.data.calc_loop_triangles()
    return low, high, len(body.data.loop_triangles)


def save_figure(figure, joints, root, body):
    os.makedirs(FIGURES_FOLDER, exist_ok=True)
    path = os.path.join(FIGURES_FOLDER, f"{figure['name']}.glb")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_extras=True, export_yup=True)
    low, high, triangles = measure(body)
    entry = {
        'file': f"{figure['name']}.glb",
        'what': figure['what'],
        'height_metres': round(high.z - low.z, 3),
        'size_metres': {'width_x': round(high.x - low.x, 3), 'depth': round(high.y - low.y, 3), 'height': round(high.z - low.z, 3)},
        'faces': '+y in Blender (-z in three.js): turned 0 it shows its back to a camera looking up +y',
        'kind': 'walker' if figure.get('walker') else 'waiting',
        'triangles': triangles,
        'kilobytes': os.path.getsize(path) // 1024,
        'source': SOURCE,
        'licence': LICENCE,
    }
    if 'grip_bar' in figure:
        entry['grip_bar_at'] = [round(v * joints['scale'], 3) for v in figure['grip_bar']]
        entry['grip_bar_note'] = 'where the upright bar its right hand holds stands, from its origin (Blender x, y)'
    if 'brazier_ahead' in figure:
        entry['brazier_ahead'] = round(figure['brazier_ahead'] * joints['scale'], 3)
        entry['brazier_note'] = 'the brazier\'s middle this far in front of its origin (Blender +y)'
        entry['hands_lowest_metres'] = round(joints['hands_lowest'], 3)
        entry['hands_note'] = ('the lowest point of his warming hands above the ground he stands on: keep a brazier\'s rim at '
                               'least 0.10 m lower (the pit village brazier drum is 0.856 m tall), so they hover over the fire')
    if figure.get('wall_side'):
        entry['wall_at_x'] = round(high.x, 3)
        entry['wall_note'] = 'its right shoulder touches a wall standing at this x (Blender) from its origin'
    index = []
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as handle:
            index = json.load(handle)
    index = sorted([e for e in index if e['file'] != entry['file']] + [entry], key=lambda e: e['file'])
    with open(INDEX_PATH, 'w') as handle:
        json.dump(index, handle, indent=1)
    print(f"FIGURE {figure['name']}: {entry['height_metres']} m tall, {triangles} triangles, {entry['kilobytes']} KB")
    return entry


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for figure_name in arguments or list(FIGURES):
        save_figure(*build_figure(figure_name))
