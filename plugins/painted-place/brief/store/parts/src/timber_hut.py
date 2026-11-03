"""
timber_hut: a 1914-18 British army barrack hut, built as a carpenter would build it.

  - It stands on short timber stumps under three bearers, so there is a dark gap under it.
  - Its walls are lapped weatherboards with real thickness: each board's lower edge stands out over the board below,
    so every board throws a shadow line. Boards are joined end to end at staggered places; each has its own shade.
  - Corner boards, a door in a frame with a two-tread step, windows with casings, sills, sashes and glazing bars.
  - The roof is corrugated iron sheets with real corrugations, lapped side to side and end to end, on purlins and
    rafters; the eaves overhang 0.4 m with open rafter tails and fascia boards, so they throw a shadow band on the
    wall; barge boards on the gable ends; a rolled ridge cap; a stove pipe with a cap, flashing and stay wires.
  - Inside (seen through the open door and when lit): floor, board lining, rafters and tie beams, a stove, a table
    with benches, a hanging lamp.

Options (all optional):
  length            outside length along X, metres (default 10.0)
  width             outside width along Y, metres (default 5.0)
  wall_height       floor to the top of the walls, metres (default 2.3)
  door_open         the door swung open outwards (default False)
  lit_windows       windows glowing warm, the hanging lamp lit, a small warm light inside (default True)
  windows_per_side  windows on each long side; the front has these plus the door (default 4)
  seed              small differences: board shades and joints, roof sheets, stump lean, door angle

Front (the door side) faces -Y. Foot at z = 0, centred on the origin.

Made for the store from the huts in the military-base builders' scripts ('46 military-base - render_final.py',
`hut` line 388; '50 first pass' line 510 and '50 second pass' line 657), which the owner judged "looks like
cardboard" (a box with a plank picture on it); rebuilt here from the period photographs' construction.
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
    'name': 'timber_hut',
    'what': 'a 1914-18 army barrack hut: lapped weatherboards, corrugated iron roof with deep eaves, on stumps',
    'size_m': (10.74, 6.18, 5.32),
    'options': {
        'length': 'outside length along X in metres (default 10.0)',
        'width': 'outside width along Y in metres (default 5.0)',
        'wall_height': 'floor to the top of the walls in metres (default 2.3)',
        'door_open': 'the door swung open outwards (default False)',
        'lit_windows': 'windows glow warm, the hanging lamp is lit, a small warm light inside (default True)',
        'windows_per_side': 'windows on each long side; the front has these plus the door (default 4)',
        'seed': 'board shades and joints, roof sheets, stump lean, door angle (default 0)',
    },
    'materials': ['PART • timber_hut: weathered boards, army paint', 'WOOD • peeling dark painted doors',
                  'SURFACE • worn_corrugated_iron (timber_hut)', 'SURFACE • rusty_corrugated_iron (timber_hut)',
                  'SURFACE • rusty_metal_02 (timber_hut)', 'SURFACE • rough_wood (timber_hut)', 'SURFACE • wood_planks_grey',
                  'SURFACE • old_planks_02', 'IRON • soot-black lamp posts', 'GLASS • warm occupied interiors',
                  'GLASS • sleeping navy interiors', 'LAMP • honey flame glow', 'RECESSES • near-black blue'],
    'source': "rebuilt from `hut` in '46 military-base - render_final.py' (line 388) and the 50 scripts (line 510 / 657), "
              "after the owner's note that the builders' hut 'looks like cardboard'",
    'views': 'reads from every side',
    'trap': 'The weathered-boards paint colour is chosen by where the hut stands, so two huts side by side may differ.',
}

PART = 'timber_hut'
BOARDS = 'MADE • weathered boards, peeling paint'
PAINTED = 'WOOD • peeling dark painted doors'
IRON = 'IRON • soot-black lamp posts'

# weatherboards: how much of each board shows, its full height, its thickness at the lower and upper edge
E = 0.15
HB = 0.175
T_BUTT = 0.022
T_TOP = 0.008
B0 = (T_BUTT + 0.0005) * HB / E - T_BUTT + T_TOP   # the board's back stands this far off the frame at its lower edge
FRONT = B0 + T_BUTT                                  # the lower edge's face stands this far out from the frame
LINING = -0.11                                       # the inside lining, behind the frame

# roof
PITCH = math.radians(27.0)
T = math.tan(PITCH)
C = math.cos(PITCH)
S = math.sin(PITCH)
RAFTER_D = 0.12
PURLIN_D = 0.06
EAVES = 0.40          # eaves overhang beyond the wall boards
VERGE = 0.30          # roof overhang beyond the gable walls
LAMBDA = 0.076        # corrugation pitch (3 inch)
AMP = 0.0095          # half the corrugation depth
SHEET_T = 0.0015
COVER = 10 * LAMBDA   # each sheet covers 10 corrugations and laps one more over its neighbour


ARMY_PAINT = [(0.0, (0.19, 0.18, 0.155)),    # pale lime-wash grey
              (0.2, (0.135, 0.135, 0.125)),  # dull grey
              (0.4, (0.072, 0.082, 0.052)),  # weathered army green
              (0.6, (0.062, 0.044, 0.03)),   # creosote brown
              (0.8, (0.15, 0.13, 0.085)),    # faded khaki
              (0.9, (0.075, 0.085, 0.075))]  # dark grey-green


def army_boards():
    """The store's weathered boards (a shade per board, rain streaks, old paint peeling in cracked patches), with its
    paint colours swapped for the army's: green, creosote brown, khaki, greys. Still one paint per hut, by where
    it stands."""
    name = 'PART • timber_hut: weathered boards, army paint'
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    import store
    mat = store.material(BOARDS).copy()
    mat.name = name
    for node in mat.node_tree.nodes:
        if node.type == 'VALTORGB' and node.color_ramp.interpolation == 'CONSTANT':
            for element, (position, colour) in zip(node.color_ramp.elements, ARMY_PAINT):
                element.position = position
                element.color = (*colour, 1.0)
    mat.diffuse_color = (0.08, 0.085, 0.06, 1.0)
    return mat


class Wall:
    """One wall's own coordinates: s along it (left to right seen from outside), n outwards, z up."""

    def __init__(self, origin, along, out, s_lo, s_hi):
        self.o, self.a, self.n = Vector(origin), Vector(along), Vector(out)
        self.s_lo, self.s_hi = s_lo, s_hi

    def p(self, s, n, z):
        return self.o + self.a * s + self.n * n + Vector((0.0, 0.0, z))

    def box(self, builder, lo, hi, **kw):
        (s0, n0, z0), (s1, n1, z1) = lo, hi
        pts = [self.p(s0, n0, z0), self.p(s1, n0, z0), self.p(s1, n1, z0), self.p(s0, n1, z0),
               self.p(s0, n0, z1), self.p(s1, n0, z1), self.p(s1, n1, z1), self.p(s0, n1, z1)]
        return sh.add_hexahedron(builder, pts, **kw)


