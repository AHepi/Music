"""
What this file does: checks the garden things the Japanese garden's builders brought to the store (log 57) against what
their cards promise. The stone lantern: a Kasuga lantern 1.8 m tall and a low, broad yukimi on three legs; its fire box
open through its front window and its sun window and solid at the back corners; lit, a light inside the fire box that
the eye cannot see and paper that casts no shadow, unlit none; every stone its own part of the photographed rock, with
moss and rain streaks. The water basin: water standing below the rim inside the bowl for both stones, the stream from
the spout's mouth landing in that water, the front stone in front, the spout and ladle there only when asked. The jar:
1.0 times its card's height with its lid, open and dark inside without it, its painting placed by the seed. The clogs:
two boards on two teeth each, the tops pressed where the feet go, the thongs red unless asked, one tipped on its side
when scattered. The hanging lantern: its hook 0.8 m above its foot whatever its kind, lit inside with a hidden light or
dark. The bucket: every stave its own part of the photograph, the handle staves above the rim, the water below it. The
broom: leaning back towards +Y with its fan on the ground and spread along X, or lying flat. The same seed, the same
thing; a wrong choice refused.
    python3 tests/test_store_garden_things.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import store  # noqa: E402


def part(name, seed=0, **options):
    fresh_scene()
    root = store.add_part(name, seed=seed, **options)
    bpy.context.view_layer.update()
    objects = [o for o in root.children]
    return root, {o.name.split('.')[0]: o for o in objects}


def points(obj):
    co = numpy.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    matrix = numpy.array(obj.matrix_world)
    return co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def all_points(objects):
    return numpy.concatenate([points(o) for o in objects if o.type == 'MESH'])


def face_numbers(obj, name):
    attr = obj.data.attributes.get(name)
    if attr is None:
        return numpy.zeros(0)
    data = numpy.zeros(len(attr.data))
    attr.data.foreach_get('value', data)
    return data


def ray_hits(obj, origin, direction, reach):
    """Does a ray from origin (world) along direction meet obj's mesh within reach metres?"""
    inverse = obj.matrix_world.inverted()
    o = inverse @ Vector(origin)
    d = (inverse.to_3x3() @ Vector(direction)).normalized()
    hit, where, normal, index = obj.ray_cast(o, d, distance=reach)
    return hit


def refused(call):
    try:
        call()
    except ValueError:
        return True
    return False


def fingerprint(objects):
    return round(float(numpy.abs(all_points(objects)).sum()), 4)


def test_stone_lantern():
    root, objs = part('stone_lantern')
    stone, paper = objs['stone_lantern stone'], objs['stone_lantern paper']
    p = points(stone)
    tall = p[:, 2].max()
    check(1.7 < p[:, 2].max() < 1.9 and abs(p[:, 2].min()) < 0.02, 'the Kasuga lantern is %.2f m tall (1.7 to 1.9 asked)' % p[:, 2].max())
    check('stone_lantern light' not in objs, 'an unlit lantern has a light')
    pieces = len(set(numpy.round(face_numbers(stone, 'pp_piece'), 5)))
    check(pieces >= 6, 'the lantern\'s stones do not each carry their own pp_piece (%d different)' % pieces)
    mat = stone.data.materials[0]
    check(mat.get('pp_moss') and mat.get('pp_moss_of', '').find('weathered') >= 0 and 'dark_rock_02' in mat.name,
          'the lantern\'s stone is not the photographed rock with rain streaks and moss: %s' % mat.name)
    # the fire box: open through the front window and the sun window, solid at the back corners
    zc = 1.22
    check(not ray_hits(stone, (0, 0, zc), (0, -1, 0), 0.5), 'the front window of the fire box is not open')
    check(not ray_hits(stone, (0, 0, zc), (math.cos(math.radians(210)), math.sin(math.radians(210)), 0), 0.5), 'the sun window is not open')
    check(ray_hits(stone, (0, 0, zc), (math.cos(math.radians(150)), math.sin(math.radians(150)), 0), 0.5), 'the back corner of the fire box is not solid')
    check(paper.visible_shadow is False, 'the lantern\'s paper casts a shadow (the light inside would not get out)')
    q = points(paper)
    check(q[:, 2].min() > 1.08 and q[:, 2].max() < 1.36 and numpy.abs(q[:, :2]).max() < 0.16, 'the paper is not inside the fire box')
    root, objs = part('stone_lantern', lit=True)
    light = objs.get('stone_lantern light')
    check(light is not None and light.type == 'LIGHT' and light.data.energy > 5, 'a lit lantern has no light')
    where = light.matrix_world.translation
    check(math.hypot(where.x, where.y) < 0.1 and 1.1 < where.z < 1.34, 'the light is not inside the fire box (%.2f, %.2f, %.2f)' % tuple(where))
    check(light.visible_camera is False, 'the lantern\'s light can be seen by the eye')
    check(objs['stone_lantern paper'].data.materials[0].name == 'PART • garden: lantern paper, lit', 'a lit lantern\'s paper does not glow')
    root, objs = part('stone_lantern', kind='yukimi')
    p = points(objs['stone_lantern stone'])
    width = p[:, 0].max() - p[:, 0].min()
    check(p[:, 2].max() < 1.05 and width > 1.0, 'the yukimi should be low and broad: %.2f m tall, %.2f m across' % (p[:, 2].max(), width))
    feet = p[p[:, 2] < 0.01]
    angles = numpy.degrees(numpy.arctan2(feet[:, 1], feet[:, 0]))
    found = sum(1 for a in (-150, -30, 90) if (numpy.abs((angles - a + 180) % 360 - 180) < 20).any())
    check(found == 3, 'the yukimi does not stand on three legs (%d feet found)' % found)
    check(refused(lambda: part('stone_lantern', kind='oribe')), 'the lantern took a kind it does not have')
    a = fingerprint(part('stone_lantern', seed=3)[1].values())
    b = fingerprint(part('stone_lantern', seed=3)[1].values())
    check(abs(a - b) < 1e-4, 'the same seed made a different lantern')
    print('PASS stone_lantern: Kasuga %.2f m with %d stones each its own part of the photograph, front and sun windows open, back corners solid; '
          'lit with a hidden light in the fire box; yukimi %.2f m across on three legs' % (tall, pieces, width))


