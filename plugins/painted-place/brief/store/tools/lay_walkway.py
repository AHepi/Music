"""
What this file does: lays a duckboard walkway along a line you give. Straight sections of slatted boards nailed across
two runners, laid end to end the way real duckboards were (in sections about 2.4 m long), each section and each board
with its own small tilt, sink and shade; the middle of the boards worn paler where boots go; wet films on the wood; rusty
nail heads, some with a rust run; and, only if you ask, mud trodden onto the boards and lumped where the walkway meets
the ground. It decides nothing about where the walkway goes: the line is yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import lay_walkway
    made = lay_walkway.lay([(0, 0, 0), (0.4, 5, 0), (2.5, 11, 0.6)], width=0.6, seed=3)
    made = lay_walkway.lay(bpy.data.objects['Path'], ground=bpy.data.objects['Ground'], mud_at_ends=0.6)

The line may be a list of points (x, y, z), a curve object, a mesh object made of a line of edges, or the path of a JSON
file holding {"points": [[x, y, z], ...]}. With `ground` (a mesh object), every section rests on that object's surface
(rays are cast straight down onto it) instead of on the line's own heights. The walkway is laid in equal sections of
about `section_length` from the first point to the last; a tight bend wants a shorter section_length.

From the command line:

    python3 lay_walkway.py --help
    python3 lay_walkway.py --points "0,0,0 0.4,5,0 2.5,11,0.6" --out walkway.blend
    python3 lay_walkway.py --blend camp.blend --line Path --ground Ground --out camp_with_walkway.blend

Options, with their defaults:
    width            0.6 m      across the walkway (the boards' length)
    board_width      0.2 m      each board, along the walkway
    gap              0.035 m    between boards
    board_thickness  0.035 m
    runner_width     0.07 m     the two timbers under the boards
    runner_height    0.05 m
    runner_inset     0.1 m      how far in from the boards' ends the runners sit
    section_length   2.4 m      one section of duckboard
    sag              0.01 m     how far the middle of a section sags
    wear             0.7        0 none to 1: the middle of the boards polished pale by boots
    wet              0.4        0 dry to 1: standing water films on the wood
    mud_at_ends      0          0 none to 1: mud lumps where the walkway meets the ground, and mud trodden onto the first boards
    missing          0.02       the chance a board is gone
    nails            True       nail heads where boards cross the runners
    rust             0.35       the chance a nail has a rust run along the board
    ground           none       a mesh object to rest the sections on
    seed             0          the same seed lays the same walkway
    collection       none       where to put the objects (default: a new collection 'walkway')

Sharp corners in the line (a turn of more than 25 degrees at one of its points) are kept: the section before a corner
runs a little past it, and the next begins where its first board lies clear of that one. A smooth curve is laid in straight sections of about section_length, so a tight bend
wants a shorter section_length.

It returns the objects it made: 'walkway boards', 'walkway runners', 'walkway nails', 'walkway rust' and, with mud,
'walkway mud'. Boards and runners carry the UV map 'metres' and the numbers 'MADE • walkway boards' reads.
"""

import argparse
import bisect
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

