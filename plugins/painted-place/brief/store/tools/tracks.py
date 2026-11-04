"""
What this file does: carves the marks of passing into a ground the ground tool made, along a line you give: the two
ruts of a horse and cart (with the horse's hoof prints between them), of a motor car, a lorry or a heavy tractor; a
trodden footpath; a walker's footprints; and potholes where you say. Every mark is real depth in the ground (a picture
of a track looks painted under a low lamp: nothing casts a shadow), and every mark reads the ground's wetness as it
goes: in wet mud it is deep, its walls lumpy, torn at the edge and smeared along by the wheel, the soil pushed up into
a rough lip on each side with clods on it when fresh, a tyre's ridges standing across its floor and water gathering in
its lower part; on firm damp ground shallow and sharp, with the tyre's tread or the boots' hobnails printed; on dry
ground only a shallow trough, its edges crushed pale and the dust brushed away. One age dial, 0 fresh to 1 old, moves
four things together: how sharp the edges are, how dark and glossy the floor is, what has fallen or washed into the
groove, and whether water still stands in it or has dried to a cracked floor. Every mark writes 'bare' on the ground
where it left bare earth (the grass tool keeps out of it). It decides nothing about where marks go: the line, the
vehicle, the age and the places of potholes are yours; the ground's own wetness decides only how each mark looks where
it falls.

From your own script, after ground.wet() (the wetness sets how deep the marks go) and before grass and stones:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import ground, tracks
    yard = ground.make(size=(14, 30), location=(0, 12, 0), seed=3)
    ground.wet(yard, wetness=0.7)
    lane = [(0.3, -3, 0), (0.6, 10, 0), (-0.5, 27, 0)]
    tracks.ruts(yard, lane, vehicle='cart', passes=3, age=0.4)          # a horse and cart
    tracks.ruts(yard, field_line, vehicle='tractor', passes=5, age=0.25)  # deep motor ruts with ridged floors
    tracks.potholes(yard, lane, at=[4.0, 17.5], size=0.6, age=0.7)
    tracks.path(yard, [(-6, 2, 0), (-1, 8, 0), (5, 9, 0)], width=0.5, age=0.6)
    tracks.footprints(yard, [(2, 4, 0), (3.5, 9, 0)], age=0.1)
    ground.fill(yard, ground.spots(yard))                      # the water, in every dip the tracks made too

Each call returns {'spots': where water stands along this mark, 'made': the objects it added (clods, grit), 'deepest':
metres}. Lines are smoothed into the curve a wheel or a walker would take through your points; a line can be a list of
points, a curve or line-mesh object, or a JSON file of points.

    python3 tracks.py --help
    python3 tracks.py --blend IN.blend --ground ground --kind ruts --points "0,-3,0 0.5,10,0" --vehicle car --age 0.3 --out OUT.blend

Options:
  ruts(ground, line, vehicle, passes, age, seed, horse)
    vehicle   'cart' (wheels 1.45 m apart, narrow iron tyres 6 cm that cut deep slots), 'car' (1.4 m, tyres 11 cm with
              tread), 'lorry' (1.7 m, 18 cm), 'tractor' (1.5 m, 32 cm tyres with deep lugs, whose ridges stand across
              the floor and hold water between them) or your own (gauge, tyre width) in metres; default 'cart'
    passes    how many times wheels went this way: more passes, deeper, and wider because the wheels are never quite in
              the same place; default 1
    horse     a cart's horse walks between the ruts, its hoof prints pocking the strip (a walk for each pass); default
              True for a cart; only a cart has one
  path(ground, line, width, age, seed)
    width     the trodden strip, metres; default 0.5
  footprints(ground, line, stride, boot, age, seed, start)
    stride    from one print to the next (left, then right), metres; default 0.75
    boot      (length, width) of a boot, metres; default (0.30, 0.11)
    start     the foot of the first print, 'left' or 'right'; default 'left'
  potholes(ground, line, at, size, age, which, vehicle, seed)
    at        distances along the line, metres, or 'ends and turns' (a metre in from each end, and where the line turns
              sharpest); default 'ends and turns'
    size      across, metres; default 0.5
    which     on which wheel line: 'both', 'left', 'right' or 'middle' (where a horse walks); default 'both'
  every kind: age (0 fresh .. 1 old; ruts 0.3, path 0.5, footprints 0.2, potholes 0.6), seed (same seed, same marks),
  detail (the size the ground is divided to under the mark, metres; ruts 0.02, footprints 0.0125, path 0.04,
  potholes 0.025), collection (where clods and grit go; default the ground's own).

Deepest marks, by the ground's wetness: ruts 1 to 2 cm dry, 3 to 5 damp, 6 to 12 wet (deeper with passes, for a lorry
or a tractor, and by up to half again in the last few metres at each end of the line and where it turns; at most 25 cm,
a tractor's 32); hoof prints about 2 cm damp, 4 to 7 cm in mud; footprints a few millimetres dry, about 1 cm damp, 2 to
4 cm in wet mud, the heel deepest; a path 2 to 6 cm; potholes 5 to 15 cm.
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
import numpy
from mathutils import Matrix, Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import ground as ground_tool  # noqa: E402
import _lines  # noqa: E402
import _noise  # noqa: E402

TOOL = {
    'name': 'tracks',
    'what': 'carves ruts (a horse and cart, a car, a lorry, a tractor), a trodden path, footprints and potholes into the '
            'ground along a line you give; their depth, lumps, lip, water and tread follow the ground\'s wetness, and one age dial wears them',
    'call': "tracks.ruts(yard, [(0, -3, 0), (0.6, 10, 0)], vehicle='cart', passes=3, age=0.4); tracks.footprints(yard, line, age=0.1)",
    'options': {
        'ruts: vehicle': "'cart' (1.45 m apart, iron tyres 6 cm), 'car' (1.4 m, 11 cm), 'lorry' (1.7 m, 18 cm), 'tractor' "
                         "(1.5 m, 32 cm, deep lugs) or (gauge, tyre width) ('cart')",
        'ruts: passes': 'how many times wheels went this way (1)',
        'ruts: horse': "the hoof prints of a cart's horse between the ruts (True for a cart)",
        'path: width': 'the trodden strip, metres (0.5)',
        'footprints: stride': 'from one print to the next, metres (0.75)',
        'footprints: boot': '(length, width), metres ((0.30, 0.11))',
        'footprints: start': "'left' or 'right' ('left')",
        'potholes: at': "distances along the line, or 'ends and turns' ('ends and turns')",
        'potholes: size': 'across, metres (0.5)',
        'potholes: which': "'both', 'left', 'right' or 'middle' wheel line ('both')",
        'age': '0 fresh .. 1 old: fresh marks are sharp, with a dark glossy floor, crumbs on the lip and no water yet; '
               'half-aged ones hold water in their deepest part; old ones are rounded, with grit in the groove and a cracked floor '
               '(ruts 0.3, path 0.5, footprints 0.2, potholes 0.6)',
        'seed': 'the same seed, the same marks (0)',
        'detail': 'how finely the ground is divided under the mark, metres (ruts 0.02, footprints 0.0125, path 0.04, potholes 0.025)',
    },
    'materials': ['the ground\'s own soil (MADE • dirt reads the tread, wear, wetness and crust the marks write)'],
    'source': 'the research of log 53 (how ruts, footprints and potholes form and age; how mud games carve tracks), made for the store',
    'trap': 'carve after ground.wet() and before grass and stones (or settle the stones again); then ground.fill(yard, '
            'ground.spots(yard)) for the water in every mark',
}

VEHICLES = {
    'cart': {'gauge': 1.45, 'tyre': 0.06, 'weight': 1.0, 'kind': 'iron'},
    'car': {'gauge': 1.40, 'tyre': 0.11, 'weight': 0.8, 'kind': 'tyre'},
    'lorry': {'gauge': 1.70, 'tyre': 0.18, 'weight': 1.3, 'kind': 'tyre'},
    'tractor': {'gauge': 1.50, 'tyre': 0.32, 'weight': 1.5, 'kind': 'lugs'},
}
RUT_DEPTH = ([0.0, 0.15, 0.35, 0.7, 1.0], [0.012, 0.016, 0.04, 0.09, 0.12])                 # wetness -> metres
PRINT_DEPTH = ([0.0, 0.15, 0.35, 0.6, 0.86, 1.0], [0.0015, 0.002, 0.008, 0.02, 0.035, 0.04])
HOOF_DEPTH = ([0.0, 0.15, 0.35, 0.6, 0.86, 1.0], [0.004, 0.006, 0.018, 0.04, 0.065, 0.075])     # a horse is heavy on a small foot
DEEPEST_RUT = 0.25
TREAD_KINDS = {'iron': 0.0, 'tyre': 1.0, 'lugs': 1.0, 'hobnails': 2.0}


# ----------------------------------------------------------------------------------------------- small helpers

def _smoothstep(low, high, value):
    """0 below low, 1 above high, smooth between (low may be above high: then it falls)."""
    t = numpy.clip((numpy.asarray(value, dtype=numpy.float64) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _bump(t):
    """1 in the middle falling smoothly to 0 at t = -1 and 1."""
    t = numpy.clip(numpy.abs(t), 0.0, 1.0)
    return (1.0 - t * t) ** 2


def _water_hold(age):
    """How far below a groove's full depth its water stands, as a share of the depth: fresh, little water yet (1); half
    aged, water in its deepest part (about 0.6); old, dried again (1)."""
    return 1.0 - 0.42 * math.sin(math.pi * float(numpy.clip(age, 0.0, 1.0)))


def _drying(dial):
    """How much the ground's drying lowers the water in marks: 1 on dry ground, falling to 0 as it gets soaked."""
    return float(numpy.clip((1.0 - dial) * 1.6, 0.0, 1.0))


