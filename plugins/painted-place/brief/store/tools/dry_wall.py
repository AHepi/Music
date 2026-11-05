"""
What this file does: lays a dry-stone wall along a line you give. Two faces of flat stones in rough courses, each stone
standing out on its own with a dark gap round it (no mortar), the courses smaller towards the top and every joint
crossed by the stone above it; the wall narrows as it rises (wider at its foot than under its top); long through-stones
every metre or so show their ends on both faces; a row of chunky coping stones stands on edge along the top, leaning
together in runs the way copes do; a dark core inside stops light showing through the gaps. Where you ask for a gap (a
gateway) the wall stops and is finished square with long end stones, as at the line's two ends. On a ground you give,
the wall's foot follows the ground's height (ground.height_at); without one it stands on the line's own heights.
Nothing here chooses where a wall goes: the line, the gaps and the sizes are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import dry_wall
    made = dry_wall.lay([(-6, 0, 0), (6, 0, 0), (6, 9, 0)], height=1.25, gaps=[(4.0, 7.0)], ground=yard, seed=3)
    made['stones'], made['coping'], made['core']        # the three objects it makes

The line may be a list of points (x, y, z), a curve object (it follows the curve whichever way it goes), a mesh object
made of a line of edges, or the path of a JSON file holding {"points": [[x, y, z], ...]}. By default (smooth) a few
points give a smooth curve through them, as a wall built round a bend: each face is laid along its own length, so the
stones neither gap on the outside of a bend nor pile up on its inside, and the coping stones are wedges there. A curve
object keeps its own shape, its sharp points built as corners. With smooth=False the wall runs straight between your
points and a turn sharper than 20 degrees is built as a corner: the faces meet, long squared corner stones take turns
along one face and the other (at 60 degrees and sharper), and a big stone sits on the top. Gaps are (from, to) in
metres along the line (smoothed, as built), measured from its first point as seen from above.

From the command line:

    python3 dry_wall.py --help
    python3 dry_wall.py --points "-6,0,0 6,0,0 6,9,0" --gap 4 7 --out wall.blend
    python3 dry_wall.py --blend yard.blend --line "Wall line" --ground ground --out yard_walled.blend

Options, with their defaults:
    height          1.25 m   the ground to the top of the coping stones
    base            0.62 m   the wall's width at its foot
    top             0.42 m   its width just under the coping
    coping          0.26 m   about how tall the coping stones stand (each its own height, now and then a taller one)
    gaps            none     (from, to) metres along the line where the wall is left out (gateways)
    ground          none     a mesh object (the ground tool's, or your own) whose height the wall's foot follows
    smooth          True     a smooth curve through your points; False: straight between them, sharp turns as corners
    seed            0        the same seed lays the same wall
    material        'SURFACE • old_stone_wall_02'    the stones' material: a store name or a material you hold
    shades          0.3      how much lighter or darker one stone is than the next (a copy of the material named
                             '<material> • stone by stone' reads it); 0 uses your material as it is
    core_material   'RECESSES • near-black blue'     the core, seen in the gaps between stones
    collection      none     where the objects go (a new collection 'dry_wall')

What it makes: 'dry wall stones' (the face, through and end stones; obj['stones'] counts them), 'dry wall coping'
(obj['copes']) and 'dry wall core'. Every face carries its stone's 'stone_tone' and 'stone_patch' (the stone_grain tool
reads 'stone_patch'), and the stones their course ('stone_course', from 0 at the foot) and which face they are in
('stone_face': 1 the line's left, -1 its right, 2 and -2 the thin stones pinned in there, 3 through-stones, 4 end
stones, 5 corner stones). A Bevel modifier rounds the stones' edges. The stones' foot is sunk 4 cm into the ground.
"""

import argparse
import bisect
import math
import os
import random
import sys

import bpy
import numpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _lines  # noqa: E402
import _rough_stones  # noqa: E402

STONE = 'SURFACE • old_stone_wall_02'
CORE = 'RECESSES • near-black blue'
CORNER = 20.0             # degrees: a sharper turn in the line is built as a corner
SQUARED = 60.0            # degrees: a corner this sharp or sharper gets long squared corner stones, a course each way
SINK = 0.04               # metres the footings sit below the ground
UP = Vector((0.0, 0.0, 1.0))

