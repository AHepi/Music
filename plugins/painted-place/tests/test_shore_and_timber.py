"""
What this file does: checks the timber, shore and tree details on two tiny places built here.

  A beach: sand sloping into the sea, a plain timber shed wall with a window, a timber post, a palm trunk and a rock
  at the water's edge. The wall must be laid as boards; the sand by the water must get a wet film, the sea foam, the
  sand a wrack line and driftwood; the rock a wet copy of its material; the post and wall sand drifted at their feet
  and rot up them; the palm fronds and coconuts on the ground.

  A garden pond: earth round still water, a plain timber wall with a door, a fence post and a tree trunk. The water
  must get a mossy bank and leaves, no foam and no wrack; the post weeds at its foot; the tree leaves under it.

  A tea room: a flagged floor, three plaster walls and a ceiling (the camera's wall left out), a table, a timber post
  and a stove. Nothing may grow or gather indoors: no weeds, moss, leaves, rubbish, damp or rot at any foot.

On all three: nothing small floats, and dressing a second time changes nothing.
    python3 tests/test_shore_and_timber.py
"""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'materials'))
import apply_by_role  # noqa: E402
import lay_shore  # noqa: E402


def box(name, centre, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return obj


def camera_at(scene, spot, target):
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    scene.collection.objects.link(camera)
    camera.location = spot
    camera.rotation_euler = (Vector(target) - Vector(spot)).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 32
    scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
    scene.camera = camera


def ground_below(scene, point):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    start = Vector((point.x, point.y, point.z + 0.5))
    for _ in range(40):
        hit, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, start, Vector((0, 0, -1)), distance=5.0)
        if not hit:
            return None
        if obj.name.startswith(('DETAIL •', 'LOOK •')) or normal.z < 0.6:
            start = location - Vector((0, 0, 0.00002))     # just past it: a flake can lie a fraction of a millimetre above the sand
            continue
        return location.z
    return None


def nothing_floats(scene, names, tolerance):
    for obj in scene.objects:
        if not obj.name.startswith(names) or obj.type != 'MESH':
            continue
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        step = max(1, len(vertices) // 60)
        for point in vertices[::step]:
            z = ground_below(scene, point)
            assert z is not None and point.z - z < tolerance, (obj.name, tuple(round(c, 2) for c in point), z)


def beach():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=40, size=1, location=(0, 0, 0.1))
    sand = bpy.context.object
    sand.name = 'beach sand'
    sand.scale = (24, 24, 1)
    bpy.ops.object.transform_apply(scale=True)
    for v in sand.data.vertices:
        v.co.z = -0.05 * v.co.y                      # the beach slopes down into the sea; the waterline is near y = 2
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 28, 0))
    sea = bpy.context.object
    sea.name = 'sea water'
    sea.scale = (80, 60, 1)
    bpy.ops.object.transform_apply(scale=True)
    box('shed wall timber', (-1.0, -4.0, 1.45), (4.0, 0.2, 2.4))
    box('shed window dark', (-1.0, -4.13, 1.6), (0.8, 0.06, 0.8))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=2.6, location=(2.5, -4.0, 1.55))
    bpy.context.object.name = 'shed post timber'
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.18, depth=8.0, location=(-5.0, 0.0, 4.1))
    bpy.context.object.name = 'palm trunk'
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.7, location=(4.0, 2.4, 0.0))
    bpy.context.object.name = 'shore rock'
    camera_at(scene, (0.0, -12.0, 2.3), (0.0, 4.0, 0.4))

    report = apply_by_role.apply(scene)
    boards, details = report['boards'], report['details']
    shore, timber, trees = details['shore'], details['timber'], details['trees']
    assert report['timber_looks'].get('bark') == 1 and report['timber_looks'].get('boards', 0) >= 2, report['timber_looks']
    assert boards['timber_walls_boarded'] == 1 and boards['boards'] > 12, boards
    assert shore['water_kinds'] == ['sea'], shore
    for key in ('wet_ground_cells', 'foam_patches', 'wrack_pieces', 'driftwood_logs', 'things_wet_to_the_tide_line', 'sand_drift_runs'):
        assert shore.get(key, 0) > 0, (key, shore)
    assert timber['rot_faces'] > 0, timber
    assert trees['palm_fronds_on_the_ground'] + trees['coconuts_and_husks'] > 0, trees
    rock = scene.objects['shore rock']
    assert lay_shore.WET_SUFFIX in rock.active_material.name, rock.active_material.name
    import scans
    if scans.available():
        laid = [o for o in scene.objects if o.name.startswith('TIMBER •') and o.type == 'MESH']
        assert laid and laid[0].data.materials[0].name.startswith('SCAN •'), [o.data.materials[0].name for o in laid]
        sand_material = scene.objects['beach sand'].active_material
        assert any(n.type == 'TEX_IMAGE' for n in sand_material.node_tree.nodes), sand_material.name
        assert scene.objects['palm trunk'].active_material.name.startswith('SCAN • wet palm bark'), scene.objects['palm trunk'].active_material.name
        assert report['stone_given_scanned_grain'] >= 1, report['stone_given_scanned_grain']
    nothing_floats(scene, ('DETAIL • shore wet ground', 'DETAIL • shore wrack', 'DETAIL • tree dead palm', 'DETAIL • timber paint'), 0.08)
    # dress again: nothing piles up, no wet copy of a wet copy
    count, materials = len(scene.objects), len(bpy.data.materials)
    apply_by_role.apply(scene)
    assert len(scene.objects) == count, ('objects', count, len(scene.objects))
    assert len(bpy.data.materials) == materials, ('materials', materials, len(bpy.data.materials))
    assert rock.active_material.name.count(lay_shore.WET_SUFFIX.strip()) == 1, rock.active_material.name
    print('PASS test_shore_and_timber: beach')


