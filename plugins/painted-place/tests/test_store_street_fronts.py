"""
What this file does: checks the tools the town street's fronts brought to the store (log 55) against what they promise.
The eaves: the roof's edge past every wall face by the overhang given (past lay_stone's blocks when the wall is stone),
flush where a side is shared, its eaves boards, rafter ends under the overhang and a gutter in front of each eave with
outlets where asked; a lean-to's gutter on its low side, a flat roof flat. The downpipe: on the face asked, at the place
asked, from its top straight down to the ground, with its hopper head, sockets, holdfasts and shoe, standing off the
stone, its leaks and splash when asked. The stain tool: planes set out by the distance given (or in front of lay_stone's
blocks), the old defaults unchanged, the heavy kinds, taper and uneven. Weathering: a new material each time, the old
one as it was. The same seed, the same result; wrong options refused.
    python3 tests/test_store_street_fronts.py
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


def box(name, size, location, turn=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_euler.z = math.radians(turn)
    bpy.context.view_layer.update()
    return obj


def points(objects, frame=None):
    """Every vertex of the objects, in the world or in a frame's own axes (an object whose matrix gives the frame)."""
    objects = objects if isinstance(objects, (list, tuple)) else [objects]
    to_frame = frame.matrix_world.inverted() if frame is not None else None
    found = []
    for obj in objects:
        co = numpy.zeros(len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get('co', co)
        matrix = numpy.array(obj.matrix_world if to_frame is None else to_frame @ obj.matrix_world)
        found.append(co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3])
    return numpy.concatenate(found)


def refused(call, error=ValueError):
    try:
        call()
    except error:
        return True
    return False


def numbers(obj, name):
    data = numpy.zeros(len(obj.data.attributes[name].data))
    obj.data.attributes[name].data.foreach_get('value', data)
    return data


# ------------------------------------------------------------------------------------------------ eaves

