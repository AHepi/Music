"""
What this file does: checks the look stage on a tiny scene built here (a ground, a wall, one glowing window,
one lamp, a camera): lights appear at the glowing patches, the scene's own light is muted, the sky and the
finish are set, a 96 x 170 picture draws, and remove_look puts everything back. Run with the bpy module:
    python3 tests/test_look_stage.py
or inside Blender:  blender -b --python tests/test_look_stage.py
"""
import os
import sys
import tempfile

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'stage'))
import look_stage  # noqa: E402


def glowing(name, colour, strength):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes['Principled BSDF']
    principled.inputs['Emission Color'].default_value = (*colour, 1)
    principled.inputs['Emission Strength'].default_value = strength
    return material


def box(name, location, size, material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if material:
        obj.data.materials.append(material)
    return obj


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    box('ground', (0, 10, -0.05), (20, 40, 0.1))
    box('wall', (-5, 10, 5), (1, 20, 10))
    box('window lit', (-4.45, 8, 4), (0.1, 1, 1.5), glowing('GLASS test warm', (1, 0.4, 0.08), 2.8))
    box('window cold', (-4.45, 12, 4), (0.1, 1, 1.5), glowing('GLASS test cold', (0.2, 0.4, 1.0), 2.0))
    box('lamp glass', (3, 6, 3.8), (0.3, 0.3, 0.4), glowing('Lamp glass test', (1, 0.5, 0.1), 5))
    box('fire flame', (1, 4, 0.3), (0.4, 0.4, 0.5), glowing('Fire flame test', (1, 0.45, 0.1), 8))
    own = bpy.data.lights.new('own sun', 'SUN')
    own_obj = bpy.data.objects.new('own sun', own)
    scene.collection.objects.link(own_obj)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    scene.collection.objects.link(camera)
    camera.location = (0, -8, 1.65)
    camera.rotation_euler = (1.45, 0, 0)
    scene.camera = camera

    report = look_stage.apply_look(scene, samples=4, resolution=(96, 170))
    names = [o.name for o in scene.objects if o.name.startswith(look_stage.LOOK_PREFIX)]
    assert report['glow_patches_found'] == 3, report  # the warm window, the lamp and the fire; the cold window is not warm
    assert report['glow_lights_added'] == 4, report   # lamp: mantle + wash; window: one; fire: one
    assert any('glow lamp' in n for n in names) and any('glow window' in n for n in names) and any('glow fire' in n for n in names), names
    assert own_obj.hide_render and own_obj.get('look_muted'), 'the scene light should be muted, not deleted'
    assert scene.world.name.startswith(look_stage.LOOK_PREFIX), scene.world.name
    assert scene.compositing_node_group.name.startswith(look_stage.LOOK_PREFIX)
    assert scene.render.engine == 'CYCLES' and scene.view_settings.look == 'AgX - Medium High Contrast'
    assert any(n.type == 'KUWAHARA' for n in scene.compositing_node_group.nodes)
    low, high = report['bounds']
    assert low[2] <= 0 and high[2] >= 5, report['bounds']

    out = os.path.join(tempfile.mkdtemp(), 'tiny.png')
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    assert os.path.exists(out) and os.path.getsize(out) > 500, 'the tiny picture did not draw'

    look_stage.remove_look(scene)
    assert not [o for o in scene.objects if o.name.startswith(look_stage.LOOK_PREFIX)], 'look objects should be gone'
    assert not own_obj.hide_render, 'the scene light should be lit again'
    assert scene.world is None or not scene.world.name.startswith(look_stage.LOOK_PREFIX)
    assert scene.compositing_node_group is None

    # applying twice is safe
    look_stage.apply_look(scene, samples=4, resolution=(96, 170))
    look_stage.apply_look(scene, samples=4, resolution=(96, 170))
    assert len([o for o in scene.objects if o.type == 'LIGHT' and o.name.startswith(look_stage.LOOK_PREFIX)]) == 4 + 4
    print('PASS test_look_stage')


if __name__ == '__main__':
    main()
