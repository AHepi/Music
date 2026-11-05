"""
arched_bridge: a Japanese arched timber bridge (taikobashi, the drum bridge) over a garden pond, built as the real ones
are: two curved beams (the stringers) springing from a stone sill on each bank, deck boards laid across them following
the arch with foot battens on its steep flanks, a railing each side (posts mortised into a low kerb rail, a middle rail
and a round handrail following the curve, taller end posts with bronze or wooden caps, the giboshi), and under the arch
frames of posts standing down through the water onto the pond's bed, each with a cap beam under the stringers and a tie
beam through its posts. The timber is painted red over the grain of the shelf's photographed planks: worn to grey wood
on the handrail where hands slide and at the deck's edges, flaked in patches, dark and green at the water line; the
deck's boards bare, wet, grey wood. Its length runs along X, crossing from -X to +X; the origin is on the water's
surface under the middle of the bridge, z = 0.

Options:
    span     metres between the banks along X, where the deck comes down to the bank (default 4.0)
    width    metres across the deck, rail to rail (default 1.3)
    rise     metres the deck's crown rises above its ends (default 0.8)
    caps     'bronze' (default) or 'wood': the caps on the end posts
    seed     the paint's flaking, each board's part of the photograph, small lean in the posts

Where it came from: '/home/claude/build-57-garden/first pass/render_final.py', the arched bridge (lines 1110-1157):
the builder's circular arch, stringers, posts and rails, deck boards following it and copper caps; rebuilt here from
the board's photograph 03 (Kameido): the railing posts set into a kerb rail on the deck, a round handrail, foot battens
on the steep flanks, cap beams and through ties on the frames under the arch, posts standing to the pond's bed, stone
sills on the banks, the turned caps with their neck rings, and the paint laid over the photographed planks (decision 84)
instead of a made red.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402
import _shapes_garden_plants as plants  # noqa: E402

PART = 'arched_bridge'
DECK_END = 0.35          # the deck's top where it comes down to each bank, above the water
BED = -0.5               # the pond's bed, where the posts stand
BOARD = 0.045            # deck boards' thickness
STRINGER = (0.12, 0.24)  # across, deep
RED = (0.30, 0.036, 0.020)

CARD = {
    'name': PART,
    'what': 'a Japanese arched timber bridge (taikobashi): curved stringers on stone sills, deck boards following the arch '
            'with foot battens on its flanks, railings with a kerb rail, middle rail, round handrail and capped end posts '
            '(giboshi), frames of posts standing in the water with cap beams and ties; red paint over photographed wood, '
            'worn grey on the handrail and edges, green and dark at the water line',
    'size_m': (4.60, 1.64, 2.43),
    'foot_z': BED,
    'options': {
        'span': 'metres between the banks along X, where the deck comes down to each bank (default 4.0; 2.5 to 8)',
        'width': 'metres across the deck, rail to rail (default 1.3; 0.9 to 2.5)',
        'rise': 'metres the deck crown rises above its ends (default 0.8; a drum bridge rises about a quarter of its '
                'span, half for the steepest)',
        'caps': "'bronze' (default): green-bronze caps on the end posts; 'wood': turned wooden caps, painted",
        'seed': 'the paint flaking, each board and timber part of the photograph, a small lean in the posts (default 0)',
    },
    'materials': ['SURFACE • old_planks_02', 'SURFACE • dark_rock_02', 'PART • arched_bridge: old bronze'],
    'source': "'/home/claude/build-57-garden/first pass/render_final.py', the arched bridge (lines 1110-1157)",
    'views': 'reads from every side; best from along the pond at a low angle, where the arch and its reflection make a '
             'ring; the frames under it show from the side (along Y)',
    'trap': 'its origin is the water surface (z = 0) under the middle, not its lowest point: the posts stand 0.5 m down '
            'to the pond bed, and the deck comes down to the banks 0.35 m above the water at x = -span/2 and +span/2, '
            'where its stone sills and stringer ends reach 0.3 m further out: make the banks there, at that height',
}


def _section_rect(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]


def _section_round(r, sides=8):
    return [(r * math.cos(2 * math.pi * (k + 0.5) / sides), r * math.sin(2 * math.pi * (k + 0.5) / sides)) for k in range(sides)]


# a timber running along X gets its own frame with its Z along X, so the photographed planks' grain runs along it
ALONG_X = Matrix(((0.0, 0.0, 1.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
ALONG_Y = Matrix(((-1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))   # a turn, not a mirror


def build(collection, seed=0, span=4.0, width=1.3, rise=0.8, caps='bronze'):
    L = barn.number('arched_bridge span', span, 1.5, 12.0)
    W = barn.number('arched_bridge width', width, 0.6, 3.0)
    H = barn.number('arched_bridge rise', rise, 0.15, L * 0.5)
    if caps not in ('bronze', 'wood'):
        raise ValueError("arched_bridge caps is 'bronze' or 'wood', not %r" % (caps,))
    rng = shapes.rng_for(PART, seed)
    radius = (H * H + (L / 2) ** 2) / (2 * H)
    zc = DECK_END + H - radius

    def deck(x):
        return zc + math.sqrt(max(radius * radius - x * x, 0.0))

    def angle(x):
        return math.atan2(-x, math.sqrt(max(radius * radius - x * x, 1e-9)))

    # arc length from x = -L/2, and back
    def arc_of(x):
        return radius * (math.asin(max(-1.0, min(1.0, x / radius))) + math.asin(min(1.0, (L / 2) / radius)))

    total = arc_of(L / 2)

    def x_of(s):
        return radius * math.sin(s / radius - math.asin(min(1.0, (L / 2) / radius)))

    xs = [-L / 2 - 0.16 + (L + 0.32) * k / 48 for k in range(49)]
    y_beam = W / 2 - STRINGER[0] / 2
    y_post = W / 2 - 0.05

    timber_x = shapes.Shape()        # stringers and rails: along X
    uprights = shapes.Shape()        # posts: upright
    across = shapes.Shape()          # cap beams and ties: along Y
    boards = shapes.Shape()          # deck boards and battens
    stones = shapes.Shape()
    metal = shapes.Shape()

    # ------------------------------------------------------------------ the stringers: two curved beams under the deck's edges
    for side in (-1, 1):
        pts = [Vector((x, side * y_beam, deck(x) - BOARD - STRINGER[1] / 2)) for x in xs]
        plants.tagged(timber_x, lambda: timber_x.sweep(pts, 0.1, section=_section_rect(*STRINGER), up=(0, 0, 1)),
                      piece=rng.random(), pp_bare=lambda co: 0.15)

    # ------------------------------------------------------------------ the deck: boards across, following the arch; foot battens on the flanks
    pitch = 0.168
    count = max(4, int(total / pitch))
    step = total / count
    for k in range(count):
        s0 = (k + 0.5) * step
        x = x_of(s0)
        a = angle(x)
        z = deck(x) - BOARD / 2
        rot = Matrix(((math.cos(a), 0, -math.sin(a)), (0, 1, 0), (math.sin(a), 0, math.cos(a))))     # the board's X along the arch
        plants.tagged(boards, lambda: boards.box((x, rng.uniform(-0.01, 0.01), z), (step - 0.008, W, BOARD), rot),
                      piece=rng.random())
        if abs(math.tan(a)) > 0.28 and k % 2 == 0:
            n = rot @ Vector((0, 0, 1))
            c = Vector((x, 0.0, z)) + n * (BOARD / 2 + 0.012)
            plants.tagged(boards, lambda: boards.box(c, (0.05, W - 0.3, 0.024), rot), piece=rng.random())

    # ------------------------------------------------------------------ the railings
    rail_pts = lambda h, side: [Vector((x, side * y_post, deck(x) + h)) for x in
                                [-L / 2 + 0.05 + (L - 0.1) * k / 40 for k in range(41)]]
    posts_n = max(3, int(round(total / 0.62)))
    for side in (-1, 1):
        # kerb rail (on the deck, the posts set into it), middle rail, handrail
        plants.tagged(timber_x, lambda: timber_x.sweep(rail_pts(0.04, side), 0.1, section=_section_rect(0.075, 0.08), up=(0, 0, 1)),
                      piece=rng.random(), pp_bare=lambda co: 0.25)
        plants.tagged(timber_x, lambda: timber_x.sweep(rail_pts(0.40, side), 0.1, section=_section_rect(0.045, 0.06), up=(0, 0, 1)),
                      piece=rng.random(), pp_bare=lambda co: 0.1)
        # the handrail: worn on top where hands slide, most near the ends where people take hold to climb
        top_z = lambda co: 1.0 if co[2] > deck(co[0]) + 0.75 else 0.0
        ends = lambda co: 0.55 + 0.45 * min(1.0, abs(co[0]) / (L / 2)) ** 2
        plants.tagged(timber_x, lambda: timber_x.sweep(rail_pts(0.745, side), 0.1, section=_section_round(0.042, 8), up=(0, 0, 1)),
                      piece=rng.random(), pp_bare=lambda co: top_z(co) * ends(co))
        for k in range(posts_n + 1):
            s0 = 0.05 + (total - 0.1) * k / posts_n
            x = x_of(s0)
            end = k in (0, posts_n)
            size = 0.12 if end else 0.085
            top = 0.95 if end else 0.745
            z0 = deck(x) - 0.01
            lean = Vector((rng.uniform(-0.006, 0.006), rng.uniform(-0.006, 0.006), 0.0))
            plants.tagged(uprights, lambda: uprights.beam((x, side * y_post, z0), Vector((x, side * y_post, deck(x) + top)) + lean,
                                                          size, size),
                          piece=rng.random(), pp_bare=lambda co: 0.35 if co[2] > deck(co[0]) + top - 0.06 else 0.0)
            if end:
                cap_at = Vector((x, side * y_post, deck(x) + top)) + lean
                profile = [(0.0, 0.0), (0.071, 0.0), (0.071, 0.05), (0.079, 0.056), (0.079, 0.068), (0.052, 0.078),
                           (0.046, 0.092), (0.062, 0.108), (0.077, 0.132), (0.073, 0.162), (0.054, 0.192), (0.028, 0.222),
                           (0.012, 0.246), (0.005, 0.27), (0.0, 0.282)]
                target = metal if caps == 'bronze' else uprights
                plants.tagged(target, lambda: target.lathe(profile, segments=20, matrix=Matrix.Translation(cap_at)),
                              piece=rng.random(), pp_bare=lambda co: 0.6)

    # ------------------------------------------------------------------ the frames under the arch: posts to the pond's bed, cap beams, ties
    frames = max(1, int(L / 1.25))
    for k in range(1, frames + 1):
        x = -L / 2 + L * k / (frames + 1)
        under = deck(x) - BOARD - STRINGER[1] * 1.02
        if under < 0.35:
            continue
        cap_h = 0.15
        for side in (-1, 1):
            foot = Vector((x + rng.uniform(-0.01, 0.01), side * y_beam, BED))
            plants.tagged(uprights, lambda: uprights.beam(foot, (x, side * y_beam, under - cap_h + 0.02), 0.13, 0.13),
                          piece=rng.random())
        plants.tagged(across, lambda: across.beam((x, -W / 2 - 0.12, under - cap_h / 2), (x, W / 2 + 0.12, under - cap_h / 2), 0.14, cap_h),
                      piece=rng.random())
        tie_z = min(0.28, under - cap_h - 0.12)
        plants.tagged(across, lambda: across.beam((x, -W / 2 - 0.16, tie_z), (x, W / 2 + 0.16, tie_z), 0.05, 0.12),
                      piece=rng.random())

    # ------------------------------------------------------------------ stone sills on the banks under the stringers' ends, down to the pond's bed
    for side in (-1, 1):
        x = side * (L / 2 + 0.05)
        top = deck(side * (L / 2 + 0.16)) - BOARD - STRINGER[1] - 0.005
        low = BED
        plants.tagged(stones, lambda: stones.box((x, 0.0, (top + low) / 2), (0.5, W + 0.24, top - low)), piece=rng.random())
    stones.chamfer_all(0.025)

    paint = plants.painted_wood(PART, 'red paint', paint=RED, peel=0.385, **{'Mud height': 0.42, 'Mud color': (0.016, 0.022, 0.012),
                                                                          'Grime': 0.45, 'Edge wear': 0.25})
    deck_wood = plants.surface('old_planks_02', PART, 'deck boards', Wet=0.55, Grime=0.4, **{'Edge wear': 0.3})
    rock = plants.surface('dark_rock_02', PART, 'sills', Wet=0.5, **{'Mud height': 0.25, 'Mud color': (0.02, 0.025, 0.015)})
    made = [
        timber_x.finish('arched_bridge stringers and rails', collection, paint, smooth=True, sharp=50.0, local=ALONG_X),
        uprights.finish('arched_bridge posts', collection, paint, smooth=True, sharp=50.0, chamfer=0.008),
        boards.finish('arched_bridge deck', collection, deck_wood, smooth=True, sharp=50.0, chamfer=0.005, local=ALONG_Y),
        stones.finish('arched_bridge sills', collection, rock, smooth=True, sharp=50.0),
    ]
    if not across.empty():
        made.append(across.finish('arched_bridge cap beams and ties', collection, paint, smooth=True, sharp=50.0, chamfer=0.008, local=ALONG_Y))
    if not metal.empty():
        made.append(metal.finish('arched_bridge caps', collection, plants.bronze_material(PART), smooth=True, sharp=60.0))
    return made
