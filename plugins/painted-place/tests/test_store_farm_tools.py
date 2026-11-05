"""
What this file does: checks the farm tools the barn builders' sets brought to the store (log 54) against what their
notes claim. The dry-stone wall: its stones lie along its line and nowhere else, none in a gateway, its coping at the
height asked, its foot on the ground's own height, the same seed the same wall, wrong options refused. The hedge: its
sprays lie in a strip along its line, none in a gap, its top uneven, its live copies drawn, the same seed the same
hedge. The rubble face: only on the side asked, in relief in front of it, openings clear with jamb stones beside them,
rising with a lean-to's slope and never above it. The litter tool's straw: laid only when asked, only where asked, its
strands not fanned out from one point, pressed flat where trodden, every strand lying on the ground. Moss: a new mossy
material, the old one as it was. The clearing tool: takes away only the points inside the footprint, of the scatterings
it was given, keeping every other point and its numbers. lay_boards' hollow box: open through its doorway into a dark
inside, and the default box unchanged. All of them answer --help.
    python3 tests/test_store_farm_tools.py
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import store  # noqa: E402
import ground  # noqa: E402
import _lines  # noqa: E402


def world_points(obj):
    co = numpy.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    matrix = numpy.array(obj.matrix_world)
    return co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def along_across(line, xy):
    path = _lines.Path([Vector((p[0], p[1], 0.0)) for p in line])
    fine = _lines.Path([path.at(d) for d in numpy.linspace(0.0, path.total, int(path.total / 0.02) + 2)])
    along, across, _ahead = fine.project(xy)
    return along, across, path.total


def refused(call, error=ValueError):
    try:
        call()
    except error:
        return True
    return False


def heights(yard, xy):
    return numpy.array([ground.height_at(yard, x, y) for x, y in xy])


# ------------------------------------------------------------------------------------------------ the dry-stone wall

def test_dry_wall():
    import dry_wall
    fresh_scene()
    yard = ground.make(size=(14.0, 8.0), location=(0.0, 2.0, 0.0), relief=0.06, seed=3)
    line = [(-5.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 4.0, 0.0)]
    made = dry_wall.lay(line, height=1.25, base=0.62, top=0.42, gaps=[(3.0, 4.5)], ground=yard, smooth=False, seed=2)
    check(sorted(made) == ['coping', 'core', 'stones'], 'the wall made %s' % sorted(made))
    stones_points = world_points(made['stones'])
    copes = world_points(made['coping'])
    check(made['stones']['stones'] == len(stones_points) // 13 and made['stones']['stones'] > 300,
          'the wall has %d stones for %d points' % (made['stones']['stones'], len(stones_points)))
    check(made['coping']['copes'] == len(copes) // 8 and made['coping']['copes'] > 40, '%d coping stones' % made['coping']['copes'])
    every = numpy.concatenate([stones_points, copes, world_points(made['core'])])
    along, across, total = along_across(line, every[:, :2])
    away = numpy.abs(along - 7.0) > 0.6                               # off the corner, where the outer corner stands half x 1.41 out
    check(numpy.abs(across[away]).max() < 0.31 + 0.08, 'a stone lies %.2f m from the wall\'s line (half the base is 0.31)' % numpy.abs(across[away]).max())
    check(numpy.abs(across).max() < 0.31 * math.sqrt(2.0) + 0.08, 'a stone lies %.2f m from the wall\'s corner' % numpy.abs(across).max())
    check(along.min() > -0.05 and along.max() < total + 0.05, 'a stone lies past the line\'s ends (%.2f to %.2f of %.2f m)' % (along.min(), along.max(), total))
    in_gap = (along > 3.0 + 0.02) & (along < 4.5 - 0.02)
    check(not in_gap.any(), '%d stone points lie in the gateway asked for (3.0 to 4.5 m)' % in_gap.sum())
    for u in (2.6, 4.9):                                              # the wall comes right up to the gateway on both sides
        check((numpy.abs(along - u) < 0.2).sum() > 20, 'the wall stops short of the gateway near %.1f m' % u)
    # the coping's top at the height asked, above the ground under it
    slabs = copes.reshape(-1, 8, 3)
    centres = slabs.mean(axis=1)
    tops = slabs[:, :, 2].max(axis=1) - heights(yard, centres[:, :2])
    check(abs(numpy.median(tops) - 1.25) < 0.08 and tops.max() < 1.25 + 0.25,
          'the coping stands %.2f m (median) to %.2f m above the ground, not about 1.25' % (numpy.median(tops), tops.max()))
    # the foot follows the ground: in each half metre along, the lowest stone is sunk about 4 cm under the ground there
    along_stones, _, _ = along_across(line, stones_points[:, :2])
    feet = []
    for u in list(numpy.arange(0.3, 2.7, 0.5)) + list(numpy.arange(5.0, 10.5, 0.5)):
        near = numpy.abs(along_stones - u) < 0.25
        lowest = stones_points[near][numpy.argmin(stones_points[near, 2])]
        feet.append(lowest[2] - ground.height_at(yard, lowest[0], lowest[1]))
    feet = numpy.array(feet)
    check(numpy.abs(feet + 0.04).max() < 0.035, 'the wall\'s foot does not follow the ground: lowest stones %.3f to %.3f m from it' % (feet.min(), feet.max()))
    corner_stones = labels(made['stones'], 'stone_face') == 5
    check(corner_stones.sum() >= 6, 'the corner has too few corner stones (%d)' % corner_stones.sum())
    again = dry_wall.lay(line, height=1.25, gaps=[(3.0, 4.5)], ground=yard, smooth=False, seed=2)
    check(numpy.allclose(world_points(again['stones']), stones_points), 'the same seed laid a different wall')
    other = dry_wall.lay(line, height=1.25, gaps=[(3.0, 4.5)], ground=yard, smooth=False, seed=3)
    check(len(world_points(other['stones'])) != len(stones_points) or not numpy.allclose(world_points(other['stones']), stones_points),
          'another seed laid the same wall')
    flat = dry_wall.lay([(0.0, 10.0, 0.3), (3.0, 10.0, 0.3)], seed=1)                 # no ground: the line's own height
    check(abs(world_points(flat['stones'])[:, 2].min() - (0.3 - 0.04)) < 0.03, 'without a ground the wall does not stand on the line\'s height')
    for wrong in ({'top': 0.8}, {'height': 0.0}, {'gaps': [(10.0, 14.0)]}, {'gaps': [(1.0, 2.0), (1.5, 2.5)]}, {'coping': 1.2},
                  {'gaps': [(0.0, 11.0)]}):
        check(refused(lambda: dry_wall.lay(line, smooth=False, **wrong)), 'the wall accepted %s' % wrong)
    check(refused(lambda: dry_wall.lay(line, hieght=1.0), TypeError), 'a misspelt option was accepted')
    print('PASS dry_wall: %d stones and %d copes along 11 m with a square corner (%d corner stones), all within the wall\'s width '
          'of its line, none in the gateway; coping %.2f m above the ground; the foot %.3f m under the ground everywhere; same seed, '
          'same wall; wrong options refused' % (made['stones']['stones'], made['coping']['copes'], corner_stones.sum() // 1, numpy.median(tops), feet.mean()))


def labels(obj, name):
    """A whole-number label per stone (each stone is 13 points and 9 faces; the label is on its faces)."""
    values = numpy.zeros(len(obj.data.polygons), dtype=numpy.int64)
    data = numpy.zeros(len(obj.data.polygons), dtype=numpy.int32)
    obj.data.attributes[name].data.foreach_get('value', data)
    values[:] = data
    return values[::9]


def s_bend(name='wall curve'):
    """A Bezier S-bend: straight, a left bend of about 120 degrees, a right bend of about 120 degrees, straight."""
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 24
    spline = data.splines.new('BEZIER')
    points = [(-5.0, -4.0), (-2.0, -4.0), (0.6, -2.5), (0.6, 0.5), (0.6, 3.5), (3.2, 5.0), (5.5, 5.0)]
    spline.bezier_points.add(len(points) - 1)
    for point, (x, y) in zip(spline.bezier_points, points):
        point.co = (x, y, 0.0)
        point.handle_left_type = point.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    return obj


def sloping_ground():
    yard = ground.make(size=(16.0, 14.0), location=(0.0, 0.5, 0.0), relief=0.04, seed=4)
    world = ground.world_points(yard)
    ground.set_world_heights(yard, world[:, 2] + 0.1 * world[:, 1])        # climbing 1 in 10 towards +y
    return yard


def test_dry_wall_curve():
    """Along a curve object that turns through more than 180 degrees and climbs a slope: both faces follow the curve,
    no gap opens between the stones on the outside of a bend and none pile up on its inside."""
    import dry_wall
    fresh_scene()
    yard = sloping_ground()
    curve = s_bend()
    line = dry_wall.Line(curve)
    turning = sum(abs(angle) for _, angle in line.turns())
    check(turning > 180.0, 'the S-bend turns through only %.0f degrees' % turning)
    check(max(abs(angle) for _, angle in line.turns()) < dry_wall.CORNER, 'the smooth curve was built with corners')
    made = dry_wall.lay(curve, ground=yard, seed=7)
    stones = made['stones']
    points = world_points(stones).reshape(-1, 13, 3)
    face_kind = labels(stones, 'stone_face')
    course = labels(stones, 'stone_course')
    centre = numpy.array([tuple(p) for p in line.path.points])
    fine = _lines.Path([Vector((p[0], p[1], 0.0)) for p in centre])
    middles = points[:, 4, :]                                            # the middle of each stone's face
    along, across, ahead = fine.project(middles[:, :2])
    for side in (1, -1):
        mine = face_kind == side
        check(mine.sum() > 300, 'too few stones on the %s face (%d)' % ('left' if side > 0 else 'right', mine.sum()))
        offset = across[mine] * side
        check(offset.min() > 0.12 and offset.max() < 0.38, 'a stone of the %s face lies %.2f to %.2f m from the curve (its half width is 0.21 to 0.31)'
              % ('left' if side > 0 else 'right', offset.min(), offset.max()))
        covered = numpy.histogram(along[mine], bins=numpy.arange(0.0, line.total + 0.5, 0.5))[0]
        check((covered[1:-1] > 0).all(), 'the %s face has a bare stretch along the curve' % ('left' if side > 0 else 'right'))
    # the gaps between neighbouring stones of a course, measured on the face from one stone's end to the next one's
    lengths = numpy.array(line.lengths[:len(line.points)])
    turn = numpy.unwrap([math.atan2(line.tangent(u).y, line.tangent(u).x) for u in lengths])
    bends = numpy.interp(along, lengths, numpy.gradient(turn, lengths))   # 1 / radius, left positive
    outside, inside = [], []
    through = max(set(course[face_kind == 3].tolist()) or {-1}, key=lambda c: c)
    for k in sorted(set(course[(face_kind == 1) | (face_kind == -1)].tolist())):
        if k == through:
            continue
        for side in (1, -1):
            chosen = numpy.flatnonzero((face_kind == side) & (course == k))
            chosen = chosen[numpy.argsort(along[chosen])]
            for a, b in zip(chosen, chosen[1:]):
                way = points[a, 5] - points[a, 3]
                way /= max(numpy.linalg.norm(way), 1e-9)
                gap = float((points[b, 3] - points[a, 5]) @ way)
                bend = bends[a] * side                                       # > 0: this face is on the inside of the bend
                if abs(bends[a]) > 1.0 / 6.0:
                    (inside if bend > 0 else outside).append(gap)
                check(-0.035 < gap < 0.065, 'stones %s on the %s face: a gap of %.3f m between neighbours (course %d)'
                      % ('pile up' if gap < 0 else 'gap', 'left' if side > 0 else 'right', gap, k))
    outside, inside = numpy.array(outside), numpy.array(inside)
    check(len(outside) > 50 and len(inside) > 50, 'too few stones on the bends to judge (%d outside, %d inside)' % (len(outside), len(inside)))
    check(abs(outside.mean() - inside.mean()) < 0.012, 'round the bends the stones gap %.3f m on the outside against %.3f m on the inside'
          % (outside.mean(), inside.mean()))
    # climbing the slope: the foot on the ground all along, the coping at the height asked above it
    every = world_points(stones)
    along_all, _, _ = fine.project(every[:, :2])
    feet = []
    for u in numpy.arange(0.5, line.total - 0.5, 0.75):
        near = numpy.abs(along_all - u) < 0.3
        lowest = every[near][numpy.argmin(every[near, 2])]
        feet.append(lowest[2] - ground.height_at(yard, lowest[0], lowest[1]))
    feet = numpy.array(feet)
    check(feet.max() < 0.0 and feet.min() > -0.1, 'on the slope the foot strays from the ground: %.3f to %.3f m (sunk 0 to 10 cm expected)' % (feet.min(), feet.max()))
    copes = world_points(made['coping']).reshape(-1, 8, 3)
    tops = copes[:, :, 2].max(axis=1) - heights(yard, copes.mean(axis=1)[:, :2])
    check(abs(numpy.median(tops) - 1.25) < 0.08, 'on the slope the coping stands %.2f m above the ground' % numpy.median(tops))
    climb = every[along_all > line.total - 1.0, 2].min() - every[along_all < 1.0, 2].min()
    check(climb > 0.7, 'the wall does not climb the slope (its foot rises %.2f m from one end to the other; the ground about 0.9)' % climb)
    print('PASS dry_wall on a curve: along a Bezier S-bend turning %.0f degrees and climbing 1 in 10, both faces follow it (%d and %d '
          'stones); round the bends the gaps between stones are %.3f m on the outside and %.3f m on the inside, none open, none piled up; '
          'the foot on the ground, the coping %.2f m above it' % (turning, (face_kind == 1).sum(), (face_kind == -1).sum(), outside.mean(),
                                                                inside.mean(), numpy.median(tops)))


# ------------------------------------------------------------------------------------------------ the hedge

def test_hedge():
    import hedge
    fresh_scene()
    yard = ground.make(size=(13.0, 6.0), location=(0.0, 1.0, 0.0), relief=0.06, seed=3)
    line = [(-5.5, 1.0, 0.0), (1.0, 1.4, 0.0), (5.5, 0.6, 0.0)]
    made = hedge.lay(line, height=1.6, width=1.1, gaps=[(5.0, 6.6)], ground=yard, seed=4)
    check(sorted(made) == ['core', 'sprays', 'twigs'], 'the hedge made %s' % sorted(made))
    sprays = made['sprays']
    points = world_points(sprays)
    check(sprays['sprays'] == len(points) and len(points) > 1500, 'the hedge has %d sprays (%d points)' % (sprays['sprays'], len(points)))
    along, across, total = along_across(line, points[:, :2])
    check(numpy.abs(across).max() < 1.1 / 2 * 1.35 + 0.15, 'a spray lies %.2f m from the hedge\'s line' % numpy.abs(across).max())
    check(along.min() >= -0.01 and along.max() <= total + 0.01, 'a spray lies past the line\'s ends')
    in_gap = (along > 5.0 + 0.02) & (along < 6.6 - 0.02)
    check(not in_gap.any(), '%d sprays grow in the gap asked for (5.0 to 6.6 m)' % in_gap.sum())
    above = points[:, 2] - heights(yard, points[:, :2])
    tops = []
    for u in numpy.arange(0.25, total - 0.25, 0.5):
        near = (numpy.abs(along - u) < 0.25)
        if near.sum() > 10 and not (4.5 < u < 7.1):
            tops.append(numpy.percentile(above[near], 98))
    tops = numpy.array(tops)
    check(abs(numpy.median(tops) - 1.6) < 0.35, 'the hedge stands %.2f m tall (median of its top), not about 1.6' % numpy.median(tops))
    check(tops.max() - tops.min() > 0.12 and tops.std() > 0.03, 'the hedge\'s top is too even (%.2f to %.2f m)' % (tops.min(), tops.max()))
    check(above.min() > -0.2, 'sprays sink %.2f m into the ground' % above.min())
    depsgraph = bpy.context.evaluated_depsgraph_get()
    drawn = sum(1 for i in depsgraph.object_instances if i.is_instance and i.parent is not None and i.parent.original == sprays)
    check(drawn == len(points), '%d live copies drawn for %d sprays' % (drawn, len(points)))
    check(len(made['twigs'].data.polygons) > 500 and len(made['core'].data.polygons) > 20, 'no twigs or no core')
    for name in ('hedge_tone', 'hedge_dry', 'hedge_inner'):
        values = numpy.zeros(len(points))
        sprays.data.attributes[name].data.foreach_get('value', values)
        check(values.min() >= 0.0 and values.max() <= 1.0 and values.max() - values.min() > 0.3, '%s runs %.2f to %.2f' % (name, values.min(), values.max()))
    again = hedge.lay(line, height=1.6, width=1.1, gaps=[(5.0, 6.6)], ground=yard, seed=4)
    check(numpy.allclose(world_points(again['sprays']), points), 'the same seed grew a different hedge')
    for wrong in ({'raggedness': 3.0}, {'width': 0.0}, {'amount': 0.0}, {'gaps': [(-1.0, 2.0)]}, {'dry': 2.0}):
        check(refused(lambda: hedge.lay(line, **wrong)), 'the hedge accepted %s' % wrong)
    print('PASS hedge: %d sprays in a strip along the line, none in the gap; its top %.2f to %.2f m, uneven; every spray drawn; '
          'same seed, same hedge; wrong options refused' % (len(points), tops.min(), tops.max()))


def test_hedge_curve():
    """Along the same S-bend: the hedge follows it, as thick on the outside of each bend as on its inside."""
    import dry_wall
    import hedge
    fresh_scene()
    yard = sloping_ground()
    curve = s_bend('hedge curve')
    made = hedge.lay(curve, ground=yard, seed=5)
    points = world_points(made['sprays'])
    line = dry_wall.Line(curve)
    fine = _lines.Path([Vector((p.x, p.y, 0.0)) for p in line.path.points])
    along, across, _ = fine.project(points[:, :2])
    check(numpy.abs(across).max() < 1.1 / 2 * 1.35 + 0.15, 'a spray lies %.2f m from the curve' % numpy.abs(across).max())
    lengths = line.lengths[:len(line.points)]
    turn = numpy.unwrap([math.atan2(line.tangent(u)[1], line.tangent(u)[0]) for u in lengths])
    bend = numpy.interp(along, lengths, numpy.gradient(turn, lengths))
    sharp = numpy.abs(bend) > 1.0 / 5.0
    inside = sharp & (numpy.sign(across) == numpy.sign(bend))
    outside = sharp & (numpy.sign(across) == -numpy.sign(bend))
    # per metre of each side's own face (0.45 m out from the curve's middle), round the bends
    reach = 0.45
    inside_length = numpy.sum(numpy.where(numpy.abs(numpy.interp(lengths, lengths, numpy.gradient(turn, lengths))) > 1.0 / 5.0,
                                          1.0 - numpy.abs(numpy.gradient(turn, lengths)) * reach, 0.0) * numpy.gradient(lengths))
    outside_length = numpy.sum(numpy.where(numpy.abs(numpy.gradient(turn, lengths)) > 1.0 / 5.0,
                                           1.0 + numpy.abs(numpy.gradient(turn, lengths)) * reach, 0.0) * numpy.gradient(lengths))
    ratio = (outside.sum() / outside_length) / max(inside.sum() / inside_length, 1e-9)
    check(0.75 < ratio < 1.33, 'round the bends the hedge is %.2f times as thick on the outside as on the inside' % ratio)
    print('PASS hedge on a curve: it follows the S-bend; round the bends it is %.2f times as thick on the outside as on the inside' % ratio)


# ------------------------------------------------------------------------------------------------ the rubble face

def box(name, size, location):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def test_rubble():
    import lay_rubble
    fresh_scene()
    wall = box('wall', (6.0, 0.6, 2.4), (0.0, 0.0, 1.2))                      # front face at y = -0.3, left end at x = -3
    openings = [('front', 'door', 0.8, 0.0, 1.0, 1.9), ('front', 'window', 3.5, 1.0, 0.8, 0.7)]
    made = lay_rubble.lay(wall, sides=['front'], openings=openings, seed=5)
    stones = made['stones']
    points = world_points(stones)
    check(stones['stones'] == len(points) // 13 and stones['stones'] > 150, '%d rubble stones' % stones['stones'])
    check(points[:, 1].max() < -0.3 + 0.04 and points[:, 1].min() > -0.3 - 0.07 - 0.06,
          'the stones are not on the front face, in relief (y %.3f to %.3f; the face is at -0.30)' % (points[:, 1].min(), points[:, 1].max()))
    faces = points.reshape(-1, 13, 3)[:, 4, 1]                               # the middle of each stone's face
    check(faces.max() < -0.3 - 0.01, 'a stone\'s face does not stand out from the wall (its middle at y = %.3f)' % faces.max())
    check(points[:, 0].min() > -3.0 - 0.1 and points[:, 0].max() < 3.0 + 0.1 and points[:, 2].min() > -0.06 and points[:, 2].max() < 2.4 + 0.01,
          'the stones run past the wall\'s face')
    centres = points.reshape(-1, 13, 3).mean(axis=1)
    for kind, left, bottom, width, height in [o[1:] for o in openings]:
        x0, x1, z0, z1 = -3.0 + left, -3.0 + left + width, bottom, bottom + height
        inside = (centres[:, 0] > x0 + 0.03) & (centres[:, 0] < x1 - 0.03) & (centres[:, 2] > z0 + 0.03) & (centres[:, 2] < z1 - 0.03)
        check(not inside.any(), '%d stones lie in the %s' % (inside.sum(), kind))
        for side_x, outward in ((x0, -1), (x1, 1)):
            beside = (numpy.abs(centres[:, 0] - (side_x + outward * 0.17)) < 0.14) & (centres[:, 2] > z0) & (centres[:, 2] < z1)
            check(beside.sum() >= 3, 'the %s has too few jamb stones beside its %s side (%d)' % (kind, 'left' if outward < 0 else 'right', beside.sum()))
    check(made['recesses'] is not None and len(made['recesses'].data.polygons) == 2, 'the openings have no dark panels')
    check(wall.data.materials[0].name == lay_rubble.MORTAR, 'the wall did not become the mortar')
    again = lay_rubble.lay(wall, sides=['front'], openings=openings, seed=5)
    check(numpy.allclose(world_points(again['stones']), points), 'the same seed laid different rubble')
    # a lean-to's end wall: the top rises from the left end (2.35 m) to the right (2.35 + 4 tan 12 = 3.20 m)
    house = box('house', (4.0, 3.0, 2.35), (10.0, 0.0, 1.175))
    slope = lay_rubble.lay(house, sides=['front'], pitch=12.0, high_side='right', seed=6)
    end = world_points(slope['stones'])
    rise = math.tan(math.radians(12.0))
    line_top = 2.35 + (end[:, 0] - 8.0) * rise
    check((end[:, 2] - line_top).max() < 0.03, 'a stone stands %.3f m above the lean-to\'s slope' % (end[:, 2] - line_top).max())
    right = end[end[:, 0] > 11.6, 2].max()
    left = end[end[:, 0] < 8.4, 2].max()
    check(abs(right - (2.35 + 3.8 * rise)) < 0.08 and abs(left - 2.35) < 0.1, 'the stones do not rise with the slope (%.2f at the left, %.2f at the right)' % (left, right))
    check(slope['backing'] is not None, 'no backing behind the stones where the slope rises above the box')
    for wrong in ({'sides': ['top']}, {'openings': [('front', 'door', 5.5, 0.0, 1.0, 1.9)]}, {'relief': 0.0}, {'pitch': 70.0},
                  {'openings': [('back', 'door', 0.5, 0.0, 1.0, 1.9)]}):
        check(refused(lambda: lay_rubble.lay(wall, sides=['front'], **dict({'openings': []}, **wrong)) if 'sides' not in wrong else lay_rubble.lay(wall, **wrong)),
              'the rubble tool accepted %s' % wrong)
    print('PASS lay_rubble: %d stones in relief on the front face only, none in the door or window, jamb stones up both sides of each; '
          'on a lean-to end they rise from %.2f to %.2f m and never above the slope; same seed, same stones; wrong options refused'
          % (stones['stones'], left, right))


# ------------------------------------------------------------------------------------------------ straw

def test_straw():
    import litter
    import tracks
    fresh_scene()
    yard = ground.make(size=(7.0, 6.0), relief=0.05, seed=3)
    ground.wet(yard, 0.4)
    tracks.path(yard, [(0.0, -3.0, 0.0), (0.0, 3.0, 0.0)], width=1.2, age=0.5, seed=1)
    plain = litter.scatter(yard, seed=1, collection=bpy.data.collections.new('plain'))
    check(sorted(plain) == ['leaves', 'twigs'], 'litter laid %s when straw was not asked for' % sorted(plain))
    straw = litter.scatter(yard, area=(-2.5, -2.0, 2.5, 2.0), kinds=('straw',), amount=4.0, seed=3)['straw']
    points = world_points(straw)
    check(len(points) == straw['pieces'] and len(points) > 20, '%d clumps of straw' % len(points))
    check(points[:, 0].min() >= -2.5 and points[:, 0].max() <= 2.5 and points[:, 1].min() >= -2.0 and points[:, 1].max() <= 2.0,
          'straw laid outside the rectangle asked for')
    # the clumps' shapes: strands spread over each clump, lying across it, not fanned out from its middle like an asterisk
    shapes = straw.modifiers[0].node_group.nodes['Collection Info'].inputs['Collection'].default_value
    fanned, spread = [], []
    for shape in shapes.objects:
        co = numpy.zeros(len(shape.data.vertices) * 3)
        shape.data.vertices.foreach_get('co', co)
        strands = co.reshape(-1, 2 * litter.STRAND_POINTS, 3)
        first = strands[:, :2, :2].mean(axis=1)
        last = strands[:, -2:, :2].mean(axis=1)
        middle = strands[:, :, :2].mean(axis=1)
        way = (last - first) / numpy.maximum(numpy.linalg.norm(last - first, axis=1, keepdims=True), 1e-9)
        out = middle - middle.mean(axis=0)
        out /= numpy.maximum(numpy.linalg.norm(out, axis=1, keepdims=True), 1e-9)
        fanned.append(numpy.abs(numpy.sum(way * out, axis=1)).mean())
        spread.append(numpy.median(numpy.linalg.norm(middle - middle.mean(axis=0), axis=1)))
    check(max(fanned) < 0.8, 'straw strands fan out from the clump\'s middle (alignment %.2f; an asterisk is near 1)' % max(fanned))
    check(min(spread) > 0.08, 'straw strands bunch at one point (half lie within %.2f of the middle of a 1 m clump)' % min(spread))
    # pressed flat where trodden: on the path the clumps are lower for their size than off it
    scale = numpy.zeros(len(points) * 3)
    straw.data.attributes['litter_scale'].data.foreach_get('vector', scale)
    scale = scale.reshape(-1, 3)
    flatness = scale[:, 2] / scale[:, 0]
    on_path, off_path = numpy.abs(points[:, 0]) < 0.3, numpy.abs(points[:, 0]) > 1.2
    check(on_path.sum() >= 2 and off_path.sum() >= 2, 'too few clumps on (%d) or off (%d) the path to compare' % (on_path.sum(), off_path.sum()))
    check(flatness[on_path].mean() < 0.6 * flatness[off_path].mean(), 'trodden straw is not pressed flat (%.2f on the path, %.2f off it)'
          % (flatness[on_path].mean(), flatness[off_path].mean()))
    # every strand lies on the ground: the copies are draped onto it, none buried and none floating
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = straw.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    co = numpy.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', co)
    evaluated.to_mesh_clear()
    co = co.reshape(-1, 3)[::97]
    lift = co[:, 2] - heights(yard, co[:, :2])
    check(lift.min() > -0.002 and lift.max() < 0.08, 'straw strands lie %.3f to %.3f m above the ground (0 to 8 cm expected)' % (lift.min(), lift.max()))
    again = litter.scatter(yard, area=(-2.5, -2.0, 2.5, 2.0), kinds=('straw',), amount=4.0, seed=3)['straw']
    check(numpy.allclose(world_points(again), points), 'the same seed laid different straw')
    check(refused(lambda: litter.scatter(yard, kinds=('hay',))), 'litter accepted a kind it does not have')
    print('PASS litter straw: not laid unless asked; %d clumps only in the rectangle; strands spread over each clump (alignment with '
          'the middle %.2f, an asterisk is 1); pressed to %.2f of their height on the path, %.2f off it; every strand on the ground; '
          'same seed, same straw' % (len(points), max(fanned), flatness[on_path].mean(), flatness[off_path].mean()))


# ------------------------------------------------------------------------------------------------ moss

def test_moss():
    import moss
    fresh_scene()
    stone = store.material('SURFACE • old_stone_wall_02')
    nodes_before, links_before = len(stone.node_tree.nodes), len(stone.node_tree.links)
    linked_before = stone.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node.name
    mossy = moss.add(stone, amount=0.85)
    check(mossy is not stone and mossy.name.startswith(stone.name + ' • moss'), 'moss did not make a new material (%s)' % mossy.name)
    check(len(stone.node_tree.nodes) == nodes_before and len(stone.node_tree.links) == links_before
          and stone.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node.name == linked_before,
          'moss changed the material it was given')
    check(len(mossy.node_tree.nodes) > nodes_before + 10, 'the mossy copy has no moss nodes')
    names = {n.attribute_name for n in mossy.node_tree.nodes if n.type == 'ATTRIBUTE'}
    check('pp_ground' in names, 'the moss does not measure the foot from the ground under each object')
    geometry = [n for n in mossy.node_tree.nodes if n.type == 'NEW_GEOMETRY']
    check(geometry and geometry[0].outputs['Normal'].is_linked, 'the moss does not look at which way the faces look')
    check(mossy['pp_moss_of'] == stone.name and abs(mossy['pp_moss'] - 0.85) < 1e-6, 'the copy does not record what it was made from')
    plain = bpy.data.materials.new('plain grey')
    plain.use_nodes = True
    mossy_plain = moss.add(plain, foot=0.0)
    check(mossy_plain.node_tree.nodes['Principled BSDF'].inputs['Base Color'].is_linked, 'moss on a plain colour did nothing')
    emit = bpy.data.materials.new('glow only')
    emit.use_nodes = True
    emit.node_tree.nodes.remove(emit.node_tree.nodes['Principled BSDF'])
    for wrong in (lambda: moss.add(stone, amount=2.0), lambda: moss.add(stone, facing=(0.9, 0.2)), lambda: moss.add(emit),
                  lambda: moss.add('no such material')):
        check(refused(wrong, (ValueError, KeyError)), 'moss accepted something wrong')
    print('PASS moss: a new mossy material (%d nodes more), the one given unchanged; on upward faces and the foot over the ground; '
          'works on a plain colour; wrong options refused' % (len(mossy.node_tree.nodes) - nodes_before))


# ------------------------------------------------------------------------------------------------ clearing

def test_clear():
    import clear_under
    import grass
    import litter
    import stones
    fresh_scene()
    yard = ground.make(size=(6.0, 6.0), relief=0.04, seed=2)
    ground.wet(yard, 0.4)
    area = (-2.0, -2.0, 2.0, 2.0)
    turf = grass.grow(yard, area=area, layers=('turf',), seed=2, look='made')
    laid = stones.scatter(yard, area=area, layers=('pebbles', 'grit'), seed=3)
    leaves = litter.scatter(yard, area=area, kinds=('leaves',), amount=2.0, seed=4)
    before = {name: world_points(obj) for name, obj in [('turf', turf['turf']), ('pebbles', laid['pebbles']), ('grit', laid['grit']), ('leaves', leaves['leaves'])]}
    scale_before = numpy.zeros(len(before['pebbles']) * 3)
    laid['pebbles'].data.attributes['stone_scale'].data.foreach_get('vector', scale_before)
    basket = box('basket', (0.6, 0.6, 0.4), (0.3, -0.2, 0.2))
    basket.rotation_euler.z = math.radians(30.0)
    bpy.context.view_layer.update()
    taken = clear_under.clear([turf, laid], basket, margin=0.05)
    turn = math.radians(30.0)

    def under_basket(xy):
        local_x = (xy[:, 0] - 0.3) * math.cos(turn) + (xy[:, 1] + 0.2) * math.sin(turn)
        local_y = -(xy[:, 0] - 0.3) * math.sin(turn) + (xy[:, 1] + 0.2) * math.cos(turn)
        dx, dy = numpy.maximum(numpy.abs(local_x) - 0.3, 0.0), numpy.maximum(numpy.abs(local_y) - 0.3, 0.0)
        return numpy.hypot(dx, dy) <= 0.05
    for name, obj, count_key in (('turf', turf['turf'], 'tufts'), ('pebbles', laid['pebbles'], 'stones'), ('grit', laid['grit'], 'stones')):
        old = before[name]
        covered = under_basket(old[:, :2])
        now = world_points(obj)
        check(covered.sum() > 0, 'nothing of the %s lay under the basket to clear (the test is too small)' % name)
        check(taken[obj.name] == covered.sum(), '%s: took away %d, %d lay under the basket' % (name, taken[obj.name], covered.sum()))
        check(now.shape == old[~covered].shape and numpy.allclose(now, old[~covered]), 'the %s outside the basket were moved or lost' % name)
        check(obj[count_key] == len(now), '%s still counts %d for %d points' % (name, obj[count_key], len(now)))
    scale_after = numpy.zeros(len(world_points(laid['pebbles'])) * 3)
    laid['pebbles'].data.attributes['stone_scale'].data.foreach_get('vector', scale_after)
    check(numpy.allclose(scale_after.reshape(-1, 3), scale_before.reshape(-1, 3)[~under_basket(before['pebbles'][:, :2])]),
          'the pebbles kept lost their own sizes')
    check(numpy.allclose(world_points(leaves['leaves']), before['leaves']), 'leaves not passed to the clearing were changed')
    moved = stones.settle(yard, laid)
    check(moved == laid['pebbles']['stones'] + laid['grit']['stones'], 'settle no longer works after clearing')
    circle = clear_under.clear(leaves, lambda x, y: (x - 1.0) ** 2 + (y - 1.0) ** 2 < 0.4 ** 2)
    left = world_points(leaves['leaves'])
    gone = (before['leaves'][:, 0] - 1.0) ** 2 + (before['leaves'][:, 1] - 1.0) ** 2 < 0.4 ** 2
    check(circle['litter leaves'] == gone.sum() and numpy.allclose(left, before['leaves'][~gone]), 'the circle footprint cleared the wrong leaves')
    clear_under.clear(turf, (-1.5, -1.5, -1.0, -1.0))
    rest = world_points(turf['turf'])
    check(not ((rest[:, 0] >= -1.5) & (rest[:, 0] <= -1.0) & (rest[:, 1] >= -1.5) & (rest[:, 1] <= -1.0)).any(), 'turf left in the rectangle cleared')
    clear_under.clear(laid['grit'], [(0.5, 0.5), (1.5, 0.5), (0.5, 1.5)])
    rest = world_points(laid['grit'])
    check(not ((rest[:, 0] > 0.5) & (rest[:, 1] > 0.5) & (rest[:, 0] + rest[:, 1] < 2.0)).any(), 'grit left in the triangle cleared')
    for wrong in (lambda: clear_under.clear(yard, basket), lambda: clear_under.clear(turf, 'here'), lambda: clear_under.clear('grass', basket),
                  lambda: clear_under.clear(turf, basket, margin=-1.0)):
        check(refused(wrong), 'the clearing accepted something wrong')
    print('PASS clear_under: under a turned basket it took away %d tufts, %d pebbles and %d grit and kept every other one with its '
          'numbers; leaves not given untouched; settle still works; a circle, a rectangle and a triangle clear only inside; wrong things refused'
          % (taken[turf['turf'].name], taken[laid['pebbles'].name], taken[laid['grit'].name]))


# ------------------------------------------------------------------------------------------------ lay_boards, hollow

def test_hollow_boards():
    import lay_boards
    fresh_scene()
    hut = box('barn', (5.0, 6.0, 3.2), (0.0, 5.0, 1.6))                     # front face at y = 2, back at y = 8, left end x = -2.5
    made = lay_boards.lay(hut, openings=[('front', 'door', 1.5, 0.0, 2.0, 2.4)], eaves='pitched', fill=True, hollow=True,
                          inside_material='SURFACE • old_planks_02', seed=7)
    check(made.get('shell') is hut and hut.get('hollow'), 'hollow=True did not make the hut a shell')
    inverse = hut.matrix_world.inverted()

    def first_hit(obj, start, direction=Vector((0.0, 1.0, 0.0))):
        to_local = obj.matrix_world.inverted()
        hit, where, _normal, face = obj.ray_cast(to_local @ Vector(start), (to_local.to_3x3() @ direction).normalized())
        return (obj.matrix_world @ where, face) if hit else (None, None)
    where, face = first_hit(hut, (0.0, 0.0, 1.2))                            # in front of the door's middle (door from x -1 to 1)
    check(where is not None and abs(where.y - 7.9) < 0.02, 'a look through the doorway does not reach the back wall\'s inside (hit at %s)' % (where,))
    check(hut.data.materials[hut.data.polygons[face].material_index].name == 'SURFACE • old_planks_02', 'the inside is not in the inside material')
    beside, _ = first_hit(hut, (-2.0, 0.0, 1.2))                             # the wall beside the door: solid
    check(beside is not None and abs(beside.y - 2.0) < 0.02, 'the wall beside the door is not solid at its face (hit at %s)' % (beside,))
    blocked, _ = first_hit(made['boards'], (0.0, 0.0, 1.2))
    check(blocked is None or blocked.y > 2.5, 'a door leaf closes the doorway of a hollow hut')
    under, _ = first_hit(hut, (0.0, 5.0, 2.5), Vector((0.0, 0.0, -1.0)))
    check(under is not None and abs(under.z - 0.03) < 0.01, 'the hollow hut has no floor (hit at %s)' % (under,))
    fresh_scene()
    solid = box('hut', (4.0, 3.0, 2.4), (0.0, 0.0, 1.2))
    plain = lay_boards.lay(solid, openings=[('front', 'door', 1.55, 0.0, 0.9, 1.95)], seed=4)
    check('shell' not in plain and len(solid.data.polygons) == 6, 'without hollow the hut is no longer the plain box it was')
    print('PASS lay_boards hollow: the doorway opens into the shell (a look through it reaches the back wall\'s inside, in the inside '
          'material), the wall beside it is solid, no door leaf in the way, a floor; without hollow the box is as before')


def test_help():
    for name in ('dry_wall', 'hedge', 'lay_rubble', 'moss', 'clear_under', 'litter', 'lay_boards'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS dry_wall, hedge, lay_rubble, moss, clear_under, litter and lay_boards answer --help')


def main():
    test_dry_wall()
    test_dry_wall_curve()
    test_hedge()
    test_hedge_curve()
    test_rubble()
    test_straw()
    test_moss()
    test_clear()
    test_hollow_boards()
    test_help()
    print('PASS test_store_farm_tools')


if __name__ == '__main__':
    main()
