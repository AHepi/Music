"""
What this file does: lays hand-dressed kerbstones along a line or curve you give: the line is the kerb's top edge on
the road side (the road's edge). Each stone is its own length and shade, tipped a little towards the road and settled
a little out of level, with a gap at every joint; its road face leans back slightly, its top falls a little towards
the road, its edges are worn round; chips are knocked off the road-side top edge where cart wheels hit it, most of all
at the stones' corners. Its top stands at the height you give above the line, its back at the width you give from it.
As an option a row of flat channel (gutter) stones is laid along the kerb's foot on the road side, dished so water runs
along the kerb. Nothing here chooses where a kerb goes: the line, its side and its sizes are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import lay_kerb
    made = lay_kerb.lay([(3.45, -9, 0), (3.45, 24, 0), (4.6, 26.6, 0), (8, 27.2, 0)], road='left', height=0.13, seed=1)
    made['kerb']                      # the kerbstones (made['kerb']['stones'] counts them, ['chips'] the chips)
    made = lay_kerb.lay(curve_object, road='right', channel=0.3, seed=2)
    made['channel']                   # the channel stones, when asked for

The line may be a list of points (x, y, z), a curve object, a mesh object made of a line of edges, or the path of a
JSON file holding {"points": [[x, y, z], ...]}. Its z is the road's surface there (the setts' tops): the kerb's top
stands `height` above it. `road` says on which side of the line the road lies, looking along the line from its first
point: the kerb is laid on the other side, from the line back to `width`. By default (smooth) a few points give a smooth
curve through them and the stones bend with it (as quadrant kerbs round a street corner); with smooth=False the kerb
runs straight between your points and a stone never spans a turn.

From the command line:

    python3 lay_kerb.py --help
    python3 lay_kerb.py --points "3.45,-9,0 3.45,20,0" --road left --channel 0.3 --out kerb.blend
    python3 lay_kerb.py --blend street.blend --line "Kerb line" --road right --out street_kerbed.blend

Options, with their defaults:
    road            'left'   which side of the line the road lies on, looking along it from its first point
    height          0.13 m   the road's surface (the line) to the kerb's top at its back
    width           0.30 m   the kerb's top, from the line back (away from the road)
    depth           0.30 m   the whole stone, top to foot (all but `height` of it is under the road)
    length          1.0 m    about how long each stone is (each its own, from 0.75 to 1.25 of this)
    gap             0.01 m   about how wide the joints are (each its own)
    lean            1.0      how far the stones have moved since they were laid: tipped towards the road, settled out
                             of level, a little out of line; 0 laid true
    chips           1.0      about how many chips per metre of the road-side top edge (more at the corners); 0 none
    shades          0.25     how much one stone is lighter or darker than the next, 0 to 0.9 (a copy of the material
                             named '<material> • stone by stone' reads it); 0 uses your material as it is
    channel         0        the width of a row of channel stones along the kerb's foot on the road side, metres
                             (0.25 to 0.4 is usual); 0 none. The channel takes that much of the road: stop the setts there
    dish            0.012 m  how much lower the channel is at the kerb than at its road edge (water runs at the kerb)
    smooth          True     a smooth curve through your points; False: straight between them
    seed            0        the same seed lays the same kerb
    material        'SURFACE • worn_rock_natural_01'   the stones: a store name or a material you hold (photographed;
                    the street's own 'STONE • worn honey-grey architectural dressings' still works by name)
    channel_material  none   the channel stones (none: the kerb's material)
    collection      none     where the objects go (a new collection 'lay_kerb')

What it makes: 'kerbstones' (obj['stones'], obj['chips']) and, when asked, 'kerb channel' (obj['stones']). Every face
carries its stone's 'stone_tone' (0 to 1, its shade), 'stone_number' and 'pp_piece' (0 to 1, its own random number: a
photographed material shows each stone its own part of its pictures by it); every point of the kerbstones carries
'kerb_chip', how far a chip cut it back (metres; 0 where the stone is whole).

Along a road laid by lay_cobbles.lay_setts_along, lay_cobbles.road_edges(line, width) gives its two edges at the setts'
tops: lay_kerb.lay(left, road='right') and lay_kerb.lay(right, road='left') stand the kerbs exactly at the road's edge.
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _lines  # noqa: E402
import _rough_stones  # noqa: E402

STONE = 'SURFACE • worn_rock_natural_01'                 # photographed (decision 80; brief/store/materials/Photographed.md)
OLD_STONE = 'STONE • worn honey-grey architectural dressings'     # the street's own: still there by name
UP = Vector((0.0, 0.0, 1.0))
BATTER = 0.012            # metres the road face stands further out at the road's level than at the top
STEP = 0.015              # metres between the slices a stone is built from (fine enough for a chip to bite)

TOOL = {
    'name': 'lay_kerb',
    'what': 'hand-dressed kerbstones along a line or curve you give (the road-side top edge): each stone its own length '
            'and shade, tipped and settled a little, gaps at the joints, worn round edges, chips knocked off the '
            'road-side edge where cart wheels hit; a row of dished channel (gutter) stones as an option',
    'call': "lay_kerb.lay([(3.45, -9, 0), (3.45, 24, 0), (4.6, 26.6, 0), (8, 27.2, 0)], road='left', height=0.13, channel=0.3, seed=1)",
    'options': {
        'road': "which side of the line the road lies on, looking along it from its first point: 'left' or 'right' ('left')",
        'height': "the road's surface (the line's own height) to the kerb's top (0.13 m)",
        'width': "the kerb's top, from the line back away from the road (0.30 m)",
        'depth': 'the whole stone, top to foot; all but the height is under the road (0.30 m)',
        'length': 'about how long each stone is; each its own, 0.75 to 1.25 of it (1.0 m)',
        'gap': 'about how wide the joints are (0.01 m)',
        'lean': 'how far the stones have moved: tipped towards the road, settled out of level, a little out of line; 0 laid true (1.0)',
        'chips': 'about how many chips per metre of the road-side top edge, more at the corners; 0 none (1.0)',
        'shades': 'how much one stone is lighter or darker than the next, 0 to 0.9 (0.25; 0 uses your material as it is)',
        'channel': 'the width of a row of channel stones along the foot on the road side, metres; 0 none (0)',
        'dish': 'how much lower the channel is at the kerb than at its road edge (0.012 m)',
        'smooth': 'a smooth curve through your points, the stones bending with it; a curve object keeps its own shape (True); False: straight runs',
        'seed': 'the same seed lays the same kerb (0)',
        'material, channel_material': "the stones (default '%s', photographed; the street's own '%s' still works by name); the channel's (default the kerb's)" % (STONE, OLD_STONE),
        'collection': "where the objects go (a new collection 'lay_kerb')",
    },
    'materials': [STONE, OLD_STONE],
    'source': "`kerb_run` in the town street builder's '55 street - render_final.py' (line 229) and the second builder's "
              "kerb chips (line 1210), made into a tool: the builder's plain boxes now follow a curve, each stone tipped, "
              "settled and shaded on its own, and the chips cut into the road-side edge where wheels hit instead of "
              "denting every face of every stone with one noise",
    'trap': "the line is the kerb's road-side top edge, not its middle, and `road` must name the road's side or the kerb "
            "is laid into the road (along a road laid on a line, take its edges from lay_cobbles.road_edges); with "
            "channel stones, stop the setts `channel` metres short of the line; call store.prepare_for_render(scene) "
            "once before drawing",
}


# ------------------------------------------------------------------------------------------------ the line

class _Run:
    """One stretch of the line the stones are laid along: a finely sampled path with its own heights."""

    def __init__(self, points):
        self.path = _lines.Path(points)
        self.total = self.path.total

    def frame(self, s, away_sign):
        """The point on the line `s` metres along, and the flat unit way away from the road there."""
        here = self.path.at(s)
        ahead = self.path.at(min(s + 0.02, self.total)) - self.path.at(max(s - 0.02, 0.0))
        ahead = Vector((ahead.x, ahead.y, 0.0))
        ahead = ahead.normalized() if ahead.length > 1e-9 else Vector((1.0, 0.0, 0.0))
        away = Vector((ahead.y, -ahead.x, 0.0)) * away_sign
        return here, away


def _runs(line, smooth):
    """The stretches to lay: one smooth curve through the points, or (smooth=False) one straight run per segment."""
    points = []
    for point in _lines.line_points(line):
        p = Vector((point[0], point[1], point[2] if len(point) > 2 else 0.0))
        if points and (p.xy - points[-1].xy).length < 1e-5:
            continue
        points.append(p)
    if len(points) < 2:
        raise ValueError('the line needs at least two different points (seen from above)')
    is_object = isinstance(line, bpy.types.Object)
    if not smooth:
        return [_Run([a, b]) for a, b in zip(points[:-1], points[1:])]
    if is_object:                                    # a curve object keeps its own shape (already finely sampled)
        return [_Run(points)]
    return [_Run(_lines.Path(points).smooth(0.05).points)]


# ------------------------------------------------------------------------------------------------ one stone

def _kerb_profile(height, width, depth, fall=0.005, front=0.015, back=0.008):
    """The kerbstone's cross-section going round it, as (t, v, (in_t, in_v)): t metres from the line away from the
    road, v metres up from the road's surface, and the way into the stone from that point (where a chip pushes it).
    The road face leans back (BATTER), the top falls `fall` towards the road, the edges are worn round."""
    foot = height - depth
    top_front = height - fall

    def face_t(v):
        return -BATTER * (1.0 - min(max(v, 0.0), height) / height)

    profile = [(-BATTER, foot, (1.0, 0.0))]
    knee = top_front - front
    for v in (0.0, knee * 0.35, knee * 0.65, knee - 0.05, knee - 0.032, knee - 0.018, knee - 0.007):
        if v > profile[-1][1] + 0.004 and v < knee - 0.002:
            profile.append((face_t(v), v, (1.0, 0.0)))
    for degrees in (180.0, 150.0, 120.0):            # the worn front edge, from the face over to the top
        a = math.radians(degrees)
        profile.append((front + front * math.cos(a), knee + front * math.sin(a), (-math.cos(a), -math.sin(a))))
    tops = [front + d for d in (0.0, 0.008, 0.02, 0.035, 0.055, 0.08)]
    t = tops[-1]
    while t < width - back - 0.05:
        t += 0.04
        tops.append(t)
    for t in tops:
        if t < width - back - 0.01:
            profile.append((t, top_front + fall * t / width, (0.0, -1.0)))
    for degrees in (90.0, 45.0, 0.0):                # the back edge, rounded a little less
        a = math.radians(degrees)
        profile.append((width - back + back * math.cos(a), height - back + back * math.sin(a), (-math.cos(a), -math.sin(a))))
    profile.append((width, foot, (-1.0, 0.0)))
    return profile


def _channel_profile(channel, dish, thick=0.12, edge=0.006):
    """A channel stone's cross-section (t negative: towards the road), its top falling `dish` towards the kerb."""
    inner = -BATTER - 0.006
    outer = inner - channel

    def top(t):
        return -dish * (t - outer) / (inner - outer)

    profile = [(outer, -thick, (1.0, 0.0)), (outer, top(outer) - edge, (1.0, 0.0)),
               (outer + edge * 0.3, top(outer) - edge * 0.3, (0.7, -0.7))]
    steps = 6
    for k in range(steps + 1):
        t = outer + edge + (channel - 2 * edge) * k / steps
        profile.append((t, top(t), (0.0, -1.0)))
    profile += [(inner - edge * 0.3, top(inner) - edge * 0.3, (-0.7, -0.7)), (inner, top(inner) - edge, (-1.0, 0.0)),
                (inner, -thick, (-1.0, 0.0))]
    return profile


