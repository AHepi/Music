"""
What this file does: checks the ground and water tools the Japanese garden set brought to the store (build 57) against
what they promise. The slab path: its slabs follow their line within its width, never overlap one another, each its
own part of the photograph; water stands only inside its own slab, flat, with the stone's high parts standing out of
it, as much as asked (none when asked for none); the joints' bed lies under the slabs' tops; it stands on a ground when
given one; the same seed the same path; wrong options refused. The bamboo fence: posts at the line's ends and corners
at the height asked, a lattice's open canes and a close fence's packed ones, the ties on the front asked, its foot
measured from the ground, new canes when asked. The water lilies: only in the area, clear of what they are told to
keep clear of, floating at the level given, flowers as asked. The far hills: their layers one behind the other, paler
with distance, turned the way asked. The litter's maple leaves: lying on the slab path's tops or floating on its water,
matte; a swept heap where asked; the litter tool's old kinds exactly as before. The puddle: exactly as before unless
asked, a stronger mirror and a matte film on copies of its materials when asked. All of them answer --help.
    python3 tests/test_store_garden_ground.py
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

import _lines  # noqa: E402

# the litter and puddle tools' output before the garden set came (measured on the tools as they were, 5 November 2026):
# (how many numbers, their sum) for each thing, built in prove_same's scene (an 8 x 8 m ground, relief 0.08, seed 3, wet 0.6)
BEFORE = {
    'litter seed 0 leaves': (1749, -70.20109), 'litter seed 0 twigs': (192, 2.48197), 'litter straw': (51, -3.6094),
    'litter seed 3 leaves tone': (609, 294.18154), 'litter leaves turn': (597, -18.65083),
    'puddle flat water': (6723, -34.43328), 'puddle ground water': (6723, -53.48174), 'puddle ground film dry': (2080, 786.64626),
    'puddle level shallow': (2241, 376.21591), 'puddle no film water': (6723, 6.69799),
}


def points(obj):
    bpy.context.view_layer.update()                   # a new object's place is in its matrix only after an update
    co = numpy.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    matrix = numpy.array(obj.matrix_world)
    return co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def numbers(obj, name, width=1):
    attribute = obj.data.attributes.get(name)
    check(attribute is not None, '%s carries no %r' % (obj.name, name))
    data = numpy.zeros(len(attribute.data) * width)
    attribute.data.foreach_get('vector' if width == 3 else 'value', data)
    return data.reshape(-1, width) if width > 1 else data


def refused(call, error=ValueError):
    try:
        call()
    except error:
        return True
    return False


def inside(polygon, xy):
    """Which of the points (n, 2) lie inside the polygon (m, 2)."""
    x, y = xy[:, 0], xy[:, 1]
    result = numpy.zeros(len(xy), dtype=bool)
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        crosses = (yi > y) != (yj > y)
        result ^= crosses & (x < (xj - xi) * (y - yi) / ((yj - yi) if yj != yi else 1e-12) + xi)
        j = i
    return result


def fingerprint(values):
    values = numpy.asarray(values).ravel()
    return len(values), round(float(values.sum()), 5)


def same(found, expected, tolerance=2e-3):
    return found[0] == expected[0] and abs(found[1] - expected[1]) < tolerance


# ------------------------------------------------------------------------------------------------ the slab path

def slab_outlines(slabs):
    import lay_slab_path
    per = len(lay_slab_path.RINGS) * lay_slab_path.OUTLINE + 1 + 2 * lay_slab_path.OUTLINE   # top, middle, side, foot
    world = points(slabs)
    check(len(world) == per * slabs['slabs'], 'the slab path holds %d points, not %d for %d slabs' % (len(world), per * slabs['slabs'], slabs['slabs']))
    return [world[k * per:k * per + lay_slab_path.OUTLINE] for k in range(slabs['slabs'])], world, per


def test_slab_path():
    import lay_slab_path
    fresh_scene()
    line = [(-0.4, -1.6, 0.05), (0.0, 0.0, 0.05), (0.6, 1.6, 0.05), (0.5, 3.4, 0.08)]
    made = lay_slab_path.lay(line, width=1.25, water=0.5, seed=3)
    slabs, water, bed = made['slabs'], made['water'], made['bed']
    check(slabs['slabs'] >= 12 and water is not None and bed is not None, 'the path made %r' % {k: v and v.name for k, v in made.items()})
    outlines, world, per = slab_outlines(slabs)
    path = _lines.Path([Vector(p) for p in line]).smooth(0.05)
    along, across, _ = path.project(world[:, :2])
    check(numpy.abs(across).max() < 1.25 / 2 + 0.01, 'a slab reaches %.3f m from the line, past half the width' % numpy.abs(across).max())
    # no two slabs overlap: a fine grid of points from above, each inside one slab at most
    xs = numpy.linspace(world[:, 0].min(), world[:, 0].max(), 140)
    ys = numpy.linspace(world[:, 1].min(), world[:, 1].max(), 260)
    grid = numpy.stack(numpy.meshgrid(xs, ys), axis=-1).reshape(-1, 2)
    covered = numpy.zeros(len(grid), dtype=int)
    for outline in outlines:
        covered += inside(outline[:, :2], grid)
    check(covered.max() <= 1, '%d points from above lie inside two slabs at once' % (covered > 1).sum())
    check((covered == 0).sum() > 0.04 * (covered > 0).sum(), 'the joints between the slabs are missing')
    pieces = numbers(slabs, 'pp_piece')
    stone = numbers(slabs, 'stone_number')
    per_slab = [numpy.unique(pieces[stone == k]) for k in range(slabs['slabs'])]
    check(all(len(p) == 1 for p in per_slab), 'a slab shows more than one part of the photograph')
    check(len(numpy.unique(numpy.round([p[0] for p in per_slab], 6))) >= 0.9 * slabs['slabs'], 'the slabs share their parts of the photograph')
    # the water: flat, every point inside its own slab's outline, the stone standing out of it in places
    level_points = points(water)
    check(len(level_points) > 0, 'no water stands on the path')
    homes = numpy.zeros(len(level_points), dtype=int)
    for outline in outlines:
        homes += inside(outline[:, :2], level_points[:, :2])
    check(homes.min() == 1, '%d points of water lie outside every slab (or over a joint)' % (homes != 1).sum())
    depth = numbers(slabs, 'water')
    wet_slabs = [k for k in range(slabs['slabs']) if depth[k * per:(k + 1) * per].max() > 0]
    check(len(wet_slabs) == slabs['wet_slabs'] and len(wet_slabs) >= 3, 'the wet slabs: %d found, %d written' % (len(wet_slabs), slabs['wet_slabs']))
    import lay_slab_path as tool
    for k in wet_slabs:
        inner = depth[k * per + tool.WATER_RING * tool.OUTLINE:k * per + len(tool.RINGS) * tool.OUTLINE + 1]
        check((inner > 0).any() and (inner == 0).any(), 'slab %d is either all under water or holds none inside its edge' % k)
    shallow = numbers(water, 'shallow')
    check(shallow.min() < 0.3 and shallow.max() > 0.95, 'the water is not deep in the middle and clear at its edge (%.2f to %.2f)' % (shallow.min(), shallow.max()))
    # the joints' bed under the tops
    bed_z = points(bed)[:, 2]
    check(abs(bed_z.max() - (0.08 - lay_slab_path.BED_BELOW)) < 0.02 and bed_z.min() > 0.05 - lay_slab_path.BED_BELOW - 0.02,
          'the joints\' bed lies at %.3f to %.3f, not about %.2f under the slabs\' tops' % (bed_z.min(), bed_z.max(), lay_slab_path.BED_BELOW))
    water_material = made['water'].active_material
    clear = next(n for n in water_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    check(water_material.name.startswith(lay_slab_path.WATER) and 'clear on stone' in water_material.name
          and clear.inputs['Transmission Weight'].default_value == 1.0 and clear.inputs['IOR'].default_value > 1.6,
          'the water is not clear with the stronger mirror: %s' % water_material.name)
    top = lay_slab_path.top_at(made, *numpy.mean(outlines[2][:, :2], axis=0))
    check(top is not None and abs(top - 0.05) < 0.04, 'top_at found %r on a slab, not about 0.05' % top)
    check(lay_slab_path.top_at(made, 5.0, 5.0) is None, 'top_at found a slab off the path')
    print('PASS lay_slab_path: %d slabs within the path\'s width, none overlapping, each its own part of the photograph; '
          'water in %d of them, each puddle inside its own slab with stone standing out of it, deep in the middle and '
          'shallow at its edge, clear on the stone with the stronger mirror; the joints\' bed under the tops' % (slabs['slabs'], len(wet_slabs)))
    # water asked for: none, every slab that can
    dry = lay_slab_path.lay(line, water=0.0, seed=3, joints='none')
    check(dry['water'] is None and dry['bed'] is None and dry['slabs']['wet_slabs'] == 0, 'water=0 and joints=none still made water or a bed')
    soaked = lay_slab_path.lay(line, water=1.0, seed=3)
    check(soaked['slabs']['wet_slabs'] >= 0.7 * soaked['slabs']['slabs'], 'water=1 wetted only %d of %d slabs' % (soaked['slabs']['wet_slabs'], soaked['slabs']['slabs']))
    again = lay_slab_path.lay(line, width=1.25, water=0.5, seed=3)
    check(numpy.allclose(points(again['slabs']), points(slabs)), 'the same seed laid a different path')
    other = lay_slab_path.lay(line, width=1.25, water=0.5, seed=4)
    check(len(points(other['slabs'])) != len(world) or not numpy.allclose(points(other['slabs']), world), 'another seed laid the same path')
    # on a ground: the slabs stand `rise` above it and follow its slope
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(10.0, 0.0, 0.0))
    slope = bpy.context.object
    slope.scale = (4.0, 8.0, 1.0)
    slope.rotation_euler = (math.radians(4.0), 0.0, 0.0)
    bpy.context.view_layer.update()
    on = lay_slab_path.lay([(10.0, -2.5, 0.0), (10.0, 2.5, 0.0)], ground=slope, rise=0.04, water=0.0, seed=1)
    for k, outline in enumerate(slab_outlines(on['slabs'])[0][:6]):
        cx, cy = numpy.mean(outline[:, :2], axis=0)
        top = lay_slab_path.top_at(on, cx, cy)
        ground_z = cy * math.tan(math.radians(4.0))
        check(top is not None and abs(top - (ground_z + 0.04)) < 0.03, 'slab %d stands at %r on the ground, not about %.3f' % (k, top, ground_z + 0.04))
    check(refused(lambda: lay_slab_path.lay(line, joints='sand')) and refused(lambda: lay_slab_path.lay(line, water=2.0))
          and refused(lambda: lay_slab_path.lay(line, width=0.1)) and refused(lambda: lay_slab_path.lay([(0, 0, 0)])),
          'lay_slab_path took a wrong option')
    print('PASS lay_slab_path: water=0 lays none, water=1 wets most slabs; the same seed the same path, another seed '
          'another; on a sloping ground each slab stands 4 cm above it; wrong options refused')


# ------------------------------------------------------------------------------------------------ the bamboo fence

def test_bamboo_fence():
    import bamboo_fence
    fresh_scene()
    line = [(0.0, 0.0, 0.0), (3.6, 0.0, 0.0), (3.6, 1.8, 0.0)]
    made = bamboo_fence.lay(line, kind='lattice', height=1.0, seed=2)
    bamboo, cord = made['bamboo'], made['cord']
    check(bamboo['posts'] == 4 and bamboo['canes'] >= 14 and cord['ties'] >= 3 * bamboo['canes'],
          'the lattice made %d posts, %d canes, %d ties' % (bamboo['posts'], bamboo['canes'], cord['ties']))
    world = points(bamboo)
    check(abs(world[:, 2].max() - 1.0) < 0.06 and world[:, 2].min() < -0.25, 'the lattice stands %.3f to %.3f, not up to 1.0 m from 0.3 m in the ground' % (world[:, 2].min(), world[:, 2].max()))
    for corner in ((0.0, 0.0), (3.6, 0.0), (3.6, 1.8)):
        near = numpy.hypot(world[:, 0] - corner[0], world[:, 1] - corner[1]) < 0.045
        check(near.any() and world[near, 2].max() > 0.95, 'no post stands at the corner %r' % (corner,))
    # the ties on the front: right of the line, looking along it (the first run faces -Y)
    ties = points(cord)
    first_run = ties[ties[:, 0] < 3.4]
    check((first_run[:, 1] < 0).mean() > 0.95, 'the ties of the first run are not on its front (right, -Y)')
    left = bamboo_fence.lay([(0.0, 5.0, 0.0), (3.6, 5.0, 0.0)], front='left', seed=2)
    check((points(left['cord'])[:, 1] > 5.0).mean() > 0.95, "front='left' did not put the ties on the left")
    heights = numbers(bamboo, 'cane_height')
    check(heights.min() < -0.2 and heights.max() > 0.95, 'the canes\' heights above the ground run %.2f to %.2f' % (heights.min(), heights.max()))
    check(bamboo.active_material.name == bamboo_fence.OLD and cord.active_material.name == bamboo_fence.CORD, 'the fence wears %s and %s' % (bamboo.active_material.name, cord.active_material.name))
    close = bamboo_fence.lay([(0.0, 10.0, 0.0), (3.0, 10.0, 0.0)], kind='close', new=True, seed=3)
    check(close['bamboo']['canes'] >= 80 and abs(points(close['bamboo'])[:, 2].max() - 1.6) < 0.06,
          'the close fence holds %d canes up to %.2f m (packed canes, 1.6 m)' % (close['bamboo']['canes'], points(close['bamboo'])[:, 2].max()))
    check(close['bamboo'].active_material.name == bamboo_fence.NEW, 'new=True did not give new canes')
    again = bamboo_fence.lay(line, kind='lattice', height=1.0, seed=2)
    check(numpy.allclose(points(again['bamboo']), world), 'the same seed built a different fence')
    check(refused(lambda: bamboo_fence.lay(line, kind='brushwood')) and refused(lambda: bamboo_fence.lay(line, height=9.0))
          and refused(lambda: bamboo_fence.lay(line, front='up')), 'bamboo_fence took a wrong option')
    print('PASS bamboo_fence: a lattice of %d posts at the line\'s ends and corner, %d canes and %d ties on the front asked, '
          '1 m high from 0.3 m in the ground, its foot measured from the ground; a close fence of %d packed new canes; the '
          'same seed the same fence; wrong options refused' % (bamboo['posts'], bamboo['canes'], cord['ties'], close['bamboo']['canes']))


# ------------------------------------------------------------------------------------------------ the water lilies

def test_water_lilies():
    import water_lilies
    fresh_scene()
    area = [(0.0, 0.0), (3.0, 0.2), (3.2, 2.6), (0.2, 2.4)]
    keep = (1.5, 1.2, 0.35)
    made = water_lilies.lay(area, level=-0.05, amount=2.0, flowers=2.0, keep_clear=[keep], margin=0.1, seed=3)
    pads, flowers = made['pads'], made['flowers']
    check(pads['pads'] >= 15 and flowers is not None and flowers['flowers'] >= 1, 'the lilies made %r' % {k: v and v.get(k) for k, v in made.items()})
    world = points(pads)
    check(abs(world[:, 2].min() - (-0.05 + 0.004)) < 0.003, 'the pads float at %.4f, not 4 mm over the level -0.05' % world[:, 2].min())
    radial = numbers(pads, 'lily_r')
    middles = world[radial == 0.0]
    check(inside(numpy.array(area), middles[:, :2]).all(), 'a pad\'s middle lies outside the area')
    gap = numpy.hypot(world[:, 0] - keep[0], world[:, 1] - keep[1]).min()
    check(gap > keep[2] + 0.1 - 0.02, 'a pad comes within %.3f m of a thing to keep clear of (its radius %.2f and margin 0.1)' % (gap, keep[2]))
    # a water object as the area: the pads float at its height
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(10.0, 0.0, 0.3))
    pond = bpy.context.object
    on_pond = water_lilies.lay(pond, flowers=0.0, seed=1)
    pond_points = points(on_pond['pads'])
    check(on_pond['flowers'] is None and abs(pond_points[:, 2].min() - 0.304) < 0.003 and (numpy.abs(pond_points[:, 0] - 10.0) < 1.2).all(),
          'on a water object the pads lie at %.3f (not 0.304) or off it, or flowers came unasked' % pond_points[:, 2].min())
    again = water_lilies.lay(area, level=-0.05, amount=2.0, flowers=2.0, keep_clear=[keep], margin=0.1, seed=3)
    check(numpy.allclose(points(again['pads']), world), 'the same seed floated different lilies')
    check(refused(lambda: water_lilies.lay(area)) and refused(lambda: water_lilies.lay(area, level=0, colour='blue'))
          and refused(lambda: water_lilies.lay(area, level=0, amount=0)), 'water_lilies took a wrong option')
    print('PASS water_lilies: %d pads and %d flowers floating 4 mm over the level, only in the area, clear of what they '
          'were told; on a water object at its height; the same seed the same lilies; wrong options refused' % (pads['pads'], flowers['flowers']))


# ------------------------------------------------------------------------------------------------ the far hills

def test_far_hills():
    import far_hills
    fresh_scene()
    made = far_hills.lay(distance=(120, 450), layers=4, seed=2)['hills']
    check(len(made) == 4, '%d layers, not 4' % len(made))
    distances = [obj['distance'] for obj in made]
    check(abs(distances[0] - 120) < 1 and abs(distances[-1] - 450) < 1 and all(a < b for a, b in zip(distances, distances[1:])),
          'the ridges stand at %s' % distances)
    hazes = [numbers(obj, 'hill_haze').min() for obj in made]
    check(all(a < b for a, b in zip(hazes, hazes[1:])), 'the farther ridges are not hazier: %s' % hazes)
    first = points(made[0])
    check(first[:, 1].min() > 40 and abs(first[:, 0].mean()) < 20 and first[:, 2].max() < 120, 'the nearest ridge lies at y %.0f, x %.0f, up to %.0f m' % (first[:, 1].min(), first[:, 0].mean(), first[:, 2].max()))
    turned = far_hills.lay(facing=90, layers=1, seed=2)['hills'][0]
    check(points(turned)[:, 0].max() < -40, 'facing=90 did not put the hills towards -X')
    check(refused(lambda: far_hills.lay(distance=(400, 100))) and refused(lambda: far_hills.lay(layers=0))
          and refused(lambda: far_hills.lay(mist=3.0)), 'far_hills took a wrong option')
    print('PASS far_hills: four ridges from 120 to 450 m, each farther one hazier, turned the way asked; wrong options refused')


# ------------------------------------------------------------------------------------------------ litter: maple, heap, old kinds

def test_litter():
    import ground
    import lay_slab_path
    import litter
    fresh_scene()
    yard = ground.make(size=(8, 8), relief=0.08, seed=3)
    ground.wet(yard, wetness=0.6)
    old = litter.scatter(yard, seed=0)
    check(set(old) == {'leaves', 'twigs'}, 'the default kinds changed: %s' % sorted(old))
    found = {'litter seed 0 leaves': fingerprint(points(old['leaves'])), 'litter seed 0 twigs': fingerprint(points(old['twigs']))}
    three = litter.scatter(yard, seed=3)
    found['litter seed 3 leaves tone'] = fingerprint(numbers(three['leaves'], 'litter_tone'))
    every = litter.scatter(yard, area=(-2, -2, 2, 1), kinds=('leaves', 'twigs', 'straw'), amount=2.0, seed=5)
    found['litter straw'] = fingerprint(points(every['straw']))
    found['litter leaves turn'] = fingerprint(numbers(every['leaves'], 'litter_rotation', 3))
    for name, value in found.items():
        check(same(value, BEFORE[name]), 'the litter tool\'s %s changed: %s, before %s' % (name, value, BEFORE[name]))
    print('PASS litter: its old kinds lay exactly the leaves, twigs and straw they laid before the maple kind came')
    path = lay_slab_path.lay([(10.0, -1.0, 0.05), (10.0, 1.5, 0.05)], width=1.2, water=0.6, seed=5)
    maple = litter.scatter(path['slabs'], kinds=('maple',), amount=2.0, seed=4)['maple']
    where = points(maple)
    check(maple['pieces'] >= 20, 'only %d maple leaves fell on the path' % maple['pieces'])
    off = 0
    for x, y, z in where:
        top = lay_slab_path.top_at(path, x, y)
        if top is None or z < top - 0.003 or z > top + 0.03:
            off += 1
    check(off <= 0.03 * len(where), '%d of %d maple leaves lie off the slabs\' tops and water' % (off, len(where)))
    material = bpy.data.materials.get(litter.MAPLE_MATERIAL)
    principled = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    check(principled.inputs['Specular IOR Level'].default_value <= 0.2, 'the maple leaves are too shiny (they would mirror the blue sky)')
    heap = litter.heap((14.0, 0.0, 0.0), size=0.6, seed=2)
    hp = points(heap)
    core = hp[:int(round(heap['pieces'] / 1.12))]
    check(heap['pieces'] >= 200 and abs(hp[:, 2].max() - 0.15) < 0.04 and numpy.hypot((core[:, 0] - 14.0) / 0.3, core[:, 1] / 0.216).max() < 1.3,
          'the heap holds %d leaves up to %.3f m (0.15 asked), or spills past its oval' % (heap['pieces'], hp[:, 2].max()))
    strays = hp[len(core):]
    check((strays[:, 0] < 14.0 - 0.25).all(), 'the heap\'s strays are not on the side the broom came from')
    check(refused(lambda: litter.scatter(yard, kinds=('acorns',))) and refused(lambda: litter.heap((0, 0, 0), kind='straw')), 'litter took a wrong kind')
    print('PASS litter maple: %d matte maple leaves lying on the slab path\'s tops and water; a swept heap of %d leaves '
          '15 cm high with its strays behind it; wrong kinds refused' % (maple['pieces'], heap['pieces']))


# ------------------------------------------------------------------------------------------------ the puddle

def test_puddle():
    import ground
    import puddle
    fresh_scene()
    yard = ground.make(size=(8, 8), relief=0.08, seed=3)
    ground.wet(yard, wetness=0.6)
    found = {}
    water, film = puddle.make((2.0, 1.0, 0.0), size=(1.2, 0.8), turn=20, seed=2)
    found['puddle flat water'] = fingerprint(_local(water))
    check(water.active_material.name == puddle.WATER_MATERIAL and film.active_material.name == puddle.FILM_MATERIAL, 'the default puddle wears copies')
    water, film = puddle.make((-1.0, -1.0, 0.0), size=(2.5, 0.6), turn=-30, ground=yard, seed=4, raggedness=1.4)
    found['puddle ground water'] = fingerprint(_local(water))
    found['puddle ground film dry'] = fingerprint(numbers(film, 'dry'))
    water, film = puddle.make((0.5, 2.0, 0.0), size=(0.9, 0.9), ground=yard, level=0.02, shallow_band=0.04, seed=1)
    found['puddle level shallow'] = fingerprint(numbers(water, 'shallow'))
    water, film = puddle.make((0.0, 0.0, 0.1), film=False, seed=7)
    found['puddle no film water'] = fingerprint(_local(water))
    for name, value in found.items():
        check(same(value, BEFORE[name]), 'the puddle tool\'s %s changed: %s, before %s' % (name, value, BEFORE[name]))
    store_water = bpy.data.materials[puddle.WATER_MATERIAL]
    ior_before = next(n for n in store_water.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['IOR'].default_value
    strong, matte = puddle.make((3.0, -2.0, 0.0), ground=yard, seed=2, mirror=0.7, no_ring=True)
    mirror_bsdf = next(n for n in strong.active_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    check(strong.active_material.name == puddle.WATER_MATERIAL + ' • mirror 0.70' and mirror_bsdf.inputs['IOR'].default_value > ior_before + 0.5
          and mirror_bsdf.inputs['Specular IOR Level'].default_value > 0.8, 'mirror=0.7 did not give the water a stronger mirror')
    check(next(n for n in store_water.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['IOR'].default_value == ior_before,
          'the store\'s own puddle water was changed')
    film_bsdf = next(n for n in matte.active_material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    check(matte.active_material.name == puddle.FILM_MATERIAL + ' • no ring' and film_bsdf.inputs['Roughness'].default_value > 0.6
          and not film_bsdf.inputs['Roughness'].links, 'no_ring did not give the film a matte copy')
    shallow = numbers(strong, 'shallow')
    check((shallow > 0.99).mean() < 0.35, 'no_ring did not keep the clear rim narrow')
    print('PASS puddle: exactly as before unless asked; mirror and no_ring give copies of its materials (a stronger mirror, '
          'a matte film, a narrow clear rim) and leave the store\'s own as they were')


def _local(obj):
    co = numpy.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    return co


def test_help():
    for name in ('lay_slab_path', 'bamboo_fence', 'water_lilies', 'far_hills', 'litter', 'puddle'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS lay_slab_path, bamboo_fence, water_lilies, far_hills, litter and puddle answer --help')


def main():
    test_slab_path()
    test_bamboo_fence()
    test_water_lilies()
    test_far_hills()
    test_litter()
    test_puddle()
    test_help()
    print('PASS test_store_garden_ground')


if __name__ == '__main__':
    main()