def test_water_basin():
    for stone in ('round', 'square'):
        root, objs = part('water_basin', stone=stone)
        basin = points(objs['water_basin stone'])
        water = points(objs['water_basin water'])
        rim = basin[numpy.hypot(basin[:, 0], basin[:, 1]) < 0.25][:, 2].max()
        level = water[:, 2].mean()
        check(level < rim - 0.01 and level > rim - 0.06, '%s basin: the water (%.3f) does not stand just under the rim (%.3f)' % (stone, level, rim))
        bowl_floor = basin[numpy.hypot(basin[:, 0], basin[:, 1]) < 0.03][:, 2].min()
        check(bowl_floor < level - 0.05, '%s basin: no bowl under the water' % stone)
        reach = numpy.hypot(water[:, 0], water[:, 1]).max()
        stream = points(objs['water_basin stream'])
        low = stream[stream[:, 2].argmin()]
        top = stream[stream[:, 2].argmax()]
        check(abs(low[2] - level) < 0.012 and math.hypot(low[0], low[1]) < reach, '%s basin: the stream does not land in the water' % stone)
        spout = points(objs['water_basin spout'])
        check(top[2] > level + 0.15 and spout[:, 1].max() > 0.45, '%s basin: the stream does not fall from the spout behind the basin' % stone)
        feet = points(objs['water_basin foot stones'])
        check(feet[:, 1].min() < -0.6, '%s basin: no stone in front to crouch on' % stone)
        check('water_basin ladle' in objs, '%s basin: no ladle' % stone)
    root, objs = part('water_basin', spout=False, ladle=False)
    check(not any(k in objs for k in ('water_basin spout', 'water_basin stream', 'water_basin ladle')), 'spout=False, ladle=False still made them')
    check(refused(lambda: part('water_basin', stone='oval')), 'the basin took a stone it does not have')
    print('PASS water_basin: round and square, water standing just under the rim over a bowl, the stream from the spout behind landing '
          'in it, the front stone in front, spout and ladle only when asked')


def test_jar():
    root, objs = part('jar')
    everything = all_points(objs.values())
    check(abs(everything[:, 2].max() - 0.71) < 0.02, 'the jar with its lid is %.3f m tall' % everything[:, 2].max())
    root, objs = part('jar', lid=False)
    body = objs['jar body']
    check('jar lid' not in objs, 'lid=False still made a lid')
    check(ray_hits(body, (0, 0, 0.7), (0, 0, -1), 0.12) is False and ray_hits(body, (0, 0, 0.7), (0, 0, -1), 0.2),
          'without its lid the jar\'s mouth is not open (a look down meets something before the inside)')
    s0 = part('jar', seed=0)[1]['jar body']['jar_seed']
    s1 = part('jar', seed=1)[1]['jar body']['jar_seed']
    check(abs(s0 - s1) > 1e-6, 'two seeds paint the jar the same')
    names = [n.name for n in part('jar')[1]['jar body'].data.materials]
    check(names == ['PART • jar: blue-and-white glaze'], 'the jar is not in its glaze: %s' % names)
    print('PASS jar: 0.71 m with its lid, open and dark inside without it, its painting placed by the seed')


