"""
What this file does: checks the road laid along a line or curve (lay_cobbles.lay_setts_along, lay_flags_along,
road_edges) against what it promises. On an S-bend: every sett lies inside the road's width, no two overlap, no joint
opens wider than asked, the courses lie square to the line and fan on the bends (the setts on the inside shorter), and
each course's joints are staggered from the next. A climbing road follows the line's height. Flags along the curve pass
the same checks. A kerb laid along road_edges sits at the road's edge all the way. The street's wear works on a curved
road (shades, quarries, rocked, holes with water, a relaid patch, grit and moss), and so do joint_weeds and the puddle's
refusal of the bed. Every sett, flag and kerbstone carries its own 'pp_piece' from 0 to 1. The same seed lays the same
road; wrong options are refused; lay_cobbles answers --help.
    python3 tests/test_store_curved_road.py
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import _lines  # noqa: E402

S_BEND = [(0.0, 0.0, 0.0), (0.0, 8.0, 0.0), (3.5, 18.0, 0.0), (10.5, 26.0, 0.0), (14.0, 36.0, 0.0), (14.0, 44.0, 0.0)]   # bends of 9.3 m radius
WIDTH = 5.0


def world_points(obj):
    co = numpy.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    matrix = numpy.array(obj.matrix_world)
    return co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def numbers(obj, name, width=1):
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no %r' % (obj.name, name))
    data = numpy.zeros(len(attribute.data) * width)
    attribute.data.foreach_get('vector' if width == 3 else 'value', data)
    return data.reshape(-1, width) if width > 1 else data


def refused(call, error=ValueError):
    try:
        call()
    except error:
        return True
    return False


def measure(line):
    """The smoothed line, finely sampled, for measuring how far along and to its left points lie."""
    path = _lines.Path([Vector(p) for p in line]).smooth(0.05)
    flat = _lines.Path([Vector((p.x, p.y, 0.0)) for p in path.points])
    return _lines.Path([flat.at(d) for d in numpy.linspace(0.0, flat.total, int(flat.total / 0.01) + 2)])


def stones_of(obj):
    """Each stone's middle (n, 3), half sizes (n, 2), heading (n,) and its own ways (right, ahead) seen from above."""
    middles = world_points(obj)
    halves = numbers(obj, 'stone_scale', 3)[:, :2] / 2.0
    eulers = numbers(obj, 'stone_rotation', 3)
    heading = numpy.array([Euler(e).to_matrix().to_euler('ZXY').z for e in eulers])
    right = numpy.stack([numpy.cos(heading), numpy.sin(heading)], axis=1)      # the stone's own x (across)
    ahead = numpy.stack([-numpy.sin(heading), numpy.cos(heading)], axis=1)     # its own y (along)
    return middles, halves, heading, right, ahead


def tapers_of(obj):
    """Each stone's taper (a wedge-shaped flag's depth is depth * (1 - taper * x), x from -0.5 to 0.5 across it)."""
    return numbers(obj, 'stone_taper') if obj.data.attributes.get('stone_taper') is not None else numpy.zeros(len(obj.data.vertices))


def corners_of(middles, halves, right, ahead, tapers):
    out = []
    for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        depth = halves[:, 1:2] * (1.0 - tapers[:, None] * su * 0.5)
        out.append(middles[:, :2] + right * (su * halves[:, :1]) + ahead * (sv * depth))
    return numpy.concatenate(out)


