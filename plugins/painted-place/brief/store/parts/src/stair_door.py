"""
stair_door: the door to a tenement's common stair, about 1910: a heavy panelled door in dark paint, its two upper
panels glazed with obscured glass the stair's gas shows through, two raised panels below, a big brass knob, a keyhole
plate and a letter plate; a door case with a transom and a fanlight over it, its glass lit too; a worn sandstone step
before it, hollowed in the middle where every foot has trodden, its front edge whitened with pipeclay by the women who
scrub it; and a small warm light of its own just outside the glass, so the step, the door's face and the pavement in
front are lit as the stair's light would light them. Unlit, the glass is dark and there is no light.

The origin is the middle of the doorway's foot on the wall's face (y = 0); the wall is at +Y, the door stands 7 cm back
in the opening and the step reaches 0.4 m out in front.

Options:
    width    the doorway's width, metres (default 1.0)
    lit      True (default): the stair lit behind the glass and the small light outside it on; False: dark
    seed     the step's wear, the pipeclay's edge

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the stair lit behind its door (lines
511-519: a glowing fanlight plane, two glowing panes on the door and two point lights in front of it), the door leaves
(lines 494-497) and the doorsteps (line 445). Rebuilt here as a whole panelled door with its case, fanlight, brass and
a worn, whitened step, the light kept with it.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402
import _shapes_street_shop as street  # noqa: E402

PART = 'stair_door'

CARD = {
    'name': PART,
    'what': "a tenement common-stair door: dark panelled door with two obscured glass upper panels lit from the stair, brass knob, "
            "keyhole and letter plates, a door case with a lit fanlight, a worn hollowed sandstone step whitened at its edge, and "
            "its own small warm light outside the glass that lights the step",
    'size_m': (1.35, 0.54, 2.97),
    'options': {
        'width': "the doorway's width, metres (default 1.0)",
        'lit': 'True (default): the glass lit from the stair and a hidden 25 W light just outside it lights the step and the pavement; '
               'False: dark glass, no light',
        'seed': "the step's wear, the pipeclay's edge (default 0)",
    },
    'materials': [street.WOOD, street.STONE, street.BRASS, street.LIT_GLASS, street.DARK_GLASS, 'PART • stair_door: pipeclay'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the stair lit behind its door (lines 511-519), the door "
              "leaves (lines 494-497) and the doorsteps (line 445)",
    'views': 'reads from the front and both sides; its back is the wall',
    'trap': "the light is the part's own and sits 0.3 m outside the glass: at a dark door the step and things set on it read only "
            "where that light reaches; turn it up or down (the object 'stair_door light'), do not take it away",
}

REVEAL = 0.07
DOOR_H = 2.30
FAN_H = 0.44


def pipeclay():
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        n = shapes.noise_fac(nodes, links, vec, 18.0, detail=5.0)
        p.inputs['Base Color'].default_value = (0.42, 0.40, 0.35, 1.0)
        p.inputs['Roughness'].default_value = 0.95
        links.new(shapes.map_range(nodes, links, n, 0.38, 0.55, 0.0, 0.85), p.inputs['Alpha'])
        m.diffuse_color = (0.42, 0.40, 0.35, 1.0)
    return shapes.part_material(PART, 'pipeclay', maker)


def build(collection, seed=0, width=1.0, lit=True):
    W = barn.number('stair_door width', width, 0.7, 2.0)
    lit = street.flag('stair_door lit', lit)
    rng = shapes.rng_for(PART, seed)
    objects = []
    wood = shapes.Shape()
    glass = shapes.Shape()
    brass = shapes.Shape()
    case = 0.10
    top = DOOR_H + 0.08 + FAN_H

    # ------------------------------------------------------------------ the door case, transom and fanlight
    yc = REVEAL - 0.03
    for side in (-1, 1):
        wood.box((side * (W / 2 + case / 2 - 0.02), yc + 0.05, top / 2 + 0.06), (case, 0.10, top + 0.12))
        wood.box((side * (W / 2 + case - 0.01), yc - 0.005, top / 2 + 0.06), (0.03, 0.03, top + 0.12))   # architrave's moulded edge
    wood.box((0.0, yc + 0.05, top + 0.06), (W + 2 * case - 0.04, 0.106, 0.12))
    wood.box((0.0, yc + 0.04, top + 0.13), (W + 2 * case + 0.04, 0.12, 0.03))                          # its cap
    wood.box((0.0, yc + 0.05, DOOR_H + 0.04), (W, 0.094, 0.08))                                        # transom
    fz0, fz1 = DOOR_H + 0.08, top
    bars = 3
    for k in range(1, bars + 1):
        x = -W / 2 + W * k / (bars + 1)
        wood.box((x, yc + 0.06, (fz0 + fz1) / 2), (0.025, 0.04, fz1 - fz0))
    glass.box((0.0, yc + 0.065, (fz0 + fz1) / 2), (W - 0.01, 0.006, fz1 - fz0))

    # ------------------------------------------------------------------ the door: stiles, rails, muntin, raised panels, glazed panels
    dy = REVEAL + 0.025
    dw = W - 0.01
    st = 0.12
    wood.box((-dw / 2 + st / 2, dy, DOOR_H / 2), (st, 0.05, DOOR_H))
    wood.box((dw / 2 - st / 2, dy, DOOR_H / 2), (st, 0.05, DOOR_H))
    for z, h in ((0.11, 0.22), (1.0, 0.18), (DOOR_H - 0.06, 0.12)):
        wood.box((0.0, dy, z), (dw, 0.044, h))
    wood.box((0.0, dy, (0.22 + DOOR_H - 0.12) / 2), (0.10, 0.038, DOOR_H - 0.34))                      # muntin
    pw = (dw - 2 * st - 0.10) / 2
    for side in (-1, 1):
        px = side * (0.05 + pw / 2)
        wood.box((px, dy + 0.005, (0.22 + 0.91) / 2), (pw, 0.03, 0.91 - 0.22))                        # lower panel, sunk
        wood.box((px, dy - 0.012, 0.565), (pw - 0.08, 0.014, 0.53))                                   # raised field
        glass.box((px, dy + 0.006, (1.09 + DOOR_H - 0.12) / 2), (pw, 0.006, DOOR_H - 0.12 - 1.09))
        for zb in (1.09, DOOR_H - 0.12):
            wood.box((px, dy - 0.022, zb), (pw, 0.012, 0.02))                                         # beads holding the glass
    # brass: knob, keyhole plate, letter plate, a bell push on the case
    brass.cylinder((0.0, dy - 0.025, 1.0), (0.0, dy - 0.06, 1.0), 0.012, segments=10)
    brass.sphere((0.0, dy - 0.075, 1.0), 0.032, segments=14, rings=7)
    brass.box((dw / 2 - st / 2, dy - 0.027, 1.06), (0.035, 0.004, 0.08))
    brass.box((0.0, dy - 0.027, 0.78), (0.26, 0.004, 0.06))
    brass.cylinder((W / 2 + case / 2, yc - 0.002, 1.25), (W / 2 + case / 2, yc - 0.012, 1.25), 0.02, segments=10)
    objects.append(wood.finish('stair_door door and case', collection, street.WOOD, smooth=False))
    glass_obj = glass.finish('stair_door glass', collection, street.LIT_GLASS if lit else street.DARK_GLASS, smooth=False)
    objects.append(glass_obj)
    objects.append(brass.finish('stair_door brass', collection, street.BRASS, smooth=True, sharp=40))

    # ------------------------------------------------------------------ the worn step: hollowed where feet go, whitened at its edge
    step = shapes.Shape()
    sw = W + 0.35
    sy0, sy1 = -0.40, REVEAL
    sh = 0.17
    cols, rows = 16, 8
    dip = rng.uniform(0.012, 0.02)
    centre_x = rng.uniform(-0.08, 0.08)
    tops = []
    for i in range(cols + 1):
        x = -sw / 2 + sw * i / cols
        row = []
        for j in range(rows + 1):
            y = sy0 + (sy1 - sy0) * j / rows
            wear = math.exp(-((x - centre_x) / (0.28 * W)) ** 2) * math.exp(-((y - (sy0 + 0.16)) / 0.2) ** 2)
            edge = 0.012 if j == 0 else 0.0
            row.append(Vector((x, y, sh - dip * wear - edge)))
        tops.append(row)
    top_v = [[step.bm.verts.new(p) for p in row] for row in tops]
    for i in range(cols):
        for j in range(rows):
            step._face([top_v[i][j], top_v[i + 1][j], top_v[i + 1][j + 1], top_v[i][j + 1]])
    # the sides and bottom: walls down from the top's edge to z = 0
    ring = [top_v[i][0] for i in range(cols + 1)] + [top_v[cols][j] for j in range(1, rows + 1)] + \
           [top_v[i][rows] for i in range(cols - 1, -1, -1)] + [top_v[0][j] for j in range(rows - 1, 0, -1)]
    bottom = [step.bm.verts.new((v.co.x, v.co.y, 0.0)) for v in ring]
    n = len(ring)
    for k in range(n):
        step._face([ring[k], bottom[k], bottom[(k + 1) % n], ring[(k + 1) % n]])
    step._face(list(reversed(bottom)))
    objects.append(step.finish('stair_door step', collection, street.STONE, smooth=False))
    clay = shapes.Shape()
    for i in range(cols):
        x0, x1 = -sw / 2 + sw * i / cols, -sw / 2 + sw * (i + 1) / cols
        a, b = tops[i][0], tops[i + 1][0]
        a2, b2 = tops[i][1], tops[i + 1][1]
        clay.poly([a + Vector((0, -0.002, 0.002)), b + Vector((0, -0.002, 0.002)), b2 + Vector((0, 0, 0.002)), a2 + Vector((0, 0, 0.002))])
        clay.poly([Vector((a.x, sy0 - 0.002, a.z)), Vector((b.x, sy0 - 0.002, b.z)), Vector((b.x, sy0 - 0.002, sh - 0.07)), Vector((a.x, sy0 - 0.002, sh - 0.07))])
    clay_obj = clay.finish('stair_door pipeclay', collection, pipeclay(), smooth=False, shadow=False)
    objects.append(clay_obj)

    if lit:
        objects.append(street.hidden_light(collection, 'stair_door light', (0.0, -0.30, 1.55), 25.0, radius=0.2))
    return objects