def _slices(s0, s1):
    """Where along the stone its slices go, and how far each is drawn in (the worn ends)."""
    length = s1 - s0
    ends = [(0.0, 0.006), (0.005, 0.0022), (0.014, 0.0006)]
    middle = []
    count = max(1, int(math.ceil((length - 0.028) / STEP)))
    for k in range(1, count):
        middle.append((0.014 + (length - 0.028) * k / count, 0.0))
    first = [(s0 + d, inset) for d, inset in ends]
    last = [(s1 - d, inset) for d, inset in reversed(ends)]
    return first + [(s0 + d, inset) for d, inset in middle] + last


def _chips_for(s0, s1, chips, rng):
    """The chips knocked off one stone's road-side top edge: (along, reach along, reach in, reach down)."""
    if chips <= 0:
        return []
    found = []
    expected = chips * (s1 - s0)
    count = 0
    threshold = math.exp(-expected)                     # a Poisson count of chips along the edge
    product = rng.random()
    while product > threshold and count < 12:
        count += 1
        product *= rng.random()
    for _ in range(count):
        found.append((rng.uniform(s0 + 0.04, s1 - 0.04), rng.uniform(0.028, 0.075), rng.uniform(0.014, 0.04),
                      rng.uniform(0.02, 0.055)))
    for end in (s0, s1):                                # the corners take the worst knocks
        if rng.random() < min(0.85, 0.4 * chips):
            found.append((end + rng.uniform(-0.01, 0.01), rng.uniform(0.035, 0.09), rng.uniform(0.018, 0.05),
                          rng.uniform(0.025, 0.07)))
    return found


