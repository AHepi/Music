"""
What this file does: the store tools' tests for the boards, stone, puddle, stone grain, sky and haze, smoke ribbon,
railing, stain and stones tools (test_store_tools.py runs it): each, run on a small scene, makes what it says.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import store  # noqa: E402


def box(name, size, location):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def numbers(obj, name):
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no %r' % (obj.name, name))
    data = [0.0] * len(attribute.data)
    attribute.data.foreach_get('value', data)
    return data


def test_boards():
    fresh_scene()
    import lay_boards
    hut = box('hut', (4.0, 3.0, 2.4), (0.0, 0.0, 1.2))
    made = lay_boards.lay(hut, openings=[('front', 'door', 1.55, 0.0, 0.9, 1.95), ('front', 'window', 0.4, 0.9, 0.8, 0.9),
                                         ('back', 'window', 1.6, 0.9, 0.8, 0.9)], eaves='pitched', seed=4)
    boards, roof = made['boards'], made['roof']
    check(boards is not None and len(boards.data.polygons) > 800, 'lay_boards laid too little: %s' % (len(boards.data.polygons) if boards else None))
    tones = numbers(boards, 'board_tone')
    check(min(tones) >= 0.0 and max(tones) <= 1.0 and max(tones) - min(tones) > 0.2, 'board_tone does not vary from board to board')
    check(roof is not None and len(roof.data.polygons) > 20, 'eaves made no roof')
    low = min((roof.matrix_world @ v.co).x for v in roof.data.vertices)
    check(low < -2.0 - 0.25, 'the roof does not overhang the wall (its edge at x = %.2f)' % low)
    check(all(tuple(o.scale) == (1.0, 1.0, 1.0) for o in (boards, roof)), 'a boards object is scaled')
    print('PASS lay_boards: %d faces of boards, the roof overhangs the wall by %.2f m' % (len(boards.data.polygons), -2.0 - low))


def test_stone():
    fresh_scene()
    import lay_stone
    wall = box('wall', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4))
    stonework = lay_stone.lay(wall, openings=[('front', 'door', 0.3, 0.0, 0.9, 2.0), ('front', 'window', 1.7, 1.0, 0.8, 1.0)], seed=2)
    stonework = stonework if not isinstance(stonework, (list, tuple, dict)) else (list(stonework.values()) if isinstance(stonework, dict) else stonework)[0]
    check(len(stonework.data.polygons) > 600, 'lay_stone laid too little: %d faces' % len(stonework.data.polygons))
    top = max((stonework.matrix_world @ v.co).z for v in stonework.data.vertices)
    foot = min((stonework.matrix_world @ v.co).z for v in stonework.data.vertices)
    check(foot < 0.02 and top > 2.6, 'the courses do not run from the foot (%.2f) to the top (%.2f)' % (foot, top))
    print('PASS lay_stone: %d faces of stonework from z = %.2f to %.2f' % (len(stonework.data.polygons), foot, top))


def test_puddle():
    fresh_scene()
    import puddle
    bpy.ops.mesh.primitive_plane_add(size=6.0)
    ground = bpy.context.object
    water, film = puddle.make((0.5, 0.5, 0.0), size=(2.5, 0.6), turn=30, ground=ground, seed=2)
    shallow, dry = numbers(water, 'shallow'), numbers(film, 'dry')
    check(min(shallow) < 0.05 and max(shallow) > 0.95, 'shallow runs %.2f to %.2f, not 0 to 1' % (min(shallow), max(shallow)))
    check(min(dry) < 0.05 and max(dry) > 0.95, 'dry runs %.2f to %.2f, not 0 to 1' % (min(dry), max(dry)))
    check(water.data.materials[0].name == 'MADE • puddle water' and film.data.materials[0].name == 'MADE • wet ground film', 'puddle materials: %s, %s' % (water.data.materials[0].name, film.data.materials[0].name))
    xs = [(water.matrix_world @ v.co) for v in water.data.vertices]
    far = max(xs, key=lambda p: (p - xs[0]).length)          # the far end from any point, then the far end from that
    span = max((p - far).length for p in xs)
    check(1.6 < span < 3.2, 'a 2.5 m puddle spans %.2f m' % span)
    check(max(p.z for p in xs) < 0.05, 'the water floats above the ground')
    print('PASS puddle: water and wet film made where asked, shallow and dry run 0 to 1, %.2f m long' % span)


def test_grain():
    fresh_scene()
    import stone_grain
    material = store.material('Hand-painted sandstone • shade 03')
    count = len(material.node_tree.nodes)
    check(stone_grain.add(material) is True, 'stone grain was not added')
    check(len(material.node_tree.nodes) > count, 'stone grain added no nodes')
    check(stone_grain.add(material) is False, 'stone grain was added twice to the same material')
    print('PASS stone_grain: added once to a stone material, refused the second time')


def _plan_overlap(a, b):
    """Two boards' outlines seen from above (each four corners in order round it) overlap: no line between them."""
    for outline in (a, b):
        for i in range(4):
            edge = outline[(i + 1) % 4] - outline[i]
            axis = (-edge.y, edge.x)
            span_a = [axis[0] * p.x + axis[1] * p.y for p in a]
            span_b = [axis[0] * p.x + axis[1] * p.y for p in b]
            if max(span_a) <= min(span_b) + 1e-4 or max(span_b) <= min(span_a) + 1e-4:
                return False
    return True


