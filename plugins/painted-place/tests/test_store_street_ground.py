"""
What this file does: checks the street ground tools the town street builders' set brought to the store (log 55)
against what they promise. The kerb: it follows its line and its curve, on the side away from the road, stays at its
width and its height, has chips knocked off its road-side edge (and none when asked for none), lays its channel stones
on the road side with their top at the road's level and dished towards the kerb, the same seed the same kerb, wrong
options refused. lay_cobbles' wear: without it the setts and flags are exactly as they were before it came (the same
stones in the same places, the store's own materials); each sett its own shade and setts from two quarries on a copy
of the material (the store's left as it was); rocked setts sunk and tipped, only where asked; holes where asked, with
water standing in them; a relaid patch of paler new setts, a little proud, with pitch in the joints and no old sett left
in it; grit packed in the joints under the tops and moss only where asked; the same seed the same road; wrong options
refused. The joint weeds: only in the area, only in joints, never in a wheel line, the same seed the same weeds, wrong
options refused. All of them answer --help.
    python3 tests/test_store_street_ground.py
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

# the default setts and flags of lay_cobbles before the wear options came (seed 1, a 3 x 8 m road, a 1.6 x 8 m pavement):
# count, then the sums of the points, sizes, turns and shapes (measured on the tool as it was)
BEFORE = {'setts': (549, -33.760755, 778.097813, 0.258291, 4709), 'flags': (23, 57.600957, 56.144068, 0.048237, 81)}


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


def plane(name, size_x, size_y, location=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size_x, size_y, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def measured(line, xy, smooth=True):
    """How far along the (smoothed) line each point lies, and how far to its right (the side away from a road on the left)."""
    path = _lines.Path([Vector((p[0], p[1], 0.0)) for p in line])
    path = path.smooth(0.05) if smooth else path
    fine = _lines.Path([path.at(d) for d in numpy.linspace(0.0, path.total, int(path.total / 0.01) + 2)])
    along, left, _ahead = fine.project(xy)
    return along, -left, path.total


# ------------------------------------------------------------------------------------------------ the kerb

def test_kerb():
    import lay_kerb
    fresh_scene()
    line = [(0.0, 0.0, 0.0), (0.0, 6.0, 0.0), (1.2, 8.6, 0.0), (4.0, 9.4, 0.0)]          # straight, then round a corner
    made = lay_kerb.lay(line, road='left', height=0.13, width=0.30, depth=0.30, channel=0.3, seed=2)
    check(sorted(made) == ['channel', 'kerb'], 'the kerb made %s' % sorted(made))
    kerb, gutter = made['kerb'], made['channel']
    points = world_points(kerb)
    along, away, total = measured(line, points[:, :2])
    check(kerb['stones'] >= 9, 'only %d kerbstones along %.1f m' % (kerb['stones'], total))
    check(along.min() > -0.03 and along.max() < total + 0.03, 'a kerbstone lies past the line\'s ends (%.2f to %.2f of %.2f m)' % (along.min(), along.max(), total))
    above = points[:, 2] > 0.02                                       # the part standing above the road
    check(away[above].min() > -0.03, 'the kerb stands %.3f m out into the road (on the road side of its line)' % -away[above].min())
    check(away.max() < 0.30 + 0.025, 'the kerb reaches %.3f m back from its line; its width is 0.30' % away.max())
    # it stays at its width all along, round the corner too: the back of the kerb is found at every half metre
    for u in numpy.arange(0.3, total - 0.3, 0.5):
        near = numpy.abs(along - u) < 0.12
        check(near.any() and away[near].max() > 0.30 - 0.02, 'the kerb is narrower than 0.30 m near %.1f m along its line' % u)
        check(away[near & above].min() < 0.02, 'the kerb\'s road face leaves its line near %.1f m along' % u)
    top = points[:, 2].max()
    check(0.125 < top <= 0.1305, 'the kerb\'s top is at %.3f m; asked 0.13' % top)
    check(points[:, 2].min() < -0.15, 'the kerbstones do not reach down into the ground (lowest %.3f m)' % points[:, 2].min())
    tones = numbers(kerb, 'stone_tone')
    check(len(set(numpy.round(tones, 4))) == kerb['stones'], 'the kerbstones do not each have their own shade')
    check(kerb.data.materials[0].name.endswith('• stone by stone'), 'the kerb is not in a shaded copy of its material: %s' % kerb.data.materials[0].name)
    # chips knocked off the road-side top edge, and only there
    chip = numbers(kerb, 'kerb_chip')
    check(kerb['chips'] > 3 and (chip > 0.008).sum() > 30, 'too few chips: %d chips, %d points cut back' % (kerb['chips'], (chip > 0.008).sum()))
    cut = chip > 0.003
    check(away[cut].max() < 0.09 and points[cut, 2].min() > 0.13 - 0.09, 'a chip lies away from the road-side top edge (%.3f m back, %.3f m up)' % (away[cut].max(), points[cut, 2].min()))
    whole = lay_kerb.lay(line, road='left', chips=0, seed=2)['kerb']
    check(numbers(whole, 'kerb_chip').max() == 0.0 and whole['chips'] == 0, 'chips=0 still chipped the kerb')
    # the channel: on the road side, its top at the road's level, lower at the kerb than at its road edge
    gutter_points = world_points(gutter)
    g_along, g_away, _ = measured(line, gutter_points[:, :2])
    check(g_away.max() < 0.0 and g_away.min() > -(0.3 + 0.012 + 0.03), 'the channel lies %.3f to %.3f m from the line; asked 0.3 m on the road side' % (g_away.min(), g_away.max()))
    check(gutter_points[:, 2].max() < 0.003, 'the channel stands %.3f m above the road' % gutter_points[:, 2].max())
    tops = gutter_points[:, 2] > -0.03
    inner = tops & (g_away > -0.06)
    outer = tops & (g_away < -0.27)
    check(gutter_points[inner, 2].mean() < gutter_points[outer, 2].mean() - 0.006, 'the channel is not dished towards the kerb')
    check(gutter['stones'] >= 12, 'only %d channel stones' % gutter['stones'])
    # the road on the right puts the kerb on the other side of the line
    right = world_points(lay_kerb.lay(line, road='right', seed=2)['kerb'])
    _a, right_away, _t = measured(line, right[:, :2])
    check(right_away.max() < 0.03 and right_away.min() < -0.27, 'road=right did not lay the kerb on the left of the line')
    # the same seed lays the same kerb; another seed another
    again = world_points(lay_kerb.lay(line, road='left', height=0.13, width=0.30, depth=0.30, channel=0.3, seed=2)['kerb'])
    check(again.shape == points.shape and numpy.abs(again - points).max() < 1e-6, 'the same seed laid a different kerb')
    other = world_points(lay_kerb.lay(line, road='left', seed=3)['kerb'])
    check(other.shape != points.shape or numpy.abs(other - points).max() > 1e-3, 'another seed laid the same kerb')
    # straight runs: no stone spans a turn
    straight = lay_kerb.lay([(10.0, 0.0, 0.0), (10.0, 3.0, 0.0), (13.0, 3.0, 0.0)], road='left', smooth=False, seed=1)['kerb']
    s_points = world_points(straight)
    stone = numbers(straight, 'stone_number').astype(int)
    faces = numpy.array([p.vertices[0] for p in straight.data.polygons])
    spans = []
    for number in range(straight['stones']):
        ids = numpy.unique(numpy.concatenate([list(p.vertices) for p, n in zip(straight.data.polygons, stone) if n == number]))
        xs, ys = s_points[ids, 0], s_points[ids, 1]
        spans.append((xs.max() - xs.min() > 0.4) and (ys.max() - ys.min() > 0.4))
    check(not any(spans) and len(faces) > 0, 'with smooth=False a stone spans the turn')
    for bad in ({'road': 'middle'}, {'width': 0.0}, {'chips': -1}, {'channel': 0.05}, {'depth': 0.1}, {'shades': 2.0}, {'lean': -1}):
        check(refused(lambda: lay_kerb.lay(line, **bad)), 'lay_kerb accepted %s' % bad)
    check(refused(lambda: lay_kerb.lay([(0, 0, 0), (0, 0, 0)])), 'lay_kerb accepted a line of one point')
    print('PASS lay_kerb: %d stones follow the line and round its corner on the side away from the road, at 0.30 m wide and '
          '%.3f m high; %d chips on the road-side edge only (none when asked for none); %d channel stones on the road side, '
          'dished to the kerb; road=right mirrors it; straight runs keep stones off the turn; same seed, same kerb; wrong options refused'
          % (kerb['stones'], top, kerb['chips'], gutter['stones']))


# ------------------------------------------------------------------------------------------------ the setts' wear

def fingerprint(obj):
    mesh = obj.data
    scale = numbers(obj, 'stone_scale', 3)
    rotation = numbers(obj, 'stone_rotation', 3)
    shapes = numbers(obj, 'stone_shape')
    return (len(mesh.vertices), round(float(world_points(obj).sum()), 4), round(float(scale.sum()), 4),
            round(float(rotation.sum()), 4), int(shapes.sum()))


def road_and_pavement():
    fresh_scene()
    return plane('road', 3.0, 8.0), plane('pavement', 1.6, 8.0, location=(2.4, 0.0, 0.12))


def footprints(setts):
    """Each sett's middle (x, y), half size and turn, from its own numbers."""
    import joint_weeds
    middles, halves, turns = joint_weeds.joints_of(setts)
    return middles, halves, turns