TOOL = {
    'name': 'lay_walkway',
    'what': 'a duckboard walkway along a line you give: sections of nailed boards on runners, worn, wet, nails rusting; mud only if asked',
    'call': "lay_walkway.lay([(0, 0, 0), (0.4, 5, 0), (2.5, 11, 0.6)], width=0.6, ground=ground_object, seed=3)",
    'options': {
        'width': 'across the walkway, the boards\' length (0.6 m)',
        'board_width': 'each board along the walkway (0.2 m)',
        'gap': 'between boards (0.035 m)',
        'board_thickness': '0.035 m',
        'runner_width': '0.07 m', 'runner_height': '0.05 m',
        'runner_inset': 'how far in from the boards\' ends the runners sit (0.1 m)',
        'section_length': 'one section of duckboard; shorter follows a tight bend better (2.4 m)',
        'sag': 'how far the middle of a section sags (0.01 m)',
        'wear': 'the middle of the boards polished pale, 0 to 1 (0.7)',
        'wet': 'standing water films on the wood, 0 to 1 (0.4)',
        'mud_at_ends': 'mud lumps where the walkway meets the ground and mud on the first boards, 0 to 1 (0: none)',
        'missing': 'the chance a board is gone (0.02)',
        'nails': 'nail heads where boards cross the runners (True)',
        'rust': 'the chance a nail has a rust run (0.35)',
        'ground': 'a mesh object to rest the sections on (none: the line\'s own heights)',
        'seed': 'the same seed lays the same walkway (0)',
    },
    'materials': ['MADE • walkway boards', 'MADE • rusty nail heads', 'MADE • rust stain', 'MADE • wet mud'],
    'source': 'the duckboards of the military base builders (log 50, first and second pass scripts), made into a tool (log 51)',
    'trap': 'sharp corners in your line are kept (a section ends at each); a smooth curve is laid in straight sections, so a tight bend wants a shorter section_length',
}

UP = Vector((0.0, 0.0, 1.0))


# ------------------------------------------------------------------------------------------------ the line

def _chain(mesh):
    """The vertex order of a mesh made of one line of edges (from one end to the other)."""
    if not mesh.edges:
        return list(range(len(mesh.vertices)))
    neighbours = {index: [] for index in range(len(mesh.vertices))}
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbours[a].append(b)
        neighbours[b].append(a)
    ends = [index for index, near in neighbours.items() if len(near) == 1]
    start = ends[0] if ends else next(index for index, near in neighbours.items() if near)
    order, seen = [start], {start}
    while True:
        following = [index for index in neighbours[order[-1]] if index not in seen]
        if not following:
            return order
        order.append(following[0])
        seen.add(following[0])


def line_points(line):
    """World points of the line: a list of points, a curve or mesh object, or a JSON file of points."""
    if isinstance(line, str):
        with open(line) as handle:
            data = json.load(handle)
        line = data['points'] if isinstance(data, dict) else data
    if isinstance(line, bpy.types.Object):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = line.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points = [line.matrix_world @ mesh.vertices[index].co for index in _chain(mesh)]
        finally:
            evaluated.to_mesh_clear()
        return points
    return [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in line]


class Path:
    """A polyline measured along its length."""

    def __init__(self, points):
        kept = [Vector(points[0])]
        for point in points[1:]:
            if (Vector(point) - kept[-1]).length > 1e-5:
                kept.append(Vector(point))
        if len(kept) < 2:
            raise ValueError('the line needs at least two different points')
        self.points = kept
        self.lengths = [0.0]
        for a, b in zip(kept, kept[1:]):
            self.lengths.append(self.lengths[-1] + (b - a).length)
        self.total = self.lengths[-1]

    def at(self, distance):
        distance = min(max(distance, 0.0), self.total)
        index = min(bisect.bisect_right(self.lengths, distance) - 1, len(self.points) - 2)
        span = self.lengths[index + 1] - self.lengths[index]
        t = (distance - self.lengths[index]) / span if span > 0 else 0.0
        return self.points[index].lerp(self.points[index + 1], t)


def _clear_start(extension, turn, width, board_width):
    """How far past a corner the next run must start (along its own way) so that its first board lies clear of the last
    run, which runs `extension` metres past the corner; `turn` is the signed angle between the two ways (radians)."""
    half = width / 2
    cos_turn, sin_turn = math.cos(turn), math.sin(turn)
    start = 0.0
    while start < 2.5 * width:
        clear = True
        for i in range(8):
            along = start + board_width * i / 7
            for j in range(9):
                across = -half + width * j / 8
                x = along * cos_turn - across * sin_turn          # in the last run's frame: x along it, y across it
                y = along * sin_turn + across * cos_turn
                if -2.0 * width <= x <= extension - 0.002 and abs(y) <= half - 0.002:
                    clear = False
                    break
            if not clear:
                break
        if clear:
            return start
        start += 0.01
    return start