TOOL = {
    'name': 'dry_wall',
    'what': 'a dry-stone wall along a line or curve you give, whichever way it goes: flat stones in rough courses on two '
            'battered faces, through-stones, a dark core, chunky coping stones on edge leaning in runs along the top; gaps '
            'where you say (gateways), finished square; corners with long corner stones',
    'call': "dry_wall.lay([(-6, 0, 0), (6, 0, 0), (6, 9, 0)], height=1.25, gaps=[(4.0, 7.0)], ground=yard, seed=3)",
    'options': {
        'height': 'the ground to the top of the coping (1.25 m)',
        'base, top': "the wall's width at its foot and just under the coping (0.62 m, 0.42 m)",
        'coping': 'about how tall the coping stones stand (0.26 m)',
        'gaps': '(from, to) metres along the line where the wall is left out: gateways (none)',
        'ground': "a mesh object whose height the wall's foot follows (none: the line's own heights)",
        'smooth': 'a smooth curve through your points, each face laid along its own length round the bends; a curve object keeps its own shape (True); False: straight runs, sharp turns built as corners',
        'seed': 'the same seed lays the same wall (0)',
        'material': "the stones ('%s')" % STONE,
        'shades': 'how much one stone is lighter or darker than the next, 0 to 0.9 (0.3; 0 uses your material as it is)',
        'core_material': "the core seen in the gaps ('%s')" % CORE,
        'collection': "where the objects go (a new collection 'dry_wall')",
    },
    'materials': [STONE, CORE],
    'source': "`dry_wall` in the barn builder's '54 barn first pass - render_final.py' (line 675), made into a tool, with "
              "chunkier leaning copes (the builder's thin ones read as a picket fence), through-stones and finished ends",
    'trap': 'the coping must be chunky and lean: thin upright copes read as a picket fence; a gate hung in a gap needs '
            'its own posts (the wall ends are finished, not cut for hinges)',
}


# ------------------------------------------------------------------------------------------------ the line

class Line:
    """The line seen from above, measured along its length, with its own heights and corner turns. With `smooth`, a
    list of points becomes a smooth curve through them (so a few points give a bend, not straight runs and corners);
    a curve object keeps its own shape, smoothed between its sharp points, which stay corners."""

    def __init__(self, line, smooth=True):
        is_curve = isinstance(line, bpy.types.Object) and line.type == 'CURVE'
        kept = []
        for point in _lines.line_points(line):
            p = Vector((point[0], point[1], point[2] if len(point) > 2 else 0.0))
            if kept and (p.xy - kept[-1].xy).length < 1e-5:
                continue
            kept.append(p)
        if len(kept) < 2:
            raise ValueError('the line needs at least two different points (seen from above)')
        if smooth:
            pieces = _split_at_kinks(kept, CORNER) if is_curve else [kept]
            smoothed = []
            for piece in pieces:
                points = _lines.Path(piece).smooth(0.1).points
                smoothed.extend(points if not smoothed else points[1:])
            kept = [p for i, p in enumerate(smoothed) if i == 0 or (p.xy - smoothed[i - 1].xy).length > 1e-5]
        self.path = _lines.Path([Vector((p.x, p.y, 0.0)) for p in kept])
        self.points = self.path.points
        self.lengths = self.path.lengths
        self.total = self.path.total
        self.heights = [p.z for p in kept][:len(self.points)]

    def tangent(self, u):
        index = min(max(bisect.bisect_right(self.lengths, u) - 1, 0), len(self.points) - 2)
        return (self.points[index + 1] - self.points[index]).normalized()

    def turns(self):
        """(distance along, signed turn in degrees: left positive) at every inner point."""
        found = []
        for i in range(1, len(self.points) - 1):
            a = (self.points[i] - self.points[i - 1]).normalized()
            b = (self.points[i + 1] - self.points[i]).normalized()
            angle = math.degrees(math.atan2(a.x * b.y - a.y * b.x, a.dot(b)))
            found.append((self.lengths[i], angle))
        return found

    def own_height(self, u):
        return float(numpy.interp(u, self.lengths, self.heights))


def _split_at_kinks(points, threshold):
    """A line of points cut into pieces at every point where it turns more sharply than `threshold` degrees (the
    pieces share that point)."""
    pieces, current = [], [points[0]]
    for i in range(1, len(points) - 1):
        current.append(points[i])
        a = (points[i] - points[i - 1]).xy
        b = (points[i + 1] - points[i]).xy
        if a.length > 1e-9 and b.length > 1e-9:
            angle = math.degrees(abs(math.atan2(a.x * b.y - a.y * b.x, a.dot(b))))
            if angle > threshold:
                pieces.append(current)
                current = [points[i]]
    current.append(points[-1])
    pieces.append(current)
    return pieces