def inside_any(xy, middles, halves, turns, inset):
    """For each point: is it more than `inset` inside some stone's footprint?"""
    from scipy.spatial import cKDTree
    tree = cKDTree(middles[:, :2])
    result = numpy.zeros(len(xy), dtype=bool)
    for i, near in enumerate(tree.query_ball_point(xy, r=0.4)):
        for j in near:
            c, s = math.cos(turns[j]), math.sin(turns[j])
            dx, dy = xy[i, 0] - middles[j, 0], xy[i, 1] - middles[j, 1]
            lx, ly = c * dx + s * dy, -s * dx + c * dy
            if abs(lx) < halves[j, 0] - inset and abs(ly) < halves[j, 1] - inset:
                result[i] = True
                break
    return result


def test_cobbles_unchanged():
    import lay_cobbles
    road, pavement = road_and_pavement()
    setts = lay_cobbles.lay_setts(road, seed=1)
    flags = lay_cobbles.lay_flags(pavement, seed=1)
    for name, made in (('setts', setts), ('flags', flags)):
        found = fingerprint(made)
        expected = BEFORE[name]
        check(found[0] == expected[0] and found[4] == expected[4] and all(abs(a - b) < 2e-3 for a, b in zip(found[1:4], expected[1:4])),
              'the default %s changed: %s, before %s' % (name, found, expected))
        check(made.data.attributes.get('stone_tint') is None, 'the default %s carry a tint' % name)
    check(setts.data.attributes.get('stone_tint') is None and not any(k in setts for k in ('relaid setts', 'pitch', 'hole water', 'grit bed', 'joint stones', 'rocked', 'holes')),
          'the default setts made wear nobody asked for: %s' % list(setts.keys()))
    shape = next(iter(bpy.data.collections[[c.name for c in bpy.data.collections if c.name.startswith('lay_cobbles shapes • setts')][0]].objects))
    # the store's own material, or (a photographed one) its copy that undoes each copy's own size (decision 80)
    check(shape.data.materials[0].name in (lay_cobbles.SETT_MATERIAL, lay_cobbles.SETT_MATERIAL + ' • stone sized'),
          'the default setts are not in the store\'s own material: %s' % shape.data.materials[0].name)
    # asking for shades or quarries moves no stone
    road2, _ = plane('road two', 3.0, 8.0, location=(0.0, 20.0, 0.0)), None
    tinted = lay_cobbles.lay_setts(road2, seed=1, shades=0.3, quarries=True)
    moved = world_points(tinted) - world_points(setts) - numpy.array([0.0, 20.0, 0.0])
    check(len(tinted.data.vertices) == len(setts.data.vertices) and numpy.abs(moved).max() < 1e-6, 'asking for shades moved the setts')
    print('PASS lay_cobbles without the wear: the same %d setts and %d flags in the same places as before it came, in the store\'s '
          'own materials; asking for shades or quarries moves no stone' % (BEFORE['setts'][0], BEFORE['flags'][0]))


