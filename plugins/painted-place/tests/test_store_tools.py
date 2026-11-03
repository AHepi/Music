"""
What this file does: checks every tool in the store: each answers --help; each, run on a small scene, makes what it
says (the walkway's boards all rest on both runners and carry the numbers their material reads; the cobbles tool lays
setts on a road and flags on a pavement; the boards tool lays boards and eaves on a box; the stone tool lays courses on
a wall; the puddle tool writes 'shallow' and 'dry' from 0 to 1; stone grain changes a stone material once; the finish
writes a picture); and the same seed makes the same thing.
    python3 tests/test_store_tools.py
"""
import importlib
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import store  # noqa: E402


def values(obj, name):
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no %r' % (obj.name, name))
    data = [0.0] * len(attribute.data)
    attribute.data.foreach_get('value', data)
    return data


def plane(name, size_x, size_y, location=(0.0, 0.0, 0.0), cuts=0):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size_x, size_y, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if cuts:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=cuts)
        bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def box(name, size, location):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def test_help():
    for name in store.names('tools'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS every tool answers --help (%s)' % ', '.join(store.names('tools')))


def walkway_once(seed):
    fresh_scene()
    import lay_walkway
    ground = plane('ground', 12.0, 14.0, cuts=20)
    for vertex in ground.data.vertices:
        vertex.co.z = 0.08 * vertex.co.y + 0.03 * ((vertex.co.x * 1.7) % 1.0)
    made = lay_walkway.lay([(0.0, -5.0, 0.0), (0.8, 0.0, 0.0), (-0.5, 5.0, 0.0)], ground=ground, mud_at_ends=0.5, seed=seed)
    return made


def test_walkway():
    made = walkway_once(4)
    names = [o.name for o in made]
    check(names[:2] == ['walkway boards', 'walkway runners'] and 'walkway nails' in names and 'walkway mud' in names, 'walkway made %s' % names)
    boards, runners = made[0], made[1]
    count = len(boards.data.vertices) // 8
    check(count == boards['walkway_boards'] and count > 30, 'walkway boards: %d' % count)
    resting = 0
    vertices = [v.co.copy() for v in boards.data.vertices]
    for b in range(count):
        bottom = vertices[8 * b: 8 * b + 4]
        left, right = (bottom[0] + bottom[2]) / 2, (bottom[1] + bottom[3]) / 2
        found = {}
        for k in range(61):
            t = k / 60
            point = left.lerp(right, t)
            hit, location, _n, _i = runners.ray_cast(point + Vector((0, 0, 0.004)), Vector((0, 0, -1)), distance=0.02)
            if hit:
                side = t < 0.5
                gap = point.z - location.z
                if side not in found or abs(gap) < abs(found[side]):
                    found[side] = gap
        if len(found) == 2 and all(-0.003 < g < 0.003 for g in found.values()):
            resting += 1
    check(resting == count, 'only %d of %d boards rest on both runners' % (resting, count))
    for number in ('board_tone', 'across', 'wear', 'wet', 'mud'):
        data = values(boards, number)
        check(min(data) >= -1.0001 and max(data) <= 1.0001, '%s out of range' % number)
    check(min(values(boards, 'across')) < -0.9 and max(values(boards, 'across')) > 0.9, 'across does not run end to end')
    check(boards.data.uv_layers.get('metres') is not None, 'the boards have no metres UV map')
    check(all(tuple(o.scale) == (1.0, 1.0, 1.0) for o in made), 'a walkway object is scaled')
    first = sum(v.co.x for v in boards.data.vertices)
    again = sum(v.co.x for v in walkway_once(4)[0].data.vertices)
    check(abs(first - again) < 1e-6, 'the same seed laid a different walkway')
    print('PASS lay_walkway: %d boards, every one resting on both runners; nails, mud, numbers and UV map present; same seed, same walkway' % count)


def test_finish():
    import finish
    from PIL import Image
    import numpy
    folder = tempfile.mkdtemp()
    source = os.path.join(folder, 'raw.png')
    gradient = numpy.zeros((96, 160, 3), dtype=numpy.uint8)
    gradient[..., 0] = numpy.linspace(10, 250, 160)[None, :]
    gradient[..., 2] = 40
    Image.fromarray(gradient).save(source)
    target = finish.finish(source, os.path.join(folder, 'done.png'))
    done = numpy.asarray(Image.open(target), dtype=numpy.float32)
    check(done.shape == gradient.shape, 'the finished picture changed size')
    check(numpy.percentile(done, 1) >= 2.0, 'the finish left pure black (no blue-black floor): darkest 1%% at %.1f' % numpy.percentile(done, 1))
    print('PASS finish: writes the finished picture, same size, no pure black')


def optional(name, test):
    if name in store.names('tools'):
        test()
    else:
        print('note: no %s tool in the store' % name)


def test_cobbles():
    fresh_scene()
    import lay_cobbles
    road = plane('road', 3.0, 8.0)
    pavement = plane('pavement', 1.6, 8.0, location=(2.4, 0.0, 0.12))
    setts = lay_cobbles.lay_setts(road, seed=1)
    flags = lay_cobbles.lay_flags(pavement, seed=1)
    stones = lambda made: sum(len(o.data.vertices) for o in (made if isinstance(made, (list, tuple)) else [made]) if o.type == 'MESH')
    check(stones(setts) > 400, 'lay_setts laid too few setts: %d' % stones(setts))
    check(stones(flags) > 12, 'lay_flags laid too few flags: %d' % stones(flags))
    again = lay_cobbles.lay_setts(plane('road two', 3.0, 8.0, location=(0.0, 20.0, 0.0)), seed=1)
    check(stones(again) == stones(setts), 'the same seed laid a different number of setts')
    print('PASS lay_cobbles: %d setts on a 3 x 8 m road, %d flags on a 1.6 x 8 m pavement' % (stones(setts), stones(flags)))


def main():
    test_help()
    test_walkway()
    test_finish()
    optional('lay_cobbles', test_cobbles)
    extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_store_tools_more.py')
    if os.path.exists(extra):
        spec = importlib.util.spec_from_file_location('more', extra)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()
    print('PASS test_store_tools')


if __name__ == '__main__':
    main()
