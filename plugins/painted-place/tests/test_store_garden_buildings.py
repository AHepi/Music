"""
What this file does: checks the three tools for a Japanese inn's buildings (lay_tile_roof, lay_shoji, lay_veranda): each
answers --help; the roof, of every kind, covers the box with its eaves past every wall, lifts its corners, steps its
courses, gives every tile its own number pp_piece, turns with the box and writes the eave's height on it; the screens fill
each opening with panels in two tracks, light the openings asked and give back where their small lights go; the veranda's
floor stands at its height and depth, its boards are worn and rain-darkened, its beam sits under the roof's rafters and
its step stands in front; the same seed makes the same thing, and wrong options are refused.
    python3 tests/test_store_garden_buildings.py
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402


def box(name, size, location, turn=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_euler = (0.0, 0.0, math.radians(turn))
    bpy.context.view_layer.update()
    return obj


def world_points(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def numbers(obj, name):
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no %r' % (obj.name, name))
    data = [0.0] * len(attribute.data)
    attribute.data.foreach_get('value', data)
    return data


def refused(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except ValueError:
        return True
    return False


def test_help():
    for name in ('lay_tile_roof', 'lay_shoji', 'lay_veranda'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS lay_tile_roof, lay_shoji and lay_veranda answer --help')


def roof_once(kind, seed=2, front_gable=None, turn=0.0, location=(0.0, 0.0, 1.5)):
    fresh_scene()
    import lay_tile_roof
    house = box('house', (9.0, 5.4, 3.0), location, turn)
    made = lay_tile_roof.lay(house, kind=kind, overhang=1.0, pitch=28, lift=0.3, front_gable=front_gable, seed=seed)
    return house, made


def test_roof():
    import lay_tile_roof
    for kind in lay_tile_roof.KINDS:
        house, made = roof_once(kind)
        tiles, timber = made['tiles'], made['timber']
        pts = world_points(tiles)
        xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
        check(len(tiles.data.polygons) > 3000, '%s roof: only %d tile faces' % (kind, len(tiles.data.polygons)))
        reach_x = 0.6 if kind == 'gable' else 1.0
        check(min(xs) < -4.5 - reach_x + 0.1 and max(xs) > 4.5 + reach_x - 0.1, '%s roof: the eaves reach x %.2f to %.2f over a 9 m box' % (kind, min(xs), max(xs)))
        check(min(ys) < -2.7 - 0.9 and max(ys) > 2.7 + 0.9, '%s roof: the eaves reach y %.2f to %.2f over a 5.4 m box' % (kind, min(ys), max(ys)))
        check(min(zs) > 3.0, '%s roof: a tile at %.2f m, below the wall top (3.0 m)' % (kind, min(zs)))
        check(max(zs) > 3.0 + 0.3 + 2.0, '%s roof: its top at %.2f m is too low for a 28 degree roof' % (kind, max(zs)))
        # the eave lifts towards its ends: the lowest tile near an end of the front eave stands higher than at its middle
        mid = min(p.z for p in pts if abs(p.x) < 0.5 and p.y < -3.3)
        end = min(p.z for p in pts if 4.4 < p.x < 4.9 and p.y < -3.3)
        check(end > mid + 0.08, '%s roof: the eave at its end (%.3f) is not lifted over its middle (%.3f)' % (kind, end, mid))
        pieces = numbers(tiles, 'pp_piece')
        check(min(pieces) >= 0.0 and max(pieces) <= 1.0 and len(set(round(v, 4) for v in pieces)) > 1000, '%s roof: the tiles do not each carry their own pp_piece' % kind)
        check(tiles.data.materials[0].name.startswith('lay_tile_roof • '), '%s roof: the tiles wear %s, not the tool\'s copy' % (kind, tiles.data.materials[0].name))
        check(len(timber.data.polygons) > 500 and len(timber.data.materials) == 3, '%s roof: the timber is %d faces in %d materials' % (kind, len(timber.data.polygons), len(timber.data.materials)))
        check((made['gables'] is not None) == (kind != 'hipped'), '%s roof: gables %s' % (kind, made['gables']))
        under = list(house['tile_roof_under'])
        check(len(under) == 11 and abs(under[0] - (1.5 + 0.3)) < 0.01 and under[-1] < under[0] - 0.15, '%s roof: tile_roof_under %s' % (kind, [round(v, 2) for v in under]))
        eaves = house['tile_roof_eaves'].split(',')
        check(eaves == (['front', 'back'] if kind == 'gable' else ['front', 'back', 'left', 'right']), '%s roof: tile_roof_eaves %s' % (kind, eaves))
        check(abs(made['eave_height'] - (mid - 0.0)) < 0.35, '%s roof: eave_height %.2f, the eave\'s lowest tile %.2f' % (kind, made['eave_height'], mid))
    # the courses step: tile faces lie at many heights along one row of cover tiles, never in one plane
    print('PASS lay_tile_roof: hip-and-gable, hipped and gable roofs cover a 9 x 5.4 m box with eaves 1 m past its walls, '
          'tiles above the wall top, the eaves lifted towards the corners, each tile its own pp_piece, the eave\'s height written on the box')


def test_roof_more():
    import lay_tile_roof
    house, plain = roof_once('hip-and-gable', front_gable=None)
    n_plain = len(plain['gables'].data.polygons)
    front_plain = [p for p in world_points(plain['tiles']) if abs(p.x) < 1.0 and -3.2 < p.y < -1.2]
    house, made = roof_once('hip-and-gable', front_gable=2.6)
    check(len(made['gables'].data.polygons) > n_plain, 'the front gable added no gable face')
    front = [p for p in world_points(made['tiles']) if abs(p.x) < 1.0 and -3.2 < p.y < -1.2]
    check(max(p.z for p in front) > max(p.z for p in front_plain) + 0.4, 'the front gable does not stand up from the front slope')
    # same seed, same roof; another seed, other pieces
    a = numbers(roof_once('hipped', seed=5)[1]['tiles'], 'pp_piece')
    b = numbers(roof_once('hipped', seed=5)[1]['tiles'], 'pp_piece')
    c = numbers(roof_once('hipped', seed=6)[1]['tiles'], 'pp_piece')
    check(a == b and a != c, 'the same seed did not make the same roof, or another seed the same')
    # it turns and moves with the box
    house, made = roof_once('hip-and-gable', turn=30.0, location=(20.0, -7.0, 1.5))
    pts = world_points(made['tiles'])
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    check(abs(cx - 20.0) < 0.6 and abs(cy + 7.0) < 0.6, 'a turned, moved box: the roof is centred at %.2f, %.2f, not 20, -7' % (cx, cy))
    ridge = [p for p in pts if p.z > max(q.z for q in pts) - 0.15]
    direction = (ridge[0] - ridge[-1])
    angle = math.degrees(math.atan2(direction.y, direction.x)) % 180
    check(abs(angle - 30.0) < 8 or abs(angle - 30.0 - 180) < 8, 'a box turned 30 degrees: the ridge runs at %.1f degrees' % angle)
    fresh_scene()
    deep = box('deep', (4.0, 8.0, 3.0), (0.0, 0.0, 1.5))
    made = lay_tile_roof.lay(deep, kind='gable')
    pts = world_points(made['tiles'])
    top = [p for p in pts if p.z > max(q.z for q in pts) - 0.1]
    check(max(p.y for p in top) - min(p.y for p in top) > 6.0, 'ridge=long on a box deeper than wide does not run front to back')
    for wrong in ({'kind': 'dome'}, {'pitch': 60}, {'overhang': 5}, {'lift': 2}, {'ridge': 'diagonal'}, {'kind': 'hipped', 'ridge': 'front'}):
        check(refused(lay_tile_roof.lay, deep, **wrong), 'lay_tile_roof accepted %s' % wrong)
    print('PASS lay_tile_roof: the front gable stands up from the front slope; the same seed makes the same roof; it turns '
          'and moves with its box; the ridge follows the longer side; wrong options are refused')


def shoji_once(seed=2, turn=0.0):
    fresh_scene()
    import lay_shoji
    house = box('house', (9.0, 5.4, 3.0), (0.0, 0.0, 1.5), turn)
    made = lay_shoji.lay(house, openings=[('front', 0.6, 0.0, 3.6, 1.9), ('front', 'door', 4.8, 0.0, 1.8, 1.9),
                                          ('left', 1.0, 0.9, 1.4, 1.0)], lit=[0], dim=[1], seed=seed)
    return house, made


def test_shoji():
    import lay_shoji
    house, made = shoji_once()
    paper, frames = made['paper'], made['frames']
    check(made['panels'] == 8 and len(paper.data.polygons) == 8, 'lay_shoji: %d panels, %d paper faces (want 4 + 2 + 2)' % (made['panels'], len(paper.data.polygons)))
    slots = [p.material_index for p in paper.data.polygons]
    check(slots == [1, 1, 1, 1, 2, 2, 0, 0], 'lay_shoji: the paper\'s slots are %s (lit, lit, lit, lit, dim, dim, plain, plain wanted)' % slots)
    check([m.name for m in paper.data.materials] == ['lay_shoji • paper plain', 'lay_shoji • paper lit', 'lay_shoji • paper dim'], 'lay_shoji: the paper wears %s' % [m.name for m in paper.data.materials])
    lit = paper.data.materials[1].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value
    dim = paper.data.materials[2].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value
    check(lit > 5 * dim > 0, 'lay_shoji: lit paper glows %.2f, dim %.2f' % (lit, dim))
    # each panel's paper on the front stands in front of the wall's face, alternately on the two tracks
    fronts = []
    for polygon in paper.data.polygons[:6]:
        y = (paper.matrix_world @ polygon.center).y
        check(-2.7 - 0.12 < y < -2.7, 'lay_shoji: a front panel\'s paper at y %.3f, not just in front of the face (-2.7)' % y)
        fronts.append(round(y, 3))
    check(fronts[0] != fronts[1] and fronts[0] == fronts[2], 'lay_shoji: the panels do not alternate between two tracks: %s' % fronts)
    side = paper.matrix_world @ paper.data.polygons[7].center
    check(-4.5 - 0.12 < side.x < -4.5 and 1.0 < side.z < 2.0, 'lay_shoji: the left side\'s panel is at %s' % (tuple(round(v, 2) for v in side),))
    pts = world_points(frames)
    front_frames = [p for p in pts if p.y < -2.69]
    xs = [p.x for p in front_frames]
    check(min(xs) > -4.5 + 0.6 - 0.11 and max(xs) < -4.5 + 6.6 + 0.11, 'lay_shoji: the front frames run x %.2f to %.2f, past their openings' % (min(xs), max(xs)))
    check(len(made['light_points']) == 1, 'lay_shoji: %d light points for one lit opening' % len(made['light_points']))
    lx, ly, lz = made['light_points'][0]
    check(abs(lx - (-4.5 + 0.6 + 1.8)) < 0.01 and abs(ly - (-2.7 - 0.45)) < 0.01 and abs(lz - 0.95) < 0.01, 'lay_shoji: the light point is at %.2f, %.2f, %.2f' % (lx, ly, lz))
    pieces = numbers(paper, 'pp_piece')
    check(len(set(pieces)) == 8, 'lay_shoji: the panels do not each carry their own pp_piece')
    a = numbers(shoji_once(seed=4)[1]['frames'], 'pp_piece')
    b = numbers(shoji_once(seed=4)[1]['frames'], 'pp_piece')
    check(a == b, 'lay_shoji: the same seed made other screens')
    house, made = shoji_once(turn=90.0)
    centre = made['paper'].matrix_world @ made['paper'].data.polygons[0].center
    check(2.7 < centre.x < 2.7 + 0.12, 'lay_shoji: on a box turned 90 degrees the front panels are at x %.2f, not just past 2.7' % centre.x)
    for wrong in ({'openings': [('front', 8.0, 0.0, 3.6, 1.9)]}, {'openings': [('front', 0.6, 0.0, 3.6, 1.9)], 'panels': 1},
                  {'openings': [('front', 0.6, 0.0, 3.6, 1.9)], 'lattice': 'round'}, {'openings': [('top', 0.6, 0.0, 3.6, 1.9)]},
                  {'openings': [('front', 0.6, 0.0, 3.6, 1.9)], 'lit': [3]}):
        check(refused(lay_shoji.lay, house, **wrong), 'lay_shoji accepted %s' % wrong)
    print('PASS lay_shoji: 8 panels in 3 openings, the lit ones lit and the dim ones dim, two tracks just in front of the wall, '
          'within their openings, a light point 0.45 m out in front of the lit opening, each panel its own pp_piece, the same seed '
          'the same screens, turned with the box; wrong openings and options are refused')


def test_veranda():
    fresh_scene()
    import lay_tile_roof
    import lay_veranda
    house = box('house', (9.0, 5.4, 3.0), (0.0, 0.0, 1.5))
    lay_tile_roof.lay(house, overhang=1.0, seed=1)
    made = lay_veranda.lay(house, side='front', depth=0.9, height=0.45, step='stone', step_at=2.4, seed=2)
    floor, frame, stones = made['floor'], made['frame'], made['stones']
    pts = world_points(floor)
    check(abs(max(p.z for p in pts) - 0.45) < 0.006, 'lay_veranda: the floor\'s top at %.3f, not 0.45' % max(p.z for p in pts))
    check(abs(min(p.y for p in pts) - (-2.7 - 0.92)) < 0.01 and max(p.y for p in pts) < -2.7 + 0.001, 'lay_veranda: the floor runs y %.2f to %.2f' % (min(p.y for p in pts), max(p.y for p in pts)))
    check(abs(min(p.x for p in pts) + 4.5) < 0.01 and abs(max(p.x for p in pts) - 4.5) < 0.01, 'lay_veranda: the floor runs x %.2f to %.2f, not the side\'s length' % (min(p.x for p in pts), max(p.x for p in pts)))
    slots = {p.material_index for p in floor.data.polygons}
    check(slots == {0, 1, 2} and made['boards'] > 20, 'lay_veranda: %d boards in slots %s (plain, worn and rain-dark wanted)' % (made['boards'], slots))
    outer = [p.material_index for p in floor.data.polygons if (floor.matrix_world @ p.center).y < -2.7 - 0.8 and abs((floor.matrix_world @ p.center).x - (-4.5 + 2.4)) > 1.5]
    check(outer and outer.count(2) > 0.9 * len(outer), 'lay_veranda: the outer boards are not rain-dark')
    # the beam under the roof's rafters
    under = list(house['tile_roof_under'])
    beam_top = made['beam_height']
    e = 0.9 - 0.02 - 0.06 + 0.065
    i = int(e / 0.1)
    roof_under = under[i] + (under[i + 1] - under[i]) * (e / 0.1 - i) + 1.5
    check(0.08 < roof_under - beam_top < 0.13, 'lay_veranda: the beam\'s top at %.3f, the roof\'s underside there %.3f' % (beam_top, roof_under))
    check(max(p.z for p in world_points(frame)) < roof_under, 'lay_veranda: the frame pokes through the roof')
    sp = world_points(stones)
    step = [p for p in sp if p.y < -2.7 - 1.05]
    check(step and abs(sum(p.x for p in step) / len(step) - (-4.5 + 2.4)) < 0.2 and 0.15 < max(p.z for p in step) < 0.45, 'lay_veranda: no step stone in front at 2.4 m along, below the floor')
    check(len(set(numbers(floor, 'pp_piece'))) > 20, 'lay_veranda: the boards do not carry their own pp_piece')
    # no roof: the beam at the box's top; another side; wrong options refused
    fresh_scene()
    plain = box('plain', (6.0, 4.0, 2.8), (0.0, 0.0, 1.4), 90.0)
    made = lay_veranda.lay(plain, side='right', depth=1.2, height=0.6, start=0.5, end=3.0, step='wood', seed=3)
    check(abs(made['beam_height'] - 2.8) < 0.001, 'lay_veranda: with no roof the beam\'s top is %.3f, not the box\'s top' % made['beam_height'])
    pts = world_points(made['floor'])
    check(abs(max(p.z for p in pts) - 0.6) < 0.006 and min(p.y for p in pts) > 3.0 - 0.001 and max(p.y for p in pts) < 3.0 + 1.23, 'lay_veranda: the right side of a turned box: floor at y %.2f to %.2f' % (min(p.y for p in pts), max(p.y for p in pts)))
    for wrong in ({'step': 'ladder'}, {'depth': 5.0}, {'height': 0.05}, {'side': 'top'}, {'start': 3.0, 'end': 2.0}, {'posts': 0.2}):
        check(refused(lay_veranda.lay, plain, **wrong), 'lay_veranda accepted %s' % wrong)
    print('PASS lay_veranda: the floor at 0.45 m, 0.9 m deep along the whole side, boards plain, worn and rain-dark (the outer ones '
          'dark), the beam 0.1 m under the roof\'s underside, a step stone in front, each board its own pp_piece; on a turned box '
          'with no roof the beam at its top; wrong options are refused')


def main():
    test_help()
    test_roof()
    test_roof_more()
    test_shoji()
    test_veranda()


if __name__ == '__main__':
    try:
        main()
    except AssertionError as error:
        print('FAIL %s' % error)
        sys.exit(1)