def test_cobbles_shades_and_quarries():
    import lay_cobbles
    road, pavement = road_and_pavement()
    setts = lay_cobbles.lay_setts(road, seed=1, shades=0.3, quarries=(0.32, 0.12))
    tints = numbers(setts, 'stone_tint', 3)
    check(len(tints) == len(setts.data.vertices), 'not every sett carries a tint')
    grey = numpy.isclose(tints[:, 0], tints[:, 1]) & numpy.isclose(tints[:, 1], tints[:, 2])
    warm = tints[:, 0] > tints[:, 2] * 1.5
    dark = tints[:, 2] > tints[:, 0] * 1.1
    n = len(tints)
    check(abs(warm.sum() / n - 0.32) < 0.07 and abs(dark.sum() / n - 0.12) < 0.05 and (grey | warm | dark).all(),
          'quarries (0.32, 0.12) gave %.2f warm and %.2f dark' % (warm.sum() / n, dark.sum() / n))
    shade = tints[grey, 0]
    check(shade.min() >= 0.7 - 1e-6 and shade.max() <= 1.3 + 1e-6 and shade.std() > 0.12, 'shades 0.3 gave tints %.2f to %.2f' % (shade.min(), shade.max()))
    copy = bpy.data.materials.get(lay_cobbles.SETT_MATERIAL + ' • sett by sett')
    check(copy is not None, 'no copy of the sett material was made')
    reads = [n for n in copy.node_tree.nodes if n.type == 'ATTRIBUTE' and n.attribute_name == 'stone_tint' and n.attribute_type == 'INSTANCER']
    check(reads, 'the copy does not read each sett\'s tint')
    original = bpy.data.materials[lay_cobbles.SETT_MATERIAL]
    check(not [n for n in original.node_tree.nodes if n.type == 'ATTRIBUTE' and n.attribute_name == 'stone_tint'], 'the store\'s own sett material was changed')
    flags = lay_cobbles.lay_flags(pavement, seed=1, shades=0.15)
    flag_tints = numbers(flags, 'stone_tint', 3)
    check(flag_tints[:, 0].min() >= 0.85 - 1e-6 and flag_tints[:, 0].max() <= 1.15 + 1e-6 and flag_tints[:, 0].std() > 0.03, 'flag shades out of range')
    for bad in ({'shades': 1.5}, {'quarries': (0.8, 0.5)}, {'quarries': 'many'}):
        check(refused(lambda: lay_cobbles.lay_setts(plane('bad road', 1.0, 1.0, location=(9, 9, 0)), **bad)), 'lay_setts accepted %s' % bad)
    print('PASS lay_cobbles shades and quarries: every sett its own shade (0.7 to 1.3), %.0f%% warm brown and %.0f%% blue-black, on a '
          'copy of the material that reads them; the store\'s material as it was; flags shaded too' % (100 * warm.sum() / n, 100 * dark.sum() / n))


