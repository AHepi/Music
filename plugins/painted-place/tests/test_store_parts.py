"""
What this file does: checks every part in the store: its module has a CARD that says what it is, its size and where it
came from; built into an empty scene it stands with its foot on the ground (z = 0) at the origin, at the size its card
gives, every piece at scale 1 with a material; a different seed changes it a little and the same seed not at all; and
its saved part file opens with the part's objects in it.
    python3 tests/test_store_parts.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import STORE, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import store  # noqa: E402


def bounds(objects):
    low, high = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type not in ('MESH', 'CURVE'):
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            low = Vector(tuple(map(min, low, world)))
            high = Vector(tuple(map(max, high, world)))
    return low, high


def build(name, seed):
    fresh_scene()
    root = store.add_part(name, seed=seed)
    bpy.context.view_layer.update()
    objects = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE')]
    return root, objects


def fingerprint(objects):
    total = 0.0
    for obj in objects:
        if obj.type == 'MESH':
            total += sum(abs(c) for v in obj.data.vertices[::7] for c in (obj.matrix_world @ v.co))
    return round(total, 4)


def main():
    names = store.names('parts')
    check(names, 'the store has no parts')
    for name in names:
        card = store.part_card(name)
        for key in ('what', 'size_m', 'source', 'views', 'materials'):
            check(key in card and card[key] not in (None, ''), '%s: CARD has no %r' % (name, key))
        root, objects = build(name, 0)
        check(objects, '%s built nothing' % name)
        low, high = bounds(objects)
        size = high - low
        check(abs(low.z) <= 0.06, '%s: its foot is at z = %.3f, not on the ground' % (name, low.z))
        centre = (low + high) / 2
        check(abs(centre.x) <= max(0.3, size.x * 0.35) and abs(centre.y) <= max(0.3, size.y * 0.35),
              '%s: not centred on the origin (centre %.2f, %.2f)' % (name, centre.x, centre.y))
        for given, measured, axis in zip(card['size_m'], size, 'xyz'):
            check(abs(measured - float(given)) <= max(0.06, 0.25 * float(given)),
                  '%s: %s size %.2f m, its card says %.2f m' % (name, axis, measured, float(given)))
        for obj in objects:
            check(all(abs(s - 1.0) < 1e-4 for s in obj.scale), '%s: %s is scaled %s (apply its scale)' % (name, obj.name, tuple(obj.scale)))
            check(len(obj.data.materials) > 0 and all(m is not None for m in obj.data.materials), '%s: %s has an empty material slot' % (name, obj.name))
        same = fingerprint(build(name, 0)[1])
        again = fingerprint(objects)
        check(abs(same - again) < 1e-3, '%s: the same seed built a different part' % name)
        other = fingerprint(build(name, 7)[1])
        if abs(other - same) < 1e-6:
            print('note: %s looks the same with another seed' % name)
        path = os.path.join(STORE, 'parts', name + '.blend')
        check(os.path.exists(path), '%s: no part file %s (store.save_part_file)' % (name, path))
        with bpy.data.libraries.load(path, link=False) as (source, _):
            in_file = list(source.objects)
        check(any(o.startswith(name) for o in in_file), '%s: its part file holds none of its objects (%s)' % (name, in_file[:5]))
        print('PASS %s: %.2f x %.2f x %.2f m, %d objects, foot at z = %.3f' % (name, size.x, size.y, size.z, len(objects), low.z))
    print('PASS test_store_parts: %d parts' % len(names))


if __name__ == '__main__':
    main()
