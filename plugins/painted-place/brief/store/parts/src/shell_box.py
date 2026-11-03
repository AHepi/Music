"""
shell_box: 1914-18 18-pounder rounds standing in an open wooden ammunition box: brass cartridge cases (rim, body,
neck) with their shells on top (dull dark paint, a copper driving band, a brass fuze at the nose), in two rows either
side of a divider board; the box built of boards with end battens and rope handles; its lid leant against the
front.

Options:
  count   how many rounds stand in the box (default 6; the box grows to hold them, two rows)
  seed    small differences: each round's lean and turn, the lid's lean, wood

About 0.48 x 0.41 x 0.58 m at the defaults (the leaning lid included). The box's length runs along X; the lid leans on the front (-Y).
Foot at z = 0, centred on the origin.

Made for the store from `shells` in '46 military-base - render_final.py' (line 656) and the open ammunition crate in
'50 second pass - render_final.py' (near line 1201, lid propped, shell noses showing).
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
import bmesh  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'shell_box',
    'what': 'brass-cased 18-pounder rounds standing in an open wooden box, its lid leant against it',
    'size_m': (0.48, 0.41, 0.58),
    'options': {
        'count': 'how many rounds stand in the box (default 6; the box grows to hold them, two rows)',
        'seed': "each round's lean and turn, the lid's lean, wood (default 0)",
    },
    'materials': ['SURFACE • rough_wood (shell_box)', 'MADE • old brass', 'MADE • old copper', 'PART • shell_box: dull shell paint',
                  'PART • shell_box: hemp rope'],
    'source': "`shells` in '46 military-base - render_final.py' (line 656); the open ammunition crate in "
              "'50 second pass - render_final.py' (near line 1201)",
    'views': 'reads from every side',
    'trap': '',
}

PART = 'shell_box'
PITCH = 0.112          # spacing of the rounds
CASE_R = 0.044
ROUND_H = 0.53


def build(collection, seed=0, count=6, **_ignored):
    rnd = sh.rand(seed, PART)
    n = max(1, int(count))
    cols = max(1, int(math.ceil(n / 2.0)))
    rows = 2 if n > 1 else 1
    t = 0.019
    lx = cols * PITCH + 2 * t + 0.03
    ly = rows * PITCH + 2 * t + 0.03 + (0.012 if rows == 2 else 0.0)
    lz = 0.29
    wood = sh.copy_surface('SURFACE • rough_wood', PART, mud_height=0.08, grime=0.6, edge_wear=0.35)
    rope = sh.rope_material(PART)
    along_x = sh.Grain('shell_box boards', wood, (1, 0, 0), rnd)
    along_y = sh.Grain('shell_box end boards', wood, (0, 1, 0), rnd)
    upright = sh.Grain('shell_box battens', wood, (0, 0, 1), rnd)
    ropes = sh.Builder('shell_box rope handles', rope)
    hx, hy = lx / 2, ly / 2
    bottom = 0.03                       # on two skids

    for side in (-1, 1):                # long sides, two boards each
        for k, (a, b) in enumerate(((0.0, 0.5), (0.5, 1.0))):
            za, zb = bottom + (lz - bottom) * a, bottom + (lz - bottom) * b
            y0, y1 = sorted((side * hy, side * (hy - t)))
            sh.add_box(along_x, (-hx, y0, za + 0.0015), (hx, y1, zb - 0.0015))
        x0, x1 = sorted((side * hx, side * (hx - t)))   # ends
        sh.add_box(along_y, (x0, -hy + t, bottom), (x1, hy - t, lz))
        bx0, bx1 = sorted((side * hx, side * (hx + 0.02)))
        for y in (-hy + 0.04, hy - 0.04):
            sh.add_box(upright, (bx0, y - 0.03, bottom), (bx1, y + 0.03, lz))
        za = bottom + (lz - bottom) * 0.7
        loop = sh.sag_line(Vector((side * (hx + 0.03), -hy + 0.06, za)), Vector((side * (hx + 0.03), hy - 0.06, za)), 0.07, 12)
        sh.tube(ropes.bm, loop, 0.008, sides=6)
        for y in (-hy + 0.06, hy - 0.06):
            sh.cylinder(ropes.bm, (side * (hx + 0.015), y, za), (side * (hx + 0.04), y, za), 0.014, segments=8)
    sh.add_box(along_x, (-hx + t, -hy + t, bottom), (hx - t, hy - t, bottom + t))            # floor
    for x in (-hx + 0.05, hx - 0.05):
        sh.add_box(along_y, (x - 0.03, -hy + 0.01, 0.0), (x + 0.03, hy - 0.01, bottom))     # skids
    if rows == 2:
        sh.add_box(along_x, (-hx + t, -0.006, bottom + t), (hx - t, 0.006, lz - 0.05))      # divider

    # the lid, leant against the front
    lean = math.radians(rnd.uniform(14.0, 22.0))
    lid_h = ly + 0.0
    foot_y = -hy - 0.012 - math.sin(lean) * lid_h
    lid = sh.Grain('shell_box lid', wood, (1, 0, 0), rnd)
    up = Vector((0.0, math.sin(lean), math.cos(lean)))
    out = Vector((0.0, -math.cos(lean), math.sin(lean)))
    for k, (a, b) in enumerate(((0.0, 0.33), (0.33, 0.66), (0.66, 1.0))):
        p0 = Vector((0.0, foot_y, 0.0)) + up * (lid_h * a + 0.0015)
        p1 = Vector((0.0, foot_y, 0.0)) + up * (lid_h * b - 0.0015)
        pts = []
        for p in (p0, p1):
            for dx, dn in ((-hx, 0.0), (hx, 0.0), (hx, t), (-hx, t)):
                pts.append(p + Vector((dx, 0, 0)) + out * dn)
        sh.add_hexahedron(lid, pts[:4] + pts[4:])
    for x in (-hx + 0.04, hx - 0.04):                   # battens across the lid's inside face
        p0 = Vector((x, foot_y, 0.0)) + up * 0.01 - out * 0.0
        pts = []
        for p in (p0, Vector((x, foot_y, 0.0)) + up * (lid_h - 0.01)):
            for dx, dn in ((-0.03, 0.0), (0.03, 0.0), (0.03, -0.02), (-0.03, -0.02)):
                pts.append(p + Vector((dx, 0, 0)) + out * dn)
        sh.add_hexahedron(lid, pts)

    # the rounds: brass case, steel shell, copper driving band, brass fuze
    brass = sh.Builder('shell_box cartridge cases', 'MADE • old brass', smooth=True)
    shell_paint = sh.plain_material(PART, 'dull shell paint', (0.034, 0.036, 0.033), roughness=0.62, metallic=0.25, variation=0.35,
                                    scale=60.0, bump=0.2)
    steel = sh.Builder('shell_box shells', shell_paint, smooth=True)
    copper = sh.Builder('shell_box driving bands', 'MADE • old copper', smooth=True)
    fuze = sh.Builder('shell_box fuzes', 'MADE • old brass', smooth=True)
    floor_z = bottom + t
    case = [(0.0, 0.0), (0.049, 0.0), (0.049, 0.008), (0.045, 0.01), (0.045, 0.012), (0.044, 0.03), (0.0425, 0.27), (0.0415, 0.29)]
    shell = [(0.0415, 0.29), (0.0415, 0.39), (0.039, 0.43), (0.032, 0.465), (0.022, 0.49)]
    band = [(0.0418, 0.3), (0.0435, 0.303), (0.0435, 0.318), (0.0418, 0.32)]
    nose = [(0.022, 0.49), (0.019, 0.505), (0.014, 0.52), (0.006, ROUND_H), (0.0, ROUND_H + 0.001)]
    placed = 0
    for r in range(rows):
        for c in range(cols):
            if placed >= n:
                break
            placed += 1
            x = -hx + t + 0.015 + PITCH * (c + 0.5)
            y = (-0.006 - PITCH * 0.5 - 0.004) if (rows == 2 and r == 0) else ((0.006 + PITCH * 0.5 + 0.004) if rows == 2 else 0.0)
            tilt = Matrix.Rotation(rnd.uniform(-0.035, 0.035), 4, 'X') @ Matrix.Rotation(rnd.uniform(-0.035, 0.035), 4, 'Y')
            M = Matrix.Translation((x, y, floor_z)) @ tilt @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, 'Z')
            sh.lathe(brass.bm, case, segments=20, matrix=M, close_bottom=False, close_top=False)
            sh.lathe(steel.bm, shell, segments=20, matrix=M, close_bottom=False, close_top=False)
            sh.lathe(copper.bm, band, segments=20, matrix=M, close_bottom=False, close_top=False)
            sh.lathe(fuze.bm, nose, segments=16, matrix=M, close_bottom=False, close_top=False)
            sh.lathe(brass.bm, [(0.0, 0.0005), (0.012, 0.0005)], segments=12, matrix=M, close_bottom=False, close_top=False)

    made = []
    for builder in (along_x, along_y, upright, ropes, lid, brass, steel, copper, fuze):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return made