def ground_heights(line, ground, step=0.25, offset=0.0):
    """A function giving the height of the foot at a distance along the line: the ground's own (ground.height_at,
    asked every `step` metres and at every point of the line, then read between) or, without a ground, the line's.
    With `offset`, the ground that far to the line's left (negative: its right), under a face of the wall."""
    if ground is None:
        return line.own_height
    import ground as ground_tool
    if getattr(ground, 'type', None) != 'MESH':
        raise ValueError('ground is a mesh object (the ground tool makes one), not %r' % (ground,))
    distances = sorted(set(numpy.linspace(0.0, line.total, max(2, int(math.ceil(line.total / step)) + 1)).tolist() + list(line.lengths)))
    found = []
    for u in distances:
        p = line.path.at(u)
        if offset:
            ahead = line.tangent(u)
            p = p + Vector((-ahead.y, ahead.x, 0.0)) * offset
        found.append(ground_tool.height_at(ground, p.x, p.y))
    known = [(u, h) for u, h in zip(distances, found) if h is not None]
    if not known:
        raise ValueError('the line does not cross the ground %r anywhere' % ground.name)
    us, hs = zip(*known)
    return lambda u: float(numpy.interp(u, us, hs))


def read_gaps(gaps, total):
    """Gaps as sorted (from, to) pairs, checked: inside the line, from before to, not overlapping."""
    found = []
    for gap in gaps or ():
        try:
            a, b = float(gap[0]), float(gap[1])
        except (TypeError, IndexError, ValueError):
            raise ValueError('a gap is (from, to) in metres along the line, not %r' % (gap,))
        if not (0.0 <= a < b <= total + 1e-6):
            raise ValueError('a gap (%.2f, %.2f) must lie within the line (0 to %.2f m) with from before to' % (a, b, total))
        found.append((a, min(b, total)))
    found.sort()
    for (a0, b0), (a1, b1) in zip(found, found[1:]):
        if a1 < b0:
            raise ValueError('the gaps (%.2f, %.2f) and (%.2f, %.2f) overlap' % (a0, b0, a1, b1))
    return found


def runs(line, gaps, corner=CORNER):
    """The pieces of the line to build: between its ends and the gaps, each split at sharp corners. Each run is a dict:
    start, end (metres along) and at each end its kind: ('end', 0) a finished end, or ('corner', turn in degrees)."""
    stops = [(0.0, ('end', 0.0))]
    for u, angle in line.turns():
        if abs(angle) > corner and not any(a - 1e-6 <= u <= b + 1e-6 for a, b in gaps):
            stops.append((u, ('corner', angle)))
    for a, b in gaps:
        stops.append((a, ('end', 0.0)))
        stops.append((b, ('end', 0.0)))
    stops.append((line.total, ('end', 0.0)))
    stops.sort(key=lambda s: s[0])
    found = []
    for (u0, kind0), (u1, kind1) in zip(stops, stops[1:]):
        middle = (u0 + u1) / 2.0
        if u1 - u0 < 0.15 or any(a - 1e-6 <= middle <= b + 1e-6 for a, b in gaps):
            continue
        found.append({'start': u0, 'end': u1, 'start_kind': kind0, 'end_kind': kind1})
    return found


def frame(line, run, u):
    """The point on the line at u (carried on straight past the run's ends) and the line's way ahead there."""
    if u > run['end']:
        ahead = line.tangent(run['end'] - 1e-6)
        return line.path.at(run['end']) + ahead * (u - run['end']), ahead
    if u < run['start']:
        ahead = line.tangent(run['start'] + 1e-6)
        return line.path.at(run['start']) - ahead * (run['start'] - u), ahead
    return line.path.at(u), line.tangent(min(max(u, run['start'] + 1e-6), run['end'] - 1e-6))


def bend_frame(line, run, u, reach=0.1):
    """As frame(), with the way ahead taken over `reach` metres either side (within the run), so the faces round a
    bend smoothly instead of turning at every point of the line."""
    point, ahead = frame(line, run, u)
    if run['start'] < u < run['end']:
        before = line.path.at(max(u - reach, run['start']))
        after = line.path.at(min(u + reach, run['end']))
        if (after - before).length > 1e-6:
            ahead = (after - before).normalized()
    return point, ahead


