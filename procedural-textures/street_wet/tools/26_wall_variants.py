# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2: the checker found that the cottage walls came out LIGHTER wet than dry (1.16 times in the close view), the opposite of what rain does to brick and stone. This run draws
# the wall close-up camera ("wall_lamp": standing in the road, looking at the foot of the right-hand wall beside the first gas lamp) with EEVEE, dry and wet, with different
# settings for the four wall materials, so the wet/dry ratio picture (tools/24_wall_ratio.py) can be made for each:
#   dry          the layer at 0
#   wet_r1       the round 1 wall settings (band 0.45 m from the pavement, wet roughness 0.45, shine and coat as the layer's defaults)
#   wet_new      the round 2 settings in apply_wetness_to_set.py (band 0.9 m from the floor, rougher 0.55, no extra shine, trace of coat, porosity 0.9, darkest 0.3)
#   wet_dull     as wet_new but wet roughness 0.8 and no coat at all (a wall that is only darker, not shiny)
#   wet_rough9   (run 8) as wet_new but wet roughness 0.9, the same as the dry wall's (a wall whose gloss does not change at all)
#   wet_darker   (run 8) as wet_rough9 but darkest 0.1 (the soaked foot at a tenth of its dry colour)
# EEVEE settings are the plate's, with the round 2 shadow cure (shadow_ray_count / shadow_step_count 4 / 16: see the recipe note on the speckle).
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/26_wall_variants.py -- OUT_FOLDER [CAMERA] [variant ...]
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out_folder = args[0]
camera_name = args[1] if len(args) > 1 else 'wall_lamp'
wanted = args[2:] or ['dry', 'wet_r1', 'wet_new', 'wet_dull']
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
scene.camera = cams[camera_name]
aw.apply(wetness=0.0, puddles=0.0)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = (640, 480) if camera_name == 'wall_lamp' else (540, 960)
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = 24
scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
WALLS = [name for name in aw.APPLIED if name.startswith(('cottage_brick_door', 'cottage_stone_door'))]
print('WALL MATERIALS', WALLS)
NEW = {name: dict(wet_roughness=aw.APPLIED[name][0].inputs['Wet Roughness'].default_value, boost=aw.APPLIED[name][0].inputs['Specular Boost'].default_value,
                  coat=aw.APPLIED[name][0].inputs['Film Coat'].default_value, band=aw.APPLIED[name][0].inputs['Wall Band'].default_value,
                  porosity=aw.APPLIED[name][0].inputs['Porosity'].default_value, darkest=aw.APPLIED[name][0].inputs['Darkest'].default_value,
                  slope=aw.APPLIED[name][0].inputs['Ground Slope'].default_value, offset=aw.APPLIED[name][0].inputs['Ground Offset'].default_value) for name in WALLS}
seconds = {}
for variant in wanted:
    for name in WALLS:
        node = aw.APPLIED[name][0]
        new = NEW[name]
        values = dict(new)
        if variant == 'wet_r1':
            values.update(wet_roughness=0.45, boost=0.25, coat=0.3, band=0.45, porosity=0.7 if 'brick' in name else 0.6, darkest=0.45, slope=aw.SLOPE if 'stone' in name else -aw.SLOPE,
                          offset=aw.WALL_FOOT_OFFSET)
        elif variant == 'wet_dull':
            values.update(wet_roughness=0.8, coat=0.0, boost=0.0)
        elif variant == 'wet_rough9':
            values.update(wet_roughness=0.9, coat=0.0, boost=0.0)
        elif variant == 'wet_darker':
            values.update(wet_roughness=0.9, coat=0.0, boost=0.0, darkest=0.1)
        node.inputs['Wet Roughness'].default_value = values['wet_roughness']
        node.inputs['Specular Boost'].default_value = values['boost']
        node.inputs['Film Coat'].default_value = values['coat']
        node.inputs['Wall Band'].default_value = values['band']
        node.inputs['Porosity'].default_value = values['porosity']
        node.inputs['Darkest'].default_value = values['darkest']
        node.inputs['Ground Slope'].default_value = values['slope']
        node.inputs['Ground Offset'].default_value = values['offset']
    aw.set_state(0.0, 0.0) if variant == 'dry' else aw.set_state(0.85, 0.5)
    scene.render.filepath = os.path.join(out_folder, f'{camera_name}_{variant}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds[variant] = round(time.time() - started, 1)
    print('DRAWN', camera_name, variant, seconds[variant], 's', flush=True)
open(os.path.join(out_folder, f'{camera_name}_seconds.txt'), 'w').write(str(seconds) + '\n')
