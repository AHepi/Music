"""
sandbag_wall: a straight wall of filled sandbags, laid in courses and bonded like bricks (each course shifted half a
bag), each bag a soft pillow pressed into the course below, every one a little different in size, turn and slump,
tied ends turned this way and that; the front face set back a little each course (a batter), mud on the lowest
courses.

Options:
  length    the wall's length along X in metres (default 3.0)
  courses   how many courses high (default 5; each about 0.105 m)
  depth     how many bags thick (default 2)
  seed      small differences: every bag's size, turn and slump

About 3.0 x 0.55 x 0.55 m at the defaults. The wall runs along X; its front faces -Y. Foot at z = 0, centred.

Made for the store from `sandbags` in '46 military-base - render_final.py' (line 602) and the 50 scripts' `sandbags`
('50 first pass' line 651, '50 second pass' line 798); rebuilt with real bag shapes, a batter and a bond.
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
import bmesh  # noqa: E402,F401

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'sandbag_wall',
    'what': 'a straight sandbag wall in bonded courses, each bag a soft, slightly different pillow',
    'size_m': (3.07, 0.55, 0.56),
    'options': {
        'length': "the wall's length along X in metres (default 3.0)",
        'courses': 'how many courses high, about 0.105 m each (default 5)',
        'depth': 'how many bags thick (default 2)',
        'seed': "every bag's size, turn and slump (default 0)",
    },
    'materials': ['SURFACE • hessian_380 (sandbag_wall)'],
    'source': "`sandbags` in '46 military-base - render_final.py' (line 602), '50 first pass' (line 651) and "
              "'50 second pass - render_final.py' (line 798)",
    'views': 'reads from every side',
    'trap': 'Courses shift by half a bag, so the wall ends are toothed; walls meeting at a corner overlap a little.',
}

PART = 'sandbag_wall'
BAG_L, BAG_W, BAG_H = 0.5, 0.26, 0.15
COURSE_H = 0.105
BATTER = 0.018


def build(collection, seed=0, length=3.0, courses=5, depth=2, **_ignored):
    rnd = sh.rand(seed, PART)
    L = max(0.5, float(length))
    n_courses = max(1, int(courses))
    rows = max(1, int(depth))
    hessian = sh.copy_surface('SURFACE • hessian_380', PART, mud_height=0.22, grime=0.7, darken=0.19, bump=0.6)
    bags = sh.Builder('sandbag_wall bags', hessian, smooth=True)
    thickness = rows * BAG_W * 0.96
    n_bags = max(1, int(round(L / BAG_L)))
    step = L / n_bags
    for k in range(n_courses):
        offset = 0.5 * step if k % 2 else 0.0
        z = k * COURSE_H + 0.78 * BAG_H / 2
        set_back = k * BATTER
        for r in range(rows):
            y = -thickness / 2 + BAG_W * 0.48 + r * BAG_W * 0.96 + set_back * (1.0 - r / max(rows, 1)) * 0.6
            count = n_bags if k % 2 == 0 else n_bags - 1
            for i in range(count):
                x = -L / 2 + offset + step * (i + 0.5)
                length_b = step * rnd.uniform(0.96, 1.06)
                sh.sandbag(bags.bm, (x + rnd.uniform(-0.02, 0.02), y + rnd.uniform(-0.015, 0.015), z + rnd.uniform(-0.006, 0.008)),
                           length_b, BAG_W * rnd.uniform(0.95, 1.05), BAG_H * rnd.uniform(0.92, 1.08), rnd.uniform(-0.06, 0.06), rnd,
                           tied=rnd.choice((-1, 1)), slump=(0.012 if k > 0 else 0.0) * rnd.uniform(0.5, 1.2))
    return [bags.finish(collection)]