def test_walkway_corner():
    import math as maths
    import lay_walkway
    from mathutils import Vector
    for turn in (45, 90):
        fresh_scene()
        angle = maths.radians(turn)
        line = [(0.0, 0.0, 0.0), (0.0, 4.0, 0.0), (4.0 * maths.sin(angle), 4.0 + 4.0 * maths.cos(angle), 0.0)]
        boards = lay_walkway.lay(line, seed=1, missing=0.0)[0]
        vertices = [v.co.copy() for v in boards.data.vertices]
        outlines = []
        for b in range(len(vertices) // 8):
            bottom = vertices[8 * b: 8 * b + 4]                      # corners 0, 1, 3, 2 go round the board
            outlines.append([Vector((p.x, p.y)) for p in (bottom[0], bottom[1], bottom[3], bottom[2])])
        crossing = sum(1 for i in range(len(outlines)) for j in range(i + 1, len(outlines)) if _plan_overlap(outlines[i], outlines[j]))
        check(crossing == 0, 'at a %d degree corner %d pairs of boards lie through each other' % (turn, crossing))
        path = lay_walkway.Path(lay_walkway.line_points(line))
        longest = bare = 0.0
        distance = 0.0
        while distance <= path.total:
            point = path.at(distance)
            covered = boards.ray_cast(Vector((point.x, point.y, 1.0)), Vector((0.0, 0.0, -1.0)))[0]
            bare = 0.0 if covered else bare + 0.01
            longest = max(longest, bare)
            distance += 0.01
        check(longest < 0.25, 'at a %d degree corner the middle of the way is bare for %.2f m' % (turn, longest))
        print('PASS lay_walkway at a %d degree corner: no boards through each other, the longest bare stretch %.2f m' % (turn, longest))


def test_puddle_on_setts():
    fresh_scene()
    import lay_cobbles
    import puddle
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    road = bpy.context.object
    road.scale = (3.0, 6.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    lay_cobbles.lay_setts(road, seed=1)
    bed = max((road.matrix_world @ v.co).z for v in road.data.vertices)
    check(bed < -0.1, 'the bed was not lowered under the setts (it is at %.3f)' % bed)
    setts = bpy.data.objects['setts']
    check(abs(setts['top_height']) < 1e-6, 'the setts do not record their top height (%s)' % setts.get('top_height'))
    for level in (0.0, 0.002):
        water, _film = puddle.make((0.2, 0.5, 0.0), size=(1.4, 0.8), level=level, seed=1)
        bpy.context.view_layer.update()
        heights = [(water.matrix_world @ v.co).z for v in water.data.vertices]
        mean = sum(heights) / len(heights)
        check(abs(mean - level) < 0.0008, 'water asked for at %.3f lies at %.4f' % (level, mean))
    try:
        puddle.make((0.2, 0.5, 0.0), size=(1.0, 0.6), ground=road, seed=1)
        check(False, 'a puddle draped on the cobbled road (now the bed under the stones) was not refused')
    except ValueError as problem:
        check('level' in str(problem), 'the refusal does not point to level: %s' % problem)
    try:
        puddle.make((0.2, 0.5, 0.0), size=(1.0, 0.6), ground=bpy.data.objects['setts'], seed=1)
        check(False, 'a puddle given the setts as ground did not say why it cannot drape on them')
    except ValueError as problem:
        check('level' in str(problem), 'the puddle error does not point to level: %s' % problem)
    print('PASS setts lie with their tops at the road height, the bed %.3f m below; a puddle among them stands at the level asked for' % -bed)


def test_catalogue_help():
    import hashlib
    import subprocess
    from _common import STORE, TOOLS
    page = os.path.join(STORE, 'Store.md')
    before = hashlib.sha256(open(page, 'rb').read()).hexdigest()
    result = subprocess.run([sys.executable, os.path.join(TOOLS, 'catalogue.py'), '--help'], capture_output=True, text=True, timeout=300)
    check(result.returncode == 0 and 'usage' in result.stdout, 'catalogue.py --help failed')
    check(hashlib.sha256(open(page, 'rb').read()).hexdigest() == before, 'catalogue.py --help changed Store.md')
    print('PASS catalogue.py --help prints its help and changes nothing')


def test_sky_and_haze():
    scene = fresh_scene()
    import sky_and_haze
    from mathutils import Vector
    world = sky_and_haze.sky(scene)
    check(scene.world is world and world.node_tree.nodes.get('Background') is not None, 'the sky did not become the world')
    box = sky_and_haze.haze(low=(-20.0, -5.0, 0.0), high=(20.0, 60.0, 15.0))
    check(box.data.materials[0].node_tree.nodes.get('Volume Scatter') is not None, 'the haze box has no scattering air')
    check((box.location - Vector((0.0, 27.5, 7.5))).length < 1e-6 and (box.dimensions - Vector((40.0, 65.0, 15.0))).length < 1e-6,
          'the haze box is not where it was asked to be (%s, %s)' % (tuple(box.location), tuple(box.dimensions)))
    try:
        sky_and_haze.haze(low=(0, 0, 10), high=(5, 5, 0))
        check(False, 'a haze box with its corners the wrong way round was accepted')
    except ValueError:
        pass
    print('PASS sky_and_haze: the dusk sky becomes the world; the haze fills the box asked for, and only that')


def test_smoke_ribbon():
    fresh_scene()
    import smoke_ribbon
    from mathutils import Vector
    viewer = Vector((0.0, -10.0, 1.6))
    smoke = smoke_ribbon.make(start=(0.0, 20.0, 6.0), facing=viewer, drift=(1.0, 0.0), rise=10.0, seed=1)
    check(smoke.data.uv_layers.get('UVMap') is not None, 'the smoke ribbon has no UV map for its material')
    first = (smoke.data.vertices[0].co + smoke.data.vertices[1].co) / 2
    check((first - Vector((0.0, 20.0, 6.0))).length < 0.01, 'the smoke does not start at the chimney (%s)' % (tuple(first),))
    bottom = (smoke.data.vertices[0].co - smoke.data.vertices[1].co).length
    top = (smoke.data.vertices[-1].co - smoke.data.vertices[-2].co).length
    check(top > 3 * bottom, 'the smoke does not widen as it rises (%.2f m to %.2f m)' % (bottom, top))
    facing = 0
    for polygon in smoke.data.polygons:
        to_viewer = (viewer - smoke.matrix_world @ polygon.center).normalized()
        if abs(polygon.normal.dot(to_viewer)) > 0.5:
            facing += 1
    check(facing >= 0.8 * len(smoke.data.polygons), 'only %d of %d smoke faces turn to the viewer' % (facing, len(smoke.data.polygons)))
    check(smoke.data.materials[0].name == 'MADE • smoke ribbon', 'the smoke has the wrong material')
    print('PASS smoke_ribbon: starts at the chimney, widens from %.1f to %.1f m, %d of %d faces turned to the viewer' % (bottom, top, facing, len(smoke.data.polygons)))


def test_railing():
    fresh_scene()
    import lay_railing
    from mathutils import Vector
    made = lay_railing.lay([(-3.0, 0.0, 0.0), (3.0, 0.0, 0.0), (3.0, 4.0, 0.0)], height=1.1, spacing=0.14, plinth=0.15, seed=1)
    bars = made['railing bars']
    count = bars['railing_bars']
    # 6 m + 4 m of line at 0.14 m, less a bar at each of the posts: about 65 bars
    check(55 <= count <= 75, 'a 10 m railing at 0.14 m spacing has %d bars' % count)
    check(len(bars.data.polygons) == count * 13, '%d bars but %d faces (13 each)' % (count, len(bars.data.polygons)))
    points = [bars.matrix_world @ v.co for v in bars.data.vertices]
    check(abs(min(p.z for p in points) - 0.15) < 0.01, 'the bars do not stand on the plinth top (lowest point z = %.3f)' % min(p.z for p in points))
    check(abs(max(p.z for p in points) - 1.25) < 0.02, 'the spear points are not at plinth + height (highest z = %.3f)' % max(p.z for p in points))
    check(bars['railing_posts'] >= 4, 'too few posts: %d' % bars['railing_posts'])
    check('railing plinth' in made and 'railing rust' in made, 'no plinth or no rust made')
    fade = numbers(made['railing rust'], 'fade')
    check(min(fade) < 0.01 and max(fade) > 0.99, 'the rust fade runs %.2f to %.2f' % (min(fade), max(fade)))
    check(made['railing rust'].data.materials[0].name == 'MADE • stain rust', 'the rust has the wrong material')
    # the gate: two leaves hung at +-width/2, each swung open by the angle asked (the left leaf's far end goes to +Y)
    gate = lay_railing.gate((0.0, 0.0, 0.0), width=1.2, open_angle=35.0, seed=2)
    left, right = gate['gate left leaf'], gate['gate right leaf']
    check((left.location - Vector((-0.6, 0.0, 0.0))).length < 1e-6 and (right.location - Vector((0.6, 0.0, 0.0))).length < 1e-6,
          'the hinges are not at the opening\'s sides (%s, %s)' % (tuple(left.location), tuple(right.location)))
    import math
    far_left = max((left.matrix_world @ v.co for v in left.data.vertices), key=lambda p: p.x)
    expected = Vector((-0.6, 0.0, 0.0)) + Vector((math.cos(math.radians(35.0)), math.sin(math.radians(35.0)), 0.0)) * left['gate_leaf_width']
    check((far_left.xy - expected.xy).length < 0.03, 'the left leaf\'s far end is at %s, not swung 35 degrees to %s' % (tuple(far_left.xy), tuple(expected.xy)))
    far_right = min((right.matrix_world @ v.co for v in right.data.vertices), key=lambda p: p.x)
    check(far_right.y > 0.3, 'the right leaf did not swing inwards (its far end at y = %.2f)' % far_right.y)
    closed = lay_railing.gate((5.0, 0.0, 0.0), width=1.2, open_angle=0.0, seed=2)
    shut = max((closed['gate left leaf'].matrix_world @ v.co for v in closed['gate left leaf'].data.vertices), key=lambda p: p.x)
    check(abs(shut.y) < 0.03 and abs(shut.x - (4.4 + closed['gate left leaf']['gate_leaf_width'])) < 0.03, 'a shut leaf does not lie along the opening')
    check(all(k in gate for k in ('gate left pier', 'gate right pier', 'gate left pier cap')), 'the piers were not made')
    pier = gate['gate left pier']
    top = max((pier.matrix_world @ v.co).z for v in pier.data.vertices)
    check(1.4 < top < 1.7, 'the pier body is %.2f m tall' % top)
    print('PASS lay_railing: %d bars on a plinth with rust at their feet; the gate leaves hang at the piers and swing 35 degrees' % count)


def test_stain():
    fresh_scene()
    import stain
    from mathutils import Vector
    wall = box('wall', (6.0, 0.5, 3.0), (1.0, 2.0, 1.5))        # front face at y = 1.75, left end (seen from -Y) at x = -2
    soot = stain.on_wall(wall, 'front', 1.0, 2.0, 0.5, 1.5, kind='soot', strong_at='top', seed=1)
    points = [soot.matrix_world @ v.co for v in soot.data.vertices]
    ys = [p.y for p in points]
    check(1.735 <= min(ys) and max(ys) <= 1.75, 'the soot plane is not just in front of the front face (y %.3f to %.3f; the face is at 1.75)' % (min(ys), max(ys)))
    check(abs(min(p.x for p in points) - (-1.0)) < 1e-6 and abs(max(p.x for p in points) - 0.0) < 1e-6, 'the soot plane does not run 1 to 2 m from the left end (x %.2f to %.2f)' % (min(p.x for p in points), max(p.x for p in points)))
    check(abs(min(p.z for p in points) - 0.5) < 1e-6 and abs(max(p.z for p in points) - 1.5) < 1e-6, 'the soot plane does not stand 0.5 to 1.5 m up')
    fade = numbers(soot, 'fade')
    check(min(fade) >= 0.0 and max(fade) <= 1.0 and min(fade) < 0.05 and max(fade) > 0.95, 'fade runs %.2f to %.2f, not 0 to 1' % (min(fade), max(fade)))
    top_fade = [f for f, p in zip(fade, points) if p.z > 1.49]
    foot_fade = [f for f, p in zip(fade, points) if p.z < 0.51]
    check(min(top_fade) < 0.05 and min(foot_fade) > 0.95, 'strong_at top: the top should be strongest (fade %.2f) and the foot gone (%.2f)' % (min(top_fade), min(foot_fade)))
    check(soot.data.materials[0].name == 'MADE • stain soot' and not soot.visible_shadow, 'the soot plane has the wrong material or casts a shadow')
    # the other faces: right (+X, at x = 4; its left end seen from +X is at y = -0.25... the wall's low y)
    right = stain.on_wall(wall, 'right', 0.0, 0.5, 0.0, 1.0, kind='damp', strong_at='bottom')
    xs = [(right.matrix_world @ v.co).x for v in right.data.vertices]
    check(4.0 <= min(xs) and max(xs) <= 4.015, 'the right-face plane is not just off the right face (x %.3f to %.3f)' % (min(xs), max(xs)))
    back = stain.on_wall(wall, 'back', 0.0, 1.0, 0.0, 1.0, kind='rust', strong_at='top')
    ys = [(back.matrix_world @ v.co).y for v in back.data.vertices]
    check(2.25 <= min(ys) and max(ys) <= 2.265, 'the back-face plane is not just off the back face')
    bxs = [(back.matrix_world @ v.co).x for v in back.data.vertices]
    check(abs(max(bxs) - 4.0) < 1e-6, 'from the back, the left end is the +X end (plane x up to %.2f)' % max(bxs))
    # a ground smear draped on a sloping ground
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0.0, -3.0, 0.0), rotation=(0.1, 0.0, 0.0))
    ground = bpy.context.object
    smear = stain.on_ground((0.0, -3.0, 0.0), size=(0.6, 0.4), kind='mud', turn=20, ground=ground, seed=3)
    spots = [smear.matrix_world @ v.co for v in smear.data.vertices]
    rising = max(spots, key=lambda p: p.y).z - min(spots, key=lambda p: p.y).z
    check(0.04 < rising < 0.14, 'the smear does not follow the sloping ground (its +Y side is %.3f m higher; the slope gives about 0.08)' % rising)
    sfade = numbers(smear, 'fade')
    check(abs(min(sfade) - 0.3) < 0.01 and max(sfade) > 0.99, 'the smear fade runs %.2f to %.2f (strength 0.7: 0.3 to 1)' % (min(sfade), max(sfade)))
    span = max((p - spots[0]).length for p in spots)
    check(0.6 < span < 1.0, 'a 0.6 m half-length smear spans %.2f m' % span)
    try:
        stain.on_wall(wall, 'top', 0, 1, 0, 1)
        check(False, "a side named 'top' was accepted")
    except ValueError:
        pass
    print('PASS stain: planes 4 mm off the front, right and back faces where asked, fade 0 at the strong end to 1; the ground smear drapes onto the slope')


