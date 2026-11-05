"""
What this file does: checks the wall tool (lay_wall): on planes from 1 x 1 m to 12 x 6 m, facing +X, -X, +Y and -Y,
lying flat, turned within their own plane, all with unapplied scale and rotation, the bricks or blocks cover the plane
exactly (every unit inside the outline, the courses reaching within a joint of every edge, whole courses from bottom to
top); the bonds are kept (stretcher: each joint halfway along the brick above; Flemish: headers and stretchers
alternate, each header centred on the stretcher below; English: stretcher and header courses alternate); the bricks are
real size and the relief within limits; a gable's units stay inside its slopes; stone works too; every unit carries its
own 'pp_piece' and its 'pp_atlas' lies inside one rectangle of its set's atlas; the same seed lays the same wall, wrong
options are refused and --help answers.
    python3 tests/test_store_wall.py
"""
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import STORE, TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import lay_wall  # noqa: E402

BRICK_RISE = 0.075


def plane(name, width, height, location, rotation, scale=(1.0, 1.0)):
    """A 1 x 1 plane scaled to width x height and turned, its scale and rotation left unapplied."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location, rotation=[math.radians(r) for r in rotation])
    obj = bpy.context.object
    obj.name = name
    obj.scale = (width * scale[0], height * scale[1], 1.0)
    bpy.context.view_layer.update()
    return obj


def frame_of(obj):
    """The plane's own frame, worked out here from its face (not by the tool): origin, along, up, out, outline."""
    matrix = obj.matrix_world
    polygon = obj.data.polygons[0]
    out = (matrix.to_3x3().inverted_safe().transposed() @ polygon.normal).normalized()
    if abs(out.z) >= 0.7:
        along = matrix.to_3x3() @ Vector((1.0, 0.0, 0.0))
        along = (along - out * along.dot(out)).normalized()
    else:
        along = Vector((0.0, 0.0, 1.0)).cross(out).normalized()
    up = out.cross(along)
    origin = matrix @ obj.data.vertices[polygon.vertices[0]].co
    outline = [((matrix @ obj.data.vertices[i].co - origin).dot(along), (matrix @ obj.data.vertices[i].co - origin).dot(up)) for i in polygon.vertices]
    area = 0.5 * sum(outline[i - 1][0] * outline[i][1] - outline[i][0] * outline[i - 1][1] for i in range(len(outline)))
    if area < 0:
        outline.reverse()
    return origin, along, up, out, outline


def units_of(made, frame):
    """Each unit's vertices in the plane's frame (s along, t up, d out) and its UVs, grouped by its pp_piece."""
    mesh = made.data
    origin, along, up, out, _ = frame
    attribute = mesh.attributes.get('pp_piece')
    check(attribute is not None, 'the units carry no pp_piece')
    check(attribute.domain == 'FACE' and attribute.data_type == 'FLOAT', 'pp_piece is %s on %s, not a float on the faces' % (attribute.data_type, attribute.domain))
    layer = mesh.uv_layers.get('pp_atlas')
    check(layer is not None, "the units have no UV map 'pp_atlas'")
    co = numpy.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    matrix = numpy.array(made.matrix_world)
    co = co @ matrix[:3, :3].T + matrix[:3, 3]
    pieces = numpy.empty(len(mesh.polygons))
    attribute.data.foreach_get('value', pieces)
    totals = numpy.empty(len(mesh.polygons), dtype=numpy.int64)
    mesh.polygons.foreach_get('loop_total', totals)
    loop_vertex = numpy.empty(len(mesh.loops), dtype=numpy.int64)
    mesh.loops.foreach_get('vertex_index', loop_vertex)
    uv = numpy.empty(len(mesh.loops) * 2)
    layer.data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2)
    piece_of_loop = numpy.repeat(pieces, totals)
    order = numpy.argsort(piece_of_loop, kind='stable')
    sorted_pieces = piece_of_loop[order]
    starts = numpy.concatenate(([0], numpy.nonzero(numpy.diff(sorted_pieces))[0] + 1))
    points = co[loop_vertex[order]] - numpy.array(origin)
    s = points @ numpy.array(along)
    t = points @ numpy.array(up)
    d = points @ numpy.array(out)
    uv = uv[order]
    result = {'piece': sorted_pieces[starts]}
    for name, values in (('s', s), ('t', t), ('d', d), ('u', uv[:, 0]), ('v', uv[:, 1])):
        result[name + '_min'] = numpy.minimum.reduceat(values, starts)
        result[name + '_max'] = numpy.maximum.reduceat(values, starts)
    result['all_s'], result['all_t'] = s, t
    return result