def gaps_and_overlaps(obj, path, half, step=0.03):
    """Over a grid of places on the road: the most stones covering one place, and the farthest any place lies from a
    stone (a place in the middle of a joint lies half the joint from the stones each side)."""
    from scipy.spatial import cKDTree
    middles, halves, _heading, right, ahead = stones_of(obj)
    tapers = tapers_of(obj)
    s = numpy.arange(0.02, path.total - 0.02, step)
    t = numpy.arange(-half + 0.006, half - 0.006 + 1e-9, step)
    pts = path.arrays()
    places = []
    for ti in t:
        xs = numpy.interp(s, pts[1], pts[0][:, 0])
        ys = numpy.interp(s, pts[1], pts[0][:, 1])
        idx = numpy.clip(numpy.searchsorted(pts[1], s), 0, len(pts[1]) - 1)
        aheads = pts[2][idx]
        places.append(numpy.stack([xs - ti * aheads[:, 1], ys + ti * aheads[:, 0]], axis=1))
    places = numpy.concatenate(places)
    _d, near = cKDTree(middles[:, :2]).query(places, k=10)
    offset = places[:, None, :] - middles[near, :2]
    across = numpy.sum(offset * right[near], axis=2)
    lu = numpy.abs(across) - halves[near, 0]
    x = numpy.clip(across / (2.0 * halves[near, 0]), -0.5, 0.5)
    lv = numpy.abs(numpy.sum(offset * ahead[near], axis=2)) - halves[near, 1] * (1.0 - tapers[near] * x)
    covering = ((lu < -0.0008) & (lv < -0.0008)).sum(axis=1)
    distance = numpy.hypot(numpy.maximum(lu, 0.0), numpy.maximum(lv, 0.0)).min(axis=1)
    return int(covering.max()), float(distance.max()), places[numpy.argmax(distance)]


def check_laid(obj, line, half, joint, what):
    """Inside the width, none overlapping, no joint wider than `joint`, square to the line; returns the measures."""
    path = measure(line)
    middles, halves, heading, right, ahead = stones_of(obj)
    corners = corners_of(middles, halves, right, ahead, tapers_of(obj))
    along, across, _ahead = path.project(corners)
    check(numpy.abs(across).max() <= half + 0.003, '%s: a stone reaches %.3f m from the line; the road is %.2f m each side'
          % (what, numpy.abs(across).max(), half))
    check(along.min() > -0.01 and along.max() < path.total + 0.01, '%s: a stone lies past the line\'s ends' % what)
    most, farthest, where = gaps_and_overlaps(obj, path, half)
    check(most <= 1, '%s: two stones overlap' % what)
    check(farthest <= joint / 2 + 0.0015, '%s: a joint opens %.3f m wide near (%.2f, %.2f); asked at most %.3f'
          % (what, 2 * farthest, where[0], where[1], joint))
    m_along, m_across, m_ahead = path.project(middles[:, :2])
    line_heading = numpy.arctan2(m_ahead[:, 1], m_ahead[:, 0])
    off = numpy.degrees(numpy.abs((heading + math.pi / 2 - line_heading + math.pi / 2) % math.pi - math.pi / 2))
    check(off.max() < 3.0, '%s: a stone is turned %.1f degrees off square to the line' % (what, off.max()))
    return m_along, m_across, halves, off, 2 * farthest


def bends_at(line, along):
    path = _lines.Path([Vector(p) for p in line]).smooth(0.05)
    points, lengths, ahead = path.arrays()
    heading = numpy.unwrap(numpy.arctan2(ahead[:, 1], ahead[:, 0]))
    bend = numpy.gradient(heading, lengths)
    return numpy.interp(along, lengths, bend)


# ------------------------------------------------------------------------------------------------ the S-bend road