def _below_brim(age, dial):
    """How far below a groove's brim its water stands, as a share of the groove's depth: water gathers in a groove's
    lower part only, lower when fresh (not gathered yet) or old (drying), and lower as the place dries."""
    return float(numpy.clip(0.25 + 0.6 * _water_hold(age) * (0.4 + 0.6 * _drying(dial)), 0.0, 0.95))


def _moving_average(values, lengths, window):
    if len(values) < 3:
        return values
    spacing = max((lengths[-1] - lengths[0]) / (len(values) - 1), 1e-6)
    width = int(round(window / spacing))
    if width <= 1:
        return values
    kernel = numpy.ones(width) / width
    padded = numpy.pad(values, (width, width), mode='edge')
    return numpy.convolve(padded, kernel, mode='same')[width:-width]


def _noise_along(along, frequency, key):
    """Smooth wandering (-1 .. 1) as a function of distance along the line, read at each point."""
    if not len(along):
        return numpy.zeros(0)
    step = min(0.05, 0.2 / frequency)
    samples = numpy.arange(float(along.min()) - 0.5, float(along.max()) + 0.5 + step, step)
    values = numpy.array([noise.noise(Vector((s * frequency, key * 1.37 + 0.31, key * 0.73 + 0.5))) for s in samples])
    return numpy.interp(along, samples, values)


def _vehicle(vehicle):
    if isinstance(vehicle, str):
        if vehicle not in VEHICLES:
            raise ValueError("vehicle is 'cart', 'car', 'lorry' or (gauge, tyre width), not %r" % vehicle)
        return dict(VEHICLES[vehicle])
    try:
        gauge, tyre = float(vehicle[0]), float(vehicle[1])
    except (TypeError, ValueError, IndexError):
        raise ValueError("vehicle is 'cart', 'car', 'lorry' or (gauge, tyre width) in metres, not %r" % (vehicle,))
    if not (0.3 <= gauge <= 4.0 and 0.02 <= tyre <= 0.8):
        raise ValueError('a vehicle of your own is (gauge 0.3 to 4 m, tyre width 0.02 to 0.8 m), not %r' % (vehicle,))
    return {'gauge': gauge, 'tyre': tyre, 'weight': 1.0, 'kind': 'tyre'}


def _check(ground, age):
    if ground is None or getattr(ground, 'type', None) != 'MESH':
        raise ValueError('give the ground: a mesh object (the ground tool makes one)')
    if not 0.0 <= float(age) <= 1.0:
        raise ValueError('age runs from 0 (fresh) to 1 (old), not %r' % (age,))
    if 'wetness_dial' not in ground:
        ground_tool.wet(ground, 0.0)
    return float(age)


def _smooth_path(line):
    return _lines.Path(_lines.line_points(line)).smooth(0.05)