def section_bounds(path, section_length, width, corner_angle=25.0, board_width=0.2):
    """Each straight section's start and end: (distance along the line at the start, at the end, start point, end point).
    The line is cut at its corners (where it turns by more than corner_angle degrees at one of its points), and each run
    between corners into equal sections of about section_length. At a corner the run before it goes on a little past
    the corner, as a through section of duckboard would, and the run after it begins where its first board lies clear of
    that one, so the corner is crossed with neither a hole in the middle of the way nor boards through each other."""
    corners = []
    for index in range(1, len(path.points) - 1):
        before = path.points[index] - path.points[index - 1]
        after = path.points[index + 1] - path.points[index]
        before.z = after.z = 0.0
        if before.length > 1e-6 and after.length > 1e-6 and math.degrees(before.angle(after)) > corner_angle:
            into, out = before.normalized(), after.normalized()
            turn = math.atan2(into.x * out.y - into.y * out.x, into.dot(out))
            # how far the run before the corner goes past it: enough that its last board lies over the way that turns
            extension = 0.6 * board_width if abs(turn) >= math.radians(89.0) else max(0.6 * board_width, min(0.25 * width, (width / 2) / math.tan(abs(turn))))
            corners.append({'distance': path.lengths[index], 'point': path.points[index].copy(), 'into': into,
                            'extension': extension, 'clear': _clear_start(extension, turn, width, board_width)})
    bounds = []
    edges = [None] + corners + [None]
    for before, after in zip(edges, edges[1:]):
        start = before['distance'] + before['clear'] if before else 0.0
        end = after['distance'] if after else path.total
        if end - start < 0.25:
            continue
        count = max(1, int(round(end - start) / section_length + 0.5)) if end - start > section_length else 1
        each = (end - start) / count
        cuts = [start + k * each for k in range(count + 1)]
        points = [path.at(d) for d in cuts]
        if after:
            corner = after['point']
            points[-1] = corner + after['into'] * after['extension']
        bounds.extend((cuts[k], cuts[k + 1], points[k], points[k + 1]) for k in range(count))
    return bounds