def _subtract(intervals, cuts):
    out = []
    for a, b in intervals:
        pieces = [(a, b)]
        for ca, cb in cuts:
            nxt = []
            for pa, pb in pieces:
                if cb <= pa or ca >= pb:
                    nxt.append((pa, pb))
                    continue
                if ca > pa:
                    nxt.append((pa, ca))
                if cb < pb:
                    nxt.append((cb, pb))
            pieces = nxt
        out.extend(p for p in pieces if p[1] - p[0] > 0.02)
    return out


def _joints(a, b, rnd, longest=4.2):
    """A run of boarding split into boards of real lengths, joined end to end with a hairline gap."""
    pieces = []
    start = a
    first = rnd.uniform(0.6, longest)
    edge = a + first
    while edge < b - 0.5:
        pieces.append((start, edge - 0.002))
        start = edge + 0.002
        edge = start + rnd.uniform(2.4, longest)
    pieces.append((start, b))
    return pieces


def _board(builder, layer, wall, z0, z1, s0a, s1a, s0b, s1b, tone):
    def ring(s0, s1, z):
        f = (z - z0) / HB
        back = B0 * (1.0 - f)
        front = FRONT + (T_TOP - FRONT) * f
        return [wall.p(s0, back, z), wall.p(s1, back, z), wall.p(s1, front, z), wall.p(s0, front, z)]
    sh.add_hexahedron(builder, ring(s0a, s1a, z0) + ring(s0b, s1b, z1), layer=layer, value=tone)


def _clad(builder, layer, wall, z_base, top, openings, rnd, gable_half=None):
    """Weatherboards course by course from z_base. `top`: where the wall's boards stop (long walls), or for a
    gable `gable_half(z)` gives the half width the boards may reach at height z."""
    i = 0
    while True:
        z0 = z_base + i * E
        z1 = z0 + HB
        if gable_half is None:
            if z0 > top - 0.03:
                break
            z1 = min(z1, top)
            lo0, hi0, lo1, hi1 = wall.s_lo, wall.s_hi, wall.s_lo, wall.s_hi
        else:
            h0 = min(gable_half(z0), wall.s_hi)
            if h0 < 0.08:
                break
            h1 = max(min(gable_half(z1), wall.s_hi), 0.01)
            lo0, hi0, lo1, hi1 = -h0, h0, -h1, h1
        cuts = [(op['sa'], op['sb']) for op in openings if op['k0'] <= i < op['k1']]
        runs = _subtract([(lo0, hi0)], cuts)
        for a, b in runs:
            pieces = _joints(a, b, rnd) if (gable_half is None or z1 < top) else [(a, b)]
            for pa, pb in pieces:
                tone = rnd.uniform(0.30, 0.78)
                if gable_half is None or (abs(lo1 - lo0) < 1e-6 and abs(hi1 - hi0) < 1e-6):
                    _board(builder, layer, wall, z0, z1, pa, pb, pa, pb, tone)
                else:
                    ta, tb = max(pa, lo1), min(pb, hi1)
                    if tb - ta < 0.01:
                        mid = min(max((pa + pb) / 2, lo1), hi1)
                        ta, tb = mid - 0.005, mid + 0.005
                    _board(builder, layer, wall, z0, z1, pa, pb, ta, tb, tone)
        i += 1


def _window(frames, frame_layer, sash, glass, wall, sa, sb, za, zb):
    """Reveal linings, casings with a drip cap, a sill and apron, and a sash with glazing bars and glass."""
    v = dict(layer=frame_layer, value=0.55)
    t = 0.022
    wall.box(frames, (sa - t, LINING - 0.01, za), (sa, 0.03, zb), **v)                 # jambs
    wall.box(frames, (sb, LINING - 0.01, za), (sb + t, 0.03, zb), **v)
    wall.box(frames, (sa - t, LINING - 0.01, zb), (sb + t, 0.03, zb + t), **v)          # head lining
    wall.box(frames, (sa - t, LINING - 0.01, za - t), (sb + t, -0.04, za), **v)         # inner sill board
    cw = 0.085
    wall.box(frames, (sa - t - cw, 0.026, za - 0.005), (sa - t + 0.012, 0.056, zb + t + cw), **v)   # casings
    wall.box(frames, (sb + t - 0.012, 0.026, za - 0.005), (sb + t + cw, 0.056, zb + t + cw), **v)
    wall.box(frames, (sa - t - cw - 0.01, 0.026, zb + t - 0.004), (sb + t + cw + 0.01, 0.058, zb + t + cw + 0.004), **v)
    # drip cap on the head casing: sloped top sheds the rain
    s0, s1 = sa - t - cw - 0.03, sb + t + cw + 0.03
    zc = zb + t + cw + 0.004
    pts = [wall.p(s0, 0.026, zc), wall.p(s1, 0.026, zc), wall.p(s1, 0.085, zc), wall.p(s0, 0.085, zc),
           wall.p(s0, 0.026, zc + 0.035), wall.p(s1, 0.026, zc + 0.035), wall.p(s1, 0.085, zc + 0.018), wall.p(s0, 0.085, zc + 0.018)]
    sh.add_hexahedron(frames, pts, **v)
    # sill: sloping outwards, standing proud, wider than the casings
    s0, s1 = sa - t - cw - 0.05, sb + t + cw + 0.05
    pts = [wall.p(s0, -0.045, za - 0.045), wall.p(s1, -0.045, za - 0.045), wall.p(s1, 0.11, za - 0.07), wall.p(s0, 0.11, za - 0.07),
           wall.p(s0, -0.045, za + 0.002), wall.p(s1, -0.045, za + 0.002), wall.p(s1, 0.11, za - 0.03), wall.p(s0, 0.11, za - 0.03)]
    sh.add_hexahedron(frames, pts, **v)
    wall.box(frames, (sa - t - cw + 0.01, 0.026, za - 0.07 - 0.11), (sb + t + cw - 0.01, 0.05, za - 0.065), **v)   # apron
    # the sash: stiles, rails, glazing bars (2 across, 3 up), glass behind the bars
    n_out, n_in = -0.012, -0.056
    st, top_rail, bottom_rail, bar = 0.05, 0.05, 0.075, 0.022
    wall.box(sash, (sa, n_in, za), (sa + st, n_out, zb))
    wall.box(sash, (sb - st, n_in, za), (sb, n_out, zb))
    wall.box(sash, (sa + st, n_in, za), (sb - st, n_out, za + bottom_rail))
    wall.box(sash, (sa + st, n_in, zb - top_rail), (sb - st, n_out, zb))
    s_in0, s_in1, z_in0, z_in1 = sa + st, sb - st, za + bottom_rail, zb - top_rail
    sc = (s_in0 + s_in1) / 2
    wall.box(sash, (sc - bar / 2, -0.048, z_in0), (sc + bar / 2, -0.018, z_in1))
    for k in (1, 2):
        zr = z_in0 + (z_in1 - z_in0) * k / 3
        wall.box(sash, (s_in0, -0.048, zr - bar / 2), (s_in1, -0.018, zr + bar / 2))
    wall.box(glass, (s_in0 - 0.006, -0.036, z_in0 - 0.006), (s_in1 + 0.006, -0.031, z_in1 + 0.006))