def test_cobbles_rocked_holes_patch():
    import lay_cobbles
    road, _pavement = road_and_pavement()
    plain = lay_cobbles.lay_setts(road, seed=1)
    plain_points, plain_turns = world_points(plain), numbers(plain, 'stone_rotation', 3)
    road2 = plane('road two', 3.0, 8.0, location=(0.0, 20.0, 0.0))
    area = (-1.5, 16.0, 1.5, 20.0)                     # the near half of the second road
    rocked = lay_cobbles.lay_setts(road2, seed=1, rocked=0.3, rocked_area=area)
    points = world_points(rocked) - numpy.array([0.0, 20.0, 0.0])
    turns = numbers(rocked, 'stone_rotation', 3)
    sunk = plain_points[:, 2] - points[:, 2]
    tipped = numpy.abs(turns - plain_turns).max(axis=1) > 1e-4
    moved = (sunk > 1e-6) | tipped
    in_area = points[:, 1] + 20.0 <= 20.0
    check(numpy.abs(points[:, :2] - plain_points[:, :2]).max() < 1e-6, 'rocking moved setts sideways')
    check(not moved[~in_area].any(), '%d setts outside the rocked area were rocked' % moved[~in_area].sum())
    share = moved[in_area].mean()
    check(abs(share - 0.3) < 0.08 and rocked['rocked'] == moved.sum(), 'rocked 0.3 rocked %.2f of the setts in its area (counted %d)' % (share, rocked['rocked']))
    check(sunk[moved].min() >= 0.004 - 1e-6 and sunk[moved].max() <= 0.016 + 1e-6 and tipped[moved].all(), 'rocked setts are not sunk 4 to 16 mm and tipped')
    # holes where asked, water standing in them
    road3 = plane('road three', 3.0, 8.0, location=(0.0, 40.0, 0.0))
    places = [(0.5, 41.0), (-0.7, 42.2)]
    holed = lay_cobbles.lay_setts(road3, seed=1, holes=places, hole_water=True)
    check(len(holed.data.vertices) == len(plain.data.vertices) - 2, 'holes took out %d setts, not 2' % (len(plain.data.vertices) - len(holed.data.vertices)))
    missing_too = holed['holes']
    check(missing_too >= 2, 'the setts object counts %d holes' % missing_too)
    water = holed['hole water']
    water_points = world_points(water)
    middles = water_points[::9]                        # each hole's water: a middle and eight round it
    check(len(middles) == missing_too, '%d holes but water in %d' % (missing_too, len(middles)))
    laid = world_points(holed)
    for place in places:
        nearest_water = numpy.hypot(middles[:, 0] - place[0], middles[:, 1] - place[1]).min()
        nearest_sett = numpy.hypot(laid[:, 0] - place[0], laid[:, 1] - place[1]).min()
        check(nearest_water < 0.2 and nearest_sett > nearest_water, 'no hole with water at %s' % (place,))
    top = holed['top_height']
    check((middles[:, 2] < top - 0.019).all() and (middles[:, 2] > top - 0.05).all(), 'the water in the holes is not 2 cm under the tops')
    check(water.data.attributes.get('shallow') is not None and water.data.materials[0].name == lay_cobbles.WATER_MATERIAL, 'the hole water lacks its material or its shallow rim')
    check(holed['grit bed'] is not None, 'no wet grit under the water in the holes')
    # a relaid patch
    road4 = plane('road four', 3.0, 8.0, location=(0.0, 60.0, 0.0))
    patch = (-0.9, 58.0, 0.7, 59.4)
    relaid_road = lay_cobbles.lay_setts(road4, seed=1, patch=patch)
    old = world_points(relaid_road)
    inside = (old[:, 0] > patch[0]) & (old[:, 0] < patch[2]) & (old[:, 1] > patch[1]) & (old[:, 1] < patch[3])
    check(not inside.any(), '%d old setts left in the relaid patch' % inside.sum())
    new = relaid_road['relaid setts']
    new_points = world_points(new)
    check(relaid_road['relaid'] == len(new_points) >= relaid_road['lifted'] * 0.8 and relaid_road['lifted'] > 30,
          'the patch lifted %d old setts and laid %d new' % (relaid_road['lifted'], len(new_points)))
    margin = 0.2
    check(((new_points[:, 0] > patch[0] - margin) & (new_points[:, 0] < patch[2] + margin) & (new_points[:, 1] > patch[1] - margin)
           & (new_points[:, 1] < patch[3] + margin)).all(), 'a new sett lies away from the patch')
    pale = numbers(new, 'stone_tint', 3)
    check(pale[:, 0].min() > 1.4, 'the new setts are not paler (tints from %.2f)' % pale[:, 0].min())
    proud = new_points[:, 2] - relaid_road['top_height']
    check(proud.max() > 0.004 and proud.max() <= 0.0121 and numpy.median(proud) > -0.02, 'the new setts are not a little proud (%.3f to %.3f)' % (proud.min(), proud.max()))
    pitch = relaid_road['pitch']
    pitch_points = world_points(pitch)
    check(pitch.data.materials[0].name == lay_cobbles.PITCH and pitch.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[0] < 0.02,
          'the pitch is not near black')
    check((pitch_points[:, 2] < relaid_road['top_height'] - 0.009).all() and (pitch_points[:, 2] > relaid_road['top_height'] - 0.04).all(), 'the pitch is not just under the tops')
    for bad in ({'rocked': 1.5}, {'patch': 'here'}, {'holes': [1, 2]}, {'rocked': 0.2, 'rocked_area': 'near'}):
        check(refused(lambda: lay_cobbles.lay_setts(plane('bad road', 1.0, 1.0, location=(9, 9, 0)), **bad)), 'lay_setts accepted %s' % bad)
    print('PASS lay_cobbles rocked, holes and patch: %.0f%% of the setts in the area rocked (sunk 4 to 16 mm, tipped), none outside; '
          'holes where asked, water 2 cm under the tops over grit; a patch of %d new setts, paler and a little proud, '
          'pitch in the joints, no old sett left in it' % (100 * share, len(new_points)))


