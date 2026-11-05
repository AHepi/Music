"""
What this file does: checks what the garden's closer pass (log 58) added to the store's plants and lanterns:
  - azalea (a new part): every check the parts test makes (a CARD, the foot on the ground, the card's size, every
    piece with a material, nothing floating, every option built, the same seed the same part, the part file and its
    four cards, a wrong option refused); then that it is what it says: clipped mounds as tall as asked, run together
    along X when asked; a skin of leaf rosettes (live copies, each with its own tone); flowers as live copies of the
    flower shapes (five notched lobes, 'petal' and 'blotch' on their points) facing out of the mound; each colour its
    own material; fewer flowers at a lower bloom, none at bloom 0; out of flower no flowers, a denser skin and pale new
    shoots;
  - hedge flowers: a hedge laid with flowers=0 is the hedge as it was (three objects, the same sprays); with flowers
    it has a fourth object of flowers about as many as its skin carries (260 to the square metre at flowers=1), along
    its line and above its foot, the sprays unchanged; the colour and a material of your own are taken; wrong values
    refused;
  - maple_tree trunk: 0 (the default) and a value under where the tree divides of itself build the tree as before;
    trunk=2.4 lifts the whole crown (its lowest leaves above 2.3 m) on a taller trunk, its flared foot unchanged;
  - hanging_lantern glow: its light 22 W times glow, its paper (and the glazed kind's candle flame) glow ** 1.5 as
    bright on its own copy of the material, the shared paper untouched; unlit, nothing glows; wrong values refused;
  - stone_lantern light: its light as many watts as asked when lit (18 by default), none unlit; wrong values refused.
    python3 tests/test_store_garden_closer.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
import store  # noqa: E402
import test_store_garden_plants as plants_test  # noqa: E402


def objects_of(root):
    return [o for o in root.children_recursive if o.type in ('MESH', 'LIGHT')]


def named(root, word):
    found = [o for o in objects_of(root) if word in o.name]
    return found[0] if found else None


def points_of(obj):
    return plants_test.world_points(obj)


def values(obj, name, kind='value', width=1):
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no number %r' % (obj.name, name))
    out = numpy.empty(len(attribute.data) * width, dtype=numpy.float64)
    attribute.data.foreach_get(kind, out)
    return out.reshape(-1, width) if width > 1 else out


def refused(make):
    try:
        make()
    except (ValueError, TypeError):
        return True
    return False


def turns(eulers):
    """3x3 turns from Blender's XYZ angles (Rz @ Ry @ Rx), as the copies are turned."""
    x, y, z = eulers[:, 0], eulers[:, 1], eulers[:, 2]
    cx, sx, cy, sy, cz, sz = numpy.cos(x), numpy.sin(x), numpy.cos(y), numpy.sin(y), numpy.cos(z), numpy.sin(z)
    out = numpy.zeros((len(eulers), 3, 3))
    out[:, 0, 0], out[:, 0, 1], out[:, 0, 2] = cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx
    out[:, 1, 0], out[:, 1, 1], out[:, 1, 2] = sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx
    out[:, 2, 0], out[:, 2, 1], out[:, 2, 2] = -sy, cy * sx, cy * cx
    return out


# ------------------------------------------------------------------------------------------------ the azalea

