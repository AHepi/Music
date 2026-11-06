"""
What this file does: checks the moss tool's real moss (moss.py: cushions with thickness, the pile of tufts laid by the
particle system, grow() on a stone object, feet() at rocks' feet, lichen crusts) and the rocks tool's moss with it
(rocks.py: moss_style 'cushions' by default, 'paint' as before), and that every call that worked before still works:
moss.add as it was, the rocks tool's material(), _shapes() and _sheet() as the garden's script calls them.
Plain PASS lines; stops with exit code 1 at the first failure.
    python3 tests/test_store_moss.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import moss  # noqa: E402
import rocks  # noqa: E402
import store  # noqa: E402


def ball(name='stone ball', radius=0.5, location=(0.0, 0.0, 0.0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=radius)
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def attribute(mesh, name):
    layer = mesh.attributes.get(name)
    if layer is None:
        return None
    values = numpy.zeros(len(layer.data))
    layer.data.foreach_get('value', values)
    return values


def main():
    fresh_scene()
    # ------------------------------------------------------------------ add() as it was, and with lichen
    plain = moss.add('SURFACE • old_stone_wall_02', amount=0.85)
    check(plain.name == 'SURFACE • old_stone_wall_02 • moss' and abs(plain['pp_moss'] - 0.85) < 1e-6, 'add() no longer makes its copy as before')
    check(not [n for n in plain.node_tree.nodes if n.type == 'TEX_VORONOI'], 'add() without lichen lays lichen')
    check(bpy.data.materials['SURFACE • old_stone_wall_02'].node_tree.nodes.get('Weather') is not None, 'add() changed the store material')
    crust = moss.add('SURFACE • old_stone_wall_02', 0.6, 0.0, (0.45, 0.85), 3.0, (0.035, 0.05, 0.014), 0.7)
    check([n for n in crust.node_tree.nodes if n.type == 'TEX_VORONOI'] and abs(crust['pp_lichen'] - 0.7) < 1e-6, 'add(lichen=) lays no lichen crusts')
    for bad in ({'amount': 2.0}, {'foot': -1}, {'scale': 0.0}, {'facing': (0.9, 0.1)}):
        try:
            moss.add('SURFACE • old_stone_wall_02', **bad)
            check(False, 'add(%r) was not refused' % bad)
        except ValueError:
            pass
    print('PASS add(): the mossy copy as before, lichen crusts only when asked, bad options refused')

    # ------------------------------------------------------------------ the cushions' and the pile's materials
    cushions = moss.cushion_material()
    check(cushions is moss.cushion_material(), 'the cushions material is not shared')
    pictures = [n.image.name for n in cushions.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    check(any('forest_leaves_02' in p for p in pictures), 'the cushions do not wear the photographed moss: %s' % pictures)
    check(store.material('SURFACE • forest_leaves_02').get('store_size_m'), 'SURFACE • forest_leaves_02 is not in the store')
    names = {n.attribute_name for n in cushions.node_tree.nodes if n.type == 'ATTRIBUTE'}
    check({'moss_depth', 'moss_age'} <= names, 'the cushions read %s' % sorted(names))
    pile_mat = moss.pile_material()
    names = {n.attribute_name for n in pile_mat.node_tree.nodes if n.type == 'ATTRIBUTE'}
    check({'tip', 'stalk'} <= names, 'the pile reads %s' % sorted(names))
    shapes = moss.tufts(pile_mat)
    check(len(shapes.objects) == 6 and all(len(o.data.polygons) > 20 for o in shapes.objects), 'the tufts are not six shapes')
    sizes = [max(o.dimensions) for o in shapes.objects]
    check(all(0.004 < s < 0.03 for s in sizes), 'the tufts are not about 0.5 to 2 cm: %s' % sizes)
    print('PASS materials: cushions in photographed moss (forest_leaves_02) under the greens, a pile of six tuft shapes 0.5 to 2 cm')

    # ------------------------------------------------------------------ the moss's look at dusk: olive, little sheen, lumps
    principled = next(n for n in cushions.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    ramp = next(n for n in cushions.node_tree.nodes if n.type == 'VALTORGB' and len(n.color_ramp.elements) == 3)
    darks = [n for n in cushions.node_tree.nodes if n.type == 'MAP_RANGE' and abs(n.inputs['From Max'].default_value - 0.32) < 1e-4]
    check(abs(principled.inputs['Sheen Weight'].default_value - 0.3) < 1e-4 and abs(cushions.node_tree.nodes['Normal picture'].inputs['Strength'].default_value - 0.7) < 1e-4
          and darks and abs(darks[0].inputs['To Min'].default_value - 0.24) < 1e-4 and cushions['moss_key'].endswith('olive'),
          'the cushions are not olive with little sheen and strong lumps by default: %s' % cushions['moss_key'])
    first = moss.cushion_material(sheen=0.8, lumps=0.2, greens='bright')
    first_ramp = next(n for n in first.node_tree.nodes if n.type == 'VALTORGB' and len(n.color_ramp.elements) == 3)
    first_darks = [n for n in first.node_tree.nodes if n.type == 'MAP_RANGE' and abs(n.inputs['From Max'].default_value - 0.32) < 1e-4]
    check(first is not cushions and abs(next(n for n in first.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Sheen Weight'].default_value - 0.8) < 1e-4
          and abs(first.node_tree.nodes['Normal picture'].inputs['Strength'].default_value - 0.2) < 1e-4
          and abs(first_darks[0].inputs['To Min'].default_value - 0.38) < 1e-4,
          'sheen=0.8, lumps=0.2, greens=bright do not give the cushions as they first were')
    young, first_young = ramp.color_ramp.elements[0].color, first_ramp.color_ramp.elements[0].color
    check(sum(young[:3]) < 0.8 * sum(first_young[:3]) and young[1] / young[0] < first_young[1] / first_young[0] + 0.05,
          'the olive young moss is not darker than the bright: %s against %s' % (tuple(young), tuple(first_young)))
    check(abs(next(n for n in moss.pile_material().node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Sheen Weight'].default_value - 0.21) < 1e-4
          and abs(next(n for n in moss.pile_material(sheen=0.5).node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Sheen Weight'].default_value - 0.5) < 1e-4,
          'the tufts\' sheen is not 0.21 by default, or sheen= is not followed')
    for bad in ({'sheen': 1.5}, {'lumps': -1}, {'greens': 'lime'}):
        try:
            moss.cushion_material(**bad)
            check(False, 'cushion_material(%r) was not refused' % bad)
        except ValueError:
            pass
    print('PASS the look at dusk: olive greens, sheen 0.3 (tufts 0.21), lumps 0.7 by default; sheen=0.8, lumps=0.2, greens=bright the first look; bad values refused')

    # ------------------------------------------------------------------ on_mesh: cushions in a mesh
    stone = ball('stone ball', 0.5)
    before_faces = len(stone.data.polygons)
    area = moss.on_mesh(stone.data, amount=1.0, thickness=0.03, seed=3)
    mesh = stone.data
    check(area > 0.05 and len(mesh.materials) == 2 and mesh.materials[0] is None and mesh.materials[1].name.startswith('moss • cushions'),
          'on_mesh made no cushions in a slot of their own (area %.3f)' % area)
    index = numpy.zeros(len(mesh.polygons), dtype=numpy.int64)
    mesh.polygons.foreach_get('material_index', index)
    shell = index == len(mesh.materials) - 1
    check(shell.sum() == mesh['moss_faces'] and len(mesh.polygons) == before_faces + mesh['moss_faces'], 'the cushions are not faces of their own')
    for name in ('moss_depth', 'moss_age', 'moss_film', 'moss_hollow', 'moss_cushioned'):
        check(attribute(mesh, name) is not None, 'the mesh has no %s' % name)
    co = numpy.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    depth = attribute(mesh, 'moss_depth')
    cushion_points = numpy.unique(numpy.concatenate([list(p.vertices) for p, s in zip(mesh.polygons, shell) if s]))
    lift = numpy.linalg.norm(co[cushion_points], axis=1) - 0.5
    check(lift.max() > 0.015 and lift.max() < 0.06 and numpy.percentile(lift, 5) > -0.004,
          'the cushions do not stand off the stone as thick as asked: %.4f to %.4f m' % (lift.min(), lift.max()))
    thick = depth[cushion_points] > 0.6
    check(thick.any() and (~thick).any() and lift[thick].mean() > 2.0 * lift[~thick].mean(),
          'the cushions do not thin at their edges (%.4f middle, %.4f edge)' % (lift[thick].mean(), lift[~thick].mean()))
    up = co[cushion_points][:, 2].mean()
    check(up > 0.1, 'the cushions are not on the top (their mean height %.3f m)' % up)
    over = (co[cushion_points][:, 2] < 0.15).sum()             # below where the faces look up enough (facing 0.3)
    check(over > 0, 'the cushions do not creep over the rim down the sides')
    print('PASS on_mesh: %.2f m2 of cushions on a 1 m ball, up to %.0f mm thick, thinning at their edges, over the rim' % (area, lift.max() * 1000))
    less = ball('less moss', 0.5)
    check(moss.on_mesh(less.data, amount=0.5, seed=3) < area * 0.8, 'amount 0.5 covers as much as amount 1')

    # ------------------------------------------------------------------ pile: the tufts by the particle system
    system = moss.pile(stone, None, 1.0)
    check(system is not None and system.vertex_group_density == 'moss pile', 'the pile does not follow its vertex group')
    settings = system.settings
    check(settings.type == 'HAIR' and settings.render_type == 'COLLECTION' and len(settings.instance_collection.objects) == 6,
          'the pile is not hair copying the six tufts')
    check(abs(settings.count - int(area * moss.PILE_DENSITY)) <= 1, 'the pile has %d tufts for %.2f m2' % (settings.count, area))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    laid = len(stone.evaluated_get(depsgraph).particle_systems[0].particles)
    check(laid == settings.count, 'the pile laid %d of %d tufts' % (laid, settings.count))
    print('PASS pile: %d tufts laid by a hair particle system (copies of six shapes) on the cushions only' % laid)

    # ------------------------------------------------------------------ grow: real moss on an object you give
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.4, depth=0.5, location=(3.0, 0.0, 0.25))
    basin = bpy.context.active_object
    basin.name = 'test basin'
    basin.scale = (1.2, 1.2, 1.2)
    verts_before = len(basin.data.vertices)
    grown = moss.grow(basin, amount=1.0, seed=2)
    check(grown is not None and grown.name == 'moss on test basin' and grown.parent == basin, 'grow made no moss object on the basin')
    check(len(basin.data.vertices) == verts_before and not basin.modifiers, 'grow changed the object it was given')
    bpy.context.view_layer.update()
    world = [grown.matrix_world @ v.co for v in grown.data.vertices]
    top = max(v.z for v in world)
    check(grown.data['moss_area'] > 0.05 and top > basin.matrix_world.translation.z + 0.29, 'the basin\'s top carries no moss (%.3f)' % top)
    check(grown.particle_systems and grown.particle_systems[0].settings.count > 100, 'the basin\'s moss has no pile')
    basin.location.x += 1.0
    bpy.context.view_layer.update()
    check(abs((grown.matrix_world.translation - basin.matrix_world.translation).length) < 1e-5, 'the moss does not move with the basin')
    print('PASS grow: %.2f m2 of moss on a scaled basin, parented to it, the basin untouched' % grown.data['moss_area'])
    check(grown.data.get('moss_closed') is None, 'grow closed a basin that was closed already')

    # ------------------------------------------------------------------ grow on an open shape: closed for the growing
    import math
    profile = [(0.36, -0.08), (0.43, 0.08), (0.455, 0.28), (0.42, 0.45), (0.36, 0.53), (0.28, 0.55), (0.245, 0.52), (0.21, 0.43),
               (0.12, 0.385), (0.001, 0.38)]                                # the garden's carved basin, open underneath
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(math.tau * i / 32), r * math.sin(math.tau * i / 32), z)) for i in range(32)] for r, z in profile]
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(32):
            bm.faces.new((a[i], a[(i + 1) % 32], b[(i + 1) % 32], b[i]))
    open_mesh = bpy.data.meshes.new('open basin')
    bm.to_mesh(open_mesh)
    bm.free()
    open_basin = bpy.data.objects.new('open basin', open_mesh)
    bpy.context.scene.collection.objects.link(open_basin)
    open_basin.location = (-3.0, 0.0, 0.08)
    faces_before = len(open_mesh.polygons)
    on_open = moss.grow(open_basin, amount=0.9, seed=4, sheen=0.5, lumps=1.0, greens='bright')
    check(on_open is not None and on_open.data['moss_area'] > 0.5 and str(on_open.data.get('moss_closed', '')).startswith('holes filled'),
          'grow on a basin open underneath grew %s' % (on_open and on_open.data['moss_area']))
    check(len(open_mesh.polygons) == faces_before, 'grow closed the open basin itself')
    look = on_open.data.materials[0]
    check(abs(next(n for n in look.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Sheen Weight'].default_value - 0.5) < 1e-4
          and abs(look.node_tree.nodes['Normal picture'].inputs['Strength'].default_value - 1.0) < 1e-4 and look['moss_key'].endswith('bright'),
          'grow(sheen=, lumps=, greens=) did not reach the cushions')
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=4, size=1.0, location=(-6.0, 0.0, 0.8))
    sheet = bpy.context.active_object
    sheet.scale = (1.5, 0.4, 1.0)
    sheet['pp_ground'] = 0.0
    on_sheet = moss.grow(sheet, amount=1.0, foot=0.0, seed=2)
    check(on_sheet is not None and on_sheet.data['moss_area'] > 0.3 and on_sheet.data.get('moss_closed') == 'thickened',
          'grow on a thin open sheet grew %s' % (on_sheet and on_sheet.data['moss_area']))
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, 0.0, 0.15))      # a trough made as a thin shell, open on top
    trough = bpy.context.active_object
    trough.scale = (0.6, 0.4, 0.3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bm = bmesh.new()
    bm.from_mesh(trough.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY')
    bm.to_mesh(trough.data)
    bm.free()
    trough['pp_ground'] = 0.0
    on_trough = moss.grow(trough, amount=1.0, seed=3)
    check(on_trough is not None and on_trough.data.get('moss_closed') == 'thickened', 'a trough open on top was not thickened: %s'
          % (on_trough and on_trough.data.get('moss_closed')))
    bpy.context.view_layer.update()
    lid = [v for v in on_trough.data.vertices if abs((on_trough.matrix_world @ v.co).x + 9.0) < 0.2
           and abs((on_trough.matrix_world @ v.co).y) < 0.1 and (on_trough.matrix_world @ v.co).z > 0.25]
    check(not lid, 'moss grew over the trough\'s opening (%d points)' % len(lid))
    print('PASS grow on open shapes: %.2f m2 on a basin open underneath (its holes filled for the growing, the basin left open), '
          '%.2f m2 on a thin sheet (thickened), %.2f m2 on a trough open on top with none over its opening; sheen, lumps and '
          'greens reach the cushions' % (on_open.data['moss_area'], on_sheet.data['moss_area'], on_trough.data['moss_area']))

    # ------------------------------------------------------------------ rocks: cushions by default, paint as before
    garden = rocks.material('boulder', None, 0.9, 0.7, 0.4, 0.0, None, None)        # the garden's own call
    check('cushions' in garden.name and garden.get('rocks_cushions'), 'the rocks\' moss is not cushions by default')
    nodes = garden.node_tree.nodes
    check(nodes.get('Moss amount') is not None and [n for n in nodes if n.type == 'TEX_VORONOI'], 'cushioned rocks lost their moss amount or lichen')
    found = [n for n in nodes if n.type == 'MATH' and n.operation == 'MULTIPLY' and n.use_clamp and not n.inputs[1].is_linked
             and n.inputs[0].is_linked and abs(n.inputs[1].default_value - 0.9) < 1e-3]
    check(len(found) == 1 and found[0].name == 'Moss amount', 'the garden\'s search for the moss amount finds %d nodes' % len(found))
    paint = rocks.material('boulder', None, 0.9, 0.7, 0.4, 0.0, None, None, moss_style='paint')
    check('cushions' not in paint.name and not paint.get('rocks_cushions') and not [n for n in paint.node_tree.nodes if n.type == 'TEX_VORONOI'],
          'moss_style paint is not the colour only, as before')
    try:
        rocks.material('boulder', moss=0.5, moss_style='fur')
        check(False, 'moss_style fur was not refused')
    except ValueError:
        pass
    shapes_made = rocks._shapes('boulder', [5, 6], 0.5, None, garden, 40)           # as the garden's rocks_at calls it
    for shape in shapes_made.objects:
        check(len(shape.data.materials) == 2 and shape.data['moss_area'] > 0 and shape.modifiers.get('moss pile'),
              '%s has no cushions or pile' % shape.name)
    bumped = rocks.material('flat', 'lichen_rock', 0.9, 0.7, 0.35, 0.03, None, None)
    shape = rocks._shapes('flat', [220], 0.7, None, bumped, 64).objects[0]
    check([m.type for m in shape.modifiers] == ['PARTICLE_SYSTEM', 'SUBSURF'], 'a bumped shape\'s modifiers are %s' % [m.type for m in shape.modifiers])
    sheet = rocks._sheet('test sheet', [((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0)], bpy.context.scene.collection)
    check(len(sheet.data.polygons) == 1, '_sheet no longer makes its tiny face')
    flat = rocks.at_spots([(6.0, 0.0)], kind='flat', size=0.6, moss=0.9, relief=0.02, detail=3, seed=4)
    shape = flat['shapes'][0].objects[0]
    check(shape.modifiers['finer for the bumps'].render_levels == 3 and shape.modifiers.get('moss pile'), 'at_spots lost its finer skin or pile')
    placed = rocks.place([(8.0, 0.0)], kind='boulder', size=0.6, moss=1.0, seed=3)[0]
    check(placed.data['moss_area'] > 0 and placed.modifiers[0].type == 'PARTICLE_SYSTEM' and placed.modifiers[-1].type == 'SUBSURF',
          'place() rocks have no cushions, pile and finer skin')
    print('PASS rocks: moss is real cushions by default (the garden\'s calls to material, _shapes and _sheet unchanged), paint as before, lichen on the stone')

    # ------------------------------------------------------------------ feet: moss and plants where rocks meet the soil
    import ground as ground_tool
    yard = ground_tool.make(size=(4.0, 4.0), cell=0.1, relief=0.02, seed=1, name='test yard')
    yard.location.x = 12.0
    bpy.context.view_layer.update()
    laid = rocks.scatter(yard, kind='boulder', count=4, sizes=(0.2, 0.5), moss=0.8, seed=2)
    made = moss.feet(yard, laid, turf=0.5, ferns=1, seed=3)
    check(made['moss'] is not None and made['moss'].data['moss_area'] > 0.02, 'feet laid no moss at the rocks\' feet')
    check(made['moss'].particle_systems and made['moss'].particle_systems[0].settings.count > 100
          and not made['moss'].show_instancer_for_render, 'the moss at the feet is not tufts on the soil (its sheet would be drawn)')
    check(made['turf'] is not None and made['ferns'] and len(made['ferns']) == 1, 'feet grew no turf or fern')
    print('PASS feet: %.2f m2 of moss at the feet of %d rocks, turf and a fern' % (made['moss'].data['moss_area'], laid['placed']))

    # ------------------------------------------------------------------ feet: keep the moss, turf and ferns out of places
    fern = made['ferns'][0]
    fx, fy = fern.location.x, fern.location.y
    size = 0.6
    block = (fx - 0.35, fy - 0.35, fx + 0.35, fy + 0.35)                    # an area over where the fern landed
    kept = moss.feet(yard, laid, turf=0.5, ferns=1, seed=3, keep_out=block)
    check(len(kept['ferns']) == 1 and kept['ferns_left_out'] == 0, 'feet with keep_out set no fern (%d left out)' % kept['ferns_left_out'])
    kx, ky = kept['ferns'][0].location.x, kept['ferns'][0].location.y
    check(not (block[0] <= kx <= block[2] and block[1] <= ky <= block[3]), 'a fern landed inside the keep_out area')
    weights = [v.groups[0].weight for v in kept['moss'].data.vertices if v.groups] if kept['moss'] else []
    inside = [w for v, w in zip([v for v in kept['moss'].data.vertices if v.groups], weights)
              if block[0] <= v.co.x <= block[2] and block[1] <= v.co.y <= block[3]]
    check(inside and max(inside) == 0.0, 'the moss at the feet grows inside the keep_out area')
    tested = moss.feet(yard, laid, turf=0.0, ferns=2, seed=3, keep=lambda x, y: abs(x - fx) > 0.6 or abs(y - fy) > 0.6)
    check(all(abs(f.location.x - fx) > 0.6 or abs(f.location.y - fy) > 0.6 for f in tested['ferns']), 'keep(x, y) let a fern in where it said no')
    nowhere = moss.feet(yard, laid, turf=0.0, ferns=1, seed=3, keep=lambda x, y: False)
    check(not nowhere['ferns'] and nowhere['ferns_left_out'] == 1, 'a fern was set where keep said no everywhere')
    again = moss.feet(yard, laid, turf=0.0, ferns=1, seed=3)
    check((again['ferns'][0].location - fern.location).length < 1e-6, 'feet without keep no longer sets its fern as before')
    for bad in ({'keep': 3}, {'keep_out': [(0, 0), (1, 1)]}):
        try:
            moss.feet(yard, laid, turf=0.0, **bad)
            check(False, 'feet(%r) was not refused' % bad)
        except ValueError:
            pass
    print('PASS feet keep and keep_out: the fern moves to another side out of the area, no moss inside it, keep(x, y) followed, '
          'none where nothing is kept; without them as before')

    # ------------------------------------------------------------------ the tool's description and --help
    for key in ('name', 'what', 'call', 'options', 'materials', 'source', 'trap'):
        check(moss.TOOL.get(key), 'the moss tool says nothing for %s' % key)
    for option in ('lichen', 'thickness', 'pile_amount', 'reach', 'turf', 'ferns', 'keep', 'keep_out', 'sheen', 'lumps', 'greens'):
        check(option in moss.TOOL['options'], 'the moss tool does not describe %s' % option)
    for option in ('moss_style', 'moss_thickness', 'moss_pile', 'lichen'):
        check(option in rocks.TOOL['options'], 'the rocks tool does not describe %s' % option)
    for tool in ('moss.py', 'rocks.py'):
        answer = subprocess.run([sys.executable, os.path.join(TOOLS, tool), '--help'], capture_output=True, text=True)
        check(answer.returncode == 0 and 'Trap' in answer.stdout, '%s --help does not answer' % tool)
    print('PASS the moss tool and the rocks tool describe their new options and answer --help')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as failure:
        print('FAIL test_store_moss: %s' % failure)
        sys.exit(1)