def test_eaves():
    import lay_eaves
    import lay_stone
    fresh_scene()
    house = box('house', (6.0, 5.0, 5.0), (1.0, 2.0, 2.5), turn=20)           # in its own axes: x -3..3, y -2.5..2.5, z -2.5..2.5
    made = lay_eaves.lay(house, kind='pitched', ridge='front', overhang=0.4, outlets={'front': [0.5]}, seed=2)
    check(sorted(made) == ['eaves', 'gutters', 'outlets', 'roof', 'walls'], 'the eaves made %s' % sorted(made))
    check(len(made['roof']) == 2, 'a pitched roof should be two slopes, got %d' % len(made['roof']))
    roof = points(made['roof'], house)
    for axis, half, name in ((0, 3.0, 'left and right'), (1, 2.5, 'front and back')):
        low, high = roof[:, axis].min(), roof[:, axis].max()
        check(abs(low + half + 0.4) < 0.015 and abs(high - half - 0.4) < 0.015,
              'the roof does not overhang the %s walls by 0.4 m: its edges at %.3f and %.3f (walls at +-%.1f)' % (name, low, high, half))
    # the ridge runs along the front (x), the eaves are at the front and back and lower than the ridge
    top_at_middle = roof[numpy.abs(roof[:, 1]) < 0.2][:, 2].max()
    check(top_at_middle > roof[numpy.abs(roof[:, 1]) > 2.7][:, 2].max() + 1.0, 'the ridge is not along the front')
    # eaves boards and rafter ends: between the wall's face and the roof's edge, under the slates
    eaves = points(made['eaves'], house)
    rafters = made['eaves']['rafters']
    check(rafters >= 2 * 9, 'too few rafter ends: %d on two 6 m eaves' % rafters)
    under = eaves[eaves[:, 1] < -2.5]                                            # out past the front wall's face
    check(len(under) >= 4 * (rafters // 2) + 8, 'no rafter ends or eaves board under the front overhang (%d points)' % len(under))
    check(under[:, 1].min() > -2.5 - 0.4 - 0.001, 'the eaves board stands past the roof\'s edge (%.3f)' % under[:, 1].min())
    check(eaves[:, 2].max() < roof[:, 2].max(), 'the eaves boards stand above the roof')
    # the gutters: one on each eave, in front of the eaves board, a little below the slates' edge, along the whole eave
    gutters = made['gutters']
    check(gutters is not None and gutters['gutters'] == 2, 'a pitched roof should have two gutters')
    iron = points(gutters, house)
    front_gutter = iron[iron[:, 1] < -2.5]
    check(len(front_gutter) > 100 and front_gutter[:, 0].min() < -3.2 and front_gutter[:, 0].max() > 3.2, 'the front gutter does not run the eave\'s length')
    edge_z = roof[roof[:, 1] < -2.85][:, 2].min()
    check(front_gutter[:, 2].max() < edge_z + 0.08 and front_gutter[:, 1].min() < -2.9 - 0.04, 'the front gutter does not hang in front of and below the eave')
    # the outlet: 0.5 m from the front's left end, under the gutter
    check(len(made['outlets']) == 1, 'one outlet asked, %d made' % len(made['outlets']))
    outlet = house.matrix_world.inverted() @ Vector(made['outlets'][0])
    channel = front_gutter[numpy.abs(front_gutter[:, 0] - outlet.x) > 0.2]
    check(abs(outlet.x - (-3.0 + 0.5)) < 0.01 and outlet.y < -2.9 and outlet.z < channel[:, 2].min() - 0.05, 'the outlet is not under the gutter 0.5 m along (%.2f, %.2f, %.2f)' % tuple(outlet))
    # the walls carried up: a gable at each end up to the roof
    walls = points(made['walls'], house)
    check(walls[:, 2].min() > 2.5 - 0.001 and walls[:, 2].max() > top_at_middle - 0.3, 'the gables do not stand from the box\'s top up to the ridge')
    # same seed, same eaves; another seed, other rafters
    again = lay_eaves.lay(house, kind='pitched', ridge='front', overhang=0.4, outlets={'front': [0.5]}, seed=2)
    check(numpy.allclose(points(again['eaves'], house), eaves), 'the same seed made different eaves')
    other = lay_eaves.lay(house, kind='pitched', ridge='front', overhang=0.4, seed=3)
    check(not numpy.allclose(points(other['eaves'], house), eaves), 'another seed made the same rafters')
    # by side, and 'shared': flush with the box there
    terrace = lay_eaves.lay(house, ridge='front', overhang={'front': 0.6, 'back': 0.3, 'left': 'shared', 'right': 'shared'})
    roof = points(terrace['roof'], house)
    check(abs(roof[:, 1].min() + 3.1) < 0.015 and abs(roof[:, 1].max() - 2.8) < 0.015, 'front 0.6 and back 0.3: the edges are at %.3f and %.3f' % (roof[:, 1].min(), roof[:, 1].max()))
    check(abs(roof[:, 0].min() + 3.0) < 0.015 and abs(roof[:, 0].max() - 3.0) < 0.015, 'shared sides: the roof is not flush with the box (%.3f, %.3f)' % (roof[:, 0].min(), roof[:, 0].max()))
    # on a stone wall the overhang is measured past the blocks: 0.2 relief + 0.04 + the overhang
    stone = box('stone house', (6.0, 5.0, 5.0), (20.0, 2.0, 2.5))
    stonework = lay_stone.lay(stone, sides=['front'], seed=1)
    stoned = lay_eaves.lay(stone, ridge='front', overhang=0.42)
    roof = points(stoned['roof'], stone)
    check(abs(roof[:, 1].min() + 2.5 + 0.24 + 0.42) < 0.015, 'past lay_stone\'s blocks: the front edge is at %.3f, not %.3f' % (roof[:, 1].min(), -2.5 - 0.66))
    blocks = points(stonework, stone)
    check(points(stoned['eaves'], stone)[:, 2].min() > blocks[:, 2].max() - 0.5, 'the eaves hang too far down the stone')
    # a lean-to: its gutter on the low side only, rising to the high side; a flat roof: flat, eaves boards all round
    shed = box('shed', (4.0, 3.0, 2.4), (-20.0, 0.0, 1.2))
    lean = lay_eaves.lay(shed, kind='lean-to', high_side='back', overhang=0.3)
    roof = points(lean['roof'], shed)
    check(roof[roof[:, 1] > 1.5][:, 2].max() > roof[roof[:, 1] < -1.5][:, 2].max() + 0.6, 'the lean-to does not rise to its high side')
    check(lean['gutters']['gutters'] == 1 and points(lean['gutters'], shed)[:, 1].max() < 0.0, 'the lean-to\'s gutter is not on its low side alone')
    flat = lay_eaves.lay(shed, kind='flat', overhang=0.3)
    roof = points(flat['roof'], shed)
    check(roof[:, 2].max() - roof[:, 2].min() < 0.06 + 3.6 * math.tan(math.radians(2.0)) + 0.02, 'the flat roof is not flat')
    check(flat['eaves']['eaves boards'] == 4, 'a flat roof should have eaves boards all round (%d)' % flat['eaves']['eaves boards'])
    # wrong options refused
    for wrong in ({'kind': 'hipped'}, {'pitch': 80}, {'overhang': -0.2}, {'overhang': {'front': 0.4}}, {'ridge': 'diagonal'},
                  {'ridge': 'front', 'outlets': {'left': [1.0]}}, {'ridge': 'front', 'gutters': ['left']}, {'high_side': 'up'},
                  {'ridge': 'front', 'outlets': {'front': [9.0]}}, {'kind': 'flat', 'pitch': 10}):
        check(refused(lambda: lay_eaves.lay(house, **wrong)), 'lay_eaves accepted %s' % wrong)
    check(refused(lambda: lay_eaves.lay(house, overhnag=0.4), TypeError), 'a misspelt option was accepted')
    print('PASS lay_eaves: the roof overhangs every side by the 0.4 m given (past the stone\'s blocks on a stone wall), flush on '
          'shared sides; %d rafter ends, eaves boards and a gutter on each eave with its outlet where asked; the lean-to\'s gutter '
          'on its low side, the flat roof flat; same seed, same eaves; wrong options refused' % rafters)


# ------------------------------------------------------------------------------------------------ downpipe

def face_frame(wall, side):
    import stain
    face = stain.wall_side(wall, side)
    return face['origin'], face['along'], face['normal']


def on_face(world, frame):
    origin, along, normal = frame
    relative = world - numpy.array(origin)
    return relative @ numpy.array(along), relative @ numpy.array(normal), world[:, 2] - origin.z


def test_downpipe():
    import downpipe
    import lay_stone
    fresh_scene()
    wall = box('wall', (5.0, 0.6, 6.0), (2.0, 1.0, 3.0), turn=30)
    made = downpipe.lay(wall, 'front', along=1.0, top=5.5, seed=1)
    pipe = made['pipe']
    u, d, z = on_face(points(pipe), face_frame(wall, 'front'))
    check(abs(z.min()) < 0.01 and abs(z.max() - 5.5) < 0.002, 'the pipe does not run from the ground (%.3f) to its top (%.3f, asked 5.5)' % (z.min(), z.max()))
    check(numpy.abs(u - 1.0).max() < 0.23, 'the pipe strays from 1.0 m along the face (%.2f to %.2f)' % (u.min(), u.max()))
    check(d.min() > -0.001, 'the pipe goes into the wall (%.3f m)' % d.min())
    straight = (z > 0.5) & (z < 4.0) & (numpy.abs(u - 1.0) < 0.06)                # the pipe itself, between the shoe and the hopper
    check(abs(numpy.median(d[straight]) - 0.085) < 0.03, 'the plain wall\'s pipe stands %.3f m out, not about 0.085' % numpy.median(d[straight]))
    head = z > 5.5 - 0.3
    check(u[head].max() - u[head].min() > 0.3, 'no hopper head at the top (%.2f m wide)' % (u[head].max() - u[head].min()))
    foot = z < 0.2
    check(d[foot].max() > 0.085 + 0.15, 'no shoe throwing the water out at the foot')
    check(pipe['sockets'] == 2 and pipe['holdfasts'] == 3, '%d sockets and %d holdfasts on a 5.2 m pipe' % (pipe['sockets'], pipe['holdfasts']))
    check(not made['stains'], 'stains laid without being asked')
    again = downpipe.lay(wall, 'front', along=1.0, top=5.5, seed=1)
    check(numpy.allclose(points(again['pipe']), points(pipe)), 'the same seed made a different pipe')
    # on lay_stone's wall: standing off the blocks; leaks behind it in front of the stone; a splash on the ground
    stone = box('stone wall', (5.0, 0.6, 6.0), (20.0, 1.0, 3.0))
    lay_stone.lay(stone, sides=['front'], seed=2)
    wet = downpipe.lay(stone, 'front', along=0.6, top=5.4, leaks=True, splash=True, seed=4)
    frame = face_frame(stone, 'front')
    u, d, z = on_face(points(wet['pipe']), frame)
    straight = (z > 0.5) & (z < 4.0) & (numpy.abs(u - 0.6) < 0.06)
    check(d[straight].min() > 0.24 - 0.002, 'the pipe touches the stone blocks (its back %.3f m out, the blocks to 0.237)' % d[straight].min())
    sockets = wet['pipe']['sockets']
    check(len(wet['stains']) == 1 + 2 * sockets + 1 + 1, '%d stains for %d sockets (a stripe, a leak and a rust run per socket, the hopper\'s rust, a splash)' % (len(wet['stains']), sockets))
    for plane in wet['stains'][:-1]:
        _, pd, _ = on_face(points(plane), frame)
        check(pd.min() >= 0.244 - 0.0005, 'a leak plane stands %.3f m out, behind the stone\'s blocks' % pd.min())
    splash = points(wet['stains'][-1])
    check(numpy.abs(splash[:, 2]).max() < 0.02, 'the splash is not on the ground')
    # a ground mesh: the shoe stands on it; a gutter outlet: the swan neck reaches it
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(2.0, -2.0, 0.15))
    ground = bpy.context.object
    up = downpipe.lay(wall, 'front', along=3.0, top=5.0, ground=ground, outlet=None)
    check(abs(up['pipe']['foot'] - 0.15) < 0.001 and abs(points(up['pipe'])[:, 2].min() - 0.15) < 0.01, 'the shoe does not stand on the ground given')
    origin, along_v, normal = face_frame(wall, 'front')
    outlet = origin + along_v * 4.0 + normal * 0.7 + Vector((0.0, 0.0, 5.6))
    neck = downpipe.lay(wall, 'front', along=4.0, top=5.2, outlet=tuple(outlet))
    check(abs(points(neck['pipe'])[:, 2].max() - 5.61) < 0.02, 'the swan neck does not reach the outlet')
    by_outlet = downpipe.lay(wall, 'front', outlet=tuple(outlet))                # its place and height from the outlet alone
    bu, _, bz = on_face(points(by_outlet['pipe']), face_frame(wall, 'front'))
    check(abs(by_outlet['pipe']['top'] - (5.6 - 0.4)) < 0.001 and abs(numpy.median(bu) - 4.0) < 0.05, 'given only an outlet, the pipe is not under it')
    # wrong options refused
    for args, options in (((wall, 'front'), {}), ((wall, 'top', 1.0, 5.0), {}), ((wall, 'front', 7.0, 5.0), {}), ((wall, 'front', 1.0, 0.8), {}),
                          ((wall, 'front', 1.0, 5.0), {'radius': 0.5}), ((wall, 'front', 1.0, 5.0), {'out': 0.01}),
                          ((wall, 'front', 1.0, 5.0), {'outlet': (0.0, 0.0, 1.0)}), ((wall, 'front', 1.0, 5.0), {'lengths': 0.1})):
        check(refused(lambda: downpipe.lay(*args, **options)), 'downpipe accepted %s %s' % (args[1:], options))
    check(refused(lambda: downpipe.lay(wall, 'front', 1.0, 5.0, hoper=False), TypeError), 'a misspelt option was accepted')
    print('PASS downpipe: from its top (5.5 m) straight down the face to the ground at the place asked, hopper head, %d sockets '
          'with holdfasts, a shoe; off the stone on a stone wall, its leaks in front of the blocks, a splash on the ground; the shoe '
          'on a ground given, the swan neck up to an outlet; same seed, same pipe; wrong options refused' % pipe['sockets'])


# ------------------------------------------------------------------------------------------------ stain

def test_stain_set_out():
    import lay_stone
    import stain
    fresh_scene()
    wall = box('wall', (6.0, 0.5, 3.0), (1.0, 2.0, 1.5))                         # front face at y = 1.75, left end at x = -2
    plain = stain.on_wall(wall, 'front', 1.0, 2.0, 0.5, 1.5, kind='soot', seed=1)
    ys = points(plain)[:, 1]
    check(numpy.allclose(ys, 1.75 - 0.004), 'the default plane is not 4 mm off the face (y %.4f)' % ys.min())
    check(len(plain.data.vertices) == 9 * 15, 'the default plane changed its points (%d)' % len(plain.data.vertices))
    rows = points(plain).reshape(15, 9, 3)
    check(numpy.allclose(rows[0, :, 0], rows[-1, :, 0]), 'the default plane is no longer square')
    set_out = stain.on_wall(wall, 'front', 1.0, 2.0, 0.5, 1.5, kind='soot', seed=1, offset=0.236)
    check(numpy.allclose(points(set_out)[:, 1], 1.75 - 0.236), 'offset 0.236 does not set the plane 0.236 m out')
    check(numpy.allclose(numbers(set_out, 'fade'), numbers(plain, 'fade')), 'setting the plane out changed its fade')
    check(refused(lambda: stain.on_wall(wall, 'front', 1.0, 2.0, 0.5, 1.5, offset='front')), "offset='front' was accepted on a wall lay_stone did not build")
    stone = box('stone', (6.0, 0.5, 3.0), (1.0, 12.0, 1.5))
    stonework = lay_stone.lay(stone, sides=['front'], seed=3, bands=False, quoins=False)
    front = stain.on_wall(stone, 'front', 0.0, 6.0, 0.0, 3.0, kind='heavy soot', offset='front', seed=2)
    out = 11.75 - points(front)[:, 1]
    check(numpy.allclose(out, 0.24), "offset='front' sets the plane %.3f m out, not 0.24 (the relief 0.2 and 0.04)" % out.min())
    block_faces = 11.75 - points(stonework)[:, 1]
    blocks = block_faces[block_faces < 0.2 + 0.06]                               # the blocks' faces (jambs and sills stand further)
    check(blocks.max() < out.min(), 'a block stands %.3f m out, in front of the stain at %.3f' % (blocks.max(), out.min()))
    # the heavy kinds have their own materials, which read 'fade'
    for kind in ('heavy soot', 'far soot', 'heavy damp', 'leak'):
        plane = stain.on_wall(stone, 'front', 1.0, 2.0, 0.5, 1.5, kind=kind, offset='front')
        material = plane.data.materials[0]
        check(material.name == 'MADE • stain %s' % kind, '%s has the material %s' % (kind, material.name))
        check('fade' in {n.attribute_name for n in material.node_tree.nodes if n.type == 'ATTRIBUTE'}, '%s does not read fade' % kind)
    damp_colours = [tuple(round(c, 3) for c in n.inputs[6].default_value[:3]) for n in bpy.data.materials['MADE • stain heavy damp'].node_tree.nodes
                    if n.type == 'MIX' and n.data_type == 'RGBA']
    check((0.2, 0.19, 0.165) in damp_colours, 'the heavy damp has no salt line')
    # taper: the weak end narrower; uneven: the weak end wanders
    run = stain.on_wall(wall, 'front', 1.0, 2.0, 0.5, 2.0, kind='heavy soot', taper=0.4, seed=4)
    rows = points(run).reshape(15, 9, 3)
    bottom, top = numpy.ptp(rows[0, :, 0]), numpy.ptp(rows[-1, :, 0])
    check(abs(top - 1.0) < 1e-6 and abs(bottom - 0.4) < 1e-6, 'taper 0.4: the run is %.2f m at its strong end and %.2f at its weak end' % (top, bottom))
    damp = stain.on_wall(wall, 'front', 0.0, 6.0, 0.0, 1.2, kind='heavy damp', strong_at='bottom', uneven=0.4, seed=5)
    across = len(damp.data.vertices) // 15
    fade = numbers(damp, 'fade').reshape(15, across)
    heights = numpy.array([numpy.argmax(fade[:, i] > 0.5) for i in range(across)]) / 14 * 1.2
    check(across >= 30 and numpy.ptp(heights) > 0.15, 'uneven 0.4: the tide line wanders only %.2f m along 6 m' % numpy.ptp(heights))
    straight = stain.on_wall(wall, 'front', 0.0, 6.0, 0.0, 1.2, kind='damp', strong_at='bottom', seed=5)
    flat_fade = numbers(straight, 'fade').reshape(15, 9)
    check(numpy.ptp([numpy.argmax(flat_fade[:, i] > 0.5) for i in range(2, 7)]) == 0, 'without uneven the tide line is not straight')
    for wrong in ({'taper': 0.0}, {'taper': 1.5}, {'uneven': 0.9}, {'offset': 'outside'}, {'offset': -0.1}, {'kind': 'tar'}):
        check(refused(lambda: stain.on_wall(wall, 'front', 1.0, 2.0, 0.5, 1.5, **wrong)), 'stain accepted %s' % wrong)
    print("PASS stain: planes set out by the distance given (0.236 m), offset='front' 0.24 m, in front of every block; the "
          "default plane 4 mm out, square and unchanged; the heavy kinds with their materials (the damp's salt line); taper "
          "narrows the weak end, uneven makes it wander; wrong options refused")


# ------------------------------------------------------------------------------------------------ weathering

def fingerprint(material):
    tree = material.node_tree
    return (len(tree.nodes), len(tree.links), sorted((l.from_node.name, l.to_node.name, l.to_socket.identifier) for l in tree.links))


def test_weathering():
    import weathering
    fresh_scene()
    name = 'Hand-painted sandstone • shade 00'
    original = store.material(name)
    before = fingerprint(original)
    aged = weathering.stone(name, seed=1)
    check(aged is not original and aged.name.startswith(name + ' • weathered'), 'stone did not return a new material (%s)' % aged.name)
    check(fingerprint(original) == before, 'weathering changed the original stone material')
    check(fingerprint(aged)[0] > before[0], 'the weathered copy has nothing added')
    check(aged['pp_weathered_of'] == name, 'the copy does not say what it was made from')
    ranges = [(n.inputs['To Min'].default_value, n.inputs['To Max'].default_value) for n in aged.node_tree.nodes if n.type == 'MAP_RANGE']
    check(any(abs(a - 1.0) < 1e-6 and abs(b - 0.38) < 1e-6 for a, b in ranges), 'the default does not darken the stone to 0.38 in its streaks')
    def shift(material):
        return [tuple(n.inputs[1].default_value) for n in material.node_tree.nodes if n.type == 'VECT_MATH' and n.operation == 'ADD' and not n.inputs[1].links][-1]
    check(shift(weathering.stone(name, seed=1)) == shift(aged), 'the same seed put the streaks elsewhere')
    check(shift(weathering.stone(name, seed=2)) != shift(aged), 'another seed put the streaks in the same place')
    wet = weathering.stone('STONE • worn honey-grey architectural dressings', dark=0.45, overall=0.88, wet=0.8)
    check(fingerprint(store.material('STONE • worn honey-grey architectural dressings'))[0] < fingerprint(wet)[0], 'the wet copy is not a copy')
    door_name = 'WOOD • peeling dark painted doors'
    door = store.material(door_name)
    door_before = fingerprint(door)
    peeled = weathering.peel(door_name, amount=0.6, seed=3)
    check(peeled is not door and peeled.name.startswith(door_name + ' • peeling') and fingerprint(door) == door_before,
          'peel did not leave the original as it was and return a copy')
    check('pp_ground' in {n.attribute_name for n in peeled.node_tree.nodes if n.type == 'ATTRIBUTE'}, 'peel does not measure from the ground under each object')
    timbers = [tuple(n.inputs[7].default_value[:3]) for n in peeled.node_tree.nodes if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[7].links]
    check(any(numpy.allclose(t, (0.075, 0.066, 0.055)) for t in timbers), 'the paint does not peel to grey timber')
    plain = bpy.data.materials.new('no principled')
    plain.use_nodes = True
    plain.node_tree.nodes.remove(plain.node_tree.nodes['Principled BSDF'])
    for call in (lambda: weathering.stone(name, dark=1.2), lambda: weathering.peel(door_name, amount=2.0), lambda: weathering.stone(plain),
                 lambda: weathering.peel(42), lambda: weathering.stone(name, streak_width=10.0), lambda: weathering.peel(door_name, timber=(0.1, 0.1))):
        check(refused(call), 'weathering accepted a wrong option')
    check(refused(lambda: weathering.stone(name, drak=0.5), TypeError), 'a misspelt option was accepted')
    print('PASS weathering: stone and peel return new materials (named for the original, saying what they came from) and leave '
          'the originals as they were; the stone darkens to 0.38 in its streaks by default; same seed, same streaks; the paint '
          'peels to grey timber measured from the ground; wrong options refused')


def test_help():
    for name in ('lay_eaves', 'downpipe', 'weathering', 'stain'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS lay_eaves, downpipe, weathering and stain answer --help')


def main():
    test_eaves()
    test_downpipe()
    test_stain_set_out()
    test_weathering()
    test_help()
    print('PASS test_store_street_fronts')


if __name__ == '__main__':
    main()