def azalea_checks():
    plants_test.common_checks('azalea')
    fresh_scene()
    root = store.add_part('azalea')
    inside, leaves, flowers = named(root, 'inside'), named(root, 'leaves'), named(root, 'flowers')
    check(inside and leaves and flowers, 'azalea: not its inside, leaves and flowers: %s' % [o.name for o in objects_of(root)])
    skin = points_of(inside)
    check(abs(skin[:, 2].max() - 0.7) < 0.08, 'azalea: its top is at %.2f m, not about 0.7' % skin[:, 2].max())
    check(abs(skin[:, 2].min()) < 0.01, 'azalea: its skin does not come down to the ground (%.3f)' % skin[:, 2].min())
    across = skin[:, 0].max() - skin[:, 0].min()
    check(abs(across - 1.2) < 0.15, 'azalea: one mound is %.2f m across, not about 1.2' % across)
    # the leaves: live copies of the rosettes, each with its own tone
    check(any(m.type == 'NODES' for m in leaves.modifiers), 'azalea: its leaves are not live copies')
    rosettes = len(leaves.data.vertices)
    check(rosettes > 3000, 'azalea: only %d leaf rosettes' % rosettes)
    tone = values(leaves, 'leaf_tone')
    check(tone.std() > 0.15, 'azalea: its rosettes do not each have their own tone')
    shapes = values(leaves, 'leaf_shape')
    check(shapes.min() >= 0 and shapes.max() <= 5 and len(set(shapes.astype(int))) == 6, 'azalea: not all six rosette shapes used')
    # the flowers: live copies of the flower shapes, facing out of the mound
    check(any(m.type == 'NODES' for m in flowers.modifiers), 'azalea: its flowers are not live copies')
    count = len(flowers.data.vertices)
    check(count > 800, 'azalea in flower (bloom 0.85) has only %d flowers' % count)
    check(flowers.data.materials[0].name == 'PART • azalea: flowers, pink', 'azalea: flowers in %r' % flowers.data.materials[0].name)
    where = points_of(flowers)
    facing = turns(values(flowers, 'flower_rotation', 'vector', 3))[:, :, 2]
    outward = where - numpy.array([0.0, 0.0, 0.25])
    out_share = float(numpy.mean(numpy.sum(facing * outward, axis=1) > 0))
    check(out_share > 0.85, 'azalea: only %.0f%% of its flowers face out of the mound' % (100 * out_share))
    high = float(numpy.mean(where[:, 2] > 0.35))
    check(high > 0.55, 'azalea: only %.0f%% of its flowers are on its upper half' % (100 * high))
    shape_objects = [o for o in bpy.data.collections['flower shapes • PART • azalea: flowers, pink'].objects]
    check(len(shape_objects) == 6, 'azalea: %d flower shapes, not 6' % len(shape_objects))
    open_flower = shape_objects[0].data
    for name in ('petal', 'blotch'):
        check(open_flower.attributes.get(name) is not None, 'azalea: the flower shape has no %r' % name)
    rim = numpy.array([v.co[:] for v in open_flower.vertices])[41:61]          # the outer ring (the throat, then three rings of 20)
    radius = numpy.hypot(rim[:, 0], rim[:, 1])
    lobes = sum(1 for i in range(20) if radius[i] > radius[i - 1] and radius[i] >= radius[(i + 1) % 20])
    check(lobes == 5, 'azalea: the open flower has %d lobes, not 5' % lobes)
    blotch = values(open_flower and shape_objects[0], 'blotch')
    check(blotch.max() > 0.5, 'azalea: no spots on the upper lobe')
    # each colour its own material; fewer flowers at a lower bloom, none at bloom 0; out of flower
    for colour in ('magenta', 'white'):
        fresh_scene()
        other = named(store.add_part('azalea', colour=colour), 'flowers')
        check(other.data.materials[0].name == 'PART • azalea: flowers, %s' % colour, 'azalea colour=%r gave %r' % (colour, other.data.materials[0].name))
    fresh_scene()
    few = len(named(store.add_part('azalea', bloom=0.3), 'flowers').data.vertices)
    check(0.15 * count < few < 0.6 * count, 'azalea bloom=0.3 has %d flowers against %d at 0.85' % (few, count))
    fresh_scene()
    check(named(store.add_part('azalea', bloom=0.0), 'flowers') is None, 'azalea bloom=0 still has flowers')
    fresh_scene()
    green = store.add_part('azalea', flowering=False)
    check(named(green, 'flowers') is None, 'azalea out of flower still has flowers')
    dense = len(named(green, 'leaves').data.vertices)
    check(1.3 * rosettes < dense < 1.7 * rosettes, 'azalea out of flower has %d rosettes against %d in flower' % (dense, rosettes))
    shoots = float(numpy.mean(values(named(green, 'leaves'), 'leaf_tone') > 0.85))
    check(0.03 < shoots < 0.3, 'azalea out of flower: %.0f%% pale new shoots' % (100 * shoots))
    # several mounds run together, the size and height asked
    fresh_scene()
    run = points_of(named(store.add_part('azalea', mounds=3), 'inside'))
    length = run[:, 0].max() - run[:, 0].min()
    check(1.8 < length < 3.4, 'azalea mounds=3 runs %.2f m along X' % length)
    check(run[:, 2].max() < 0.7 + 0.06, 'azalea mounds=3: a mound stands %.2f m, taller than asked' % run[:, 2].max())
    check(abs((run[:, 0].max() + run[:, 0].min()) / 2) < 0.1, 'azalea mounds=3 is not centred on the origin')
    fresh_scene()
    big = points_of(named(store.add_part('azalea', size=2.0, height=0.9), 'inside'))
    check(abs((big[:, 0].max() - big[:, 0].min()) - 2.0) < 0.2 and abs(big[:, 2].max() - 0.9) < 0.1,
          'azalea size=2, height=0.9 is %.2f m across and %.2f m tall' % (big[:, 0].max() - big[:, 0].min(), big[:, 2].max()))
    for wrong in ({'colour': 'blue'}, {'bloom': 2.0}, {'mounds': 0}, {'height': 1.5, 'size': 1.0}):
        fresh_scene()
        check(refused(lambda: store.add_part('azalea', **wrong)), 'azalea took %s' % wrong)
    print('PASS azalea: clipped mound 0.7 m tall and 1.2 m across, %d leaf rosettes (live copies, each its own tone, six '
          'shapes), %d flowers (live copies of six shapes, five lobes, spotted upper lobe, %.0f%% facing out, %.0f%% on its '
          'upper half); its own material for each colour; %d flowers at bloom 0.3, none at 0; out of flower no flowers, '
          '%d rosettes, %.0f%% new shoots; three mounds run %.2f m; size and height as asked; wrong values refused'
          % (rosettes, count, 100 * out_share, 100 * high, few, dense, 100 * shoots, length))