def _gable_vent(frames, frame_layer, backing, wall, zc, w=0.56, h=0.34):
    """A louvred vent high in the gable: a frame, slanted slats, darkness behind."""
    v = dict(layer=frame_layer, value=0.5)
    fw = 0.055
    wall.box(frames, (-w / 2, 0.028, zc - h / 2), (w / 2, 0.062, zc - h / 2 + fw), **v)
    wall.box(frames, (-w / 2, 0.028, zc + h / 2 - fw), (w / 2, 0.062, zc + h / 2), **v)
    wall.box(frames, (-w / 2, 0.028, zc - h / 2 + fw), (-w / 2 + fw, 0.062, zc + h / 2 - fw), **v)
    wall.box(frames, (w / 2 - fw, 0.028, zc - h / 2 + fw), (w / 2, 0.062, zc + h / 2 - fw), **v)
    wall.box(backing, (-w / 2 + fw, 0.030, zc - h / 2 + fw), (w / 2 - fw, 0.034, zc + h / 2 - fw))
    inner = h - 2 * fw
    for k in range(4):
        z = zc - h / 2 + fw + inner * (k + 0.5) / 4
        s0, s1 = -w / 2 + fw, w / 2 - fw
        pts = [wall.p(s0, 0.036, z + 0.035), wall.p(s1, 0.036, z + 0.035), wall.p(s1, 0.048, z + 0.04), wall.p(s0, 0.048, z + 0.04),
               wall.p(s0, 0.056, z - 0.02), wall.p(s1, 0.056, z - 0.02), wall.p(s1, 0.066, z - 0.012), wall.p(s0, 0.066, z - 0.012)]
        sh.add_hexahedron(frames, pts, **v)