def test_s_bend():
    import lay_cobbles
    fresh_scene()
    setts = lay_cobbles.lay_setts_along(S_BEND, WIDTH, seed=2, missing=0.0)      # no true missing setts: no holes in the count
    half = WIDTH / 2
    along, across, halves, off, widest = check_laid(setts, S_BEND, half, 0.025, 'the setts')
    check(len(setts.data.vertices) > 3000 and setts['stones'] == len(setts.data.vertices), 'only %d setts' % len(setts.data.vertices))
    # fanning: on the bends the setts on the inside are shorter (along the road) than those on the outside
    bend = bends_at(S_BEND, along)
    on_bend = numpy.abs(bend) > 1.0 / 14.0
    inside = on_bend & (across * numpy.sign(bend) > half * 0.5)
    outside = on_bend & (across * numpy.sign(bend) < -half * 0.5)
    ratio = halves[inside, 1].mean() / halves[outside, 1].mean()
    check(inside.sum() > 50 and outside.sum() > 50 and ratio < 0.8, 'the courses do not fan on the bends (inside setts %.2f of the outside\'s depth)' % ratio)
    straight = numpy.abs(bend) < 1.0 / 200.0
    check(abs(halves[straight & (across > half * 0.5), 1].mean() / halves[straight & (across < -half * 0.5), 1].mean() - 1.0) < 0.1,
          'on the straight the setts are not the same depth both sides')
    # each course's joints staggered from the next
    road = lay_cobbles._RoadLine(S_BEND)
    import random
    courses = lay_cobbles._courses(road, half, random.Random(2), (0.125, 0.19), (0.23, 0.36), lay_cobbles.SETT_JOINT, 0.025, 0.085, 0.22, 0.06)
    close = total = 0
    for (_a, _b, cells), (_c, _d, following) in zip(courses, courses[1:]):
        joints, next_joints = numpy.array([c[1] for c in cells[:-1]]), numpy.array([c[1] for c in following[:-1]])
        if len(joints) and len(next_joints):
            nearest = numpy.abs(joints[:, None] - next_joints[None, :]).min(axis=1)
            close += int((nearest < 0.04).sum())
            total += len(joints)
    check(close <= total * 0.02, '%d of %d joints line up with the next course\'s (within 4 cm)' % (close, total))
    # its own bed, lowered under the setts, which the puddle will not drape water on
    bed = setts['bed']
    check(bed.get('lay_cobbles_lowered') == 0.125 and abs(world_points(bed)[:, 2].max() + 0.125) < 1e-6, 'the bed is not 12.5 cm under the line')
    import puddle
    check(refused(lambda: puddle.make(location=(0.0, 4.0, 0.0), size=(1.0, 0.5), ground=bed)), 'the puddle draped water on the setts\' bed')
    pieces = numbers(setts, 'pp_piece')
    check(pieces.min() >= 0.0 and pieces.max() <= 1.0 and pieces.std() > 0.2 and len(numpy.unique(pieces)) == len(pieces), 'the setts\' pp_piece is not each its own, 0 to 1')
    print('PASS lay_setts_along on an S-bend: %d setts, all inside the 5 m road, none overlapping, the widest joint %.3f m (asked '
          'at most 0.025), square to the line within %.1f degrees; on the bends the inside setts %.0f%% of the outside\'s depth; '
          '%d of %d joints within 4 cm of the next course\'s; a bed 12.5 cm under; each sett its own pp_piece'
          % (len(setts.data.vertices), widest, off.max(), 100 * ratio, close, total))


def test_climbing():
    import lay_cobbles
    fresh_scene()
    line = [(0.0, 0.0, 0.0), (0.0, 10.0, 1.0), (4.0, 18.0, 1.6), (4.0, 24.0, 1.6)]
    setts = lay_cobbles.lay_setts_along(line, 4.0, seed=1)
    path = _lines.Path([Vector(p) for p in line]).smooth(0.05)
    flat = measure(line)
    middles = world_points(setts)
    along, across, _ahead = flat.project(middles[:, :2])
    points, lengths, _a = path.arrays()
    flat_lengths = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(points[:, :2], axis=0), axis=1))])
    line_z = numpy.interp(along, flat_lengths, points[:, 2])
    crown = 0.025 * (numpy.minimum(numpy.abs(across), 2.0) / 2.0) ** 1.8
    error = middles[:, 2] - (line_z - crown)
    check(numpy.abs(error).max() < 0.008, 'the setts leave the climbing line\'s height by %.3f m' % numpy.abs(error).max())
    slope = numpy.gradient(points[:, 2], flat_lengths)
    eulers = numbers(setts, 'stone_rotation', 3)
    pitch = numpy.array([(Euler(e).to_matrix() @ Vector((0.0, 1.0, 0.0))).z for e in eulers])
    want = numpy.interp(along, flat_lengths, slope)
    want = want / numpy.sqrt(1.0 + want ** 2)
    check(numpy.abs(pitch - want).max() < 0.02, 'the setts do not lie along the climb (off by %.3f)' % numpy.abs(pitch - want).max())
    check(abs(setts['top_height'] - 0.0) < 1e-6 and abs(setts['top_highest'] - 1.6) < 0.05, 'top_height %.3f, highest %.3f' % (setts['top_height'], setts['top_highest']))
    at = lay_cobbles.top_at(setts, 0.0, 10.0)
    check(abs(at - 1.0) < 0.01, 'top_at gives %.3f at the line\'s point 1 m up' % at)
    bed = world_points(setts['bed'])
    b_along, _b, _c = flat.project(bed[:, :2])
    check(numpy.abs(bed[:, 2] - (numpy.interp(b_along, flat_lengths, points[:, 2]) - 0.125)).max() < 0.01, 'the bed does not climb with the road')
    # flags along the climb too: their tops at the line's height (each within its own small lift)
    flags = lay_cobbles.lay_flags_along([(p[0] + 6.0, p[1], p[2]) for p in line], 1.6, seed=1)
    f_middles = world_points(flags)
    f_along, _f, _g = measure([(p[0] + 6.0, p[1], p[2]) for p in line]).project(f_middles[:, :2])
    f_error = f_middles[:, 2] + 0.07 - numpy.interp(f_along, flat_lengths, points[:, 2])
    check(numpy.abs(f_error).max() < 0.012, 'the flags leave the climbing line\'s height by %.3f m' % numpy.abs(f_error).max())
    # a straight road from two points
    straight = lay_cobbles.lay_setts_along([(-10.0, 0.0, 0.0), (-10.0, 6.0, 0.0)], 3.0, seed=1, missing=0.0)
    check_laid(straight, [(-10.0, 0.0, 0.0), (-10.0, 6.0, 0.0)], 1.5, 0.025, 'the straight road')
    print('PASS lay_setts_along on a climbing road: every sett within %.1f mm of the line\'s height less the crown, pitched with '
          'the climb; top_at finds the tops anywhere; the bed climbs 12.5 cm under; flags follow the climb; a straight road '
          'from two points' % (1000 * numpy.abs(error).max()))