# ------------------------------------------------------------------------------------------------ the hedge's flowers

def hedge_flower_checks():
    import hedge
    line = [(0.0, 0.0, 0.0), (3.0, 0.6, 0.0), (6.0, 0.2, 0.0)]
    fresh_scene()
    plain = hedge.lay(line, height=0.9, width=1.0, raggedness=0.3, twigs=0.0, dry=0.0, seed=3)
    check(sorted(plain) == ['core', 'sprays', 'twigs'], 'a hedge without flowers made %s' % sorted(plain))
    sprays_before = points_of(plain['sprays'])
    fresh_scene()
    made = hedge.lay(line, height=0.9, width=1.0, raggedness=0.3, twigs=0.0, dry=0.0, seed=3, flowers=1.0)
    check(sorted(made) == ['core', 'flowers', 'sprays', 'twigs'], 'a hedge in flower made %s' % sorted(made))
    check(numpy.allclose(points_of(made['sprays']), sprays_before), 'flowers changed the hedge itself')
    flowers = made['flowers']
    count = len(flowers.data.vertices)
    check(flowers['flowers'] == count, "the hedge's flowers count %r, not %d" % (flowers['flowers'], count))
    length = made['sprays']['length']
    skin = (2 * 0.9 + 1.0) * length
    check(0.6 * 260 * skin < count < 1.4 * 260 * skin, 'the hedge in flower has %d flowers on about %.1f m2 of skin' % (count, skin))
    where = points_of(flowers)
    check(where[:, 2].min() > -0.05 and where[:, 2].max() < 0.9 * 1.4 + 0.3, "the hedge's flowers go from %.2f to %.2f m up" % (where[:, 2].min(), where[:, 2].max()))
    import dry_wall
    path = dry_wall.Line(line, smooth=True)
    on_line = numpy.array([tuple(path.path.at(float(u)))[:2] for u in numpy.linspace(0.0, path.total, 400)])
    away = numpy.linalg.norm(where[:, None, :2] - on_line[None, :, :], axis=2).min(axis=1)
    # within half its width and the reach of a spray (up to 0.58 m: the flowers sit in the sprays' leafy fans)
    check(away.max() < 1.0 / 2 + 0.7, "a flower of the hedge lies %.2f m from its line" % away.max())
    check(any(m.type == 'NODES' for m in flowers.modifiers), "the hedge's flowers are not live copies")
    check(flowers.data.materials[0].name == 'hedge flowers • pink', "the hedge's flowers are in %r" % flowers.data.materials[0].name)
    fresh_scene()
    half = hedge.lay(line, height=0.9, width=1.0, raggedness=0.3, twigs=0.0, dry=0.0, seed=3, flowers=0.4, flower_colour='white')
    few = len(half['flowers'].data.vertices)
    check(0.2 * count < few < 0.6 * count, 'flowers=0.4 gave %d flowers against %d at 1' % (few, count))
    check(half['flowers'].data.materials[0].name == 'hedge flowers • white', 'flower_colour white gave %r' % half['flowers'].data.materials[0].name)
    fresh_scene()
    mine = bpy.data.materials.new('my blossom')
    own = hedge.lay(line, height=0.9, width=1.0, seed=3, flowers=0.5, flowers_material=mine)
    check(own['flowers'].data.materials[0] == mine, 'a material of my own for the flowers was not used')
    for wrong in ({'flowers': 2.0}, {'flowers': -0.1}, {'flowers': 0.5, 'flower_colour': 'blue'}):
        fresh_scene()
        check(refused(lambda: hedge.lay(line, **wrong)), 'the hedge took %s' % wrong)
    check('flowers' in hedge.TOOL['options'] and 'flower_colour' in hedge.TOOL['options'], "the hedge's TOOL does not list its flower options")
    print('PASS hedge flowers: without them the hedge is as it was; flowers=1 adds %d flowers (about %.0f to the square metre of '
          'skin) as live copies along its line, the sprays unchanged; flowers=0.4 %d, in white; a material of my own taken; '
          'wrong values refused' % (count, count / skin, few))


