"""
What this file does: the store tools' tests for the boards, stone, puddle and stone grain tools (test_store_tools.py
runs it): each, run on a small scene, makes what it says.
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


def test_walkway_corner():
    fresh_scene()
    import lay_walkway
    from mathutils import Vector
    line = [(0.0, 0.0, 0.0), (0.0, 4.0, 0.0), (4.0, 4.0, 0.0)]
    boards = lay_walkway.lay(line, seed=1)[0]
    vertices = [v.co for v in boards.data.vertices]
    worst = 0.0
    for b in range(len(vertices) // 8):
        centre = sum(vertices[8 * b: 8 * b + 8], Vector()) / 8
        best = 1e9
        for a, c in zip(line, line[1:]):
            a, c = Vector(a), Vector(c)
            t = max(0.0, min(1.0, (centre - a).dot(c - a) / (c - a).length_squared))
            point = a + (c - a) * t
            best = min(best, Vector((centre.x - point.x, centre.y - point.y)).length)
        worst = max(worst, best)
    check(worst < 0.15, 'at a corner a board lies %.2f m off the line' % worst)
    print('PASS lay_walkway keeps a sharp corner: no board more than %.2f m off the line' % worst)


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
    water, _film = puddle.make((0.2, 0.5, 0.0), size=(1.4, 0.8), level=0.002, seed=1)
    heights = [(water.matrix_world @ v.co).z for v in water.data.vertices]
    check(abs(sum(heights) / len(heights) - 0.002) < 0.002, 'the water is not at the level asked for (%.4f)' % (sum(heights) / len(heights)))
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
    world = sky_and_haze.sky(scene)
    check(scene.world is world and world.node_tree.nodes.get('Background') is not None, 'the sky did not become the world')
    box = sky_and_haze.haze(low=(-20.0, -5.0, 0.0), high=(20.0, 60.0, 15.0))
    check(box.data.materials[0].node_tree.nodes.get('Volume Scatter') is not None, 'the haze box has no scattering air')
    check(abs(box.location.z - 7.5) < 1e-6 and abs(box.dimensions.z - 15.0) < 1e-6, 'the haze box is not where it was asked to be')
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
    facing = 0
    for polygon in smoke.data.polygons:
        to_viewer = (viewer - smoke.matrix_world @ polygon.center).normalized()
        if abs(polygon.normal.dot(to_viewer)) > 0.7:
            facing += 1
    check(facing >= 0.8 * len(smoke.data.polygons), 'only %d of %d smoke faces turn to the viewer' % (facing, len(smoke.data.polygons)))
    check(smoke.data.materials[0].name == 'MADE • smoke ribbon', 'the smoke has the wrong material')
    print('PASS smoke_ribbon: %d of %d faces turned to the viewer, its material reads the ribbon\'s UV map' % (facing, len(smoke.data.polygons)))


def main():
    test_sky_and_haze()
    test_smoke_ribbon()
    test_walkway_corner()
    test_puddle_on_setts()
    test_catalogue_help()
    names = store.names('tools')
    for name, test in (('lay_boards', test_boards), ('lay_stone', test_stone), ('puddle', test_puddle), ('stone_grain', test_grain)):
        if name in names:
            test()
        else:
            print('note: no %s tool in the store' % name)
