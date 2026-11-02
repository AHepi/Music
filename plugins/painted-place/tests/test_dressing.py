"""
What this file does: checks the whole dressing on a tiny street built here (two wall boxes with a window and a door,
a pavement, a kerb, a flat road, an iron pipe and a lamp, a camera): the road becomes laid setts, the facing wall is
laid up in ashlar with its window dressed, and the details appear where they belong (puddles, gutter water, damp
feet, weeds, moss, rubbish) and nowhere absurd (nothing above 5 m, nothing parked prototypes counted in the look's bounds).
    python3 tests/test_dressing.py
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


def box(name, centre, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return obj


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 10, 0))
    road = bpy.context.object
    road.name = 'road setts'
    road.scale = (6, 24, 1)
    bpy.ops.object.transform_apply(scale=True)
    box('pavement flags left', (-4.0, 10, 0.07), (2.0, 24, 0.14))
    box('kerb stone left', (-3.1, 10, 0.08), (0.2, 24, 0.16))
    box('left terrace wall', (-7.5, 10, 6), (5, 24, 12))
    box('left terrace window lit', (-4.94, 8, 4.5), (0.06, 1.0, 1.6))
    box('left terrace door wood', (-4.94, 12, 1.25), (0.06, 1.1, 2.4))
    box('downpipe iron', (-4.9, 15, 5), (0.1, 0.1, 10))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=3.6, location=(-3.4, 6, 1.9))
    bpy.context.object.name = 'lamp post iron'
    box('lamp glass', (-3.4, 6, 3.95), (0.3, 0.3, 0.45))
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    scene.collection.objects.link(camera)
    camera.location = (0.0, -4.0, 1.65)
    camera.rotation_euler = (Vector((-2.0, 12.0, 1.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 32
    scene.camera = camera

    report = apply_by_role.apply(scene)
    assert report['unassigned'] == [], report['unassigned']
    assert report['laid_stones'].get('road setts', {}).get('setts', 0) > 1000, report['laid_stones']
    facade, details = report['facade'], report['details']
    assert facade['walls_built'] == 1 and facade['blocks'] > 200, facade
    assert facade['windows_dressed'] == 1, facade
    assert facade['things_moved_out'] >= 1, facade                      # the downpipe moved out with the new face
    for key in ('puddles', 'gutter_runs', 'damp_feet', 'weed_tufts', 'moss_patches', 'rubbish_pieces', 'litter_pieces'):
        assert details.get(key, 0) > 0, (key, details)
    assert details['rubbish_kind'].startswith('street'), details
    assert details['pipes_rusted'] >= 1, details
    # nothing small floats high above the street
    for obj in scene.objects:
        if obj.name.startswith('DETAIL •') and obj.type == 'MESH' and not obj.get('prototype') and len(obj.data.vertices):
            top = max((obj.matrix_world @ v.co).z for v in obj.data.vertices)
            if obj.name.startswith(('DETAIL • weed', 'DETAIL • moss', 'DETAIL • rubbish', 'DETAIL • wet leaves', 'DETAIL • puddles')):
                assert top < 0.6, (obj.name, top)
    # the look's bounds ignore parked prototypes
    low, high = look_stage.scene_bounds(scene)
    assert low.z > -2.0, ('parked prototypes leaked into the bounds', low)
    # running the dressing again does not pile things up
    count = len(scene.objects)
    bed_z = scene.objects['road setts'].location.z
    apply_by_role.apply(scene)
    assert len(scene.objects) == count, (count, len(scene.objects))
    assert abs(scene.objects['road setts'].location.z - bed_z) < 1e-6, 'the road bed sank again on a second dressing'
    print('PASS test_dressing')


if __name__ == '__main__':
    main()
