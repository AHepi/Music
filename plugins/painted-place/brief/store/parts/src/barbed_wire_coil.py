"""
barbed_wire_coil: a 1914-18 concertina coil of barbed wire lying on the ground, drawn out along X: loops of
twisted barbed wire, each loop a little different, two coils wound into each other, clipped together where they
cross, the loops pressed flat a little where they rest on the ground.

Options:
  length   how far the coil is drawn out along X in metres (default 3.0)
  seed     small differences: the loops' sizes and wobble, barb placing

About 3.0 x 0.9 x 0.85 m at the defaults. Its length runs along X. Foot at z = 0, centred on the origin.

Made for the store from `helix` in '46 military-base - render_final.py' (line 730) and the coil in the 50 scripts
(`wire_line` and the concertina coil after it, '50 first pass' line 698 / 738, '50 second pass' line 845 / 885);
rebuilt with real barbed strands.
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
import bmesh  # noqa: E402,F401
from mathutils import Vector, noise  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'barbed_wire_coil',
    'what': 'a concertina coil of barbed wire drawn out along the ground',
    'size_m': (3.03, 0.9, 0.87),
    'options': {
        'length': 'how far the coil is drawn out along X in metres (default 3.0)',
        'seed': "the loops' sizes and wobble, barb placing (default 0)",
    },
    'materials': ['RUST • rain-aged iron'],
    'source': "`helix` in '46 military-base - render_final.py' (line 730); the concertina coil in '50 first pass' "
              "(line 738) and '50 second pass - render_final.py' (line 885)",
    'views': 'reads from every side; the wire is fine (2-3 mm), so from far off it is a faint web and the barbs show close up',
    'trap': 'The wire is a real 2-3 mm thick: at a distance it can vanish in a small, low-sample render.',
}

PART = 'barbed_wire_coil'


def build(collection, seed=0, length=3.0, **_ignored):
    rnd = sh.rand(seed, PART)
    L = max(0.6, float(length))
    wire = sh.Builder('barbed_wire_coil wire', 'RUST • rain-aged iron')
    clips = sh.Builder('barbed_wire_coil clips', 'RUST • rain-aged iron')
    radius = 0.43
    pitch = 0.22
    turns = max(2, int(round(L / pitch)))
    phase = Vector((rnd.uniform(0, 40), rnd.uniform(0, 40), rnd.uniform(0, 40)))
    coils = []
    for c, (r_c, start) in enumerate(((radius, 0.0), (radius * 0.93, math.pi))):
        pts = []
        n = turns * 40
        for i in range(n + 1):
            t = i / n
            a = 2 * math.pi * turns * t + start
            loop = int(turns * t)
            r = r_c * (1.0 + 0.06 * noise.noise(Vector((loop * 0.7, c * 3.1, 0.5)) + phase))
            x = -L / 2 + L * t + 0.035 * math.sin(a * 0.5 + c) + 0.03 * noise.noise(Vector((t * 9.0, c, 1.0)) + phase)
            y = r * math.cos(a)
            z = r_c + r * math.sin(a)
            z = max(z, 0.0035 + 0.008 * (1 + math.sin(a * 3.0)))        # loops pressed flat on the ground
            pts.append(Vector((x, y, z)))
        coils.append(pts)
        sh.barbed_strand(wire.bm, pts, rnd, barb_every=0.15)
    # clips where the two coils pass close to each other
    a_pts, b_pts = coils
    for i in range(0, len(a_pts), 20):
        p = a_pts[i]
        j = min(range(max(0, i - 30), min(len(b_pts), i + 30)), key=lambda q: (b_pts[q] - p).length)
        q = b_pts[j]
        if (q - p).length < 0.08:
            m = (p + q) / 2
            sh.cylinder(clips.bm, m - (q - p) * 0.6 - Vector((0, 0, 0.004)), m + (q - p) * 0.6 + Vector((0, 0, 0.004)), 0.004, segments=5)
    made = []
    for builder in (wire, clips):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return made