def test_cobbles_grit_and_moss():
    import lay_cobbles
    road, _pavement = road_and_pavement()
    moss_area = (0.9, -4.0, 1.5, 4.0)
    setts = lay_cobbles.lay_setts(road, seed=1, grit=True, moss=moss_area)
    top = setts['top_height']
    bed = world_points(setts['grit bed'])
    check(bed[:, 2].max() < top - 0.029 and bed[:, 2].min() > top - 0.03 - 0.03, 'the grit bed is not 3 cm under the tops (%.3f to %.3f)' % (bed[:, 2].min(), bed[:, 2].max()))
    stones = world_points(setts['joint stones'])
    moss = world_points(setts['joint moss'])
    check(len(stones) > 3000 and len(moss) > 50, 'too few stones (%d) or moss cushions (%d) in the joints' % (len(stones), len(moss)))
    # each lies 2.4 to 3.1 cm under its own sett's top (a sett's top wobbles by up to 6 mm about the road's)
    check((stones[:, 2] < top - 0.017).all() and (moss[:, 2] < top - 0.017).all(), 'something in the joints stands too high')
    middles, halves, turns = footprints(setts)
    sample = numpy.random.default_rng(1).choice(len(stones), 800, replace=False)
    check(not inside_any(stones[sample, :2], middles, halves, turns, inset=0.012).any(), 'joint stones lie inside setts, not in the joints')
    check(((moss[:, 0] >= moss_area[0]) & (moss[:, 0] <= moss_area[2])).all(), 'moss grows outside the area asked for')
    check(refused(lambda: lay_cobbles.lay_setts(plane('bad road', 1.0, 1.0, location=(9, 9, 0)), moss='all')), 'moss without grit was accepted')
    again = lay_cobbles.lay_setts(plane('road two', 3.0, 8.0, location=(0.0, 20.0, 0.0)), seed=1, grit=True, moss=(0.9, 16.0, 1.5, 24.0))
    check(len(world_points(again['joint stones'])) == len(stones) and len(world_points(again['joint moss'])) == len(moss),
          'the same seed packed the joints differently')
    print('PASS lay_cobbles grit and moss: a grit bed 3 cm under the tops, %d small stones in the joints (none inside a sett, none '
          'standing proud), %d moss cushions only where asked; same seed, same joints' % (len(stones), len(moss)))


