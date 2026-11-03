"""
bell_tent: a 1914-18 British army bell tent: a canvas cone of 24 sewn panels on a centre pole, over a short
upright wall; 23 guy ropes from the eave hem to angled wooden pegs, each with its wooden runner; small pegs holding
the wall's foot; a canvas cap on top with the pole's tip through it. Inside: a groundsheet, the pole, rolled
blankets and a kit bag (seen through the open door).

Options:
  door_open   the door flaps rolled back and tied, the inside showing (default True)
  seed        small differences: the canvas's slack and wrinkles, guy and peg placing, a slight lean

About 3.9 m across the canvas (7.2 m with the guy ropes), 3.2 m high. The door faces -Y. Foot at z = 0.

Made for the store from `tent` in '50 first pass - render_final.py' (line 377), '50 second pass - render_final.py'
(line 495) and '46 military-base - render_final.py' (line 463); rebuilt whole from the board's photographs
(02 Recruits, Fargo Camp: seams, door flap, guy ropes) so it reads from every side.
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402,F401
from mathutils import Vector, noise  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'bell_tent',
    'what': 'a 1914-18 army bell tent: canvas cone of sewn panels on a centre pole, guy ropes to pegs, door flaps',
    'size_m': (7.21, 7.06, 3.23),
    'options': {
        'door_open': 'the door flaps rolled back and tied, the inside showing (default True)',
        'seed': "the canvas's slack and wrinkles, guy and peg placing, a slight lean (default 0)",
    },
    'materials': ['SURFACE • rough_linen (bell_tent)', 'PART • bell_tent: hemp rope', 'SURFACE • rough_wood',
                  'SURFACE • hessian_380', 'IRON • soot-black lamp posts', 'RECESSES • near-black blue'],
    'source': "rebuilt from `tent` in '50 first pass - render_final.py' (line 377), '50 second pass' (line 495) and "
              "'46 military-base - render_final.py' (line 463), with the board's photograph 02 for its make",
    'views': 'reads from every side',
    'trap': 'The guy ropes reach 3.5 m from the centre: leave that much clear ground round it.',
}

PART = 'bell_tent'
PANELS = 24
COLS_PER_PANEL = 6
R_WALL = 1.86        # the upright wall
WALL_TOP = 0.71      # where the wall tucks up under the cone
R_EAVE = 1.95        # the cone's lower edge (eave hem)
Z_EAVE = 0.60
Z_TOP = 2.95         # where the cone meets the cap
R_TOP = 0.07
Z_DOOR = 1.72        # top of the door slit


def build(collection, seed=0, door_open=True, **_ignored):
    rnd = sh.rand(seed, PART)
    canvas = sh.copy_surface('SURFACE • rough_linen', PART, mud_height=0.4, grime=0.65, darken=0.25)
    rope = sh.rope_material(PART)
    made = []

    door_theta = -math.pi / 2                     # the door faces -Y
    panel = 2 * math.pi / PANELS
    lean = Vector((rnd.uniform(-0.035, 0.035), rnd.uniform(-0.035, 0.035), 0.0))
    phase = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    gap0 = (0.86 if door_open else 0.0) * panel   # how far the door flaps are drawn back at the ground

    def gap(z):
        if not door_open or z >= Z_DOOR:
            return 0.0
        return gap0 * (1.0 - z / Z_DOOR) ** 0.8

    def theta_of(i, z):
        """Column i's angle at height z: the two panels beside the door are drawn back when the door is open."""
        t = door_theta + panel * i / COLS_PER_PANEL
        rel = (t - door_theta)
        g = gap(z)
        if g > 0.0:
            if rel < panel:
                rel = g + rel / panel * (panel - g)
            elif rel > 2 * math.pi - panel:
                back = 2 * math.pi - rel
                rel = 2 * math.pi - (g + back / panel * (panel - g))
        return door_theta + rel

    slack = [rnd.uniform(0.55, 1.6) for _ in range(PANELS)]   # some panels hang slacker than others

    def panel_bulge(t):
        u = ((t - door_theta) / panel) % PANELS
        k = int(u) % PANELS
        f = u - int(u)
        seam = max(0.0, 1.0 - min(f, 1.0 - f) * COLS_PER_PANEL * 0.9)
        return math.sin(math.pi * f) * slack[k], seam

    def wrinkle(p, amount):
        return amount * (noise.noise(Vector((p.x * 3.2, p.y * 3.2, p.z * 2.4)) + phase) +
                         0.5 * noise.noise(Vector((p.x * 7.0, p.y * 7.0, p.z * 1.2)) - phase))

    def cone_point(t, z):
        f = (z - Z_EAVE) / (Z_TOP - Z_EAVE)
        r = R_EAVE + (R_TOP - R_EAVE) * f
        bulge, seam = panel_bulge(t)
        envelope = math.sin(math.pi * min(max(f, 0.0), 1.0)) ** 0.7
        r -= 0.045 * bulge * envelope + 0.012 * bulge * (1 - f) ** 6 + 0.035 * math.sin(math.pi * min(max(f, 0.0), 1.0))
        r += 0.006 * seam
        zz = z - 0.035 * bulge * max(0.0, 1.0 - f * 6.0)    # the hem droops between the guys
        p = Vector((r * math.cos(t), r * math.sin(t), zz)) + lean * max(f, 0.0)
        p += Vector((math.cos(t), math.sin(t), 0.0)) * wrinkle(p, 0.022 * envelope)
        return p

    def wall_point(t, z):
        bulge, seam = panel_bulge(t)
        foot = (1.0 - z / WALL_TOP) ** 2
        r = R_WALL + 0.045 * foot - 0.02 * bulge * foot + 0.004 * seam
        p = Vector((r * math.cos(t), r * math.sin(t), z))
        p += Vector((math.cos(t), math.sin(t), 0.0)) * wrinkle(p, 0.016)
        return p

    # ---------------------------------------------------------------- the canvas: cone and wall, one sheet each
    tent = sh.Builder('bell_tent canvas', canvas, smooth=True)
    n_cols = PANELS * COLS_PER_PANEL

    def sheet(rows_z, point):
        grid = []
        for z in rows_z:
            row = []
            for i in range(n_cols + 1):
                if i == n_cols and gap(z) == 0.0:
                    row.append(row[0])
                    continue
                row.append(tent.bm.verts.new(point(theta_of(i, z), z)))
            grid.append(row)
        for j in range(len(rows_z) - 1):
            for i in range(n_cols):
                a, b, c, d = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]
                if len({a, b, c, d}) == 4:
                    tent.bm.faces.new((a, b, c, d))
        return grid

    cone_rows = [Z_EAVE + (Z_TOP - Z_EAVE) * (k / 20.0) ** 1.15 for k in range(21)]
    if door_open:
        cone_rows = sorted(set([round(z, 4) for z in cone_rows] + [Z_DOOR]))
    cone_grid = sheet(cone_rows, cone_point)
    wall_rows = [0.0, 0.12, 0.26, 0.42, 0.58, WALL_TOP]
    sheet(wall_rows, wall_point)
    # a doubled hem along the eave, standing a little proud of the cone
    hem = sh.Builder('bell_tent eave hem', canvas, smooth=True)
    hem_pts = []
    for i in range(n_cols + 1):
        hem_pts.append(cone_point(theta_of(i, Z_EAVE), Z_EAVE) + Vector((0, 0, 0.012)))
    if door_open:
        sh.tube(hem.bm, hem_pts, 0.014, sides=5)
    else:
        sh.tube(hem.bm, hem_pts, 0.014, sides=5, caps=False)

    # cap at the top, with the pole's tip through it
    sh.lathe(hem.bm, [(0.12, Z_TOP - 0.03), (0.17, Z_TOP + 0.02), (0.165, Z_TOP + 0.07), (0.1, Z_TOP + 0.11), (0.035, Z_TOP + 0.125)],
             segments=20, centre=(lean.x, lean.y, 0.0), close_bottom=True, close_top=True)

    # ---------------------------------------------------------------- the door: rolled flaps tied back, or the closed slit
    if door_open:
        tie = sh.Builder('bell_tent door ties', rope)
        for side in (-1, 1):
            pts, radii = [], []
            for k in range(13):
                z = 0.02 + (Z_DOOR - 0.06) * k / 12
                t = door_theta + side * gap(z)
                base = wall_point(t, z) if z < Z_EAVE + 0.04 else cone_point(t, z)
                ro = 0.075 * (1.0 - z / Z_DOOR) + 0.016
                outward = Vector((math.cos(t), math.sin(t), 0.0))
                tangent = Vector((-math.sin(t), math.cos(t), 0.0)) * side
                pts.append(base + outward * ro * 0.9 + tangent * ro * 0.5)
                radii.append(ro)
            sh.tube(hem.bm, pts, 0.0, sides=8, radii=radii)
            axis = (pts[6] - pts[4]).normalized()
            sh.torus(tie.bm, pts[5], axis, radii[5] + 0.006, 0.007, segments=14, sides=4)
        made.append(tie.finish(collection))
    else:
        outward = Vector((math.cos(door_theta), math.sin(door_theta), 0.0))
        lap = [wall_point(door_theta, 0.02), wall_point(door_theta, WALL_TOP - 0.06), cone_point(door_theta, Z_EAVE + 0.02),
               cone_point(door_theta, Z_DOOR)]
        for a, b in zip(lap[:-1], lap[1:]):
            sh.beam(hem.bm, a + outward * 0.008, b + outward * 0.008, 0.075, 0.012, up=outward)
        toggles = sh.Builder('bell_tent door toggles', 'SURFACE • rough_wood')
        for z in (0.45, 0.95, 1.4):
            base = (wall_point(door_theta, z) if z < Z_EAVE + 0.04 else cone_point(door_theta, z)) + Vector((0, -0.025, 0))
            sh.cylinder(toggles.bm, base + Vector((-0.04, 0, 0)), base + Vector((0.04, 0, 0)), 0.009, segments=6)
        made.append(toggles.finish(collection))

    # ---------------------------------------------------------------- guy ropes, runners and pegs
    ropes = sh.Builder('bell_tent guy ropes', rope)
    pegs = sh.Builder('bell_tent pegs and runners', 'SURFACE • rough_wood')
    for k in range(PANELS):
        if k == 0:
            continue                                          # the door seam carries no guy
        t = door_theta + panel * k + rnd.uniform(-0.012, 0.012)
        out = Vector((math.cos(t), math.sin(t), 0.0))
        side = Vector((-math.sin(t), math.cos(t), 0.0))
        anchor = cone_point(door_theta + panel * k, Z_EAVE) + Vector((0, 0, 0.01))
        reach = R_EAVE + rnd.uniform(1.45, 1.65)
        foot = out * reach
        peg_top = foot + out * 0.07 + Vector((0, 0, 0.19))
        lean_side = side * rnd.uniform(-0.02, 0.02)
        sh.beam(pegs.bm, foot - out * 0.02, peg_top + lean_side, 0.034, 0.024, up=out)
        sh.beam(pegs.bm, peg_top + lean_side - out * 0.012 + Vector((0, 0, -0.035)), peg_top + lean_side + out * 0.03 + Vector((0, 0, -0.01)),
                0.036, 0.02, up=(0, 0, 1))
        tie_point = foot + out * 0.04 + Vector((0, 0, 0.13)) + lean_side
        line = sh.sag_line(anchor, tie_point, rnd.uniform(0.01, 0.03), 10)
        sh.tube(ropes.bm, line, 0.0055, sides=5)
        # the runner (a wooden slider) 0.45 m up the rope from the peg, the doubled rope from it round the peg
        direction = (anchor - tie_point).normalized()
        runner_c = tie_point + direction * 0.45
        sh.beam(pegs.bm, runner_c - direction * 0.065, runner_c + direction * 0.065, 0.032, 0.018, up=side)
        sh.tube(ropes.bm, sh.sag_line(runner_c - direction * 0.05 + side * 0.012, tie_point + side * 0.015, 0.004, 4), 0.005, sides=5)
        sh.torus(ropes.bm, tie_point - out * 0.005, (0, 0, 1), 0.022, 0.005, segments=10, sides=4)
    # small pegs and loops holding the wall's foot, at each seam
    for k in range(PANELS):
        t = door_theta + panel * (k + 0.5)
        if door_open and abs(((t - door_theta + math.pi) % (2 * math.pi)) - math.pi) < panel * 1.2:
            continue
        out = Vector((math.cos(t), math.sin(t), 0.0))
        base = out * (R_WALL + 0.1)
        sh.beam(pegs.bm, base, base + out * 0.04 + Vector((0, 0, 0.11)), 0.026, 0.02, up=out)
        sh.tube(ropes.bm, [out * (R_WALL + 0.045) + Vector((0, 0, 0.06)), base + out * 0.02 + Vector((0, 0, 0.08))], 0.004, sides=4)

    # ---------------------------------------------------------------- pole and the inside
    pole = sh.Grain('bell_tent pole', 'SURFACE • rough_wood', (0, 0, 1), rnd)
    sh.add_cylinder(pole, (0, 0, 0.0), (lean.x, lean.y, Z_TOP + 0.13), 0.036, 0.03, segments=10)
    sh.add_cylinder(pole, (lean.x, lean.y, Z_TOP + 0.13), (lean.x * 1.02, lean.y * 1.02, Z_TOP + 0.2), 0.028, 0.02, segments=8)
    tip = sh.Builder('bell_tent pole tip', 'IRON • soot-black lamp posts')
    sh.cylinder(tip.bm, (lean.x, lean.y, Z_TOP + 0.19), (lean.x, lean.y, Z_TOP + 0.27), 0.013, 0.003, segments=8)
    sh.cylinder(tip.bm, (lean.x, lean.y, Z_TOP + 0.175), (lean.x, lean.y, Z_TOP + 0.2), 0.03, 0.03, segments=10)
    floor = sh.Builder('bell_tent groundsheet', 'RECESSES • near-black blue')
    sh.cylinder(floor.bm, (0, 0, 0.0), (0, 0, 0.008), R_WALL - 0.08, segments=40)
    kit = sh.Builder('bell_tent blankets and kit', 'SURFACE • hessian_380', smooth=True)
    for k in range(6):
        t = door_theta + math.pi * 0.35 + k * (2 * math.pi * 0.65) / 6 + rnd.uniform(-0.1, 0.1)
        out = Vector((math.cos(t), math.sin(t), 0.0))
        side = Vector((-math.sin(t), math.cos(t), 0.0))
        c = out * rnd.uniform(1.3, 1.45) + Vector((0, 0, 0.09))
        r = rnd.uniform(0.085, 0.11)
        sh.cylinder(kit.bm, c - side * 0.38 + Vector((0, 0, r - 0.09)), c + side * 0.38 + Vector((0, 0, r - 0.09)), r, segments=10)
    bag = Vector((math.cos(door_theta + 2.6), math.sin(door_theta + 2.6), 0)) * 1.1
    sh.lathe(kit.bm, [(0.12, 0.0), (0.16, 0.08), (0.165, 0.35), (0.13, 0.5), (0.04, 0.56)], segments=12, centre=(bag.x, bag.y, 0.008))

    for builder in (tent, hem, ropes, pegs, pole, tip, floor, kit):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return [m for m in made if m is not None]