def inside_convex(outline, s, t, tolerance):
    """True where (s, t) lies inside the convex outline (counter-clockwise), or within tolerance of it."""
    ok = numpy.ones(len(s), dtype=bool)
    for i in range(len(outline)):
        (s0, t0), (s1, t1) = outline[i - 1], outline[i]
        length = math.hypot(s1 - s0, t1 - t0)
        distance = ((s1 - s0) * (t - t0) - (t1 - t0) * (s - s0)) / length
        ok &= distance >= -tolerance
    return ok


def atlas_of(made):
    name = made['atlas']
    path = os.path.join(STORE, 'materials', 'atlas', name + '.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    return lay_wall.STAND_IN[name]


def courses(units, rise_at):
    """Units by course: {course index: [unit indices sorted along]}."""
    centre_t = (units['t_min'] + units['t_max']) / 2
    found = {}
    for i, tc in enumerate(centre_t):
        found.setdefault(rise_at(tc), []).append(i)
    centre_s = (units['s_min'] + units['s_max']) / 2
    return {k: sorted(v, key=lambda i: centre_s[i]) for k, v in found.items()}


def check_cover(label, made, frame, kind):
    """Every unit inside the outline, relief within limits, pp_piece and pp_atlas good, and (for a level rectangle)
    whole courses reaching within a joint of every edge."""
    units = units_of(made, frame)
    outline = frame[4]
    joint = 0.010 if kind == 'brick' else 0.005
    relief = made['relief']
    count = len(units['piece'])
    check(count == made['units'], '%s: %d pieces of pp_piece for %d units (each unit needs its own)' % (label, count, made['units']))
    check(units['piece'].min() >= 0.0 and units['piece'].max() <= 1.0, '%s: pp_piece outside 0 to 1' % label)
    inside = inside_convex(outline, units['all_s'], units['all_t'], 0.001)
    check(inside.all(), '%s: %d unit corners lie outside the plane\'s outline' % (label, int((~inside).sum())))
    give = 0.006 if kind == 'brick' else 0.012
    check(units['d_min'].min() >= -0.0045, '%s: a unit reaches %.4f m behind the plane' % (label, units['d_min'].min()))
    check(units['d_max'].min() >= relief - give and units['d_max'].max() <= relief + give,
          '%s: the faces stand %.4f to %.4f m out, not within %.3f of %.3f' % (label, units['d_max'].min(), units['d_max'].max(), give, relief))
    rectangles = numpy.array(atlas_of(made)['units'])
    eps = 1e-5
    fits = ((units['u_min'][:, None] >= rectangles[None, :, 0] - eps) & (units['v_min'][:, None] >= rectangles[None, :, 1] - eps)
            & (units['u_max'][:, None] <= rectangles[None, :, 2] + eps) & (units['v_max'][:, None] <= rectangles[None, :, 3] + eps)).any(1)
    check(fits.all(), '%s: %d units have pp_atlas outside every rectangle of their atlas' % (label, int((~fits).sum())))
    return units


def check_rectangle(label, made, frame, kind):
    units = check_cover(label, made, frame, kind)
    outline = frame[4]
    joint = 0.010 if kind == 'brick' else 0.005
    s_low, s_high = min(p[0] for p in outline), max(p[0] for p in outline)
    t_low, t_high = min(p[1] for p in outline), max(p[1] for p in outline)
    height = t_high - t_low
    n = made['courses']
    if kind == 'brick':
        check(n == max(1, round(height / BRICK_RISE)), '%s: %d courses on a %.2f m plane' % (label, n, height))
        rise = height / n
        by_course = courses(units, lambda tc: int((tc - t_low) // rise))
        check(sorted(by_course) == list(range(n)), '%s: courses found %s, not 0 to %d' % (label, sorted(by_course)[:5], n - 1))
        centre_t = (units['t_min'] + units['t_max']) / 2
        for k, members in by_course.items():
            off = numpy.abs(centre_t[members] - (t_low + (k + 0.5) * rise)).max()
            check(off < 0.0015, '%s: course %d is %.4f m off its whole-course place' % (label, k, off))
    else:
        order = numpy.argsort(units['t_min'])
        bottoms, tops = numpy.round(units['t_min'], 4), numpy.round(units['t_max'], 4)
        levels = sorted(set(zip(bottoms.tolist(), tops.tolist())), key=lambda bt: bt[0])
        bands = []
        for b, t in levels:
            if bands and abs(b - bands[-1][0]) < 0.003:
                bands[-1] = (min(bands[-1][0], b), max(bands[-1][1], t))
            else:
                bands.append((b, t))
        check(len(bands) == n, '%s: %d bands of blocks for %d courses' % (label, len(bands), n))
        for (b0, t0), (b1, t1) in zip(bands[:-1], bands[1:]):
            check(b1 - t0 <= joint + 0.001, '%s: a gap of %.4f m between courses' % (label, b1 - t0))
        rise_edges = [b for b, _ in bands]
        by_course = courses(units, lambda tc: max(i for i, b in enumerate(rise_edges) if b <= tc + 1e-6))
        _ = order
    check(units['t_min'].min() <= t_low + joint + 1e-4, '%s: the bottom course starts %.4f m above the edge' % (label, units['t_min'].min() - t_low))
    check(units['t_max'].max() >= t_high - joint - 1e-4, '%s: the top course stops %.4f m below the edge' % (label, t_high - units['t_max'].max()))
    for k, members in by_course.items():
        left, right = units['s_min'][members].min(), units['s_max'][members].max()
        check(left <= s_low + joint + 1e-4 and right >= s_high - joint - 1e-4,
              '%s: course %d runs from %.4f to %.4f m, not within a joint of the edges %.3f and %.3f' % (label, k, left, right, s_low, s_high))
    return units, by_course


def widths(units, members):
    return [(units['s_min'][i], units['s_max'][i], units['s_max'][i] - units['s_min'][i]) for i in members]


MIDDLE = 0.4      # the bond is laid from both edges; the cut bricks where the two meet lie within this of the middle


def in_middle(units, i, s_low, s_high):
    return abs((units['s_min'][i] + units['s_max'][i]) / 2 - (s_low + s_high) / 2) < MIDDLE


def check_real_size(label, units, by_course, s_low, s_high):
    sizes = {0.215: 0, 0.1025: 0, 0.04625: 0}
    heights = units['t_max'] - units['t_min']
    for k, members in by_course.items():
        for i in members[2:-2]:
            if in_middle(units, i, s_low, s_high):
                continue
            w = units['s_max'][i] - units['s_min'][i]
            match = [size for size in sizes if abs(w - size) < 0.0012]
            check(match, '%s: an inner brick %.4f m long, not 215, 102.5 or 46.25 mm' % (label, w))
            sizes[match[0]] += 1
            check(abs(heights[i] - 0.065) < 0.0006, '%s: a brick %.4f m high, not 65 mm' % (label, heights[i]))
    return sizes


def check_stretcher(label, units, by_course, s_low, s_high):
    tested = 0
    for k in sorted(by_course):
        if k + 1 not in by_course:
            continue
        row, above = widths(units, by_course[k]), widths(units, by_course[k + 1])
        for (a0, a1, aw), (b0, b1, bw) in zip(row[:-1], row[1:]):
            middle = (a1 + b0) / 2
            if abs(aw - 0.215) > 0.001 or abs(bw - 0.215) > 0.001 or middle < s_low + 0.3 or middle > s_high - 0.3 \
                    or abs(middle - (s_low + s_high) / 2) < MIDDLE + 0.12:
                continue
            over = [(c0, c1) for c0, c1, cw in above if c0 <= middle <= c1]
            check(over, '%s: the joint at %.3f in course %d has a joint right above it' % (label, middle, k))
            c0, c1 = over[0]
            check(abs((c0 + c1) / 2 - middle) < 0.003, '%s: the joint at %.3f in course %d is not halfway along the brick above (%.3f)' % (label, middle, k, (c0 + c1) / 2))
            tested += 1
    check(tested >= 10, '%s: only %d joints tested' % (label, tested))
    return tested


def kind_of(width):
    return 'S' if abs(width - 0.215) < 0.0012 else ('H' if abs(width - 0.1025) < 0.0012 else '?')


def check_flemish(label, units, by_course, s_low, s_high):
    tested = 0
    middle = (s_low + s_high) / 2
    for k in sorted(by_course):
        row = widths(units, by_course[k])
        for side in ([u for u in row[2:-2] if (u[0] + u[1]) / 2 < middle - MIDDLE], [u for u in row[2:-2] if (u[0] + u[1]) / 2 > middle + MIDDLE]):
            inner = [kind_of(w) for _, _, w in side]
            check('?' not in inner, '%s: course %d has an inner brick that is neither header nor stretcher' % (label, k))
            check(all(a != b for a, b in zip(inner[:-1], inner[1:])), '%s: course %d does not alternate headers and stretchers: %s' % (label, k, ''.join(inner)))
        if k == 0:
            continue
        below = widths(units, by_course[k - 1])
        stretchers = [(c0 + c1) / 2 for c0, c1, cw in below if kind_of(cw) == 'S']
        for c0, c1, cw in row[2:-2]:
            if kind_of(cw) != 'H' or abs((c0 + c1) / 2 - middle) < MIDDLE:
                continue
            centre = (c0 + c1) / 2
            near = min(abs(centre - x) for x in stretchers)
            check(near < 0.003, '%s: the header at %.3f in course %d is %.4f m off the middle of the stretcher below' % (label, centre, k, near))
            tested += 1
    check(tested > 20, '%s: only %d headers tested' % (label, tested))
    return tested


def check_english(label, units, by_course, s_low, s_high):
    kinds = []
    middle = (s_low + s_high) / 2
    for k in sorted(by_course):
        inner = set(kind_of(w) for c0, c1, w in widths(units, by_course[k])[2:-2] if abs((c0 + c1) / 2 - middle) >= MIDDLE)
        check(len(inner) == 1 and '?' not in inner, '%s: course %d mixes %s' % (label, k, inner))
        kinds.append(inner.pop())
    check(all(a != b for a, b in zip(kinds[:-1], kinds[1:])), '%s: stretcher and header courses do not alternate: %s' % (label, ''.join(kinds[:12])))


def signature(made):
    co = numpy.empty(len(made.data.vertices) * 3)
    made.data.vertices.foreach_get('co', co)
    uv = numpy.empty(len(made.data.loops) * 2)
    made.data.uv_layers['pp_atlas'].data.foreach_get('uv', uv)
    return co, uv


FACINGS = {'-y': (90, 0, 0), '+x': (90, 0, 90), '+y': (90, 0, 180), '-x': (90, 0, 270)}


def test_bricks():
    fresh_scene()
    cases = [('1 x 1 m facing -y, stretcher', 1.0, 1.0, '-y', 'stretcher', (1.0, 1.0)),
             ('3 x 2 m facing +x, flemish', 3.0, 2.0, '+x', 'flemish', (1.0, 1.0)),
             ('2.6 x 1.7 m facing +y, english', 2.6, 1.7, '+y', 'english', (1.0, 1.0)),
             ('4 x 3 m facing -x, header', 4.0, 3.0, '-x', 'header', (1.0, 1.0)),
             ('12 x 6 m facing -y, flemish', 12.0, 6.0, '-y', 'flemish', (1.0, 1.0)),
             ('2 x 1.5 m facing +x, scale (2, 0.5) unapplied, stretcher', 1.0, 3.0, '+x', 'stretcher', (2.0, 0.5))]
    x = 0.0
    for label, w, h, facing, bond, scale in cases:
        obj = plane('plane ' + label, w, h, (x, 0.0, 3.5), FACINGS[facing], scale)
        x += 14.0
        made = lay_wall.lay(obj, kind='brick', bond=bond, seed=7)
        frame = frame_of(obj)
        check(frame[3].dot(Vector({'-y': (0, -1, 0), '+x': (1, 0, 0), '+y': (0, 1, 0), '-x': (-1, 0, 0)}[facing])) > 0.99, '%s: the test plane faces the wrong way' % label)
        units, by_course = check_rectangle(label, made, frame, 'brick')
        s_low, s_high = min(p[0] for p in frame[4]), max(p[0] for p in frame[4])
        sizes = check_real_size(label, units, by_course, s_low, s_high)
        ends = 0
        for k, members in by_course.items():          # the bond kept at both edges: the right end mirrors the left
            row = widths(units, members)
            if len(row) < 8:
                continue
            left_end = [w for _, _, w in row[:3]]
            right_end = [w for _, _, w in row[-3:]][::-1]
            check(all(abs(a - b) < 0.0012 for a, b in zip(left_end, right_end)),
                  '%s: course %d ends %s at the left but %s at the right' % (label, k, ['%.4f' % w for w in left_end], ['%.4f' % w for w in right_end]))
            ends += 1
        extra = ', the bond kept at both edges in %d courses' % ends if ends else ''
        if bond == 'stretcher' and w * scale[0] >= 1.9:
            extra += ', %d joints halfway along the bricks above' % check_stretcher(label, units, by_course, s_low, s_high)
        if bond == 'flemish':
            extra += ', %d headers centred on the stretchers below' % check_flemish(label, units, by_course, s_low, s_high)
        if bond == 'english':
            check_english(label, units, by_course, s_low, s_high)
            extra += ', stretcher and header courses alternate'
        print('PASS lay_wall brick, %s: %d bricks in %d whole courses, all inside, within a joint of every edge; real size (%d stretchers, %d headers, %d closers inside); relief and pp_atlas good%s'
              % (label, made['units'], made['courses'], sizes[0.215], sizes[0.1025], sizes[0.04625], extra))


def test_lying_and_turned():
    fresh_scene()
    floor = plane('floor', 3.0, 2.0, (0.0, 0.0, 0.0), (0, 0, 30))
    made = lay_wall.lay(floor, kind='brick', bond='stretcher', seed=2)
    frame = frame_of(floor)
    check(abs(frame[1].dot(Vector((math.cos(math.radians(30)), math.sin(math.radians(30)), 0.0)))) > 0.999, 'the floor frame is not along its own X')
    units, by_course = check_rectangle('3 x 2 m lying flat, turned 30 degrees', made, frame, 'brick')
    s_low, s_high = min(p[0] for p in frame[4]), max(p[0] for p in frame[4])
    check_real_size('lying flat', units, by_course, s_low, s_high)
    tested = check_stretcher('lying flat', units, by_course, s_low, s_high)
    print('PASS lay_wall lying flat (3 x 2 m, turned 30 degrees, scale unapplied): %d bricks, courses along the plane\'s own X, whole, inside, to every edge; %d joints halfway' % (made['units'], tested))
    stone_floor = plane('stone floor', 2.4, 1.6, (6.0, 0.0, 0.0), (0, 0, -20))
    made = lay_wall.lay(stone_floor, kind='stone', seed=4)
    check_rectangle('stone lying flat', made, frame_of(stone_floor), 'stone')
    print('PASS lay_wall stone lying flat: %d blocks in %d courses, inside, to every edge' % (made['units'], made['courses']))
    # a standing plane turned within itself: its edges slope, the courses stay level and are cut along its outline
    rolled = plane('rolled', 2.0, 1.5, (12.0, 0.0, 2.0), (90, 25, 0))
    made = lay_wall.lay(rolled, kind='brick', bond='flemish', seed=5)
    frame = frame_of(rolled)
    units = check_cover('a standing plane turned 25 degrees in itself', made, frame, 'brick')
    heights = units['t_max'] - units['t_min']
    check(numpy.median(heights) > 0.06, 'the turned plane\'s bricks are not level courses')
    print('PASS lay_wall on a standing plane turned 25 degrees within itself: %d bricks in level courses, every one inside its sloping outline' % made['units'])


def test_gable():
    fresh_scene()
    mesh = bpy.data.meshes.new('gable')
    mesh.from_pydata([(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (2.5, 0.0, 2.4)], [], [(0, 1, 2)])
    gable = bpy.data.objects.new('gable', mesh)
    bpy.context.scene.collection.objects.link(gable)
    for kind in ('brick', 'stone'):
        made = lay_wall.lay(gable, kind=kind, bond='english', seed=3)
        frame = frame_of(gable)
        units = check_cover('gable (%s)' % kind, made, frame, kind)
        # the courses follow the slopes: each course reaches within a brick of the slope at its top
        outline = frame[4]
        t_low = min(p[1] for p in outline)
        apex = max(p[1] for p in outline)
        centre_t = (units['t_min'] + units['t_max']) / 2
        reach = []
        for level in numpy.linspace(t_low + 0.3, apex - 0.5, 6):
            members = numpy.nonzero(numpy.abs(centre_t - level) < 0.04)[0]
            if len(members) == 0:
                continue
            top = units['t_max'][members].max()
            half = 2.5 * (apex - top) / (apex - t_low)                       # the gable's half width at that height
            mid = (min(p[0] for p in outline) + max(p[0] for p in outline)) / 2
            reach.append(max(units['s_min'][members].min() - (mid - half), (mid + half) - units['s_max'][members].max()))
        check(reach and max(reach) < 0.03, 'gable (%s): the courses stop %.3f m short of the slopes' % (kind, max(reach) if reach else -1))
        print('PASS lay_wall on a gable (%s): %d units, every one inside the triangle, cut along its slopes (each course reaches the slope at its top line, and %.2f m past it lower down)' % (kind, made['units'], -max(reach)))


def test_stone():
    fresh_scene()
    cases = [('1 x 1 m facing +x', 1.0, 1.0, '+x'), ('12 x 6 m facing -y', 12.0, 6.0, '-y'), ('3 x 2.2 m facing -x', 3.0, 2.2, '-x'), ('2 x 1.3 m facing +y', 2.0, 1.3, '+y')]
    x = 0.0
    for label, w, h, facing in cases:
        obj = plane('stone ' + label, w, h, (x, 0.0, 3.5), FACINGS[facing])
        x += 14.0
        made = lay_wall.lay(obj, kind='stone', seed=11)
        units, by_course = check_rectangle('stone ' + label, made, frame_of(obj), 'stone')
        lengths = units['s_max'] - units['s_min']
        print('PASS lay_wall stone, %s: %d blocks in %d whole courses (%.2f to %.2f m tall), inside, within a joint of every edge, lengths %.2f to %.2f m'
              % (label, made['units'], made['courses'], (units['t_max'] - units['t_min']).min(), (units['t_max'] - units['t_min']).max(), lengths.min(), lengths.max()))


def test_seed_options_help():
    fresh_scene()
    a = plane('a', 2.0, 1.5, (0.0, 0.0, 1.0), FACINGS['-y'])
    b = plane('b', 2.0, 1.5, (0.0, 0.0, 1.0), FACINGS['-y'])
    first = signature(lay_wall.lay(a, kind='brick', bond='flemish', seed=9))
    second = signature(lay_wall.lay(b, kind='brick', bond='flemish', seed=9))
    check(first[0].shape == second[0].shape and numpy.abs(first[0] - second[0]).max() < 1e-7 and numpy.abs(first[1] - second[1]).max() < 1e-7,
          'the same seed laid a different wall')
    third = signature(lay_wall.lay(plane('c', 2.0, 1.5, (0.0, 0.0, 1.0), FACINGS['-y']), kind='brick', bond='flemish', seed=10))
    check(first[1].shape != third[1].shape or numpy.abs(first[1] - third[1]).max() > 1e-3, 'another seed laid the same wall')
    s1 = signature(lay_wall.lay(plane('d', 2.0, 1.5, (0.0, 0.0, 1.0), FACINGS['-y']), kind='stone', seed=9))
    s2 = signature(lay_wall.lay(plane('e', 2.0, 1.5, (0.0, 0.0, 1.0), FACINGS['-y']), kind='stone', seed=9))
    check(s1[0].shape == s2[0].shape and numpy.abs(s1[0] - s2[0]).max() < 1e-7, 'the same seed laid a different stone wall')
    print('PASS lay_wall: the same seed lays the same wall (brick and stone), another seed another')
    bpy.ops.object.empty_add()
    empty = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cube = bpy.context.object
    refused = 0
    for label, call in (("kind='wood'", lambda: lay_wall.lay(a, kind='wood')), ("bond='rat trap'", lambda: lay_wall.lay(a, bond='rat trap')),
                        ('wear=5', lambda: lay_wall.lay(a, wear=5)), ('course=0', lambda: lay_wall.lay(a, kind='stone', course=0)),
                        ('relief=1', lambda: lay_wall.lay(a, relief=1.0)), ('an option it does not have', lambda: lay_wall.lay(a, colour='red')),
                        ('an empty', lambda: lay_wall.lay(empty)), ('a cube (not one flat plane)', lambda: lay_wall.lay(cube)),
                        ("atlas='no such set'", lambda: lay_wall.lay(a, atlas='no such set'))):
        try:
            call()
        except (ValueError, TypeError):
            refused += 1
            continue
        check(False, 'lay_wall accepted %s' % label)
    print('PASS lay_wall refuses wrong options (%d cases)' % refused)
    result = subprocess.run([sys.executable, os.path.join(TOOLS, 'lay_wall.py'), '--help'], capture_output=True, text=True, timeout=120)
    check(result.returncode == 0 and 'usage' in result.stdout.lower(), 'lay_wall --help failed: %s' % (result.stderr or result.stdout)[-300:])
    check(all(k in lay_wall.TOOL for k in ('name', 'what', 'call', 'options', 'materials', 'source', 'trap')), 'lay_wall.TOOL lacks a key')
    print('PASS lay_wall answers --help and describes itself in TOOL')


def test_flip_and_materials():
    fresh_scene()
    import store
    wall = plane('flip', 2.0, 1.2, (0.0, 0.0, 1.0), FACINGS['-y'])
    made = lay_wall.lay(wall, kind='brick', seed=1, flip=True)
    frame = frame_of(wall)
    units = units_of(made, frame)
    check(units['d_max'].max() < 0.005 and units['d_min'].min() < -0.006, 'flip=True did not lay the bricks on the back of the plane')
    print('PASS lay_wall flip=True lays the units on the side the plane looks away from')
    names = store.names('materials')
    for kind in ('brick', 'stone'):
        made = lay_wall.lay(plane('m ' + kind, 1.5, 1.0, (4.0, 0.0, 1.0), FACINGS['-y']), kind=kind, seed=1)
        atlas = atlas_of(made)
        used = made.data.materials[0].name
        if atlas.get('material') in names:
            check(used == atlas['material'], '%s units are in %r, not their atlas\'s %r' % (kind, used, atlas['material']))
        else:
            check('stand-in' in used, '%s units are in %r without the atlas material in the store' % (kind, used))
        print('PASS lay_wall %s: the units are in %r (atlas %s)' % (kind, used, made['atlas']))
    mortar = wall.data.materials[0].name if len(wall.data.materials) else None
    wanted = next((m for m in lay_wall.MORTAR_MATERIALS if m in names), None)
    check(mortar == wanted, 'the plane is in %r, not the mortar %r' % (mortar, wanted))
    print('PASS lay_wall: the plane becomes the mortar %r' % mortar)


def test_lay_stone_photographed():
    fresh_scene()
    import lay_stone
    import store
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 1.4))
    wall = bpy.context.object
    wall.scale = (3.0, 0.5, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    stonework = lay_stone.lay(wall, openings=[('front', 'door', 0.3, 0.0, 0.9, 2.0), ('front', 'window', 1.7, 1.0, 0.8, 1.0)], seed=2)
    attribute = stonework.data.attributes.get('pp_piece')
    check(attribute is not None and attribute.domain == 'FACE' and attribute.data_type == 'FLOAT', 'lay_stone\'s blocks carry no pp_piece on their faces')
    pieces = numpy.empty(len(stonework.data.polygons))
    attribute.data.foreach_get('value', pieces)
    totals = numpy.empty(len(stonework.data.polygons), dtype=numpy.int64)
    stonework.data.polygons.foreach_get('loop_total', totals)
    loop_vertex = numpy.empty(len(stonework.data.loops), dtype=numpy.int64)
    stonework.data.loops.foreach_get('vertex_index', loop_vertex)
    per_loop = numpy.repeat(pieces, totals)
    low = numpy.full(len(stonework.data.vertices), 2.0)
    high = numpy.full(len(stonework.data.vertices), -1.0)
    numpy.minimum.at(low, loop_vertex, per_loop)
    numpy.maximum.at(high, loop_vertex, per_loop)
    check(numpy.abs(high - low).max() < 1e-9, 'a lay_stone block (its faces joined at its corners) carries more than one pp_piece')
    check(len(set(pieces.tolist())) >= stonework['blocks'], 'lay_stone: %d pp_piece numbers for %d blocks' % (len(set(pieces.tolist())), stonework['blocks']))
    check(pieces.min() >= 0.0 and pieces.max() <= 1.0, 'lay_stone pp_piece outside 0 to 1')
    used = [m.name for m in stonework.data.materials]
    if lay_stone.PHOTO_STONE in store.names('materials'):
        check(used[0] == lay_stone.PHOTO_STONE and used[1] == lay_stone.PHOTO_STONE, 'lay_stone\'s blocks and dressings are in %s, not the photographed %r' % (used[:2], lay_stone.PHOTO_STONE))
    print('PASS lay_stone: %d blocks, each block and dressing its own pp_piece (%d numbers); blocks and dressings in %r'
          % (stonework['blocks'], len(set(pieces.tolist())), used[0]))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.0, 0.0, 1.4))
    old = bpy.context.object
    old.scale = (3.0, 0.5, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    painted = lay_stone.lay(old, seed=2, shades=lay_stone.SHADES, trim_material=lay_stone.TRIM_MATERIAL)
    used = [m.name for m in painted.data.materials]
    check(used[:12] == lay_stone.SHADES and used[12] == lay_stone.TRIM_MATERIAL, 'the old painted materials are not used when asked: %s' % used[:3])
    print('PASS lay_stone: the old painted sandstone still works by name (shades=lay_stone.SHADES, trim_material=lay_stone.TRIM_MATERIAL)')


def test_hole():
    fresh_scene()
    outer = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4), (0.0, 2.4)]
    hole = [(1.1, 0.75), (1.9, 0.75), (1.9, 1.85), (1.1, 1.85)]
    verts = [(x, 0.0, z) for x, z in outer + hole]
    mesh = bpy.data.meshes.new('wall with a window')
    mesh.from_pydata(verts, [], [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    wall = bpy.data.objects.new('wall with a window', mesh)
    bpy.context.scene.collection.objects.link(wall)
    made = lay_wall.lay(wall, kind='brick', bond='english', seed=6)
    frame = frame_of(wall)
    check(frame[3].dot(Vector((0.0, -1.0, 0.0))) > 0.99, 'the test wall faces the wrong way')
    units = units_of(made, frame)
    origin, along, up = frame[0], frame[1], frame[2]
    hole_st = [((Vector((x, 0.0, z)) - origin).dot(along), (Vector((x, 0.0, z)) - origin).dot(up)) for x, z in hole]
    h_s0, h_s1 = min(p[0] for p in hole_st), max(p[0] for p in hole_st)
    h_t0, h_t1 = min(p[1] for p in hole_st), max(p[1] for p in hole_st)
    s, t = units['all_s'], units['all_t']
    in_hole = (s > h_s0 + 0.001) & (s < h_s1 - 0.001) & (t > h_t0 + 0.001) & (t < h_t1 - 0.001)
    check(not in_hole.any(), 'the wall laid %d unit corners inside the window hole' % int(in_hole.sum()))
    beside = numpy.nonzero((units['t_min'] > h_t0 + 0.08) & (units['t_max'] < h_t1 - 0.08))[0]
    left = units['s_max'][beside][units['s_max'][beside] < h_s0 + 0.001]
    right = units['s_min'][beside][units['s_min'][beside] > h_s1 - 0.001]
    check(len(left) and len(right), 'no courses beside the window')
    rows = len(set(numpy.round(units['t_min'][beside], 3).tolist()))
    check(numpy.sort(left)[-rows:].min() >= h_s0 - 0.010 - 1e-4 and numpy.sort(right)[:rows].max() <= h_s1 + 0.010 + 1e-4,
          'the courses beside the window stop more than a joint from its sides')
    over = numpy.nonzero(((units['s_min'] + units['s_max']) / 2 > h_s0) & ((units['s_min'] + units['s_max']) / 2 < h_s1))[0]
    above = units['t_min'][over][units['t_min'][over] >= h_t1 - 0.001]
    below = units['t_max'][over][units['t_max'][over] <= h_t0 + 0.001]
    # over and under the hole the units are cut in height; a piece thinner than 2 cm (4 cm of stone) is left out as mortar
    check(len(above) and above.min() <= h_t1 + 0.010 + 0.020 + 1e-4, 'the bricks over the window start %.4f m above its top' % ((above.min() - h_t1) if len(above) else -1))
    check(len(below) and below.max() >= h_t0 - 0.010 - 0.020 - 1e-4, 'the bricks under the window stop %.4f m below its foot' % ((h_t0 - below.max()) if len(below) else -1))
    print('PASS lay_wall on a wall with a window hole: %d bricks, none in the hole, the %d courses beside it reach within a joint of its sides, the bricks over and under it within %.3f and %.3f m of its top and foot'
          % (made['units'], rows, above.min() - h_t1, h_t0 - below.max()))
    stone_wall = bpy.data.objects.new('stone wall with a window', mesh.copy())
    bpy.context.scene.collection.objects.link(stone_wall)
    stone_wall.location.x = 5.0
    bpy.context.view_layer.update()
    made = lay_wall.lay(stone_wall, kind='stone', seed=6)
    frame = frame_of(stone_wall)
    units = units_of(made, frame)
    origin, along, up = frame[0], frame[1], frame[2]
    hole_st = [((Vector((x + 5.0, 0.0, z)) - origin).dot(along), (Vector((x + 5.0, 0.0, z)) - origin).dot(up)) for x, z in hole]
    h_s0, h_s1 = min(p[0] for p in hole_st), max(p[0] for p in hole_st)
    h_t0, h_t1 = min(p[1] for p in hole_st), max(p[1] for p in hole_st)
    s, t = units['all_s'], units['all_t']
    in_hole = (s > h_s0 + 0.001) & (s < h_s1 - 0.001) & (t > h_t0 + 0.001) & (t < h_t1 - 0.001)
    check(not in_hole.any(), 'the stone wall laid %d block corners inside the window hole' % int(in_hole.sum()))
    over = numpy.nonzero(((units['s_min'] + units['s_max']) / 2 > h_s0) & ((units['s_min'] + units['s_max']) / 2 < h_s1))[0]
    above = units['t_min'][over][units['t_min'][over] >= h_t1 - 0.001]
    below = units['t_max'][over][units['t_max'][over] <= h_t0 + 0.001]
    check(len(above) and above.min() <= h_t1 + 0.005 + 0.040 + 1e-4 and len(below) and below.max() >= h_t0 - 0.005 - 0.040 - 1e-4,
          'the blocks over and under the window do not reach its top and foot')
    print('PASS lay_wall stone on a wall with a window hole: %d blocks, none in the hole, cut in height to within %.3f and %.3f m of its top and foot'
          % (made['units'], above.min() - h_t1, h_t0 - below.max()))


def main():
    test_bricks()
    test_lying_and_turned()
    test_gable()
    test_hole()
    test_stone()
    test_seed_options_help()
    test_flip_and_materials()
    test_lay_stone_photographed()
    print('PASS test_store_wall')


if __name__ == '__main__':
    main()
