# What this does: shows where the WETNESS layer puts water on the cottage walls, as plain pictures (no lighting): red = how wet (wet band at the foot, damp, streaks),
# green = the streak mask (rain running down from every window sill and the eaves), blue = the dry value of the wall. Two cottage fronts: the right-hand stone
# cottage 03 (facade layout "door_left") and the left-hand brick cottage 03 ("door_left"), seen square-on from the middle of the road, 600 x 800 dots, one
# sample each. Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/03_wall_masks.py -- OUT_FOLDER [wetness]
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

out_folder = sys.argv[sys.argv.index('--') + 1]
wetness = float(sys.argv[sys.argv.index('--') + 2]) if len(sys.argv) > sys.argv.index('--') + 2 else 0.85
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
aw.cameras()
aw.apply(wetness=wetness, puddles=0.5)
aw.mask_settings(scene, 600, 800)
scene.render.image_settings.color_depth = '8'
for material in bpy.data.materials:
    tree = material.node_tree
    output = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None) if tree else None
    if output is None:
        continue
    emission = tree.nodes.new('ShaderNodeEmission')
    if material.name in aw.APPLIED:
        node = aw.APPLIED[material.name][0]
        combine = tree.nodes.new('ShaderNodeCombineColor')
        tree.links.new(node.outputs['Wet Mask'], combine.inputs['Red'])
        tree.links.new(node.outputs['Streak Mask'], combine.inputs['Green'])
        combine.inputs['Blue'].default_value = 0.0
        tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    else:
        emission.inputs['Color'].default_value = (0.0, 0.0, 0.25, 1)
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
for name, location, target in (('stone_front', (-0.5, 10.75, 3.0), (4.15, 10.75, 3.0)), ('brick_front', (0.5, 10.75, 3.0), (-4.15, 10.75, 3.0))):
    camera = aw.make_camera(name, location, look_at=target, fov_vertical=68.0)
    scene.camera = camera
    scene.render.filepath = os.path.join(out_folder, f'{name}_masks.png')
    bpy.ops.render.render(write_still=True)
    print('DRAWN', name)
