# What this does: the first half of calibrating the Puddles dial. It puts the WETNESS layer on the street (a copy), then draws each of three cameras (the
# film's main camera, the lockout plate camera, the notice-corner plate camera; props are not in this copy of the street, so the notice-corner view has an
# emptier road than the real shot) as a picture of numbers: red = the layer's "Puddle Depth" on the road and the pavements, green = 1 on the road,
# blue = 1 on the pavements, black everywhere else. 540 x 960, one light sample each (a few seconds). A second script (02b_puddle_fit.py, plain Python) reads them,
# counts what share of the road is puddle for any dial setting, and fits the dial's curve.
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/02_puddle_sweep.py -- OUT_FOLDER
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

out_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
aw.apply(wetness=0.85, puddles=0.5)
aw.mask_settings(scene, 540, 960)
scene.render.image_settings.color_depth = '8'
for material in bpy.data.materials:
    tree = material.node_tree
    if tree is None:
        continue
    output = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if output is None:
        continue
    emission = tree.nodes.new('ShaderNodeEmission')
    if material.name in ('street_setts', 'pavement_flags'):
        node = aw.APPLIED[material.name][0]
        combine = tree.nodes.new('ShaderNodeCombineColor')
        tree.links.new(node.outputs['Puddle Depth'], combine.inputs['Red'])
        combine.inputs['Green'].default_value = 1.0 if material.name == 'street_setts' else 0.0
        combine.inputs['Blue'].default_value = 1.0 if material.name == 'pavement_flags' else 0.0
        tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    else:
        emission.inputs['Color'].default_value = (0, 0, 0, 1)
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
for name in ('main', 'lockout', 'notice'):
    scene.camera = cams[name]
    scene.render.filepath = os.path.join(out_folder, f'{name}_depth.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    print('DRAWN', name, round(time.time() - started, 1), 's')

# the whole street seen from straight above (orthographic, 20 dots a metre), only the road, channels, kerbs and pavements: the share of the AREA that is puddle
for obj in scene.objects:
    obj.hide_render = obj.name not in ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements')
data = bpy.data.cameras.new('overhead')
data.type = 'ORTHO'
data.ortho_scale = 84.0
data.clip_start, data.clip_end = 0.1, 300.0
overhead = bpy.data.objects.new('overhead', data)
scene.collection.objects.link(overhead)
overhead.location = (0.0, 30.0, 100.0)
scene.camera = overhead
scene.render.resolution_x, scene.render.resolution_y = 176, 1680
scene.render.filepath = os.path.join(out_folder, 'overhead_depth.png')
bpy.ops.render.render(write_still=True)
print('DRAWN overhead')