def pond():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, centre, size in (('garden earth left', (-6, 4, -0.1), (16, 24, 0.2)), ('garden earth right', (14, 4, -0.1), (8, 24, 0.2)),
                               ('garden earth front', (6, -4, -0.1), (8, 12, 0.2)), ('garden earth back', (6, 12.5, -0.1), (8, 7, 0.2))):
        box(name, centre, size)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(6, 5.5, -0.14))
    water = bpy.context.object
    water.name = 'pond water'
    water.scale = (8, 7, 1)
    bpy.ops.object.transform_apply(scale=True)
    box('pond bed mud', (6, 5.5, -0.6), (8, 7, 0.2))
    box('garden wall timber', (-2.0, 7.0, 1.2), (5.0, 0.2, 2.4))
    box('garden door', (-2.0, 6.87, 1.0), (0.9, 0.06, 2.0))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1.2, location=(1.0, 1.0, 0.6))
    bpy.context.object.name = 'fence post timber'
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.2, depth=6.0, location=(-4.0, 3.0, 3.0))
    bpy.context.object.name = 'maple tree trunk'
    camera_at(scene, (2.0, -6.0, 1.65), (3.0, 6.0, 0.0))

    report = apply_by_role.apply(scene)
    boards, details = report['boards'], report['details']
    shore, trees, feet = details['shore'], details['trees'], details['feet']
    assert boards['timber_walls_boarded'] == 1, boards
    assert shore['water_kinds'] == ['still'], shore
    assert 'foam_patches' not in shore and shore.get('wrack_pieces', 0) == 0, shore
    assert shore.get('bank_leaves', 0) > 0 and shore.get('wet_ground_cells', 0) > 0, shore
    assert any(o.name.startswith('DETAIL • shore moss along the bank') for o in scene.objects), 'no moss along the bank'
    assert trees['fallen_leaves_under_trees'] > 0, trees
    assert feet['weed_tufts_at_feet'] + feet['moss_at_feet'] > 0, feet
    nothing_floats(scene, ('DETAIL • shore wet ground', 'DETAIL • tree fallen', 'DETAIL • weeds at the feet'), 0.08)
    count = len(scene.objects)
    apply_by_role.apply(scene)
    assert len(scene.objects) == count, ('objects', count, len(scene.objects))
    print('PASS test_shore_and_timber: pond')


def room():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    box('tea room floor flags', (0, 4, -0.05), (8, 8, 0.1))
    box('tea room back wall plaster', (0, 8.1, 1.6), (8, 0.2, 3.2))
    box('tea room left wall plaster', (-4.1, 4, 1.6), (0.2, 8.4, 3.2))
    box('tea room right wall plaster', (4.1, 4, 1.6), (0.2, 8.4, 3.2))
    box('tea room ceiling plaster', (0, 4, 3.3), (8.4, 8.4, 0.2))
    box('tea room table', (0.5, 5.0, 0.38), (1.2, 0.8, 0.76))
    box('tea room post timber', (-2.0, 6.0, 1.6), (0.2, 0.2, 3.2))
    box('tea room stove iron', (2.5, 7.4, 0.5), (0.7, 0.6, 1.0))
    box('tea room window lit', (0, 7.98, 1.6), (1.4, 0.06, 1.2))
    camera_at(scene, (0.0, 0.6, 1.6), (0.0, 8.0, 1.0))
    report = apply_by_role.apply(scene)
    details = report['details']
    for key in ('damp_feet', 'weed_tufts', 'moss_patches', 'litter_pieces', 'rubbish_pieces'):
        assert details.get(key, 0) == 0, (key, details.get(key))
    for key in ('weed_tufts_at_feet', 'moss_at_feet', 'leaves_at_feet'):
        assert details['feet'][key] == 0, (key, details['feet'])
    timber = details['timber']
    assert timber['rot_faces'] == 0 and timber['mould_faces'] == 0 and timber['flakes_and_splinters'] == 0, timber
    count = len(scene.objects)
    apply_by_role.apply(scene)
    assert len(scene.objects) == count, ('objects', count, len(scene.objects))
    print('PASS test_shore_and_timber: room')


if __name__ == '__main__':
    beach()
    pond()
    room()