# ------------------------------------------------------------------------------------------------ the maple's trunk

def maple_trunk_checks():
    def build(**options):
        fresh_scene()
        root = store.add_part('maple_tree', **options)
        bpy.context.view_layer.update()
        return points_of(named(root, 'wood')), points_of(named(root, 'leaves'))
    wood, leaves = build()
    same_wood, same_leaves = build(trunk=0.0)
    check(numpy.allclose(wood, same_wood) and numpy.allclose(leaves, same_leaves), 'maple_tree trunk=0 is not the tree as before')
    low_wood, low_leaves = build(trunk=0.4)
    check(numpy.allclose(wood, low_wood) and numpy.allclose(leaves, low_leaves), 'maple_tree trunk=0.4 (under where it divides) changed the tree')
    tall_wood, tall_leaves = build(trunk=2.4)
    check(tall_leaves[:, 2].min() > 2.3, 'maple_tree trunk=2.4: its lowest leaves are at %.2f m' % tall_leaves[:, 2].min())
    top = max(tall_wood[:, 2].max(), tall_leaves[:, 2].max())
    check(5.3 < top < 6.7, 'maple_tree trunk=2.4: its top is at %.2f m' % top)
    flare = wood[:, 2] < 0.1
    check(numpy.allclose(wood[flare][:, 2], tall_wood[flare][:, 2], atol=1e-4), 'maple_tree trunk=2.4 changed the height of its flared foot')
    lift = tall_leaves[:, 2] - leaves[:, 2]
    check(lift.std() < 1e-3 and abs(lift.mean() - (top - max(wood[:, 2].max(), leaves[:, 2].max()))) < 1e-3, 'maple_tree trunk=2.4 did not lift the crown whole')
    fresh_scene()
    check(refused(lambda: store.add_part('maple_tree', trunk=9.0)), 'maple_tree took trunk=9')
    print('PASS maple_tree trunk: 0 and 0.4 build the tree as before; 2.4 lifts the whole crown by %.2f m (lowest leaves %.2f m, '
          'top %.2f m), its flared foot unchanged; 9 refused' % (lift.mean(), tall_leaves[:, 2].min(), top))