class FaceLine:
    """One face of the wall seen from above: the line carried `half` metres to its left (side +1) or right (side -1),
    measured along itself, so stones are laid by the face's own length: none gap on the outside of a bend, none pile up
    on its inside."""

    def __init__(self, line, run, side, half, start, end, step=0.05):
        count = max(2, int(math.ceil((end - start) / step)) + 1)
        self.us = numpy.linspace(start, end, count)
        points = []
        for u in self.us:
            point, ahead = bend_frame(line, run, float(u))
            points.append((point.x - ahead.y * side * half, point.y + ahead.x * side * half))
        self.points = numpy.array(points)
        self.vs = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(self.points, axis=0), axis=1))])

    def v(self, u):
        return float(numpy.interp(u, self.us, self.vs))

    def u(self, v):
        return float(numpy.interp(v, self.vs, self.us))

    def at(self, v):
        return Vector((float(numpy.interp(v, self.vs, self.points[:, 0])), float(numpy.interp(v, self.vs, self.points[:, 1])), 0.0))


def corner_reach(kind, side, half):
    """How far a face on `side` (+1 the line's left, -1 its right) runs past a corner (negative: stops short of it)."""
    if kind[0] != 'corner':
        return 0.0
    angle = kind[1]
    return -side * math.copysign(1.0, angle) * half * math.tan(math.radians(abs(angle)) / 2.0)


# ------------------------------------------------------------------------------------------------ the wall

def _course_heights(total, rng):
    """(bottom, height) of each course from the footings (sunk SINK into the ground) to `total` above the ground:
    big footings, then courses getting smaller towards the top; the last stretched to finish exactly."""
    courses, z = [], -SINK
    while z < total - 0.02:
        share = max(0.0, z) / max(total, 1e-6)
        h = (rng.uniform(0.16, 0.21) if not courses else (0.13 - 0.055 * share) * rng.uniform(0.75, 1.25))
        if total - (z + h) < 0.06:
            h = total - z
        courses.append((z, h))
        z += h
    return courses


def _lay_face(stones, line, run, side, course, number, half_at, height_at, blocked, joints_below, rng, lean):
    """One course of one face: stones from end to end of the run (past corners as far as the faces meet), laid along
    the face's own line, each stone the chord between two points of it (so round a bend the stones neither gap nor
    pile up); the blocked stretches (end stones, through-stones, corner stones; metres along the wall's line) left;
    no joint lands over a joint of the course below. Returns this course's joints (metres along the wall's line)."""
    z, h = course
    z_mid = z + h / 2.0
    half = half_at(z_mid)
    start = run['start'] - corner_reach(run['start_kind'], side, half)
    end = run['end'] + corner_reach(run['end_kind'], side, half)
    free = [(start, end)]
    for a, b in blocked:
        pieces = []
        for p, q in free:
            if b <= p or a >= q:
                pieces.append((p, q))
                continue
            if a > p:
                pieces.append((p, a))
            if b < q:
                pieces.append((b, q))
        free = pieces
    face = FaceLine(line, run, side, half, start, end)
    below = [face.v(j) for j in joints_below]
    share = max(0.0, z_mid) / max(height_at, 1e-6)
    joints = []
    for p, q in free:
        vp, vq = face.v(p), face.v(q)
        if vq - vp < 0.06:
            continue
        v = vp
        while v < vq - 1e-6:
            w = (0.42 - 0.14 * share) * rng.uniform(0.55, 1.45)
            joint = v + w
            for under in below:
                if abs(joint - under) < 0.07:
                    joint = under + (0.08 if rng.random() < 0.5 or joint - v < 0.2 else -0.08)
                    break
            if vq - joint < 0.12:
                joint = vq
            joint = min(max(joint, v + 0.1), vq) if vq - v > 0.1 else vq
            gap = rng.uniform(0.008, 0.02)
            a, b = v + gap / 2.0, joint - gap / 2.0
            if b - a > 0.03:
                corner_a, corner_b = face.at(a), face.at(b)
                chord = corner_b - corner_a
                length = chord.length
                along = chord / max(length, 1e-9)
                out = Vector((-along.y, along.x, 0.0)) * side
                middle = (corner_a + corner_b) / 2.0
                depth = min(rng.uniform(0.22, 0.34), 2.0 * half - 0.05)
                proud = rng.uniform(-0.015, 0.02)
                u_a, u_b = face.u(a), face.u(b)
                room = h - rng.uniform(0.008, 0.018)
                tall = room * (rng.uniform(0.6, 0.85) if rng.random() < 0.3 else 1.0)
                stones.mesh.stone(middle + out * proud, along, out, (-length / 2.0, length / 2.0),
                                  (stones.level(side, u_a, z), stones.level(side, u_b, z)),
                                  (stones.level(side, u_a, z + tall), stones.level(side, u_b, z + tall)),
                                  depth, rng, bulge=rng.uniform(0.003, 0.01), jitter=0.007, lean=lean + rng.uniform(-0.07, 0.07),
                                  twist=rng.uniform(-0.012, 0.012), chip=min(0.02, tall * 0.3),
                                  labels={'stone_course': number, 'stone_face': side})
                if room - tall > 0.025:              # a thin stone pinned in over a short one
                    pin = length * rng.uniform(0.45, 0.85)
                    first = -length / 2.0 + rng.uniform(0.0, length - pin)
                    low, high = z + tall + 0.004, z + room
                    stones.mesh.stone(middle + out * (proud - 0.01), along, out, (first, first + pin),
                                      (stones.level(side, u_a, low), stones.level(side, u_b, low)),
                                      (stones.level(side, u_a, high), stones.level(side, u_b, high)), 0.12, rng,
                                      bulge=0.003, jitter=0.004, lean=lean, chip=min(0.012, (high - low) * 0.3),
                                      labels={'stone_course': number, 'stone_face': 2 * side})
            joints.append(face.u(joint))
            v = joint
    return joints


