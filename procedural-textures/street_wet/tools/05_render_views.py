# What this does: draws pictures of the street COPY with Cycles (Blender's exact renderer, on the processor, 2 threads, with the noise filter OpenImageDenoise), for any
# camera and any state: 'today' = the street exactly as the film project has it (nothing added), 'dry' = the new materials with the WETNESS layer switched to dry
# (so only Poly Haven's real roughness and height pictures are new), 'wet' = wetness 0.85 / puddles 0.5, 'heavy' = wetness 1.0 / puddles 0.8 ("heavier rain").
# One run can draw several states in this order: today first (before the layer goes on), then dry, wet, heavy.
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/05_render_views.py -- OUT_FOLDER CAMERA STATES W H SAMPLES [TIME_LIMIT_SECONDS] [key=value ...]
#   CAMERA: main | lockout | notice | close_road | wall_lamp      STATES: for example today,dry,wet,heavy      key=value: any layer setting for every material (puddle_roughness=0.08)
# Writes OUT_FOLDER/<camera>_<state>.png and OUT_FOLDER/<camera>_<state>_seconds.txt
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out_folder, camera_name, states = args[0], args[1], args[2].split(',')
width, height, samples = int(args[3]), int(args[4]), int(args[5])
time_limit = float(args[6]) if len(args) > 6 and '=' not in args[6] else 0.0
overrides = {a.split('=')[0]: float(a.split('=')[1]) for a in args[6:] if '=' in a}
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
cams = aw.cameras()
scene.camera = cams[camera_name]
aw.cycles_settings(scene, width, height, samples)
if time_limit:
    scene.cycles.time_limit = time_limit
STATE_VALUES = {'dry': (0.0, 0.0), 'wet': (0.85, 0.5), 'heavy': (1.0, 0.8)}
applied = False
for state in states:
    if state != 'today' and not applied:
        aw.apply(wetness=0.0, puddles=0.0, **overrides)
        applied = True
    if state in STATE_VALUES:
        aw.set_state(*STATE_VALUES[state])
    scene.render.filepath = os.path.join(out_folder, f'{camera_name}_{state}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = round(time.time() - started, 1)
    open(os.path.join(out_folder, f'{camera_name}_{state}_seconds.txt'), 'w').write(f'{seconds}\n')
    print('DRAWN', camera_name, state, seconds, 's')