def test_flags_and_kerb():
    import lay_cobbles
    import lay_kerb
    fresh_scene()
    left, right = lay_cobbles.road_edges(S_BEND, WIDTH)
    check(len(left) == len(right) > 700, 'road_edges gave %d and %d points' % (len(left), len(right)))
    path = measure(S_BEND)
    _al, l_across, _x = path.project(numpy.array(left)[:, :2])
    _ar, r_across, _y = path.project(numpy.array(right)[:, :2])
    check(numpy.abs(l_across - 2.5).max() < 0.005 and numpy.abs(r_across + 2.5).max() < 0.005, 'the edges are not 2.5 m each side of the line')
    check(abs(numpy.array(left)[:, 2].max() + 0.025) < 1e-6, 'the edge is not at the setts\' tops (the line less the crown)')
    middle_left, _r = lay_cobbles.road_edges(S_BEND, WIDTH, beyond=0.30 + 0.9, rise=0.13)
    flags = lay_cobbles.lay_flags_along(middle_left, 1.8, seed=3)
    _along, _across, halves, off, widest = check_laid(flags, middle_left, 0.9, 0.05, 'the flags')
    check(numpy.abs(world_points(flags)[:, 2] + 0.07 - (0.13 - 0.025)).max() < 0.008, 'the flags\' tops are not at the line\'s height')
    f_tapers = tapers_of(flags)
    check(f_tapers.max() > 0.05 and (f_tapers < 0.02).mean() > 0.3, 'the flags do not fan on the bends (tapers up to %.3f)' % f_tapers.max())
    f_pieces = numbers(flags, 'pp_piece')
    check(f_pieces.std() > 0.2 and f_pieces.min() >= 0 and f_pieces.max() <= 1, 'the flags\' pp_piece is not varied from 0 to 1')
    # a kerb along the left edge, the road on its right: at the road's edge all the way
    kerb = lay_kerb.lay(left, road='right', seed=1)['kerb']
    points = world_points(kerb)
    k_along, k_across, _k = path.project(points[:, :2])
    above = points[:, 2] > -0.025 + 0.02
    check(k_across[above].min() > 2.5 - 0.03 and k_across.max() < 2.5 + 0.30 + 0.03,
          'the kerb leaves the road\'s edge: %.3f to %.3f m from the line, the edge at 2.5' % (k_across[above].min(), k_across.max()))
    for u in numpy.arange(0.4, path.total - 0.4, 0.5):
        near = numpy.abs(k_along - u) < 0.15
        check((near & above).any() and k_across[near & above].min() < 2.5 + 0.02, 'the kerb\'s road face leaves the edge near %.1f m along' % u)
    k_pieces = numbers(kerb, 'pp_piece')
    numbers_of = numbers(kerb, 'stone_number').astype(int)
    per_stone = [numpy.unique(k_pieces[numbers_of == n]) for n in range(kerb['stones'])]
    check(all(len(p) == 1 for p in per_stone) and len(numpy.unique(k_pieces)) == kerb['stones'] and k_pieces.std() > 0.15,
          'the kerbstones do not each carry one pp_piece of their own on their faces')
    check(kerb.data.attributes['pp_piece'].domain == 'FACE', 'the kerb\'s pp_piece is not on its faces')
    print('PASS road_edges, lay_flags_along and the kerb: the edges 2.5 m each side at the setts\' tops; %d flags inside the '
          'pavement, none overlapping, the widest joint %.3f m (asked at most 0.05), square within %.1f degrees; a kerb of %d '
          'stones along the left edge stands at the road\'s edge all the way; each flag and kerbstone its own pp_piece'
          % (len(flags.data.vertices), widest, off.max(), kerb['stones']))