def _hoof_prints(mark, way, passes, age, rng):
    """The horse's hoof prints between a cart's ruts, one walk for each pass: rounded prints about 13 cm across, the
    iron shoe pressed deeper round the toe and sides and open at the heel, a splash of mud round them in wet ground;
    many passes pock the strip between the ruts."""
    for run in range(passes):
        side = 1.0 if rng.random() < 0.5 else -1.0
        s = rng.uniform(0.1, 0.5)
        drift = rng.gauss(0.0, 0.04)
        while s < way.total - 0.1:
            point = way.at(s)
            ahead = way.at(min(way.total, s + 0.05)) - way.at(max(0.0, s - 0.05))
            ahead.z = 0.0
            ahead = ahead.normalized() if ahead.length > 1e-6 else Vector((0.0, 1.0, 0.0))
            left = Vector((-ahead.y, ahead.x, 0.0))
            centre = point + left * (side * 0.075 + drift + rng.gauss(0.0, 0.025))
            side = -side
            s += 0.42 * rng.uniform(0.8, 1.2)
            near = numpy.array(mark.tree.query_ball_point([centre.x, centre.y], 0.16), dtype=numpy.int64)
            if not len(near):
                continue
            offset = mark.xy[near] - numpy.array([centre.x, centre.y])
            a = offset @ numpy.array([ahead.x, ahead.y])
            b = offset @ numpy.array([left.x, left.y])
            wet_here = float(numpy.median(mark.wet[near]))
            depth = float(numpy.interp(wet_here, *HOOF_DEPTH)) * rng.uniform(0.8, 1.2) * (1.0 - 0.3 * age)
            q = numpy.sqrt((a / 0.07) ** 2 + (b / 0.062) ** 2)
            disc = _smoothstep(1.05, 0.82, q)
            shoe = _bump((q - 0.86) / 0.13) * _smoothstep(-0.065, -0.03, a)          # the shoe, open at the heel
            sticky = float(_smoothstep(0.35, 0.75, wet_here))
            splash = depth * 0.35 * sticky * (1.0 - 0.6 * age) * _bump((q - 1.25) / 0.22)
            mark.add_groove(-depth * (0.75 * disc + 0.35 * shoe), splash, disc, where=near)
            mark.raise_number('drop_extra', disc * depth * _below_brim(age, mark.dial), where=near)
            mark.raise_number('track_wet', disc * (1.0 - age) * 0.3 * sticky, where=near)
            mark.raise_number('wear', disc * 0.4 * (1.0 - wet_here), where=near)


def _near_lines(way, xy, offsets, band):
    """Which points lie within `band` metres of the lines `offsets` metres to the left of the line."""
    along, across, _ = way.project(xy)
    near = numpy.zeros(len(xy), dtype=bool)
    for offset in offsets:
        near |= numpy.abs(across - offset) <= band
    return near & (along >= -band) & (along <= way.total + band)


def _wetness_along(way, xy, wet, offset, tree):
    """The ground's wetness along the line, `offset` metres to its left, smoothed over half a metre (one value per sample
    of the line), so a groove's depth changes with the ground it crosses and not from point to point."""
    line, lengths, ahead = way.arrays()
    side = numpy.column_stack([-ahead[:, 1], ahead[:, 0]])
    _, nearest = tree.query(line[:, :2] + side * offset)
    return _moving_average(wet[nearest], lengths, 0.5)


# ----------------------------------------------------------------------------------------------- the ground under a mark

def _refine(ground, inside, detail):
    """Divide the ground's faces where inside(xy) is true until they are about `detail` metres across."""
    return ground_tool.refine(ground, inside, detail)