def test_cobbles_same_seed():
    import lay_cobbles
    options = dict(seed=4, shades=0.3, quarries=True, rocked=0.2, holes=[(0.3, 1.0)], hole_water=True, patch=(-1.0, -2.0, 0.4, -0.8),
                   grit=True, moss=(1.0, -4.0, 1.5, 4.0))
    runs = []
    for _ in range(2):
        road, _pavement = road_and_pavement()
        setts = lay_cobbles.lay_setts(road, **options)
        runs.append((fingerprint(setts), fingerprint(setts['relaid setts']), len(setts['joint stones'].data.vertices),
                     round(float(numbers(setts, 'stone_tint', 3).sum()), 4)))
    check(runs[0] == runs[1], 'the same seed laid a different worn road: %s / %s' % tuple(runs))
    print('PASS lay_cobbles with all the wear: the same seed lays the same road')


# ------------------------------------------------------------------------------------------------ weeds in the joints

def test_joint_weeds():
    import lay_cobbles
    import joint_weeds
    road, pavement = road_and_pavement()
    setts = lay_cobbles.lay_setts(road, seed=1, grit=True)
    flags = lay_cobbles.lay_flags(pavement, seed=1)
    area = (0.4, -4.0, 1.5, 4.0)
    wheel = [(1.0, -4.0), (1.0, 4.0)]
    made = joint_weeds.grow(setts, area=area, wheel_lines=[wheel], wheel_width=0.3, amount=2.0, seed=2)
    check(sorted(made) == ['grass', 'weeds'], 'joint_weeds made %s' % sorted(made))
    roots = numpy.concatenate([world_points(made['grass']), world_points(made['weeds'])])
    count = len(roots)
    check(made['grass']['tufts'] + made['weeds']['tufts'] == count and 8 < count < 40,
          '%d tufts on %.1f square metres at amount 2 (about 2.4 a square metre)' % (count, 1.1 * 8))
    check(((roots[:, 0] >= area[0]) & (roots[:, 0] <= area[2]) & (roots[:, 1] >= area[1]) & (roots[:, 1] <= area[3])).all(), 'a tuft grows outside the area')
    check((numpy.abs(roots[:, 0] - 1.0) > 0.15).all(), 'a tuft grows in the wheel line')
    middles, halves, turns = footprints(setts)
    check(not inside_any(roots[:, :2], middles, halves, turns, inset=0.015).any(), 'a tuft grows out of a sett, not a joint')
    near_edge = inside_any(roots[:, :2], middles, halves + 0.03, turns, inset=0.0)
    check(near_edge.all(), 'a tuft grows away from every sett')
    from scipy.spatial import cKDTree
    _d, nearest = cKDTree(middles[:, :2]).query(roots[:, :2])
    below = middles[nearest, 2] - roots[:, 2]       # under the nearest sett's top (the road is crowned; neighbours differ by 12 mm)
    check((below > -0.002).all() and (below < 0.03).all(), 'tufts are not rooted just under the tops (%.3f to %.3f m under)' % (below.min(), below.max()))
    on_flags = joint_weeds.grow(flags, area=(1.6, -4.0, 3.2, 4.0), amount=3.0, kinds='grass', seed=5)
    flag_roots = world_points(on_flags['grass'])
    f_middles, f_halves, f_turns = footprints(flags)
    check(len(flag_roots) > 5 and not inside_any(flag_roots[:, :2], f_middles, f_halves, f_turns, inset=0.015).any(), 'weeds on the flags are not in their joints')
    again = joint_weeds.grow(setts, area=area, wheel_lines=[wheel], wheel_width=0.3, amount=2.0, seed=2)
    again_roots = numpy.concatenate([world_points(again['grass']), world_points(again['weeds'])])
    check(again_roots.shape == roots.shape and numpy.abs(again_roots - roots).max() < 1e-6, 'the same seed grew different weeds')
    other = joint_weeds.grow(setts, area=area, amount=2.0, seed=3)
    other_roots = numpy.concatenate([world_points(other['grass']), world_points(other['weeds'])])
    check(other_roots.shape != roots.shape or numpy.abs(other_roots - roots).max() > 1e-3, 'another seed grew the same weeds')
    for bad in ({'amount': -1}, {'kinds': ('trees',)}, {'wheel_width': -0.2}):
        check(refused(lambda: joint_weeds.grow(setts, **bad)), 'joint_weeds accepted %s' % bad)
    check(refused(lambda: joint_weeds.grow(road)), 'joint_weeds accepted a plain road for stones')
    print('PASS joint_weeds: %d tufts, every one in a joint within the area and out of the wheel line, on setts and on flags; '
          'same seed, same weeds; wrong options refused' % count)


def test_help():
    for name in ('lay_kerb', 'joint_weeds', 'lay_cobbles'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS lay_kerb, joint_weeds and lay_cobbles answer --help')


def main():
    test_kerb()
    test_cobbles_unchanged()
    test_cobbles_shades_and_quarries()
    test_cobbles_rocked_holes_patch()
    test_cobbles_grit_and_moss()
    test_cobbles_same_seed()
    test_joint_weeds()
    test_help()
    print('PASS test_store_street_ground')


if __name__ == '__main__':
    main()