class _Stones:
    """The stones being laid and the ground under the wall: under its middle and under each face."""

    def __init__(self, mesh, ground, faces, body):
        self.mesh = mesh
        self.ground = ground
        self.faces = faces
        self.body = body

    def level(self, side, u, z):
        """The world height of a course height z on a face (side +1, -1; 0 the lower of the two): each face's courses
        run from the ground under that face (on a slope across the wall, the downhill face starts lower) up to the
        same top, so no face's foot stands in the air and the coping still sits on both."""
        middle = self.ground(u)
        under = min(self.faces[1](u), self.faces[-1](u)) if side == 0 else self.faces[side](u)
        low, high = under - SINK, middle + self.body
        return low + (z + SINK) * (high - low) / (self.body + SINK)


def lay(line, height=1.25, base=0.62, top=0.42, coping=0.26, gaps=(), ground=None, smooth=True, seed=0, material=STONE,
        shades=0.3, core_material=CORE, collection=None):
    """Lay the wall along the line; returns {'stones': object, 'coping': object, 'core': object} (see the note at the
    top)."""
    height, base, top, coping, shades = float(height), float(base), float(top), float(coping), float(shades)
    if not 0.3 <= height <= 4.0:
        raise ValueError('height is 0.3 to 4 m (the ground to the top of the coping), not %r' % (height,))
    if not 0.2 <= base <= 3.0:
        raise ValueError('base is the width at the foot, 0.2 to 3 m, not %r' % (base,))
    if not 0.12 <= top <= base:
        raise ValueError('top is the width under the coping, from 0.12 m up to the base width (%.2f), not %r' % (base, top))
    if not 0.08 <= coping <= height - 0.2:
        raise ValueError('coping is 0.08 m up to the height less 0.2 m, not %r' % (coping,))
    if not 0.0 <= shades <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    rng = random.Random(seed)
    path = Line(line, smooth=smooth)
    gap_list = read_gaps(gaps, path.total)
    pieces = runs(path, gap_list)
    if not pieces:
        raise ValueError('nothing left to build: the gaps take the whole line')
    foot = ground_heights(path, ground)
    body = height - coping                                            # the top of the face courses
    batter = (base - top) / 2.0 / max(body, 1e-6)                     # how far each face leans in per metre up

    def half_at(z):
        return (base + (top - base) * min(max(z, 0.0), body) / max(body, 1e-6)) / 2.0

    origin = Vector((path.points[0].x, path.points[0].y, foot(0.0)))
    stone_mesh = _rough_stones.StoneMesh(origin)
    cope_mesh = _rough_stones.StoneMesh(origin)
    core_mesh = _rough_stones.StoneMesh(origin)
    stones = _Stones(stone_mesh, foot, {+1: ground_heights(path, ground, offset=base / 2.0),
                                        -1: ground_heights(path, ground, offset=-base / 2.0)}, body)
    courses = _course_heights(body, rng)
    through_course = min(range(len(courses)), key=lambda k: abs(courses[k][0] + courses[k][1] / 2.0 - 0.5 * body)) if len(courses) > 2 else -1
    for run in pieces:
        length = run['end'] - run['start']
        # through-stones: every metre or so, in the course nearest half the height
        throughs = []
        u = run['start'] + rng.uniform(0.5, 0.9)
        while u < run['end'] - 0.5:
            throughs.append((u, rng.uniform(0.2, 0.28)))
            u += rng.uniform(0.9, 1.3)
        joints_below = {+1: [], -1: []}
        for k, course in enumerate(courses):
            z, h = course
            z_mid = z + h / 2.0
            blocked = []
            # a finished end: a long or short stone right across the wall, the next course the other way
            for at_start, kind in ((True, run['start_kind']), (False, run['end_kind'])):
                if kind[0] != 'end':
                    continue
                reach = min((0.36 if (k % 2 == 0) == at_start else 0.22) * rng.uniform(0.9, 1.1), length / 2.0 - 0.02)
                a, b = (run['start'], run['start'] + reach) if at_start else (run['end'] - reach, run['end'])
                blocked.append((a, b))
                end_at = a if at_start else b
                inward = 1.0 if at_start else -1.0
                point, ahead = bend_frame(path, run, end_at)
                left = Vector((-ahead.y, ahead.x, 0.0))
                half = half_at(z_mid) + 0.005
                low, high = stones.level(0, end_at, z), stones.level(0, end_at, z + h) - rng.uniform(0.008, 0.016)
                # the end face set back by its bulge, so the wall stops where it was asked to
                stone_mesh.stone(point + ahead * inward * 0.022, left, -ahead * inward, (-half, half), (low, low),
                                 (high, high), reach - 0.03, rng,
                                 bulge=rng.uniform(0.008, 0.016), jitter=0.006, labels={'stone_course': k, 'stone_face': 4})
            # a corner: a long squared corner stone on the outside, along one face this course and the other face the next
            side_blocked = {+1: [], -1: []}
            for at_start, kind in ((True, run['start_kind']), (False, run['end_kind'])):
                if kind[0] != 'corner' or abs(kind[1]) < SQUARED:
                    continue
                angle = kind[1]
                outer = -1 if angle > 0 else 1                         # turning left, the outside is the line's right
                half = half_at(z_mid)
                reach_past = half * math.tan(math.radians(abs(angle)) / 2.0)
                miter = run['start'] - reach_past if at_start else run['end'] + reach_past
                if (k % 2 == 0) == (not at_start):                     # the run before the corner takes the even courses
                    length = rng.uniform(0.3, 0.42)
                    a, b = (miter, miter + length) if at_start else (miter - length, miter)
                    middle = (a + b) / 2.0
                    point, ahead = frame(path, run, middle)
                    left = Vector((-ahead.y, ahead.x, 0.0))
                    out = left * outer
                    top_gap = rng.uniform(0.008, 0.014)
                    depth = 2.0 * half - 0.02
                    # its end at the corner follows the other face, so the corner stays closed at any angle
                    slant = depth / math.tan(math.radians(abs(angle)))
                    back = (a - middle - slant, b - middle - 0.01) if at_start else (a - middle + 0.01, b - middle + slant)
                    stone_mesh.stone(point + out * (half + rng.uniform(0.0, 0.01)), ahead, out, (a - middle, b - middle),
                                     (stones.level(outer, a, z), stones.level(outer, b, z)),
                                     (stones.level(outer, a, z + h) - top_gap, stones.level(outer, b, z + h) - top_gap),
                                     depth, rng, bulge=rng.uniform(0.004, 0.01), jitter=0.004, lean=batter, chip=0.006, back_span=back,
                                     labels={'stone_course': k, 'stone_face': 5})
                else:                                                  # the other run's corner stone shows its end here
                    width = min(2.0 * half / max(math.sin(math.radians(abs(angle))), 0.5), 1.2)
                    a, b = (miter, miter + width) if at_start else (miter - width, miter)
                side_blocked[outer].append((a, b))
            if k == through_course:
                for u_through, reach in throughs:
                    a, b = u_through - reach / 2.0, u_through + reach / 2.0
                    blocked.append((a - 0.005, b + 0.005))
                    point, ahead = bend_frame(path, run, u_through)
                    left = Vector((-ahead.y, ahead.x, 0.0))
                    half = half_at(z_mid) + 0.035
                    low, high = stones.level(0, u_through, z), stones.level(0, u_through, z + h) - 0.012
                    stone_mesh.stone(point + left * half, ahead, left, (-reach / 2.0, reach / 2.0), (low, low),
                                     (high, high), 2.0 * half, rng,
                                     bulge=rng.uniform(0.008, 0.018), jitter=0.008, labels={'stone_course': k, 'stone_face': 3})
            for side in (+1, -1):
                joints_below[side] = _lay_face(stones, path, run, side, course, k, half_at, body, blocked + side_blocked[side],
                                               joints_below[side], rng, batter)
        # the dark core, following the ground, carried past a corner so the faces' corner has it behind
        core_low, core_high = max(0.05, base / 2.0 - 0.14), max(0.04, top / 2.0 - 0.12)
        u0 = run['start'] + (0.0 if run['start_kind'][0] == 'corner' else 0.03)
        u1 = run['end'] - (0.0 if run['end_kind'][0] == 'corner' else 0.03)
        count = max(2, int(math.ceil((u1 - u0) / 0.3)) + 1)
        points, faces = [], []
        for i in range(count):
            u = u0 + (u1 - u0) * i / (count - 1)
            g = foot(min(max(u, run['start']), run['end']))
            for across, z in ((core_low, g - SINK), (-core_low, g - SINK), (-core_high, g + body - 0.03), (core_high, g + body - 0.03)):
                # at a corner each point of the end is carried to the corner's mitre, so the core never shows outside
                shift = 0.0
                if i == count - 1 and run['end_kind'][0] == 'corner':
                    shift = -across * math.tan(math.radians(run['end_kind'][1]) / 2.0)
                elif i == 0 and run['start_kind'][0] == 'corner':
                    shift = across * math.tan(math.radians(run['start_kind'][1]) / 2.0)
                point, ahead = bend_frame(path, run, u + shift)
                left = Vector((-ahead.y, ahead.x, 0.0))
                points.append(point + left * across + UP * z)
            if i:
                a, b = 4 * (i - 1), 4 * i
                faces.extend([(a, a + 1, b + 1, b), (a + 1, a + 2, b + 2, b + 1), (a + 2, a + 3, b + 3, b + 2), (a + 3, a, b, b + 3)])
        faces.extend([(3, 2, 1, 0), (4 * (count - 1), 4 * (count - 1) + 1, 4 * (count - 1) + 2, 4 * (count - 1) + 3)])
        core_mesh.solid(points, faces)
        # the coping: chunky slabs on edge across the top, leaning together in runs, a big stone at each end and corner
        width = top
        start, end = run['start'], run['end']
        if run['start_kind'][0] == 'corner':
            start += width / 2.0
        if run['end_kind'][0] == 'corner':
            end -= width / 2.0
        u = start
        lean, lean_until = 0.0, start
        since_tall = rng.randint(4, 8)
        first = True
        while u < end - 0.05:
            finishing = run['end_kind'][0] == 'end'
            if first and run['start_kind'][0] == 'end' or (finishing and end - u < 0.36):
                thickness, tilt = min(rng.uniform(0.24, 0.3), end - u - 0.004), 0.0           # a square end stone
            else:
                if u >= lean_until:
                    roll = rng.random()
                    lean = math.radians(rng.uniform(-3.0, 3.0)) if roll < 0.2 else math.radians(rng.uniform(6.0, 16.0)) * rng.choice((-1, 1))
                    lean_until = u + rng.uniform(1.5, 4.0)
                thickness = rng.uniform(0.12, 0.22)
                tilt = lean + math.radians(rng.uniform(-4.0, 4.0))
            first = False
            step = thickness / max(math.cos(tilt), 0.5)
            if u + step > end:
                thickness, tilt, step = end - u - 0.004, 0.0, end - u - 0.004
                if thickness < 0.06:
                    break
            middle = u + step / 2.0
            point, ahead = bend_frame(path, run, middle)
            left = Vector((-ahead.y, ahead.x, 0.0))
            _, before = bend_frame(path, run, max(middle - 0.15, run['start']))
            _, after = bend_frame(path, run, min(middle + 0.15, run['end']))
            span = max(min(middle + 0.15, run['end']) - max(middle - 0.15, run['start']), 1e-6)
            bend = math.atan2(before.x * after.y - before.y * after.x, before.dot(after)) / span     # 1 / radius, left positive
            tall = coping * rng.uniform(0.85, 1.12)
            since_tall -= 1
            if since_tall <= 0:
                tall *= 1.25
                since_tall = rng.randint(5, 9)
            g = foot(middle)
            across = width + rng.uniform(0.0, 0.07)
            # round a bend each cope is a wedge, thicker on the outside, so the copes close up on both edges
            cope_mesh.slab(point + UP * (g + body - 0.025), ahead, left, (thickness, across, tall + 0.025),
                           rng, lean=tilt, taper=(rng.uniform(0.8, 0.95), rng.uniform(0.82, 0.96)), wedge=max(-0.9, min(0.9, bend * across)))
            u += step + rng.uniform(0.003, 0.01)
    # a big stone on the top at every corner the wall turns
    for u_corner, angle in path.turns():
        if abs(angle) <= CORNER or any(a - 1e-6 <= u_corner <= b + 1e-6 for a, b in gap_list):
            continue
        before, after = path.tangent(u_corner - 1e-6), path.tangent(u_corner + 1e-6)
        middle_way = (before + after).normalized()
        point = path.path.at(u_corner)
        g = foot(u_corner)
        cope_mesh.slab(point + UP * (g + body - 0.025), middle_way, Vector((-middle_way.y, middle_way.x, 0.0)),
                       (top + 0.04, top + 0.06, coping * 0.95 + 0.025), rng, taper=(0.9, 0.9))
    if collection is None:
        collection = bpy.data.collections.new('dry_wall')
        bpy.context.scene.collection.children.link(collection)
    stone_material = store.material(material) if isinstance(material, str) else material
    stone_material = _rough_stones.shaded(stone_material, shades)
    core = store.material(core_material) if isinstance(core_material, str) else core_material
    lowest = min(foot(u) for u in numpy.linspace(0.0, path.total, 20))
    made = {
        'stones': stone_mesh.make('dry wall stones', [stone_material], collection, bevel=0.008),
        'coping': cope_mesh.make('dry wall coping', [stone_material], collection, bevel=0.01),
        'core': core_mesh.make('dry wall core', [core], collection),
    }
    for obj in made.values():
        store.mark(obj, ground=lowest)
    made['stones']['stones'] = stone_mesh.count
    made['coping']['copes'] = cope_mesh.count
    made['stones']['length'] = sum(r['end'] - r['start'] for r in pieces)
    made['stones']['gaps'] = len(gap_list)
    bpy.context.view_layer.update()
    return made


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of dry_wall.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--points', help='the line as "x,y,z x,y,z ..." (makes a new file unless --blend is given)')
    parser.add_argument('--points-json', help='a JSON file holding {"points": [[x, y, z], ...]}')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--ground', help='the name of the ground object in the --blend file (the wall follows its height)')
    parser.add_argument('--gap', type=float, nargs=2, action='append', default=[], metavar=('FROM', 'TO'),
                        help='metres along the line where the wall is left out (repeat for more)')
    for name, default, text in (('height', 1.25, 'the ground to the top of the coping'), ('base', 0.62, 'the width at the foot'),
                                ('top', 0.42, 'the width under the coping'), ('coping', 0.26, 'how tall the coping stones stand'),
                                ('shades', 0.3, 'how much one stone is lighter or darker than the next, 0 to 0.9')):
        parser.add_argument('--' + name, type=float, default=default, help='%s; default %s' % (text, default))
    parser.add_argument('--no-smooth', action='store_true', help='straight runs between the points, sharp turns built as corners')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same wall; default 0')
    parser.add_argument('--out', help='save the result here (.blend)')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    line = None
    if args.line:
        if args.line not in bpy.data.objects:
            parser.error('no object %r in the file' % args.line)
        line = bpy.data.objects[args.line]
    elif args.points_json:
        line = args.points_json
    elif args.points:
        line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()]
    if line is None:
        parser.error('give the line: --points, --points-json or --line')
    ground = None
    if args.ground:
        if args.ground not in bpy.data.objects:
            parser.error('no object %r in the file' % args.ground)
        ground = bpy.data.objects[args.ground]
    made = lay(line, height=args.height, base=args.base, top=args.top, coping=args.coping, gaps=[tuple(g) for g in args.gap],
               ground=ground, smooth=not args.no_smooth, seed=args.seed, shades=args.shades)
    print('made %d stones and %d coping stones along %.2f m of wall' % (made['stones']['stones'], made['coping']['copes'], made['stones']['length']))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