def build(collection, seed=0, length=10.0, width=5.0, wall_height=2.3, door_open=False, lit_windows=True,
          windows_per_side=4, **_ignored):
    rnd = sh.rand(seed, 'timber_hut')
    L, W, H = float(length), float(width), float(wall_height)
    n_win = max(0, int(windows_per_side))
    made = []

    z_floor = 0.485
    z_base = z_floor - 0.10                  # the lowest board's lower edge
    z_wp = z_floor + H                       # top of the walls (wall plate)
    stump_top = 0.30

    wood = sh.copy_surface('SURFACE • rough_wood', PART, mud_height=0.22)
    sheets_worn = sh.copy_surface('SURFACE • worn_corrugated_iron', PART, picture_scale=LAMBDA / 0.1125, darken=0.36, grime=0.5)
    sheets_rusty = sh.copy_surface('SURFACE • rusty_corrugated_iron', PART, picture_scale=LAMBDA / 0.0328, darken=0.42, grime=0.5)
    boards = army_boards()
    flashing = sh.copy_surface('SURFACE • rusty_metal_02', PART, darken=0.22, grime=0.6)

    walls_b = sh.Builder('timber_hut wall boards', boards)
    tone = walls_b.layer('board_tone')
    trims = sh.Builder('timber_hut corner boards, casings and sills', boards)
    trim_tone = trims.layer('board_tone')
    sash = sh.Builder('timber_hut window sashes', PAINTED)
    glass = sh.Builder('timber_hut window glass', 'GLASS • warm occupied interiors' if lit_windows else 'GLASS • sleeping navy interiors')
    backing = sh.Builder('timber_hut vent darkness', 'RECESSES • near-black blue')
    lining = sh.Builder('timber_hut inside lining', 'SURFACE • old_planks_02')

    front = Wall((0, -W / 2, 0), (1, 0, 0), (0, -1, 0), -L / 2 - FRONT, L / 2 + FRONT)
    back = Wall((0, W / 2, 0), (-1, 0, 0), (0, 1, 0), -L / 2 - FRONT, L / 2 + FRONT)
    right = Wall((L / 2, 0, 0), (0, 1, 0), (1, 0, 0), -W / 2, W / 2)
    left = Wall((-L / 2, 0, 0), (0, -1, 0), (-1, 0, 0), -W / 2, W / 2)

    # ---------------------------------------------------------------- openings on the course grid
    def course(z):
        return int(round((z - z_base) / E))

    top_course = course(z_wp) - 1
    kw1 = min(course(z_floor + 0.95) + 7, top_course - 1)
    kw0 = max(kw1 - 7, course(z_floor + 0.55))
    win_za, win_zb = z_base + kw0 * E, z_base + kw1 * E - 0.02
    kd1 = max(kw1, course(z_floor + 1.95) + (0 if (z_base + kw1 * E - 0.02 - z_floor) >= 1.85 else 1))
    kd1 = min(kd1, top_course - 1)
    door_zb = z_base + kd1 * E - 0.02

    slots = n_win + 1
    pitch_front = L / slots
    win_w = max(0.45, min(0.80, pitch_front - 0.55, (L / max(n_win, 1)) - 0.55))
    door_w = max(0.7, min(0.90, pitch_front - 0.40))
    door_slot = n_win // 2
    front_open, back_open = [], []
    door_s = 0.0
    for k in range(slots):
        s = -L / 2 + pitch_front * (k + 0.5)
        if k == door_slot:
            door_s = s
            front_open.append(dict(sa=s - door_w / 2, sb=s + door_w / 2, za=z_floor, zb=door_zb, k0=1, k1=kd1, kind='door'))
        else:
            front_open.append(dict(sa=s - win_w / 2, sb=s + win_w / 2, za=win_za, zb=win_zb, k0=kw0, k1=kw1, kind='window'))
    for k in range(n_win):
        s = -L / 2 + (L / n_win) * (k + 0.5)
        back_open.append(dict(sa=s - win_w / 2, sb=s + win_w / 2, za=win_za, zb=win_zb, k0=kw0, k1=kw1, kind='window'))

    # ---------------------------------------------------------------- weatherboards
    rise_rb = RAFTER_D / C

    def gable_half(z):
        return W / 2 - (z - z_wp - rise_rb) / T

    _clad(walls_b, tone, front, z_base, z_wp, front_open, rnd)
    _clad(walls_b, tone, back, z_base, z_wp, back_open, rnd)
    _clad(walls_b, tone, right, z_base, z_wp, [], rnd, gable_half)
    _clad(walls_b, tone, left, z_base, z_wp, [], rnd, gable_half)

    # corner boards: an L of two boards at each corner, covering the board ends
    cb, ct = 0.095, 0.034
    for wall, gable_wall, sign in ((front, right, 1), (front, left, -1), (back, left, 1), (back, right, -1)):
        s_end = wall.s_hi if sign > 0 else wall.s_lo
        lo = (s_end - cb, FRONT - 0.006, z_base - 0.01) if sign > 0 else (s_end - ct, FRONT - 0.006, z_base - 0.01)
        hi = (s_end + ct, FRONT + ct, z_wp + 0.02) if sign > 0 else (s_end + cb, FRONT + ct, z_wp + 0.02)
        wall.box(trims, lo, hi, layer=trim_tone, value=0.5)
    for gable_wall in (right, left):
        for side in (-1, 1):
            s_edge = side * (W / 2 + FRONT)
            lo, hi = sorted((s_edge, s_edge - side * cb))
            gable_wall.box(trims, (lo, FRONT - 0.006, z_base - 0.01), (hi, FRONT + ct - 0.002, z_wp + 0.05), layer=trim_tone, value=0.5)

    # ---------------------------------------------------------------- windows, vents, door frame
    for wall, opens in ((front, front_open), (back, back_open)):
        for op in opens:
            if op['kind'] == 'window':
                _window(trims, trim_tone, sash, glass, wall, op['sa'], op['sb'], op['za'], op['zb'])
    rise = (W / 2) * T
    for gable_wall in (right, left):
        _gable_vent(trims, trim_tone, backing, gable_wall, z_wp + rise * 0.42 + 0.05)

    sa, sb = door_s - door_w / 2, door_s + door_w / 2
    t = 0.03
    v = dict(layer=trim_tone, value=0.55)
    front.box(trims, (sa - t, LINING - 0.01, z_floor), (sa, 0.03, door_zb), **v)
    front.box(trims, (sb, LINING - 0.01, z_floor), (sb + t, 0.03, door_zb), **v)
    front.box(trims, (sa - t, LINING - 0.01, door_zb), (sb + t, 0.03, door_zb + t), **v)
    cw = 0.10
    front.box(trims, (sa - t - cw, 0.026, z_floor - 0.02), (sa - t + 0.012, 0.058, door_zb + t + cw), **v)
    front.box(trims, (sb + t - 0.012, 0.026, z_floor - 0.02), (sb + t + cw, 0.058, door_zb + t + cw), **v)
    front.box(trims, (sa - t - cw - 0.01, 0.026, door_zb + t - 0.004), (sb + t + cw + 0.01, 0.06, door_zb + t + cw + 0.004), **v)
    s0, s1 = sa - t - cw - 0.03, sb + t + cw + 0.03
    zc = door_zb + t + cw + 0.004
    pts = [front.p(s0, 0.026, zc), front.p(s1, 0.026, zc), front.p(s1, 0.09, zc), front.p(s0, 0.09, zc),
           front.p(s0, 0.026, zc + 0.04), front.p(s1, 0.026, zc + 0.04), front.p(s1, 0.09, zc + 0.02), front.p(s0, 0.09, zc + 0.02)]
    sh.add_hexahedron(trims, pts, **v)
    front.box(trims, (sa - 0.02, LINING - 0.01, z_floor - 0.06), (sb + 0.02, 0.07, z_floor + 0.014), **v)   # threshold

    # ---------------------------------------------------------------- the door leaf (ledged and braced), its ironwork
    door = sh.Builder('timber_hut door', PAINTED)
    iron = sh.Builder('timber_hut ironwork', IRON)
    angle = math.radians(rnd.uniform(72.0, 108.0)) if door_open else 0.0
    hinge_s, hinge_n = sa, 0.066

    def dp(s, n, z):
        ds, dn = s - hinge_s, n - hinge_n
        return front.p(hinge_s + ds * math.cos(angle) - dn * math.sin(angle), hinge_n + ds * math.sin(angle) + dn * math.cos(angle), z)

    def dbox(builder, lo, hi):
        (s0, n0, z0), (s1, n1, z1) = lo, hi
        pts = [dp(s0, n0, z0), dp(s1, n0, z0), dp(s1, n1, z0), dp(s0, n1, z0), dp(s0, n0, z1), dp(s1, n0, z1), dp(s1, n1, z1), dp(s0, n1, z1)]
        sh.add_hexahedron(builder, pts)

    leaf_s0, leaf_s1 = sa + 0.004, sb - 0.004
    leaf_z0, leaf_z1 = z_floor + 0.016, door_zb - 0.004
    n_boards = 5
    bw = (leaf_s1 - leaf_s0) / n_boards
    for k in range(n_boards):
        thick = rnd.uniform(-0.002, 0.002)
        dbox(door, (leaf_s0 + k * bw + 0.0015, 0.012, leaf_z0), (leaf_s0 + (k + 1) * bw - 0.0015, 0.035 + thick, leaf_z1))
    ledge_z = [leaf_z0 + 0.18, (leaf_z0 + leaf_z1) / 2, leaf_z1 - 0.2]
    for z in ledge_z:
        dbox(door, (leaf_s0 + 0.03, -0.016, z - 0.07), (leaf_s1 - 0.03, 0.012, z + 0.07))
    for za_, zb_ in ((ledge_z[0], ledge_z[1]), (ledge_z[1], ledge_z[2])):
        p0 = (leaf_s0 + 0.08, za_ + 0.07)
        p1 = (leaf_s1 - 0.08, zb_ - 0.07)
        d = Vector((p1[0] - p0[0], p1[1] - p0[1])).normalized()
        nrm = Vector((-d.y, d.x)) * 0.05
        quad = [(p0[0] - nrm.x, p0[1] - nrm.y), (p0[0] + nrm.x, p0[1] + nrm.y), (p1[0] + nrm.x, p1[1] + nrm.y), (p1[0] - nrm.x, p1[1] - nrm.y)]
        pts = [dp(s_, -0.015, z_) for s_, z_ in quad] + [dp(s_, 0.012, z_) for s_, z_ in quad]
        sh.add_hexahedron(door, pts)
    for z in (ledge_z[0], ledge_z[2]):
        dbox(iron, (leaf_s0 - 0.004, 0.035, z - 0.022), (leaf_s0 + 0.48, 0.041, z + 0.022))
        sh.add_cylinder(iron, front.p(hinge_s - 0.01, hinge_n - 0.012, z - 0.05), front.p(hinge_s - 0.01, hinge_n - 0.012, z + 0.05), 0.013, segments=8)
        front.box(iron, (sa - 0.07, 0.056, z - 0.025), (sa - 0.01, 0.064, z + 0.025))
    zl = z_floor + 1.02
    dbox(iron, (leaf_s1 - 0.11, 0.035, zl - 0.06), (leaf_s1 - 0.07, 0.04, zl + 0.06))
    dbox(iron, (leaf_s1 - 0.1, 0.04, zl - 0.05), (leaf_s1 - 0.08, 0.065, zl - 0.035))
    dbox(iron, (leaf_s1 - 0.1, 0.04, zl + 0.035), (leaf_s1 - 0.08, 0.065, zl + 0.05))
    dbox(iron, (leaf_s1 - 0.1, 0.055, zl - 0.05), (leaf_s1 - 0.08, 0.068, zl + 0.05))

    # ---------------------------------------------------------------- step: two treads on stepped stringers
    steps_x = sh.Grain('timber_hut step treads', wood, (1, 0, 0), rnd)
    steps_s = sh.Builder('timber_hut step stringers', wood)
    rise_step = z_floor / 3.0
    for k, (n0, n1) in enumerate(((0.035, 0.33), (0.33, 0.62))):
        ztop = rise_step * (2 - k)
        p = [front.p(door_s - 0.56, n0, ztop - 0.035), front.p(door_s + 0.56, n1 + 0.025, ztop)]
        sh.add_box(steps_x, (min(p[0].x, p[1].x), min(p[0].y, p[1].y), ztop - 0.035), (max(p[0].x, p[1].x), max(p[0].y, p[1].y), ztop))
        p = [front.p(door_s - 0.5, n1 - 0.022, ztop - 0.035 - rise_step + 0.035), front.p(door_s + 0.5, n1, ztop - 0.035)]
        sh.add_box(steps_x, (min(p[0].x, p[1].x), min(p[0].y, p[1].y), max(0.0, ztop - rise_step)), (max(p[0].x, p[1].x), max(p[0].y, p[1].y), ztop - 0.035))
    for side in (-1, 1):
        s_c = door_s + side * 0.52
        outline = [(0.035, 0.0), (0.62, 0.0), (0.62, rise_step - 0.035), (0.33, rise_step - 0.035), (0.33, 2 * rise_step - 0.035), (0.035, 2 * rise_step - 0.035)]
        sh.extrude_polygon(steps_s.bm, outline, front.p(s_c - 0.02, 0, 0), front.n, Vector((0, 0, 1)), front.a, 0.04)

    # ---------------------------------------------------------------- stumps, bearers, floor
    along_x = sh.Grain('timber_hut bearers, plates and purlins', wood, (1, 0, 0), rnd)
    along_z = sh.Grain('timber_hut stumps and posts', wood, (0, 0, 1), rnd)
    along_y = sh.Grain('timber_hut tie beams', wood, (0, 1, 0), rnd)
    n_stumps = max(3, int(round(L / 1.6)) + 1)
    for y_line in (-W / 2 + 0.11, 0.0, W / 2 - 0.11):
        for j in range(n_stumps):
            x = -L / 2 + 0.16 + (L - 0.32) * j / (n_stumps - 1)
            size = rnd.uniform(0.16, 0.2)
            depth = size * rnd.uniform(0.9, 1.05)
            lean = (rnd.uniform(-0.025, 0.025), rnd.uniform(-0.025, 0.025))
            turn = rnd.uniform(-0.12, 0.12)
            ring = [(cx * math.cos(turn) - cy * math.sin(turn), cx * math.sin(turn) + cy * math.cos(turn))
                    for cx, cy in ((-size / 2, -depth / 2), (size / 2, -depth / 2), (size / 2, depth / 2), (-size / 2, depth / 2))]
            sh.add_hexahedron(along_z, [(x + cx + lean[0], y_line + cy + lean[1], 0.0) for cx, cy in ring] +
                              [(x + cx, y_line + cy, stump_top) for cx, cy in ring])
        sh.add_box(along_x, (-L / 2, y_line - 0.06, stump_top), (L / 2, y_line + 0.06, z_floor - 0.035))
    floor = sh.Builder('timber_hut floor', 'SURFACE • wood_planks_grey')
    sh.add_box(floor, (-L / 2, -W / 2, z_floor - 0.035), (L / 2, W / 2, z_floor))

    # ---------------------------------------------------------------- roof frame
    origin_z = z_wp + (W / 2) * T + (RAFTER_D + PURLIN_D) / C     # purlin tops (sheet troughs) at the ridge line

    def sp(side, x, t_, h):
        return Vector((x, side * (t_ * C + h * S), origin_z - t_ * S + h * C))

    def normal(side):
        return Vector((0.0, side * S, C))

    y_tail = W / 2 + FRONT + EAVES
    x_verge = L / 2 + FRONT + VERGE
    rafters = {side: sh.Grain('timber_hut rafters %s' % ('front' if side < 0 else 'back'), wood, (0, side * C, -S), rnd, x_hint=(1, 0, 0))
               for side in (-1, 1)}
    n_raft = max(2, int(round((L - 0.1) / 0.6)) + 1)
    raft_x = [-L / 2 + 0.05 + (L - 0.1) * k / (n_raft - 1) for k in range(n_raft)]

    def at_u(side, x, u, h):
        return sp(side, x, (u - h * S) / C, h)

    for side in (-1, 1):
        for x in raft_x:
            ring_top, ring_tail = [], []
            for dx, h in ((-0.025, -PURLIN_D - RAFTER_D), (0.025, -PURLIN_D - RAFTER_D), (0.025, -PURLIN_D), (-0.025, -PURLIN_D)):
                ring_top.append(at_u(side, x + dx, 0.015, h))
                ring_tail.append(at_u(side, x + dx, y_tail, h))
            sh.add_hexahedron(rafters[side], ring_top + ring_tail)
        # purlins along the roof: one near the tails, one over the wall, then up to the ridge
        us = [y_tail - 0.07, W / 2 - 0.04]
        u = W / 2 - 0.04
        while u - 0.82 > 0.12:
            u -= 0.82
            us.append(u)
        for u in us:
            t_c = u / C
            sh.add_beam(along_x, sp(side, -x_verge + 0.03, t_c, -PURLIN_D / 2), sp(side, x_verge - 0.03, t_c, -PURLIN_D / 2), 0.075, PURLIN_D,
                        up=normal(side))
        # wall plate and the eaves blocking between the rafters
        sh.add_box(along_x, (-L / 2, side * (W / 2 - 0.1) - 0.0 if side > 0 else -W / 2, z_wp - 0.1), (L / 2, W / 2 if side > 0 else -W / 2 + 0.1, z_wp))
        y_in, y_out = side * (W / 2 - 0.05), side * W / 2
        z_in = origin_z - (W / 2 - 0.05) * T - 0.005
        z_out = origin_z - (W / 2) * T - 0.005
        pts = [Vector((-L / 2, y_in, z_wp)), Vector((L / 2, y_in, z_wp)), Vector((L / 2, y_out, z_wp)), Vector((-L / 2, y_out, z_wp)),
               Vector((-L / 2, y_in, z_in)), Vector((L / 2, y_in, z_in)), Vector((L / 2, y_out, z_out)), Vector((-L / 2, y_out, z_out))]
        sh.add_hexahedron(along_x, pts)
    # ridge board
    z_ridge_rb = z_wp + (W / 2) * T
    sh.add_box(along_x, (-L / 2, -0.015, z_ridge_rb - 0.06), (L / 2, 0.015, origin_z - PURLIN_D / C))
    # tie beams and king posts every few rafters (seen inside)
    for k in range(2, n_raft - 2, 4):
        x = raft_x[k] + 0.05
        sh.add_box(along_y, (x - 0.025, -W / 2 + 0.02, z_wp), (x + 0.025, W / 2 - 0.02, z_wp + 0.15))
        sh.add_box(along_z, (x - 0.04, -0.04, z_wp + 0.15), (x + 0.04, 0.04, z_ridge_rb))

    # fascia and barge boards
    fascia = sh.Builder('timber_hut fascia and barge boards', boards)
    f_tone = fascia.layer('board_tone')
    for side in (-1, 1):
        z_top = origin_z - (y_tail + 0.025) * T - 0.002
        y0, y1 = sorted((side * y_tail, side * (y_tail + 0.025)))
        sh.add_box(fascia, (-x_verge, y0, z_top - 0.2), (x_verge, y1, z_top), layer=f_tone, value=0.5)
        for xs in (-1, 1):
            x0, x1 = sorted((xs * x_verge, xs * (x_verge - 0.026)))
            ring_apex, ring_eaves = [], []
            for x, h in ((x0, -0.23), (x1, -0.23), (x1, -0.003), (x0, -0.003)):
                ring_apex.append(at_u(side, x, 0.0, h))
                ring_eaves.append(at_u(side, x, y_tail + 0.025, h))
            sh.add_hexahedron(fascia, ring_apex + ring_eaves, layer=f_tone, value=0.5)

    # ---------------------------------------------------------------- corrugated iron sheets
    t_end = (y_tail + 0.025 + 0.06) / C
    rows = [(t_end - 1.86, t_end), (0.012, t_end - 1.71)] if t_end > 2.7 else [(0.012, t_end)]
    x_start, x_end = -x_verge - 0.04, x_verge + 0.04
    n_sheets = int(math.ceil((x_end - x_start - LAMBDA) / COVER))
    sheet_groups = {}
    for side in (-1, 1):
        for g in range(4):
            shift = Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5), 0.0))
            matrix = Matrix.Translation(shift) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
            sheet_groups[(side, g)] = sh.Builder('timber_hut roof sheets %s %d' % ('front' if side < 0 else 'back', g + 1), sheets_worn,
                                                 matrix=matrix, extra_materials=(sheets_rusty,))
    rusty_columns = {side: [rnd.random() < 0.16 for _ in range(n_sheets)] for side in (-1, 1)}
    for side in (-1, 1):
        for r, (t0, t1) in enumerate(rows):
            for k in range(n_sheets):
                x0 = x_start + k * COVER
                x1 = min(x0 + COVER + LAMBDA, x_end)
                if x1 - x0 < 2 * LAMBDA:
                    continue
                builder = sheet_groups[(side, (k + 2 * r) % 4)]
                lift = (0.004 if k % 2 else 0.0) + (0.009 if r == 1 else 0.0) + rnd.uniform(0.0, 0.0015)
                bow = rnd.uniform(-0.004, 0.004)
                rusty = 1 if (rusty_columns[side][k] != (rnd.random() < 0.08)) else 0
                _sheet(builder, side, sp, x0, x1, t0, t1, x_start, lift, bow, rusty)
    # ridge cap: two flanges and a roll
    ridge = sh.Builder('timber_hut ridge cap and flashing', flashing)
    h_cap = 2 * AMP + 0.013 + SHEET_T + 0.004
    for side in (-1, 1):
        ring_a, ring_b = [], []
        for t_, h in ((-0.004, h_cap), (0.17, h_cap), (0.17, h_cap + 0.002), (-0.004, h_cap + 0.002)):
            ring_a.append(sp(side, x_start + 0.01, t_, h))
            ring_b.append(sp(side, x_end - 0.01, t_, h))
        sh.add_hexahedron(ridge, ring_a + ring_b)
    roll_z = origin_z + (h_cap + 0.002) * C + 0.012
    sh.add_cylinder(ridge, (x_start + 0.01, 0, roll_z), (x_end - 0.01, 0, roll_z), 0.028, segments=12)

    # ---------------------------------------------------------------- stove pipe through the back slope, the stove under it
    gaps = [(a + b) / 2 for a, b in zip(raft_x[:-1], raft_x[1:])]
    pipe_x = min(gaps, key=lambda g: abs(g - (L / 2 - 1.7)))
    pipe_u = 0.95
    pipe_y = pipe_u
    roof_z = origin_z - pipe_u * T
    pipe_top = origin_z + 2 * AMP + 0.85
    stove_top = z_floor + 0.72
    sh.add_cylinder(iron, (pipe_x, pipe_y, stove_top - 0.02), (pipe_x, pipe_y, pipe_top), 0.065, segments=14)
    sh.add_cylinder(iron, (pipe_x, pipe_y, pipe_top - 0.02), (pipe_x, pipe_y, pipe_top + 0.005), 0.072, segments=14)
    sh.add_cylinder(iron, (pipe_x, pipe_y, pipe_top + 0.075), (pipe_x, pipe_y, pipe_top + 0.19), 0.17, 0.018, segments=14)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        p0 = Vector((pipe_x + math.cos(a) * 0.06, pipe_y + math.sin(a) * 0.06, pipe_top - 0.05))
        p1 = Vector((pipe_x + math.cos(a) * 0.1, pipe_y + math.sin(a) * 0.1, pipe_top + 0.09))
        sh.add_beam(iron, p0, p1, 0.018, 0.004, up=(math.cos(a), math.sin(a), 0))
    # stay wires down to the roof
    for a in (0.6, 2.6, 4.5):
        top = Vector((pipe_x, pipe_y, pipe_top - 0.25)) + Vector((math.cos(a), math.sin(a), 0)) * 0.066
        foot_u = pipe_u + math.sin(a) * 0.75
        foot = Vector((pipe_x + math.cos(a) * 0.75, foot_u, origin_z - foot_u * T + 2 * AMP + 0.015))
        sh.tube(iron.bm, [to - Vector() for to in sh.sag_line(top, foot, 0.01, 6)], 0.003, sides=4,
                matrix=None)
    # flashing plate on the crests and a collar
    t_p = pipe_u / C
    hp = 2 * AMP + 0.013 + SHEET_T + 0.002
    ring_a = [sp(1, pipe_x - 0.26, t_p - 0.3, hp), sp(1, pipe_x + 0.26, t_p - 0.3, hp), sp(1, pipe_x + 0.26, t_p - 0.3, hp + 0.002), sp(1, pipe_x - 0.26, t_p - 0.3, hp + 0.002)]
    ring_b = [sp(1, pipe_x - 0.26, t_p + 0.28, hp), sp(1, pipe_x + 0.26, t_p + 0.28, hp), sp(1, pipe_x + 0.26, t_p + 0.28, hp + 0.002), sp(1, pipe_x - 0.26, t_p + 0.28, hp + 0.002)]
    sh.add_hexahedron(ridge, ring_a + ring_b)
    collar_z = origin_z - pipe_u * T
    sh.add_cylinder(ridge, (pipe_x, pipe_y, collar_z - 0.03), (pipe_x, pipe_y, collar_z + 0.13), 0.11, 0.071, segments=14)
    # the stove: a round iron stove on three legs, on an iron hearth plate
    sh.add_box(iron, (pipe_x - 0.4, pipe_y - 0.4, z_floor), (pipe_x + 0.4, pipe_y + 0.4, z_floor + 0.006))
    stove_profile = [(0.002, 0.12), (0.2, 0.12), (0.24, 0.16), (0.25, 0.3), (0.245, 0.55), (0.21, 0.66), (0.12, 0.71), (0.002, 0.72)]
    sh.lathe(iron.bm, [(r, z) for r, z in stove_profile], segments=16, centre=(pipe_x, pipe_y, z_floor), close_bottom=False, close_top=False)
    for k in range(3):
        a = 2 * math.pi * k / 3
        sh.add_cylinder(iron, (pipe_x + math.cos(a) * 0.17, pipe_y + math.sin(a) * 0.17, z_floor + 0.006),
                        (pipe_x + math.cos(a) * 0.15, pipe_y + math.sin(a) * 0.15, z_floor + 0.14), 0.025, 0.02, segments=6)
    front_stove = Vector((pipe_x, pipe_y - 0.25, z_floor + 0.35))
    sh.add_box(iron, front_stove + Vector((-0.08, -0.012, -0.07)), front_stove + Vector((0.08, 0.01, 0.07)))

    # ---------------------------------------------------------------- inside: lining with holes for the openings, table, benches, lamp
    def line_wall(wall, s_lo, s_hi, z_lo, z_hi, opens):
        ss = sorted({s_lo, s_hi} | {v for op in opens for v in (op['sa'], op['sb']) if s_lo < v < s_hi})
        zs = sorted({z_lo, z_hi} | {v for op in opens for v in (op['za'], op['zb']) if z_lo < v < z_hi})
        for s0, s1 in zip(ss[:-1], ss[1:]):
            for z0, z1 in zip(zs[:-1], zs[1:]):
                sm, zm = (s0 + s1) / 2, (z0 + z1) / 2
                if any(op['sa'] < sm < op['sb'] and op['za'] < zm < op['zb'] for op in opens):
                    continue
                vs = [lining.bm.verts.new(wall.p(s, LINING, z)) for s, z in ((s0, z1), (s1, z1), (s1, z0), (s0, z0))]
                lining.bm.faces.new(vs)

    line_wall(front, -L / 2 - LINING, L / 2 + LINING, z_floor, z_wp, front_open)
    line_wall(back, -L / 2 - LINING, L / 2 + LINING, z_floor, z_wp, back_open)
    for gable_wall in (right, left):
        line_wall(gable_wall, -W / 2 - LINING, W / 2 + LINING, z_floor, z_wp, [])
        hw = W / 2 + LINING
        vs = [lining.bm.verts.new(gable_wall.p(s, LINING, z)) for s, z in
              ((-hw, z_wp + (-LINING) * T), (0.0, z_wp + (W / 2) * T), (hw, z_wp + (-LINING) * T), (hw, z_wp), (-hw, z_wp))]
        lining.bm.faces.new(vs)

    table = sh.Grain('timber_hut table and benches', wood, (1, 0, 0), rnd)
    legs = sh.Grain('timber_hut table legs', wood, (0, 0, 1), rnd)
    tx, ty = -L / 4 - 0.3, -0.35
    sh.add_box(table, (tx - 1.0, ty - 0.36, z_floor + 0.72), (tx + 1.0, ty + 0.36, z_floor + 0.755))
    sh.add_box(table, (tx - 0.9, ty - 0.05, z_floor + 0.62), (tx + 0.9, ty + 0.05, z_floor + 0.66))
    for bx in (tx - 0.8, tx + 0.8):
        for dy in (-0.28, 0.28):
            sh.add_beam(legs, (bx, ty + dy * 1.15, z_floor), (bx, ty + dy * 0.8, z_floor + 0.72), 0.06, 0.06, up=(0, 1, 0))
        sh.add_box(table, (bx - 0.03, ty - 0.33, z_floor + 0.66), (bx + 0.03, ty + 0.33, z_floor + 0.72))
    for by in (ty - 0.68, ty + 0.68):
        sh.add_box(table, (tx - 0.95, by - 0.13, z_floor + 0.43), (tx + 0.95, by + 0.13, z_floor + 0.465))
        for bx in (tx - 0.8, tx + 0.8):
            sh.add_box(legs, (bx - 0.025, by - 0.11, z_floor), (bx + 0.025, by + 0.11, z_floor + 0.43))

    tie_xs = [raft_x[k] + 0.05 for k in range(2, n_raft - 2, 4)]
    lamp_x = min(tie_xs, key=abs) if tie_xs else 0.0
    lamp_z = z_wp - 0.55
    sh.add_cylinder(iron, (lamp_x, 0.0, lamp_z + 0.13), (lamp_x, 0.0, z_wp), 0.003, segments=4)
    sh.add_cylinder(iron, (lamp_x, 0.0, lamp_z - 0.1), (lamp_x, 0.0, lamp_z - 0.06), 0.06, segments=12)
    sh.add_cylinder(iron, (lamp_x, 0.0, lamp_z + 0.07), (lamp_x, 0.0, lamp_z + 0.13), 0.06, 0.02, segments=12)
    lamp_glass = sh.Builder('timber_hut lamp glass', 'LAMP • honey flame glow' if lit_windows else 'GLASS • sleeping navy interiors', smooth=True)
    sh.lathe(lamp_glass.bm, [(0.02, -0.06), (0.045, -0.03), (0.05, 0.0), (0.045, 0.04), (0.02, 0.07)], segments=12,
             centre=(lamp_x, 0.0, lamp_z))

    for builder in (walls_b, trims, sash, glass, backing, lining, door, iron, steps_x, steps_s, along_x, along_z, along_y,
                    floor, fascia, ridge, table, legs, lamp_glass, *rafters.values(), *sheet_groups.values()):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    for obj in made:
        if obj.name.startswith('timber_hut lamp glass'):
            obj.visible_shadow = False
    if lit_windows:
        made.append(sh.point_light('timber_hut lamp light', collection, (lamp_x, 0.0, lamp_z), 45.0, (1.0, 0.56, 0.24), 0.04))
    return made


