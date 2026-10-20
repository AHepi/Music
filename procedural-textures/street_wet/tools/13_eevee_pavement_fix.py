# What this does: tries a stronger cure for the sparkly ("gritty") pavement flags in EEVEE, the renderer the film's plates are drawn with: the pavement's relief is flattened fully when wet
# (Relief Flatten 1.0 instead of 0.6) and its wet roughness is 0.6 instead of 0.45. Draws the main camera, wet, EEVEE with ray tracing on, 16 samples, 540 x 960, to compare with
# work/r12/eevee_wet_raytracing_on.png. Needs a virtual screen: run it with xvfb-run.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/13_eevee_pavement_fix.py -- OUT_FOLDER
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
aw.cameras()
aw.MATERIALS['pavement_flags'].update(relief_flatten=1.0, wet_roughness=0.6)
aw.apply(wetness=0.85, puddles=0.5)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.render.image_settings.file_format = 'PNG'
scene.eevee.taa_render_samples = 16
scene.eevee.use_raytracing = True
scene.render.filepath = os.path.join(out_folder, 'eevee_wet_pavement_fix.png')
started = time.time()
bpy.ops.render.render(write_still=True)
print('DRAWN', round(time.time() - started, 1), 's')