def _chip_cut(s, t, v, inward, top_v, chips, rng):
    """How far (metres) the chips push a point of the stone into it, along `inward` (in the (t, v) cross-section)."""
    deepest = 0.0
    for along, a, b, c in chips:
        ds = (s - along) / a
        if abs(ds) >= 1.0:
            continue
        tc, vc = -0.004, top_v + 0.004                  # the chip's middle: just outside the worn edge
        dt, dv = (t - tc) / b, (v - vc) / c
        q = ds * ds + dt * dt + dv * dv
        if q >= 1.0:
            continue
        nt, nv = inward
        A = (nt / b) ** 2 + (nv / c) ** 2
        if A < 1e-12:
            continue
        B = 2.0 * ((t - tc) * nt / (b * b) + (v - vc) * nv / (c * c))
        C = q - 1.0
        k = (-B + math.sqrt(max(B * B - 4.0 * A * C, 0.0))) / (2.0 * A)
        deepest = max(deepest, k)
    if deepest > 0:
        deepest *= rng.uniform(0.88, 1.12)              # a broken face is never smooth
    return deepest


class _Stones:
    """Stones gathered into one mesh: each a sweep of its cross-section along the line, capped at both ends."""

    def __init__(self):
        self.verts, self.faces, self.face_tone, self.face_number, self.vert_chip = [], [], [], [], []
        self.face_piece = []
        self.count = 0
        self.chips = 0

    def stone(self, run, away_sign, s0, s1, profile, rng, tone, lean, chips=(), top_v=0.0, settle=(0.0, 0.0),
              tip=0.0, shift=(0.0, 0.0), piece=0.0):
        n = len(profile)
        back_t = max(p[0] for p in profile)
        back_v = max(p[1] for p in profile)
        centre_t = sum(p[0] for p in profile) / n
        centre_v = sum(p[1] for p in profile) / n
        base = len(self.verts)
        rings = 0
        for s, inset in _slices(s0, s1):
            here, away = run.frame(s, away_sign)
            share = (s - s0) / max(s1 - s0, 1e-6)
            dz = settle[0] + (settle[1] - settle[0]) * share
            dt = shift[0] + (shift[1] - shift[0]) * share
            for t, v, inward in profile:
                if inset > 0:                                       # the worn ends: drawn in towards the middle
                    to_t, to_v = centre_t - t, centre_v - v
                    size = math.hypot(to_t, to_v) or 1.0
                    t, v = t + to_t / size * inset, v + to_v / size * inset
                cut = _chip_cut(s, t, v, inward, top_v, chips, rng) if chips else 0.0
                if cut > 0:
                    t, v = t + inward[0] * cut, v + inward[1] * cut
                # tipped towards the road about its back top edge (its front sinks; its back stays at the height
                # asked), then settled and shifted
                pt, pv = t - back_t, v - back_v
                t = back_t + pt * math.cos(tip) - pv * math.sin(tip)
                v = back_v + pt * math.sin(tip) + pv * math.cos(tip)
                world = here + away * (t + dt) + UP * (v + dz)
                self.verts.append(tuple(world))
                self.vert_chip.append(cut)
            rings += 1
        for r in range(rings - 1):
            a, b = base + r * n, base + (r + 1) * n
            for j in range(n):
                k = (j + 1) % n
                self.faces.append((a + j, a + k, b + k, b + j))
        self.faces.append(tuple(base + j for j in range(n)))
        last = base + (rings - 1) * n
        self.faces.append(tuple(last + j for j in reversed(range(n))))
        added = (rings - 1) * n + 2
        self.face_tone.extend([tone] * added)
        self.face_number.extend([self.count] * added)
        self.face_piece.extend([piece] * added)
        self.count += 1
        self.chips += len(chips)

    def make(self, name, material, collection, ground):
        mesh = bpy.data.meshes.new(name)
        origin = Vector(self.verts[0]) if self.verts else Vector()
        mesh.from_pydata([tuple(Vector(v) - origin) for v in self.verts], [], self.faces)
        for attribute, kind, domain, values in (('stone_tone', 'FLOAT', 'FACE', self.face_tone),
                                                ('stone_number', 'INT', 'FACE', self.face_number),
                                                ('pp_piece', 'FLOAT', 'FACE', self.face_piece),
                                                ('kerb_chip', 'FLOAT', 'POINT', self.vert_chip)):
            layer = mesh.attributes.new(attribute, kind, domain)
            if values:
                layer.data.foreach_set('value', values)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces[:])
        tool.to_mesh(mesh)
        tool.free()
        mesh.shade_smooth()
        if hasattr(mesh, 'set_sharp_from_angle'):
            mesh.set_sharp_from_angle(angle=math.radians(38.0))
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = origin
        collection.objects.link(obj)
        store.use_material(obj, material, ground=ground)
        obj['stones'] = self.count
        return obj


