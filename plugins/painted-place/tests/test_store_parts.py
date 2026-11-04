"""
What this file does: checks every part in the store: its module has a CARD that says what it is, its size and where it
came from; built into an empty scene it stands with its foot on the ground (z = 0) at the origin, at the size its card
gives, every piece at scale 1 with a material; a different seed changes it a little and the same seed not at all; and
its saved part file opens with the part's objects in it. Then two more checks:
  - no piece floats: every mesh object of a part either has its lowest point within 2 cm of the ground, or its tight
    bounding box (grown by 1.5 cm) meets another object's of the same part (a brace hanging behind its legs, a lid
    standing in the air, fail by name);
  - every option works: the part is built once more with each option of its card set to something other than its
    default (a boolean turned round; every other named choice in the card text; a number one and a half times the
    default, or 5 for 0; 'seed' and defaults the card text does not give plainly are skipped with a note), and the
    foot, the scale-1 rule and the no-floating check are made on that build too.
    python3 tests/test_store_parts.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import STORE, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import store  # noqa: E402


def bounds(objects):
    """The part's world-space box: tight for meshes (from their points: a turned object's bound_box is loose, and a
    tipped cart read as 0.7 m under the ground by it), bound_box corners for curves."""
    low, high = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for name, (tlow, thigh) in tight_boxes(objects).items():
        low = Vector(tuple(map(min, low, tlow)))
        high = Vector(tuple(map(max, high, thigh)))
    for obj in objects:
        if obj.type != 'CURVE':
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


def tight_boxes(objects):
    """Each mesh object's world-space box from its points (a rotated object's bound_box is loose), by name."""
    import numpy
    boxes = {}
    for obj in objects:
        if obj.type != 'MESH' or not obj.data.vertices:
            continue
        points = numpy.empty(len(obj.data.vertices) * 3, dtype=numpy.float64)
        obj.data.vertices.foreach_get('co', points)
        points = points.reshape(-1, 3)
        matrix = numpy.array(obj.matrix_world)
        world = points @ matrix[:3, :3].T + matrix[:3, 3]
        boxes[obj.name] = (world.min(axis=0), world.max(axis=0))
    return boxes


def floating(objects, ground=0.0, touch=0.02, grow=0.015):
    """The names of mesh objects that touch neither the ground (lowest point within `touch` of it) nor, with their
    box grown by `grow`, any other object of the part."""
    boxes = tight_boxes(objects)
    loose = []
    for name, (low, high) in boxes.items():
        if abs(low[2] - ground) <= touch or low[2] < ground:
            continue
        meets = False
        for other, (olow, ohigh) in boxes.items():
            if other == name:
                continue
            if all(low[k] - grow <= ohigh[k] and high[k] + grow >= olow[k] for k in range(3)):
                meets = True
                break
        if not meets:
            loose.append('%s (lowest point z = %.3f)' % (name, low[2]))
    return loose


def other_values(text):
    """From an option's card text, values other than its default to build the part with: a boolean turned round, every
    other quoted choice, or a number one and a half times the default (5 for 0). None if the default cannot be read."""
    text = text.strip()
    match = re.search(r"\(default ([^)]*)\)", text)
    default = match.group(1).split(';')[0].strip() if match else None
    if default is None:
        match = re.match(r"^('[^']*'|True|False|-?[\d.]+)\s*\(default\)", text)
        default = match.group(1) if match else None
    if default is None:
        return None
    if default in ('True', 'False'):
        return [default != 'True']
    if default.startswith("'"):
        others = [v for v in re.findall(r"'([^']*)'", text) if v != default.strip("'")]
        return others or None
    try:
        number = float(default) if '.' in default else int(default)
    except ValueError:
        return None
    if number == 0:
        return [5]
    return [round(number * 1.5, 3) if isinstance(number, float) else int(round(number * 1.5))]


# options that move the part's foot, as their cards say: (part, option) -> where the foot is, from the value given
# and the card's own foot (the ore car stands on rails 0.18 m up; the teapot sign hangs from its bracket's height)
OPTION_FOOT = {('ore_car', 'on_rails'): lambda value, foot: 0.18,
               ('teapot_sign', 'height'): lambda value, foot: foot + (float(value) - 3.0)}


def check_build(name, objects, foot, label):
    """The checks every build of a part must pass: foot on the ground, every piece at scale 1 with a material, no
    piece floating."""
    low, high = bounds(objects)
    check(abs(low.z - foot) <= 0.06, '%s%s: its foot is at z = %.3f, its card says %.2f' % (name, label, low.z, foot))
    for obj in objects:
        check(all(abs(s - 1.0) < 1e-4 for s in obj.scale), '%s%s: %s is scaled %s (apply its scale)' % (name, label, obj.name, tuple(obj.scale)))
        check(len(obj.data.materials) > 0 and all(m is not None for m in obj.data.materials), '%s%s: %s has an empty material slot' % (name, label, obj.name))
    loose = floating(objects, ground=foot)
    check(not loose, '%s%s: floating, touching neither the ground nor another piece: %s' % (name, label, '; '.join(loose)))
    return low, high


def fingerprint(objects):
    """One number from every point of every mesh, in the world: the same part gives the same number."""
    import numpy
    total = 0.0
    for obj in objects:
        if obj.type != 'MESH' or not obj.data.vertices:
            continue
        points = numpy.empty(len(obj.data.vertices) * 3, dtype=numpy.float64)
        obj.data.vertices.foreach_get('co', points)
        points = points.reshape(-1, 3)
        matrix = numpy.array(obj.matrix_world)
        world = points @ matrix[:3, :3].T + matrix[:3, 3]
        total += float(numpy.abs(world).sum())
    return round(total, 3)


def main():
    names = store.names('parts')
    check(names, 'the store has no parts')
    for name in names:
        card = store.part_card(name)
        for key in ('what', 'size_m', 'source', 'views', 'materials'):
            check(key in card and card[key] not in (None, ''), '%s: CARD has no %r' % (name, key))
        root, objects = build(name, 0)
        check(objects, '%s built nothing' % name)
        foot = float(card.get('foot_z', 0.0))      # a wall sign hangs above its origin (the foot of its wall); its card says how far
        low, high = check_build(name, objects, foot, '')
        count = len(objects)
        size = high - low
        centre = (low + high) / 2
        if 'foot_z' not in card:
            check(abs(centre.x) <= max(0.3, size.x * 0.35) and abs(centre.y) <= max(0.3, size.y * 0.35),
                  '%s: not centred on the origin (centre %.2f, %.2f)' % (name, centre.x, centre.y))
        for given, measured, axis in zip(card['size_m'], size, 'xyz'):
            check(abs(measured - float(given)) <= max(0.06, 0.25 * float(given)),
                  '%s: %s size %.2f m, its card says %.2f m' % (name, axis, measured, float(given)))
        # every option, set to something other than its default
        tried = []
        for key, text in (card.get('options') or {}).items():
            if key == 'seed':
                continue
            values = other_values(text)
            if values is None:
                print('note: %s: cannot read the default of %r from its card (%s); not built with it' % (name, key, text[:60]))
                continue
            for value in values:
                fresh_scene()
                store.add_part(name, seed=0, **{key: value})
                bpy.context.view_layer.update()
                built = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE')]
                check(built, '%s built nothing with %s=%r' % (name, key, value))
                moved = OPTION_FOOT.get((name, key))
                check_build(name, built, moved(value, foot) if moved else foot, ' with %s=%r' % (key, value))
                tried.append('%s=%r' % (key, value))
        first = fingerprint(build(name, 0)[1])
        same = fingerprint(build(name, 0)[1])
        check(abs(same - first) < 1e-3, '%s: the same seed built a different part' % name)
        other = fingerprint(build(name, 7)[1])
        if abs(other - same) < 1e-6:
            print('note: %s looks the same with another seed' % name)
        path = os.path.join(STORE, 'parts', name + '.blend')
        check(os.path.exists(path), '%s: no part file %s (store.save_part_file)' % (name, path))
        with bpy.data.libraries.load(path, link=False) as (source, _):
            in_file = list(source.objects)
        check(any(o.startswith(name) for o in in_file), '%s: its part file holds none of its objects (%s)' % (name, in_file[:5]))
        for view in ('three', 'close', 'side', 'back'):
            check(os.path.exists(os.path.join(STORE, 'cards', 'parts', '%s - %s.png' % (name, view))), '%s: no %s card' % (name, view))
        fresh_scene()
        try:
            store.add_part(name, no_such_option=1)
            check(False, '%s took an option it does not have without a word' % name)
        except TypeError as problem:
            check('no_such_option' in str(problem), '%s: the error for a wrong option does not name it: %s' % (name, problem))
        check(not bpy.data.collections, '%s: a refused option left a collection behind' % name)
        print('PASS %s: %.2f x %.2f x %.2f m, %d objects, foot at z = %.3f, nothing floating, four cards, a wrong option refused; also built with %s'
              % (name, size.x, size.y, size.z, count, low.z, ', '.join(tried) or 'no options'))
    print('PASS test_store_parts: %d parts' % len(names))


if __name__ == '__main__':
    main()