def _ground_height(ground, x, y, fallback):
    """The height of the ground object straight below (x, y), or the fallback if the ray misses it."""
    if ground is None:
        return fallback
    inverse = ground.matrix_world.inverted()
    origin = inverse @ Vector((x, y, fallback + 200.0))
    direction = (inverse.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    hit, location, _normal, _index = ground.ray_cast(origin, direction)
    if not hit:
        return fallback
    return (ground.matrix_world @ location).z


# ------------------------------------------------------------------------------------------------ meshes

class MeshParts:
    """Collects boxes and beams into one mesh, with a UV map in metres (grain along V) and numbers per point."""

    def __init__(self, names):
        self.vertices, self.faces, self.face_uvs = [], [], []
        self.values = {name: [] for name in names}

    def _add_values(self, count, values, local_points):
        for name in self.values:
            value = values.get(name, 0.0)
            if callable(value):
                self.values[name].extend(value(p) for p in local_points)
            else:
                self.values[name].extend([value] * count)

    def box(self, centre, axis_x, axis_y, axis_z, size, values, uv_offset, end_skew=(0.0, 0.0)):
        """A box in the frame (axis_x, axis_y, axis_z), right-handed. The grain runs along axis_x.
        end_skew moves the two ends' corners along axis_x by +-skew x (y / half width): a slightly angled saw cut."""
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        start = len(self.vertices)
        local = []
        for sz in (0, 1):
            for sy in (0, 1):
                for sx in (0, 1):
                    x = (sx * 2 - 1) * hx
                    y = (sy * 2 - 1) * hy
                    z = (sz * 2 - 1) * hz
                    x += (end_skew[1] if sx else end_skew[0]) * (y / hy)
                    local.append(Vector((x, y, z)))
                    self.vertices.append(centre + axis_x * x + axis_y * y + axis_z * z)
        ou, ov = uv_offset
        quads = {  # outward, counter-clockwise from outside; the key says which local axes give (U, V)
            (0, 2, 3, 1): ('y', 'x'), (4, 5, 7, 6): ('y', 'x'),        # bottom, top: U across, V along the grain
            (0, 1, 5, 4): ('z', 'x'), (2, 6, 7, 3): ('z', 'x'),        # the long sides
            (0, 4, 6, 2): ('y', 'z'), (1, 3, 7, 5): ('y', 'z'),        # the ends (end grain)
        }
        for quad, (u_axis, v_axis) in quads.items():
            self.faces.append(tuple(start + corner for corner in quad))
            self.face_uvs.append([(getattr(local[c], u_axis) + ou, getattr(local[c], v_axis) + ov) for c in quad])
        self._add_values(8, values, local)

    def beam(self, rings, values, uv_offset):
        """A beam through rings of four corners each (bottom-left, bottom-right, top-right, top-left), with each
        ring's distance along the beam; grain along the beam."""
        start = len(self.vertices)
        count = len(rings)
        ou, ov = uv_offset
        uv_corner = []
        for corners, along in rings:
            for index, corner in enumerate(corners):
                self.vertices.append(corner)
                uv_corner.append((index, along))
        width_u = {0: 0.0, 1: 0.07, 2: 0.12, 3: 0.19}

        def uv(vertex):
            index, along = uv_corner[vertex - start]
            return (width_u[index] + ou, along + ov)

        def ring(i, corner):
            return start + 4 * i + corner
        for i in range(count - 1):
            for quad in ((ring(i, 0), ring(i + 1, 0), ring(i + 1, 1), ring(i, 1)),       # bottom
                         (ring(i, 3), ring(i, 2), ring(i + 1, 2), ring(i + 1, 3)),       # top
                         (ring(i, 0), ring(i, 3), ring(i + 1, 3), ring(i + 1, 0)),       # left
                         (ring(i, 1), ring(i + 1, 1), ring(i + 1, 2), ring(i, 2))):      # right
                self.faces.append(quad)
                self.face_uvs.append([uv(v) for v in quad])
        last = count - 1
        for quad in ((ring(0, 0), ring(0, 1), ring(0, 2), ring(0, 3)),
                     (ring(last, 0), ring(last, 3), ring(last, 2), ring(last, 1))):
            self.faces.append(quad)
            self.face_uvs.append([uv(v) for v in quad])
        self._add_values(4 * count, values, [None] * (4 * count))

    def build(self, name, collection, material):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(v) for v in self.vertices], [], self.faces)
        layer = mesh.uv_layers.new(name='metres')
        flat = [uv for corners in self.face_uvs for uv in corners]
        layer.data.foreach_set('uv', [c for uv in flat for c in uv])
        for value_name, values in self.values.items():
            attribute = mesh.attributes.new(value_name, 'FLOAT', 'POINT')
            attribute.data.foreach_set('value', values)
        mesh.validate()
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.data.materials.append(material)
        return obj


def _bmesh_object(name, bm, collection, material, values=None):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if values:
        for value_name, data in values.items():
            attribute = mesh.attributes.new(value_name, 'FLOAT', 'POINT')
            attribute.data.foreach_set('value', data)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


# ------------------------------------------------------------------------------------------------ the walkway

