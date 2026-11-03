"""
barbed_wire_fence: a 1914-18 barbed wire fence: rough round timber posts, each leaning a little its own way, with
strands of barbed wire (two twisted wires, four-point barbs every 12-13 cm) stapled to the posts' front and sagging
between them, and a diagonal strand criss-crossing each bay as in the board's photograph of a wire tangle.

Options:
  length         the fence's length along X in metres (default 6.0)
  post_spacing   metres between posts (default 2.5; adjusted so the posts fit the length)
  strands        how many horizontal strands (default 4)
  seed           small differences: post lean and height, sag, barb placing

About 6.2 x 0.15 x 1.39 m at the defaults. The fence runs along X; the wire is on its front (-Y) face. Foot at z = 0.

Made for the store from `build_fence` in '46 military-base - render_final.py' (line 534) and `wire_line` in the 50
scripts ('50 first pass' line 698, '50 second pass' line 845); rebuilt with real twisted, barbed strands.
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
import bmesh  # noqa: E402,F401
from mathutils import Vector  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'barbed_wire_fence',
    'what': 'a barbed wire fence: leaning timber posts, sagging strands of twisted barbed wire, a diagonal in each bay',
    'size_m': (6.21, 0.15, 1.39),
    'options': {
        'length': "the fence's length along X in metres (default 6.0)",
        'post_spacing': 'metres between posts (default 2.5; adjusted so the posts fit the length)',
        'strands': 'how many horizontal strands (default 4)',
        'seed': 'post lean and height, sag, barb placing (default 0)',
    },
    'materials': ['SURFACE • rough_wood (barbed_wire_fence)', 'RUST • rain-aged iron'],
    'source': "`build_fence` in '46 military-base - render_final.py' (line 534); `wire_line` in '50 first pass' (line 698) "
              "and '50 second pass - render_final.py' (line 845)",
    'views': 'reads from every side; the wire is fine (2-3 mm), so from far off it is a faint web and the barbs show close up',
    'trap': 'The wire is a real 2-3 mm thick: at a distance it can vanish in a small, low-sample render.',
}

PART = 'barbed_wire_fence'


def build(collection, seed=0, length=6.0, post_spacing=2.5, strands=4, **_ignored):
    rnd = sh.rand(seed, PART)
    L = max(1.0, float(length))
    n_bays = max(1, int(round(L / max(0.8, float(post_spacing)))))
    n_strands = max(1, int(strands))
    wood = sh.copy_surface('SURFACE • rough_wood', PART, mud_height=0.3, grime=0.5)
    posts = sh.Grain('barbed_wire_fence posts', wood, (0, 0, 1), rnd)
    wire = sh.Builder('barbed_wire_fence wire', 'RUST • rain-aged iron')
    staples = sh.Builder('barbed_wire_fence staples', 'RUST • rain-aged iron')

    tops = []
    for k in range(n_bays + 1):
        x = -L / 2 + L * k / n_bays + rnd.uniform(-0.05, 0.05)
        h = rnd.uniform(1.26, 1.38)
        r = rnd.uniform(0.045, 0.06)
        lean = Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.04, 0.04), 0.0))
        base = Vector((x, 0.0, 0.0))
        top = base + lean + Vector((0, 0, h))
        sh.add_cylinder(posts, base, top, r, r * 0.92, segments=9, phase=rnd.uniform(0, 1))
        cut = top + Vector((0, 0, 0.0))
        sh.add_cylinder(posts, cut - Vector((0, 0, 0.001)), cut + Vector((0, 0, 0.012)), r * 0.85, r * 0.6, segments=9)
        tops.append((base, top, r))

    def on_post(k, z):
        base, top, r = tops[k]
        f = z / (top.z - base.z)
        p = base.lerp(top, f)
        return p + Vector((0.0, -(r + 0.004), 0.0))

    heights = [0.22 + (1.12 - 0.22) * i / max(n_strands - 1, 1) for i in range(n_strands)] if n_strands > 1 else [0.7]
    for z in heights:
        pts = []
        for k in range(n_bays):
            a, b = on_post(k, z + rnd.uniform(-0.02, 0.02)), on_post(k + 1, z + rnd.uniform(-0.02, 0.02))
            seg = sh.sag_line(a, b, rnd.uniform(0.025, 0.06), 12, wobble=0.006, rnd=rnd)
            pts.extend(seg if not pts else seg[1:])
        sh.barbed_strand(wire.bm, pts, rnd)
        for k in range(n_bays + 1):
            p = on_post(k, z)
            sh.box(staples.bm, p + Vector((-0.012, -0.002, -0.004)), p + Vector((0.012, 0.004, 0.004)))
    # a diagonal in each bay, alternate ways, a little in front of the strands
    for k in range(n_bays):
        z0, z1 = (heights[0], heights[-1]) if k % 2 == 0 else (heights[-1], heights[0])
        a = on_post(k, z0) + Vector((0, -0.012, 0))
        b = on_post(k + 1, z1) + Vector((0, -0.012, 0))
        sh.barbed_strand(wire.bm, sh.sag_line(a, b, 0.03, 14, wobble=0.008, rnd=rnd), rnd)

    made = []
    for builder in (posts, wire, staples):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return made
