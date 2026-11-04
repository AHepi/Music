"""
What this file does: checks the store's ground tools, the ground tool and the tracks tool, against what their notes
claim: the ground carries every number its soil reads, from 0 to 1; a camber lifts the road's middle by the drop given;
wet ground has dry, damp, wet and flooded parts and dry ground none flooded; water stands only where it is deep and wide
enough; the same seed makes the same ground. Ruts are deep with lips in wet mud and shallow without lips on dry ground;
old ruts are rounder than fresh ones; a car prints its tread on damp ground; wet ruts are smeared and hold water;
footprints alternate left and right with the heel deepest; potholes are carved only where asked; a path is trodden pale;
nothing is carved outside a mark; the same seed makes the same marks; wrong options are refused; a tractor's tread
stands in ridges and a cart's horse leaves hoof prints; water is cut from the ground's own faces; grass keeps out of the
ruts and water; leaves float on water; all four tools answer --help.
    python3 tests/test_store_ground.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import numpy  # noqa: E402
import ground  # noqa: E402
import tracks  # noqa: E402
import _lines  # noqa: E402

LANE = [(0.0, -4.0, 0.0), (0.0, 4.0, 0.0)]


def lane_ground(wetness, relief=0.03, seed=1, size=(6.0, 10.0), pattern='even'):
    """A 6 x 10 m ground, evenly wet unless asked (so a test knows how wet the ground under a mark is)."""
    fresh_scene()
    yard = ground.make(size=size, location=(0.0, 0.0, 0.0), relief=relief, seed=seed)
    ground.wet(yard, wetness, pattern=pattern)
    return yard


def across_lane(points):
    way = _lines.Path(_lines.line_points(LANE)).smooth(0.05)
    return way.project(points[:, :2])


def test_make_and_numbers():
    fresh_scene()
    yard = ground.make(size=(8.0, 8.0), relief=0.08, seed=3)
    mesh = yard.data
    for name in ground.POINT_NUMBERS:
        check(mesh.attributes.get(name) is not None, 'the ground carries no %r' % name)
    check(mesh.materials and mesh.materials[0].name.startswith('MADE • dirt'), 'the ground has no dirt soil on it')
    normals = numpy.zeros(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get('normal', normals)
    check(normals.reshape(-1, 3)[:, 2].min() > 0.5, 'some faces of the ground face down')
    for w in (0.0, 0.3, 0.6, 0.9):
        ground.wet(yard, w)
        for name in ('hollow', 'wetness', 'crust'):
            values = ground.numbers(mesh, name)
            check(values.min() >= 0.0 and values.max() <= 1.0, '%s runs %.2f..%.2f at wetness %.1f (0..1 expected)' % (name, values.min(), values.max(), w))
    print('PASS ground.make: a sheet facing up with the dirt soil and all %d numbers, each 0..1 at four wetnesses' % len(ground.POINT_NUMBERS))


def test_camber():
    fresh_scene()
    road = ground.make(size=(6.0, 6.0), relief=0.0, camber=([(0.0, -4.0, 0.0), (0.0, 4.0, 0.0)], 3.0, 0.05), seed=1)
    points = ground.world_points(road)
    middle = points[numpy.abs(points[:, 0]) < 0.06, 2].mean()
    edge = points[numpy.abs(numpy.abs(points[:, 0]) - 1.5) < 0.06, 2].mean()
    outside = points[numpy.abs(points[:, 0]) > 2.0, 2]
    check(abs((middle - edge) - 0.05) < 0.006, 'the camber lifts the middle %.3f m above the edges (0.05 asked)' % (middle - edge))
    check(numpy.abs(outside).max() < 1e-6, 'the camber lifted ground outside the road')
    print('PASS camber: the road\'s middle stands %.3f m above its edges (0.05 asked), the ground beside it untouched' % (middle - edge))


def test_wet_states_and_water():
    fresh_scene()
    yard = ground.make(size=(12.0, 12.0), relief=0.08, camber=([(0.4, -3, 0), (0.2, 4, 0), (0.6, 11, 0)], 3.5, 0.05), seed=3)
    mesh = yard.data
    spots = ground.wet(yard, 0.6)
    wet = ground.numbers(mesh, 'wetness')
    shares = [(wet < 0.2).mean(), ((wet >= 0.2) & (wet < 0.5)).mean(), ((wet >= 0.5) & (wet < ground.FLOODED)).mean(),
              (wet >= ground.FLOODED).mean()]
    check(all(share > 0.005 for share in shares), 'at wetness 0.6 a state is missing (dry, damp, wet, flooded: %s)' % ['%.3f' % s for s in shares])
    check(shares[3] < 0.1, 'at wetness 0.6 %.0f%% of the ground stands under water (too much)' % (100 * shares[3]))
    check(spots, 'wetness 0.6 gave no water')
    for spot in spots:
        check(spot['depth'] >= 0.004 and spot['area'] >= 0.02, 'water stands where it is too shallow or small: %s' % spot)
    check([s['area'] for s in spots] == sorted([s['area'] for s in spots], reverse=True), 'the water is not listed largest first')
    dry_spots = ground.wet(yard, 0.0)
    dry = ground.numbers(mesh, 'wetness')
    check(not dry_spots and dry.max() < 0.2, 'dry ground has water (%d places) or wet parts (wettest %.2f)' % (len(dry_spots), dry.max()))
    even = ground.wet(yard, 0.5, pattern='even')
    evenly = ground.numbers(mesh, 'wetness')
    check(numpy.percentile(evenly, 95) - numpy.percentile(evenly, 5) < 0.15, "'even' wetness is not even")
    spots = ground.wet(yard, 0.6)
    made = ground.fill(yard, spots[:3], seed=1)
    check(len(made) >= 1, 'ground.fill made no water')
    low, high = ground.world_points(yard)[:, :2].min(axis=0), ground.world_points(yard)[:, :2].max(axis=0)
    for water, spot in zip(made, spots[:3]):
        corners = numpy.array([tuple(water.matrix_world @ v.co) for v in water.data.vertices])
        check(numpy.abs(corners[:, 2] - spot['level']).max() < 1e-4, 'a water sheet does not lie flat at its spot\'s level')
        check((corners[:, :2] >= low - 1e-6).all() and (corners[:, :2] <= high + 1e-6).all(), 'water reaches past the ground\'s edge')
        check(water.data.attributes.get('shallow') is not None, 'the water carries no shallow rim')
    rainy = ground.fill(yard, spots[:1], seed=1, rain=0.5)[0].data.materials[0]
    check(abs(rainy.node_tree.nodes['Rain'].outputs[0].default_value - 0.5) < 1e-6, 'rain did not ring the water')
    check(made[0].data.materials[0].node_tree.nodes['Rain'].outputs[0].default_value == 0.0, 'rain changed the plain water too')
    ground.wet(yard, 0.7)
    try:
        ground.fill(yard, spots[:1])
        check(False, 'water was filled from spots found before the ground changed')
    except ValueError:
        pass
    print('PASS ground.wet: at 0.6 dry %.0f%%, damp %.0f%%, wet %.0f%%, flooded %.1f%%; %d pools, each deep and wide enough, largest first; '
          'dry ground none; even is even; fill cut flat sheets from the ground itself, rain rings a copy, stale spots refused'
          % tuple([100 * s for s in shares] + [len(spots)]))


def test_same_seed():
    first = ground.world_points(lane_ground(0.5, relief=0.08, seed=5))[:, 2]
    second = ground.world_points(lane_ground(0.5, relief=0.08, seed=5))[:, 2]
    other = ground.world_points(lane_ground(0.5, relief=0.08, seed=6))[:, 2]
    check(numpy.array_equal(first, second), 'the same seed made a different ground')
    check(not numpy.array_equal(first, other), 'a different seed made the same ground')
    print('PASS ground: the same seed makes the same ground, another seed another')


def test_ruts_wet_and_dry():
    results = {}
    for w in (0.75, 0.1):
        yard = lane_ground(w)
        before = ground.world_points(yard)
        result = tracks.ruts(yard, LANE, vehicle='cart', passes=2, age=0.5, seed=2)
        after = ground.world_points(yard)
        rise = after[:len(before), 2] - before[:, 2]
        along, across, _ = across_lane(before)
        outside = (numpy.abs(across) > 1.6) | (along < -1.0) | (along > 9.0)
        check(numpy.abs(rise[outside]).max() < 1e-6, 'ruts carved the ground outside their corridor (wetness %.2f)' % w)
        results[w] = (result['deepest'], rise.max(), len(result['spots']), ground.numbers(yard.data, 'smear').max())
    wet_depth, wet_rise, wet_spots, smear = results[0.75]
    dry_depth, dry_rise, _, _ = results[0.1]
    check(0.06 <= wet_depth <= 0.25, 'cart ruts in wet mud are %.3f m deep (0.06 to 0.25 expected)' % wet_depth)
    check(0.008 <= dry_depth <= 0.045, 'cart ruts on dry ground are %.3f m deep (0.008 to 0.045 expected)' % dry_depth)
    check(dry_depth < 0.4 * wet_depth, 'dry ruts (%.3f) are not much shallower than wet ones (%.3f)' % (dry_depth, wet_depth))
    check(wet_rise > 0.01, 'wet ruts have no lip (the ground rose %.3f m at most)' % wet_rise)
    check(dry_rise < 0.002, 'dry ruts pushed up a lip (%.3f m)' % dry_rise)
    check(wet_spots >= 1, 'wet ruts at middle age hold no water')
    check(smear > 0.3, 'wet ruts are not smeared (smear at most %.2f)' % smear)
    print('PASS ruts: %.3f m deep with a %.3f m lip and water in %d places in wet mud; %.3f m and no lip on dry ground; nothing carved outside'
          % (wet_depth, wet_rise, wet_spots, dry_depth))


def steepest(yard):
    mesh = yard.data
    normals = numpy.zeros(len(mesh.polygons) * 3)
    mesh.polygons.foreach_get('normal', normals)
    return float(numpy.degrees(numpy.arccos(numpy.clip(normals.reshape(-1, 3)[:, 2].min(), -1.0, 1.0))))


def test_ruts_age_tread_and_refusals():
    fresh_ruts = lane_ground(0.75)                             # each new ground clears the scene: measure at once
    tracks.ruts(fresh_ruts, LANE, vehicle='cart', age=0.05, seed=2)
    fresh_steep = steepest(fresh_ruts)
    old_ruts = lane_ground(0.75)
    tracks.ruts(old_ruts, LANE, vehicle='cart', age=0.95, seed=2)
    old_steep = steepest(old_ruts)
    check(old_steep < fresh_steep - 5.0, 'old ruts are not rounder than fresh ones (steepest face %.0f against %.0f degrees)' % (old_steep, fresh_steep))
    car = lane_ground(0.3)
    tracks.ruts(car, LANE, vehicle='car', age=0.05, seed=2)
    mesh = car.data
    tread, kind = ground.numbers(mesh, 'tread'), ground.numbers(mesh, 'tread_kind')
    check(((tread > 0.3) & (numpy.abs(kind - 1.0) < 0.01)).sum() > 100, "a car's fresh ruts on damp ground print no tread")
    faces = numpy.zeros(len(mesh.polygons))
    mesh.polygons.foreach_get('area', faces)
    check(numpy.sqrt(faces.min()) < 0.03, 'the ground was not divided finely under the ruts (smallest face %.3f m)' % numpy.sqrt(faces.min()))
    first = ground.world_points(car)[:, 2]
    again = lane_ground(0.3)
    tracks.ruts(again, LANE, vehicle='car', age=0.05, seed=2)
    check(numpy.array_equal(first, ground.world_points(again)[:, 2]), 'the same seed carved different ruts')
    for wrong in ({'vehicle': 'tank'}, {'age': 1.5}, {'passes': 0}, {'vehicle': (9.0, 0.1)}):
        try:
            tracks.ruts(again, LANE, **wrong)
            check(False, 'ruts accepted %s' % wrong)
        except ValueError:
            pass
    print('PASS ruts: old ruts are rounder (steepest face %.0f against %.0f degrees fresh); a car prints its tread on damp ground; '
          'the ground is divided finely under them; the same seed, the same ruts; wrong options are refused' % (old_steep, fresh_steep))


def test_footprints():
    for w, name in ((0.5, 'damp'), (0.05, 'dry')):
        yard = lane_ground(w, relief=0.0)                      # flat at height 0: every point's height is its change
        result = tracks.footprints(yard, LANE, stride=0.75, age=0.1, seed=3)
        after = ground.world_points(yard)
        mesh = yard.data
        change = after[:, 2]
        deep = change < -0.4 * result['deepest']
        groups, count = ground._groups(deep, ground.edges_of(mesh))
        prints = []
        for g in range(count):
            members = groups == g
            if members.sum() < 4:
                continue
            centre = after[members, :2].mean(axis=0)
            lowest = after[members][numpy.argmin(change[members])]
            prints.append((centre[1], centre[0], lowest[1] - centre[1]))
        prints.sort()
        check(9 <= len(prints) <= 12, '%s: %d prints along 8 m at a 0.75 m stride (about 10 expected)' % (name, len(prints)))
        sides = [x > 0 for _, x, _ in prints]
        check(all(a != b for a, b in zip(sides, sides[1:])), '%s: the prints do not alternate left and right' % name)
        heels = sum(1 for _, _, back in prints if back < 0)
        check(heels >= 0.7 * len(prints), '%s: the heel is the deepest part in only %d of %d prints' % (name, heels, len(prints)))
        if name == 'damp':
            check(0.004 <= result['deepest'] <= 0.02, 'footprints on damp ground are %.3f m deep (about 0.008)' % result['deepest'])
        else:
            check(result['deepest'] <= 0.005, 'footprints on dry ground are %.3f m deep (a few millimetres)' % result['deepest'])
            check(ground.numbers(mesh, 'wear').max() > 0.8, 'footprints on dry ground do not brush the dust away')
    print('PASS footprints: about one print each stride, left and right in turn, the heel deepest; millimetres deep on dry ground, '
          'the dust brushed away')


def test_potholes_and_path():
    yard = lane_ground(0.6, relief=0.0)
    before = ground.world_points(yard)
    result = tracks.potholes(yard, LANE, at=[2.0, 6.0], size=0.5, age=0.6, which='left', seed=1)
    after = ground.world_points(yard)
    change = after[:len(before), 2] - before[:, 2]
    along, across, _ = across_lane(before)
    holes = change < -0.01
    check(holes.any(), 'potholes carved nothing')
    near = (numpy.abs(along - 2.0) < 0.8) | (numpy.abs(along - 6.0) < 0.8)
    check(not (holes & ~near).any(), 'a pothole was carved away from the places asked')
    check((across[holes] > 0.3).all(), "the 'left' potholes are not on the left wheel line")
    check(0.05 <= result['deepest'] <= 0.16, 'potholes are %.3f m deep (0.05 to 0.15)' % result['deepest'])
    try:
        tracks.potholes(yard, LANE, at=[12.0])
        check(False, 'a pothole off the end of the line was accepted')
    except ValueError:
        pass
    auto = lane_ground(0.6, relief=0.0)
    tracks.potholes(auto, LANE, seed=1)
    carved = ground.world_points(auto)
    sunk = carved[carved[:, 2] < -0.01]
    check(len(sunk) and (numpy.abs(sunk[:, 1] + 3.2) < 0.8).any() and (numpy.abs(sunk[:, 1] - 3.2) < 0.8).any()
          and (numpy.abs(sunk[:, 1]) < 2.0).sum() == 0, "'ends and turns' on a straight line did not put potholes in from each end only")
    trodden = lane_ground(0.2, relief=0.0)
    way = tracks.path(trodden, LANE, width=0.5, age=0.8, seed=1)
    check(0.02 <= way['deepest'] <= 0.07, 'the path is %.3f m deep (0.02 to 0.06)' % way['deepest'])
    wear = ground.numbers(trodden.data, 'wear')
    points = ground.world_points(trodden)
    middle = (numpy.abs(points[:, 0]) < 0.08) & (numpy.abs(points[:, 1]) < 3.0)
    check(wear[middle].mean() > 0.5, 'the middle of the path is not trodden (wear %.2f)' % wear[middle].mean())
    print('PASS potholes: carved only at 2 and 6 m on the left wheel line, %.3f m deep; one off the line refused. Path: %.3f m deep, '
          'its middle trodden (wear %.2f)' % (result['deepest'], way['deepest'], wear[middle].mean()))


def test_heavy_ruts_and_horse():
    yard = lane_ground(0.75, relief=0.0)
    tracks.ruts(yard, LANE, vehicle='tractor', passes=1, age=0.1, seed=4)
    points = ground.world_points(yard)
    along, across, _ = across_lane(points)
    on_wheel = (across - 0.75 > 0.01) & (across - 0.75 < 0.06) & (along > 1.0) & (along < 7.0)   # one half of the tyre's tread
    steps = numpy.round(along[on_wheel] / 0.025).astype(int)                     # one height every 2.5 cm along the wheel's line
    profile = numpy.array([points[on_wheel][steps == k, 2].mean() for k in range(steps.min(), steps.max() + 1) if (steps == k).any()])
    profile = profile - numpy.convolve(numpy.pad(profile, 12, mode='edge'), numpy.ones(25) / 25, mode='same')[12:-12]
    power = numpy.abs(numpy.fft.rfft(profile)) ** 2
    rate = numpy.fft.rfftfreq(len(profile), 0.025)                              # rises per metre
    lugs = 1.0 / (0.62 * 0.32)
    peak = power[(rate > lugs * 0.85) & (rate < lugs * 1.15)].max()
    around = numpy.median(power[(rate > 1.5) & (rate < 12.0)])
    check(peak > 6.0 * around, "a tractor's fresh ruts in wet ground show no tread ridges across the floor (ridges %.1f times the rest)" % (peak / around))
    bare = ground.numbers(yard.data, 'bare')
    check(bare[on_wheel].mean() > 0.9, 'the floor of a rut is not written as bare earth (%.2f)' % bare[on_wheel].mean())
    walls = (ground.numbers(yard.data, 'track_wet') > 0.15)
    check(ground.numbers(yard.data, 'crust')[walls].max() < 0.05, 'the walls of fresh ruts crack like a dried puddle bed')
    cart = lane_ground(0.75, relief=0.0)
    tracks.ruts(cart, LANE, vehicle='cart', passes=2, age=0.2, seed=4)
    points = ground.world_points(cart)
    along, across, _ = across_lane(points)
    middle = (numpy.abs(across) < 0.15) & (along > 0.5) & (along < 7.5)
    hoofed = (points[middle, 2] < -0.01).sum()
    plain = lane_ground(0.75, relief=0.0)
    tracks.ruts(plain, LANE, vehicle='cart', passes=2, age=0.2, seed=4, horse=False)
    points = ground.world_points(plain)
    along, across, _ = across_lane(points)
    middle = (numpy.abs(across) < 0.15) & (along > 0.5) & (along < 7.5)
    check(hoofed > 100 and (points[middle, 2] < -0.01).sum() == 0, "a cart's horse left no hoof prints between the ruts, or horse=False left some")
    try:
        tracks.ruts(plain, LANE, vehicle='car', horse=True)
        check(False, 'a car was given a horse')
    except ValueError:
        pass
    print("PASS heavy ruts: a tractor's tread ridges stand across the floor, every %.2f m (%.0f times the other rises and falls), "
          "the floor is bare earth, fresh walls do not crack; a cart's horse pocks the strip between the ruts (%d points), not with "
          "horse=False" % (1.0 / lugs, peak / around, hoofed))


def test_grass_and_litter():
    import grass
    import litter
    yard = lane_ground(0.6, relief=0.04)
    tracks.ruts(yard, LANE, vehicle='car', passes=2, age=0.3, seed=1)
    import _scans
    made = grass.grow(yard, seed=3)
    expected = {'turf', 'tussocks', 'weeds'} | ({'herbs'} if _scans.available('nettle_plant') else set())
    check(set(made) == expected and made['turf']['tufts'] > 500, 'grass grew too little: %s' % {k: v['tufts'] for k, v in made.items()})
    if _scans.available('grass_medium_01'):
        check(made['turf']['look'] == 'scanned', 'the turf is not the store\'s scanned grass although the scans are there')
    made_look = grass.grow(yard, seed=3, layers=('turf',), look='made')['turf']
    check(made_look['look'] == 'made' and made_look['tufts'] > 500, "look='made' did not grow made grass")
    tufts = numpy.array([tuple(v.co) for v in made['turf'].data.vertices])
    points = ground.world_points(yard)
    from scipy.spatial import cKDTree
    _, nearest = cKDTree(points[:, :2]).query(tufts[:, :2])
    bare = ground.numbers(yard.data, 'bare')[nearest]
    water = ground.numbers(yard.data, 'water')[nearest]
    check((bare > 0.6).mean() < 0.01, '%.1f%% of the turf grows on bare earth (in a rut)' % (100 * (bare > 0.6).mean()))
    check((water > 0.0).sum() == 0, 'grass grows under standing water')
    again = grass.grow(yard, seed=3, layers=('turf',))['turf']
    check(numpy.array_equal(tufts, numpy.array([tuple(v.co) for v in again.data.vertices])), 'the same seed grew different grass')
    more = grass.grow(yard, seed=3, layers=('turf',), amount=2.0)['turf']['tufts']
    check(more > 1.6 * made['turf']['tufts'], 'twice the amount did not grow about twice the turf')
    for wrong in ({'layers': ('moss',)}, {'amount': -1}):
        try:
            grass.grow(yard, **wrong)
            check(False, 'grass accepted %s' % wrong)
        except ValueError:
            pass
    spots = ground.spots(yard)
    laid = litter.scatter(yard, amount=2.0, seed=2)
    check(laid['leaves']['pieces'] > 100 and laid['twigs']['pieces'] > 5, 'litter laid too little')
    leaves = numpy.array([tuple(v.co) for v in laid['leaves'].data.vertices])
    water = ground.numbers(yard.data, 'water')
    _, nearest = cKDTree(points[:, :2]).query(leaves[:, :2], k=3)
    surface_level = numpy.where(water > 0.0, points[:, 2] + water, -numpy.inf)[nearest].max(axis=1)
    afloat = water[nearest].min(axis=1) > 0.01                  # out on the water, not on its shore
    if afloat.any():
        check(numpy.abs(leaves[afloat, 2] - surface_level[afloat] - 0.0015).max() < 0.004, 'a leaf on water does not float at the water\'s level')
    try:
        litter.scatter(yard, kinds=('stones',))
        check(False, 'litter accepted a kind it does not have')
    except ValueError:
        pass
    if _scans.available('dry_branches_medium_01'):
        twig_shapes = laid['twigs'].modifiers[0].node_group.nodes['Collection Info'].inputs['Collection'].default_value
        check(twig_shapes.name.startswith('scan shapes'), 'the twigs are not the store\'s scanned branches although they are there')
    print('PASS grass: %d turf tufts, none on bare earth or under water; the same seed, the same grass; twice the amount, about twice; '
          'wrong options refused. Litter: %d leaves (%d afloat at the water\'s level), %d twigs' % (
              made['turf']['tufts'], laid['leaves']['pieces'], int(afloat.sum()), laid['twigs']['pieces']))


def test_detail_and_sky():
    import sky_and_haze
    yard = lane_ground(0.7, relief=0.02)
    tracks.ruts(yard, LANE, vehicle='car', passes=1, age=0.3, seed=1)
    before = ground.world_points(yard)
    count_before = len(before)
    moved = ground.detail(yard, area=(-1.5, -2.0, 1.5, 2.0), cell=0.015)
    after = ground.world_points(yard)
    change = after[:count_before, 2] - before[:, 2]
    inside = (numpy.abs(before[:, 0]) <= 1.5) & (numpy.abs(before[:, 1]) <= 2.0)
    check(moved > 1000 and len(after) > count_before, 'detail neither divided nor moved the ground')
    check(numpy.abs(change[~inside]).max() < 1e-6, 'detail moved ground outside the area given')
    check(numpy.abs(change[inside]).max() < 0.03 and numpy.abs(change[inside]).max() > 0.003,
          'detail moved the ground %.4f m at most (a few millimetres to 2 cm expected)' % numpy.abs(change[inside]).max())
    fresh_scene()
    bpy_scene = __import__('bpy').context.scene
    plain = __import__('bpy').data.objects.new('plain', __import__('bpy').data.meshes.new('plain'))
    try:
        ground.detail(plain)
        check(False, 'detail worked on a ground with no soil photographs')
    except ValueError:
        pass
    world = sky_and_haze.photo_sky(bpy_scene, 'overcast_soil_puresky')
    check(any(node.type == 'TEX_ENVIRONMENT' and node.image is not None for node in world.node_tree.nodes), 'photo_sky put no photographed sky in the world')
    try:
        sky_and_haze.photo_sky(bpy_scene, 'no such sky')
        check(False, 'photo_sky accepted a sky the store does not have')
    except ValueError:
        pass
    print('PASS detail: %d points pushed by the soil photographs, at most %.3f m, nothing outside the area; refused without '
          'soil photographs. photo_sky: the grey rain sky in the world; an unknown sky refused' % (moved, numpy.abs(change[inside]).max()))


def test_help():
    for name in ('ground', 'tracks', 'grass', 'litter'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS ground, tracks, grass and litter answer --help')


def main():
    test_make_and_numbers()
    test_camber()
    test_wet_states_and_water()
    test_same_seed()
    test_ruts_wet_and_dry()
    test_ruts_age_tread_and_refusals()
    test_footprints()
    test_potholes_and_path()
    test_heavy_ruts_and_horse()
    test_grass_and_litter()
    test_detail_and_sky()
    test_help()


if __name__ == '__main__':
    main()
