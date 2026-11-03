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


def main():
    names = store.names('tools')
    for name, test in (('lay_boards', test_boards), ('lay_stone', test_stone), ('puddle', test_puddle), ('stone_grain', test_grain)):
        if name in names:
            test()
        else:
            print('note: no %s tool in the store' % name)
