"""
shop_front: a Victorian shop front for the ground floor of a stone or brick tenement, about 1900-1915, in painted
timber: two pilasters on plinths with capitals, a scroll console on each, a blank fascia board leaning forward between
them (no words, ever), a stepped cornice with a lead flashing on top; under the window a panelled stall riser with a
moulded sill; the big window divided by slender mullions and a transom, small panes over the transom; beside it a door
recessed in a tiled lobby, half glazed with a fanlight, and a worn stone step. Behind the glass the shop itself:
a window bed with a stepped stand and pyramids of tins, a counter, a hanging gas globe, and shelves of jars and tins
on the back wall. Lit, the back wall glows warm, the globe burns and a small hidden light inside lights the goods and
spills out through the glass onto the pavement; dark, it is a shop shut for the night.

The wall is at +Y: the shop front's back lies on the wall face (y = 0), and the shop's inside goes 1.6 m into the
building behind it. The origin is the middle of the front's foot, on the pavement.

Options:
    width    the whole front's width, pilaster to pilaster, metres (default 4.8; at least 2.6)
    lit      True (default): lit inside; False: dark
    door     'right' (default) or 'left': which side the door is, seen from the street
    seed     the goods on the shelves and in the window, the counter's place, the step's wear

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', Building.details(), the shop fronts (lines
446-474: fascia, cornice, pilasters, consoles and stall riser as plain boxes; the lit window an emission plane with
the shelves, jars, tins and counter as flat dark boxes stuck on it, line 461) and the door leaves (line 494). Rebuilt
here with real depth: a shop inside you see into, goods that are things on shelves, a recessed door, mouldings,
consoles and glazing bars, and its own light.
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

PART = 'shop_front'

CARD = {
    'name': PART,
    'what': 'a Victorian shop front in painted timber: pilasters with scroll consoles, a blank leaning fascia (no words), a stepped '
            'cornice, a panelled stall riser, a big window with mullions, a transom and small top panes, a half-glazed door recessed '
            'in a tiled lobby with a fanlight and a stone step; behind the glass a real shop: a window display of tins, a counter, '
            'a gas globe and shelves of jars and tins; lit warm with its own hidden light, or dark',
    'size_m': (4.94, 2.08, 3.53),
    'options': {
        'width': "the whole front's width, pilaster to pilaster, metres (default 4.8; at least 2.6)",
        'lit': 'True (default): the back wall glows, the gas globe burns and a hidden 45 W light inside lights the goods and spills '
               'out onto the pavement; False: shut and dark',
        'door': "'right' (default) or 'left': the side of the door, seen from the street",
        'seed': "the goods on the shelves and in the window, the counter's place, the step's wear (default 0)",
    },
    'materials': [street.WOOD, street.STONE, street.BRASS, 'LAMP • honey flame glow', street.RECESS,
                  'PART • shop_front: grimy window glass', 'PART • shop_front: old lead', 'PART • shop_front: tins and jars',
                  'PART • shop_front: jars, glass', 'PART • shop_front: lamp-lit back wall', 'PART • shop_front: shop walls',
                  'PART • shop_front: lobby tiles', 'PART • shop_front: shop floor boards'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', Building.details(): the shop fronts (lines 446-474), "
              "the lit window's shelves, jars, tins and counter (line 461), the door leaves (line 494)",
    'views': 'reads from the front and both sides; the glass is real, so the shop inside shows from any angle in front; '
             'its back is open into the wall',
    'trap': "the shop's inside goes 1.6 m behind the wall face (+Y): a solid wall there hides it, so cut the wall away behind it; "
            "the part brings a hidden box, 'shop_front opening', for a Boolean (Difference) on your wall",
}

DEPTH = 1.6          # the shop's inside, behind the wall face
PW, PD = 0.32, 0.16  # pilaster width and projection
DW = 1.05            # door opening
POST = 0.14          # the post between window and door
HEAD = 2.70          # window and door head
GLASS_Y = -0.06      # the window glass plane


def lobby_tiles():
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        checker = nodes.new('ShaderNodeTexChecker')
        checker.inputs['Scale'].default_value = 1.0
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (14.0, 14.0, 14.0)
        links.new(vec, mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], checker.inputs['Vector'])
        checker.inputs['Color1'].default_value = (0.20, 0.17, 0.12, 1.0)
        checker.inputs['Color2'].default_value = (0.09, 0.025, 0.018, 1.0)
        dirt = shapes.noise_fac(nodes, links, vec, 6.0, detail=4.0)
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, dirt, 0.4, 0.75, 0.0, 0.7), checker.outputs['Color'], (0.03, 0.025, 0.02))
        links.new(col, p.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, dirt, 0.3, 0.7, 0.25, 0.6), p.inputs['Roughness'])
        m.diffuse_color = (0.14, 0.09, 0.06, 1.0)
    return shapes.part_material(PART, 'lobby tiles', maker)


def plain(what, colour, rough=0.85):
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        n = shapes.noise_fac(nodes, links, vec, 4.0, detail=4.0)
        links.new(shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, n, 0.3, 0.7), tuple(c * 0.7 for c in colour), colour),
                  p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = rough
        m.diffuse_color = tuple(colour) + (1.0,)
    return shapes.part_material(PART, what, maker)


def build(collection, seed=0, width=4.8, lit=True, door='right'):
    W = barn.number('shop_front width', width, 2.6, 12.0)
    lit = street.flag('shop_front lit', lit)
    street.choice('shop_front door', door, ('right', 'left'))
    rng = shapes.rng_for(PART, seed)
    objects = []

    x_l, x_r = -W / 2, W / 2
    xw0 = x_l + PW                     # window from xw0 to xw1, then the post, then the door from xd0 to xd1
    xd1 = x_r - PW
    xd0 = xd1 - DW
    xw1 = xd0 - POST
    win_w = xw1 - xw0
    lights = max(2, int(round(win_w / 1.0)))

    wood = shapes.Shape()      # the painted timber of the front
    inside_wood = shapes.Shape()

    # ------------------------------------------------------------------ pilasters, capitals, consoles
    for side in (-1, 1):
        cx = side * (W / 2 - PW / 2)
        wood.box((cx, -(PD + 0.03) / 2, 0.15), (PW + 0.04, PD + 0.03, 0.30))                 # plinth
        wood.box((cx, -PD / 2, (0.30 + 2.55) / 2), (PW, PD, 2.25))                            # shaft
        for dx in (-0.075, 0.075):
            wood.cylinder((cx + dx, -PD, 0.36), (cx + dx, -PD, 2.49), 0.013, segments=8)      # beads down the shaft
        wood.box((cx, -(PD + 0.035) / 2, 2.585), (PW + 0.03, PD + 0.035, 0.03))              # necking
        wood.box((cx, -(PD + 0.05) / 2, 2.65), (PW + 0.06, PD + 0.05, 0.10))                 # capital
        # the console: a scroll bracket standing on the capital, under the cornice
        outline = [(0.0, 0.0), (0.045, 0.0), (0.06, 0.04), (0.055, 0.10), (0.065, 0.18), (0.095, 0.28), (0.14, 0.37),
                   (0.18, 0.45), (0.205, 0.50), (0.205, 0.58), (0.0, 0.58)]
        frame = Matrix(((0.0, 0.0, 1.0, cx - 0.11), (-1.0, 0.0, 0.0, -0.12), (0.0, 1.0, 0.0, HEAD), (0.0, 0.0, 0.0, 1.0)))
        wood.prism(outline, 0.0, 0.22, matrix=frame)
        for face_x in (cx - 0.112, cx + 0.112):
            wood.torus((face_x, -0.12 - 0.05, HEAD + 0.07), 0.032, 0.011, axis=(1.0, 0.0, 0.0), segments=14, sides=6)
            wood.torus((face_x, -0.12 - 0.14, HEAD + 0.44), 0.05, 0.012, axis=(1.0, 0.0, 0.0), segments=16, sides=6)
        wood.box((cx, -0.12 - 0.105, HEAD + 0.595), (0.25, 0.23, 0.03))                      # its cap block

    # ------------------------------------------------------------------ fascia (blank) and cornice
    f_x0, f_x1 = x_l + PW / 2 + 0.11, x_r - PW / 2 - 0.11
    wood.box((0.0, -0.06, 3.05), (f_x1 - f_x0, 0.12, 0.46))                                   # backing
    wood.box((0.0, -0.15, 3.05), (f_x1 - f_x0, 0.045, 0.46), rotation=Matrix.Rotation(math.radians(10), 3, 'X'))
    wood.cylinder((f_x0, -0.205, 3.27), (f_x1, -0.205, 3.27), 0.022, segments=8)              # beads top and bottom
    wood.cylinder((f_x0, -0.13, 2.835), (f_x1, -0.13, 2.835), 0.02, segments=8)
    wood.box((0.0, -0.063, HEAD + 0.06), (xd1 - xw0 + 0.02, 0.126, 0.12))                       # the head over window and door
    for (z0, z1, out) in ((3.28, 3.34, 0.27), (3.34, 3.44, 0.33), (3.44, 3.50, 0.37)):
        wood.box((0.0, -out / 2, (z0 + z1) / 2), (W + 0.12, out, z1 - z0))
    lead = shapes.Shape()
    lead.box((0.0, -0.18, 3.508), (W + 0.14, 0.42, 0.016), rotation=Matrix.Rotation(math.radians(-3), 3, 'X'))
    lead.cylinder((x_l - 0.07, -0.39, 3.505), (x_r + 0.07, -0.39, 3.505), 0.012, segments=8)  # its rolled front edge

    # ------------------------------------------------------------------ stall riser, sill, window frame, mullions, transom
    wood.box(((xw0 + xw1) / 2, -0.04, 0.35), (win_w, 0.08, 0.70))                              # riser body
    wood.box(((xw0 + xw1) / 2, -0.065, 0.05), (win_w, 0.13, 0.10))                             # plinth
    panel_w = win_w / lights
    for k in range(lights + 1):
        x = xw0 + k * panel_w
        wood.box((min(max(x, xw0 + 0.04), xw1 - 0.04), -0.1, 0.40), (0.08, 0.04, 0.60))       # riser stiles
    wood.box(((xw0 + xw1) / 2, -0.1, 0.13), (win_w, 0.034, 0.06))
    wood.box(((xw0 + xw1) / 2, -0.1, 0.66), (win_w, 0.034, 0.06))
    for k in range(lights):
        a, b = xw0 + k * panel_w + 0.04, xw0 + (k + 1) * panel_w - 0.04
        wood.box(((a + b) / 2, -0.115, 0.395), (b - a - 0.06, 0.02, 0.38))                     # the raised field
    wood.box(((xw0 + xw1) / 2, -0.08, 0.73), (win_w + 0.04, 0.16, 0.06),
             rotation=Matrix.Rotation(math.radians(-6), 3, 'X'))                                 # the window sill
    wood.cylinder((xw0 - 0.02, -0.16, 0.71), (xw1 + 0.02, -0.16, 0.71), 0.02, segments=8)
    for x in (xw0 + 0.03, xw1 - 0.03):
        wood.box((x, -0.05, (0.76 + HEAD) / 2), (0.06, 0.10, HEAD - 0.76))                      # frame posts
    wood.box(((xw1 + xd0) / 2, -0.06, HEAD / 2), (POST, 0.12, HEAD))                            # post between window and door
    mull_x = [xw0 + 0.06 + (win_w - 0.12) * k / lights for k in range(1, lights)]
    for x in mull_x:
        wood.box((x, GLASS_Y, (0.76 + HEAD) / 2), (0.05, 0.07, HEAD - 0.76))
    T0, T1 = 2.24, 2.30
    wood.box(((xw0 + xw1) / 2, GLASS_Y, (T0 + T1) / 2), (win_w - 0.1, 0.062, T1 - T0))           # transom
    edges = [xw0 + 0.06] + mull_x + [xw1 - 0.06]
    glass = shapes.Shape()
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = a + 0.025, b - 0.025
        glass.box(((a2 + b2) / 2, GLASS_Y, (0.76 + T0) / 2), (b2 - a2 + 0.01, 0.006, T0 - 0.76))
        mid = (a2 + b2) / 2
        wood.box((mid, GLASS_Y, (T1 + HEAD) / 2), (0.03, 0.05, HEAD - T1))                       # top lights in two
        for c, d in ((a2, mid - 0.015), (mid + 0.015, b2)):
            glass.box(((c + d) / 2, GLASS_Y, (T1 + HEAD) / 2), (d - c + 0.01, 0.006, HEAD - T1))

    # ------------------------------------------------------------------ the lobby, the door, the fanlight, the step
    LOBBY = 0.55
    ld0, ld1 = xd0 + 0.06, xd1 - 0.06
    for x, face in ((xd0 + 0.03, 1.0), (xd1 - 0.03, -1.0)):
        wood.box((x, (GLASS_Y + LOBBY) / 2, HEAD / 2), (0.06, LOBBY - GLASS_Y, HEAD))             # lobby walls
        for z0, z1 in ((0.15, 0.95), (1.1, 2.5)):                                                  # their raised panels
            wood.box((x + face * 0.031, (GLASS_Y + LOBBY) / 2, (z0 + z1) / 2), (0.006, LOBBY - GLASS_Y - 0.14, z1 - z0))
    wood.box(((xd0 + xd1) / 2, (GLASS_Y + LOBBY) / 2, HEAD - 0.025), (DW, LOBBY - GLASS_Y, 0.05))   # lobby ceiling
    tiles = shapes.Shape()
    tiles.box(((ld0 + ld1) / 2, (GLASS_Y + LOBBY) / 2, 0.11), (ld1 - ld0, LOBBY - GLASS_Y, 0.02))
    door_w = ld1 - ld0 - 0.01
    dcx = (ld0 + ld1) / 2
    dy = LOBBY + 0.025
    wood.box((dcx, dy + 0.04, 2.21), (ld1 - ld0, 0.072, 0.06))                                    # the door's transom
    for x in (ld0 + 0.02, ld1 - 0.02):
        wood.box((x, dy + 0.04, HEAD / 2), (0.04, 0.08, HEAD))                                   # door case
    wood.box((dcx - door_w / 2 + 0.05, dy, 1.15), (0.10, 0.05, 2.06))                            # stiles
    wood.box((dcx + door_w / 2 - 0.05, dy, 1.15), (0.10, 0.05, 2.06))
    for z, hgt in ((0.20, 0.20), (0.98, 0.12), (2.12, 0.10)):
        wood.box((dcx, dy, z), (door_w, 0.044, hgt))                                             # rails
    wood.box((dcx, dy + 0.004, 0.62), (door_w - 0.2, 0.036, 0.62))                                        # the lower panel
    wood.box((dcx, dy - 0.03, 0.62), (door_w - 0.32, 0.02, 0.5))
    wood.box((dcx, dy - 0.01, 1.55), (0.025, 0.035, 1.02))                                       # its glazing bar
    glass.box((dcx, dy, 1.555), (door_w - 0.19, 0.006, 1.04))
    glass.box((dcx, dy + 0.04, (2.24 + HEAD - 0.05) / 2), (ld1 - ld0 - 0.08, 0.006, HEAD - 0.05 - 2.24))   # fanlight
    wood.box((dcx, dy + 0.035, (2.24 + HEAD - 0.05) / 2), (0.025, 0.04, HEAD - 0.05 - 2.24))
    brass = shapes.Shape()
    kx = dcx + door_w / 2 - 0.09
    brass.cylinder((kx, dy - 0.025, 1.0), (kx, dy - 0.07, 1.0), 0.008, segments=8)
    brass.sphere((kx, dy - 0.08, 1.0), 0.026, segments=12, rings=6)
    brass.box((kx, dy - 0.028, 0.93), (0.03, 0.006, 0.06))
    brass.box((dcx, dy - 0.028, 1.06), (0.3, 0.004, 0.02))                                       # the push plate's rail
    step = shapes.Shape()
    sw = DW + 0.12
    step.box(((xd0 + xd1) / 2, (-0.42 + GLASS_Y) / 2, 0.055), (sw, GLASS_Y + 0.42, 0.11))
    step.chamfer_all(0.015)
    stone_step = step.finish('shop_front step', collection, street.STONE, smooth=False)
    objects.append(stone_step)

    # ------------------------------------------------------------------ the shop inside: shell, back wall, shelves, counter
    sx0, sx1 = xw0, xd1
    walls = shapes.Shape()
    walls.box(((sx0 + sx1) / 2, DEPTH / 2, 0.06), (sx1 - sx0, DEPTH, 0.12))                       # floor slab
    walls.box(((sx0 + sx1) / 2, DEPTH / 2, 2.93), (sx1 - sx0, DEPTH, 0.06))                       # ceiling
    walls.box((sx0 - 0.03, (DEPTH + 0.06 + GLASS_Y) / 2, 1.5), (0.06, DEPTH + 0.06 - GLASS_Y, 3.0))   # side walls
    walls.box((sx1 + 0.03, (DEPTH + 0.06 + LOBBY) / 2, 1.5), (0.06, DEPTH + 0.06 - LOBBY, 3.0))
    walls.box(((sx0 + sx1) / 2, DEPTH + 0.05, 1.5), (sx1 - sx0, 0.02, 3.0))                         # behind the back wall
    walls.box(((sx0 + sx1) / 2, 0.01, 2.81), (sx1 - sx0, 0.02, 0.18))                             # inside over the window head
    floor = shapes.Shape()
    floor.box(((sx0 + sx1) / 2, (0.45 + DEPTH) / 2, 0.125), (sx1 - sx0, DEPTH - 0.45, 0.01))
    back = shapes.Shape()
    back.box(((sx0 + sx1) / 2, DEPTH + 0.02, 1.5), (sx1 - sx0, 0.04, 2.88))
    # the window bed and its stepped stand
    inside_wood.box(((xw0 + xw1) / 2, (GLASS_Y + 0.45) / 2, 0.73), (win_w, 0.45 - GLASS_Y, 0.06))
    inside_wood.box(((xw0 + xw1) / 2, 0.45, 0.4), (win_w, 0.03, 0.66))
    stand_w = min(1.0, win_w * 0.34)
    stand_x = xw0 + win_w * rng.uniform(0.42, 0.58)
    for k, (y0, z) in enumerate(((0.06, 0.88), (0.17, 1.0), (0.28, 1.12))):
        inside_wood.box((stand_x, (y0 + 0.40) / 2, (0.76 + z) / 2), (stand_w - 0.12 * k, 0.40 - y0, z - 0.76))
    # shelves on the back wall
    shelf_z = [1.05, 1.45, 1.85, 2.25]
    for z in shelf_z:
        inside_wood.box(((sx0 + sx1) / 2, DEPTH - 0.14, z), (sx1 - sx0 - 0.1, 0.28, 0.03))
    for x in (sx0 + 0.04, sx1 - 0.04, (sx0 + sx1) / 2):
        inside_wood.box((x, DEPTH - 0.14, 1.7), (0.03, 0.28, 1.4))
    inside_wood.box(((sx0 + sx1) / 2, DEPTH - 0.2, 0.5), (sx1 - sx0 - 0.1, 0.4, 0.75))           # drawers under the shelves
    for k in range(int((sx1 - sx0) / 0.45)):
        x = sx0 + 0.3 + k * 0.45
        if x < sx1 - 0.2:
            brass_knob = (x, DEPTH - 0.405, 0.62)
            brass.sphere(brass_knob, 0.012, segments=8, rings=4)
    # the counter
    c_len = min(2.2, (sx1 - sx0) * 0.55)
    c_x0 = sx0 + rng.uniform(0.2, 0.4)
    cy0, cy1 = 0.80, 1.18
    inside_wood.box((c_x0 + c_len / 2, (cy0 + cy1) / 2, 0.55), (c_len, cy1 - cy0, 0.86))
    inside_wood.box((c_x0 + c_len / 2, (cy0 + cy1) / 2, 0.995), (c_len + 0.06, cy1 - cy0 + 0.06, 0.03))
    for k in range(int(c_len / 0.5) + 1):
        inside_wood.box((c_x0 + 0.05 + k * (c_len - 0.1) / max(1, int(c_len / 0.5)), cy0 - 0.01, 0.55), (0.05, 0.02, 0.8))
    # brass scales on the counter
    scx = c_x0 + c_len * 0.3
    brass.box((scx, (cy0 + cy1) / 2, 1.03), (0.3, 0.16, 0.04))
    brass.cylinder((scx, (cy0 + cy1) / 2, 1.05), (scx, (cy0 + cy1) / 2, 1.25), 0.012, segments=8)
    brass.box((scx, (cy0 + cy1) / 2, 1.25), (0.34, 0.02, 0.015))
    for dx in (-0.16, 0.16):
        brass.cylinder((scx + dx, (cy0 + cy1) / 2, 1.05), (scx + dx, (cy0 + cy1) / 2, 1.075), 0.07, 0.085, segments=14)

    # ------------------------------------------------------------------ goods: tins and jars on the shelves, in the window, on the counter
    tins = shapes.Shape()
    jars = shapes.Shape()
    barn.number_layers(tins, faces=('tone',))
    barn.number_layers(jars, faces=('tone',))

    def tone_new(shape, before, value):
        shape.bm.faces.ensure_lookup_table()
        barn.face_numbers(shape, [shape.bm.faces[i] for i in range(before, len(shape.bm.faces))], tone=value)

    def tin(x, y, z, r, h, round_tin=True):
        before = len(tins.bm.faces)
        if round_tin:
            tins.cylinder((x, y, z), (x, y, z + h), r, segments=12)
        else:
            tins.box((x, y, z + h / 2), (r * 2, r * 1.6, h))
        tone_new(tins, before, rng.choice((0.05, 0.25, 0.4, 0.55, 0.7, 0.82)))
        before = len(tins.bm.faces)
        if round_tin and rng.random() < 0.6:
            tins.cylinder((x, y, z + h * 0.3), (x, y, z + h * 0.7), r + 0.002, segments=12)    # a paper label
            tone_new(tins, before, 0.95)

    def jar(x, y, z, r, h):
        before = len(jars.bm.faces)
        jars.lathe([(0.0, 0.0), (r, 0.0), (r, h * 0.82), (r * 0.7, h * 0.9), (r * 0.7, h), (0.0, h)], segments=12,
                   matrix=Matrix.Translation((x, y, z)))
        tone_new(jars, before, rng.random())
        before = len(tins.bm.faces)
        tins.cylinder((x, y, z + h * 0.9), (x, y, z + h + 0.02), r * 0.74, segments=12)             # the lid
        tone_new(tins, before, rng.choice((0.4, 0.55, 0.82)))

    for z in shelf_z:
        x = sx0 + 0.1
        while x < sx1 - 0.16:
            if rng.random() < 0.45:
                r = rng.uniform(0.045, 0.065)
                jar(x + r, DEPTH - 0.14 + rng.uniform(-0.04, 0.04), z + 0.015, r, rng.uniform(0.16, 0.27))
                x += 2 * r + rng.uniform(0.015, 0.05)
            elif rng.random() < 0.88:
                r = rng.uniform(0.035, 0.06)
                h = min(0.36, rng.uniform(0.08, 0.2))
                round_tin = rng.random() < 0.7
                tin(x + r, DEPTH - 0.14 + rng.uniform(-0.05, 0.05), z + 0.015, r, h, round_tin)
                if round_tin and rng.random() < 0.4 and h < 0.13:
                    tin(x + r, DEPTH - 0.14, z + 0.015 + h + 0.002, r, h, True)                        # stacked two high
                x += 2 * r + rng.uniform(0.01, 0.04)
            else:
                x += rng.uniform(0.1, 0.3)
    # pyramids of tins in the window, either side of the stand
    for px in (xw0 + 0.25 + rng.uniform(0.0, 0.15), xw1 - 0.6 - rng.uniform(0.0, 0.15)):
        r = 0.045
        rows = 4
        for row in range(rows):
            for k in range(rows - row):
                tin(px + (2 * k + row) * (r + 0.002), 0.08 + rng.uniform(-0.01, 0.01), 0.76 + row * 0.105, r, 0.10, True)
    for k, (y0, z) in enumerate(((0.06, 0.88), (0.17, 1.0), (0.28, 1.12))):
        w_here = stand_w - 0.12 * k
        x = stand_x - w_here / 2 + 0.06
        while x < stand_x + w_here / 2 - 0.08:
            if rng.random() < 0.5:
                jar(x + 0.05, y0 + 0.07, z, 0.05, rng.uniform(0.16, 0.22))
                x += 0.13
            else:
                tin(x + 0.045, y0 + 0.07, z, 0.045, rng.uniform(0.08, 0.14), True)
                x += 0.11
    for k in range(3):
        jar(c_x0 + c_len * (0.62 + 0.12 * k), (cy0 + cy1) / 2, 1.01, 0.06, rng.uniform(0.2, 0.28))

    # ------------------------------------------------------------------ the gas globe and the light
    gx = (sx0 + sx1) / 2 + rng.uniform(-0.3, 0.3)
    gy = 0.62
    iron = shapes.Shape()
    iron.cylinder((gx, gy, 2.9), (gx, gy, 2.42), 0.008, segments=6)
    iron.cylinder((gx, gy, 2.44), (gx, gy, 2.38), 0.04, 0.05, segments=12)
    globe = shapes.Shape()
    globe.sphere((gx, gy, 2.30), 0.085, segments=16, rings=8)

    # ------------------------------------------------------------------ out
    objects.append(wood.finish('shop_front timber', collection, street.WOOD, smooth=False))
    objects.append(inside_wood.finish('shop_front shop fittings', collection, street.WOOD, smooth=False))
    objects.append(lead.finish('shop_front lead flashing', collection, street.lead(PART), smooth=True, sharp=40))
    glass_obj = glass.finish('shop_front glass', collection, street.see_through_glass(PART), smooth=False)
    glass_obj.visible_shadow = False
    objects.append(glass_obj)
    objects.append(brass.finish('shop_front brass', collection, street.BRASS, smooth=True, sharp=40))
    objects.append(tiles.finish('shop_front lobby tiles', collection, lobby_tiles(), smooth=False))
    objects.append(walls.finish('shop_front shop walls', collection, plain('shop walls', (0.20, 0.15, 0.09)), smooth=False))
    objects.append(floor.finish('shop_front shop floor', collection, plain('shop floor boards', (0.07, 0.045, 0.025), rough=0.6), smooth=False))
    if lit:
        back_mat = street.glow(PART, 'lamp-lit back wall', (1.0, 0.5, 0.17), 0.8, 2.9, 0.5, 2.6)
    else:
        back_mat = plain('shop walls', (0.20, 0.15, 0.09))
    objects.append(back.finish('shop_front back wall', collection, back_mat, smooth=False))
    objects.append(tins.finish('shop_front tins', collection, street.goods(PART), smooth=True, sharp=40))
    objects.append(jars.finish('shop_front jars', collection, street.jar_glass(PART), smooth=True, sharp=50))
    objects.append(iron.finish('shop_front gas pendant', collection, street.IRON, smooth=True, sharp=40))
    globe_obj = globe.finish('shop_front gas globe', collection, 'LAMP • honey flame glow' if lit else street.jar_glass(PART), smooth=True)
    globe_obj.visible_shadow = False
    objects.append(globe_obj)
    lights = []
    if lit:
        lights.append(street.hidden_light(collection, 'shop_front light', (gx, gy, 2.2), 45.0, radius=0.1))
        lights.append(street.hidden_light(collection, 'shop_front window light', ((xw0 + xw1) / 2, 0.1, 2.55), 15.0, radius=0.2))
    # the hidden box a builder may cut the wall with
    cutter = shapes.Shape()
    cutter.box(((sx0 + sx1) / 2, (DEPTH + 0.06) / 2 - 0.02, 1.5), (sx1 - sx0 + 0.02, DEPTH + 0.06, 3.0))
    cut = cutter.finish('shop_front opening', collection, street.RECESS, smooth=False, shadow=False)
    cut.hide_render = True
    cut.display_type = 'WIRE'
    objects.append(cut)

    if door == 'left':
        flip = Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0))
        for obj in objects:
            obj.data.transform(flip)
            obj.data.flip_normals()
        for light in lights:
            light.matrix_world = flip @ light.matrix_world
    return objects + lights