def _sheet(builder, side, sp, x0, x1, t0, t1, x_phase, lift, bow, material_index):
    """One corrugated sheet as a thin closed shell, corrugations running down the slope."""
    bm = builder.bm
    nx = max(2, int(round((x1 - x0) / (LAMBDA / 8.0))))
    nt = 3
    grid = []
    for layer_h in (SHEET_T, 0.0):
        rows_ = []
        for j in range(nt + 1):
            t_ = t0 + (t1 - t0) * j / nt
            row = []
            for i in range(nx + 1):
                x = x0 + (x1 - x0) * i / nx
                h = lift + AMP * (1.0 - math.cos(2 * math.pi * (x - x_phase) / LAMBDA)) + bow * math.sin(math.pi * j / nt) + layer_h
                row.append(bm.verts.new(sh.to_local(builder, sp(side, x, t_, h))))
            rows_.append(row)
        grid.append(rows_)
    top, bottom = grid
    faces = []
    for j in range(nt):
        for i in range(nx):
            faces.append(bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i])))
            faces.append(bm.faces.new((bottom[j][i], bottom[j + 1][i], bottom[j + 1][i + 1], bottom[j][i + 1])))
    for i in range(nx):
        faces.append(bm.faces.new((top[0][i], bottom[0][i], bottom[0][i + 1], top[0][i + 1])))
        faces.append(bm.faces.new((top[nt][i + 1], bottom[nt][i + 1], bottom[nt][i], top[nt][i])))
    for j in range(nt):
        faces.append(bm.faces.new((top[j + 1][0], bottom[j + 1][0], bottom[j][0], top[j][0])))
        faces.append(bm.faces.new((top[j][nx], bottom[j][nx], bottom[j + 1][nx], top[j + 1][nx])))
    for f in faces:
        f.material_index = material_index
    bmesh.ops.recalc_face_normals(bm, faces=faces)