def test_wear():
    import lay_cobbles
    import joint_weeds
    fresh_scene()
    area = (-3.0, 0.0, 3.0, 8.0)
    setts = lay_cobbles.lay_setts_along(S_BEND, WIDTH, seed=4, shades=0.3, quarries=True, rocked=0.3, rocked_area=area,
                                        holes=[(0.5, 3.0), (14.0, 40.0)], hole_water=True, patch=(2.5, 17.0, 5.0, 18.5),
                                        grit=True, moss=(8.0, 22.0, 13.0, 30.0))
    plain = lay_cobbles.lay_setts_along(S_BEND, WIDTH, seed=4, collection=bpy.data.collections.new('plain'))
    tints = numbers(setts, 'stone_tint', 3)
    warm = (tints[:, 0] > tints[:, 2] * 1.5).mean()
    check(abs(warm - 0.32) < 0.07, 'quarries gave %.2f warm setts' % warm)
    check(setts['rocked'] > 30, 'only %d setts rocked' % setts['rocked'])
    p_mid, s_mid = world_points(plain), world_points(setts)
    from scipy.spatial import cKDTree
    distance, nearest = cKDTree(p_mid[:, :2]).query(s_mid[:, :2])
    moved = (distance < 1e-6) & ((p_mid[nearest, 2] - s_mid[:, 2]) > 0.003)
    outside = ~((s_mid[:, 0] > area[0]) & (s_mid[:, 0] < area[2]) & (s_mid[:, 1] > area[1]) & (s_mid[:, 1] < area[3]))
    check(moved.sum() > 30 and not (moved & outside).any(), 'rocked setts outside the area (%d) or too few inside (%d)' % ((moved & outside).sum(), moved.sum()))
    check(setts['holes'] >= 2 and len(world_points(setts['hole water'])) == 9 * setts['holes'], 'holes %d with water %d' % (setts['holes'], len(world_points(setts['hole water']))))
    for place in ((0.5, 3.0), (14.0, 40.0)):
        check(numpy.hypot(s_mid[:, 0] - place[0], s_mid[:, 1] - place[1]).min() > 0.08, 'a sett still stands in the hole at %s' % (place,))
    relaid = world_points(setts['relaid setts'])
    in_patch = (s_mid[:, 0] > 2.5) & (s_mid[:, 0] < 5.0) & (s_mid[:, 1] > 17.0) & (s_mid[:, 1] < 18.5)
    check(not in_patch.any() and setts['relaid'] > 20 and setts['lifted'] > 20, 'the patch: %d old setts left, %d relaid' % (in_patch.sum(), setts['relaid']))
    check(numbers(setts['relaid setts'], 'pp_piece').std() > 0.15, 'the relaid setts carry no pp_piece of their own')
    pitch = world_points(setts['pitch'])
    check(pitch[:, 2].max() < -0.009 and pitch[:, 2].min() > -0.06, 'the pitch is not just under the tops')
    stones = world_points(setts['joint stones'])
    moss = world_points(setts['joint moss'])
    check(len(stones) > 3000 and len(moss) > 30, '%d joint stones, %d moss' % (len(stones), len(moss)))
    middles, halves, _h, right, ahead = stones_of(setts)
    sample = stones[numpy.random.default_rng(1).choice(len(stones), 1500, replace=False), :2]
    _d, near = cKDTree(middles[:, :2]).query(sample, k=6)
    offset = sample[:, None, :] - middles[near, :2]
    inside = (numpy.abs(numpy.sum(offset * right[near], axis=2)) < halves[near, 0] - 0.012) & \
             (numpy.abs(numpy.sum(offset * ahead[near], axis=2)) < halves[near, 1] - 0.012)
    check(not inside.any(), '%d joint stones lie inside setts' % inside.any(axis=1).sum())
    check(((moss[:, 0] >= 8.0) & (moss[:, 0] <= 13.0) & (moss[:, 1] >= 22.0) & (moss[:, 1] <= 30.0)).all(), 'moss outside its area')
    check(numpy.abs(world_points(setts['grit bed'])[:, 2] + 0.03 + 0.0125).max() <= 0.0126, 'the grit bed is not 3 cm under the tops')
    made = joint_weeds.grow(setts, area=(-3.0, 0.0, 3.0, 12.0), amount=3.0, seed=2)
    roots = numpy.concatenate([world_points(o) for o in made.values()])
    _d, near = cKDTree(middles[:, :2]).query(roots[:, :2], k=6)
    offset = roots[:, None, :2] - middles[near, :2]
    in_sett = (numpy.abs(numpy.sum(offset * right[near], axis=2)) < halves[near, 0] - 0.015) & \
              (numpy.abs(numpy.sum(offset * ahead[near], axis=2)) < halves[near, 1] - 0.015)
    check(len(roots) > 5 and not in_sett.any(), 'joint_weeds on the curved road: %d tufts, %d inside setts' % (len(roots), in_sett.any(axis=1).sum()))
    print('PASS the wear on a curved road: %.0f%% warm setts, %d rocked (only in the area), %d holes with water, a patch of %d '
          'relaid setts with pitch, %d joint stones (none inside a sett) and %d moss cushions in their area; joint_weeds grew %d '
          'tufts, all in joints' % (100 * warm, setts['rocked'], setts['holes'], setts['relaid'], len(stones), len(moss), len(roots)))


