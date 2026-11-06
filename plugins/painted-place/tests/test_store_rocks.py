"""
What this file does: checks the rocks tool (the owner's word of 6 November 2026: rocks made by rules, laid with a
particle system, better textured):
  - its TOOL description is complete and --help answers;
  - every kind makes rocks by rules: each seed its own shape, the same seed the same shape; broken stone has more sharp
    faces than an old boulder, a flat stone is low with a level top, a river stone is smooth; each sunk by a share of
    its height (its origin is the soil line);
  - scatter() lays them with Blender's particle system (hair copies of a collection of shapes) over the ground given,
    inside the area given, as many as asked when there is room, sizes inside the range given and big ones fewer than
    small ones, several shapes in every scatter, each copy turned differently and tilted with the ground, none floating
    (the ground stands above each rock's lowest point all round it) and few overlapping; the same seed lays the same
    rocks, and the ground itself is left as it was;
  - the material shows each rock its own part of the photograph (each copy's own random number), at its real size,
    with wet dark feet read from the ground's wetness through each copy's UV, moss on top when asked, and the store's
    own material left as it was;
  - place() sets single rocks at the points given, on the ground, turned as asked, with real bumps (the height picture
    as displacement on a finer mesh);
  - what the garden's rocks pass made by hand, now in the tool: at_spots() lays one particle copy on each spot given,
    each its own shape at its own size, its top as high as asked, never floating on dry ground (lowered, and said so),
    standing as asked in a pond when the water's height is given, facing as asked, real bumps on the spots asked; a
    narrow area (a ring 0.5 m wide on a 30 m ground) gets every rock asked, and a keep(x, y) test lays the same rocks
    as the same area given as a function of many places; each rock its own amount of moss (moss_spread), the moss's
    colour (the brighter green by default), the normal picture's strength, the water line at the water's height;
    flat stones in lichen_rock by default; the private calls the garden's script makes still answer;
  - the three rock sets added to the shelf are there with their four pictures, and wrong values are refused.
    python3 tests/test_store_rocks.py
"""
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import BRIEF, TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import store  # noqa: E402
import ground as ground_tool  # noqa: E402
import rocks  # noqa: E402


def mesh_points(mesh):
    co = numpy.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)