def test_stones():
    """The stones tool on a small wet ground, measured on the copies it draws: counts grow with the amount; no stone
    floats; more grit in the dips than on the crowns; only within the area given; the same seed, the same stones; each
    stone carries the ground's wetness; settle puts a stone back on ground lowered 5 cm under it."""
    import numpy
    import ground
    import stones
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    def points(obj):
        co = numpy.zeros(len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get('co', co)
        return co.reshape(-1, 3)

    def surface_of(yard):
        yard.data.calc_loop_triangles()                     # the triangles Blender draws
        return BVHTree.FromPolygons(ground.world_points(yard).tolist(), [tuple(t.vertices) for t in yard.data.loop_triangles], all_triangles=True)

    def height(tree, x, y):
        return tree.ray_cast(Vector((x, y, 5.0)), Vector((0.0, 0.0, -1.0)))[0].z

    def under(yard, tree, xy, values):
        """The ground's number straight under each place: on the triangle hit, weighted by nearness to its corners."""
        corners = ground.world_points(yard)
        found = []
        for x, y in xy:
            triangle = yard.data.loop_triangles[tree.ray_cast(Vector((x, y, 5.0)), Vector((0.0, 0.0, -1.0)))[2]].vertices
            (ax, ay), (bx, by), (cx, cy) = (corners[i, :2] for i in triangle)
            area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
            wb = ((x - ax) * (cy - ay) - (cx - ax) * (y - ay)) / area
            wc = ((bx - ax) * (y - ay) - (x - ax) * (by - ay)) / area
            found.append(values[triangle[0]] * (1 - wb - wc) + values[triangle[1]] * wb + values[triangle[2]] * wc)
        return numpy.array(found)

    def copies(obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        return [(numpy.array(i.matrix_world), i.instance_object.original) for i in depsgraph.object_instances
                if i.is_instance and i.parent is not None and i.parent.original == obj]

    fresh_scene()
    yard = ground.make(size=(4.0, 4.0), relief=0.08, seed=3)
    ground.wet(yard, 0.6)
    laid = stones.scatter(yard, seed=2)
    check(sorted(laid) == ['grit', 'pebbles', 'rocks'], 'scatter made %s, not rocks, pebbles and grit' % sorted(laid))
    check(all(obj.name == 'stones ' + layer for layer, obj in laid.items()), 'the stone objects are named %s' % [o.name for o in laid.values()])
    check(laid['grit']['stones'] > laid['pebbles']['stones'] > laid['rocks']['stones'] > 0,
          'more grit than pebbles than rocks: %s' % {k: o['stones'] for k, o in laid.items()})
    tree = surface_of(yard)
    ground_wet = ground.numbers(yard.data, 'wetness')
    for layer, obj in laid.items():
        drawn = copies(obj)
        check(len(drawn) == obj['stones'] == len(obj.data.vertices), '%s: %d copies drawn, %d points, count %d' % (layer, len(drawn), len(obj.data.vertices), obj['stones']))
        check(all(shape.data.materials[0].name == stones.MATERIAL for _, shape in drawn[:50]), '%s are not in %s' % (layer, stones.MATERIAL))
        floating = 0
        for matrix, shape in drawn:
            corners = numpy.array([v.co[:] for v in shape.data.vertices])
            lowest = (corners @ matrix[2, :3] + matrix[2, 3]).min()
            if lowest >= height(tree, matrix[0, 3], matrix[1, 3]):
                floating += 1
        check(floating == 0, '%d of the %s float: their lowest point is not under the ground at their middle' % (floating, layer))
        wet = numpy.zeros(len(obj.data.vertices))
        obj.data.attributes['wetness'].data.foreach_get('value', wet)
        check(numpy.abs(wet - under(yard, tree, points(obj)[:, :2], ground_wet)).max() < 0.01, '%s do not carry the wetness of the ground under them' % layer)
    # more grit per square metre in the dips than on the crowns
    hollow, areas = ground.numbers(yard.data, 'hollow'), ground.point_areas(yard.data)
    ground_xy = ground.world_points(yard)[:, :2]
    from scipy.spatial import cKDTree
    nearest = cKDTree(ground_xy).query(points(laid['grit'])[:, :2])[1]
    dips, crowns = hollow >= 0.5, hollow <= 0.02
    in_dips, on_crowns = dips[nearest].sum() / areas[dips].sum(), crowns[nearest].sum() / areas[crowns].sum()
    check(in_dips > on_crowns, 'where=hollows: %.0f grit per square metre in the dips, not more than %.0f on the crowns' % (in_dips, on_crowns))
    # counts grow with the amount
    counts = []
    for amount in (0.5, 1.0, 2.0):
        holder = bpy.data.collections.new('amount %s' % amount)
        bpy.context.scene.collection.children.link(holder)
        counts.append({k: o['stones'] for k, o in stones.scatter(yard, amount=amount, seed=2, collection=holder).items()})
    for layer in ('rocks', 'pebbles', 'grit'):
        check(counts[0][layer] < counts[1][layer] < counts[2][layer], '%s at amount 0.5, 1, 2: %s' % (layer, [c[layer] for c in counts]))
    # the same seed, the same stones
    again = stones.scatter(yard, seed=2, collection=bpy.data.collections.new('again'))
    check(all(numpy.allclose(points(laid[k]), points(again[k])) for k in laid), 'the same seed laid different stones')
    # only within the area given: a rectangle, a polygon, a function
    box = stones.scatter(yard, area=(-1.5, -1.0, 0.5, 0.8), seed=3, layers=('pebbles', 'grit'))
    for obj in box.values():
        p = points(obj)
        check(len(p) and p[:, 0].min() >= -1.5 and p[:, 0].max() <= 0.5 and p[:, 1].min() >= -1.0 and p[:, 1].max() <= 0.8,
              'stones laid outside the rectangle asked for (x %.2f to %.2f, y %.2f to %.2f)' % (p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()))
    triangle = stones.scatter(yard, area=[(0.0, 0.0), (1.5, 0.0), (0.0, 1.5)], seed=3, layers=('grit',))['grit']
    p = points(triangle)
    check(len(p) and (p[:, 0] >= 0).all() and (p[:, 1] >= 0).all() and (p[:, 0] + p[:, 1] <= 1.5 + 1e-9).all(), 'grit laid outside the triangle asked for')
    band = stones.scatter(yard, area=lambda xy: (numpy.abs(xy[:, 0] - 1.0) < 0.1).astype(float), seed=3, layers=('grit',), amount=2.0)['grit']
    p = points(band)
    check(len(p) > 20 and (numpy.abs(p[:, 0] - 1.0) < 0.1).all(), 'grit laid outside the band an area function asked for (%d stones)' % len(p))
    # settle: the ground lowered 5 cm under a rock; the rock goes down with it, as deep in the soil as it was
    rocks = laid['rocks']
    before = points(rocks)
    pick = int(numpy.argmin(numpy.abs(before[:, 0]) + numpy.abs(before[:, 1])))
    centre = before[pick, :2]
    world = ground.world_points(yard)
    distance = numpy.linalg.norm(world[:, :2] - centre, axis=1)
    ground.set_world_heights(yard, world[:, 2] - 0.05 * numpy.clip((0.6 - distance) / 0.25, 0.0, 1.0))
    moved = stones.settle(yard, laid)
    after = points(rocks)
    drop = after[pick, 2] - before[pick, 2]
    check(moved == sum(o['stones'] for o in laid.values()), 'settle moved %d stones' % moved)
    check(abs(drop + 0.05) < 0.002, 'settle: a rock on ground lowered 5 cm went down %.4f m' % -drop)
    far = numpy.linalg.norm(before[:, :2] - centre, axis=1) > 0.7
    check(numpy.allclose(before[far], after[far], atol=1e-5), 'settle moved rocks whose ground did not move')
    for wrong in ({'layers': ('boulders',)}, {'where': 'everywhere'}):
        try:
            stones.scatter(yard, **wrong)
            check(False, 'scatter accepted %s' % wrong)
        except ValueError:
            pass
    print('PASS stones: %d rocks, %d pebbles, %d grit on 16 square metres, none floating; grit %.0f per square metre in the dips, '
          '%.0f on the crowns; only within the area given; same seed, same stones; settle drops a rock %.3f m with its ground'
          % (laid['rocks']['stones'], laid['pebbles']['stones'], laid['grit']['stones'], in_dips, on_crowns, -drop))


def main():
    test_stones()
    test_sky_and_haze()
    test_smoke_ribbon()
    test_railing()
    test_stain()
    test_walkway_corner()
    test_puddle_on_setts()
    test_catalogue_help()
    names = store.names('tools')
    for name, test in (('lay_boards', test_boards), ('lay_stone', test_stone), ('puddle', test_puddle), ('stone_grain', test_grain)):
        if name in names:
            test()
        else:
            print('note: no %s tool in the store' % name)
