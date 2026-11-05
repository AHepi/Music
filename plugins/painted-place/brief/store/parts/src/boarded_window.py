"""
boarded_window: a tenement's common-stair window that nobody mends, about 1915: a two-over-two sash window set back in
its opening, its lower panes broken a year ago (a few shards still in the corners, the dark stair behind), sawn boards
nailed across the opening over the lower sash, their ends on the jambs, and one more board nailed across the corner
pane above where the glass cracked too; rough grey boards, each its own shade, rusty nail heads with rust run under
them.

The origin is the middle of the opening's foot, on the wall's face (y = 0): the boards lie on that face and reach
0.15 m past the opening on each side; the window frame stands 6 cm back in the opening (+Y).

Options:
    width    the opening's width, metres (default 0.96)
    height   the opening's height, metres (default 1.62)
    boards   how many boards across the lower sash (default 4; 2 to 6)
    corner   True (default): a board across the cracked corner pane above; False: the upper sash left whole
    seed     the boards' lengths, tilts and shades, which shards are left, the rust

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the stair window, boarded (lines
1618-1634): four boxes in 'SURFACE • rough_wood' with box nail heads over a glass plane. Rebuilt here with the sash
window itself, its broken panes and shards, boards as sawn timber each its own shade, round nail heads and rust runs.
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

PART = 'boarded_window'

CARD = {
    'name': PART,
    'what': 'a stair window nobody mends: a two-over-two sash set back in its opening, the lower panes broken (shards left in the '
            'corners, the dark stair behind), sawn boards nailed across over them and one across the cracked corner pane above, '
            'rusty nail heads with rust run under them',
    'size_m': (1.27, 0.23, 1.63),
    'options': {
        'width': "the opening's width, metres (default 0.96)",
        'height': "the opening's height, metres (default 1.62)",
        'boards': 'how many boards across the lower sash (default 4; 2 to 6)',
        'corner': 'True (default): a board nailed across the cracked corner pane above; False: the upper sash left whole',
        'seed': "the boards' lengths, tilts and shades, which shards are left, the rust (default 0)",
    },
    'materials': ['SURFACE • rough_wood (boarded_window), each board its own shade', street.WOOD, street.DARK_GLASS, street.RECESS,
                  street.NAILS, street.STAIN],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the stair window, boarded (lines 1618-1634)",
    'views': 'reads from the front and both sides; from behind only the frame and the dark backing show',
    'trap': "it brings its own frame and sashes 6 cm back in the opening: leave the opening empty (a wall tool's own glass and sash "
            "would stand in it too), put the origin on the wall's face at the opening's foot; the boards reach 0.15 m past each side",
}

REVEAL = 0.06


def build(collection, seed=0, width=0.96, height=1.62, boards=4, corner=True):
    W = barn.number('boarded_window width', width, 0.4, 2.5)
    H = barn.number('boarded_window height', height, 0.6, 3.0)
    count = int(round(barn.number('boarded_window boards', boards, 2, 6)))
    corner = street.flag('boarded_window corner', corner)
    rng = shapes.rng_for(PART, seed)
    objects = []

    wood = shapes.Shape()
    glass = shapes.Shape()
    panes = street.sash_window(wood, None, 0.0, REVEAL, 0.0, W, H, bars=1, frame_w=0.075, depth=0.10)
    lower = [p for p in panes if p['sash'] == 'lower']
    upper = [p for p in panes if p['sash'] == 'upper']
    cracked = upper[rng.randrange(len(upper))]
    for p in upper:
        glass.box(((p['x0'] + p['x1']) / 2, p['y'], (p['z0'] + p['z1']) / 2), (p['x1'] - p['x0'] + 0.01, 0.004, p['z1'] - p['z0'] + 0.01))
    # the broken lower panes: shards left in the putty along their edges
    for p in lower:
        corners = [(p['x0'], p['z0']), (p['x1'], p['z0']), (p['x1'], p['z1']), (p['x0'], p['z1'])]
        for k, (cx, cz) in enumerate(corners):
            if rng.random() < 0.7:
                sx = 1.0 if k in (0, 3) else -1.0
                sz = 1.0 if k in (0, 1) else -1.0
                a = rng.uniform(0.05, 0.2) * (p['x1'] - p['x0'])
                b = rng.uniform(0.08, 0.35) * (p['z1'] - p['z0'])
                tri = [(cx, cz), (cx + sx * a * 2.2, cz), (cx + sx * a * 0.4, cz + sz * b)]
                v0 = glass._verts([(x, p['y'] - 0.002, z) for (x, z) in tri])
                v1 = glass._verts([(x, p['y'] + 0.002, z) for (x, z) in tri])
                glass._rings([v0, v1], True, True, True)
    objects.append(wood.finish('boarded_window frame and sashes', collection, street.WOOD, smooth=False))
    objects.append(glass.finish('boarded_window glass and shards', collection, street.DARK_GLASS, smooth=False))
    back = shapes.Shape()
    back.box((0.0, REVEAL + 0.14, H / 2), (W, 0.01, H))
    objects.append(back.finish('boarded_window the dark stair', collection, street.RECESS, smooth=False))

    # ------------------------------------------------------------------ the boards, nailed on the wall's face
    boards_mat = barn.shaded_surface('rough_wood', PART, low=0.6, high=1.15, Grime=0.5, Wet=0.1)
    nails = shapes.Shape()
    stains = shapes.Shape()
    barn.number_layers(stains, points=('fade',))
    span_top = max(0.5, H * 0.52)
    pitch = (span_top - 0.08) / count
    board_h = min(0.19, pitch - 0.012)
    placed = []
    for k in range(count):
        z = 0.08 + pitch * (k + 0.5) + rng.uniform(-0.01, 0.01)
        length = W + 0.30 + rng.uniform(-0.06, 0.04)
        xc = rng.uniform(-0.03, 0.03)
        tilt = math.radians(rng.uniform(-2.5, 2.5))
        placed.append((xc, z, length, tilt, board_h))
    if corner:
        cx = (cracked['x0'] + cracked['x1']) / 2
        cz = (cracked['z0'] + cracked['z1']) / 2
        side = 1.0 if cx > 0 else -1.0
        placed.append((cx * 0.5 + side * 0.05, cz, W * 0.62 + 0.15, math.radians(side * rng.uniform(10, 18)), 0.15))
    for k, (xc, z, length, tilt, bh) in enumerate(placed):
        y = -0.011 - 0.003 * (k % 2)
        d = Vector((math.cos(tilt), 0.0, math.sin(tilt)))
        a = Vector((xc, y, z)) - d * (length / 2)
        b = Vector((xc, y, z)) + d * (length / 2)
        objects.append(shapes.timber(collection, 'boarded_window board %d' % (k + 1), a, b, bh, 0.022, boards_mat, rng=rng,
                                     up=Vector((0.0, -1.0, 0.0)), chamfer=0.003, shift=0.4))
        for end in (-1, 1):
            at = Vector((xc, y, z)) + d * (end * (length / 2 - 0.06))
            for dz in (-0.045, 0.045):
                p = at + Vector((0.0, -0.012, dz * (bh / 0.19)))
                nails.sphere(p, 0.0065, segments=8, rings=4, squash=(1.0, 0.45, 1.0))
                if rng.random() < 0.6:
                    street.rust_run(stains, p.x - 0.008, p.x + 0.008, p.z - 0.004, rng.uniform(0.04, 0.12), y - 0.0125, rng, cols=3, rows=3,
                                    low=z - bh / 2 + 0.005)
    objects.append(nails.finish('boarded_window nail heads', collection, street.NAILS, smooth=True, sharp=None))
    objects.append(stains.finish('boarded_window rust runs', collection, street.STAIN, smooth=True, sharp=None, shadow=False))
    return objects