class _Mark:
    """One call's carving: the points near the line, the change of height to make there, and the numbers the soil
    reads, gathered from every groove, print or hole of the call and then written in one go."""

    def __init__(self, ground, way, reach, refine_inside, detail, keep=None):
        from scipy.spatial import cKDTree
        self.ground = ground
        self.path = way
        self.reach = reach
        _refine(ground, refine_inside, detail)
        self.points = ground_tool.world_points(ground)
        line, _, _ = way.arrays()
        low = line[:, :2].min(axis=0) - reach
        high = line[:, :2].max(axis=0) + reach
        boxed = numpy.flatnonzero(numpy.all((self.points[:, :2] >= low) & (self.points[:, :2] <= high), axis=1))
        along, across, ahead = way.project(self.points[boxed, :2])
        if keep is not None:
            near = keep(self.points[boxed, :2])
        else:
            near = (numpy.abs(across) <= reach) & (along >= -reach) & (along <= way.total + reach)
        self.index = boxed[near]
        self.xy = self.points[self.index, :2]
        self.along, self.across, self.ahead = along[near], across[near], ahead[near]
        mesh = ground.data
        self.wet = numpy.clip(ground_tool.numbers(mesh, 'wetness')[self.index], 0.0, 1.0)
        self.tree = cKDTree(self.xy) if len(self.xy) else None
        n = len(self.index)
        self.groove = numpy.zeros(n)            # metres down (negative): the deepest of every groove
        self.lip = numpy.zeros(n)               # metres up: the highest of every lip
        self.floor = numpy.zeros(n)             # 0..1: how much each point is the floor of a groove
        self.tread = numpy.zeros(n)
        self.tread_u = numpy.zeros(n)
        self.tread_v = numpy.zeros(n)
        self.tread_kind = numpy.zeros(n)
        self.uv_weight = numpy.zeros(n)         # how much of each point the mark that wrote its tread_u, tread_v owns
        self.smear = numpy.zeros(n)
        self.wear = numpy.zeros(n)
        self.track_wet = numpy.zeros(n)
        self.track_crust = numpy.zeros(n)
        self.drop_extra = numpy.zeros(n)
        self.lumps = numpy.zeros(n)              # how strongly the mud's lumps show (metres), and its streaks and ridges:
        self.streaks = numpy.zeros(n)            # fine relief added after the rounding, so a fresh mark keeps it
        self.ridges = numpy.zeros(n)
        self.lump_field = None
        self.streak_field = None
        self.dial = float(ground.get('wetness_dial', 0.5))

    def wetness_along(self, offset):
        return _wetness_along(self.path, self.xy, self.wet, offset, self.tree)

    def at_points(self, values):
        """A value per sample of the line, read at each point by its distance along."""
        _, lengths, _ = self.path.arrays()
        return numpy.interp(self.along, lengths, values)

    def add_groove(self, depth, lip, floor, where=slice(None)):
        self.groove[where] = numpy.minimum(self.groove[where], depth)
        self.lip[where] = numpy.maximum(self.lip[where], lip)
        self.floor[where] = numpy.maximum(self.floor[where], floor)

    def add_tread(self, strength, u, v, kind, weight, where=slice(None)):
        """The track's own across (u) and along (v) measure and its print, where this groove is more the floor than any
        before it in this call (weight 0..1)."""
        own = weight > self.uv_weight[where]
        for name, value in (('tread', strength), ('tread_u', u), ('tread_v', v), ('tread_kind', kind)):
            current = getattr(self, name)
            current[where] = numpy.where(own, value, current[where])
        self.uv_weight[where] = numpy.maximum(self.uv_weight[where], weight)

    def raise_number(self, name, values, where=slice(None)):
        current = getattr(self, name)
        current[where] = numpy.maximum(current[where], values)

    def finish(self, soften, seed, age=0.5, crumbs_per_metre=0.0, grit=None, collection=None):
        """Round the edges, carve, write the numbers, wet the ground again; returns the result."""
        if not len(self.index):
            return {'spots': [], 'made': [], 'deepest': 0.0}
        held_down = _smoothstep(0.0, 0.004, -self.groove)       # a lip that falls into a groove is gone
        change = self.groove + self.lip * (1.0 - held_down)
        change = self._soften(change, soften)
        if self.lump_field is not None:                         # lumps and streaks soften with age; ridges fade by their own measure
            change = change + self.lump_field * self.lumps * (1.0 - 0.5 * age)
        if self.streak_field is not None:
            change = change + self.streak_field * self.streaks
        change = change + self.ridges
        carved = numpy.clip(-change, 0.0, None)                 # bare earth, where no grass grows: grooves, fresh lips, trodden places
        heaved = numpy.clip(change, 0.0, None)
        bare = numpy.maximum(_smoothstep(0.003, 0.02, carved) * (1.0 - 0.6 * _smoothstep(0.7, 1.0, age)),
                             _smoothstep(0.004, 0.03, heaved) * (1.0 - age) * 0.45)          # a lip is turf pushed up: grass stays on much of it
        self.bare = numpy.maximum(getattr(self, 'bare', numpy.zeros(len(change))), bare)
        heights = self.points[:, 2].copy()
        heights[self.index] += change
        ground_tool.set_world_heights(self.ground, heights)
        mesh = self.ground.data
        for name in ('wear', 'bare', 'track_wet', 'track_crust', 'drop_extra'):
            current = ground_tool.numbers(mesh, name)
            current[self.index] = numpy.maximum(current[self.index], getattr(self, name))
            ground_tool.set_numbers(mesh, name, current)
        on_top = self.uv_weight > 0.05                         # a later mark prints over an earlier one
        for name in ('tread', 'tread_u', 'tread_v', 'tread_kind', 'smear'):
            current = ground_tool.numbers(mesh, name)
            current[self.index] = numpy.where(on_top, getattr(self, name), current[self.index])
            ground_tool.set_numbers(mesh, name, current)
        if collection is None:
            collection = self.ground.users_collection[0] if self.ground.users_collection else bpy.context.scene.collection
        made = []
        if crumbs_per_metre > 0:
            crumbs = self._crumbs(crumbs_per_metre, heights[self.index], seed, collection)
            if crumbs is not None:
                made.append(crumbs)
        spots = ground_tool.spots(self.ground)
        if grit is not None:
            try:
                import stones
            except ImportError:
                stones = None
            if stones is not None:
                laid = stones.scatter(self.ground, area=grit[0], layers=('grit',), amount=grit[1], where='even',
                                      seed=seed + 17, collection=collection)
                made.extend(obj for obj in (laid.values() if isinstance(laid, dict) else laid) if obj is not None)
        mine = []
        if spots:
            locations = numpy.array([spot['location'][:2] for spot in spots], dtype=numpy.float64)
            along, across, _ = self.path.project(locations)
            for spot, a, c in zip(spots, along, across):
                if -self.reach <= a <= self.path.total + self.reach and abs(c) <= self.reach:
                    mine.append(spot)
        return {'spots': mine, 'made': made, 'deepest': float(max(0.0, -change.min()))}

    def _soften(self, change, sigma):
        """Round the carved shape: average each point with its neighbours, more times for a wider rounding."""
        if sigma <= 0 or not len(change):
            return change
        from scipy.sparse import coo_matrix
        mesh = self.ground.data
        edges = ground_tool.edges_of(mesh)
        position = numpy.full(len(mesh.vertices), -1, dtype=numpy.int64)
        position[self.index] = numpy.arange(len(self.index))
        both = (position[edges[:, 0]] >= 0) & (position[edges[:, 1]] >= 0)
        pairs = position[edges[both]]
        if not len(pairs):
            return change
        n = len(self.index)
        rows = numpy.concatenate([pairs[:, 0], pairs[:, 1]])
        cols = numpy.concatenate([pairs[:, 1], pairs[:, 0]])
        graph = coo_matrix((numpy.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
        degree = numpy.asarray(graph.sum(axis=1)).ravel()
        mine = self.points[self.index]
        lengths = numpy.linalg.norm(mine[pairs[:, 0], :2] - mine[pairs[:, 1], :2], axis=1)
        spacing = float(numpy.median(lengths))
        steps = int(min(80, math.ceil(2.0 * (sigma / max(spacing, 1e-4)) ** 2)))
        values = change.copy()
        moving = degree > 0
        for _ in range(steps):
            mean = (graph @ values) / numpy.maximum(degree, 1)
            values = numpy.where(moving, 0.5 * values + 0.5 * mean, values)
        return values

    def _crumbs(self, per_metre, heights, seed, collection):
        """Little clods of mud standing on a fresh lip, about to fall in: placed where the lip is highest."""
        lip = numpy.where(self.groove > -0.002, self.lip, 0.0)
        crest = lip > 0.003
        if not crest.any():
            return None
        areas = ground_tool.point_areas(self.ground.data)[self.index]
        length = float(areas[crest].sum()) / 0.08                 # a lip is about 8 cm wide
        count = int(per_metre * length)
        if count <= 0:
            return None
        rng = numpy.random.default_rng(seed + 101)
        weights = lip[crest] ** 2
        chosen = numpy.flatnonzero(crest)[rng.choice(int(crest.sum()), size=count, p=weights / weights.sum())]
        spacing = float(numpy.sqrt(numpy.median(areas[crest])))
        bm = bmesh.new()
        wetness = []
        scale = 1.0 + 3.0 * float(numpy.clip(-self.groove.min(), 0.0, 0.3))     # deeper marks throw bigger clods
        for index in chosen:
            size = rng.uniform(0.008, 0.026) * scale
            jitter = rng.uniform(-0.5, 0.5, 2) * spacing
            place = Vector((self.xy[index, 0] + jitter[0], self.xy[index, 1] + jitter[1], heights[index] + size * 0.3))
            matrix = Matrix.Translation(place) @ Matrix.Rotation(rng.uniform(0.0, math.tau), 4, 'Z') @ \
                Matrix.Diagonal((size * rng.uniform(1.0, 1.6), size, size * rng.uniform(0.55, 0.85), 1.0))
            made = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=matrix)
            for vertex in made['verts']:
                vertex.co += Vector((noise.noise(vertex.co * 90.0), noise.noise(vertex.co * 90.0 + Vector((5.0, 0.0, 0.0))),
                                     noise.noise(vertex.co * 90.0 + Vector((0.0, 9.0, 0.0))))) * size * 0.45
            wetness.extend([float(numpy.clip(self.wet[index], 0.35, 0.8))] * len(made['verts']))
        mesh = bpy.data.meshes.new('track crumbs')
        bm.to_mesh(mesh)
        bm.free()
        ground_tool.set_numbers(mesh, 'wetness', wetness)
        obj = bpy.data.objects.new('track crumbs', mesh)
        collection.objects.link(obj)
        if self.ground.data.materials:
            mesh.materials.append(self.ground.data.materials[0])
        store.mark(obj, ground=float(heights.min()))
        return obj


# ----------------------------------------------------------------------------------------------- ruts

def ruts(ground, line, vehicle='cart', passes=1, age=0.3, seed=0, detail=None, horse=None, collection=None):
    """A vehicle's two ruts along the line (see the note at the top); a cart's horse walks between them, leaving its
    hoof prints (horse=False leaves them out). Returns {'spots', 'made', 'deepest'}."""
    from scipy.spatial import cKDTree
    age = _check(ground, age)
    wheel = _vehicle(vehicle)
    passes = int(passes)
    if passes < 1:
        raise ValueError('passes is 1 or more, not %r' % (passes,))
    rng = random.Random(seed)
    way = _smooth_path(line)
    gauge, tyre = wheel['gauge'], wheel['tyre']
    half = tyre / 2.0
    wheels = (-gauge / 2.0, gauge / 2.0)
    if detail is None:
        detail = 0.02
    _, lengths, _ = way.arrays()
    turning = _moving_average(way.curvature(), lengths, 1.0)
    from_end = numpy.minimum(lengths, way.total - lengths)
    harder = numpy.maximum(1.0 - _smoothstep(1.0, 3.0, from_end), _smoothstep(0.05, 0.3, turning))
    shape = (1.0 + 0.5 * harder) * wheel['weight'] * (1.0 + 0.3 * math.log2(passes)) * (1.0 - 0.25 * age)
    deepest_allowed = max(DEEPEST_RUT, tyre)

    def depth_along(wet_line):
        return numpy.minimum(numpy.interp(wet_line, *RUT_DEPTH) * shape, deepest_allowed)

    points = ground_tool.world_points(ground)                 # how far the deepest groove's lips reach, before dividing
    wet_all = numpy.clip(ground_tool.numbers(ground.data, 'wetness'), 0.0, 1.0)
    tree = cKDTree(points[:, :2])
    deepest = max(float(depth_along(_wetness_along(way, points[:, :2], wet_all, w, tree)).max()) for w in wheels)
    spread = 0.3 * tyre + 0.012
    band = half + deepest * 1.3 + 0.25 * half + 1.4 * deepest + 0.03 + (3.0 * spread if passes > 1 else 0.0) + 0.08
    if horse is None:
        horse = wheel['kind'] == 'iron'
    elif horse and wheel['kind'] != 'iron':
        raise ValueError('only a cart has a horse (vehicle=%r)' % (vehicle,))

    def to_divide(xy):
        near = _near_lines(way, xy, wheels, band)
        if horse:
            near |= _near_lines(way, xy, [0.0], 0.3)
        return near
    mark = _Mark(ground, way, gauge / 2.0 + band, to_divide, detail)
    if not len(mark.index):
        return {'spots': [], 'made': [], 'deepest': 0.0}
    ends = _smoothstep(-0.25, 0.05, mark.along) * _smoothstep(way.total + 0.25, way.total - 0.05, mark.along)
    runs = [(0.0, 1.0, 0.0)] + [(rng.gauss(0.0, spread), rng.uniform(0.55, 0.95), rng.uniform(1.0, 60.0)) for _ in range(passes - 1)]
    wander = [numpy.zeros(len(mark.along))] + [0.5 * spread * _noise_along(mark.along, 0.25, key) for _, _, key in runs[1:]]
    kind = wheel['kind']
    # the mud's own lumps, torn edges and streaks, the same for every wheel and pass (seen from above, in metres)
    clods = (0.65 * (2.0 * _noise.clods(mark.xy[:, 0], mark.xy[:, 1], scale=0.06, seed=seed + 11) - 1.0)      # broken clods with creases
             + 0.35 * _noise.wander(mark.along, mark.across, scale=0.09, seed=seed + 12, layers=2))
    torn = _noise.wander(mark.along, mark.across, scale=0.11, seed=seed + 19, layers=2)
    mark.lump_field = clods
    mark.streak_field = _noise.wander(mark.along, mark.across, scale=(0.6, 0.012), seed=seed + 23)
    firm = _smoothstep(0.18, 0.5, _noise_along(mark.along, 0.32, seed * 1.3 + 17.0))   # firmer stretches where the ruts run out shallow
    for number, wheel_line in enumerate(wheels):
        wet_line = mark.wetness_along(wheel_line)
        wet_here = mark.at_points(wet_line)
        sticky = _smoothstep(0.25, 0.75, wet_here)
        humps = (1.0 + 0.38 * _noise_along(mark.along, 0.7, seed + 7.0 * number) + 0.12 * _noise_along(mark.along, 3.0, seed + 5.0 * number + 2.0)) * \
            (1.0 - 0.65 * firm * (0.85 + 0.3 * number))
        depth_here = mark.at_points(depth_along(wet_line)) * ends * humps
        for run, (shift, share, key) in enumerate(runs):
            d = mark.across - (wheel_line + shift + wander[run])
            depth = depth_here * share
            ragged = 1.0 + 0.25 * _noise_along(mark.along, 1.7, key + 9.0 * number + 1.0) + 0.12 * _noise_along(mark.along, 6.0, key + 4.0 * number)
            wall = (0.25 * half + depth * (0.22 + 0.5 * wet_here)) * ragged      # sticky mud stands steep; dry soil crumbles back
            x = numpy.maximum(numpy.abs(d) - 0.3 * wall * torn, 0.0)             # a torn edge, in and out along the rut
            if kind == 'iron':                                 # a narrow iron tyre cuts a round-bottomed groove
                groove = -depth * numpy.clip(1.0 - (x / (half + wall)) ** 2, 0.0, None) ** 0.8
            else:                                              # a wide tyre presses a flat floor
                groove = -depth * (1.0 - _smoothstep(numpy.maximum(half - 0.3 * wall, 0.0), half + wall, x))
            floor = (1.0 - _smoothstep(half * 0.6, half + wall, x)) * ends * (depth > 1e-4)
            on_wall = _bump((x - (half + 0.5 * wall)) / (0.75 * wall + 0.02)) * ends
            mark.raise_number('lumps', (0.004 + 0.18 * depth * sticky) * (0.6 * on_wall + 0.45 * floor))   # clods on the walls and floor
            core = (1.0 - _smoothstep(half * 0.5, half * 0.95, x)) * ends
            islands = _smoothstep(0.3, 0.65, _noise.wander(mark.along, d, scale=0.22, seed=seed + 31 + run))    # mud humps standing up from the floor
            groove = groove + islands * 0.5 * depth * sticky * core
            mark.raise_number('streaks', 0.006 * sticky * numpy.clip(floor + on_wall, 0.0, 1.0) * (1.0 - age))
            pressed = numpy.zeros_like(groove)                 # the tread pressed into the floor, as real ridges
            if kind == 'lugs':
                pressed = floor * (1.0 - _smoothstep(0.15, 0.7, age)) * _smoothstep(0.15, 0.35, wet_here) * (1.0 - 0.4 * _smoothstep(0.92, 1.0, wet_here))
                spacing, chevron, height = 0.62 * tyre, 0.55, 0.11 * tyre
            elif kind == 'tyre':
                pressed = floor * (1.0 - _smoothstep(0.05, 0.45, age)) * _smoothstep(0.1, 0.3, wet_here) * (1.0 - 0.6 * _smoothstep(0.6, 0.9, wet_here))
                spacing, chevron, height = 0.32 * tyre, 0.35, 0.04 * tyre
            if kind in ('lugs', 'tyre'):
                phase = (mark.along + chevron * numpy.abs(d)) / spacing + 0.5 * (d > 0.0)
                ridge = _bump((phase - numpy.floor(phase) - 0.5) / 0.28) * (1.0 - _smoothstep(half * 0.8, half * 1.05, numpy.abs(d)))
                ridge = ridge * (0.35 + 0.65 * _smoothstep(-0.35, 0.35, _noise_along(mark.along, 1.6, key + 13.0 * number + 5.0)))   # some smeared out
                mark.raise_number('ridges', ridge * height * pressed * share)
            lip_height = depth * 0.3 * _smoothstep(0.3, 0.7, wet_here) * (1.0 - 0.6 * age)
            lumpy_lip = numpy.clip(0.5 + 1.0 * clods, 0.05, None) * (0.75 + 0.5 * (0.5 + 0.5 * _noise_along(mark.along, 4.0, key + 3.0 * number + 11.0)))
            lip_width = 1.6 * depth + 0.05
            on_lip = _bump((x - (half + 0.8 * wall + lip_width / 2.0)) / numpy.maximum(lip_width / 2.0, 1e-4)) * ends
            lip = lip_height * lumpy_lip * on_lip
            mark.raise_number('lumps', (0.003 + 0.12 * depth * sticky) * on_lip)
            mark.add_groove(groove, lip, floor * share)
            printed = floor * (1.0 - _smoothstep(0.05, 0.45, age)) * _smoothstep(0.1, 0.3, wet_here) * (1.0 - 0.6 * _smoothstep(0.6, 0.9, wet_here))
            if kind == 'lugs':
                printed = numpy.maximum(printed, pressed)
            mark.add_tread(printed * share, d, mark.along, TREAD_KINDS[kind], floor * share)
            mark.raise_number('smear', floor * share * sticky * (1.0 - 0.6 * age))
            shoulder = _bump((x - (half + 0.6 * wall)) / numpy.maximum(wall, 1e-4)) * ends
            mark.raise_number('wear', numpy.maximum(floor * 0.5, shoulder * 0.35) * (1.0 - wet_here))
            mark.raise_number('track_wet', floor * (1.0 - age) ** 1.5 * 0.3 * _smoothstep(0.1, 0.4, wet_here))
            mark.raise_number('drop_extra', floor * depth * _below_brim(age, mark.dial))
            mark.raise_number('track_crust', floor * _smoothstep(0.55, 0.95, age) * (1.0 - mark.dial) * 0.9)
            mark.raise_number('track_wet', on_lip * (1.0 - age) * 0.45 * sticky)          # heaved mud is the wettest
    if horse:
        _hoof_prints(mark, way, passes, age, rng)
    fresh = (1.0 - age / 0.4) ** 2 if age < 0.4 else 0.0
    grit = None
    if age > 0.4:
        def in_the_floor(xy):
            along, across, _ = way.project(xy)
            near = numpy.zeros(len(xy))
            for wheel_line in wheels:
                near = numpy.maximum(near, 1.0 - _smoothstep(half * 0.5, half + 0.02, numpy.abs(across - wheel_line)))
            return near * ((along >= 0.0) & (along <= way.total))
        grit = (in_the_floor, (age - 0.4) * 1.2)
    return mark.finish(soften=(0.15 + 0.6 * age) * min(tyre, 0.12), seed=seed, age=age, crumbs_per_metre=8.0 * fresh, grit=grit,
                       collection=collection)


# ----------------------------------------------------------------------------------------------- a trodden path

def path(ground, line, width=0.5, age=0.5, seed=0, detail=0.04, collection=None):
    """A trodden footpath along the line: a strip lower than the ground beside it, polished pale in the middle when dry,
    wetter in its low places, its edges soft and wandering. Returns {'spots', 'made', 'deepest'}."""
    age = _check(ground, age)
    if not 0.1 <= float(width) <= 5.0:
        raise ValueError('width is 0.1 to 5 metres, not %r' % (width,))
    way = _smooth_path(line)
    half = float(width) / 2.0
    reach = half * 1.45 + 0.1
    mark = _Mark(ground, way, reach, lambda xy: _near_lines(way, xy, [0.0], reach), detail)
    if not len(mark.index):
        return {'spots': [], 'made': [], 'deepest': 0.0}
    wet_here = mark.at_points(mark.wetness_along(0.0))
    depth = (0.02 + 0.04 * age) * (0.7 + 0.6 * wet_here)
    ends = _smoothstep(-0.4, 0.1, mark.along) * _smoothstep(way.total + 0.4, way.total - 0.1, mark.along)
    x = numpy.abs(mark.across - _noise_along(mark.along, 0.4, seed * 1.7 + 2.0) * width * 0.15)
    edge = half * 1.15 * (1.0 + 0.12 * _noise_along(mark.along, 2.5, seed * 0.9 + 4.0))
    trough = -depth * numpy.clip(1.0 - (x / edge) ** 2, 0.0, None) ** 1.5 * ends
    middle = (1.0 - _smoothstep(width * 0.12, half * 1.1, x)) * ends
    mark.add_groove(trough, numpy.zeros_like(trough), middle)
    mark.add_tread(numpy.zeros_like(trough), mark.across, mark.along, 0.0, middle)
    mark.raise_number('smear', middle * 0.5 * _smoothstep(0.35, 0.75, wet_here) * (1.0 - 0.5 * age))
    mark.raise_number('wear', middle * (0.55 + 0.45 * age) * (1.0 - 0.5 * _smoothstep(0.4, 0.8, wet_here)))
    mark.raise_number('track_wet', middle * 0.1 * _smoothstep(0.2, 0.5, wet_here))
    mark.raise_number('drop_extra', middle * depth * 0.4 * _drying(mark.dial))
    return mark.finish(soften=0.03 + 0.05 * age, seed=seed, age=age, collection=collection)


# ----------------------------------------------------------------------------------------------- footprints

def _boot_distance(a, b, length, width):
    """How far outside a boot's outline a point is (negative inside), the boot pointing along +a, its middle at 0: a
    heel and a wider forefoot joined smoothly, with a waist between."""
    scale_a, scale_b = length / 0.275, width / 0.104

    def ellipse(centre, ra, rb):
        return (numpy.sqrt(((a - centre) / ra) ** 2 + (b / rb) ** 2) - 1.0) * min(ra, rb)
    heel = ellipse(-0.095 * scale_a, 0.05 * scale_a, 0.042 * scale_b)
    fore = ellipse(0.045 * scale_a, 0.085 * scale_a, 0.052 * scale_b)
    k = 0.02
    blend = numpy.clip(0.5 + 0.5 * (fore - heel) / k, 0.0, 1.0)
    return fore * (1.0 - blend) + heel * blend - k * blend * (1.0 - blend)


def footprints(ground, line, stride=0.75, boot=(0.30, 0.11), age=0.2, seed=0, detail=0.0125, start='left', collection=None):
    """A walker's footprints along the line, left and right in turn, `stride` metres apart. Returns {'spots', 'made',
    'deepest'}."""
    age = _check(ground, age)
    if start not in ('left', 'right'):
        raise ValueError("start is 'left' or 'right', not %r" % (start,))
    length, width = float(boot[0]), float(boot[1])
    if not (0.1 <= length <= 0.6 and 0.04 <= width <= 0.25 and 0.2 <= float(stride) <= 2.5):
        raise ValueError('boot is (length 0.1 to 0.6 m, width 0.04 to 0.25 m) and stride 0.2 to 2.5 m')
    rng = random.Random(seed)
    way = _smooth_path(line)
    straddle = 0.09
    band = straddle + 0.03 + width / 2.0 + length * 0.1 + 0.07
    mark = _Mark(ground, way, band + 0.03, lambda xy: _near_lines(way, xy, [0.0], band), detail)
    if not len(mark.index):
        return {'spots': [], 'made': [], 'deepest': 0.0}
    side = 1.0 if start == 'left' else -1.0
    dry_soak = _drying(mark.dial)
    s = rng.uniform(0.0, float(stride) * 0.5)
    while s <= way.total:
        point = way.at(s)
        ahead = way.at(min(way.total, s + 0.05)) - way.at(max(0.0, s - 0.05))
        ahead.z = 0.0
        ahead = ahead.normalized() if ahead.length > 1e-6 else Vector((0.0, 1.0, 0.0))
        left = Vector((-ahead.y, ahead.x, 0.0))
        centre = point + left * (side * straddle + rng.gauss(0.0, 0.012)) + ahead * rng.gauss(0.0, 0.02)
        forward = Matrix.Rotation(math.radians(side * rng.uniform(4.0, 10.0)), 3, 'Z') @ ahead    # toes turned out
        sideways = Vector((-forward.y, forward.x, 0.0))
        near = numpy.array(mark.tree.query_ball_point([centre.x, centre.y], length * 0.85), dtype=numpy.int64)
        side = -side
        s += float(stride) * rng.uniform(0.93, 1.07)
        if not len(near):
            continue
        offset = mark.xy[near] - numpy.array([centre.x, centre.y])
        a = offset @ numpy.array([forward.x, forward.y])
        b = offset @ numpy.array([sideways.x, sideways.y])
        wet_here = float(numpy.median(mark.wet[near]))
        depth = float(numpy.interp(wet_here, *PRINT_DEPTH)) * rng.uniform(0.85, 1.15) * (1.0 - 0.3 * age)
        soft = 0.004 + 0.011 * float(_smoothstep(0.35, 0.86, wet_here))
        distance = _boot_distance(a, b, length, width)
        inside = _smoothstep(0.0, soft, -distance)
        heel = 0.75 + 0.35 * _smoothstep(0.05, -0.12, a * 0.275 / length)
        lip_height = depth * 0.5 * float(_smoothstep(0.4, 0.8, wet_here)) * (1.0 - 0.7 * age)
        lip_width = 0.02 + 0.6 * depth
        lip = lip_height * _bump((distance - lip_width / 2.0) / (lip_width / 2.0)) * (distance > 0)
        mark.add_groove(-depth * inside * heel, lip, inside, where=near)
        firm = float(_smoothstep(0.12, 0.3, wet_here) * (1.0 - _smoothstep(0.55, 0.8, wet_here)))
        mark.add_tread(inside * (1.0 - _smoothstep(0.05, 0.35, age)) * firm, b, a, TREAD_KINDS['hobnails'], inside, where=near)
        mark.raise_number('wear', inside * (0.9 if wet_here < 0.15 else 0.3), where=near)
        mark.raise_number('track_wet', inside * (1.0 - age) * 0.3 * float(_smoothstep(0.15, 0.4, wet_here)), where=near)
        mark.raise_number('drop_extra', inside * depth * _water_hold(age) * dry_soak, where=near)
        mark.raise_number('track_crust', inside * float(_smoothstep(0.6, 0.95, age)) * (1.0 - mark.dial) * 0.6, where=near)
    fresh = (1.0 - age / 0.35) ** 2 if age < 0.35 else 0.0
    return mark.finish(soften=0.002 + 0.02 * age, seed=seed, age=age, crumbs_per_metre=6.0 * fresh, collection=collection)


# ----------------------------------------------------------------------------------------------- potholes

def potholes(ground, line, at='ends and turns', size=0.5, age=0.6, which='both', vehicle='cart', seed=0, detail=0.025,
             collection=None):
    """Round holes pounded out where water stood in the wheel lines: a steep front edge (the way the line runs), a
    splashed-out back edge, 5 to 15 cm deep, at the distances along the line you give. Returns {'spots', 'made',
    'deepest'}."""
    age = _check(ground, age)
    if not 0.15 <= float(size) <= 3.0:
        raise ValueError('size is 0.15 to 3 metres across, not %r' % (size,))
    rng = random.Random(seed)
    way = _smooth_path(line)
    gauge = _vehicle(vehicle)['gauge']
    lines = {'both': [-gauge / 2.0, gauge / 2.0], 'left': [gauge / 2.0], 'right': [-gauge / 2.0], 'middle': [0.0]}
    if which not in lines:
        raise ValueError("which is 'both', 'left', 'right' or 'middle', not %r" % (which,))
    if isinstance(at, str):
        if at != 'ends and turns':
            raise ValueError("at is a list of distances along the line, or 'ends and turns', not %r" % (at,))
        in_from_end = min(1.0, way.total * 0.1)
        distances = [in_from_end, way.total - in_from_end]
        _, lengths, _ = way.arrays()
        turning = _moving_average(way.curvature(), lengths, 1.0)
        for index in numpy.argsort(-turning):
            if turning[index] < 0.15:
                break
            if all(abs(lengths[index] - d) > 2.0 for d in distances):
                distances.append(float(lengths[index]))
    else:
        distances = [float(d) for d in at]
        for d in distances:
            if not 0.0 <= d <= way.total:
                raise ValueError('a pothole at %.2f m is off the line (it is %.2f m long)' % (d, way.total))
    radius = float(size) / 2.0
    holes = []
    for distance in distances:
        point = way.at(distance)
        ahead = way.at(min(way.total, distance + 0.05)) - way.at(max(0.0, distance - 0.05))
        ahead.z = 0.0
        ahead = ahead.normalized() if ahead.length > 1e-6 else Vector((0.0, 1.0, 0.0))
        left = Vector((-ahead.y, ahead.x, 0.0))
        for offset in lines[which]:
            holes.append((point + left * offset, ahead, radius * rng.uniform(0.8, 1.2), rng.uniform(0.0, 50.0)))
    if not holes:
        return {'spots': [], 'made': [], 'deepest': 0.0}

    def inside(xy):
        near = numpy.zeros(len(xy), dtype=bool)
        for centre, _, r, _ in holes:
            near |= numpy.hypot(xy[:, 0] - centre.x, xy[:, 1] - centre.y) <= r * 2.0
        return near
    reach = max(abs(o) for o in lines[which]) + radius * 2.4 + 0.1
    mark = _Mark(ground, way, reach, inside, detail, keep=inside)
    if not len(mark.index):
        return {'spots': [], 'made': [], 'deepest': 0.0}
    dry_soak = _drying(mark.dial)
    angles = numpy.linspace(-math.pi, math.pi, 73)
    for centre, ahead, r, key in holes:
        near = numpy.array(mark.tree.query_ball_point([centre.x, centre.y], r * 2.0), dtype=numpy.int64)
        if not len(near):
            continue
        offset = mark.xy[near] - numpy.array([centre.x, centre.y])
        u = offset @ numpy.array([ahead.x, ahead.y])
        v = offset @ numpy.array([-ahead.y, ahead.x])
        ring = numpy.array([0.12 * noise.noise(Vector((math.cos(t) * 1.5 + key, math.sin(t) * 1.5, key * 0.61 + 0.3)))
                            + 0.06 * noise.noise(Vector((math.cos(t) * 4.5 - key, math.sin(t) * 4.5, key * 0.37 + 0.7))) for t in angles])
        ragged = 1.0 + numpy.interp(numpy.arctan2(v, u), angles, ring)
        reach_u = numpy.where(u > 0, r * 0.8, r * 1.25) * ragged          # steep in front, drawn out behind
        rr = numpy.sqrt((u / reach_u) ** 2 + (v / (r * ragged)) ** 2)
        wet_here = float(numpy.median(mark.wet[near[rr < 1.0]])) if (rr < 1.0).any() else mark.dial
        depth = (0.05 + 0.10 * age) * (0.7 + 0.5 * wet_here)
        churned = numpy.array([noise.noise(Vector((p * 8.0, q * 8.0, key))) for p, q in zip(u, v)])
        hole = -depth * (1.0 + 0.2 * churned * float(_smoothstep(0.3, 0.8, wet_here))) * \
            numpy.clip(1.0 - rr ** numpy.where(u > 0, 4.0, 1.5), 0.0, None) ** 0.7
        behind = _smoothstep(0.3, -0.3, u / r)
        splash = depth * 0.25 * behind * _bump((rr - 1.15) / 0.2) * (1.0 - 0.5 * age) * float(_smoothstep(0.3, 0.7, wet_here))
        floor = numpy.clip(1.0 - rr, 0.0, 1.0)
        mark.add_groove(hole, splash, floor, where=near)
        mark.add_tread(numpy.zeros_like(floor), v, u, 0.0, floor, where=near)
        mark.raise_number('smear', floor * 0.6 * float(_smoothstep(0.3, 0.75, wet_here)), where=near)
        mark.raise_number('wear', floor * 0.3 * (1.0 - wet_here), where=near)
        mark.raise_number('drop_extra', floor * depth * _water_hold(age) * 0.6 * dry_soak, where=near)
        mark.raise_number('track_crust', floor * float(_smoothstep(0.6, 0.95, age)) * (1.0 - mark.dial) * 0.9, where=near)
    return mark.finish(soften=0.01 + 0.05 * age, seed=seed, age=age, collection=collection)


# ----------------------------------------------------------------------------------------------- command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Carve ruts, a path, footprints or potholes into a ground the ground tool '
                                                 'made (see the note at the top of tracks.py).')
    parser.add_argument('--blend', help='the .blend file holding the ground')
    parser.add_argument('--ground', default='ground', help="the ground object's name; default 'ground'")
    parser.add_argument('--kind', choices=('ruts', 'path', 'footprints', 'potholes'), default='ruts', help='which mark; default ruts')
    parser.add_argument('--points', help='the line as "x,y,z x,y,z ..."')
    parser.add_argument('--vehicle', default='cart', help="ruts and potholes: 'cart', 'car', 'lorry' or 'tractor'; default cart")
    parser.add_argument('--no-horse', action='store_true', help="ruts: leave out a cart's horse's hoof prints")
    parser.add_argument('--passes', type=int, default=1, help='ruts: how many times wheels went this way; default 1')
    parser.add_argument('--width', type=float, default=0.5, help='path: the trodden strip, metres; default 0.5')
    parser.add_argument('--stride', type=float, default=0.75, help='footprints: from one print to the next, metres; default 0.75')
    parser.add_argument('--at', type=float, nargs='*', help="potholes: distances along the line (none given: 'ends and turns')")
    parser.add_argument('--size', type=float, default=0.5, help='potholes: across, metres; default 0.5')
    parser.add_argument('--which', default='both', help="potholes: 'both', 'left', 'right' or 'middle'; default both")
    parser.add_argument('--age', type=float, default=None, help='0 fresh .. 1 old (default by kind)')
    parser.add_argument('--seed', type=int, default=0, help='the same seed, the same marks; default 0')
    parser.add_argument('--out', help='save the result here')
    args = parser.parse_args(argv)
    if not args.blend or not args.points:
        parser.error('give --blend (a file with the ground) and --points (the line)')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    if args.ground not in bpy.data.objects:
        parser.error('no object %r in the file; its objects are: %s' % (args.ground, ', '.join(o.name for o in bpy.data.objects)))
    where = bpy.data.objects[args.ground]
    line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()]
    if args.kind == 'ruts':
        result = ruts(where, line, vehicle=args.vehicle, passes=args.passes, age=0.3 if args.age is None else args.age, seed=args.seed,
                      horse=False if args.no_horse else None)
    elif args.kind == 'path':
        result = path(where, line, width=args.width, age=0.5 if args.age is None else args.age, seed=args.seed)
    elif args.kind == 'footprints':
        result = footprints(where, line, stride=args.stride, age=0.2 if args.age is None else args.age, seed=args.seed)
    else:
        result = potholes(where, line, at=args.at if args.at else 'ends and turns', size=args.size, which=args.which,
                          vehicle=args.vehicle, age=0.6 if args.age is None else args.age, seed=args.seed)
    print('carved %s: deepest %.3f m; water stands in %d places along it' % (args.kind, result['deepest'], len(result['spots'])))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
