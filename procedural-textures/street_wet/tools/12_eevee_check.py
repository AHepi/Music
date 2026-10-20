# What this does: checks that the finished WETNESS layer also works in EEVEE (the fast renderer the film's plates are drawn with, see the study), with ray tracing on (so puddles mirror
# things) and off (the film's setting today), main camera, 540 x 960, 16 samples. Needs a virtual screen: run it with xvfb-run.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/12_eevee_check.py -- OUT_FOLDER
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
aw.apply(wetness=0.85, puddles=0.5)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.render.image_settings.file_format = 'PNG'
scene.eevee.taa_render_samples = 16
for label, raytracing in (('raytracing_on', True), ('raytracing_off', False)):
    scene.eevee.use_raytracing = raytracing
    scene.render.filepath = os.path.join(out_folder, f'eevee_wet_{label}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    print('DRAWN', label, round(time.time() - started, 1), 's')