def sharp_share(mesh):
    """The share of edges where the faces meet at more than 35 degrees (a broken stone's edges)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    edges = [e for e in bm.edges if len(e.link_faces) == 2]
    sharp = sum(1 for e in edges if e.calc_face_angle(0.0) > math.radians(35))
    bm.free()
    return sharp / max(len(edges), 1)


def copies(depsgraph, sheets):
    """The particle copies the sheets carry: (shape name, matrix, uv) for each."""
    names = {s.name for s in sheets}
    found = []
    for instance in depsgraph.object_instances:
        if instance.is_instance and instance.parent is not None and instance.parent.original.name in names:
            found.append((instance.object.original.name, instance.matrix_world.copy(), tuple(instance.uv),
                          instance.object.original.data))
    return found


def main():
    for key in ('name', 'what', 'call', 'options', 'materials', 'source', 'trap'):
        check(rocks.TOOL.get(key), 'TOOL has no %s' % key)
    for option in ('kind', 'count', 'sizes', 'area', 'buried', 'moss', 'seed', 'points', 'relief', 'spots', 'top', 'facing',
                   'moss_colour', 'moss_spread', 'normal_strength', 'water', 'water_band'):
        check(option in rocks.TOOL['options'], 'TOOL options do not say %s' % option)
    check('at_spots' in rocks.TOOL['call'] and 'rocks pass' in rocks.TOOL['source'],
          'TOOL does not show at_spots or say what came from the garden\'s rocks pass')
    answer = subprocess.run([sys.executable, os.path.join(TOOLS, 'rocks.py'), '--help'], capture_output=True, text=True, timeout=120)
    check(answer.returncode == 0 and 'Trap' in answer.stdout, 'rocks.py --help does not answer')
    print('PASS the TOOL description is complete and --help answers')

    # the shelf's new rock sets
    manifest = json.load(open(os.path.join(BRIEF, 'surfaces', 'manifest.json')))
    for set_id in ('lichen_rock', 'seaside_rock', 'rock_wall_02'):
        entry = manifest.get(set_id)
        check(entry and set(entry['maps']) == {'diff', 'rough', 'disp', 'normal'}, '%s is not on the shelf with four pictures' % set_id)
        for picture in entry['maps'].values():
            check(os.path.exists(os.path.join(BRIEF, 'surfaces', set_id, picture)), 'missing picture %s' % picture)
        check(entry['size_m'] == [2.0, 2.0] and 'CC0' in entry['licence'], '%s: size or licence wrong' % set_id)
    print('PASS the three rock sets are on the shelf with their four pictures, 2 x 2 m, CC0')

    # shapes by rules
    fresh_scene()
    made = {kind: [rocks.rock_mesh(kind, seed, 1.0, detail=40) for seed in range(4)] for kind in rocks.ORDER}
    for kind, meshes in made.items():
        boxes = []
        for mesh in meshes:
            points = mesh_points(mesh)
            span = points.max(axis=0) - points.min(axis=0)
            check(abs(max(span[0], span[1]) - 1.0) < 0.02, '%s: a 1 m rock is %.2f m across' % (kind, max(span[0], span[1])))
            sunk = -points[:, 2].min() / span[2]
            check(abs(sunk - mesh['rock_buried']) < 0.02 and 0.03 <= sunk <= 0.85,
                  '%s: %.2f of its height under the soil line, it says %.2f' % (kind, sunk, mesh['rock_buried']))
            boxes.append(tuple(numpy.round(span, 3)))
        check(len(set(boxes)) == len(boxes), '%s: two seeds made the same rock' % kind)
    again = mesh_points(rocks.rock_mesh('boulder', 2, 1.0, detail=40))
    check(numpy.allclose(again, mesh_points(made['boulder'][2])), 'the same seed did not make the same rock')
    sharp = {kind: numpy.mean([sharp_share(m) for m in meshes]) for kind, meshes in made.items()}
    check(sharp['angular'] > 2.0 * sharp['boulder'] and sharp['angular'] > 3.0 * sharp['river'],
          'broken stone is not sharper than boulders and river stones: %s' % {k: round(v, 4) for k, v in sharp.items()})
    heights = {kind: numpy.mean([m['rock_height'] for m in meshes]) for kind, meshes in made.items()}
    check(heights['flat'] < 0.36 and heights['flat'] < heights['river'] < heights['boulder'],
          'flat stones are not the lowest, then river stones, then boulders: %s' % {k: round(v, 2) for k, v in heights.items()})
    for mesh in made['flat']:
        points = mesh_points(mesh)
        top = points[points[:, 2] > points[:, 2].max() - 0.25 * (points[:, 2].max() - points[:, 2].min())]
        check(top[:, 2].std() < 0.03, 'a flat stone has no level top (its top quarter spreads %.3f m)' % top[:, 2].std())
    print('PASS shapes by rules: each seed its own, the same seed the same; broken stone sharpest (%.3f against boulders %.3f, '
          'river %.3f), flat stones low (%.2f) with a level top, each sunk by its share of height'
          % (sharp['angular'], sharp['boulder'], sharp['river'], heights['flat']))

    # scatter over a ground
    fresh_scene()
    yard = ground_tool.make(size=(8.0, 8.0), cell=0.1, relief=0.12, seed=5)
    ground_tool.wet(yard, 0.6)
    vertices_before = mesh_points(yard.data).copy()
    modifiers_before = len(yard.modifiers)
    area = (-3.0, -3.0, 3.0, 2.0)
    laid = rocks.scatter(yard, kind='boulder', count=60, sizes=(0.12, 0.8), area=area, gather=0.5, moss=0.6, seed=3)
    check(laid['placed'] == 60, 'only %d of 60 rocks laid in a 30 square metre area' % laid['placed'])
    check(numpy.allclose(mesh_points(yard.data), vertices_before) and len(yard.modifiers) == modifiers_before,
          'the ground was changed')
    numbers = [n for _, _, n in laid['bands']]
    check(len(numbers) >= 3 and all(numbers[k] >= numbers[k + 1] for k in range(len(numbers) - 1)) and numbers[0] > 2 * numbers[-1],
          'big rocks are not fewer than small ones: %s' % laid['bands'])
    for sheet in laid['objects']:
        check(len(sheet.particle_systems) == 1, '%s has no particle system' % sheet.name)
        settings = sheet.particle_systems[0].settings
        check(settings.type == 'HAIR' and settings.render_type == 'COLLECTION' and settings.use_collection_pick_random,
              '%s is not a particle system copying a collection of shapes' % sheet.name)
        check(not sheet.show_instancer_for_render, '%s draws its own tiny faces' % sheet.name)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    found = copies(depsgraph, laid['objects'])
    check(len(found) == 60, 'the particle systems made %d copies, not 60' % len(found))
    surface = rocks._Ground(yard)
    shapes_used, turns, floating, sizes, centres, ups = set(), [], 0, [], [], []
    for shape_name, matrix, uv, mesh in found:
        shapes_used.add(shape_name)
        position = matrix.translation
        check(area[0] - 0.01 <= position.x <= area[2] + 0.01 and area[1] - 0.01 <= position.y <= area[3] + 0.01,
              'a rock lies outside the area at (%.2f, %.2f)' % (position.x, position.y))
        under = surface.under(position.x, position.y)
        check(abs(under[0][2] - position.z) < 0.01, 'a rock is not at the soil line: %.3f m off' % (position.z - under[0][2]))
        up = (matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        check(up.angle(Vector(under[1])) < math.radians(25), 'a rock is not tilted with the ground (%.0f degrees off)'
              % math.degrees(up.angle(Vector(under[1]))))
        turns.append(round((matrix.to_3x3() @ Vector((1.0, 0.0, 0.0))).to_2d().angle_signed(Vector((1.0, 0.0))), 2))
        points = numpy.array([tuple(matrix @ Vector(p)) for p in mesh_points(mesh)])
        bottom = points[:, 2].min()
        across = points[:, :2].max(axis=0) - points[:, :2].min(axis=0)
        size = float(max(across))
        sizes.append(size)
        centres.append((position.x, position.y))
        for k in range(8):
            a = 2.0 * math.pi * k / 8.0
            ring = surface.under(position.x + 0.3 * size * math.cos(a), position.y + 0.3 * size * math.sin(a))
            if ring is not None and ring[0][2] < bottom:
                floating += 1
                break
        check(abs(uv[0] - float(under[2])) < 0.08, 'a copy does not carry the ground\'s wetness in its UV (%.2f against %.2f)'
              % (uv[0], under[2]))
    check(len(shapes_used) >= 8, 'only %d shapes in a scatter of 60' % len(shapes_used))
    check(len(set(turns)) >= 50, 'the copies are not each turned their own way')
    check(floating == 0, '%d rocks float (the ground dips below their lowest point)' % floating)
    check(min(sizes) >= 0.12 * 0.85 and max(sizes) <= 0.8 * 1.25, 'sizes run %.2f to %.2f m, asked 0.12 to 0.8' % (min(sizes), max(sizes)))
    overlapping = 0
    for i in range(len(centres)):
        for j in range(i + 1, len(centres)):
            gap = math.hypot(centres[i][0] - centres[j][0], centres[i][1] - centres[j][1])
            if gap < 0.3 * (sizes[i] + sizes[j]):
                overlapping += 1
    check(overlapping <= 1, '%d pairs of rocks overlap deeply' % overlapping)
    again = rocks.scatter(yard, kind='boulder', count=60, sizes=(0.12, 0.8), area=area, gather=0.5, moss=0.6, seed=3)
    check(again['spots'] == laid['spots'], 'the same seed did not lay the same rocks')
    other = rocks.scatter(yard, kind='boulder', count=60, sizes=(0.12, 0.8), area=area, seed=4)
    check(other['spots'] != laid['spots'], 'another seed laid the same rocks')
    crowded = rocks.scatter(yard, kind='flat', count=400, sizes=(0.5, 0.8), area=(0.0, 0.0, 1.0, 1.0), seed=1)
    check(crowded['placed'] < 400 and crowded['placed'] >= 1, 'a 1 m square took %d rocks half a metre across' % crowded['placed'])
    print('PASS scatter: 60 boulders by particle systems (%s) over the ground, which is unchanged, inside the area, at the '
          'soil line, tilted with the ground, %d shapes, each turned its own way, none floating, %d pairs overlapping deeply, '
          'sizes %.2f to %.2f m; the same seed the same rocks; a crowded square takes only what fits (%d of 400)'
          % (', '.join('%d of %.2f-%.2f m' % (n, a, b) for a, b, n in laid['bands']), len(shapes_used), overlapping,
             min(sizes), max(sizes), crowded['placed']))

    # the material
    material = laid['material']
    source = store.material('SURFACE • lichen_rock')
    check(material.name.startswith('rocks • lichen_rock') and material != source, 'the rocks do not wear their own copy of the rock set')
    pieces = material.node_tree.nodes.get('Pieces')
    check(pieces is not None and any(n.type == 'OBJECT_INFO' for n in pieces.node_tree.nodes),
          'each rock does not take its own part of the picture (no object random number in Pieces)')
    check(not any(n.type == 'OBJECT_INFO' for n in source.node_tree.nodes['Pieces'].node_tree.nodes), 'the store\'s own Pieces was changed')
    check(material.node_tree.nodes['Picture size'].node_tree == source.node_tree.nodes['Picture size'].node_tree,
          'the picture is no longer laid at its real size')
    for made_shapes, (low, high, _) in zip(laid['shapes'][::-1], laid['bands']):
        for obj in made_shapes.objects:
            span = mesh_points(obj.data).max(axis=0) - mesh_points(obj.data).min(axis=0)
            check(abs(max(span[0], span[1]) - math.sqrt(low * high)) < 0.01, 'a band\'s shapes are not made at its middle size')
    check(any(n.type == 'TEX_COORD' and n.from_instancer for n in material.node_tree.nodes), 'the feet do not read the copies\' UV')
    check(material.get('pp_moss') == 0.6, 'moss was asked for and is not on the material')
    greyer = [n for n in material.node_tree.nodes if n.type == 'HUE_SAT']
    check(greyer and abs(greyer[0].inputs['Saturation'].default_value - (1.0 - rocks.KINDS['boulder']['grey'])) < 1e-6,
          'the boulders\' photograph is not made greyer by default')
    plain = rocks.material('boulder', grey=0.0, tint=(1.0, 1.0, 1.0))
    check(not any(n.type == 'HUE_SAT' for n in plain.node_tree.nodes) and plain != material, 'grey=0 with a plain tint still changes the colour')
    check(source.node_tree.nodes['Weather'].inputs['Wet'].default_value != material.node_tree.nodes['Weather'].inputs['Wet'].default_value
          or source.node_tree.nodes['Weather'].inputs['Wet'].default_value == 0.3, 'the rain did not wet the copy')
    print('PASS the material: a copy of SURFACE • lichen_rock, each rock its own part of the picture, at its real size '
          '(shapes made at each band\'s middle size), greyer than the photograph by default, wet feet by the ground\'s wetness, '
          'moss on top; the store\'s own left as it was')

    # place
    points = [(1.0, 2.5), (-2.0, 2.6), (2.6, -2.6)]
    big = rocks.place(points, kind='boulder', size=[1.4, 0.9, 0.6], ground=yard, turn=[0, 90, 45], moss=0.5, seed=5)
    check(len(big) == 3, 'place made %d rocks for 3 points' % len(big))
    for obj, (x, y), size in zip(big, points, (1.4, 0.9, 0.6)):
        under = surface.under(x, y)
        check((obj.matrix_world.translation - Vector(under[0])).length < 0.01, '%s is not on the ground under its point' % obj.name)
        span = mesh_points(obj.data).max(axis=0) - mesh_points(obj.data).min(axis=0)
        check(abs(max(span[0], span[1]) - size) < 0.02, '%s is %.2f m across, asked %.2f' % (obj.name, max(span[0], span[1]), size))
        subdivision = [m for m in obj.modifiers if m.type == 'SUBSURF']
        check(subdivision and subdivision[0].render_levels == 2 and subdivision[0].subdivision_type == 'SIMPLE',
              '%s has no finer mesh for its bumps' % obj.name)
        rock_material = obj.data.materials[0]
        output = next(n for n in rock_material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        check(output.inputs['Displacement'].is_linked and getattr(rock_material, 'displacement_method', 'BOTH') == 'BOTH',
              '%s has no real bumps' % obj.name)
    forward = (big[1].matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).to_2d()
    check(abs(math.degrees(forward.angle_signed(Vector((1.0, 0.0))))) > 60, 'the turn asked was not given')
    flat = rocks.place([(0.0, 0.0, 0.3)], kind='flat', size=0.6, relief=0.0)
    check(abs(flat[0].matrix_world.translation.z - 0.3) < 1e-6 and not flat[0].modifiers, 'a rock without a ground is not at the z given')
    print('PASS place: three boulders on the ground at their points, at the sizes and turns asked, with real bumps '
          '(the height picture as displacement on a mesh made twice finer); a flat stone at the z given without a ground')

    # at_spots: rocks with a set place as particle copies (from the garden's rocks pass, its rocks_at)
    spots = [(-2.5, -2.5), (-1.0, -2.6), (0.5, -2.4), (2.0, -2.5)]
    across = [0.9, 0.5, 0.35, 0.6]
    soil = [float(surface.under(x, y)[0][2]) for x, y in spots]
    tops = [None, soil[1] + 0.12, soil[2] + 0.8, None]                # the third would float 0.8 m up: lowered
    set_rocks = rocks.at_spots(spots, kind='boulder', size=across, top=tops, ground=yard, relief=[0.0, 0.0, 0.0, 0.03],
                               moss=0.8, tilt=0.0, seed=11)
    check(set_rocks['placed'] == 4 and len(set_rocks['objects']) == 4 and len(set_rocks['materials']) == 2,
          'at_spots laid %d rocks with %d materials, not 4 with 2 (one with bumps)' % (set_rocks['placed'], len(set_rocks['materials'])))
    check(set_rocks['lowered'] == [2], 'at_spots lowered %s, not the one asked to float (2)' % set_rocks['lowered'])
    depsgraph = bpy.context.evaluated_depsgraph_get()

    def copy_of(sheet):
        for instance in depsgraph.object_instances:
            if instance.is_instance and instance.parent is not None and instance.parent.original.name == sheet.name:
                return instance.object.original, instance.matrix_world.copy()
        return None, None
    shapes_seen = set()
    for k, sheet in enumerate(set_rocks['objects']):
        shape, matrix = copy_of(sheet)
        check(shape is not None, '%s carries no particle copy' % sheet.name)
        check(sheet.particle_systems[0].settings.count == 1 and not sheet.show_instancer_for_render,
              '%s is not a hidden sheet with one particle' % sheet.name)
        shapes_seen.add(shape.name)
        position = matrix.translation
        check(abs(position.x - spots[k][0]) < 0.01 and abs(position.y - spots[k][1]) < 0.01, 'at_spots rock %d is not on its spot' % k)
        points = numpy.array([tuple(matrix @ Vector(p)) for p in mesh_points(shape.data)])
        span = mesh_points(shape.data).max(axis=0) - mesh_points(shape.data).min(axis=0)
        check(abs(max(span[0], span[1]) - across[k]) < 0.02, 'at_spots rock %d is %.2f m across, asked %.2f' % (k, max(span[0], span[1]), across[k]))
        reached = set_rocks['spots'][k][4]
        check(abs(points[:, 2].max() - reached) < 0.04, 'at_spots rock %d tops at %.3f, it says %.3f' % (k, points[:, 2].max(), reached))
        if tops[k] is None:
            check(abs(position.z - soil[k]) < 0.01, 'at_spots rock %d is not at the soil line' % k)
        elif k == 1:
            check(abs(reached - tops[k]) < 1e-6, 'at_spots rock 1 does not reach the top asked')
        check(points[:, 2].min() <= soil[k] + 0.01, 'at_spots rock %d floats (its lowest point %.3f above the soil)' % (k, points[:, 2].min() - soil[k]))
        bumps = [m for m in shape.modifiers if m.type == 'SUBSURF']
        rock_material = shape.data.materials[0]
        output = next(n for n in rock_material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
        if k == 3:
            check(bumps and bumps[0].render_levels == 2 and output.inputs['Displacement'].is_linked, 'the rock asked for bumps has none')
        else:
            check(not bumps and not output.inputs['Displacement'].is_linked, 'a rock not asked for bumps has them')
    check(len(shapes_seen) == 4, 'at_spots rocks share shapes (%d shapes for 4)' % len(shapes_seen))
    # in a pond: with the water's height, a rock whose foot is under the water stands as asked; facing as asked
    x, y = 2.5, 2.5
    low = float(surface.under(x, y)[0][2])
    in_pond = rocks.at_spots([(x, y)], size=0.5, top=low + 0.5, ground=yard, water=low + 0.3, tilt=0.0,
                             facing=(0.3, 0.0, 1.0), seed=12)
    check(in_pond['lowered'] == [] and abs(in_pond['spots'][0][4] - (low + 0.5)) < 1e-6,
          'a rock with its foot under the water given was pulled down')
    dry = rocks.at_spots([(x, y)], size=0.5, top=low + 0.5, ground=yard, tilt=0.0, seed=12)
    check(dry['lowered'] == [0] and dry['spots'][0][4] < low + 0.5, 'without the water a rock asked to float was not lowered')
    depsgraph = bpy.context.evaluated_depsgraph_get()
    _, matrix = copy_of(in_pond['objects'][0])
    up = (matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    check(up.angle(Vector((0.3, 0.0, 1.0)).normalized()) < math.radians(3), 'the facing asked was not given')
    check('Water line' in in_pond['materials'][0].node_tree.nodes, 'the water asked for drew no water line')
    print('PASS at_spots: 4 rocks on their spots, each its own shape at its own size (0.35 to 0.9 m), tops as asked, '
          'the one asked to float lowered into the soil and said so, bumps only where asked; in a pond (water given) '
          'it stands as asked, without the water it is lowered; facing as asked')

    # a narrow area: a ring 0.5 m wide on a 30 m ground (the garden's pond bank, cut out by hand before)
    wide = ground_tool.make(size=(30.0, 30.0), cell=0.15, relief=0.1, seed=5)

    def ring(xy):
        r = numpy.hypot(xy[:, 0] - 2.0, xy[:, 1])
        return ((r > 5.0) & (r < 5.5)).astype(float)

    def on_ring(x, y):
        return 5.0 < math.hypot(x - 2.0, y) < 5.5
    bank = rocks.scatter(wide, count=120, sizes=(0.16, 1.1), fall=1.3, spacing=0.75, gather=0.6, area=ring, seed=57)
    check(bank['placed'] == 120, 'a narrow bank took only %d of 120 rocks (%s)' % (bank['placed'], bank['bands']))
    check(all(4.99 <= math.hypot(sx - 2.0, sy) <= 5.51 for sx, sy, _, _, _ in bank['spots']), 'a bank rock lies outside the ring')
    kept = rocks.scatter(wide, count=120, sizes=(0.16, 1.1), fall=1.3, spacing=0.75, gather=0.6, area=on_ring, seed=57)
    check(kept['spots'] == bank['spots'], 'a keep(x, y) test did not lay the same rocks as the same area given for many places')
    print('PASS a narrow area: a ring 0.5 m wide on a 30 m ground takes all 120 rocks asked (%s), and a keep(x, y) test '
          'lays the same rocks' % ', '.join('%d' % n for _, _, n in bank['bands']))

    # the material's new options
    plain = rocks.material('boulder', moss=0.8)
    nodes = plain.node_tree.nodes
    check(nodes.get('Moss amount') is not None and not nodes['Moss amount'].inputs[1].is_linked
          and abs(nodes['Moss amount'].inputs[1].default_value - 0.8) < 1e-6 and nodes.get('Moss spread') is None,
          'without moss_spread the moss is not one amount for all')

    def moss_greens(made):
        return [tuple(round(c, 4) for c in n.inputs[6].default_value[:3]) for n in made.node_tree.nodes
                if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[6].is_linked]
    check(tuple(round(c, 4) for c in rocks.MOSS_COLOUR) in moss_greens(plain) and rocks.MOSS_COLOUR == (0.07, 0.105, 0.02),
          'the moss is not the brighter green by default')
    dark = rocks.material('boulder', moss=0.8, moss_colour=rocks.MOSS_DARK)
    check(tuple(round(c, 4) for c in rocks.MOSS_DARK) in moss_greens(dark) and dark != plain, 'moss_colour was not used')
    spread = rocks.material('boulder', moss=0.8, moss_spread=(0.35, 1.4))
    nodes = spread.node_tree.nodes
    spread_node, amount = nodes.get('Moss spread'), nodes.get('Moss amount')
    check(spread_node is not None and amount is not None and spread != plain, 'moss_spread made no spread')
    check(abs(spread_node.inputs['To Min'].default_value - 0.35) < 1e-6 and abs(spread_node.inputs['To Max'].default_value - 1.4) < 1e-6,
          'the spread is not 0.35 to 1.4')
    times = amount.inputs[1].links[0].from_node if amount.inputs[1].is_linked else None
    check(times is not None and times.inputs[0].links[0].from_node == spread_node and abs(times.inputs[1].default_value - 0.8) < 1e-6,
          'the moss amount is not the moss times the spread')
    source_of = spread_node.inputs['Value'].links[0].from_node
    while source_of.type != 'OBJECT_INFO' and source_of.inputs[0].is_linked:
        source_of = source_of.inputs[0].links[0].from_node
    check(source_of.type == 'OBJECT_INFO', 'the spread does not go by each rock\'s own random number')
    strong = rocks.material('boulder', normal_strength=1.7)
    source = store.material('SURFACE • lichen_rock')
    check(abs(strong.node_tree.nodes['Normal picture'].inputs['Strength'].default_value - 1.7) < 1e-6
          and abs(rocks.material('boulder').node_tree.nodes['Normal picture'].inputs['Strength'].default_value
                  - source.node_tree.nodes['Normal picture'].inputs['Strength'].default_value) < 1e-6,
          'normal_strength was not used, or changed the strength when not asked')
    wet = rocks.material('boulder', water=0.25, water_band=0.1)
    line = wet.node_tree.nodes.get('Water line')
    check(line is not None and abs(line.inputs['From Min'].default_value - 0.35) < 1e-6
          and abs(line.inputs['From Max'].default_value - 0.24) < 1e-6, 'the water line is not from 0.1 m above the water down to it')
    height_from = line.inputs['Value'].links[0].from_node
    check(height_from.bl_idname == 'ShaderNodeSeparateXYZ' and height_from.inputs[0].links[0].from_node.bl_idname == 'ShaderNodeNewGeometry',
          'the water line does not go by where each point is')
    principled = next(n for n in wet.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    darker = principled.inputs['Base Color'].links[0].from_node
    check(darker.type == 'MIX' and darker.inputs[0].is_linked and darker.inputs[0].links[0].from_node == line,
          'the water line does not darken the stone')
    check(rocks.material('boulder').node_tree.nodes.get('Water line') is None, 'a water line without water asked')
    check(rocks.material('flat').name.startswith('rocks • lichen_rock • flat') and rocks.material('river').name.startswith('rocks • seaside_rock • river'),
          'flat stones are not in lichen_rock by default (river stones in seaside_rock)')
    # the private calls the garden's script makes still answer as before
    old = rocks.material('flat', 'lichen_rock', 0.9, 0.7, 0.35, 0.03, None, None)
    old_shapes = rocks._shapes('flat', [201000], 0.5, None, old, 44)
    old_sheet = rocks._sheet('old call', [((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0)], bpy.context.scene.collection)
    check(old.name.startswith('rocks • lichen_rock • flat • moss 0.90 • bumps 0.030 m') and len(old_shapes.objects) == 1
          and len(old_sheet.data.polygons) == 1, 'the private calls material(), _shapes() and _sheet() no longer answer as before')
    print('PASS the material: one moss amount for all unless moss_spread (0.35 to 1.4 by each rock\'s own random number), '
          'the brighter moss green by default and the dark one when asked, normal_strength, a water line from 0.1 m above '
          'the water given, flat stones in lichen_rock; the garden script\'s private calls still answer')

    # wrong values refused
    for call in (lambda: rocks.scatter(yard, kind='pebble'), lambda: rocks.scatter(yard, sizes=(0.5, 0.1)),
                 lambda: rocks.material('boulder', moss=0.5, moss_spread=(1.4, 0.35)),
                 lambda: rocks.material('boulder', moss_colour=(1.0, 1.0)), lambda: rocks.material('boulder', normal_strength=3.0),
                 lambda: rocks.material('boulder', water_band=1.0), lambda: rocks.at_spots([(0, 0)], size=[1, 2]),
                 lambda: rocks.at_spots([(0, 0)], facing=[(0, 0, 1), (0, 0, 1)]), lambda: rocks.at_spots([]),
                 lambda: rocks.at_spots([(0, 0)], relief=0.9), lambda: rocks.at_spots([(40.0, 40.0)], ground=yard),
                 lambda: rocks.scatter(yard, count=0), lambda: rocks.scatter(None),
                 lambda: rocks.place([(0, 0)], size=[1, 2]), lambda: rocks.place([(0, 0)], buried=0.95),
                 lambda: rocks.scatter(yard, area='everywhere'), lambda: rocks.material('boulder', surface='no_such_rock'),
                 lambda: rocks.material('boulder', grey=1.5), lambda: rocks.material('boulder', tint=(1.0, 1.0))):
        try:
            call()
        except ValueError:
            continue
        check(False, 'a wrong value was not refused')
    print('PASS wrong kinds, sizes, counts, grounds, areas and surfaces are refused')


if __name__ == '__main__':
    main()
