# What this does: measures how much DARKER each material gets when wet, with no lighting and no reflections in the way. For the main camera and the close wall
# camera it draws the layer's Colour output as plain light (one-sample, 16-bit grey), dry (wetness 0), wet (0.85 / puddles 0.5) and heavy (1.0 / 0.8), and a picture
# of which material is where (the material number as a grey level). A second script (04b_colour_ratios.py, plain Python) turns them into a table: wet colour /
# dry colour per material (1 = unchanged, 0.7 = a third darker). The calibration aim from the plan: stone, brick, setts, flags about 0.7 to 0.8, slate about 0.85.
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/04_colour_ratios.py -- OUT_FOLDER
import json
import os
import sys

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
names = sorted(aw.APPLIED)
ids = {name: index + 1 for index, name in enumerate(names)}
json.dump(ids, open(os.path.join(out_folder, 'material_ids.json'), 'w'), indent=1)
emissions = {}
for material in bpy.data.materials:
    tree = material.node_tree
    output = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None) if tree else None
    if output is None:
        continue
    emission = tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0, 0, 0, 1)
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    emissions[material.name] = (tree, emission)


def show(kind):
    for name, (tree, emission) in emissions.items():
        for link in list(emission.inputs['Color'].links):
            tree.links.remove(link)
        if name in aw.APPLIED:
            if kind == 'id':
                value = ids[name] / 255.0
                emission.inputs['Color'].default_value = (value, value, value, 1)
            else:
                tree.links.new(aw.APPLIED[name][0].outputs['Colour'], emission.inputs['Color'])
        else:
            emission.inputs['Color'].default_value = (0, 0, 0, 1)


for camera_name in ('main', 'wall_lamp'):
    scene.camera = cams[camera_name]
    scene.render.resolution_x, scene.render.resolution_y = (540, 960) if camera_name == 'main' else (640, 480)
    show('id')
    scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = 'RGB', '8'
    scene.render.filepath = os.path.join(out_folder, f'{camera_name}_id.png')
    bpy.ops.render.render(write_still=True)
    show('colour')
    scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = 'BW', '16'
    for label, wetness, puddles in (('dry', 0.0, 0.0), ('wet', 0.85, 0.5), ('heavy', 1.0, 0.8)):
        aw.set_state(wetness, puddles)
        scene.render.filepath = os.path.join(out_folder, f'{camera_name}_colour_{label}.png')
        bpy.ops.render.render(write_still=True)
    print('DRAWN', camera_name)
