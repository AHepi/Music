# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2: draws a list of pictures of the street COPY in one Blender run, all with EEVEE (the plates' renderer), ray tracing on, with the round 2 shadow cure (shadow_ray_count 4,
# shadow_step_count 16: the soft-shadow noise was the cause of the white speckle on the wet road). The list is JOBS below: (camera, state, width, height, samples). The layer is put on
# once and its state is changed between pictures. States: today (nothing added: only valid before the layer goes on, so list it first), dry, wet (0.85 / 0.5), heavy (1.0 / 0.8).
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/29_pictures_round2.py -- OUT_FOLDER JOB [JOB ...]
#   JOB = camera:state:width:height:samples      e.g. main:wet:540:960:16 wall_lamp:wet:640:480:24      (state@name writes <camera>_<state>_<name>.png)
#   A shot file of the film project may be opened instead of set_copy/street.blend (read-only; nothing is saved): then 'main' is the camera that file is set to.
# Writes OUT_FOLDER/<camera>_<state>.png and seconds.txt (one line per picture)
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
jobs = [tuple(job.split(':')) for job in args[1:]]
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
STATE_VALUES = {'dry': (0.0, 0.0), 'wet': (0.85, 0.5), 'heavy': (1.0, 0.8)}
applied = False
log = open(os.path.join(out_folder, 'seconds.txt'), 'a')
for camera_name, state_label, width, height, samples in jobs:
    state, _, suffix = state_label.partition('@')          # 'wet@plate' = the wet state, written as <camera>_wet_plate.png
    if state != 'today' and not applied:
        aw.apply(wetness=0.0, puddles=0.0)
        applied = True
    if state in STATE_VALUES:
        aw.set_state(*STATE_VALUES[state])
    scene.camera = cams[camera_name]
    scene.render.resolution_x, scene.render.resolution_y = int(width), int(height)
    scene.eevee.taa_render_samples = int(samples)
    if hasattr(scene.eevee, 'shadow_pool_size') and int(width) > 1080:
        # the film's own plate script does this for pictures wider than 1080 (set_dressing.py, log 31): the default shadow memory overflows
        scene.eevee.shadow_pool_size = '1024'
        scene.eevee.shadow_resolution_scale = min(1.0, 1080 / int(width))
    else:
        scene.eevee.shadow_resolution_scale = 1.0
    scene.render.filepath = os.path.join(out_folder, f'{camera_name}_{state}{"_" + suffix if suffix else ""}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = round(time.time() - started, 1)
    log.write(f'{camera_name} {state_label} {width}x{height} {samples} spp: {seconds} s\n')
    log.flush()
    print('DRAWN', camera_name, state, seconds, 's', flush=True)
