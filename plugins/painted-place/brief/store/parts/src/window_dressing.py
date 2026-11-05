"""
window_dressing: what hangs in a tenement window, about 1910, sized to the window you name: a roller blind of buff
linen (sometimes green holland) pulled down to a height, on a wooden roller, a lath in its hem and an endless cord
running down the side to a small brass pulley at the sill; or net curtains, greyed with soot, hanging in folds from a
wire and drawn back to a side; or plain heavy curtains in deep folds on a pole with rings, half drawn; or a blind
with nets in front of it. Lit, the cloth glows warm with the room's light coming through it.

It is made to sit in a window opening against the glass: its back is the plane y = 0 and everything hangs in front of
it (towards -Y), within the opening's width and height. The origin is the middle of the opening's foot (the sill).

Options:
    kind     'blind' (default), 'nets', 'curtains' or 'blind and nets'
    width    the window opening's width, metres (default 0.96)
    height   the window opening's height, metres (default 1.62)
    drawn    for a blind, the share of the height it is pulled down; for nets and curtains, the share of the width
             they cover (default 0.5; 0.05 to 1)
    side     'right' (default), 'left' or 'both': the side the nets or curtains hang at (both: two halves meeting
             or parted in the middle); for a blind, the side its cord runs down
    lit      False (default): the room behind dark; True: the cloth lit through, glowing warm
    seed     the blind's cloth (buff or green), the curtains' colour, the folds

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', blinds and net curtains (lines 1552-1617:
blind(), a flat box with a lath and a roller; nets(), folds as turned boxes) and the half-drawn curtain lit through
in the lit windows (lines 525-527). Rebuilt here as hanging cloth in real folds with its fixings.
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

PART = 'window_dressing'
KINDS = ('blind', 'nets', 'curtains', 'blind and nets')
SIDES = ('right', 'left', 'both')

CARD = {
    'name': PART,
    'what': 'what hangs in a window, sized to it: a linen roller blind pulled to a height (cord to a brass pulley at the sill), greyed '
            'net curtains in folds drawn back to a side, plain heavy curtains half drawn on a pole, or a blind with nets; lit through '
            'warm or dark',
    'size_m': (0.92, 0.06, 1.61),
    'options': {
        'kind': "'blind' (default); 'nets'; 'curtains'; 'blind and nets'",
        'width': "the window opening's width, metres (default 0.96)",
        'height': "the window opening's height, metres (default 1.62)",
        'drawn': 'for a blind, the share of the height it is pulled down; for nets and curtains, the share of the width they cover '
                 '(default 0.5; 0.05 to 1)',
        'side': "'right' (default), 'left' or 'both': where the nets or curtains hang (both: two halves); for a blind, the side its cord runs down",
        'lit': 'False (default): dark room behind; True: the cloth lit through from the room, glowing warm',
        'seed': "the blind's cloth (buff or green), the curtains' colour, the folds (default 0)",
    },
    'materials': [street.WOOD, street.BRASS, 'PART • window_dressing: buff linen blind', 'PART • window_dressing: green holland blind',
                  'PART • window_dressing: greyed net', 'PART • window_dressing: curtain cloth', 'PART • window_dressing: blind cord',
                  'PART • window_dressing: <each cloth>, lit through (when lit)'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', blind() and nets() (lines 1552-1617) and the lit windows' "
              "half-drawn curtains (lines 525-527)",
    'views': 'reads from the front (-Y) and from the side; its back is flat, for the glass',
    'trap': "the store's window glass (lay_stone, lay_boards) is an opaque plane, so stand this 2 mm in front of that plane, as the "
            "builders did (it then reads as behind the glass); behind real see-through glass, put its origin 7 cm behind the glass",
}

CURTAIN_COLOURS = [(0.09, 0.02, 0.015), (0.06, 0.035, 0.02), (0.025, 0.042, 0.026), (0.07, 0.05, 0.03)]


def cloth_sheet(shape, x0, x1, z_top, z_bottom, y_back, depth, period, rng, hem_wave=0.01, rows=8, sag=0.0):
    """A hanging cloth in folds from x0 to x1: its folds stand forward of y_back by up to `depth` (towards -Y), one
    fold every `period` metres; the hem a little uneven. One open sheet."""
    cols = max(4, int(abs(x1 - x0) / (period / 6.0)))
    phase = rng.uniform(0, 2 * math.pi)
    hem = [rng.uniform(-hem_wave, hem_wave) for _ in range(cols + 1)]
    grid = []
    for i in range(cols + 1):
        t = i / cols
        x = x0 + (x1 - x0) * t
        fold = 0.5 + 0.5 * math.sin(2 * math.pi * (x - x0) / period + phase)
        column = []
        for j in range(rows + 1):
            s = j / rows                          # 0 at the top, 1 at the hem
            z = z_top + (z_bottom - z_top) * s + hem[i] * s
            z += sag * 4 * t * (1 - t) * s        # a blind's hem hangs a little lower in the middle
            open_out = 0.75 + 0.25 * s            # folds open out a little lower down
            y = y_back - 0.002 - depth * fold * open_out
            column.append(shape.bm.verts.new((x, y, z)))
        grid.append(column)
    for i in range(cols):
        for j in range(rows):
            shape._face([grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]])


def build(collection, seed=0, kind='blind', width=0.96, height=1.62, drawn=0.5, side='right', lit=False):
    street.choice('window_dressing kind', kind, KINDS)
    street.choice('window_dressing side', side, SIDES)
    W = barn.number('window_dressing width', width, 0.3, 4.0)
    H = barn.number('window_dressing height', height, 0.3, 4.0)
    drawn = barn.number('window_dressing drawn', drawn, 0.05, 1.0)
    lit = street.flag('window_dressing lit', lit)
    rng = shapes.rng_for(PART, seed)
    objects = []
    wood = shapes.Shape()
    brass = shapes.Shape()
    x_l, x_r = -W / 2 + 0.02, W / 2 - 0.02

    def cover_spans(share):
        span = (x_r - x_l) * share
        if side == 'left':
            return [(x_l, x_l + span)]
        if side == 'right':
            return [(x_r - span, x_r)]
        return [(x_l, x_l + span / 2), (x_r - span / 2, x_r)]

    if kind in ('blind', 'blind and nets'):
        green = rng.random() < 0.3
        mat = street.cloth(PART, 'green holland blind' if green else 'buff linen blind',
                           (0.035, 0.06, 0.04) if green else (0.21, 0.155, 0.085), lit=lit)
        roller_z = H - 0.045
        ry = -0.028
        wood.cylinder((x_l + 0.02, ry, roller_z), (x_r - 0.02, ry, roller_z), 0.022, segments=12)
        for x in (x_l + 0.01, x_r - 0.01):
            wood.box((x, -0.02, roller_z), (0.02, 0.04, 0.07))                               # brackets
        share = drawn if kind == 'blind' else min(drawn, 0.45)
        hem_z = roller_z - share * (H - 0.11)
        cloth = shapes.Shape()
        cloth_sheet(cloth, x_l + 0.03, x_r - 0.03, roller_z, hem_z, ry - 0.019, 0.004, 0.31, rng, hem_wave=0.004, rows=6, sag=-0.01)
        objects.append(cloth.finish('window_dressing blind', collection, mat, smooth=True, sharp=None))
        wood.box((0.0, ry - 0.026, hem_z - 0.012), (x_r - x_l - 0.05, 0.012, 0.03))           # the lath in the hem
        # the endless cord: from the roller's end down the side to a brass pulley at the sill
        cord_x = (x_r - 0.008) if side != 'left' else (x_l + 0.008)
        cord = shapes.Shape()
        for dy in (-0.012, -0.044):
            cord.cylinder((cord_x, dy, roller_z), (cord_x, dy, 0.035), 0.0022, segments=5)
        objects.append(cord.finish('window_dressing blind cord', collection,
                                   street.cloth(PART, 'blind cord', (0.12, 0.10, 0.07)), smooth=True, sharp=None))
        brass.cylinder((cord_x - 0.006, -0.028, 0.035), (cord_x + 0.006, -0.028, 0.035), 0.019, segments=12)    # the pulley
        brass.box((cord_x, -0.004, 0.025), (0.016, 0.008, 0.05))                                              # its plate on the frame
        brass.cylinder((cord_x - 0.006, -0.028, roller_z), (cord_x + 0.006, -0.028, roller_z), 0.03, segments=12)   # pulley on the roller
    if kind in ('nets', 'blind and nets'):
        net = street.cloth(PART, 'greyed net', (0.30, 0.30, 0.28), sheer=True, lit=lit)
        share = drawn if kind == 'nets' else 1.0
        y_back = -0.052 if kind == 'blind and nets' else -0.006
        nets = shapes.Shape()
        top = H - 0.03
        for (a, b) in cover_spans(share):
            gathered = 0.012 + 0.018 * (1.0 - share)
            cloth_sheet(nets, a, b, top, 0.012, y_back, gathered, 0.07, rng, hem_wave=0.008, rows=8)
        objects.append(nets.finish('window_dressing nets', collection, net, smooth=True, sharp=None))
        brass.cylinder((x_l, y_back - 0.01, top + 0.004), (x_r, y_back - 0.01, top + 0.004), 0.003, segments=6)   # the wire
        for x in (x_l, x_r):
            brass.sphere((x, y_back - 0.01, top + 0.004), 0.007, segments=8, rings=4)
    if kind == 'curtains':
        colour = rng.choice(CURTAIN_COLOURS)
        mat = street.cloth(PART, 'curtain cloth', colour, lit=lit, weave=180.0)
        curtains = shapes.Shape()
        top = H - 0.05
        for (a, b) in cover_spans(drawn):
            cloth_sheet(curtains, a, b, top, 0.01, -0.015, 0.045 + 0.03 * (1.0 - drawn), 0.13, rng, hem_wave=0.012, rows=10)
        objects.append(curtains.finish('window_dressing curtains', collection, mat, smooth=True, sharp=None))
        wood.cylinder((x_l - 0.0, -0.045, H - 0.03), (x_r + 0.0, -0.045, H - 0.03), 0.014, segments=10)          # the pole
        for x in (x_l + 0.015, x_r - 0.015):
            wood.box((x, -0.022, H - 0.03), (0.018, 0.044, 0.03))
        for (a, b) in cover_spans(drawn):
            n = max(3, int((b - a) / 0.08))
            for k in range(n + 1):
                x = a + (b - a) * k / n
                brass.torus((x, -0.045, H - 0.03), 0.02, 0.003, axis=(1.0, 0.0, 0.0), segments=10, sides=4)
    if not wood.empty():
        objects.append(wood.finish('window_dressing timber', collection, street.WOOD, smooth=False))
    else:
        wood.bm.free()
    if not brass.empty():
        objects.append(brass.finish('window_dressing brass', collection, street.BRASS, smooth=True, sharp=40))
    else:
        brass.bm.free()
    return objects