# ------------------------------------------------------------------------------------------------ the lanterns

def glowing(root):
    found = {}
    for obj in root.children_recursive:
        if obj.type != 'MESH':
            continue
        for material in obj.data.materials:
            for n in material.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED' and n.inputs['Emission Strength'].default_value > 0:
                    found[material.name] = n.inputs['Emission Strength'].default_value
    return found


def lantern_checks():
    watts = lambda root: [o.data.energy for o in root.children_recursive if o.type == 'LIGHT']
    fresh_scene()
    root = store.add_part('hanging_lantern')
    check(watts(root) == [22.0], 'hanging_lantern: its light is %s W, not 22' % watts(root))
    check(glowing(root) == {'PART • garden: lantern paper, lit': 3.5}, 'hanging_lantern: its paper glows %s' % glowing(root))
    fresh_scene()
    root = store.add_part('hanging_lantern', glow=0.25)
    check(abs(watts(root)[0] - 5.5) < 1e-4, 'hanging_lantern glow=0.25: its light is %s W, not 5.5' % watts(root))
    glow = glowing(root)
    check(list(glow) == ['PART • garden: lantern paper, lit, glow 0.25'] and abs(glow['PART • garden: lantern paper, lit, glow 0.25'] - 3.5 * 0.125) < 1e-4,
          'hanging_lantern glow=0.25: its paper glows %s' % glow)
    shared = bpy.data.materials['PART • garden: lantern paper, lit']
    check(next(n for n in shared.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Emission Strength'].default_value == 3.5,
          'hanging_lantern glow=0.25 turned the shared paper down')
    fresh_scene()
    root = store.add_part('hanging_lantern', kind='glass', glow=0.25)
    check(abs(glowing(root).get('PART • hanging_lantern: candle flame, glow 0.25', 0) - 25.0 * 0.125) < 1e-4, 'hanging_lantern glass glow=0.25: the flame glows %s' % glowing(root))
    fresh_scene()
    root = store.add_part('hanging_lantern', kind='round', glow=2.0)
    check(abs(watts(root)[0] - 44.0) < 1e-4 and abs(list(glowing(root).values())[0] - 3.5 * 2 ** 1.5) < 1e-3, 'hanging_lantern round glow=2: %s W, %s' % (watts(root), glowing(root)))
    fresh_scene()
    root = store.add_part('hanging_lantern', lit=False, glow=0.25)
    check(not watts(root) and not glowing(root), 'hanging_lantern unlit with glow=0.25 still glows')
    for wrong in (0.0, 4.0, 'bright'):
        fresh_scene()
        check(refused(lambda: store.add_part('hanging_lantern', glow=wrong)), 'hanging_lantern took glow=%r' % (wrong,))
    for options, wanted in (({'lit': True}, [18.0]), ({'lit': True, 'light': 30}, [30.0]), ({'lit': True, 'kind': 'yukimi', 'light': 40}, [40.0]),
                            ({'light': 30}, [])):
        fresh_scene()
        got = watts(store.add_part('stone_lantern', **options))
        check(got == wanted, 'stone_lantern %s: its light is %s W, not %s' % (options, got, wanted))
    for wrong in (1.0, 500.0, 'strong'):
        fresh_scene()
        check(refused(lambda: store.add_part('stone_lantern', lit=True, light=wrong)), 'stone_lantern took light=%r' % (wrong,))
    print('PASS lanterns: hanging_lantern 22 W and the shared paper at glow 1; glow=0.25 gives 5.5 W and its own paper at an '
          'eighth (the shared paper untouched), the glazed kind its flame at an eighth, glow=2 twice the light; unlit nothing '
          'glows; stone_lantern 18 W lit, 30 and 40 W as asked, none unlit; wrong values refused')


def main():
    check('azalea' in store.names('parts'), 'the store has no part azalea')
    azalea_checks()
    hedge_flower_checks()
    maple_trunk_checks()
    lantern_checks()
    print('PASS test_store_garden_closer')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as problem:
        print('FAIL', problem)
        sys.exit(1)