def lay(line, width=0.6, board_width=0.2, gap=0.035, board_thickness=0.035, runner_width=0.07, runner_height=0.05,
        runner_inset=0.1, section_length=2.4, sag=0.01, wear=0.7, wet=0.4, mud_at_ends=0.0, missing=0.02, nails=True,
        rust=0.35, ground=None, seed=0, collection=None, board_material='MADE • walkway boards',
        nail_material='MADE • rusty nail heads', rust_material='MADE • rust stain', mud_material='MADE • wet mud'):
    """Lay the walkway along the line; returns the objects made."""
    rng = random.Random(seed)
    path = Path(line_points(line))
    if collection is None:
        collection = bpy.data.collections.new('walkway')
        bpy.context.scene.collection.children.link(collection)
    boards = MeshParts(['board_tone', 'across', 'wear', 'wet', 'mud'])
    runners = MeshParts(['board_tone', 'across', 'wear', 'wet', 'mud'])
    nail_mesh = bmesh.new()
    rust_mesh = bmesh.new()
    rust_fade = []
    bounds = section_bounds(path, section_length, width, board_width=board_width)
    runner_offset = width / 2 - runner_inset
    board_count = 0
    nail_count = 0

    def mud_here(distance_along):
        if mud_at_ends <= 0:
            return 0.0
        nearest_end = min(distance_along, path.total - distance_along)
        return mud_at_ends * max(0.0, 1.0 - nearest_end / 2.2) ** 1.2

    for s0, s1, start, end in bounds:
        flat = Vector((end.x - start.x, end.y - start.y, 0.0))
        if flat.length < 1e-6:
            continue
        half_span = flat.length / 2
        flat.normalize()
        flat = Matrix.Rotation(math.radians(rng.uniform(-0.8, 0.8)), 3, 'Z') @ flat   # each section turned a little about its middle
        side = flat.cross(UP).normalized()          # to the right when walking from start to end
        joint = 0.012                               # a small gap at each joint between sections
        middle_point = (start + end) / 2
        a = middle_point - flat * (half_span - joint)
        b = middle_point + flat * (half_span - joint)
        a.z, b.z = start.z, end.z
        # the four corners the runners rest on: each on the ground (or the line), sunk a little into it
        sink = rng.uniform(0.0, 0.025)
        lift_start, lift_end = rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008)
        rest = {}
        for side_sign in (-1, 1):
            for end_name, point, lift in (('start', a, lift_start), ('end', b, lift_end)):
                spot = point + side * (side_sign * runner_offset)
                rest[(side_sign, end_name)] = _ground_height(ground, spot.x, spot.y, point.z) - sink + lift + side_sign * rng.uniform(-0.006, 0.006)
            if ground is not None:      # a hump in the middle lifts the runner instead of passing through it
                middle = (a + b) / 2 + side * (side_sign * runner_offset)
                mid_ground = _ground_height(ground, middle.x, middle.y, middle.z) - sink
                straight = (rest[(side_sign, 'start')] + rest[(side_sign, 'end')]) / 2
                if mid_ground > straight:
                    rest[(side_sign, 'start')] += mid_ground - straight
                    rest[(side_sign, 'end')] += mid_ground - straight
        span = (b - a)
        span.z = 0.0
        span_length = span.length
        section_sag = sag * rng.uniform(0.5, 1.5)

        def runner_bottom(side_sign, t):
            spot = a + span * t + side * (side_sign * runner_offset)
            z = rest[(side_sign, 'start')] * (1 - t) + rest[(side_sign, 'end')] * t - section_sag * 4 * t * (1 - t)
            return Vector((spot.x, spot.y, z))

        def runner_top(side_sign, t):
            return runner_bottom(side_sign, t) + UP * runner_height

        # where the boards go (centred in the section), then the runners under them, then the boards
        # the boards spread evenly over the whole section (each gap within a few millimetres of the one asked for), so the
        # sections read as one walkway with only a slightly wider joint between them
        count = max(1, int(round(span_length / (board_width + gap))))
        spacing = span_length / count - board_width
        pitch = board_width + spacing
        first = spacing / 2 + board_width / 2
        # runners: one beam each side, bent by the sag
        run_start = max(0.0, first - board_width / 2 - 0.025) / span_length   # the runners stop just past the end boards
        run_end = min(span_length, first + (count - 1) * pitch + board_width / 2 + 0.025) / span_length
        steps = max(2, int(span_length * (run_end - run_start) / 0.3))
        tone_runner = rng.uniform(0.05, 0.3)
        for side_sign in (-1, 1):
            rings = []
            for step in range(steps + 1):
                t = run_start + (run_end - run_start) * step / steps
                bottom = runner_bottom(side_sign, t)
                half = side * (runner_width / 2)
                rings.append(((bottom - half, bottom + half, bottom + half + UP * runner_height, bottom - half + UP * runner_height),
                              t * span_length))
            runners.beam(rings, {'board_tone': tone_runner, 'across': 1.0, 'wear': 0.0, 'wet': min(1.0, wet * 1.3),
                                 'mud': mud_here((s0 + s1) / 2)}, (rng.uniform(0, 4), rng.uniform(0, 4)))
        for index in range(count):
            if 0 < index < count - 1 and rng.random() < missing:
                continue
            u = first + index * pitch + rng.uniform(-0.008, 0.008)
            t = u / span_length
            left, right = runner_top(-1, t), runner_top(1, t)
            axis_x = (right - left).normalized()
            along = (runner_top(-1, min(1.0, t + 0.01)) + runner_top(1, min(1.0, t + 0.01))) / 2 - (left + right) / 2
            axis_y = (along - axis_x * along.dot(axis_x)).normalized()
            turn = Matrix.Rotation(math.radians(rng.uniform(-1.3, 1.3)), 3, axis_x.cross(axis_y))
            axis_x, axis_y = turn @ axis_x, turn @ axis_y
            axis_z = axis_x.cross(axis_y)
            thickness = board_thickness * rng.uniform(0.9, 1.1)
            this_width = board_width * rng.uniform(0.94, 1.04)
            length = width + rng.uniform(-0.015, 0.015)
            broken = rng.random() < 0.02
            shift = 0.0
            if broken:     # a broken board: one end snapped off short
                cut = rng.uniform(0.08, max(0.09, runner_inset * 0.8))
                length -= cut
                shift = cut / 2 * rng.choice((-1, 1))
            centre = (left + right) / 2 + axis_z * (thickness / 2) + axis_x * shift
            distance_along = s0 + joint + u
            tone = rng.random()
            board_wear = wear * rng.uniform(0.75, 1.1)
            board_wet = min(1.0, wet * rng.uniform(0.5, 1.3))
            board_mud = min(1.0, mud_here(distance_along) * rng.uniform(0.6, 1.2))
            half_length = length / 2
            boards.box(centre, axis_x, axis_y, axis_z, (length, this_width, thickness),
                       {'board_tone': tone, 'across': (lambda p, h=half_length, s=shift: max(-1.0, min(1.0, (p.x + s) / (width / 2)))),
                        'wear': board_wear, 'wet': board_wet, 'mud': board_mud},
                       (rng.uniform(0, 4), rng.uniform(0, 4)),
                       end_skew=(rng.uniform(-0.006, 0.006), rng.uniform(-0.006, 0.006)))
            board_count += 1
            if not nails:
                continue
            top = centre + axis_z * (thickness / 2)
            for side_sign in (-1, 1):
                for offset in (-0.3, 0.3):
                    spot = top + axis_x * (side_sign * runner_offset - shift + rng.uniform(-0.006, 0.006)) + axis_y * (offset * this_width + rng.uniform(-0.006, 0.006))
                    frame = Matrix((axis_x, axis_y, axis_z)).transposed().to_4x4()
                    frame.translation = spot + axis_z * 0.0012
                    bmesh.ops.create_cone(nail_mesh, cap_ends=True, segments=6, radius1=0.0078, radius2=0.0062, depth=0.003, matrix=frame)
                    nail_count += 1
                    if rng.random() < rust:
                        run = rng.uniform(0.04, 0.15)
                        direction = rng.choice((-1, 1))
                        if direction == side_sign:          # towards the board's end: stop short of it
                            run = min(run, width / 2 - runner_offset - 0.015)
                        half_w = rng.uniform(0.004, 0.008)
                        a_point = spot + axis_z * 0.0006
                        corners = (a_point - axis_y * half_w * 0.6, a_point + axis_y * half_w * 0.6,
                                   a_point + axis_x * (direction * run) + axis_y * half_w * 1.3,
                                   a_point + axis_x * (direction * run) - axis_y * half_w * 1.3)
                        made_verts = [rust_mesh.verts.new(c) for c in corners]
                        rust_mesh.faces.new(made_verts if direction < 0 else made_verts[::-1])     # facing up
                        rust_fade.extend((0.0, 0.0, 1.0, 1.0))
    made = [boards.build('walkway boards', collection, store.material(board_material)),
            runners.build('walkway runners', collection, store.material(board_material))]
    if nails and nail_count:
        made.append(_bmesh_object('walkway nails', nail_mesh, collection, store.material(nail_material)))
    else:
        nail_mesh.free()
    if rust_fade:
        rust_object = _bmesh_object('walkway rust', rust_mesh, collection, store.material(rust_material), {'fade': rust_fade})
        for polygon in rust_object.data.polygons:
            polygon.use_smooth = False
        made.append(rust_object)
    else:
        rust_mesh.free()
    if mud_at_ends > 0:
        made.append(_mud_lumps(path, width, mud_at_ends, ground, rng, collection, store.material(mud_material)))
    for obj in made:
        store.mark(obj, ground=_ground_height(ground, *path.at(0.0).xy, path.at(0.0).z) if ground else path.at(0.0).z)
    made[0]['walkway_boards'] = board_count
    return made


