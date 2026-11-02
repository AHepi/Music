"""
What this file does: checks what the tea house set (log 44) taught the plugin, on a small scene built here:
  - the brass, copper and china roles get their own made materials (metal for brass and copper, a glazed coat for china);
  - four windows in a plaster wall each get joinery, and what the builder made is kept, not doubled: a plain window
    gets a casing, a sill and a sash with glazing bars; a window with the builder's own sash bars gets no second sash;
    one with the builder's own surround gets no casing; one with the builder's own sill gets no second sill;
  - a window in a plain timber wall gets a sash;
  - the drawing script's measure of how much of the frame glowing glass takes up: small from across the street,
    most of the frame from right in front of a lit pane.
    python3 tests/test_tea_house_lessons.py
"""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'materials'))
sys.path.insert(0, os.path.join(HERE, '..', 'stage'))
import apply_by_role  # noqa: E402
import look_stage  # noqa: E402

WALL_FACE_Y = 4.85          # the plaster wall's front face; the camera stands at negative Y looking along +Y
WINDOWS_X = (-3.6, -1.2, 1.2, 3.6)
WINDOW_Z = (1.25, 2.75)


def box(name, centre, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return obj


def aim(camera, at):
    camera.rotation_euler = (Vector(at) - camera.location).to_track_quat('-Z', 'Y').to_euler()


def centres(obj):
    """The centre of every face of the joinery, in the world (a long bar has corners only at its ends; its faces' centres
    lie along it)."""
    return [obj.matrix_world @ polygon.center for polygon in obj.data.polygons]


def joinery_points_inside(obj, x_centre, half_width, z0, z1):
    """Faces of the joinery that lie over a window's glass (between its edges, well inside its frame)."""
    return [p for p in centres(obj) if abs(p.x - x_centre) < half_width and z0 < p.z < z1 and p.y < WALL_FACE_Y]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    box('tea room front wall plaster', (0, 5.0, 3.0), (10, 0.3, 6))
    middle = (WINDOW_Z[0] + WINDOW_Z[1]) / 2
    for number, x in enumerate(WINDOWS_X, start=1):
        box('window lit %d' % number, (x, WALL_FACE_Y - 0.02, middle), (1.0, 0.04, WINDOW_Z[1] - WINDOW_Z[0]))
    box('upper sash bars 2 wood', (WINDOWS_X[1], WALL_FACE_Y - 0.05, middle), (1.0, 0.03, 1.5))       # the builder's own sash
    box('surround 3 stone', (WINDOWS_X[2], WALL_FACE_Y + 0.01, middle), (1.3, 0.05, 1.8))             # the builder's own surround
    box('sill 4 stone', (WINDOWS_X[3], WALL_FACE_Y - 0.06, WINDOW_Z[0] - 0.05), (1.2, 0.12, 0.10))    # the builder's own sill
    box('side shed wall timber', (9.0, 6.0, 1.5), (4.0, 0.1, 3.0))
    box('shed window dark', (9.0, 5.93, 1.6), (0.9, 0.04, 1.2))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(-1, 2, 1.0))
    bpy.context.object.name = 'tea urn'
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 2, 1.0))
    bpy.context.object.name = 'copper kettle'
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(1, 2, 1.0))
    bpy.context.object.name = 'teapot'
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.07, location=(1.3, 2, 1.0))
    bpy.context.object.name = 'teacups 2'
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    scene.collection.objects.link(camera)
    camera.location = (0.0, -8.0, 1.65)
    aim(camera, (0.0, WALL_FACE_Y, 2.2))
    camera.data.lens = 32
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = 540, 960

    report = apply_by_role.apply(scene, setts=False, details=False)
    roles = report['by_role']
    assert roles.get('brass') == 1 and roles.get('copper') == 1 and roles.get('china') == 2, roles
    assert report['unassigned'] == [], report['unassigned']
    for name, made_for in (('tea urn', 'brass'), ('copper kettle', 'copper'), ('teapot', 'china'), ('teacups 2', 'china')):
        material = scene.objects[name].data.materials[0]
        assert material.get('pp_made_for') == made_for, (name, material.name)
        principled = material.node_tree.nodes.get('Principled BSDF')
        if made_for == 'china':
            assert principled.inputs['Coat Weight'].default_value > 0.3, material.name
        else:
            assert principled.inputs['Metallic'].is_linked, material.name            # metal, with the tarnish worked in
    print('PASS brass, copper and china: their own materials (%s)' % ', '.join(sorted({scene.objects[n].data.materials[0].name for n in ('tea urn', 'copper kettle', 'teapot')})))

    facade = report['facade']
    assert facade['plaster_windows_dressed'] == 4, facade
    assert facade['builder_sashes_kept'] == 1 and facade['builder_surrounds_kept'] == 1 and facade['builder_sills_kept'] == 1, facade
    joinery = scene.objects.get('FACADE • tea room front wall plaster • window joinery')
    assert joinery is not None and len(joinery.data.polygons) > 100, 'no joinery on the plaster wall'
    assert joinery.get('place_role') == 'wood'
    glass_z = (WINDOW_Z[0] + 0.15, WINDOW_Z[1] - 0.15)
    # window 1 (nothing of the builder's): bars over its glass, a casing beside it, a sill under it
    assert joinery_points_inside(joinery, WINDOWS_X[0], 0.35, *glass_z), 'window 1 got no sash'
    beside = [p for p in centres(joinery) if 0.52 <= abs(p.x - WINDOWS_X[0]) <= 0.65 and glass_z[0] < p.z < glass_z[1]]
    assert beside, 'window 1 got no casing'
    under = [p for p in centres(joinery) if abs(p.x - WINDOWS_X[0]) < 0.5 and WINDOW_Z[0] - 0.08 < p.z < WINDOW_Z[0]]
    assert under, 'window 1 got no sill'
    # window 2 (the builder's own sash): no second sash over its glass
    assert not joinery_points_inside(joinery, WINDOWS_X[1], 0.35, *glass_z), 'window 2 got a second sash'
    # window 3 (the builder's own surround): no casing beside it
    beside_3 = [p for p in centres(joinery) if 0.52 <= abs(p.x - WINDOWS_X[2]) <= 0.65 and glass_z[0] < p.z < glass_z[1]]
    assert not beside_3, 'window 3 got a casing inside the builder\'s surround'
    # window 4 (the builder's own sill): no second sill under it
    under_4 = [p for p in centres(joinery) if abs(p.x - WINDOWS_X[3]) < 0.5 and WINDOW_Z[0] - 0.08 < p.z < WINDOW_Z[0] - 0.01]
    assert not under_4, 'window 4 got a second sill'
    print('PASS plaster wall windows: casing, sill and sash, and the builder\'s own sash, surround and sill kept (%d blocks)' % len(joinery.data.polygons))

    assert report['boards']['window_sashes'] == 1, report['boards']
    print('PASS a window in a plain timber wall gets a sash')

    share = look_stage.glowing_share_of_frame(scene)
    assert share is not None and 0.0 < share < 0.08, share
    camera.location = (WINDOWS_X[0], WALL_FACE_Y - 0.6, 2.0)
    aim(camera, (WINDOWS_X[0], WALL_FACE_Y, 2.0))
    close = look_stage.glowing_share_of_frame(scene)
    assert close > 0.5, close
    print('PASS glowing share of the frame: %.1f%% from across the street, %.0f%% right in front of a lit pane' % (share * 100, close * 100))
    print('PASS test_tea_house_lessons')


if __name__ == '__main__':
    main()