def test_line_objects():
    import lay_cobbles
    import json
    import tempfile
    fresh_scene()
    mesh = bpy.data.meshes.new('road line')
    points = [(20.0, 0.0, 0.0), (20.0, 6.0, 0.0), (23.0, 12.0, 0.0), (28.0, 15.0, 0.0)]
    mesh.from_pydata(points, [(0, 1), (1, 2), (2, 3)], [])
    line = bpy.data.objects.new('road line', mesh)
    bpy.context.scene.collection.objects.link(line)
    curve_data = bpy.data.curves.new('road curve', 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, (x, y, z) in zip(spline.points, points):
        point.co = (x + 20.0, y, z, 1.0)
    curve = bpy.data.objects.new('road curve', curve_data)
    bpy.context.scene.collection.objects.link(curve)
    handle, path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(handle, 'w') as out:
        json.dump({'points': [[x + 40.0, y, z] for x, y, z in points]}, out)
    counts = []
    for given, shift in ((line, 0.0), (curve, 20.0), (path, 40.0)):
        setts = lay_cobbles.lay_setts_along(given, 4.0, seed=1, missing=0.0)
        moved = [(x + shift, y, z) for x, y, z in points]
        check_laid(setts, moved, 2.0, 0.025, 'the setts along a %s' % type(given).__name__)
        counts.append(len(setts.data.vertices))
    os.remove(path)
    check(max(counts) - min(counts) <= max(counts) * 0.02, 'a mesh line, a curve and a JSON file of the same points laid %s setts' % counts)
    print('PASS lay_setts_along follows a line-mesh object, a curve object and a JSON file of points alike (%s setts)' % counts)


def test_same_seed_and_refusals():
    import lay_cobbles
    runs = []
    for _ in range(2):
        fresh_scene()
        setts = lay_cobbles.lay_setts_along(S_BEND, WIDTH, seed=7, rocked=0.2, grit=True)
        flags = lay_cobbles.lay_flags_along([(8, 0, 0), (8, 10, 0), (12, 20, 0)], 2.0, seed=7)
        runs.append((world_points(setts).round(6).tolist(), numbers(setts, 'stone_scale', 3).round(6).tolist(),
                     len(setts['joint stones'].data.vertices), world_points(flags).round(6).tolist()))
    check(runs[0] == runs[1], 'the same seed laid a different road')
    fresh_scene()
    other = lay_cobbles.lay_setts_along(S_BEND, WIDTH, seed=8)
    check(world_points(other).shape != numpy.array(runs[0][0]).shape or numpy.abs(world_points(other) - numpy.array(runs[0][0])).max() > 1e-3,
          'another seed laid the same road')
    tight = [(0.0, 0.0, 0.0), (0.0, 3.0, 0.0), (2.0, 4.0, 0.0), (4.0, 3.0, 0.0)]
    for call, what in ((lambda: lay_cobbles.lay_setts_along(S_BEND, -1.0), 'a road of width -1'),
                       (lambda: lay_cobbles.lay_setts_along(S_BEND, 5.0, joint=0.001), 'a joint of 1 mm'),
                       (lambda: lay_cobbles.lay_setts_along(S_BEND, 5.0, quarries=(0.8, 0.5)), 'quarries (0.8, 0.5)'),
                       (lambda: lay_cobbles.lay_setts_along(S_BEND, 5.0, moss='all'), 'moss without grit'),
                       (lambda: lay_cobbles.lay_setts_along(S_BEND, 5.0, patch='here'), 'a patch named here'),
                       (lambda: lay_cobbles.lay_setts_along([(0, 0, 0), (0, 0, 0)], 5.0), 'a line of one point'),
                       (lambda: lay_cobbles.lay_setts_along(tight, 6.0), 'a bend tighter than the road is wide'),
                       (lambda: lay_cobbles.lay_flags_along(S_BEND, 0.1), 'a pavement 10 cm wide'),
                       (lambda: lay_cobbles.lay_flags_along(S_BEND, 2.0, shades=2.0), 'flag shades of 2'),
                       (lambda: lay_cobbles.road_edges(S_BEND, 0.0), 'edges of a road with no width')):
        check(refused(call), 'accepted %s' % what)
    result = subprocess.run([sys.executable, os.path.join(TOOLS, 'lay_cobbles.py'), '--help'], capture_output=True, text=True, timeout=120)
    check(result.returncode == 0 and 'usage' in result.stdout.lower() and '--line' in result.stdout, 'lay_cobbles --help failed: %s' % (result.stderr or result.stdout)[-300:])
    print('PASS the same seed lays the same curved road and flags, another seed another; wrong widths, joints, quarries, '
          'patches, lines, too-tight bends refused; lay_cobbles answers --help, with --line')


def test_top_at_on_flags():
    """top_at on a climbing pavement (the worked example found it gave the first point's height everywhere)."""
    import lay_cobbles
    fresh_scene()
    line = [(0, 0, 0), (0, 5, 0.25), (0, 10, 0.5), (0, 15, 0.75)]
    flags = lay_cobbles.lay_flags_along(line, 1.8, seed=3)
    heights = [lay_cobbles.top_at(flags, 0.0, y) for y in (1.0, 7.5, 14.0)]
    wanted = [0.05, 0.375, 0.70]
    check(all(abs(h - w) < 0.02 for h, w in zip(heights, wanted)),
          'top_at on climbing flags gives %s, not about %s' % (['%.3f' % h for h in heights], wanted))
    print('PASS top_at on a climbing pavement: %s m where the line is %s m' % (', '.join('%.3f' % h for h in heights),
                                                                              ', '.join('%.3f' % w for w in wanted)))


def main():
    test_s_bend()
    test_climbing()
    test_flags_and_kerb()
    test_wear()
    test_line_objects()
    test_same_seed_and_refusals()
    test_top_at_on_flags()
    print('PASS test_store_curved_road')


if __name__ == '__main__':
    main()