def _mud_lumps(path, width, amount, ground, rng, collection, material):
    """Churned mud where boots step off both ends of the walkway: a low ragged patch of trodden mud that sinks into the
    ground at its rim, running a little under the first boards, with a few small clods on it."""
    bm = bmesh.new()
    rings, segments = 9, 30
    for at_end in (False, True):
        here = path.at(path.total if at_end else 0.0)
        ahead = (path.at(path.total - 0.5) if at_end else path.at(0.5)) - here
        ahead.z = 0.0
        ahead = ahead.normalized() if ahead.length > 1e-6 else Vector((0.0, 1.0, 0.0))
        side = ahead.cross(UP)
        reach = 0.55 + 0.6 * amount                     # how far the patch runs out from the walkway's end
        spread = width * (0.75 + 0.5 * amount)
        centre = here - ahead * (reach * 0.45)
        seed_shift = Vector((rng.uniform(0, 100), rng.uniform(0, 100), 0.0))
        ring_verts = []
        middle_z = _ground_height(ground, centre.x, centre.y, here.z)
        middle = bm.verts.new(centre + UP * (middle_z - centre.z + 0.012 * amount))
        for ring in range(1, rings + 1):
            radius = ring / rings
            row = []
            for k in range(segments):
                angle = math.tau * k / segments
                direction = Vector((math.cos(angle), math.sin(angle), 0.0))
                ragged = 1.0 + 0.32 * noise.noise(direction * 1.7 + seed_shift) + 0.12 * noise.noise(direction * 5.0 + seed_shift)
                flat = centre + ahead * (direction.x * radius * ragged * reach) + side * (direction.y * radius * ragged * spread)
                z = _ground_height(ground, flat.x, flat.y, here.z)
                churn = noise.noise(flat * 3.5 + seed_shift) * 0.6 + noise.noise(flat * 11.0 + seed_shift) * 0.4
                raised = (0.014 + 0.018 * churn) * amount * (1.0 - radius ** 3) - 0.01 * radius ** 4
                row.append(bm.verts.new((flat.x, flat.y, z + raised)))
            ring_verts.append(row)
        for k in range(segments):
            bm.faces.new((middle, ring_verts[0][k], ring_verts[0][(k + 1) % segments]))
        for ring in range(rings - 1):
            inner, outer = ring_verts[ring], ring_verts[ring + 1]
            for k in range(segments):
                bm.faces.new((inner[k], outer[k], outer[(k + 1) % segments], inner[(k + 1) % segments]))
        for _ in range(int(4 + 10 * amount)):       # a few small clods kicked onto the patch
            u, v = rng.uniform(-0.9, 0.5), rng.uniform(-0.8, 0.8)
            spot = centre + ahead * (u * reach) + side * (v * spread)
            z = _ground_height(ground, spot.x, spot.y, here.z)
            size = rng.uniform(0.018, 0.05)
            matrix = Matrix.Translation((spot.x, spot.y, z + size * 0.15)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ \
                Matrix.Diagonal((size * rng.uniform(1.0, 1.8), size, size * rng.uniform(0.45, 0.7), 1.0))
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=matrix)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _bmesh_object('walkway mud', bm, collection, material)


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Lay a duckboard walkway along a line you give (see the note at the top of lay_walkway.py).')
    parser.add_argument('--points', help='the line as "x,y,z x,y,z ..." (makes a new file unless --blend is given)')
    parser.add_argument('--points-json', help='a JSON file holding {"points": [[x, y, z], ...]}')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--ground', help='the name of a ground mesh object in the --blend file to rest the walkway on')
    parser.add_argument('--out', required=False, help='save the result here')
    helps = {
        'width': 'across the walkway, the boards\' length, metres', 'board-width': 'each board along the walkway, metres',
        'gap': 'between boards, metres', 'board-thickness': 'metres', 'runner-width': 'the two timbers under the boards, metres',
        'runner-height': 'metres', 'runner-inset': 'how far in from the boards\' ends the runners sit, metres',
        'section-length': 'one section of duckboard, metres; shorter follows a tight bend better',
        'sag': 'how far the middle of a section sags, metres', 'wear': 'the middle of the boards polished pale, 0 to 1',
        'wet': 'standing water films on the wood, 0 to 1', 'mud-at-ends': 'churned mud where the walkway meets the ground, 0 (none) to 1',
        'missing': 'the chance a board is gone', 'rust': 'the chance a nail has a rust run'}
    for name, default in (('width', 0.6), ('board-width', 0.2), ('gap', 0.035), ('board-thickness', 0.035),
                          ('runner-width', 0.07), ('runner-height', 0.05), ('runner-inset', 0.1),
                          ('section-length', 2.4), ('sag', 0.01), ('wear', 0.7), ('wet', 0.4), ('mud-at-ends', 0.0),
                          ('missing', 0.02), ('rust', 0.35)):
        parser.add_argument('--' + name, type=float, default=default, help='%s; default %s' % (helps[name], default))
    parser.add_argument('--no-nails', action='store_true', help='leave out the nail heads and rust runs')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same walkway; default 0')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    if args.line:
        if args.line not in bpy.data.objects:
            parser.error('no object %r in the file; its objects are: %s' % (args.line, ', '.join(o.name for o in bpy.data.objects)))
        line = bpy.data.objects[args.line]
    elif args.points_json:
        line = args.points_json
    elif args.points:
        line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()]
    else:
        parser.error('give the line: --points, --points-json or --line')
    if args.ground and args.ground not in bpy.data.objects:
        parser.error('no object %r in the file to rest the walkway on' % args.ground)
    ground = bpy.data.objects[args.ground] if args.ground else None
    if not args.out:
        print('note: nothing will be saved; give --out FILE.blend to keep the walkway')
    made = lay(line, width=args.width, board_width=args.board_width, gap=args.gap, board_thickness=args.board_thickness,
               runner_width=args.runner_width, runner_height=args.runner_height, runner_inset=args.runner_inset,
               section_length=args.section_length, sag=args.sag, wear=args.wear, wet=args.wet,
               mud_at_ends=args.mud_at_ends, missing=args.missing, nails=not args.no_nails, rust=args.rust,
               ground=ground, seed=args.seed)
    print('made', ', '.join(obj.name for obj in made), '-', made[0]['walkway_boards'], 'boards')
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)


if __name__ == '__main__':
    main()
