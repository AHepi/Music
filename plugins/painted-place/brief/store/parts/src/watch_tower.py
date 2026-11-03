"""
watch_tower: a 1914-18 camp watch tower of rough timber: four splayed legs standing in sandbags, girts at four
levels and cross bracing on every face, a ladder up the front, a boarded platform at 5 m with a rail and a parapet
of sandbags (a gap left where the ladder comes up), corner posts carrying a corrugated iron roof with a ridge roll.

Options:
  height      the platform's height in metres (default 5.0; the roof's ridge is about 2.7 m above it)
  seed        small differences: timber sizes and lean, sandbags

About 4.0 m square with the sandbags at its feet, 8.0 m high. The ladder faces -Y. Foot at z = 0, centred on the origin.

Made for the store from `tower` in '50 first pass - render_final.py' (line 436) and '50 second pass - render_final.py'
(line 583), and the timber tower in '46 military-base - render_final.py' (`far_end`, line 743); rebuilt at camp size
so every face has its bracing and the ladder, rail and parapet read from all sides.
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'watch_tower',
    'what': 'a timber camp watch tower: braced legs, ladder, boarded platform with rail and sandbag parapet, iron roof',
    'size_m': (4.04, 4.15, 7.96),
    'options': {
        'height': "the platform's height in metres (default 5.0; the roof's ridge is about 2.7 m above it)",
        'seed': 'timber sizes and lean, sandbags (default 0)',
    },
    'materials': ['SURFACE • rough_wood (watch_tower)', 'SURFACE • old_planks_02', 'SURFACE • hessian_380 (watch_tower)',
                  'SURFACE • worn_corrugated_iron', 'SURFACE • rusty_metal_02'],
    'source': "`tower` in '50 first pass - render_final.py' (line 436) and '50 second pass' (line 583); the tower in "
              "'46 military-base - render_final.py' (far_end, line 743)",
    'views': 'reads from every side',
    'trap': 'The ladder stands 0.5 m out in front of the legs (-Y): leave room for it.',
}

PART = 'watch_tower'


def build(collection, seed=0, height=5.0, **_ignored):
    rnd = sh.rand(seed, PART)
    zp = max(3.0, float(height))
    wood = sh.copy_surface('SURFACE • rough_wood', PART, mud_height=0.35)
    bags = sh.copy_surface('SURFACE • hessian_380', PART, mud_height=0.3, grime=0.6, darken=0.22)
    b0, b1 = 1.55, 1.1                     # half the legs' spread at the ground and at the platform

    def leg(sx, sy, z):
        f = z / zp
        h = b0 + (b1 - b0) * f
        return Vector((sx * h, sy * h, z))

    vertical = sh.Grain('watch_tower legs and posts', wood, (0, 0, 1), rnd)
    along_x = sh.Grain('watch_tower girts and rails along', wood, (1, 0, 0), rnd)
    along_y = sh.Grain('watch_tower girts and rails across', wood, (0, 1, 0), rnd)
    braces = []                            # one object per brace, so each object's box fits its timber

    def brace(p0, p1, out):
        g = sh.Grain('watch_tower brace %d' % (len(braces) + 1), wood, Vector(p1) - Vector(p0), rnd, x_hint=out.cross(Vector((0, 0, 1))))
        sh.add_beam(g, p0, p1, 0.1, 0.05, up=out)
        braces.append(g)

    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for sx, sy in corners:
        size = rnd.uniform(0.19, 0.22)
        foot, head = leg(sx, sy, 0.0), leg(sx, sy, zp - 0.2)      # flat-footed on the ground, flat-topped under the bearer
        ring = ((-1, -1), (1, -1), (1, 1), (-1, 1))
        sh.add_hexahedron(vertical, [(foot.x + i * size / 2, foot.y + j * size / 2, 0.0) for i, j in ring] +
                          [(head.x + i * size / 2, head.y + j * size / 2, head.z) for i, j in ring])
    levels = [0.35, zp * 0.38, zp * 0.69, zp - 0.17]
    faces = (((-1, -1), (1, -1), along_x, 'x'), ((-1, 1), (1, 1), along_x, 'x'), ((-1, -1), (-1, 1), along_y, 'y'), ((1, -1), (1, 1), along_y, 'y'))
    for (ax, ay), (bx, by), girt_builder, axis in faces:
        out = Vector((0, ay, 0)) if axis == 'x' else Vector((ax, 0, 0))
        for z in levels:
            p0, p1 = leg(ax, ay, z) + out * 0.13, leg(bx, by, z) + out * 0.13
            d = (p1 - p0).normalized()
            sh.add_beam(girt_builder, p0 - d * 0.15, p1 + d * 0.15, 0.06, 0.15, up=(0, 0, 1))
        for z0, z1 in zip(levels[:-1], levels[1:]):
            lo_a, hi_b = leg(ax, ay, z0 + 0.08) + out * 0.17, leg(bx, by, z1 - 0.08) + out * 0.17
            lo_b, hi_a = leg(bx, by, z0 + 0.08) + out * 0.2, leg(ax, ay, z1 - 0.08) + out * 0.2
            brace(lo_a, hi_b, out)
            brace(lo_b, hi_a, out)

    # ---------------------------------------------------------------- platform: frame, boards, rail, roof posts
    half = 1.45
    floor = sh.Grain('watch_tower platform boards', 'SURFACE • old_planks_02', (1, 0, 0), rnd)
    for sy in (-1, 1):                     # bearers resting on the legs' tops
        sh.add_box(along_x, (-half, sy * b1 - 0.1, zp - 0.2), (half, sy * b1 + 0.1, zp))
    sh.add_box(along_x, (-half, -half, zp - 0.2), (half, -half + 0.12, zp))
    sh.add_box(along_x, (-half, half - 0.12, zp - 0.2), (half, half, zp))
    sh.add_box(along_y, (-half + 0.12, -half + 0.12, zp - 0.2), (-half + 0.24, half - 0.12, zp))
    sh.add_box(along_y, (half - 0.24, -half + 0.12, zp - 0.2), (half - 0.12, half - 0.12, zp))
    sh.add_box(along_y, (-0.06, -half + 0.12, zp - 0.2), (0.06, half - 0.12, zp))
    n_boards = 13
    width_b = 2 * half / n_boards
    for k in range(n_boards):
        y0 = -half + k * width_b + 0.004
        dz = rnd.uniform(-0.004, 0.004)
        sh.add_box(floor, (-half - rnd.uniform(0.0, 0.04), y0, zp + dz), (half + rnd.uniform(0.0, 0.04), y0 + width_b - 0.008, zp + 0.04 + dz))
    zf = zp + 0.04
    rail_top, rail_mid, post_top = zf + 1.05, zf + 0.55, zf + 2.0
    gap = (0.2, 0.85)                      # where the ladder comes up through the rail, front side
    for x in (-half + 0.05, 0.0, half - 0.05):
        for y in (-half + 0.05, half - 0.05):
            if x == 0.0 and y < 0:
                continue
            top = post_top if abs(x) > 0.1 else rail_top
            sh.add_beam(vertical, (x, y, zf - 0.22), (x, y, top), 0.11, 0.11, up=(0, 1, 0))
    for y in (0.0,):
        for x in (-half + 0.05, half - 0.05):
            sh.add_beam(vertical, (x, y, zf - 0.22), (x, y, rail_top), 0.11, 0.11, up=(0, 1, 0))
    for x in gap:
        sh.add_beam(vertical, (x, -half + 0.05, zf - 0.22), (x, -half + 0.05, rail_top), 0.1, 0.1, up=(0, 1, 0))
    for z in (rail_mid, rail_top):
        sh.add_box(along_x, (-half, half - 0.11, z - 0.05), (half, half + 0.0, z + 0.05))
        sh.add_box(along_x, (-half, -half, z - 0.05), (gap[0] + 0.05, -half + 0.11, z + 0.05))
        sh.add_box(along_x, (gap[1] - 0.05, -half, z - 0.05), (half, -half + 0.11, z + 0.05))
        sh.add_box(along_y, (-half, -half, z - 0.05), (-half + 0.11, half, z + 0.05))
        sh.add_box(along_y, (half - 0.11, -half, z - 0.05), (half, half, z + 0.05))
    # roof plates on the corner posts
    sh.add_box(along_x, (-half - 0.08, -half - 0.02, post_top), (half + 0.08, -half + 0.12, post_top + 0.15))
    sh.add_box(along_x, (-half - 0.08, half - 0.12, post_top), (half + 0.08, half + 0.02, post_top + 0.15))

    # ---------------------------------------------------------------- sandbag parapet inside the rail, footings
    sand = sh.Builder('watch_tower sandbags', bags, smooth=True)
    runs = [((-half + 0.2, -half + 0.2), (gap[0] - 0.1, -half + 0.2)), ((gap[1] + 0.1, -half + 0.2), (half - 0.2, -half + 0.2)),
            ((half - 0.2, -half + 0.45), (half - 0.2, half - 0.45)), ((-half + 0.2, half - 0.2), (half - 0.2, half - 0.2)),
            ((-half + 0.2, -half + 0.45), (-half + 0.2, half - 0.45))]
    for course in range(2):
        for (x0, y0), (x1, y1) in runs:
            a, b = Vector((x0, y0, 0)), Vector((x1, y1, 0))
            span = (b - a).length
            if span < 0.3:
                continue
            n = max(1, int(round(span / 0.5)))
            turn = math.atan2(b.y - a.y, b.x - a.x)
            for k in range(n):
                t = (k + 0.5 + (0.5 if course else 0.0)) / n
                if t > 1.0:
                    continue
                c = a.lerp(b, min(t, 1.0))
                sh.sandbag(sand.bm, (c.x + rnd.uniform(-0.02, 0.02), c.y + rnd.uniform(-0.02, 0.02), zf + 0.1 + course * 0.17),
                           0.5 * rnd.uniform(0.92, 1.04), 0.26, 0.24, turn + rnd.uniform(-0.08, 0.08), rnd, tied=rnd.choice((-1, 1)))
    for sx, sy in corners:
        foot = leg(sx, sy, 0.0)
        for k in range(3):
            a = math.atan2(sy, sx) + (k - 1) * 1.2 + rnd.uniform(-0.15, 0.15)
            c = foot + Vector((math.cos(a), math.sin(a), 0)) * 0.32
            sh.sandbag(sand.bm, (c.x, c.y, 0.1), 0.5, 0.26, 0.24, a + math.pi / 2, rnd)
        sh.sandbag(sand.bm, (foot.x - sx * 0.05, foot.y + sy * 0.3, 0.27), 0.48, 0.25, 0.22, math.atan2(sy, sx), rnd, slump=0.02)

    # ---------------------------------------------------------------- ladder up the front face
    lad = Vector((0.0, -1.0, 0.0))
    bottom_y, edge_y, top_z = -b0 - 0.5, -half - 0.1, zf + 0.95
    top_y = bottom_y + (edge_y - bottom_y) * top_z / zf
    rise = Vector((0.0, top_y - bottom_y, top_z))
    stiles = sh.Grain('watch_tower ladder stiles', wood, rise.normalized(), rnd, x_hint=(1, 0, 0))
    rungs = sh.Grain('watch_tower ladder rungs', wood, (1, 0, 0), rnd)
    for x in (gap[0] + 0.07, gap[1] - 0.07):
        sh.add_beam(stiles, (x, bottom_y, 0.0), (x, top_y, top_z), 0.05, 0.1, up=lad)
    k = 1
    while True:
        f = (0.3 * k) / top_z
        if 0.3 * k > zf - 0.1:
            break
        p = Vector((0.0, bottom_y, 0.0)) + rise * f
        sh.add_cylinder(rungs, (gap[0] + 0.05, p.y, p.z), (gap[1] - 0.05, p.y, p.z), 0.02, segments=6)
        k += 1

    # ---------------------------------------------------------------- roof: two corrugated iron slopes, ridge roll, barge boards
    pitch = math.radians(22.0)
    over = 0.3
    hw = half + over
    z_eave = post_top + 0.15
    rise_r = hw * math.tan(pitch)
    roof = {}
    rafter_groups = []
    for side in (-1, 1):
        shift = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.0))
        matrix = Matrix.Translation(shift) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
        roof[side] = sh.Builder('watch_tower roof %s' % ('front' if side < 0 else 'back'), 'SURFACE • worn_corrugated_iron', matrix=matrix)
        ring_eave = [(x, side * hw, z_eave + dz) for x, dz in ((-hw, 0.0), (hw, 0.0), (hw, 0.012), (-hw, 0.012))]
        ring_ridge = [(x, 0.0, z_eave + rise_r + dz) for x, dz in ((-hw, 0.0), (hw, 0.0), (hw, 0.012), (-hw, 0.012))]
        sh.add_hexahedron(roof[side], ring_eave + ring_ridge)
        # rafters under it, resting on the plates
        rafters = sh.Grain('watch_tower rafters %s' % ('front' if side < 0 else 'back'), wood, (0, -side * math.cos(pitch), math.sin(pitch)), rnd)
        rafter_groups.append(rafters)
        for x in (-half, -0.5, 0.5, half):
            sh.add_beam(rafters, (x, side * (hw - 0.05), z_eave - 0.06), (x, 0.0, z_eave + rise_r - 0.06), 0.05, 0.1,
                        up=(0, -side * math.sin(pitch), math.cos(pitch)))
    trim = sh.Builder('watch_tower ridge roll', 'SURFACE • rusty_metal_02')
    sh.cylinder(trim.bm, (-hw - 0.01, 0, z_eave + rise_r + 0.012), (hw + 0.01, 0, z_eave + rise_r + 0.012), 0.035, segments=10)
    for x in (-hw - 0.01, hw + 0.01):
        for side in (-1, 1):
            sh.add_beam(along_y, (x, side * hw, z_eave - 0.1), (x, 0.0, z_eave + rise_r - 0.1), 0.03, 0.18,
                        up=(0, -side * math.sin(pitch), math.cos(pitch)))

    made = []
    for builder in (vertical, along_x, along_y, *braces, floor, sand, stiles, rungs, roof[-1], roof[1], trim, *rafter_groups):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return made
