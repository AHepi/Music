"""
What this file does: checks the garden's bridge and plant parts (arched_bridge, maple_tree, garden_pine, fern,
bamboo_clump), first with every check the parts test makes on each part (a CARD, the foot at the card's height, the
card's size, every piece at scale 1 with a material, nothing floating, every option built, the same seed the same part,
the part file and its four cards, a wrong option refused), then what each one is said to be:
  - arched_bridge: the deck's crown stands `rise` over its ends, which are 0.35 m over the water at -span/2 and +span/2;
    the posts stand on the pond bed 0.5 m down; the paint is laid over the shelf's photographed planks and worn where
    the number 'pp_bare' says (on the handrail's top), every timber, board and stone carries its own 'pp_piece';
    caps='wood' leaves out the bronze caps; a wider, longer, higher bridge measures so;
  - maple_tree: its leaves are seven-lobed outlines with a 'tone' on each and the UV map 'leaf' for the veins, its
    bark is the shelf's photograph; each colour gives its own leaf material; fullness=0.5 has about half the leaves;
  - garden_pine: one needle pad more than `pads` (the top one), each with needle tufts; more pads with pads=14;
  - fern: as many fronds as asked (each frond its own stalk), its pinnae lobed;
  - bamboo_clump: as many culms as asked, each with its age, nodes ('ring') and waxy bands ('band'), the tallest at
    the height asked; sheaths on the young culms.
    python3 tests/test_store_garden_plants.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import STORE, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import store  # noqa: E402
import test_store_parts as parts_test  # noqa: E402

PARTS = ['arched_bridge', 'maple_tree', 'garden_pine', 'fern', 'bamboo_clump']


def objects_of(root):
    return [o for o in root.children_recursive if o.type == 'MESH']


def by_name(objects, word):
    found = [o for o in objects if word in o.name]
    check(found, 'no object named with %r among %s' % (word, [o.name for o in objects]))
    return found[0]


def world_points(obj):
    import numpy
    points = numpy.empty(len(obj.data.vertices) * 3, dtype=numpy.float64)
    obj.data.vertices.foreach_get('co', points)
    points = points.reshape(-1, 3)
    matrix = numpy.array(obj.matrix_world)
    return points @ matrix[:3, :3].T + matrix[:3, 3]


def attribute_values(obj, name):
    import numpy
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no number %r' % (obj.name, name))
    values = numpy.empty(len(attribute.data), dtype=numpy.float64)
    attribute.data.foreach_get('value', values)
    return attribute.domain, values


def common_checks(name):
    """Every check test_store_parts.py makes, for one part."""
    card = store.part_card(name)
    for key in ('what', 'size_m', 'source', 'views', 'materials'):
        check(key in card and card[key] not in (None, ''), '%s: CARD has no %r' % (name, key))
    root, objects = parts_test.build(name, 0)
    check(objects, '%s built nothing' % name)
    foot = float(card.get('foot_z', 0.0))
    low, high = parts_test.check_build(name, objects, foot, '')
    size = high - low
    centre = (low + high) / 2
    if 'foot_z' not in card:
        check(abs(centre.x) <= max(0.3, size.x * 0.35) and abs(centre.y) <= max(0.3, size.y * 0.35),
              '%s: not centred on the origin (centre %.2f, %.2f)' % (name, centre.x, centre.y))
    for given, measured, axis in zip(card['size_m'], size, 'xyz'):
        check(abs(measured - float(given)) <= max(0.06, 0.25 * float(given)),
              '%s: %s size %.2f m, its card says %.2f m' % (name, axis, measured, float(given)))
    tried = []
    for key, text in (card.get('options') or {}).items():
        if key == 'seed':
            continue
        values = parts_test.other_values(text)
        check(values is not None, '%s: cannot read the default of %r from its card' % (name, key))
        for value in values:
            fresh_scene()
            store.add_part(name, seed=0, **{key: value})
            bpy.context.view_layer.update()
            built = [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE')]
            check(built, '%s built nothing with %s=%r' % (name, key, value))
            parts_test.check_build(name, built, foot, ' with %s=%r' % (key, value))
            tried.append('%s=%r' % (key, value))
    first = parts_test.fingerprint(parts_test.build(name, 0)[1])
    same = parts_test.fingerprint(parts_test.build(name, 0)[1])
    check(abs(same - first) < 1e-3, '%s: the same seed built a different part' % name)
    other = parts_test.fingerprint(parts_test.build(name, 7)[1])
    check(abs(other - same) > 1e-6, '%s looks the same with another seed' % name)
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
    print('PASS %s: %.2f x %.2f x %.2f m, foot at z = %.3f, nothing floating, four cards, part file, a wrong option '
          'refused; also built with %s' % (name, size.x, size.y, size.z, low.z, ', '.join(tried)))


def bridge_checks():
    import numpy
    for span, width, rise in ((4.0, 1.3, 0.8), (6.0, 1.8, 1.2), (3.0, 1.0, 0.5)):
        fresh_scene()
        root = store.add_part('arched_bridge', span=span, width=width, rise=rise)
        bpy.context.view_layer.update()
        objects = objects_of(root)
        deck = world_points(by_name(objects, 'deck'))
        crown = deck[numpy.abs(deck[:, 0]) < 0.12][:, 2].max()
        ends = deck[numpy.abs(deck[:, 0]) > span / 2 - 0.12][:, 2].max()
        check(abs(crown - (0.35 + rise)) < 0.05, 'arched_bridge rise %.2f: its deck crown is at %.3f m, not %.3f' % (rise, crown, 0.35 + rise))
        check(ends < 0.35 + 0.2, 'arched_bridge span %.1f: its deck ends at %.3f m, not about 0.35 m over the water' % (span, ends))
        check(abs((deck[:, 0].max() - deck[:, 0].min()) - span) < 0.1, 'arched_bridge span %.1f: its deck runs %.2f m'
              % (span, deck[:, 0].max() - deck[:, 0].min()))
        check(abs((deck[:, 1].max() - deck[:, 1].min()) - width) < 0.06, 'arched_bridge width %.1f: its deck is %.2f m across'
              % (width, deck[:, 1].max() - deck[:, 1].min()))
        posts = world_points(by_name(objects, 'posts'))
        check(abs(posts[:, 2].min() + 0.5) < 0.01, 'arched_bridge: its posts stop at %.3f, not the pond bed at -0.5' % posts[:, 2].min())
        for obj in objects:
            if 'caps' in obj.name:
                continue
            domain, values = attribute_values(obj, 'pp_piece')
            check(domain == 'FACE' and len(set(numpy.round(values, 6))) > 1, '%s: its pieces do not each have their own pp_piece' % obj.name)
    paint = by_name(objects, 'stringers').data.materials[0]
    check(paint.name.startswith('SURFACE • old_planks_02 ('), 'arched_bridge: the paint is not over the photographed planks (%s)' % paint.name)
    pictures = [n.image.name for n in paint.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    check(len(pictures) >= 4, 'arched_bridge: the paint lost its photographs (%s)' % pictures)
    check(any(n.type == 'ATTRIBUTE' and n.attribute_name == 'pp_bare' for n in paint.node_tree.nodes), 'arched_bridge: the paint does not read pp_bare')
    domain, bare = attribute_values(by_name(objects, 'stringers'), 'pp_bare')
    check(bare.max() > 0.9 and bare.min() < 0.3, 'arched_bridge: no worn handrail top (pp_bare from %.2f to %.2f)' % (bare.min(), bare.max()))
    check(any('caps' in o.name for o in objects), 'arched_bridge: no bronze caps')
    fresh_scene()
    root = store.add_part('arched_bridge', caps='wood')
    check(not any('caps' in o.name for o in objects_of(root)), "arched_bridge caps='wood' still made bronze caps")
    print('PASS arched_bridge: the deck crown stands rise over ends 0.35 m over the water, span and width as asked (three '
          'sizes), posts on the pond bed, every piece its own pp_piece, paint over the photographed planks worn on the '
          "handrail top, caps='wood' without bronze")


def maple_checks():
    import numpy
    counts = {}
    for colour in ('red', 'orange', 'green'):
        fresh_scene()
        root = store.add_part('maple_tree', colour=colour)
        leaves = by_name(objects_of(root), 'leaves')
        material = leaves.data.materials[0]
        check(material.name == 'PART • maple_tree: leaves, ' + colour, 'maple_tree colour=%r gave the leaf material %r' % (colour, material.name))
        counts[colour] = len(leaves.data.polygons)
    domain, tones = attribute_values(leaves, 'tone')
    check(domain == 'FACE' and tones.std() > 0.1, 'maple_tree: its leaves do not each carry their own tone')
    check('leaf' in leaves.data.uv_layers, 'maple_tree: its leaves have no UV map leaf for the veins')
    sizes = numpy.array([len(p.vertices) for p in leaves.data.polygons])
    check(sizes.min() == sizes.max() and sizes[0] >= 40, 'maple_tree: its leaves are not whole maple outlines (%d to %d points)' % (sizes.min(), sizes.max()))
    # seven lobes: seven points of the outline further out than both neighbours by a good margin
    import _shapes_garden_plants as plants
    outline = plants.maple_outline()
    radius = [(x * x + y * y) ** 0.5 for x, y in outline]
    tips = [i for i in range(len(outline)) if radius[i] > 0.35 and radius[i] >= radius[i - 1] and radius[i] >= radius[(i + 1) % len(outline)]
            and radius[i] > 1.12 * min(radius[i - 3], radius[(i + 3) % len(outline)])]
    check(len(tips) == 7, 'maple_tree: the leaf outline has %d lobes, not 7' % len(tips))
    wood = by_name(objects_of(root), 'wood')
    check(wood.data.materials[0].name.startswith('SURFACE • bark_willow_02'), 'maple_tree: the bark is not the shelf photograph')
    fresh_scene()
    root = store.add_part('maple_tree', fullness=0.5)
    half = len(by_name(objects_of(root), 'leaves').data.polygons)
    check(0.35 * counts['green'] < half < 0.65 * counts['green'], 'maple_tree fullness=0.5: %d leaves against %d' % (half, counts['green']))
    print('PASS maple_tree: %d leaves, each a whole seven-lobed outline of %d points with its own tone and the UV map leaf; '
          'a leaf material for each colour; fullness=0.5 has %d; the bark photographed' % (counts['green'], sizes[0], half))


def pine_checks():
    for pads in (9, 14):
        fresh_scene()
        root = store.add_part('garden_pine', pads=pads)
        objects = objects_of(root)
        hearts = by_name(objects, 'pad hearts')
        islands = len(hearts.data.vertices) // (7 * 18 + 2)
        check(islands == pads + 1, 'garden_pine pads=%d: %d pads, not %d (the top one too)' % (pads, islands, pads + 1))
        needles = by_name(objects, 'needles')
        check(len(needles.data.polygons) > 1500 * (pads + 1), 'garden_pine: only %d needles' % len(needles.data.polygons))
    check(by_name(objects, 'wood').data.materials[0].name.startswith('SURFACE • bark_willow_02'), 'garden_pine: the bark is not the shelf photograph')
    print('PASS garden_pine: one pad more than asked (the top one) at 9 and 14, each with needle tufts (%d needles); '
          'the bark photographed' % len(needles.data.polygons))


def fern_checks():
    import numpy
    for fronds in (12, 20):
        fresh_scene()
        root = store.add_part('fern', fronds=fronds)
        objects = objects_of(root)
        stalks = by_name(objects, 'stalks')
        # each frond's stalk is a 5-sided sweep of 17 rings; the two fiddleheads are 6-sided
        count = sum(1 for p in stalks.data.polygons if len(p.vertices) == 5) // 2
        check(count == fronds, 'fern fronds=%d: %d fronds' % (fronds, count))
        blades = by_name(objects, 'fronds')
        sizes = numpy.array([len(p.vertices) for p in blades.data.polygons])
        check(sizes.min() >= 20, 'fern: its pinnae are not lobed (%d points)' % sizes.min())
    print('PASS fern: as many fronds as asked (12 and 20), %d lobed pinnae' % len(blades.data.polygons))


def bamboo_checks():
    import numpy
    for culms, height in ((9, 6.0), (4, 4.0), (16, 8.0)):
        fresh_scene()
        root = store.add_part('bamboo_clump', culms=culms, height=height)
        objects = objects_of(root)
        stems = by_name(objects, 'culms')
        domain, ages = attribute_values(stems, 'age')
        found = len(set(numpy.round(ages[ages > -1], 9)))
        check(found == culms, 'bamboo_clump culms=%d: %d culms' % (culms, found))
        top = world_points(stems)[:, 2].max()
        check(abs(top - height) < 0.12 * height, 'bamboo_clump height=%.1f: the tallest culm reaches %.2f' % (height, top))
        for name in ('band', 'ring'):
            domain, values = attribute_values(stems, name)
            check(values.max() > 0.9, 'bamboo_clump: no %s at the nodes' % name)
        check(any('sheaths' in o.name for o in objects), 'bamboo_clump: no sheaths')
    print('PASS bamboo_clump: as many culms as asked at three sizes, the tallest at the height asked, nodes with rings and '
          'waxy bands, sheaths')


def main():
    for name in PARTS:
        check(name in store.names('parts'), 'the store has no part %s' % name)
        common_checks(name)
    bridge_checks()
    maple_checks()
    pine_checks()
    fern_checks()
    bamboo_checks()
    print('PASS test_store_garden_plants: %d parts' % len(PARTS))


if __name__ == '__main__':
    try:
        main()
    except AssertionError as problem:
        print('FAIL', problem)
        sys.exit(1)
