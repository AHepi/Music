"""
What this file does: checks the scanned surfaces (the Poly Haven pictures in materials/textures) on a small place built
here: a plain timber shed wall taller than it is wide, a second wall turned 45 degrees, a kerb and a boulder whose scale
was never applied, a deck and a beam sharing one mesh, a stone wall, a road and a pavement. It checks that:
  - the pictures are all there (a broken manifest fails here instead of quietly switching the scans off);
  - the plugin's own lapped boards have their grain along the boards on both walls;
  - every dressed object carries its real scale (so a stretched kerb gets an unstretched picture);
  - the stone grain goes on the walls and flags and never on the setts, and only once when dressed twice;
  - a deck and a beam sharing a mesh each get their own material (planks and boards);
  - ashlar blocks each carry their own number (so the grain differs block to block);
  - the pictures are packed into the dressed file;
  - with the scans switched off, the code-made materials come back and nothing is grained.
    python3 tests/test_scans.py
"""
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'materials'))
import apply_by_role  # noqa: E402
import scans  # noqa: E402


def box(name, centre, size, apply_scale=True, rotation=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = (0, 0, rotation)
    if apply_scale:
        bpy.ops.object.transform_apply(scale=True, rotation=True)
    return obj


def place():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 10, 0))
    road = bpy.context.object
    road.name = 'road setts'
    road.scale = (6, 24, 1)
    bpy.ops.object.transform_apply(scale=True)
    box('pavement flags left', (-4.0, 10, 0.07), (2.0, 24, 0.14))
    box('kerb stone left', (-3.0, 10, 0.08), (0.2, 24, 0.16), apply_scale=False)          # scale never applied
    box('left terrace wall', (-7.5, 14, 6), (5, 16, 12))
    box('shed wall timber', (2.6, 3.0, 1.3), (1.6, 0.2, 2.6))                            # taller than it is wide
    box('turned shed wall timber', (3.5, 7.0, 1.3), (3.0, 0.2, 2.4), rotation=0.785)     # turned 45 degrees
    box('shore boulder rock', (2.5, 12, 0.3), (2.0, 1.2, 0.6), apply_scale=False)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.5, 16.0, 0.05))
    deck = bpy.context.object
    deck.name = 'yard deck timber'
    deck.scale = (4.0, 3.0, 0.1)
    beam = bpy.data.objects.new('yard beam timber', deck.data)                           # the same mesh, scaled as a beam
    scene.collection.objects.link(beam)
    beam.location = (1.5, 19.0, 1.5)
    beam.scale = (0.2, 0.2, 3.0)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    scene.collection.objects.link(camera)
    camera.location = (0.0, -6.0, 1.65)
    camera.rotation_euler = (Vector((0.0, 12.0, 1.0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 32
    scene.camera = camera
    return scene


def main():
    textures = os.path.join(HERE, '..', 'materials', 'textures')
    assert os.path.isdir(textures), 'the textures folder is missing'
    assert scans.available(), 'the textures folder is here but a manifest entry or picture is broken'

    scene = place()
    report = apply_by_role.apply(scene)
    assert report['scans_on_the_shelf'] and report['stone_given_scanned_grain'] >= 2, report['stone_given_scanned_grain']

    laid = [o for o in scene.objects if o.name.startswith('TIMBER •') and 'lapped boards' in o.name]
    assert len(laid) >= 2, [o.name for o in laid]
    for obj in laid:
        assert obj.get('pp_grain') == 0.0, (obj.name, obj.get('pp_grain'))
        along = obj.matrix_world.to_3x3().col[0]
        assert abs(along.z) < 1e-6, (obj.name, 'the boards run up the wall', tuple(along))
    turned = [o for o in laid if o.name.startswith('TIMBER • turned')]
    assert turned, 'no boards on the turned wall'
    wall_direction = Vector((0.7071, 0.7071, 0.0))
    assert abs(turned[0].matrix_world.to_3x3().col[0].normalized().dot(wall_direction)) > 0.99, 'boards not along the turned wall'

    kerb = scene.objects['kerb stone left']
    assert abs(kerb['pp_scale'][0] - 0.2) < 1e-4 and abs(kerb['pp_scale'][1] - 24) < 1e-3, tuple(kerb['pp_scale'])

    for material in bpy.data.materials:
        if material.name.startswith('COBBLES'):
            assert not material.get('pp_stone_grain'), 'the setts were grained'
    assert any(m.get('pp_stone_grain') for m in bpy.data.materials if m.name.startswith('PAVEMENT')), 'the flags have no grain'

    deck, beam = scene.objects['yard deck timber'], scene.objects['yard beam timber']
    assert deck.data != beam.data, 'a shared mesh dressed two ways was not split'
    assert deck.active_material.name.startswith('SCAN • weathered deck planks'), deck.active_material.name
    assert beam.active_material.name.startswith('SCAN • weathered boards'), beam.active_material.name

    facades = [o for o in scene.objects if o.name.startswith('FACADE •') and 'ashlar' in o.name]
    assert facades, 'no ashlar built'
    tones = [p.value for p in facades[0].data.attributes['board_tone'].data]
    assert len(set(round(t, 3) for t in tones)) > 50, 'the blocks do not carry their own numbers'

    scan_images = [i for i in bpy.data.images if i.filepath and 'textures' in i.filepath]
    assert scan_images and all(i.packed_file is not None for i in scan_images), [i.name for i in scan_images if i.packed_file is None]

    grained = sum(1 for m in bpy.data.materials if m.get('pp_stone_grain'))
    apply_by_role.apply(scene)
    assert sum(1 for m in bpy.data.materials if m.get('pp_stone_grain')) == grained, 'grain added twice'

    # switched off: the code-made materials, no grain
    scans.ENABLED = False
    try:
        scene = place()
        apply_by_role.apply(scene)
        assert not any(m.get('pp_stone_grain') for m in bpy.data.materials), 'grain with the scans off'
        laid = [o for o in scene.objects if o.name.startswith('TIMBER •') and 'lapped boards' in o.name]
        assert laid and laid[0].data.materials[0].name.startswith('TIMBER •'), laid[0].data.materials[0].name
    finally:
        scans.ENABLED = True
    print('PASS test_scans')


if __name__ == '__main__':
    main()
