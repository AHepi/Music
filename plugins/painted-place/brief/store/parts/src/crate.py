"""
crate: a 1914-18 wooden supply crate: side and lid boards running lengthwise (hairline gaps between them, each board
a little proud or sunk), end boards behind two upright battens at each end, a rope handle looped through the
battens at each end and knotted, a bottom on two skids, two thin iron straps round it with their nail heads.

Options:
  size    outside size in metres, as (length, width, height) or "length,width,height", or one number that scales the
          default size (default 0.75, 0.42, 0.38)
  seed    small differences: board widths and set, rope sag, wood

About 0.82 x 0.43 x 0.38 m with its rope handles. The crate's length runs along X; its front (-Y) is a long side. Foot at z = 0, centred on the origin.

Made for the store from `crate` and `crates` in '46 military-base - render_final.py' (line 701) and the crates and
ammunition boxes in the 50 scripts ('50 second pass - render_final.py' near line 793 and 909); rebuilt from boards.
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
    'name': 'crate',
    'what': 'a wooden supply crate: lengthwise boards, end battens, rope handles, iron straps, skids',
    'size_m': (0.82, 0.43, 0.38),
    'options': {
        'size': 'outside (length, width, height) in metres, or "length,width,height", or one number that scales the default (default 0.75, 0.42, 0.38)',
        'seed': 'board widths and set, rope sag, wood (default 0)',
    },
    'materials': ['SURFACE • rough_wood (crate)', 'PART • crate: hemp rope', 'RUST • rain-aged iron'],
    'source': "`crate` and `crates` in '46 military-base - render_final.py' (line 701); the crates and ammunition boxes "
              "in '50 second pass - render_final.py' (near lines 793 and 909)",
    'views': 'reads from every side',
    'trap': '',
}

PART = 'crate'


def _size(size):
    if isinstance(size, str):
        size = [float(v) for v in size.replace('x', ',').split(',')]
    if isinstance(size, (int, float)):
        size = (0.75 * size, 0.42 * size, 0.38 * size)
    return tuple(max(0.12, float(v)) for v in size)


def build(collection, seed=0, size=(0.75, 0.42, 0.38), **_ignored):
    rnd = sh.rand(seed, PART)
    lx, ly, lz = _size(size)
    wood = sh.copy_surface('SURFACE • rough_wood', PART, mud_height=0.1, grime=0.55, edge_wear=0.35)
    rope = sh.rope_material(PART)
    t = 0.019                                   # board thickness
    skid = 0.035
    along_x = [sh.Grain('crate boards %d' % (k + 1), wood, (1, 0, 0), rnd) for k in range(2)]
    along_y = sh.Grain('crate end boards', wood, (0, 1, 0), rnd)
    upright = sh.Grain('crate battens', wood, (0, 0, 1), rnd)
    iron = sh.Builder('crate straps and nails', 'RUST • rain-aged iron')
    ropes = sh.Builder('crate rope handles', rope)
    z0, z1 = skid, lz
    hx, hy = lx / 2, ly / 2
    batten = 0.022
    inner_hx = hx - batten                      # the box itself, inside the battens

    def boards(count, extent):
        widths = [rnd.uniform(0.85, 1.15) for _ in range(count)]
        total = sum(widths)
        edges, acc = [], 0.0
        for w in widths:
            edges.append((acc / total * extent, (acc + w) / total * extent))
            acc += w
        return edges

    # long sides: boards along X, each a little proud or sunk
    for side in (-1, 1):
        for k, (a, b) in enumerate(boards(3, z1 - z0)):
            proud = rnd.uniform(-0.0015, 0.0015)
            y_out = side * (hy + proud)
            y_in = side * (hy - t)
            sh.add_box(along_x[k % 2], (-inner_hx, min(y_out, y_in), z0 + a + 0.0015), (inner_hx, max(y_out, y_in), z0 + b - 0.0015))
    # lid and bottom
    for z_lo, z_hi in ((z1 - t, z1), (z0, z0 + t)):
        for k, (a, b) in enumerate(boards(3, ly - 2 * t)):
            dz = rnd.uniform(-0.0012, 0.0012) if z_hi == z1 else 0.0
            sh.add_box(along_x[(k + 1) % 2], (-inner_hx, -hy + t + a + 0.0015, z_lo + dz), (inner_hx, -hy + t + b - 0.0015, z_hi + dz))
    # ends: boards along Y between the sides, two battens outside each, the rope handle through them
    for side in (-1, 1):
        x_out, x_in = side * inner_hx, side * (inner_hx - t)
        for (a, b) in boards(2, z1 - z0 - 2 * t):
            sh.add_box(along_y, (min(x_out, x_in), -hy + t, z0 + t + a + 0.0015), (max(x_out, x_in), hy - t, z0 + t + b - 0.0015))
        bx0, bx1 = sorted((side * inner_hx, side * hx))
        for y in (-hy + 0.045, hy - 0.045):
            sh.add_box(upright, (bx0, y - 0.035, z0), (bx1, y + 0.035, z1 + 0.004))
        # rope: knotted outside each batten, hanging in a loop between
        xr = side * (hx + 0.012)
        za = z0 + (z1 - z0) * 0.68
        ya, yb = -hy + 0.045, hy - 0.045
        loop = sh.sag_line(Vector((xr, ya + 0.02, za)), Vector((xr, yb - 0.02, za)), (z1 - z0) * rnd.uniform(0.28, 0.36), 16)
        for p in loop[1:-1]:
            p.x += side * 0.012 * math.sin(math.pi * (loop.index(p) / (len(loop) - 1)))
        sh.tube(ropes.bm, loop, 0.009, sides=6)
        for y in (ya, yb):
            sh.cylinder(ropes.bm, (side * (hx - 0.002), y, za), (side * (hx + 0.022), y, za), 0.017, segments=8)
    # skids underneath, across the width
    for x in (-inner_hx + 0.08, inner_hx - 0.08):
        sh.add_box(along_y, (x - 0.035, -hy + 0.01, 0.0), (x + 0.035, hy - 0.01, z0))
    # two iron straps round the crate, nailed
    for x in (-lx * 0.3, lx * 0.3):
        w = 0.016
        sh.box(iron.bm, (x - w, -hy - 0.0025, z0), (x + w, -hy + 0.0005, z1))
        sh.box(iron.bm, (x - w, hy - 0.0005, z0), (x + w, hy + 0.0025, z1))
        sh.box(iron.bm, (x - w, -hy - 0.0025, z1 - 0.0005 + 0.0012), (x + w, hy + 0.0025, z1 + 0.0035))
        for z in (z0 + 0.03, (z0 + z1) / 2, z1 - 0.03):
            for y in (-hy - 0.004, hy + 0.0015):
                sh.cylinder(iron.bm, (x, y, z), (x, y + 0.0025, z), 0.004, segments=6)
    # nail heads along the boards
    for side in (-1, 1):
        for x in (-inner_hx + 0.03, inner_hx - 0.03):
            for z in (z0 + 0.06, (z0 + z1) / 2, z1 - 0.06):
                y = side * (hy + 0.0005)
                sh.cylinder(iron.bm, (x, y, z), (x, y + side * 0.0022, z), 0.0032, segments=5)

    made = []
    for builder in (*along_x, along_y, upright, iron, ropes):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return made