def test_clogs():
    root, objs = part('clogs')
    boards = [objs['clogs left'], objs['clogs right']]
    for board in boards:
        pressed = numpy.zeros(len(board.data.vertices))
        board.data.attributes['pressed'].data.foreach_get('value', pressed)
        check(pressed.max() > 0.6, '%s: the top is not pressed where the feet go' % board.name)
        p = points(board)
        check(p[:, 2].min() > -0.004 and 0.06 < p[:, 2].max() < 0.075, '%s: not a board on teeth 6 to 7 cm high' % board.name)
        low = p[p[:, 2] < 0.004]
        check(len(low) >= 4, '%s: nothing stands on the ground' % board.name)
    thong = objs['clogs left thong'].data.materials[0]
    check('0.32 0.02 0.01' in thong.name, 'the thongs are not red: %s' % thong.name)
    xs = [points(b)[:, 0].mean() for b in boards]
    check(xs[0] < -0.03 and xs[1] > 0.03, 'the clogs do not stand side by side')
    root, objs = part('clogs', thongs='black')
    check('0.01 0.01 0.01' in objs['clogs left thong'].data.materials[0].name, 'black thongs are not black')
    root, objs = part('clogs', pose='scattered')
    p = points(objs['clogs left'])
    check(p[:, 2].max() > 0.085 and p[:, 2].min() > -0.004, 'scattered: the left clog is not tipped on its side (%.3f m high)' % p[:, 2].max())
    check(refused(lambda: part('clogs', thongs='green')), 'the clogs took a colour they do not have')
    print('PASS clogs: two boards on teeth side by side, pressed where the feet go, red thongs (black when asked), one tipped when scattered')


def test_hanging_lantern():
    for kind in ('box', 'glass', 'round'):
        root, objs = part('hanging_lantern', kind=kind)
        everything = all_points([o for o in objs.values() if o.type == 'MESH'])
        chain = points(objs['hanging_lantern chain'])
        check(abs(chain[:, 2].max() - 0.8) < 0.01 and abs(everything[:, 2].min()) < 0.01, '%s: the hook is not 0.8 m above the foot (%.3f, %.3f)' % (kind, chain[:, 2].max(), everything[:, 2].min()))
        light = objs.get('hanging_lantern light')
        check(light is not None and light.visible_camera is False and 0.1 < light.matrix_world.translation.z < 0.5, '%s: no hidden light inside' % kind)
        lit_things = [o for o in objs.values() if o.type == 'MESH' and o.visible_shadow is False]
        check(lit_things, '%s: the paper or glass casts a shadow round the light' % kind)
    root, objs = part('hanging_lantern', lit=False)
    check('hanging_lantern light' not in objs, 'an unlit lantern has a light')
    check(objs['hanging_lantern panes'].data.materials[0].name == 'PART • garden: lantern paper', 'an unlit lantern\'s paper glows')
    check(refused(lambda: part('hanging_lantern', kind='stone')), 'the lantern took a kind it does not have')
    print('PASS hanging_lantern: box, glass and round, each with its hook 0.8 m above its foot, a hidden light inside and shadowless panes; dark when unlit')


def test_wooden_bucket():
    root, objs = part('wooden_bucket')
    staves = objs['wooden_bucket staves']
    pieces = len(set(numpy.round(face_numbers(staves, 'pp_piece'), 5)))
    check(pieces >= 18, 'the staves do not each show their own part of the photograph (%d different)' % pieces)
    p = points(staves)
    check(p[:, 2].max() > 0.36, 'the handle staves do not rise above the rim')
    water = points(objs['wooden_bucket water'])
    check(0.15 < water[:, 2].mean() < 0.25, 'the water does not stand inside the bucket')
    hoops = points(objs['wooden_bucket hoops'])
    check(numpy.hypot(hoops[:, 0], hoops[:, 1]).min() > 0.14, 'the hoops are not round the outside')
    root, objs = part('wooden_bucket', handle=False, dipper=False)
    check(points(objs['wooden_bucket staves'])[:, 2].max() < 0.27 and 'wooden_bucket dipper' not in objs, 'handle=False, dipper=False still made them')
    print('PASS wooden_bucket: %d staves each its own part of the photograph, handle staves and bar, copper hoops, water in it' % 18)


def test_bamboo_broom():
    root, objs = part('bamboo_broom')
    handle = points(objs['bamboo_broom handle'])
    twigs = points(objs['bamboo_broom twigs'])
    top = handle[handle[:, 2].argmax()]
    fan = twigs[twigs[:, 2] < 0.03]
    check(1.4 < top[2] < 1.6 and top[1] - fan[:, 1].mean() > 0.3, 'the broom does not lean back towards +Y (top at y %.2f, z %.2f)' % (top[1], top[2]))
    check(fan[:, 0].max() - fan[:, 0].min() > 0.45 and twigs[:, 2].min() > -0.005, 'the fan is not spread along X on the ground')
    root, objs = part('bamboo_broom', pose='lying')
    check(all_points(objs.values())[:, 2].max() < 0.12, 'the lying broom is not flat on the ground')
    print('PASS bamboo_broom: leaning back towards +Y with a fan %.2f m wide on the ground; flat when lying' % (fan[:, 0].max() - fan[:, 0].min()))


def main():
    test_stone_lantern()
    test_water_basin()
    test_jar()
    test_clogs()
    test_hanging_lantern()
    test_wooden_bucket()
    test_bamboo_broom()
    print('PASS test_store_garden_things')


if __name__ == '__main__':
    main()