def _lengths(total, length, rng, smallest):
    """Stone lengths filling a run end to end: each its own, the last ones fitted to the run."""
    pieces = []
    left = total
    while left > 1e-6:
        piece = length * rng.uniform(0.75, 1.25)
        if left - piece < smallest:
            if left > 1.6 * smallest and left > piece * 0.9:
                pieces += [left / 2, left / 2]           # two closers rather than one long stone
            else:
                pieces.append(left)
            break
        pieces.append(piece)
        left -= piece
    return pieces


def _material(name_or_material):
    return store.material(name_or_material) if isinstance(name_or_material, str) else name_or_material


# ------------------------------------------------------------------------------------------------ laying

def lay(line, road='left', height=0.13, width=0.30, depth=0.30, length=1.0, gap=0.01, lean=1.0, chips=1.0, shades=0.25,
        channel=0.0, dish=0.012, smooth=True, seed=0, material=STONE, channel_material=None, collection=None):
    """Lay the kerb along the line (its road-side top edge); returns {'kerb': obj} and, with a channel, 'channel'."""
    if road not in ('left', 'right'):
        raise ValueError("road is 'left' or 'right' (the road's side of the line, looking along it), not %r" % (road,))
    height, width, depth, length, gap = float(height), float(width), float(depth), float(length), float(gap)
    lean, chips, shades, channel, dish = float(lean), float(chips), float(shades), float(channel), float(dish)
    if not 0.0 <= height <= 0.5:
        raise ValueError('height is 0 to 0.5 m above the road, not %r' % (height,))
    if not 0.08 <= width <= 1.0:
        raise ValueError('width is 0.08 to 1 m, not %r' % (width,))
    if not height + 0.05 <= depth <= 1.5:
        raise ValueError('depth (top to foot) must be at least the height and 5 cm more (%.2f m), and at most 1.5 m; not %r' % (height + 0.05, depth))
    if not 0.2 <= length <= 3.0:
        raise ValueError('length is 0.2 to 3 m, not %r' % (length,))
    if not 0.0 <= gap <= 0.05:
        raise ValueError('gap is 0 to 0.05 m, not %r' % (gap,))
    if not 0.0 <= lean <= 3.0:
        raise ValueError('lean is 0 (laid true) to 3, not %r' % (lean,))
    if not 0.0 <= chips <= 10.0:
        raise ValueError('chips is 0 to 10 per metre, not %r' % (chips,))
    if not 0.0 <= shades <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    if not (channel == 0.0 or 0.1 <= channel <= 1.0):
        raise ValueError('channel is 0 (none) or a width of 0.1 to 1 m, not %r' % (channel,))
    if not 0.0 <= dish <= 0.05:
        raise ValueError('dish is 0 to 0.05 m, not %r' % (dish,))
    runs = _runs(line, smooth)
    away_sign = 1.0 if road == 'left' else -1.0
    rng = random.Random(seed)
    piece_rng = random.Random(seed * 7919 + 606)       # each stone its own part of the photographs; moves no stone
    if collection is None:
        collection = bpy.data.collections.new('lay_kerb')
        bpy.context.scene.collection.children.link(collection)
    profile = _kerb_profile(height, width, depth)
    kerb = _Stones()
    ground = None
    for run in runs:
        start = 0.0
        for piece in _lengths(run.total, length, rng, smallest=min(0.35, length * 0.5)):
            joint = gap * rng.uniform(0.6, 1.5)
            s0, s1 = start + joint / 2, start + piece - joint / 2
            start += piece
            if s1 - s0 < 0.06:
                continue
            settle = (-lean * rng.uniform(0.0, 0.012), -lean * rng.uniform(0.0, 0.012))
            tip = math.radians(lean * rng.uniform(-0.3, 1.4))
            shift = (lean * rng.uniform(-0.004, 0.004), lean * rng.uniform(-0.004, 0.004))
            found = _chips_for(s0, s1, chips, rng)
            here, _ = run.frame(s0, away_sign)
            ground = here.z if ground is None else min(ground, here.z)
            kerb.stone(run, away_sign, s0, s1, profile, rng, rng.random(), lean, chips=found, top_v=height - 0.005,
                       settle=settle, tip=tip, shift=shift, piece=piece_rng.random())
    if kerb.count == 0:
        raise ValueError('the line is too short for a single kerbstone')
    stone = _rough_stones.shaded(_material(material), shades)
    made = {'kerb': kerb.make('kerbstones', stone, collection, ground)}
    made['kerb']['chips'] = kerb.chips
    if channel > 0:
        channel_rng = random.Random(seed * 7919 + 17)     # its own dice: asking for a channel moves no kerbstone
        channel_piece = random.Random(seed * 7919 + 707)
        gutter = _Stones()
        cross = _channel_profile(channel, dish)
        for run in runs:
            start = -channel_rng.uniform(0.15, 0.4)       # its joints fall between the kerb's
            for piece in _lengths(run.total - start, length * 0.75, channel_rng, smallest=0.25):
                joint = 0.008 * channel_rng.uniform(0.6, 1.5)
                s0, s1 = max(start + joint / 2, 0.0), start + piece - joint / 2
                start += piece
                if s1 - s0 < 0.06:
                    continue
                settle = (-lean * channel_rng.uniform(0.0, 0.006), -lean * channel_rng.uniform(0.0, 0.006))
                gutter.stone(run, away_sign, s0, s1, cross, channel_rng, channel_rng.random(), lean, settle=settle,
                             tip=math.radians(lean * channel_rng.uniform(-0.4, 0.4)), piece=channel_piece.random())
        gutter_material = _rough_stones.shaded(_material(channel_material if channel_material is not None else material), shades)
        made['channel'] = gutter.make('kerb channel', gutter_material, collection, ground)
    bpy.context.view_layer.update()
    return made


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of lay_kerb.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--points', help='the line (the kerb\'s road-side top edge) as "x,y,z x,y,z ..."; makes a new file unless --blend is given')
    parser.add_argument('--points-json', help='a JSON file holding {"points": [[x, y, z], ...]}')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--road', default='left', choices=['left', 'right'], help="the road's side of the line, looking along it; default left")
    for name, default, help_text in (('height', 0.13, "the road's surface to the kerb's top, metres"), ('width', 0.30, "the kerb's top, metres"),
                                     ('depth', 0.30, 'the whole stone, top to foot, metres'), ('length', 1.0, 'about how long each stone is, metres'),
                                     ('gap', 0.01, 'about how wide the joints are, metres'), ('lean', 1.0, 'how far the stones have moved, 0 laid true'),
                                     ('chips', 1.0, 'chips per metre of the road-side edge, about; 0 none'),
                                     ('shades', 0.25, 'how much one stone is lighter or darker than the next, 0 to 0.9'),
                                     ('channel', 0.0, 'the width of a row of channel stones on the road side, metres; 0 none'),
                                     ('dish', 0.012, 'how much lower the channel is at the kerb, metres')):
        parser.add_argument('--' + name, type=float, default=default, help='%s; default %s' % (help_text, default))
    parser.add_argument('--straight', action='store_true', help='straight between the points instead of a smooth curve')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same kerb; default 0')
    parser.add_argument('--out', help='save the result here (.blend)')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    line = None
    if args.line:
        line = bpy.data.objects.get(args.line)
        if line is None:
            parser.error('no object %r in the file; its objects are: %s' % (args.line, ', '.join(o.name for o in bpy.data.objects)))
    elif args.points_json:
        line = args.points_json
    elif args.points:
        line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()]
    if line is None:
        parser.error('give the line: --points, --points-json or --line')
    if not args.out:
        print('note: nothing will be saved; give --out FILE.blend to keep the kerb')
    made = lay(line, road=args.road, height=args.height, width=args.width, depth=args.depth, length=args.length, gap=args.gap,
               lean=args.lean, chips=args.chips, shades=args.shades, channel=args.channel, dish=args.dish,
               smooth=not args.straight, seed=args.seed)
    print('made', ', '.join('%s (%d stones)' % (obj.name, obj['stones']) for obj in made.values()), '-', made['kerb']['chips'], 'chips')
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)


if __name__ == '__main__':
    main()
